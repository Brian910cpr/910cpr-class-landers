#!/usr/bin/env python3
"""Build report-only seed proposals from candidate slots."""

from __future__ import annotations

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_candidate_slot_report import (
    CONFIG_DIR,
    DEBUG_DIR,
    REPORT_JSON_PATH as CANDIDATE_REPORT_JSON_PATH,
    SOURCE_MODES,
    TZ,
    build_report_payload as build_candidate_report_payload,
    load_json,
    parse_dt,
)


REPORT_JSON_PATH = DEBUG_DIR / "seed_simulation_report.json"
REPORT_MD_PATH = DEBUG_DIR / "seed_simulation_report.md"


def load_rules() -> dict[str, dict[str, Any]]:
    payload = load_json(CONFIG_DIR / "rules.json")
    return {
        str(rule.get("rule_key") or ""): rule
        for rule in payload.get("rules", [])
        if isinstance(rule, dict) and str(rule.get("rule_key") or "")
    }


def load_instructors() -> dict[str, dict[str, Any]]:
    payload = load_json(CONFIG_DIR / "instructors.json")
    return {
        str(instructor.get("instructor_key") or ""): instructor
        for instructor in payload.get("instructors", [])
        if isinstance(instructor, dict) and str(instructor.get("instructor_key") or "")
    }


def overlaps(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_start = parse_dt(left["candidate_start"])
    left_end = parse_dt(left["candidate_end"])
    right_start = parse_dt(right["candidate_start"])
    right_end = parse_dt(right["candidate_end"])
    if not left_start or not left_end or not right_start or not right_end:
        return False
    return left_start < right_end and right_start < left_end


def candidate_sort_key(candidate: dict[str, Any], priority_order: list[str]) -> tuple[int, int, str]:
    course_key = str(candidate.get("course_key") or "")
    try:
        priority = priority_order.index(course_key)
    except ValueError:
        priority = len(priority_order)
    source_rank = 0 if candidate.get("source_window_type") == "HARD" else 1
    return priority, source_rank, str(candidate.get("candidate_start") or "")


def simulate_instructor(
    row: dict[str, Any],
    instructor: dict[str, Any],
    rules: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    instructor_key = str(row.get("instructor_key") or "")
    mode = str(row.get("calendar_mode") or "")
    if mode == "inverse_blocking":
        return {
            "instructor_key": instructor_key,
            "calendar_mode": mode,
            "candidate_count": len(row.get("candidates", [])),
            "selected_seed_proposals": [],
            "skipped_candidates": [],
            "warnings": [
                "Brian seed simulation requires future configured search horizon/base candidate windows."
            ],
            "blocking_windows": row.get("blocking_windows", []),
        }

    rule_key = str(instructor.get("priority_rule_key") or "")
    rule = rules.get(rule_key, {})
    priority_order = [str(item) for item in rule.get("priority_order", [])]
    candidates = sorted(row.get("candidates", []), key=lambda item: candidate_sort_key(item, priority_order))
    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for candidate in candidates:
        conflict = next((item for item in selected if overlaps(candidate, item)), None)
        if conflict:
            skipped_record = dict(candidate)
            skipped_record["skipped_reason"] = (
                "overlaps selected seed "
                f"{conflict.get('course_key')} {conflict.get('candidate_start')} to {conflict.get('candidate_end')}"
            )
            skipped_record["conflict_avoided"] = True
            skipped.append(skipped_record)
            continue
        selected_record = dict(candidate)
        selected_record["selection_reason"] = (
            f"{rule_key}: selected by priority order with HARD preferred and SOFT limited to support candidates"
        )
        selected_record["conflict_avoided"] = False
        selected.append(selected_record)

    for candidate in row.get("skipped", []):
        skipped_record = dict(candidate)
        skipped_record["conflict_avoided"] = False
        skipped.append(skipped_record)

    return {
        "instructor_key": instructor_key,
        "calendar_mode": mode,
        "priority_rule_key": rule_key,
        "candidate_count": len(row.get("candidates", [])),
        "selected_seed_proposals": selected,
        "skipped_candidates": skipped,
        "warnings": row.get("warnings", []),
        "blocking_windows": row.get("blocking_windows", []),
    }


def build_report_payload(source_mode: str = "auto") -> dict[str, Any]:
    load_json(CONFIG_DIR / "course_options.json")
    load_json(CONFIG_DIR / "locations.json")
    if (CONFIG_DIR / "courses.json").exists():
        load_json(CONFIG_DIR / "courses.json")

    candidate_report = build_candidate_report_payload(source_mode=source_mode)
    instructors = load_instructors()
    rules = load_rules()
    rows = []
    for row in candidate_report["instructors"]:
        instructor_key = str(row.get("instructor_key") or "")
        rows.append(simulate_instructor(row, instructors.get(instructor_key, {}), rules))

    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "source_mode": source_mode,
        "candidate_report_source": str(CANDIDATE_REPORT_JSON_PATH.relative_to(ROOT)),
        "candidate_report_generated_inline": True,
        "instructors": rows,
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# Seed Simulation Report",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Report only: {report['report_only']}",
        f"- Public behavior changed: {report['public_behavior_changed']}",
        f"- Source mode: {report['source_mode']}",
        "",
    ]
    for row in report["instructors"]:
        lines.extend(
            [
                f"## {row['instructor_key']}",
                f"- Calendar mode: {row['calendar_mode']}",
                f"- Candidate count: {row['candidate_count']}",
                f"- Selected seed proposals: {len(row['selected_seed_proposals'])}",
                f"- Skipped candidates: {len(row['skipped_candidates'])}",
                f"- Blocking windows: {len(row['blocking_windows'])}",
                f"- Warnings: {len(row['warnings'])}",
                "",
            ]
        )
        if row["selected_seed_proposals"]:
            lines.append("### Selected")
            for selected in row["selected_seed_proposals"]:
                lines.append(
                    f"- {selected['course_key']} ({selected['source_window_type']}): "
                    f"{selected['candidate_start']} to {selected['candidate_end']} - {selected.get('selection_reason')}"
                )
            lines.append("")
        if row["skipped_candidates"]:
            lines.append("### Skipped")
            for skipped in row["skipped_candidates"][:20]:
                lines.append(
                    f"- {skipped['course_key']} ({skipped['source_window_type']}): "
                    f"{skipped['candidate_start']} to {skipped['candidate_end']} - {skipped.get('skipped_reason')}"
                )
            lines.append("")
        for warning in row["warnings"]:
            lines.append(f"- Warning: {warning}")
        lines.append("")
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build report-only seed simulation from fixture or live calendar sources.")
    parser.add_argument("--source", choices=sorted(SOURCE_MODES), default="auto", help="Event source mode passed through to candidate/availability ingestion.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report_payload(source_mode=args.source)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print("Seed simulation report generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
