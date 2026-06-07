#!/usr/bin/env python3
"""Build a dry-run cleanup plan from public artifact action candidates."""

from __future__ import annotations

import json
import hashlib
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_instructor_availability_report import DEBUG_DIR, TZ
from scripts.build_public_artifact_action_candidates import build_action_report


REPORT_JSON_PATH = DEBUG_DIR / "public_artifact_cleanup_plan.json"
REPORT_MD_PATH = DEBUG_DIR / "public_artifact_cleanup_plan.md"
REDIRECT_TARGETS_PATH = ROOT / "data" / "config" / "class_lander_redirect_targets.json"
PUBLIC_SCHEDULE_PATH = ROOT / "public_schedule.json"
SCHEDULE_PATH = ROOT / "data" / "schedule.json"
APPROVALS_PATH = ROOT / "data" / "state" / "public_artifact_cleanup_approvals.json"
CLEANUP_ACTION_ORDER = [
    "redirect_class_lander_to_hub",
    "archive_class_lander",
    "remove_class_lander",
    "suppress_schedule_offer",
    "keep_as_hub_offer",
    "needs_review",
]
SUPPORTED_APPROVAL_STATUSES = {
    "needs_review",
    "approved_for_redirect",
    "approved_for_suppression",
    "approved_for_archive",
    "hold",
    "rejected",
}


def load_redirect_targets() -> dict[str, Any]:
    return json.loads(REDIRECT_TARGETS_PATH.read_text(encoding="utf-8"))


def load_cleanup_approvals() -> dict[str, dict[str, Any]]:
    if not APPROVALS_PATH.exists():
        return {}
    data = json.loads(APPROVALS_PATH.read_text(encoding="utf-8"))
    approvals: dict[str, dict[str, Any]] = {}
    for approval in data.get("approvals", []):
        if not isinstance(approval, dict):
            continue
        action_id = str(approval.get("cleanup_action_id") or "")
        status = str(approval.get("cleanup_approval_status") or "")
        if action_id and status in SUPPORTED_APPROVAL_STATUSES:
            approvals[action_id] = approval
    return approvals


def clean_html(value: Any) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def load_historical_session_context() -> dict[str, dict[str, Any]]:
    context: dict[str, dict[str, Any]] = {}
    if PUBLIC_SCHEDULE_PATH.exists():
        data = json.loads(PUBLIC_SCHEDULE_PATH.read_text(encoding="utf-8"))
        for session in data.get("sessions", []):
            if not isinstance(session, dict):
                continue
            session_id = str(session.get("session_id") or "")
            if session_id:
                context[session_id] = {
                    "course_title": clean_html(session.get("course")),
                    "date": str(session.get("start") or "")[:10],
                    "time": str(session.get("start") or "")[11:16],
                    "location": session.get("location"),
                    "source": str(PUBLIC_SCHEDULE_PATH),
                }
    if SCHEDULE_PATH.exists():
        data = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
        for session in data.get("sessions", []):
            if not isinstance(session, dict):
                continue
            session_id = str(session.get("session_id") or "")
            course = session.get("course") if isinstance(session.get("course"), dict) else {}
            title = clean_html(course.get("name") or session.get("course_name") or "")
            if session_id and title:
                existing = context.setdefault(session_id, {})
                existing["course_title"] = existing.get("course_title") or title
                existing["date"] = existing.get("date") or str(session.get("start") or "")[:10]
                existing["time"] = existing.get("time") or str(session.get("start") or "")[11:16]
                existing["location"] = existing.get("location") or session.get("location")
                existing["source"] = existing.get("source") or str(SCHEDULE_PATH)
    return context


def session_id_from_artifact_id(artifact_id: Any) -> str | None:
    text = str(artifact_id or "")
    if text.startswith("class:"):
        return text.split(":", 1)[1]
    return None


def class_lander_title(path_value: Any) -> str | None:
    if not path_value:
        return None
    path = Path(str(path_value))
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"<title>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    title = re.sub(r"<[^>]+>", " ", match.group(1))
    return re.sub(r"\s+", " ", title).strip()


