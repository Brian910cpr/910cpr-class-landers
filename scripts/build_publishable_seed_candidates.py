#!/usr/bin/env python3
"""Export report-only publishable seed candidates from the proposed seed review pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_instructor_availability_report import CONFIG_DIR, DEBUG_DIR, SOURCE_MODES, TZ, load_json, parse_dt
from scripts.build_proposed_seed_review import build_review, caution_flags, course_title, date_key, format_date, format_time


REPORT_JSON_PATH = DEBUG_DIR / "publishable_seed_candidates.json"
REPORT_MD_PATH = DEBUG_DIR / "publishable_seed_candidates.md"
INSTRUCTORS_PATH = CONFIG_DIR / "instructors.json"
REGISTRATION_TARGETS_PATH = CONFIG_DIR / "registration_targets.json"


def load_instructor_names() -> dict[str, str]:
    config = load_json(INSTRUCTORS_PATH)
    names: dict[str, str] = {}
    for instructor in config.get("instructors", []):
        if not isinstance(instructor, dict):
            continue
        key = str(instructor.get("instructor_key") or "")
        if key:
            names[key] = str(instructor.get("display_name") or key.title())
    return names


def load_targets_by_course() -> dict[str, dict[str, Any]]:
    config = load_json(REGISTRATION_TARGETS_PATH)
    targets: dict[str, dict[str, Any]] = {}
    for target in config.get("registration_targets", []):
        if not isinstance(target, dict):
            continue
        course_key = str(target.get("course_key") or "")
        if course_key:
            targets[course_key] = target
    return targets


def source_label(seed: dict[str, Any]) -> str:
    source = seed.get("source_window_type")
    if source == "BASE-HORIZON":
        return "Brian horizon"
    return str(source or "")


def is_publishable_export_seed(seed: dict[str, Any], target: dict[str, Any] | None) -> bool:
    return (
        seed.get("publishability_status") == "publishable_candidate"
        and seed.get("registration_status") == "known_enrollware_target"
        and seed.get("registration_backend") == "enrollware"
        and bool(target and target.get("active"))
    )


def iter_selected_seeds(review: dict[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    selected: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for row in review.get("instructors", []):
        if not isinstance(row, dict):
            continue
        for group in row.get("selected_by_date", []):
            if not isinstance(group, dict):
                continue
            for seed in group.get("seeds", []):
                if isinstance(seed, dict):
                    selected.append((row, seed))
    return selected


def export_seed(row: dict[str, Any], seed: dict[str, Any], instructor_names: dict[str, str], target: dict[str, Any]) -> dict[str, Any]:
    instructor_key = str(seed.get("instructor_key") or row.get("instructor_key") or "")
    course_key = str(seed.get("course_key") or "")
    start = seed.get("candidate_start")
    end = seed.get("candidate_end")
    return {
        "instructor_key": instructor_key,
        "instructor_display_name": instructor_names.get(instructor_key, instructor_key.title()),
        "course_key": course_key,
        "course_title": course_title(course_key),
        "start_datetime": start,
        "end_datetime": end,
        "date": date_key(start),
        "start_time": format_time(start),
        "end_time": format_time(end),
        "location_key": seed.get("location_key"),
        "source_type": source_label(seed),
        "registration_target_key": seed.get("registration_target_key"),
        "enrollware_course_id": target.get("course_id"),
        "publishability_status": seed.get("publishability_status"),
        "rule_reason": seed.get("selection_reason") or seed.get("rule_reason"),
        "caution_flags": caution_flags(seed, row),
    }


def build_export(source_mode: str) -> dict[str, Any]:
    review = build_review(source_mode)
    instructor_names = load_instructor_names()
    targets_by_course = load_targets_by_course()
    selected_pairs = iter_selected_seeds(review)

    exported: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []
    for row, seed in selected_pairs:
        course_key = str(seed.get("course_key") or "")
        target = targets_by_course.get(course_key)
        if is_publishable_export_seed(seed, target):
            exported.append(export_seed(row, seed, instructor_names, target or {}))
            continue
        omitted.append(
            {
                "instructor_key": seed.get("instructor_key") or row.get("instructor_key"),
                "course_key": course_key,
                "course_title": course_title(course_key),
                "candidate_start": seed.get("candidate_start"),
                "publishability_status": seed.get("publishability_status"),
                "registration_status": seed.get("registration_status"),
                "omit_reason": seed.get("publishability_note") or "Not a publishable candidate.",
            }
        )

    exported.sort(key=lambda item: (str(item.get("instructor_key") or ""), str(item.get("start_datetime") or ""), str(item.get("course_key") or "")))
    omitted.sort(key=lambda item: (str(item.get("instructor_key") or ""), str(item.get("candidate_start") or ""), str(item.get("course_key") or "")))

    by_instructor = Counter(str(seed.get("instructor_key") or "") for seed in exported)
    by_course = Counter(str(seed.get("course_key") or "") for seed in exported)
    by_backend = Counter("enrollware" for _ in exported)
    omitted_by_reason = Counter(str(seed.get("publishability_status") or "unknown") for seed in omitted)

    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "do_not_create_classes_yet": True,
        "source_mode": source_mode,
        "summary": {
            "total_selected_seeds": len(selected_pairs),
            "total_publishable_candidates_exported": len(exported),
            "blocked_seeds_omitted": len(omitted),
            "by_instructor": dict(sorted(by_instructor.items())),
            "by_course": dict(sorted(by_course.items())),
            "by_backend": dict(sorted(by_backend.items())),
            "omitted_by_reason": dict(sorted(omitted_by_reason.items())),
        },
        "publishable_seed_candidates": exported,
        "blocked_omitted": omitted,
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    instructor_labels: dict[str, str] = {}
    date_labels: dict[str, str] = {}
    for seed in report["publishable_seed_candidates"]:
        instructor_key = str(seed.get("instructor_key") or "")
        date = str(seed.get("date") or "9999-99-99")
        instructor_labels[instructor_key] = str(seed.get("instructor_display_name") or instructor_key.title())
        date_labels[date] = format_date(seed.get("start_datetime"))
        grouped[instructor_key][date].append(seed)

    lines = [
        "# Publishable Seed Candidates",
        "",
        "> REPORT ONLY - NOT PUBLIC - DO NOT CREATE CLASSES YET",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Source mode: {report['source_mode']}",
        f"- Total selected seeds: {report['summary']['total_selected_seeds']}",
        f"- Publishable candidates exported: {report['summary']['total_publishable_candidates_exported']}",
        f"- Blocked seeds omitted: {report['summary']['blocked_seeds_omitted']}",
        f"- By instructor: {json.dumps(report['summary']['by_instructor'], sort_keys=True)}",
        f"- By course: {json.dumps(report['summary']['by_course'], sort_keys=True)}",
        f"- By backend: {json.dumps(report['summary']['by_backend'], sort_keys=True)}",
        f"- Omitted by reason: {json.dumps(report['summary']['omitted_by_reason'], sort_keys=True)}",
        "",
    ]

    for instructor_key in sorted(grouped):
        lines.append(f"## {instructor_labels.get(instructor_key, instructor_key.title())}")
        for date in sorted(grouped[instructor_key]):
            lines.append(f"### {date_labels.get(date, date)}")
            for seed in sorted(grouped[instructor_key][date], key=lambda item: str(item.get("start_datetime") or "")):
                lines.append(f"- {seed['start_time']} - {seed['end_time']} - {seed['course_title']}")
                lines.append(f"  - Course key: {seed['course_key']}")
                lines.append(f"  - Source: {seed['source_type']}")
                lines.append(f"  - Location: {seed['location_key']}")
                lines.append(f"  - Registration target: {seed['registration_target_key']} / Enrollware course {seed['enrollware_course_id']}")
                lines.append(f"  - Rule reason: {seed['rule_reason']}")
                if seed["caution_flags"]:
                    lines.append(f"  - Caution flags: {', '.join(seed['caution_flags'])}")
            lines.append("")

    if not report["publishable_seed_candidates"]:
        lines.append("No publishable seed candidates were exported.")
        lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export report-only publishable seed candidates.")
    parser.add_argument("--source", choices=sorted(SOURCE_MODES), default="auto", help="Event source mode passed through to proposed seed review.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_export(args.source)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print("Publishable seed candidate export generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
