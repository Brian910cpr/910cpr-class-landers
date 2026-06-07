#!/usr/bin/env python3
"""Validate dry-run executable cleanup actions without modifying public output."""

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
from scripts.build_public_artifact_cleanup_plan import APPROVALS_PATH, build_cleanup_plan


REPORT_JSON_PATH = DEBUG_DIR / "public_artifact_cleanup_execution_validation.json"
REPORT_MD_PATH = DEBUG_DIR / "public_artifact_cleanup_execution_validation.md"


def approval_count() -> int:
    if not APPROVALS_PATH.exists():
        return 0
    data = json.loads(APPROVALS_PATH.read_text(encoding="utf-8"))
    return len([item for item in data.get("approvals", []) if isinstance(item, dict)])


def file_path_block(item: dict[str, Any]) -> bool:
    if item.get("proposed_action") not in {
        "redirect_class_lander_to_hub",
        "archive_class_lander",
        "remove_class_lander",
        "suppress_schedule_offer",
    }:
        return False
    path_value = item.get("current_file_path")
    return not path_value or not Path(str(path_value)).exists()


def approval_action_mismatch(item: dict[str, Any]) -> bool:
    approval = item.get("cleanup_approval_status")
    action = item.get("proposed_action")
    if approval == "approved_for_redirect":
        return action != "redirect_class_lander_to_hub"
    if approval == "approved_for_suppression":
        return action != "suppress_schedule_offer"
    if approval == "approved_for_archive":
        return action not in {"archive_class_lander", "remove_class_lander"}
    return False


def source_unavailable_block(item: dict[str, Any]) -> bool:
    return item.get("enrollware_backing_status") == "unknown"


def validation_record(item: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if item.get("cleanup_action_block_reason"):
        reasons.append(str(item["cleanup_action_block_reason"]))
    if item.get("destination_needs_review"):
        reasons.append("destination_needs_review is true")
    if approval_action_mismatch(item):
        reasons.append("approval status does not match proposed action")
    if file_path_block(item):
        reasons.append("current file/source path is missing")
    if source_unavailable_block(item):
        reasons.append("source is unavailable or backing status is unknown")
    return {
        "cleanup_action_id": item.get("cleanup_action_id"),
        "artifact_id": item.get("artifact_id"),
        "proposed_action": item.get("proposed_action"),
        "current_file_path": item.get("current_file_path"),
        "destination_hub": item.get("destination_hub"),
        "destination_needs_review": item.get("destination_needs_review"),
        "cleanup_approval_status": item.get("cleanup_approval_status"),
        "enrollware_backing_status": item.get("enrollware_backing_status"),
        "executable": bool(item.get("cleanup_action_executable")),
        "blocked_reasons": reasons,
    }


def build_validation_report() -> dict[str, Any]:
    plan = build_cleanup_plan()
    records = [validation_record(item) for item in plan.get("cleanup_items", [])]
    executable = [record for record in records if record["executable"]]
    blocked = [record for record in records if not record["executable"]]
    blocked_reason_counts = Counter(reason for record in blocked for reason in record["blocked_reasons"])
    fallback_redirects_blocked = [
        record
        for record in blocked
        if record.get("proposed_action") == "redirect_class_lander_to_hub"
        and record.get("destination_hub") == "/index.html"
        and record.get("destination_needs_review") is True
    ]
    mismatch_blocks = [record for record in blocked if "approval status does not match proposed action" in record["blocked_reasons"]]
    destination_review_blocks = [record for record in blocked if "destination_needs_review is true" in record["blocked_reasons"]]
    missing_file_blocks = [record for record in blocked if "current file/source path is missing" in record["blocked_reasons"]]
    source_unavailable_blocks = [record for record in blocked if "source is unavailable or backing status is unknown" in record["blocked_reasons"]]
    approvals = approval_count()
    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "dry_run_only": True,
        "public_behavior_changed": False,
        "approval_state_path": str(APPROVALS_PATH),
        "approval_record_count": approvals,
        "summary": {
            "total_cleanup_actions": len(records),
            "executable_actions": len(executable),
            "blocked_actions": len(blocked),
            "fallback_redirects_blocked": len(fallback_redirects_blocked),
            "approval_action_mismatch_blocks": len(mismatch_blocks),
            "destination_needs_review_blocks": len(destination_review_blocks),
            "missing_file_path_blocks": len(missing_file_blocks),
            "source_unavailable_blocks": len(source_unavailable_blocks),
            "no_approvals_all_blocked": approvals == 0 and len(executable) == 0,
            "public_output_remains_unmodified_by_script": True,
            "blocked_reason_counts": dict(sorted(blocked_reason_counts.items())),
        },
        "executable_actions": executable,
        "blocked_actions_sample": blocked[:200],
        "fallback_redirects_blocked_sample": fallback_redirects_blocked[:100],
        "approval_action_mismatch_blocks": mismatch_blocks[:100],
        "destination_needs_review_blocks": destination_review_blocks[:100],
        "missing_file_path_blocks": missing_file_blocks[:100],
        "source_unavailable_blocks": source_unavailable_blocks[:100],
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Public Artifact Cleanup Execution Validation",
        "",
        "> DRY RUN ONLY - NO PUBLIC FILES MODIFIED",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Approval state: {report['approval_state_path']}",
        f"- Approval records: {report['approval_record_count']}",
        f"- Total cleanup actions: {report['summary']['total_cleanup_actions']}",
        f"- Executable actions: {report['summary']['executable_actions']}",
        f"- Blocked actions: {report['summary']['blocked_actions']}",
        f"- Fallback redirects blocked: {report['summary']['fallback_redirects_blocked']}",
        f"- Approval/action mismatch blocks: {report['summary']['approval_action_mismatch_blocks']}",
        f"- Destination needs review blocks: {report['summary']['destination_needs_review_blocks']}",
        f"- Missing file/path blocks: {report['summary']['missing_file_path_blocks']}",
        f"- Source unavailable blocks: {report['summary']['source_unavailable_blocks']}",
        f"- No approvals all blocked: {report['summary']['no_approvals_all_blocked']}",
        "",
        "## Blocked Reason Summary",
        "",
    ]
    if not report["summary"]["blocked_reason_counts"]:
        lines.append("No blocked reasons.")
    for reason, count in report["summary"]["blocked_reason_counts"].items():
        lines.append(f"- {reason}: {count}")

    lines.extend(["", "## Executable Actions", ""])
    if not report["executable_actions"]:
        lines.append("No cleanup actions are executable.")
    for item in report["executable_actions"][:100]:
        lines.append(f"- {item['cleanup_action_id']} - {item['artifact_id']} - {item['proposed_action']}")

    lines.extend(["", "## Blocked Fallback Redirect Examples", ""])
    if not report["fallback_redirects_blocked_sample"]:
        lines.append("No blocked fallback redirects.")
    for item in report["fallback_redirects_blocked_sample"][:20]:
        lines.append(f"- {item['cleanup_action_id']} - {item['artifact_id']} -> {item['destination_hub']}")
        lines.append(f"  - Reasons: {', '.join(item['blocked_reasons'])}")

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
