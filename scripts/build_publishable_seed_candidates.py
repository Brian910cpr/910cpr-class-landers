#!/usr/bin/env python3
"""Export report-only publishable seed candidates from the proposed seed review pipeline."""

from __future__ import annotations

import argparse
import hashlib
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
SEED_APPROVALS_PATH = ROOT / "data" / "state" / "seed_approvals.json"
ENROLLWARE_CURRENT_SESSIONS_PATH = ROOT / "data" / "sessions_current.json"
SUPPORTED_APPROVAL_STATUSES = {
    "needs_review",
    "approved_for_preview",
    "approved_for_public",
    "rejected",
    "hold",
}


def normalized_dt(value: Any) -> str | None:
    dt = parse_dt(value)
    return dt.isoformat() if dt else None


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


def load_approvals() -> dict[str, dict[str, Any]]:
    if not SEED_APPROVALS_PATH.exists():
        return {}
    config = load_json(SEED_APPROVALS_PATH)
    approvals: dict[str, dict[str, Any]] = {}
    for approval in config.get("approvals", []):
        if not isinstance(approval, dict):
            continue
        seed_id = str(approval.get("seed_id") or "")
        status = str(approval.get("approval_status") or "")
        if seed_id and status in SUPPORTED_APPROVAL_STATUSES:
            approvals[seed_id] = approval
    return approvals


def load_enrollware_presence_index() -> dict[str, Any]:
    if not ENROLLWARE_CURRENT_SESSIONS_PATH.exists():
        return {
            "source_path": str(ENROLLWARE_CURRENT_SESSIONS_PATH),
            "source_available": False,
            "source_status": "source_unavailable",
            "session_keys": set(),
            "session_count": 0,
        }
    config = load_json(ENROLLWARE_CURRENT_SESSIONS_PATH)
    session_keys: set[tuple[str, str, str]] = set()
    for session in config.get("sessions", []):
        if not isinstance(session, dict):
            continue
        course = session.get("course", {}) if isinstance(session.get("course"), dict) else {}
        course_id = str(course.get("course_id") or course.get("course_number") or session.get("course_id") or "")
        start = normalized_dt(session.get("start_datetime") or session.get("start"))
        end = normalized_dt(session.get("end_datetime") or session.get("end"))
        if course_id and start and end:
            session_keys.add((course_id, start, end))
    build = config.get("build") if isinstance(config.get("build"), dict) else {}
    return {
        "source_path": str(ENROLLWARE_CURRENT_SESSIONS_PATH),
        "source_available": True,
        "source_status": "loaded",
        "session_keys": session_keys,
        "session_count": len(session_keys),
        "generated_at": build.get("generated_at"),
    }


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


def seed_fingerprint(seed: dict[str, Any], row: dict[str, Any]) -> str:
    parts = [
        str(seed.get("instructor_key") or row.get("instructor_key") or ""),
        str(seed.get("course_key") or ""),
        str(seed.get("candidate_start") or ""),
        str(seed.get("candidate_end") or ""),
        str(seed.get("location_key") or ""),
        str(seed.get("registration_target_key") or ""),
    ]
    return "|".join(parts)


def seed_id_for(seed: dict[str, Any], row: dict[str, Any]) -> str:
    digest = hashlib.sha256(seed_fingerprint(seed, row).encode("utf-8")).hexdigest()[:16]
    return f"seed_{digest}"


def approval_for_seed(seed_id: str, approvals: dict[str, dict[str, Any]]) -> dict[str, Any]:
    approval = approvals.get(seed_id)
    if not approval:
        return {
            "approval_status": "needs_review",
            "approval_note": "Awaiting operator review.",
            "approved_by": None,
            "approved_at": None,
            "approval_source": "default",
        }
    return {
        "approval_status": approval.get("approval_status") or "needs_review",
        "approval_note": approval.get("approval_note") or "",
        "approved_by": approval.get("approved_by"),
        "approved_at": approval.get("approved_at"),
        "approval_source": approval.get("approval_source") or "seed_approvals.json",
    }


