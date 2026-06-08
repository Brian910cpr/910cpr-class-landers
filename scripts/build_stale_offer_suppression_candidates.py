#!/usr/bin/env python3
"""Build approval-gated suppression candidates for stale Lander offers."""

from __future__ import annotations

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

from scripts.build_instructor_availability_report import DEBUG_DIR, TZ
from scripts.build_stale_offer_review_report import build_review_report


REPORT_JSON_PATH = DEBUG_DIR / "stale_offer_suppression_candidates.json"
REPORT_MD_PATH = DEBUG_DIR / "stale_offer_suppression_candidates.md"
APPROVALS_PATH = ROOT / "data" / "state" / "stale_offer_suppression_approvals.json"
SUPPORTED_APPROVAL_STATUSES = {
    "needs_review",
    "approved_for_suppression",
    "hold",
    "rejected",
}
SUPPRESSIBLE_ACTIONS = {
    "remove_from_public_output",
    "suppress_until_enrollware_backed",
}


def norm(value: Any) -> str:
    return str(value or "").strip()


def month_key(value: Any) -> str:
    text = norm(value)
    return text[:7] if len(text) >= 7 else "unknown"


def suppression_fingerprint(offer: dict[str, Any]) -> str:
    return "|".join(
        [
            norm(offer.get("source_file")),
            norm(offer.get("offer_id") or offer.get("artifact_id")),
            norm(offer.get("course_key") or offer.get("course_title")),
            norm(offer.get("date")),
            norm(offer.get("start_time")),
            norm(offer.get("recommended_action")),
        ]
    )


def suppression_action_id_for(offer: dict[str, Any]) -> str:
    digest = hashlib.sha256(suppression_fingerprint(offer).encode("utf-8")).hexdigest()[:16]
    return f"suppress_{digest}"


def load_approvals() -> dict[str, dict[str, Any]]:
    if not APPROVALS_PATH.exists():
        return {}
    data = json.loads(APPROVALS_PATH.read_text(encoding="utf-8"))
    approvals: dict[str, dict[str, Any]] = {}
    for approval in data.get("approvals", []):
        if not isinstance(approval, dict):
            continue
        action_id = norm(approval.get("suppression_action_id"))
        status = norm(approval.get("suppression_approval_status"))
        if action_id and status in SUPPORTED_APPROVAL_STATUSES:
            approvals[action_id] = approval
    return approvals


def approval_for(action_id: str, approvals: dict[str, dict[str, Any]]) -> dict[str, Any]:
    approval = approvals.get(action_id)
    if not approval:
        return {
            "suppression_approval_status": "needs_review",
            "approved_by": None,
            "approved_at": None,
            "approval_note": "Awaiting operator review.",
            "approval_source": "default",
        }
    return {
        "suppression_approval_status": approval.get("suppression_approval_status") or "needs_review",
        "approved_by": approval.get("approved_by"),
        "approved_at": approval.get("approved_at"),
        "approval_note": approval.get("approval_note") or "",
        "approval_source": "stale_offer_suppression_approvals.json",
    }


def executable_for(candidate: dict[str, Any]) -> bool:
    return (
        candidate.get("enrollware_presence_status") == "missing_from_enrollware"
        and candidate.get("recommended_action") in SUPPRESSIBLE_ACTIONS
        and candidate.get("suppression_approval_status") == "approved_for_suppression"
    )


def build_candidate(offer: dict[str, Any], approvals: dict[str, dict[str, Any]]) -> dict[str, Any]:
    action_id = suppression_action_id_for(offer)
    approval = approval_for(action_id, approvals)
    candidate = {
        "suppression_action_id": action_id,
        "offer_id": offer.get("offer_id"),
        "artifact_id": offer.get("artifact_id"),
        "source_file": offer.get("source_file"),
        "source_type": offer.get("source_type"),
        "course_title": offer.get("course_title"),
        "course_key": offer.get("course_key"),
        "date": offer.get("date"),
        "month": month_key(offer.get("date")),
        "start_time": offer.get("start_time"),
        "location": offer.get("location"),
        "instructor": offer.get("instructor"),
        "enrollware_presence_status": offer.get("enrollware_presence_status"),
        "recommended_action": offer.get("recommended_action"),
        "reason": offer.get("reason"),
        "confidence": offer.get("confidence"),
        "related_class_session_id": offer.get("related_class_session_id"),
        "public_artifact_type": offer.get("public_artifact_type"),
        "sister_conflict_group": offer.get("sister_conflict_group"),
        **approval,
    }
    candidate["executable"] = executable_for(candidate)
    candidate["executable_reason"] = (
        "Approved for suppression and missing from current Enrollware source data."
        if candidate["executable"]
        else "Not executable unless missing from Enrollware, suppressible, and approved_for_suppression."
    )
    return candidate


