#!/usr/bin/env python3
"""Preview or apply approval-state changes for a stale offer suppression batch."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_instructor_availability_report import DEBUG_DIR, TZ
from scripts.build_stale_offer_suppression_batch_plan import build_report as build_batch_plan
from scripts.build_stale_offer_suppression_candidates import (
    APPROVALS_PATH,
    SUPPORTED_APPROVAL_STATUSES,
    SUPPRESSIBLE_ACTIONS,
    build_report as build_candidate_report,
)


REPORT_JSON_PATH = DEBUG_DIR / "stale_offer_batch_approval_preview.json"
REPORT_MD_PATH = DEBUG_DIR / "stale_offer_batch_approval_preview.md"
APPROVABLE_EXISTING_STATUSES = {"needs_review", "approved_for_suppression"}
BLOCKING_EXISTING_STATUSES = {"hold", "rejected"}


def load_approval_state() -> dict[str, Any]:
    if not APPROVALS_PATH.exists():
        return {
            "schema_version": "0.1",
            "supported_statuses": sorted(SUPPORTED_APPROVAL_STATUSES),
            "approvals": [],
        }
    return json.loads(APPROVALS_PATH.read_text(encoding="utf-8"))


def write_approval_state(state: dict[str, Any]) -> None:
    APPROVALS_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def candidate_lookup() -> dict[str, dict[str, Any]]:
    report = build_candidate_report()
    return {
        str(candidate.get("suppression_action_id")): candidate
        for candidate in report.get("candidates", [])
        if candidate.get("suppression_action_id")
    }


def approval_lookup(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("suppression_action_id")): item
        for item in state.get("approvals", [])
        if isinstance(item, dict) and item.get("suppression_action_id")
    }


def find_batch(batch_id: str) -> dict[str, Any] | None:
    plan = build_batch_plan()
    for batch in plan.get("batches", []):
        if batch.get("batch_id") == batch_id:
            return batch
    return None


def validate_batch(batch: dict[str, Any], candidates: dict[str, dict[str, Any]], allow_mixed_confidence: bool) -> tuple[list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    selected: list[dict[str, Any]] = []
    if batch.get("confidence_level") != "high" and not allow_mixed_confidence:
        errors.append("Batch is not high confidence; pass --allow-mixed-confidence for dry-run/apply consideration.")
    if batch.get("risk_level") not in {"low", "medium"} and not allow_mixed_confidence:
        errors.append("Batch risk level is not low/medium; pass --allow-mixed-confidence for dry-run/apply consideration.")

    for action_id in batch.get("example_suppression_action_ids", []):
        candidate = candidates.get(str(action_id))
        if candidate:
            selected.append(candidate)
    # Use the full candidates embedded in the batch when examples are truncated.
    for item in batch.get("candidates", []):
        action_id = str(item.get("suppression_action_id") or "")
        candidate = candidates.get(action_id)
        if candidate and candidate not in selected:
            selected.append(candidate)

    if not selected:
        errors.append("Batch contains no candidate suppression_action_ids.")

    for candidate in selected:
        if candidate.get("enrollware_presence_status") != "missing_from_enrollware":
            errors.append(f"{candidate.get('suppression_action_id')} is not missing_from_enrollware.")
        if candidate.get("recommended_action") not in SUPPRESSIBLE_ACTIONS:
            errors.append(f"{candidate.get('suppression_action_id')} has unsupported recommended_action {candidate.get('recommended_action')}.")
        if candidate.get("suppression_approval_status") in BLOCKING_EXISTING_STATUSES:
            errors.append(f"{candidate.get('suppression_action_id')} is {candidate.get('suppression_approval_status')} and cannot be batch-approved.")
    return errors, selected


def predicted_executable_count(selected: list[dict[str, Any]], existing_approvals: dict[str, dict[str, Any]]) -> int:
    count = 0
    for candidate in selected:
        action_id = str(candidate.get("suppression_action_id") or "")
        existing = existing_approvals.get(action_id)
        status = existing.get("suppression_approval_status") if existing else candidate.get("suppression_approval_status")
        predicted_status = "approved_for_suppression" if status in APPROVABLE_EXISTING_STATUSES else status
        if (
            candidate.get("enrollware_presence_status") == "missing_from_enrollware"
            and candidate.get("recommended_action") in SUPPRESSIBLE_ACTIONS
            and predicted_status == "approved_for_suppression"
        ):
            count += 1
    return count


def build_preview(batch_id: str, mode: str, allow_mixed_confidence: bool) -> dict[str, Any]:
    batch = find_batch(batch_id)
    if not batch:
        return {
            "generated_at": datetime.now(TZ).isoformat(),
            "mode": mode,
            "batch_id": batch_id,
            "dry_run": mode == "dry-run",
            "approval_state_changed": False,
            "validation_passed": False,
            "errors": [f"Unknown batch_id: {batch_id}"],
            "summary": {
                "would_approve_count": 0,
                "resulting_executable_count_if_applied": 0,
            },
            "candidates": [],
        }

    candidates = candidate_lookup()
    state = load_approval_state()
    existing_approvals = approval_lookup(state)
    errors, selected = validate_batch(batch, candidates, allow_mixed_confidence)
    current_status_counts = Counter(str(item.get("suppression_approval_status") or "needs_review") for item in selected)
    source_counts = Counter(str(item.get("source_file") or "unknown") for item in selected)
    course_counts = Counter(str(item.get("course_title") or item.get("course_key") or "unknown") for item in selected)
    date_values = sorted(str(item.get("date") or "") for item in selected if item.get("date"))
    would_approve = [
        item
        for item in selected
        if item.get("suppression_approval_status") in APPROVABLE_EXISTING_STATUSES
    ]
    blocked_existing = [
        item
        for item in selected
        if item.get("suppression_approval_status") in BLOCKING_EXISTING_STATUSES
    ]
    preview = {
        "generated_at": datetime.now(TZ).isoformat(),
        "mode": mode,
        "batch_id": batch_id,
        "batch_name": batch.get("batch_name"),
        "dry_run": mode == "dry-run",
        "approval_state_path": str(APPROVALS_PATH),
        "approval_state_changed": False,
        "validation_passed": not errors,
        "errors": errors,
        "batch": {
            "candidate_count": batch.get("candidate_count"),
            "confidence_level": batch.get("confidence_level"),
            "risk_level": batch.get("risk_level"),
            "source_files_affected": batch.get("source_files_affected"),
            "recommended_action_breakdown": batch.get("recommended_action_breakdown"),
        },
        "summary": {
            "would_approve_count": len(would_approve) if not errors else 0,
            "blocked_existing_hold_or_rejected": len(blocked_existing),
            "current_approval_statuses": dict(sorted(current_status_counts.items())),
            "source_files_affected": dict(sorted(source_counts.items())),
            "course_breakdown": dict(sorted(course_counts.items())),
            "date_range": {
                "start_date": date_values[0] if date_values else None,
                "end_date": date_values[-1] if date_values else None,
            },
            "resulting_executable_count_if_applied": predicted_executable_count(selected, existing_approvals) if not errors else 0,
        },
        "suppression_action_ids_to_approve": [str(item.get("suppression_action_id")) for item in would_approve] if not errors else [],
        "candidates": selected,
        "operator_note": "Dry-run does not modify approval state. Apply mode mutates only data/state/stale_offer_suppression_approvals.json.",
    }
    return preview


def apply_preview(preview: dict[str, Any]) -> dict[str, Any]:
    if not preview.get("validation_passed"):
        return preview
    state = load_approval_state()
    approvals = approval_lookup(state)
    now = datetime.now(TZ).isoformat()
    batch_id = str(preview.get("batch_id"))
    for action_id in preview.get("suppression_action_ids_to_approve", []):
        approvals[action_id] = {
            "suppression_action_id": action_id,
            "suppression_approval_status": "approved_for_suppression",
            "approved_by": "brian",
            "approved_at": now,
            "approval_note": f"approved batch {batch_id}",
        }
    state = copy.deepcopy(state)
    state["approvals"] = sorted(approvals.values(), key=lambda item: str(item.get("suppression_action_id") or ""))
    write_approval_state(state)
    preview["approval_state_changed"] = True
    preview["applied_at"] = now
    return preview


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary = report.get("summary", {})
    lines = [
        "# Stale Offer Batch Approval Preview",
        "",
        "> DEFAULT DRY RUN - DOES NOT SUPPRESS PUBLIC OFFERS OR RUN THE EXECUTOR",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Mode: {report['mode']}",
        f"- Batch ID: {report['batch_id']}",
        f"- Batch name: {report.get('batch_name')}",
        f"- Validation passed: {report.get('validation_passed')}",
        f"- Approval state changed: {report.get('approval_state_changed')}",
        f"- Would approve: {summary.get('would_approve_count')}",
        f"- Resulting executable count if applied: {summary.get('resulting_executable_count_if_applied')}",
        f"- Current approval statuses: {json.dumps(summary.get('current_approval_statuses', {}), sort_keys=True)}",
        f"- Source files affected: {json.dumps(summary.get('source_files_affected', {}), sort_keys=True)}",
        f"- Date range: {json.dumps(summary.get('date_range', {}), sort_keys=True)}",
        "",
    ]
    if report.get("errors"):
        lines.append("## Errors")
        lines.extend(f"- {error}" for error in report["errors"])
        lines.append("")

    lines.extend(["## Suppression IDs To Approve", ""])
    if not report.get("suppression_action_ids_to_approve"):
        lines.append("No suppression_action_ids would be approved.")
    for action_id in report.get("suppression_action_ids_to_approve", []):
        lines.append(f"- {action_id}")

    lines.extend(["", "## Operator Next Steps", ""])
    lines.append("- Run validator: `python scripts/validate_stale_offer_suppression_execution.py`")
    lines.append("- Run executor dry-run: `python scripts/execute_stale_offer_suppression.py --dry-run`")
    lines.append("- Apply suppressions only after review: `python scripts/execute_stale_offer_suppression.py --apply`")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview or apply stale offer suppression batch approvals.")
    parser.add_argument("--batch-id", required=True, help="Batch ID from stale offer suppression batch plan.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview approval changes without mutating state.")
    mode.add_argument("--apply", action="store_true", help="Apply approval changes for the selected batch.")
    parser.add_argument("--allow-mixed-confidence", action="store_true", help="Allow mixed-confidence or higher-risk batches.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mode = "apply" if args.apply else "dry-run"
    report = build_preview(args.batch_id, mode, args.allow_mixed_confidence)
    if mode == "apply":
        report = apply_preview(report)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0 if report.get("validation_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
