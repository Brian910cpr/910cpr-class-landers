#!/usr/bin/env python3
"""Execute approved stale offer suppressions, gated and dry-run by default."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_instructor_availability_report import DEBUG_DIR, TZ
from scripts.validate_stale_offer_suppression_execution import build_validation_report


REPORT_JSON_PATH = DEBUG_DIR / "stale_offer_suppression_execution_report.json"
REPORT_MD_PATH = DEBUG_DIR / "stale_offer_suppression_execution_report.md"
PUBLIC_SCHEDULE_PATH = ROOT / "public_schedule.json"
CUSTOMER_FACING_OFFERS_PATH = ROOT / "docs" / "data" / "customer_facing_offers.json"
ALLOWED_WRITE_PATHS = {
    PUBLIC_SCHEDULE_PATH.resolve(),
    CUSTOMER_FACING_OFFERS_PATH.resolve(),
}
SUPPORTED_ACTIONS = {
    "remove_from_public_output",
    "suppress_until_enrollware_backed",
}


def extract_enrollware_id(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        text = str(value)
        match = re.search(r"(?:enroll\?id=|[?&]id=)(\d+)", text)
        if match:
            return match.group(1)
        if re.fullmatch(r"\d{6,}", text):
            return text
    return None


def artifact_session_id(action: dict[str, Any]) -> str | None:
    artifact = str(action.get("artifact_id") or "")
    if artifact.startswith("class:"):
        return artifact.split(":", 1)[1]
    return extract_enrollware_id(action.get("related_class_session_id"), action.get("offer_id"), action.get("artifact_id"))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def backup_file(path: Path, timestamp: str) -> Path:
    resolved = path.resolve()
    if resolved not in ALLOWED_WRITE_PATHS:
        raise ValueError(f"Refusing to back up unsupported path: {path}")
    relative = resolved.relative_to(ROOT)
    backup_path = ROOT / "data" / "backups" / "stale_offer_suppression" / timestamp / relative
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(resolved, backup_path)
    return backup_path


def group_executable_by_source(actions: list[dict[str, Any]]) -> dict[Path, list[dict[str, Any]]]:
    grouped: dict[Path, list[dict[str, Any]]] = defaultdict(list)
    for action in actions:
        source = Path(str(action.get("source_file") or ""))
        if not source.is_absolute():
            source = ROOT / source
        resolved = source.resolve()
        if resolved in ALLOWED_WRITE_PATHS:
            grouped[resolved].append(action)
    return grouped


def suppress_public_schedule(data: dict[str, Any], actions: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    target_ids = {artifact_session_id(action): action for action in actions if artifact_session_id(action)}
    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    new_sessions: list[dict[str, Any]] = []
    for session in data.get("sessions", []):
        if not isinstance(session, dict):
            new_sessions.append(session)
            continue
        session_enrollware_id = extract_enrollware_id(session.get("register_url"))
        action = target_ids.get(session_enrollware_id)
        if action:
            applied.append({**action, "matched_enrollware_id": session_enrollware_id})
            continue
        new_sessions.append(session)
    matched_ids = {item.get("matched_enrollware_id") for item in applied}
    for enrollware_id, action in target_ids.items():
        if enrollware_id not in matched_ids:
            skipped.append({**action, "skip_reason": "No exact public_schedule register_url Enrollware ID match found."})
    data = dict(data)
    data["sessions"] = new_sessions
    return data, applied, skipped


def offer_matches_action(offer: dict[str, Any], action: dict[str, Any]) -> bool:
    action_session_id = artifact_session_id(action)
    offer_session_id = extract_enrollware_id(offer.get("enrollware_class_id"), offer.get("enrollware_enroll_url"))
    if action_session_id and offer_session_id and action_session_id == offer_session_id:
        return True
    offer_id = str(action.get("offer_id") or "")
    return bool(
        offer_id
        and (
            offer_id == str(offer.get("offer_id") or "")
            or offer_id == str(offer.get("offer_slug") or "")
            or offer_id == str(offer.get("page_slug") or "")
        )
    )


def suppress_customer_facing_offers(data: dict[str, Any], actions: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    applied: list[dict[str, Any]] = []
    matched_action_ids: set[str] = set()
    new_courses: list[dict[str, Any]] = []
    for course in data.get("courses", []):
        if not isinstance(course, dict):
            new_courses.append(course)
            continue
        new_course = dict(course)
        new_options: list[dict[str, Any]] = []
        for offer in course.get("offered_options", []):
            if not isinstance(offer, dict):
                new_options.append(offer)
                continue
            action = next((candidate for candidate in actions if offer_matches_action(offer, candidate)), None)
            if action:
                applied.append(action)
                matched_action_ids.add(str(action.get("suppression_action_id")))
                continue
            new_options.append(offer)
        new_course["offered_options"] = new_options
        new_courses.append(new_course)
    skipped = [
        {**action, "skip_reason": "No exact customer_facing_offers offered_options match found."}
        for action in actions
        if str(action.get("suppression_action_id")) not in matched_action_ids
    ]
    data = dict(data)
    data["courses"] = new_courses
    return data, applied, skipped


def build_execution_report(mode: str) -> dict[str, Any]:
    validation = build_validation_report()
    executable = validation.get("executable_suppressions", [])
    blocked = validation.get("blocked_suppressions_sample", [])
    unsupported = [
        action
        for action in executable
        if action.get("recommended_action") not in SUPPORTED_ACTIONS
    ]
    executable_supported = [
        action
        for action in executable
        if action.get("recommended_action") in SUPPORTED_ACTIONS
    ]
    timestamp = datetime.now(TZ).strftime("%Y%m%d-%H%M%S")
    grouped = group_executable_by_source(executable_supported)
    actions_applied: list[dict[str, Any]] = []
    actions_skipped: list[dict[str, Any]] = []
    backup_paths: list[str] = []
    files_modified: list[str] = []

    if mode == "apply" and executable_supported:
        for path, actions in grouped.items():
            if path not in ALLOWED_WRITE_PATHS:
                actions_skipped.extend({**action, "skip_reason": "Unsupported source file."} for action in actions)
                continue
            backup_paths.append(str(backup_file(path, timestamp)))
            data = load_json(path)
            if path == PUBLIC_SCHEDULE_PATH.resolve():
                updated, applied, skipped = suppress_public_schedule(data, actions)
            elif path == CUSTOMER_FACING_OFFERS_PATH.resolve():
                updated, applied, skipped = suppress_customer_facing_offers(data, actions)
            else:
                updated, applied, skipped = data, [], [{**action, "skip_reason": "Unsupported source file."} for action in actions]
            if applied:
                write_json(path, updated)
                files_modified.append(str(path))
                actions_applied.extend(applied)
            else:
                actions_skipped.extend(skipped)

    if mode == "dry-run":
        actions_skipped.extend({**action, "skip_reason": "dry-run mode"} for action in executable_supported)
    elif mode == "apply" and not executable_supported:
        actions_skipped.extend({**action, "skip_reason": "unsupported action"} for action in unsupported)

    source_files_touched = sorted({str(Path(str(action.get("source_file"))).resolve()) for action in actions_applied})
    source_files_would_change = sorted(str(path) for path in grouped)
    public_files_changed = bool(files_modified)
    by_source = Counter(str(action.get("source_file") or "unknown") for action in executable_supported)

    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "mode": mode,
        "dry_run_only": mode == "dry-run",
        "public_behavior_changed": public_files_changed,
        "summary": {
            "executable_suppressions": len(executable),
            "supported_executable_suppressions": len(executable_supported),
            "actions_applied": len(actions_applied),
            "actions_skipped": len(actions_skipped),
            "unsupported_actions": len(unsupported),
            "blocked_suppressions": validation.get("summary", {}).get("blocked_suppressions", 0),
            "files_modified": len(files_modified),
            "public_files_changed": public_files_changed,
            "source_files_would_change": source_files_would_change,
            "executable_by_source_file": dict(sorted(by_source.items())),
        },
        "actions_applied": actions_applied,
        "actions_skipped": actions_skipped[:500],
        "unsupported_actions": unsupported,
        "blocked_suppressions_sample": blocked,
        "backup_paths": backup_paths,
        "files_modified": files_modified,
        "source_files_touched": source_files_touched,
        "safety_notes": [
            "Default mode is dry-run.",
            "--apply is required before any file modification.",
            "Zero approvals means zero executable suppressions and zero changes.",
            "Only public_schedule.json and docs/data/customer_facing_offers.json are supported in this pass.",
            "docs/*.html, class landers, live-schedule_future.json, CTAs, and Enrollware links are not modified.",
        ],
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary = report["summary"]
    lines = [
        "# Stale Offer Suppression Execution Report",
        "",
        "> GATED EXECUTOR - DEFAULT DRY RUN - PUBLIC FILES CHANGE ONLY WITH APPROVED EXECUTABLE SUPPRESSIONS AND --apply",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Mode: {report['mode']}",
        f"- Executable suppressions: {summary['executable_suppressions']}",
        f"- Supported executable suppressions: {summary['supported_executable_suppressions']}",
        f"- Actions applied: {summary['actions_applied']}",
        f"- Actions skipped: {summary['actions_skipped']}",
        f"- Unsupported actions: {summary['unsupported_actions']}",
        f"- Blocked suppressions: {summary['blocked_suppressions']}",
        f"- Files modified: {summary['files_modified']}",
        f"- Public files changed: {summary['public_files_changed']}",
        f"- Source files that would change: {json.dumps(summary['source_files_would_change'])}",
        "",
        "## Backups",
        "",
    ]
    if not report["backup_paths"]:
        lines.append("No backups created.")
    for path in report["backup_paths"]:
        lines.append(f"- {path}")

    lines.extend(["", "## Actions Applied", ""])
    if not report["actions_applied"]:
        lines.append("No actions applied.")
    for action in report["actions_applied"][:100]:
        lines.append(f"- {action.get('suppression_action_id')} - {action.get('source_file')} - {action.get('date')} {action.get('start_time') or ''}")

    lines.extend(["", "## Safety Notes", ""])
    lines.extend(f"- {note}" for note in report["safety_notes"])
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute approved stale offer suppressions.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Report what would change without modifying files.")
    mode.add_argument("--apply", action="store_true", help="Apply approved executable suppressions.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mode = "apply" if args.apply else "dry-run"
    report = build_execution_report(mode)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