def destination_mapping_for(candidate: dict[str, Any], redirect_config: dict[str, Any], historical_context: dict[str, dict[str, Any]]) -> dict[str, Any]:
    title = class_lander_title(candidate.get("current_source_file")) if candidate.get("public_artifact_type") == "class_lander" else None
    historical = historical_context.get(str(session_id_from_artifact_id(candidate.get("artifact_id")) or ""), {})
    historical_title = historical.get("course_title")
    haystack = " ".join(
        str(candidate.get(key) or "")
        for key in ["course_key", "course_title", "artifact_id"]
    )
    if title:
        haystack = f"{haystack} {title}"
    if historical_title:
        haystack = f"{haystack} {historical_title}"
    haystack = haystack.lower()
    for target in redirect_config.get("targets", []):
        if any(str(keyword).lower() in haystack for keyword in target.get("keywords", [])):
            return {
                "destination_hub": target.get("destination_hub"),
                "destination_reason": target.get("destination_reason"),
                "destination_confidence": target.get("destination_confidence", "medium"),
                "destination_needs_review": False,
                "destination_target_key": target.get("target_key"),
                "destination_source_title": historical_title or title,
                "destination_source": historical.get("source") if historical_title else "class_lander_title",
            }
    default = redirect_config.get("default_destination", {})
    return {
        "destination_hub": default.get("destination_hub", "/index.html"),
        "destination_reason": default.get("destination_reason", "No specific destination mapping matched."),
        "destination_confidence": default.get("destination_confidence", "low"),
        "destination_needs_review": bool(default.get("destination_needs_review", True)),
        "destination_target_key": "default",
        "destination_source_title": historical_title or title,
        "destination_source": historical.get("source") if historical_title else "class_lander_title",
    }


def proposed_cleanup_action(candidate: dict[str, Any]) -> str:
    recommended = candidate.get("recommended_public_action")
    artifact_type = candidate.get("public_artifact_type")
    if recommended == "remove_or_redirect_class_lander":
        return "redirect_class_lander_to_hub"
    if recommended == "show_as_hub_offer_only":
        return "keep_as_hub_offer"
    if recommended == "suppress_until_enrollware_backed" and artifact_type == "schedule_offer":
        return "suppress_schedule_offer"
    if recommended == "suppress_until_enrollware_backed":
        return "needs_review"
    return "needs_review"


def cleanup_action_id_for(
    artifact_id: Any,
    current_file_path: Any,
    proposed_action: Any,
    destination_hub: Any,
) -> str:
    fingerprint = "|".join(
        str(value or "")
        for value in [artifact_id, current_file_path, proposed_action, destination_hub]
    )
    digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16]
    return f"cleanup_{digest}"


def cleanup_approval_for(action_id: str, approvals: dict[str, dict[str, Any]]) -> dict[str, Any]:
    approval = approvals.get(action_id)
    if not approval:
        return {
            "cleanup_approval_status": "needs_review",
            "cleanup_approval_note": "Awaiting operator review.",
            "approved_by": None,
            "approved_at": None,
        }
    return {
        "cleanup_approval_status": approval.get("cleanup_approval_status") or "needs_review",
        "cleanup_approval_note": approval.get("cleanup_approval_note") or "",
        "approved_by": approval.get("approved_by"),
        "approved_at": approval.get("approved_at"),
    }


def executable_status(proposed_action: str, approval_status: str, destination_needs_review: bool) -> tuple[bool, str]:
    if proposed_action == "redirect_class_lander_to_hub":
        if destination_needs_review:
            return False, "Destination still needs review."
        if approval_status == "approved_for_redirect":
            return True, "Approved redirect action with reviewed destination."
        return False, "Redirect requires approved_for_redirect."
    if proposed_action == "suppress_schedule_offer":
        if approval_status == "approved_for_suppression":
            return True, "Approved suppression action."
        return False, "Suppression requires approved_for_suppression."
    if proposed_action in {"archive_class_lander", "remove_class_lander"}:
        if approval_status == "approved_for_archive":
            return True, "Approved archive action."
        return False, "Archive/remove requires approved_for_archive."
    return False, "This proposed action is not executable by the cleanup approval gate."


