#!/usr/bin/env python3
"""Validate executable stale offer suppressions without modifying public output."""

from __future__ import annotations

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
from scripts.build_stale_offer_suppression_candidates import (
    APPROVALS_PATH,
    SUPPRESSIBLE_ACTIONS,
    build_report as build_candidates_report,
)


REPORT_JSON_PATH = DEBUG_DIR / "stale_offer_suppression_execution_validation.json"
REPORT_MD_PATH = DEBUG_DIR / "stale_offer_suppression_execution_validation.md"


def blocked_reasons(candidate: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if candidate.get("enrollware_presence_status") != "missing_from_enrollware":
        reasons.append("enrollware_presence_status is not missing_from_enrollware")
    if candidate.get("recommended_action") not in SUPPRESSIBLE_ACTIONS:
        reasons.append("recommended_action is not suppressible")
    if candidate.get("suppression_approval_status") != "approved_for_suppression":
        reasons.append("suppression_approval_status is not approved_for_suppression")
    return reasons


def approval_action_mismatch(candidate: dict[str, Any]) -> bool:
    return (
        candidate.get("suppression_approval_status") == "approved_for_suppression"
        and candidate.get("recommended_action") not in SUPPRESSIBLE_ACTIONS
    )


def validation_record(candidate: dict[str, Any]) -> dict[str, Any]:
    reasons = blocked_reasons(candidate)
    return {
        "suppression_action_id": candidate.get("suppression_action_id"),
        "offer_id": candidate.get("offer_id"),
        "artifact_id": candidate.get("artifact_id"),
        "source_file": candidate.get("source_file"),
        "course_title": candidate.get("course_title"),
        "course_key": candidate.get("course_key"),
        "date": candidate.get("date"),
        "month": candidate.get("month"),
        "start_time": candidate.get("start_time"),
        "location": candidate.get("location"),
        "instructor": candidate.get("instructor"),
        "enrollware_presence_status": candidate.get("enrollware_presence_status"),
        "recommended_action": candidate.get("recommended_action"),
        "suppression_approval_status": candidate.get("suppression_approval_status"),
        "executable": not reasons,
        "blocked_reasons": reasons,
        "reason": candidate.get("reason"),
        "confidence": candidate.get("confidence"),
    }


def build_validation_report() -> dict[str, Any]:
    candidate_report = build_candidates_report()
    records = [validation_record(candidate) for candidate in candidate_report.get("candidates", [])]
    executable = [record for record in records if record["executable"]]
    blocked = [record for record in records if not record["executable"]]
    blocked_reason_counts = Counter(reason for record in blocked for reason in record["blocked_reasons"])
    source_counts = Counter(str(record.get("source_file") or "unknown") for record in records)
    course_counts = Counter(str(record.get("course_title") or record.get("course_key") or "unknown") for record in records)
    action_counts = Counter(str(record.get("recommended_action") or "unknown") for record in records)
    mismatch_blocks = [record for record in blocked if approval_action_mismatch(record)]
    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "approval_state_path": str(APPROVALS_PATH),
        "summary": {
            "total_suppression_candidates": len(records),
            "executable_suppressions": len(executable),
            "blocked_suppressions": len(blocked),
            "approval_action_mismatch_blocks": len(mismatch_blocks),
            "blocked_reason_counts": dict(sorted(blocked_reason_counts.items())),
            "by_source_file": dict(sorted(source_counts.items())),
            "by_course": dict(sorted(course_counts.items())),
            "by_action": dict(sorted(action_counts.items())),
            "default_zero_changes": len(executable) == 0,
        },
        "executable_suppressions": executable,
        "blocked_suppressions_sample": blocked[:250],
        "approval_action_mismatch_blocks": mismatch_blocks[:100],
        "local_proof_note": (
            "To prove the gate locally, temporarily add one suppression_action_id to "
            "data/state/stale_offer_suppression_approvals.json with "
            "suppression_approval_status=approved_for_suppression, run this validator, "
            "confirm executable_suppressions == 1, then restore the approval state."
        ),
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary = report["summary"]
    lines = [
        "# Stale Offer Suppression Execution Validation",
        "",
        "> DRY RUN ONLY - NO PUBLIC OFFER FILES MODIFIED",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Approval state: {report['approval_state_path']}",
        f"- Total suppression candidates: {summary['total_suppression_candidates']}",
        f"- Executable suppressions: {summary['executable_suppressions']}",
        f"- Blocked suppressions: {summary['blocked_suppressions']}",
        f"- Approval/action mismatch blocks: {summary['approval_action_mismatch_blocks']}",
        f"- Default zero changes: {summary['default_zero_changes']}",
        f"- By source file: {json.dumps(summary['by_source_file'], sort_keys=True)}",
        f"- By action: {json.dumps(summary['by_action'], sort_keys=True)}",
        "",
        "## Blocked Reason Summary",
        "",
    ]
    if not summary["blocked_reason_counts"]:
        lines.append("No blocked suppressions.")
    for reason, count in summary["blocked_reason_counts"].items():
        lines.append(f"- {reason}: {count}")

    lines.extend(["", "## Executable Suppressions", ""])
    if not report["executable_suppressions"]:
        lines.append("No stale offer suppressions are executable.")
    for item in report["executable_suppressions"][:100]:
        lines.append(f"- {item['suppression_action_id']} - {item.get('date')} {item.get('start_time') or ''} - {item.get('course_title')}")
        lines.append(f"  - Source: {item.get('source_file')}")

    lines.extend(["", "## Blocked Examples", ""])
    for item in report["blocked_suppressions_sample"][:30]:
        lines.append(f"- {item['suppression_action_id']} - {item.get('date')} {item.get('start_time') or ''} - {item.get('course_title')}")
        lines.append(f"  - Source: {item.get('source_file')}")
        lines.append(f"  - Approval: {item.get('suppression_approval_status')}")
        lines.append(f"  - Reasons: {', '.join(item['blocked_reasons'])}")

    lines.extend(["", "## Local Proof", "", report["local_proof_note"]])
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    report = build_validation_report()
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
