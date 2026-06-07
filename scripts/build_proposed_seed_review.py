#!/usr/bin/env python3
"""Build a human-readable review report for proposed seed selections."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_candidate_slot_report import FALLBACK_COURSES
from scripts.build_instructor_availability_report import DEBUG_DIR, SOURCE_MODES, TZ, parse_dt
from scripts.build_seed_simulation_report import build_report_payload


REPORT_JSON_PATH = DEBUG_DIR / "proposed_seed_review.json"
REPORT_MD_PATH = DEBUG_DIR / "proposed_seed_review.md"


COURSE_TITLES = {
    "aha_acls_renewal": "AHA ACLS Renewal",
    "aha_acls_initial": "AHA ACLS Initial",
    "aha_pals_renewal": "AHA PALS Renewal",
    "aha_pals_initial": "AHA PALS Initial",
    "aha_acls_heartcode_skills": "ACLS HeartCode Skills",
    "aha_pals_heartcode_skills": "PALS HeartCode Skills",
    "aha_bls_renewal": "AHA BLS Renewal",
    "aha_bls_initial": "AHA BLS Initial",
    "aha_bls_heartcode_skills": "AHA BLS HeartCode Skills",
    "aha_heartsaver_fa_cpr_aed": "Heartsaver First Aid CPR AED",
    "aha_heartsaver_cpr_aed": "Heartsaver CPR AED",
    "aha_heartsaver_online_skills": "Heartsaver Online Skills",
    "hsi_adult_fa_cpr_aed": "HSI Adult First Aid CPR AED",
    "arc_bls": "ARC BLS",
}


def course_title(course_key: str) -> str:
    return COURSE_TITLES.get(course_key) or course_key.replace("_", " ").title()


def format_time(value: Any) -> str:
    dt = parse_dt(value)
    if not dt:
        return str(value or "")
    return dt.strftime("%I:%M %p").lstrip("0")


def format_date(value: Any) -> str:
    dt = parse_dt(value)
    if not dt:
        return "Undated"
    return dt.strftime("%A, %B %-d, %Y") if sys.platform != "win32" else dt.strftime("%A, %B %#d, %Y")


def date_key(value: Any) -> str:
    dt = parse_dt(value)
    return dt.date().isoformat() if dt else "9999-99-99"


def caution_flags(seed: dict[str, Any], row: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    if seed.get("source_window_type") == "SOFT-supported":
        flags.append("SOFT-used")
    if seed.get("source_window_type") == "BASE-HORIZON":
        flags.append("Brian horizon-generated")
    if "registration_target_key" not in seed:
        flags.append("no registration target yet")
    course = FALLBACK_COURSES.get(str(seed.get("course_key") or ""), {})
    expected = int(course.get("duration_minutes") or 0)
    actual_start = parse_dt(seed.get("candidate_start"))
    actual_end = parse_dt(seed.get("candidate_end"))
    actual = int((actual_end - actual_start).total_seconds() // 60) if actual_start and actual_end else 0
    if expected and actual and expected > actual:
        flags.append("duration longer than expected")
    if any("No live ICS URL configured" in str(warning) for warning in row.get("warnings", [])):
        flags.append("missing live calendar source")
    return flags


def review_row(row: dict[str, Any]) -> dict[str, Any]:
    selected = row.get("selected_seed_proposals", [])
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    labels: dict[str, str] = {}
    for seed in selected:
        key = date_key(seed.get("candidate_start"))
        labels[key] = format_date(seed.get("candidate_start"))
        grouped[key].append(seed)
    return {
        "instructor_key": row.get("instructor_key"),
        "candidate_count": row.get("candidate_count"),
        "selected_count": len(selected),
        "skipped_count": len(row.get("skipped_candidates", [])),
        "blocking_window_count": len(row.get("blocking_windows", [])),
        "warnings": row.get("warnings", []),
        "no_candidates": not selected,
        "selected_by_date": [
            {
                "date_key": key,
                "label": labels[key],
                "seeds": sorted(items, key=lambda item: str(item.get("candidate_start") or "")),
            }
            for key, items in sorted(grouped.items())
        ],
        "skip_reason_counts": row.get("skip_reason_counts", {}),
    }


def build_review(source_mode: str) -> dict[str, Any]:
    seed_report = build_report_payload(source_mode=source_mode)
    rows = [review_row(row) for row in seed_report.get("instructors", [])]
    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "do_not_publish_yet": True,
        "source_mode": source_mode,
        "summary": {
            "candidates_considered": sum(int(row.get("candidate_count") or 0) for row in rows),
            "selected_seeds": sum(int(row.get("selected_count") or 0) for row in rows),
            "skipped_seeds": sum(int(row.get("skipped_count") or 0) for row in rows),
            "blocking_windows": sum(int(row.get("blocking_window_count") or 0) for row in rows),
            "warnings": sum(len(row.get("warnings", [])) for row in rows),
        },
        "instructors": rows,
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Proposed Seed Review",
        "",
        "> DO NOT PUBLISH YET: This report is advisory only and does not change public pages or Enrollware.",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Source mode: {report['source_mode']}",
        f"- Candidates considered: {report['summary']['candidates_considered']}",
        f"- Selected seeds: {report['summary']['selected_seeds']}",
        f"- Skipped seeds: {report['summary']['skipped_seeds']}",
        f"- Blocking windows: {report['summary']['blocking_windows']}",
        f"- Warnings: {report['summary']['warnings']}",
        "",
    ]

    for row in report["instructors"]:
        display_name = str(row["instructor_key"] or "").title()
        lines.extend(
            [
                f"## {display_name}",
                f"- Candidates considered: {row['candidate_count']}",
                f"- Selected seeds: {row['selected_count']}",
                f"- Skipped seeds: {row['skipped_count']}",
                f"- Blocking windows: {row['blocking_window_count']}",
                f"- Warnings: {len(row['warnings'])}",
                "",
            ]
        )
        if row["no_candidates"]:
            lines.append("- Caution: no candidates for instructor")
            lines.append("")
        for warning in row["warnings"]:
            lines.append(f"- Caution: {warning}")
        if row["warnings"]:
            lines.append("")

        for group in row["selected_by_date"]:
            lines.append(f"### {group['label']}")
            for seed in group["seeds"]:
                title = course_title(str(seed.get("course_key") or ""))
                start = format_time(seed.get("candidate_start"))
                end = format_time(seed.get("candidate_end"))
                source = seed.get("source_window_type")
                reason = seed.get("selection_reason") or seed.get("rule_reason")
                flags = caution_flags(seed, row)
                lines.append(f"- {start} - {end} - {title}")
                lines.append(f"  - Source: {source}")
                lines.append(f"  - Reason: {reason}")
                if flags:
                    lines.append(f"  - Caution flags: {', '.join(flags)}")
            lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-friendly proposed seed report.")
    parser.add_argument("--source", choices=sorted(SOURCE_MODES), default="auto", help="Event source mode passed through to seed simulation.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_review(args.source)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print("Proposed seed review generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