def cleanup_item(
    candidate: dict[str, Any],
    redirect_config: dict[str, Any],
    historical_context: dict[str, dict[str, Any]],
    approvals: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    action = proposed_cleanup_action(candidate)
    historical = historical_context.get(str(session_id_from_artifact_id(candidate.get("artifact_id")) or ""), {})
    destination = destination_mapping_for(candidate, redirect_config, historical_context) if action == "redirect_class_lander_to_hub" else {
        "destination_hub": None,
        "destination_reason": None,
        "destination_confidence": None,
        "destination_needs_review": False,
        "destination_target_key": None,
        "destination_source_title": None,
        "destination_source": None,
    }
    action_id = cleanup_action_id_for(
        candidate.get("artifact_id"),
        candidate.get("current_source_file"),
        action,
        destination["destination_hub"],
    )
    approval = cleanup_approval_for(action_id, approvals)
    executable, executable_reason = executable_status(
        action,
        str(approval["cleanup_approval_status"]),
        bool(destination["destination_needs_review"]),
    )
    return {
        "cleanup_action_id": action_id,
        "artifact_id": candidate.get("artifact_id"),
        "current_file_path": candidate.get("current_source_file"),
        "public_artifact_type": candidate.get("public_artifact_type"),
        "course_title": candidate.get("course_title") or historical.get("course_title"),
        "course_key": candidate.get("course_key"),
        "date": candidate.get("date") or historical.get("date"),
        "time": candidate.get("time") or historical.get("time"),
        "location": candidate.get("location") or historical.get("location"),
        "instructor": candidate.get("instructor"),
        "proposed_action": action,
        "destination_hub": destination["destination_hub"],
        "destination_reason": destination["destination_reason"],
        "destination_confidence": destination["destination_confidence"],
        "destination_needs_review": destination["destination_needs_review"],
        "destination_target_key": destination["destination_target_key"],
        "destination_source_title": destination["destination_source_title"],
        "destination_source": destination["destination_source"],
        "cleanup_approval_status": approval["cleanup_approval_status"],
        "cleanup_approval_note": approval["cleanup_approval_note"],
        "approved_by": approval["approved_by"],
        "approved_at": approval["approved_at"],
        "cleanup_action_executable": executable,
        "cleanup_action_block_reason": None if executable else executable_reason,
        "reason": candidate.get("reason"),
        "confidence": candidate.get("confidence"),
        "enrollware_backing_status": candidate.get("enrollware_backing_status"),
        "sister_conflict_group_key": candidate.get("sister_conflict_group_key"),
    }


def build_cleanup_plan() -> dict[str, Any]:
    action_report = build_action_report()
    redirect_config = load_redirect_targets()
    historical_context = load_historical_session_context()
    approvals = load_cleanup_approvals()
    items = [cleanup_item(candidate, redirect_config, historical_context, approvals) for candidate in action_report.get("action_candidates", [])]
    items.sort(
        key=lambda item: (
            CLEANUP_ACTION_ORDER.index(str(item["proposed_action"]))
            if item["proposed_action"] in CLEANUP_ACTION_ORDER
            else 99,
            str(item.get("destination_hub") or ""),
            str(item.get("course_title") or ""),
            str(item.get("date") or ""),
            str(item.get("time") or ""),
            str(item.get("artifact_id") or ""),
        )
    )
    action_counts = Counter(str(item["proposed_action"]) for item in items)
    redirect_items = [item for item in items if item["proposed_action"] == "redirect_class_lander_to_hub"]
    redirect_hub_counts = Counter(str(item.get("destination_hub") or "") for item in redirect_items)
    approval_counts = Counter(str(item.get("cleanup_approval_status") or "needs_review") for item in items)
    sister_groups = sorted({str(item["sister_conflict_group_key"]) for item in items if item.get("sister_conflict_group_key")})
    grouped: dict[str, list[dict[str, Any]]] = {action: [] for action in CLEANUP_ACTION_ORDER}
    for item in items:
        grouped.setdefault(str(item["proposed_action"]), []).append(item)
    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "dry_run_only": True,
        "public_behavior_changed": False,
        "source_action_report_generated_at": action_report.get("generated_at"),
        "summary": {
            "total_cleanup_items": len(items),
            "class_landers_to_redirect": action_counts.get("redirect_class_lander_to_hub", 0),
            "class_landers_to_archive_remove": action_counts.get("archive_class_lander", 0) + action_counts.get("remove_class_lander", 0),
            "schedule_offers_to_suppress": action_counts.get("suppress_schedule_offer", 0),
            "hub_only_offers_to_keep": action_counts.get("keep_as_hub_offer", 0),
            "needs_review": action_counts.get("needs_review", 0),
            "redirects_mapped_to_specific_hubs": sum(1 for item in redirect_items if item.get("destination_hub") != "/index.html"),
            "redirects_falling_back_to_index": sum(1 for item in redirect_items if item.get("destination_hub") == "/index.html"),
            "destination_needs_review_count": sum(1 for item in redirect_items if item.get("destination_needs_review")),
            "cleanup_approval_status_counts": {
                status: approval_counts.get(status, 0)
                for status in sorted(SUPPORTED_APPROVAL_STATUSES)
            },
            "executable_cleanup_actions": sum(1 for item in items if item.get("cleanup_action_executable")),
            "blocked_fallback_redirects": sum(
                1
                for item in redirect_items
                if item.get("destination_hub") == "/index.html" and item.get("destination_needs_review")
            ),
            "redirect_destination_counts": dict(sorted(redirect_hub_counts.items())),
            "sister_conflict_groups_affected": len(sister_groups),
            "cleanup_action_counts": dict(sorted(action_counts.items())),
        },
        "grouped_cleanup_items": grouped,
        "cleanup_items": items,
        "sister_conflict_groups_affected": [
            group
            for group in action_report.get("sister_conflict_groups_affected", [])
            if group.get("group_key") in sister_groups
        ],
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Public Artifact Cleanup Plan",
        "",
        "> DRY RUN ONLY - NO PUBLIC FILES MODIFIED",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Total cleanup items: {report['summary']['total_cleanup_items']}",
        f"- Class landers to redirect: {report['summary']['class_landers_to_redirect']}",
        f"- Class landers to archive/remove: {report['summary']['class_landers_to_archive_remove']}",
        f"- Schedule offers to suppress: {report['summary']['schedule_offers_to_suppress']}",
        f"- Hub-only offers to keep: {report['summary']['hub_only_offers_to_keep']}",
        f"- Needs review: {report['summary']['needs_review']}",
        f"- Redirects mapped to specific hubs: {report['summary']['redirects_mapped_to_specific_hubs']}",
        f"- Redirects falling back to /index.html: {report['summary']['redirects_falling_back_to_index']}",
        f"- Destination needs review: {report['summary']['destination_needs_review_count']}",
        f"- Executable cleanup actions: {report['summary']['executable_cleanup_actions']}",
        f"- Blocked fallback redirects: {report['summary']['blocked_fallback_redirects']}",
        f"- Redirect destinations: {json.dumps(report['summary']['redirect_destination_counts'], sort_keys=True)}",
        f"- Sister/conflict groups affected: {report['summary']['sister_conflict_groups_affected']}",
        "",
        "## Cleanup Approval Summary",
        "",
        f"- Needs review: {report['summary']['cleanup_approval_status_counts']['needs_review']}",
        f"- Approved for redirect: {report['summary']['cleanup_approval_status_counts']['approved_for_redirect']}",
        f"- Approved for suppression: {report['summary']['cleanup_approval_status_counts']['approved_for_suppression']}",
        f"- Approved for archive: {report['summary']['cleanup_approval_status_counts']['approved_for_archive']}",
        f"- Hold: {report['summary']['cleanup_approval_status_counts']['hold']}",
        f"- Rejected: {report['summary']['cleanup_approval_status_counts']['rejected']}",
        "",
    ]

    for action in CLEANUP_ACTION_ORDER:
        items = report["grouped_cleanup_items"].get(action, [])
        lines.extend([f"## {action}", ""])
        if not items:
            lines.append("No dry-run cleanup items.")
            lines.append("")
            continue
        by_course: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            by_course[str(item.get("course_title") or item.get("course_key") or "Unknown course")].append(item)
        for course in sorted(by_course):
            lines.extend([f"### {course}", ""])
            by_hub: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for item in by_course[course]:
                by_hub[str(item.get("destination_hub") or "No destination hub")].append(item)
            for hub in sorted(by_hub):
                lines.append(f"#### Destination: {hub}")
                by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for item in by_hub[hub]:
                    by_group[str(item.get("sister_conflict_group_key") or "No sister/conflict group")].append(item)
                for group in sorted(by_group):
                    lines.append(f"- Sister/conflict group: {group}")
                    for item in sorted(by_group[group], key=lambda value: (str(value.get("date") or ""), str(value.get("time") or ""), str(value.get("artifact_id") or "")))[:50]:
                        when = " ".join(part for part in [str(item.get("date") or ""), str(item.get("time") or "")] if part)
                        lines.append(f"  - {when} {item['artifact_id']}")
                        lines.append(f"    - Cleanup action ID: {item['cleanup_action_id']}")
                        lines.append(f"    - File: {item['current_file_path']}")
                        if item.get("destination_hub"):
                            lines.append(f"    - Destination hub: {item['destination_hub']}")
                            lines.append(f"    - Destination reason: {item['destination_reason']}")
                            lines.append(f"    - Destination confidence: {item['destination_confidence']}")
                            lines.append(f"    - Destination needs review: {item['destination_needs_review']}")
                            if item.get("destination_source_title"):
                                lines.append(f"    - Source title: {item['destination_source_title']}")
                            if item.get("destination_source"):
                                lines.append(f"    - Destination source: {item['destination_source']}")
                        lines.append(f"    - Backing: {item['enrollware_backing_status']}")
                        lines.append(f"    - Cleanup approval: {item['cleanup_approval_status']}")
                        lines.append(f"    - Approval note: {item['cleanup_approval_note']}")
                        lines.append(f"    - Executable: {item['cleanup_action_executable']}")
                        lines.append(f"    - Execution block reason: {item['cleanup_action_block_reason']}")
                        lines.append(f"    - Confidence: {item['confidence']}")
                        lines.append(f"    - Reason: {item['reason']}")
                lines.append("")

    lines.extend(["## Sister / Conflict Groups Affected", ""])
    if not report["sister_conflict_groups_affected"]:
        lines.append("No sister/conflict groups affected.")
    for group in report["sister_conflict_groups_affected"][:30]:
        lines.append(f"- {group['group_key']} - {group['artifact_count']} artifacts")
        lines.append(f"  - Types: {', '.join(group['artifact_types'])}")
        lines.append(f"  - Action: {group['recommended_group_action']}")
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    report = build_cleanup_plan()
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