def enrollware_presence_for_seed(seed: dict[str, Any], target: dict[str, Any], presence_index: dict[str, Any]) -> dict[str, Any]:
    if not presence_index.get("source_available"):
        return {
            "enrollware_presence_status": "source_unavailable",
            "enrollware_presence_note": "Current Enrollware source data is unavailable; public readiness is blocked.",
            "enrollware_presence_source": presence_index.get("source_path"),
        }
    course_id = str(target.get("course_id") or "")
    start = normalized_dt(seed.get("candidate_start"))
    end = normalized_dt(seed.get("candidate_end"))
    if not course_id or not start or not end:
        return {
            "enrollware_presence_status": "not_checked",
            "enrollware_presence_note": "Missing course ID or candidate datetime; public readiness is blocked.",
            "enrollware_presence_source": presence_index.get("source_path"),
        }
    if (course_id, start, end) in presence_index.get("session_keys", set()):
        return {
            "enrollware_presence_status": "present_in_enrollware",
            "enrollware_presence_note": "Exact course ID and start/end match found in current Enrollware source data.",
            "enrollware_presence_source": presence_index.get("source_path"),
        }
    return {
        "enrollware_presence_status": "missing_from_enrollware",
        "enrollware_presence_note": "No exact course ID and start/end match found in current Enrollware source data; public readiness is blocked.",
        "enrollware_presence_source": presence_index.get("source_path"),
    }


def public_ready_block_reason(seed: dict[str, Any]) -> str | None:
    reasons: list[str] = []
    if seed.get("publishability_status") != "publishable_candidate":
        reasons.append("publishability_status is not publishable_candidate")
    if seed.get("approval_status") != "approved_for_public":
        reasons.append("approval_status is not approved_for_public")
    if seed.get("enrollware_presence_status") != "present_in_enrollware":
        reasons.append("enrollware_presence_status is not present_in_enrollware")
    return "; ".join(reasons) if reasons else None


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


def export_seed(
    row: dict[str, Any],
    seed: dict[str, Any],
    instructor_names: dict[str, str],
    target: dict[str, Any],
    approvals: dict[str, dict[str, Any]],
    presence_index: dict[str, Any],
) -> dict[str, Any]:
    instructor_key = str(seed.get("instructor_key") or row.get("instructor_key") or "")
    course_key = str(seed.get("course_key") or "")
    start = seed.get("candidate_start")
    end = seed.get("candidate_end")
    seed_id = seed_id_for(seed, row)
    approval = approval_for_seed(seed_id, approvals)
    presence = enrollware_presence_for_seed(seed, target, presence_index)
    public_ready = (
        seed.get("publishability_status") == "publishable_candidate"
        and approval["approval_status"] == "approved_for_public"
        and presence["enrollware_presence_status"] == "present_in_enrollware"
    )
    exported = {
        "seed_id": seed_id,
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
        "public_ready": public_ready,
        "approval_status": approval["approval_status"],
        "approval_note": approval["approval_note"],
        "approved_by": approval["approved_by"],
        "approved_at": approval["approved_at"],
        "approval_source": approval["approval_source"],
        "enrollware_presence_status": presence["enrollware_presence_status"],
        "enrollware_presence_note": presence["enrollware_presence_note"],
        "enrollware_presence_source": presence["enrollware_presence_source"],
        "rule_reason": seed.get("selection_reason") or seed.get("rule_reason"),
        "caution_flags": caution_flags(seed, row),
    }
    exported["public_ready_block_reason"] = None if public_ready else public_ready_block_reason(exported)
    return exported


