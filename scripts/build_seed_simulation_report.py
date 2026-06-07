#!/usr/bin/env python3
"""Build report-only seed proposals from candidate slots."""

from __future__ import annotations

import json
import sys
import argparse
from collections import Counter
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
SEED_SELECTION_RULES_PATH = CONFIG_DIR / "seed_selection_rules.json"


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


def load_seed_selection_rules() -> dict[str, dict[str, Any]]:
    if not SEED_SELECTION_RULES_PATH.exists():
        return {}
    payload = load_json(SEED_SELECTION_RULES_PATH)
    return {
        str(rule.get("instructor_key") or ""): rule
        for rule in payload.get("seed_selection_rules", [])
        if isinstance(rule, dict) and rule.get("active") and rule.get("report_only") and str(rule.get("instructor_key") or "")
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


def candidate_day(candidate: dict[str, Any]) -> str:
    start = parse_dt(candidate.get("candidate_start"))
    return start.date().isoformat() if start else ""


def first_candidate_day(candidates: list[dict[str, Any]]) -> datetime | None:
    starts = [parse_dt(candidate.get("candidate_start")) for candidate in candidates]
    starts = [start for start in starts if start]
    return min(starts) if starts else None


def within_selection_window(candidate: dict[str, Any], start: datetime | None, window_days: int) -> bool:
    candidate_start = parse_dt(candidate.get("candidate_start"))
    if not candidate_start or not start or window_days <= 0:
        return True
    return (candidate_start.date() - start.date()).days < window_days


def lower_demand_too_soon(candidate: dict[str, Any], start: datetime | None, rule: dict[str, Any]) -> bool:
    course_key = str(candidate.get("course_key") or "")
    lower = {str(item) for item in rule.get("lower_demand_course_keys", [])}
    if course_key not in lower:
        return False
    candidate_start = parse_dt(candidate.get("candidate_start"))
    not_before = int(rule.get("lower_demand_not_before_day") or 0)
    if not candidate_start or not start or not_before <= 0:
        return False
    return (candidate_start.date() - start.date()).days < not_before


def skip_candidate(candidate: dict[str, Any], reason: str, conflict_avoided: bool = False) -> dict[str, Any]:
    skipped = dict(candidate)
    skipped["skipped_reason"] = reason
    skipped["conflict_avoided"] = conflict_avoided
    return skipped


def simulate_instructor(
    row: dict[str, Any],
    instructor: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    selection_rules: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    instructor_key = str(row.get("instructor_key") or "")
    mode = str(row.get("calendar_mode") or "")
    if mode == "inverse_blocking" and not row.get("candidates"):
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
            "base_candidate_windows": row.get("base_candidate_windows", []),
            "windows_removed_or_trimmed_by_blocks": row.get("windows_removed_or_trimmed_by_blocks", []),
            "final_usable_windows": row.get("final_usable_windows", []),
        }

    rule_key = str(instructor.get("priority_rule_key") or "")
    rule = rules.get(rule_key, {})
    selection_rule = selection_rules.get(instructor_key, {})
    priority_order = [str(item) for item in selection_rule.get("priority_course_order", [])] or [str(item) for item in rule.get("priority_order", [])]
    candidates = sorted(row.get("candidates", []), key=lambda item: candidate_sort_key(item, priority_order))
    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    selected_by_day: Counter[str] = Counter()
    selected_by_course: Counter[str] = Counter()
    selected_course_days: set[tuple[str, str]] = set()
    selection_window_start = first_candidate_day(candidates)
    max_per_day = int(selection_rule.get("max_selected_seed_stacks_per_day") or 999999)
    max_per_window = int(selection_rule.get("max_selected_seed_proposals_per_window") or 999999)
    max_per_course = int(selection_rule.get("max_selected_per_course_per_window") or 999999)
    window_days = int(selection_rule.get("window_days") or 0)
    avoid_duplicate = bool(selection_rule.get("avoid_duplicate_same_course_same_day", True))
    soft_policy = str(selection_rule.get("soft_policy") or "")

    for candidate in candidates:
        day = candidate_day(candidate)
        course_key = str(candidate.get("course_key") or "")
        if not within_selection_window(candidate, selection_window_start, window_days):
            skipped.append(skip_candidate(candidate, f"outside {window_days}-day seed selection window"))
            continue
        if len(selected) >= max_per_window:
            skipped.append(skip_candidate(candidate, f"selection window cap reached ({max_per_window})"))
            continue
        if selected_by_day[day] >= max_per_day:
            skipped.append(skip_candidate(candidate, f"daily seed stack cap reached for {day} ({max_per_day})"))
            continue
        if selected_by_course[course_key] >= max_per_course:
            skipped.append(skip_candidate(candidate, f"per-course selection cap reached for {course_key} ({max_per_course})"))
            continue
        if avoid_duplicate and (course_key, day) in selected_course_days:
            skipped.append(skip_candidate(candidate, f"duplicate same-course seed suppressed for {course_key} on {day}"))
            continue
        if candidate.get("source_window_type") == "SOFT-supported" and soft_policy == "skills_or_stack_support_only":
            is_skills = "heartcode" in course_key or "skills" in course_key
            if not is_skills:
                skipped.append(skip_candidate(candidate, "SOFT policy allows only skills/HeartCode stack support"))
                continue
        if lower_demand_too_soon(candidate, selection_window_start, selection_rule):
            skipped.append(skip_candidate(candidate, "lower-demand course deferred beyond near-term selection window"))
            continue
        conflict = next((item for item in selected if overlaps(candidate, item)), None)
        if conflict:
            skipped.append(skip_candidate(
                candidate,
                "overlaps selected seed "
                f"{conflict.get('course_key')} {conflict.get('candidate_start')} to {conflict.get('candidate_end')}",
                conflict_avoided=True,
            ))
            continue
        selected_record = dict(candidate)
        selected_record["selection_reason"] = (
            f"{selection_rule.get('selection_rule_key') or rule_key}: selected by configured thinning controls"
        )
        selected_record["conflict_avoided"] = False
        selected_record["stack_group_key"] = f"{instructor_key}:{day}:{len(selected_by_day) + 1}"
        selected.append(selected_record)
        selected_by_day[day] += 1
        selected_by_course[course_key] += 1
        selected_course_days.add((course_key, day))

    for candidate in row.get("skipped", []):
        skipped_record = dict(candidate)
        skipped_record["conflict_avoided"] = False
        skipped.append(skipped_record)

    return {
        "instructor_key": instructor_key,
        "calendar_mode": mode,
        "priority_rule_key": rule_key,
        "selection_rule_key": selection_rule.get("selection_rule_key"),
        "candidate_count": len(row.get("candidates", [])),
        "unthinned_selected_count": len(row.get("final_usable_windows", [])) if row.get("calendar_mode") == "inverse_blocking" else len(row.get("candidates", [])),
        "selected_seed_proposals": selected,
        "skipped_candidates": skipped,
        "skip_reason_counts": dict(Counter(str(item.get("skipped_reason") or "unspecified") for item in skipped)),
        "warnings": row.get("warnings", []),
        "blocking_windows": row.get("blocking_windows", []),
        "base_candidate_windows": row.get("base_candidate_windows", []),
        "windows_removed_or_trimmed_by_blocks": row.get("windows_removed_or_trimmed_by_blocks", []),
        "final_usable_windows": row.get("final_usable_windows", []),
    }


def build_report_payload(source_mode: str = "auto") -> dict[str, Any]:
    load_json(CONFIG_DIR / "course_options.json")
    load_json(CONFIG_DIR / "locations.json")
    if (CONFIG_DIR / "courses.json").exists():
        load_json(CONFIG_DIR / "courses.json")

    candidate_report = build_candidate_report_payload(source_mode=source_mode)
    instructors = load_instructors()
    rules = load_rules()
    selection_rules = load_seed_selection_rules()
    rows = []
    for row in candidate_report["instructors"]:
        instructor_key = str(row.get("instructor_key") or "")
        rows.append(simulate_instructor(row, instructors.get(instructor_key, {}), rules, selection_rules))

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
                f"- Unthinned selected count: {row.get('unthinned_selected_count')}",
                f"- Selected seed proposals: {len(row['selected_seed_proposals'])}",
                f"- Skipped candidates: {len(row['skipped_candidates'])}",
                f"- Base candidate windows: {len(row.get('base_candidate_windows', []))}",
                f"- Windows removed/trimmed by blocks: {len(row.get('windows_removed_or_trimmed_by_blocks', []))}",
                f"- Final usable windows: {len(row.get('final_usable_windows', []))}",
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
            if row.get("skip_reason_counts"):
                lines.append("### Skip Reason Counts")
                for reason, count in sorted(row["skip_reason_counts"].items(), key=lambda item: (-item[1], item[0])):
                    lines.append(f"- {reason}: {count}")
                lines.append("")
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
