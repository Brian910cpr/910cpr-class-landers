#!/usr/bin/env python3
"""Build report-only class candidate slots from instructor availability."""

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

from scripts.build_instructor_availability_report import CONFIG_DIR, DEBUG_DIR, SOURCE_MODES, TZ, build_report, load_json, parse_dt


COURSES_PATH = CONFIG_DIR / "courses.json"
COURSE_OPTIONS_PATH = CONFIG_DIR / "course_options.json"
RULES_PATH = CONFIG_DIR / "rules.json"
LOCATIONS_PATH = CONFIG_DIR / "locations.json"
REPORT_JSON_PATH = DEBUG_DIR / "candidate_slot_report.json"
REPORT_MD_PATH = DEBUG_DIR / "candidate_slot_report.md"

FALLBACK_COURSES = {
    "aha_acls_renewal": {"course_key": "aha_acls_renewal", "course_group": "ACLS", "duration_minutes": 180},
    "aha_acls_initial": {"course_key": "aha_acls_initial", "course_group": "ACLS", "duration_minutes": 360},
    "aha_pals_renewal": {"course_key": "aha_pals_renewal", "course_group": "PALS", "duration_minutes": 180},
    "aha_pals_initial": {"course_key": "aha_pals_initial", "course_group": "PALS", "duration_minutes": 360},
    "aha_acls_heartcode_skills": {"course_key": "aha_acls_heartcode_skills", "course_group": "ACLS", "duration_minutes": 60},
    "aha_pals_heartcode_skills": {"course_key": "aha_pals_heartcode_skills", "course_group": "PALS", "duration_minutes": 60},
    "aha_bls_renewal": {"course_key": "aha_bls_renewal", "course_group": "BLS", "duration_minutes": 90},
    "aha_bls_initial": {"course_key": "aha_bls_initial", "course_group": "BLS", "duration_minutes": 120},
    "aha_bls_heartcode_skills": {"course_key": "aha_bls_heartcode_skills", "course_group": "BLS", "duration_minutes": 45},
    "aha_heartsaver_fa_cpr_aed": {"course_key": "aha_heartsaver_fa_cpr_aed", "course_group": "Heartsaver", "duration_minutes": 150},
    "aha_heartsaver_cpr_aed": {"course_key": "aha_heartsaver_cpr_aed", "course_group": "Heartsaver", "duration_minutes": 120},
    "aha_heartsaver_online_skills": {"course_key": "aha_heartsaver_online_skills", "course_group": "Heartsaver", "duration_minutes": 45},
    "hsi_adult_fa_cpr_aed": {"course_key": "hsi_adult_fa_cpr_aed", "course_group": "HSI", "duration_minutes": 150},
    "arc_bls": {"course_key": "arc_bls", "course_group": "ARC", "duration_minutes": 120},
}