def build_export(source_mode: str) -> dict[str, Any]:
    review = build_review(source_mode)
    instructor_names = load_instructor_names()
    targets_by_course = load_targets_by_course()
    approvals = load_approvals()
    presence_index = load_enrollware_presence_index()
    selected_pairs = iter_selected_seeds(review)

    exported: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []
    for row, seed in selected_pairs:
        course_key = str(seed.get("course_key") or "")
        target = targets_by_course.get(course_key)
        if is_publishable_export_seed(seed, target):
            exported.append(export_seed(row, seed, instructor_names, target or {}, approvals, presence_index))
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
    approval_counts = Counter(str(seed.get("approval_status") or "needs_review") for seed in exported)
    presence_counts = Counter(str(seed.get("enrollware_presence_status") or "not_checked") for seed in exported)
    omitted_by_reason = Counter(str(seed.get("publishability_status") or "unknown") for seed in omitted)

    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "do_not_create_classes_yet": True,
        "source_mode": source_mode,
        "enrollware_presence_source": {
            "path": presence_index.get("source_path"),
            "status": presence_index.get("source_status"),
            "session_count": presence_index.get("session_count", 0),
            "generated_at": presence_index.get("generated_at"),
        },
        "summary": {
            "total_selected_seeds": len(selected_pairs),
            "total_publishable_candidates_exported": len(exported),
            "blocked_seeds_omitted": len(omitted),
            "by_instructor": dict(sorted(by_instructor.items())),
            "by_course": dict(sorted(by_course.items())),
            "by_backend": dict(sorted(by_backend.items())),
            "approval_status_counts": {
                status: approval_counts.get(status, 0)
                for status in sorted(SUPPORTED_APPROVAL_STATUSES)
            },
            "public_ready_candidates": sum(1 for seed in exported if seed.get("public_ready")),
            "enrollware_presence_status_counts": {
                "present_in_enrollware": presence_counts.get("present_in_enrollware", 0),
                "missing_from_enrollware": presence_counts.get("missing_from_enrollware", 0),
                "not_checked": presence_counts.get("not_checked", 0),
                "source_unavailable": presence_counts.get("source_unavailable", 0),
            },
            "blocked_not_in_enrollware": sum(
                1
                for seed in exported
                if seed.get("enrollware_presence_status") != "present_in_enrollware"
            ),
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
        f"- Public-ready candidates: {report['summary']['public_ready_candidates']}",
        f"- Enrollware presence source: {report['enrollware_presence_source']['path']}",
        f"- Enrollware presence source status: {report['enrollware_presence_source']['status']}",
        "",
        "## Approval Summary",
        "",
        f"- Needs review: {report['summary']['approval_status_counts']['needs_review']}",
        f"- Approved for preview: {report['summary']['approval_status_counts']['approved_for_preview']}",
        f"- Approved for public: {report['summary']['approval_status_counts']['approved_for_public']}",
        f"- Rejected: {report['summary']['approval_status_counts']['rejected']}",
        f"- Hold: {report['summary']['approval_status_counts']['hold']}",
        "",
        "## Enrollware Presence Summary",
        "",
        f"- Present in Enrollware: {report['summary']['enrollware_presence_status_counts']['present_in_enrollware']}",
        f"- Missing from Enrollware: {report['summary']['enrollware_presence_status_counts']['missing_from_enrollware']}",
        f"- Not checked: {report['summary']['enrollware_presence_status_counts']['not_checked']}",
        f"- Source unavailable: {report['summary']['enrollware_presence_status_counts']['source_unavailable']}",
        f"- Blocked not in Enrollware: {report['summary']['blocked_not_in_enrollware']}",
        f"- Public ready: {report['summary']['public_ready_candidates']}",
        "",
    ]

    for instructor_key in sorted(grouped):
        lines.append(f"## {instructor_labels.get(instructor_key, instructor_key.title())}")
        for date in sorted(grouped[instructor_key]):
            lines.append(f"### {date_labels.get(date, date)}")
            for seed in sorted(grouped[instructor_key][date], key=lambda item: str(item.get("start_datetime") or "")):
                lines.append(f"- {seed['start_time']} - {seed['end_time']} - {seed['course_title']}")
                lines.append(f"  - Seed ID: {seed['seed_id']}")
                lines.append(f"  - Course key: {seed['course_key']}")
                lines.append(f"  - Source: {seed['source_type']}")
                lines.append(f"  - Location: {seed['location_key']}")
                lines.append(f"  - Registration target: {seed['registration_target_key']} / Enrollware course {seed['enrollware_course_id']}")
                lines.append(f"  - Approval: {seed['approval_status']} ({seed['approval_source']})")
                lines.append(f"  - Approval note: {seed['approval_note']}")
                lines.append(f"  - Enrollware presence: {seed['enrollware_presence_status']}")
                lines.append(f"  - Enrollware presence note: {seed['enrollware_presence_note']}")
                lines.append(f"  - Public ready: {seed['public_ready']}")
                lines.append(f"  - Public-ready block reason: {seed['public_ready_block_reason']}")
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
