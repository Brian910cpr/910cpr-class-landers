#!/usr/bin/env python3
"""Provider-neutral, read-only interface to LanderWare public inventory.

This module deliberately consumes the final artifacts used by the website.  It
does not calculate availability: free_time_scheduler.py remains responsible for
dynamic offers and build_schedule_future.py remains responsible for real
Enrollware sessions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
DYNAMIC_OFFERS_PATH = ROOT / "docs" / "data" / "customer_facing_offers.json"
COURSE_MASTER_PATH = ROOT / "data" / "config" / "course_master.json"
API_VERSION = "landerware.agent.v1"


class AgentInterfaceError(ValueError):
    """A safe, machine-readable request error."""


def _read_json(path: Path, *, required: bool = False) -> tuple[Any, str | None]:
    if not path.exists():
        if required:
            raise AgentInterfaceError(f"required inventory artifact is missing: {path.relative_to(ROOT)}")
        return {}, f"inventory artifact is missing: {path.relative_to(ROOT)}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentInterfaceError(f"invalid inventory artifact {path.relative_to(ROOT)}: {exc}") from exc


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _as_rows(payload: Any, key: str) -> list[dict[str, Any]]:
    rows = payload.get(key, []) if isinstance(payload, dict) else []
    return [row for row in rows if isinstance(row, dict)]


def _course_records(schedule: Any, offers: Any, master: Any) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}

    def add(key: Any, title: Any, course_id: Any = None, aliases: Any = None) -> None:
        stable_key = str(key or "").strip()
        stable_id = str(course_id or "").strip()
        stable_title = str(title or "").strip()
        identity = stable_key or stable_id or _norm(stable_title).replace(" ", "-")
        if not identity:
            return
        item = records.setdefault(identity, {"course_key": stable_key, "course_id": stable_id, "course_name": stable_title, "aliases": []})
        item["course_key"] = item["course_key"] or stable_key
        item["course_id"] = item["course_id"] or stable_id
        item["course_name"] = item["course_name"] or stable_title
        values = aliases if isinstance(aliases, list) else []
        item["aliases"] = sorted({*item["aliases"], *[str(value) for value in values if value]})

    for row in _as_rows(schedule, "sessions"):
        add(row.get("course_key"), row.get("official_course_name") or row.get("course_name"), row.get("course_id"), [row.get("raw_course_name")])
    for group in _as_rows(offers, "courses"):
        add(group.get("course_key"), group.get("course_display_name") or group.get("course_title"))
    master_rows = master.get("courses", master) if isinstance(master, dict) else master
    if isinstance(master_rows, list):
        for row in master_rows:
            if isinstance(row, dict):
                add(row.get("course_key"), row.get("official_course_name") or row.get("official_title") or row.get("clean_title"), row.get("course_id"), row.get("aliases"))
    return sorted(records.values(), key=lambda row: (row["course_name"], row["course_key"], row["course_id"]))


def identify_course(intent: dict[str, Any], *, schedule: Any = None, offers: Any = None, course_master: Any = None) -> dict[str, Any]:
    """Resolve structured intent without inventing a course mapping."""
    if not isinstance(intent, dict):
        raise AgentInterfaceError("intent must be a JSON object")
    if schedule is None:
        schedule, _ = _read_json(SCHEDULE_PATH, required=True)
    if offers is None:
        offers, _ = _read_json(DYNAMIC_OFFERS_PATH)
    if course_master is None:
        course_master, _ = _read_json(COURSE_MASTER_PATH)
    records = _course_records(schedule, offers, course_master)
    requested_key = str(intent.get("course_key") or "").strip()
    requested_id = str(intent.get("course_id") or "").strip()
    requested_name = _norm(intent.get("course_name") or intent.get("query"))

    exact = [row for row in records if (requested_key and row["course_key"] == requested_key) or (requested_id and row["course_id"] == requested_id)]
    method = "course_key" if requested_key else "course_id"
    if not exact and requested_name:
        exact = [row for row in records if requested_name in {_norm(row["course_name"]), _norm(row["course_key"]), *[_norm(alias) for alias in row["aliases"]]}]
        method = "exact_name_or_alias"
    if len(exact) != 1:
        return {
            "status": "not_found" if not exact else "ambiguous",
            "match": None,
            "candidates": exact[:10],
            "message": "Use a durable course_key or course_id." if not exact else "Multiple authoritative course records matched.",
        }
    return {"status": "resolved", "match_method": method, "match": exact[0], "candidates": []}


def _date_in_range(value: str, start: date | None, end: date | None) -> bool:
    try:
        current = datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except (TypeError, ValueError):
        return False
    return (start is None or current >= start) and (end is None or current <= end)


def _parse_date(value: Any, field: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise AgentInterfaceError(f"{field} must be YYYY-MM-DD") from exc


def find_availability(request: dict[str, Any], *, schedule: Any = None, offers: Any = None, course_master: Any = None) -> dict[str, Any]:
    """Return only options already approved for the public web experience."""
    if not isinstance(request, dict):
        raise AgentInterfaceError("request must be a JSON object")
    warnings: list[str] = []
    if schedule is None:
        schedule, _ = _read_json(SCHEDULE_PATH, required=True)
    if offers is None:
        offers, warning = _read_json(DYNAMIC_OFFERS_PATH)
        if warning:
            warnings.append(warning)
    if course_master is None:
        course_master, warning = _read_json(COURSE_MASTER_PATH)
        if warning:
            warnings.append(warning)

    resolved = identify_course(request.get("course") or request, schedule=schedule, offers=offers, course_master=course_master)
    if resolved["status"] != "resolved":
        return {"api_version": API_VERSION, "status": "course_unresolved", "course_resolution": resolved, "options": [], "warnings": warnings}
    course = resolved["match"]
    start_date = _parse_date(request.get("date_from"), "date_from")
    end_date = _parse_date(request.get("date_to"), "date_to")
    if start_date and end_date and end_date < start_date:
        raise AgentInterfaceError("date_to must not precede date_from")
    limit = int(request.get("limit", 20))
    if limit < 1 or limit > 100:
        raise AgentInterfaceError("limit must be between 1 and 100")

    options: list[dict[str, Any]] = []
    for row in _as_rows(schedule, "sessions"):
        row_key = str(row.get("course_key") or "")
        row_id = str(row.get("course_id") or "")
        if not ((course["course_key"] and row_key == course["course_key"]) or (course["course_id"] and row_id == course["course_id"])):
            continue
        start = row.get("start_at")
        if not _date_in_range(start, start_date, end_date):
            continue
        capacity = row.get("max_students") or row.get("capacity")
        enrolled = row.get("enrolled_count") or row.get("students")
        remaining = max(0, int(capacity) - int(enrolled)) if capacity is not None and enrolled is not None else row.get("available_seats")
        options.append({
            "offering_id": str(row.get("session_id") or row.get("class_id") or ""),
            "offering_type": "existing_class",
            "course_key": course["course_key"], "course_id": course["course_id"], "course_name": course["course_name"],
            "start_at": start, "end_at": row.get("end_at"), "timezone": row.get("timezone") or schedule.get("timezone"),
            "location": row.get("location_display") or row.get("location_name"), "instructor": row.get("lead_instructor_name") or row.get("instructor"),
            "capacity": capacity, "remaining_capacity": remaining, "registration_url": row.get("registration_url") or row.get("enrollware_enroll_url"),
        })
    for group in _as_rows(offers, "courses"):
        if str(group.get("course_key") or "") != course["course_key"]:
            continue
        for row in _as_rows(group, "offered_options"):
            # This is the same publication gate used by build_slug_hubs.py's
            # load_customer_facing_offers(). Draft/suppressed rows are not
            # options merely because they remain in the generated artifact.
            if str(row.get("session_status") or "").strip() != "proposed":
                continue
            start = row.get("start_time") or row.get("start_at")
            if not _date_in_range(start, start_date, end_date):
                continue
            options.append({
                "offering_id": str(row.get("offer_slug") or row.get("page_slug") or ""),
                "offering_type": "dynamic_offer",
                "course_key": course["course_key"], "course_id": course["course_id"], "course_name": course["course_name"],
                "start_at": start, "end_at": row.get("end_time") or row.get("end_at"), "timezone": offers.get("timezone") or schedule.get("timezone"),
                "location": row.get("location_name"), "instructor": row.get("instructor"), "capacity": row.get("capacity"),
                "remaining_capacity": None, "registration_url": row.get("appointment_url") or row.get("registration_url"),
            })
    options.sort(key=lambda row: (row.get("start_at") or "", row["offering_type"], row["offering_id"]))
    return {
        "api_version": API_VERSION, "status": "ok", "read_only": True, "course_resolution": resolved,
        "options": options[:limit], "option_count": min(len(options), limit), "total_matching_options": len(options),
        "authoritative_sources": ["docs/data/schedule_future.json", "docs/data/customer_facing_offers.json"], "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only LanderWare Agent Interface")
    parser.add_argument("operation", choices=("identify_course", "find_availability"))
    parser.add_argument("--request", required=True, help="JSON object")
    args = parser.parse_args()
    try:
        request = json.loads(args.request)
        result = identify_course(request) if args.operation == "identify_course" else find_availability(request)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("status") in {"ok", "resolved"} else 2
    except (AgentInterfaceError, json.JSONDecodeError) as exc:
        print(json.dumps({"api_version": API_VERSION, "status": "error", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