def build_report() -> dict[str, Any]:
    review = build_review_report()
    approvals = load_approvals()
    candidates = [
        build_candidate(offer, approvals)
        for offer in review.get("stale_offers", [])
        if offer.get("enrollware_presence_status") == "missing_from_enrollware"
        and offer.get("recommended_action") in SUPPRESSIBLE_ACTIONS
    ]
    candidates.sort(
        key=lambda item: (
            str(item.get("source_file") or ""),
            str(item.get("course_title") or item.get("course_key") or ""),
            str(item.get("date") or ""),
            str(item.get("start_time") or ""),
            str(item.get("suppression_action_id") or ""),
        )
    )
    approval_counts = Counter(str(item.get("suppression_approval_status") or "needs_review") for item in candidates)
    source_counts = Counter(str(item.get("source_file") or "unknown") for item in candidates)
    course_counts = Counter(str(item.get("course_title") or item.get("course_key") or "unknown") for item in candidates)
    month_counts = Counter(str(item.get("month") or "unknown") for item in candidates)
    action_counts = Counter(str(item.get("recommended_action") or "unknown") for item in candidates)
    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "approval_state_path": str(APPROVALS_PATH),
        "banner": "REPORT ONLY - DO NOT MODIFY PUBLIC OFFER FILES YET",
        "summary": {
            "total_stale_offer_suppression_candidates": len(candidates),
            "needs_review": approval_counts.get("needs_review", 0),
            "approved_for_suppression": approval_counts.get("approved_for_suppression", 0),
            "hold": approval_counts.get("hold", 0),
            "rejected": approval_counts.get("rejected", 0),
            "executable_suppressions": sum(1 for item in candidates if item.get("executable")),
            "by_source_file": dict(sorted(source_counts.items())),
            "by_course": dict(sorted(course_counts.items())),
            "by_month": dict(sorted(month_counts.items())),
            "by_recommended_action": dict(sorted(action_counts.items())),
        },
        "candidates": candidates,
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for item in report["candidates"]:
        grouped[str(item.get("source_file") or "unknown")][str(item.get("course_title") or item.get("course_key") or "unknown")].append(item)

    lines = [
        "# Stale Offer Suppression Candidates",
        "",
        "> REPORT ONLY - DO NOT MODIFY PUBLIC OFFER FILES YET",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Approval state: {report['approval_state_path']}",
        f"- Total candidates: {report['summary']['total_stale_offer_suppression_candidates']}",
        f"- Needs review: {report['summary']['needs_review']}",
        f"- Approved for suppression: {report['summary']['approved_for_suppression']}",
        f"- Hold: {report['summary']['hold']}",
        f"- Rejected: {report['summary']['rejected']}",
        f"- Executable suppressions: {report['summary']['executable_suppressions']}",
        f"- By source file: {json.dumps(report['summary']['by_source_file'], sort_keys=True)}",
        f"- By recommended action: {json.dumps(report['summary']['by_recommended_action'], sort_keys=True)}",
        "",
        "## Candidates By Source And Course",
        "",
    ]

    for source_file in sorted(grouped):
        lines.append(f"### {source_file}")
        for course in sorted(grouped[source_file]):
            items = grouped[source_file][course]
            lines.append(f"#### {course} ({len(items)})")
            for item in sorted(items, key=lambda row: (str(row.get("date") or ""), str(row.get("start_time") or ""), str(row.get("suppression_action_id") or "")))[:50]:
                lines.append(f"- {item.get('date')} {item.get('start_time') or ''} - {item.get('suppression_action_id')}")
                lines.append(f"  - Artifact: {item.get('artifact_id')}")
                lines.append(f"  - Approval: {item.get('suppression_approval_status')}")
                lines.append(f"  - Executable: {item.get('executable')}")
                lines.append(f"  - Action: {item.get('recommended_action')}")
                lines.append(f"  - Confidence: {item.get('confidence')}")
                lines.append(f"  - Reason: {item.get('reason')}")
            lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    report = build_report()
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