def minutes_between(start_value: str, end_value: str) -> int:
    start = parse_dt(start_value)
    end = parse_dt(end_value)
    if not start or not end:
        return 0
    return int((end - start).total_seconds() // 60)


def load_courses() -> tuple[dict[str, dict[str, Any]], str]:
    if COURSES_PATH.exists():
        payload = load_json(COURSES_PATH)
        rows = payload.get("courses", [])
        if isinstance(rows, list):
            return {
                str(row.get("course_key") or ""): row
                for row in rows
                if isinstance(row, dict) and str(row.get("course_key") or "")
            }, "data/config/courses.json"
    return dict(FALLBACK_COURSES), "built_in_report_only_fallback_catalog"


def load_rules() -> dict[str, dict[str, Any]]:
    payload = load_json(RULES_PATH)
    return {
        str(rule.get("rule_key") or ""): rule
        for rule in payload.get("rules", [])
        if isinstance(rule, dict) and str(rule.get("rule_key") or "")
    }


def eligible_by_group(course: dict[str, Any], instructor: dict[str, Any]) -> bool:
    groups = {str(group) for group in instructor.get("allowed_course_groups", [])}
    return str(course.get("course_group") or "") in groups


def candidate_record(
    instructor_key: str,
    course: dict[str, Any],
    window: dict[str, Any],
    source_window_type: str,
    rule_reason: str,
    skipped_reason: str = "",
) -> dict[str, Any]:
    return {
        "instructor_key": instructor_key,
        "course_key": course.get("course_key"),
        "course_group": course.get("course_group"),
        "candidate_start": window.get("start"),
        "candidate_end": window.get("end"),
        "duration_minutes": int(course.get("duration_minutes") or 0),
        "source_window_type": source_window_type,
        "location_key": window.get("location_key"),
        "rule_reason": rule_reason,
        "skipped_reason": skipped_reason,
    }


def build_explicit_candidates(
    availability: dict[str, Any],
    instructor: dict[str, Any],
    courses: dict[str, dict[str, Any]],
    rules: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    rule_key = str(instructor.get("priority_rule_key") or "")
    rule = rules.get(rule_key, {})
    warnings: list[str] = []
    candidates: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    priority_order = [str(key) for key in rule.get("priority_order", [])]
    instructor_key = str(instructor.get("instructor_key") or availability.get("instructor_key") or "")

    for window in availability.get("normalized_hard_windows", []):
        window_minutes = minutes_between(window["start"], window["end"])
        for course_key in priority_order:
            course = courses.get(course_key) or {"course_key": course_key, "course_group": "unknown", "duration_minutes": 0}
            if not eligible_by_group(course, instructor):
                skipped.append(candidate_record(instructor_key, course, window, "HARD", f"{rule_key} priority order", "course group not allowed for instructor"))
                continue
            duration = int(course.get("duration_minutes") or 0)
            if duration <= 0:
                skipped.append(candidate_record(instructor_key, course, window, "HARD", f"{rule_key} priority order", "missing course duration"))
                continue
            if duration > window_minutes:
                skipped.append(candidate_record(instructor_key, course, window, "HARD", f"{rule_key} priority order", f"duration {duration} exceeds HARD window {window_minutes}"))
                continue
            candidates.append(candidate_record(instructor_key, course, window, "HARD", f"{rule_key}: fits normalized HARD window"))

    for window in availability.get("normalized_soft_windows", []):
        window_minutes = minutes_between(window["start"], window["end"])
        for course_key in priority_order:
            course = courses.get(course_key) or {"course_key": course_key, "course_group": "unknown", "duration_minutes": 0}
            duration = int(course.get("duration_minutes") or 0)
            is_skills = "heartcode" in course_key or "skills" in course_key
            if not eligible_by_group(course, instructor):
                skipped.append(candidate_record(instructor_key, course, window, "SOFT-supported", f"{rule_key} soft policy", "course group not allowed for instructor"))
                continue
            if not is_skills:
                skipped.append(candidate_record(instructor_key, course, window, "SOFT-supported", f"{rule_key} soft policy", "SOFT is stack-support/skills-support only"))
                continue
            if duration > window_minutes:
                skipped.append(candidate_record(instructor_key, course, window, "SOFT-supported", f"{rule_key} soft policy", f"duration {duration} exceeds SOFT window {window_minutes}"))
                continue
            candidates.append(candidate_record(instructor_key, course, window, "SOFT-supported", f"{rule_key}: skills-support candidate from SOFT edge"))

    if not availability.get("normalized_hard_windows") and not availability.get("normalized_soft_windows"):
        warnings.append("No HARD/SOFT windows available; no candidates generated.")
    return candidates, skipped, warnings


def build_report_payload(source_mode: str = "auto") -> dict[str, Any]:
    instructor_config = load_json(CONFIG_DIR / "instructors.json")
    load_json(COURSE_OPTIONS_PATH)
    load_json(LOCATIONS_PATH)
    courses, course_source = load_courses()
    rules = load_rules()
    availability_report = build_report(source_mode=source_mode)
    instructors = {
        str(item.get("instructor_key") or ""): item
        for item in instructor_config.get("instructors", [])
        if isinstance(item, dict)
    }

    rows = []
    for availability in availability_report["instructors"]:
        instructor_key = str(availability.get("instructor_key") or "")
        instructor = instructors.get(instructor_key, {})
        mode = str(availability.get("calendar_mode") or "")
        if mode == "inverse_blocking":
            rows.append(
                {
                    "instructor_key": instructor_key,
                    "calendar_mode": mode,
                    "candidates": [],
                    "skipped": [],
                    "blocking_windows": availability.get("blocking_events", []),
                    "warnings": [
                        "Brian inverse-blocking candidate generation requires a future configured search horizon/base candidate window."
                    ],
                }
            )
            continue
        candidates, skipped, warnings = build_explicit_candidates(availability, instructor, courses, rules)
        rows.append(
            {
                "instructor_key": instructor_key,
                "calendar_mode": mode,
                "source_hard_windows": availability.get("normalized_hard_windows", []),
                "source_soft_windows": availability.get("normalized_soft_windows", []),
                "candidates": candidates,
                "skipped": skipped,
                "blocking_windows": availability.get("unavailable_blocks", []),
                "warnings": warnings,
            }
        )

    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "source_mode": source_mode,
        "course_source": course_source,
        "fixture_loaded": availability_report.get("fixture_loaded"),
        "instructors": rows,
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Candidate Slot Report",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Report only: {report['report_only']}",
        f"- Public behavior changed: {report['public_behavior_changed']}",
        f"- Source mode: {report['source_mode']}",
        f"- Course source: {report['course_source']}",
        f"- Fixture loaded: {report['fixture_loaded']}",
        "",
    ]
    for item in report["instructors"]:
        lines.extend(
            [
                f"## {item['instructor_key']}",
                f"- Calendar mode: {item['calendar_mode']}",
                f"- Candidates: {len(item['candidates'])}",
                f"- Skipped records: {len(item['skipped'])}",
                f"- Blocking windows: {len(item['blocking_windows'])}",
                f"- Warnings: {len(item['warnings'])}",
                "",
            ]
        )
        if item.get("source_hard_windows"):
            lines.append("### Source HARD Windows")
            for window in item["source_hard_windows"]:
                lines.append(f"- {window['start']} to {window['end']}")
            lines.append("")
        if item.get("source_soft_windows"):
            lines.append("### Source SOFT Edge Windows")
            for window in item["source_soft_windows"]:
                lines.append(f"- {window['start']} to {window['end']}")
            lines.append("")
        if item["candidates"]:
            lines.append("### First Candidates")
            for candidate in item["candidates"][:12]:
                lines.append(
                    f"- {candidate['course_key']} ({candidate['source_window_type']}): "
                    f"{candidate['candidate_start']} to {candidate['candidate_end']} - {candidate['rule_reason']}"
                )
            lines.append("")
        for warning in item["warnings"]:
            lines.append(f"- Warning: {warning}")
        lines.append("")
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build report-only candidate slots from fixture or live calendar sources.")
    parser.add_argument("--source", choices=sorted(SOURCE_MODES), default="auto", help="Event source mode passed through to instructor availability ingestion.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report_payload(source_mode=args.source)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print("Candidate slot report generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
