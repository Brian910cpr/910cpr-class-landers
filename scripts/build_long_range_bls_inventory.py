from __future__ import annotations

import argparse
import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "data" / "config" / "long_range_bls_inventory_policy.json"
COURSE_CATALOG_PATH = ROOT / "data" / "config" / "course_catalog.json"
CONTAINERS_PATH = ROOT / "data" / "inventory" / "appointment_containers.json"
OUTPUT_PATH = ROOT / "data" / "audit" / "long_range_bls_inventory_preview.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def parse_time(value: Any) -> time | None:
    try:
        return time.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def catalog_by_id(payload: Any) -> dict[str, dict[str, Any]]:
    courses = payload.get("courses", []) if isinstance(payload, dict) else []
    return {
        str(item["course_id"]): item
        for item in courses
        if isinstance(item, dict) and item.get("course_id")
    }


def active_container_ranges(payload: Any) -> list[tuple[date, date]]:
    containers = payload.get("containers", []) if isinstance(payload, dict) else []
    ranges: list[tuple[date, date]] = []
    for item in containers:
        if not isinstance(item, dict) or item.get("status") != "active":
            continue
        start = parse_date(item.get("first_valid_date"))
        end = parse_date(item.get("last_valid_date"))
        if start and end:
            ranges.append((start, end))
    return ranges


def container_supports(target: date, ranges: list[tuple[date, date]]) -> bool:
    return any(start <= target <= end for start, end in ranges)


def build_inventory(
    policy: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
    container_ranges: list[tuple[date, date]],
    *,
    today: date,
    demand_keys: set[str] | None = None,
) -> dict[str, Any]:
    demand_keys = demand_keys or set()
    if policy.get("enabled") is not True:
        return {"schema_version": policy.get("schema_version"), "status": "disabled", "occurrences": []}

    cutoff_days = int(policy.get("short_term_cutoff_days", 90))
    horizon_days = int(policy.get("planning_horizon_days", 365))
    allowed_ids = {str(value) for value in policy.get("course_ids", [])}
    unknown_ids = sorted(allowed_ids - catalog.keys())
    if unknown_ids:
        raise ValueError(f"Long-range policy references unknown course IDs: {', '.join(unknown_ids)}")

    templates = policy.get("weekly_templates", [])
    occurrences: list[dict[str, Any]] = []
    pruned: list[dict[str, Any]] = []
    first_day = today + timedelta(days=1)
    last_day = today + timedelta(days=horizon_days)
    cursor = first_day
    while cursor <= last_day:
        for template in templates:
            if not isinstance(template, dict) or template.get("weekday") != cursor.weekday():
                continue
            course_id = str(template.get("course_id") or "")
            start = parse_time(template.get("start_time"))
            if course_id not in allowed_ids or not start:
                continue
            course = catalog[course_id]
            key = f"seo-bls-{course_id}-{cursor:%Y%m%d}-{start:%H%M}"
            has_demand = key in demand_keys
            days_out = (cursor - today).days
            if days_out <= cutoff_days and not has_demand:
                pruned.append({"inventory_key": key, "date": cursor.isoformat(), "reason": "inside_short_term_window_without_demand"})
                continue
            if not container_supports(cursor, container_ranges):
                pruned.append({"inventory_key": key, "date": cursor.isoformat(), "reason": "outside_verified_appointment_container_range"})
                continue
            occurrences.append({
                "inventory_key": key,
                "date": cursor.isoformat(),
                "start_time": start.strftime("%H:%M"),
                "course_id": course_id,
                "course_title": course.get("official_title") or course.get("short_title"),
                "course_family": course.get("family"),
                "inventory_state": "demand_detected" if has_demand else "proposed_seo_inventory",
                "schedule_role": "proposed_anchor",
                "is_committed_session": False,
                "reserves_capacity": False,
                "emit_event_structured_data": False,
                "registration_mode": "capture_interest",
                "promotion_target": "canonical_session_workflow",
                "source": "data/config/long_range_bls_inventory_policy.json",
            })
        cursor += timedelta(days=1)

    return {
        "schema_version": policy.get("schema_version"),
        "generated_at": datetime.combine(today, time.min).isoformat(),
        "as_of_date": today.isoformat(),
        "short_term_cutoff_days": cutoff_days,
        "planning_horizon_days": horizon_days,
        "safety_contract": {
            "committed_sessions_created": 0,
            "capacity_reserved": False,
            "inside_cutoff_requires_demand": True,
            "verified_appointment_container_required": True,
            "event_structured_data_allowed": False,
        },
        "summary": {"published_candidates": len(occurrences), "pruned": len(pruned)},
        "occurrences": occurrences,
        "pruned": pruned,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build safe long-range proposed BLS inventory.")
    parser.add_argument("--today", help="Override today's date (YYYY-MM-DD) for deterministic audits.")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    today = parse_date(args.today) if args.today else date.today()
    if not today:
        parser.error("--today must be YYYY-MM-DD")
    payload = build_inventory(
        read_json(POLICY_PATH),
        catalog_by_id(read_json(COURSE_CATALOG_PATH)),
        active_container_ranges(read_json(CONTAINERS_PATH)),
        today=today,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}: {payload['summary']['published_candidates']} proposed, {payload['summary']['pruned']} pruned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
