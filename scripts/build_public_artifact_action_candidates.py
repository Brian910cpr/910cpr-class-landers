#!/usr/bin/env python3
"""Build report-only action candidates from the public artifact model audit."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_public_artifact_model import build_report, sister_group_key
from scripts.build_instructor_availability_report import DEBUG_DIR, TZ


REPORT_JSON_PATH = DEBUG_DIR / "public_artifact_action_candidates.json"
REPORT_MD_PATH = DEBUG_DIR / "public_artifact_action_candidates.md"
ACTION_ORDER = [
    "remove_or_redirect_class_lander",
    "show_as_hub_offer_only",
    "suppress_until_enrollware_backed",
    "needs_review",
]


def confidence_for(artifact: dict[str, Any]) -> str:
    action = artifact.get("recommended_public_action")
    backing = artifact.get("enrollware_backing_status")
    if action == "remove_or_redirect_class_lander" and backing == "missing_from_current_enrollware":
        return "high"
    if action == "show_as_hub_offer_only" and artifact.get("public_artifact_type") in {"hub_offer", "schedule_offer"}:
        return "high"
    if action == "suppress_until_enrollware_backed" and backing == "missing_from_current_enrollware":
        return "high"
    return "medium"


def reason_for(artifact: dict[str, Any]) -> str:
    action = artifact.get("recommended_public_action")
    backing = artifact.get("enrollware_backing_status")
    artifact_type = artifact.get("public_artifact_type")
    if action == "remove_or_redirect_class_lander":
        return "Class lander does not map to a current Enrollware session."
    if action == "show_as_hub_offer_only" and backing == "generated_seed_candidate":
        return "Generated availability may appear as a hub offer, but must not create a standalone class lander."
    if action == "show_as_hub_offer_only" and artifact_type == "schedule_offer":
        return "Schedule-level entry is backed by Enrollware and should remain an offer, not a newly generated class lander."
    if action == "suppress_until_enrollware_backed":
        return "Artifact is not backed by current Enrollware source data."
    return "Model audit requires operator review."


def build_sister_lookup(audit: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    group_keys = {group["group_key"] for group in audit.get("sister_conflict_groups", [])}
    for artifact in audit.get("artifacts", []):
        key = sister_group_key(artifact)
        if key in group_keys:
            lookup[str(artifact.get("artifact_key"))] = key
    return lookup


def action_candidate(artifact: dict[str, Any], sister_lookup: dict[str, str]) -> dict[str, Any]:
    artifact_id = str(artifact.get("artifact_key") or artifact.get("path") or "")
    return {
        "artifact_id": artifact_id,
        "public_artifact_type": artifact.get("public_artifact_type") or "unknown",
        "current_source_file": artifact.get("path"),
        "course_title": artifact.get("course_title"),
        "course_key": artifact.get("course_key"),
        "date": artifact.get("date"),
        "time": artifact.get("start_time"),
        "location": artifact.get("location"),
        "instructor": artifact.get("instructor"),
        "enrollware_backing_status": artifact.get("enrollware_backing_status"),
        "recommended_public_action": artifact.get("recommended_public_action"),
        "reason": reason_for(artifact),
        "confidence": confidence_for(artifact),
        "sister_conflict_group_key": sister_lookup.get(artifact_id),
    }


def build_action_report() -> dict[str, Any]:
    audit = build_report()
    sister_lookup = build_sister_lookup(audit)
    candidates = [
        action_candidate(artifact, sister_lookup)
        for artifact in audit.get("artifacts", [])
        if artifact.get("recommended_public_action") in ACTION_ORDER
        and artifact.get("recommended_public_action") != "keep_class_lander"
    ]
    candidates.sort(
        key=lambda item: (
            ACTION_ORDER.index(str(item["recommended_public_action"]))
            if item["recommended_public_action"] in ACTION_ORDER
            else 99,
            str(item.get("course_title") or ""),
            str(item.get("date") or ""),
            str(item.get("time") or ""),
            str(item.get("artifact_id") or ""),
        )
    )

    action_counts = Counter(str(item["recommended_public_action"]) for item in candidates)
    sister_groups_affected = sorted({str(item["sister_conflict_group_key"]) for item in candidates if item.get("sister_conflict_group_key")})
    grouped: dict[str, list[dict[str, Any]]] = {action: [] for action in ACTION_ORDER}
    for candidate in candidates:
        grouped.setdefault(str(candidate["recommended_public_action"]), []).append(candidate)

    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "source_audit_generated_at": audit.get("generated_at"),
        "summary": {
            "total_action_candidates": len(candidates),
            "class_landers_to_remove_redirect": action_counts.get("remove_or_redirect_class_lander", 0),
            "hub_only_offers": action_counts.get("show_as_hub_offer_only", 0),
            "suppress_until_backed": action_counts.get("suppress_until_enrollware_backed", 0),
            "needs_review": action_counts.get("needs_review", 0),
            "sister_conflict_groups_affected": len(sister_groups_affected),
            "action_counts": dict(sorted(action_counts.items())),
        },
        "grouped_action_candidates": grouped,
        "action_candidates": candidates,
        "sister_conflict_groups_affected": [
            group
            for group in audit.get("sister_conflict_groups", [])
            if group.get("group_key") in sister_groups_affected
        ],
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Public Artifact Action Candidates",
        "",
        "> REPORT ONLY - DO NOT MODIFY PUBLIC OUTPUT YET",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Total action candidates: {report['summary']['total_action_candidates']}",
        f"- Class landers to remove/redirect: {report['summary']['class_landers_to_remove_redirect']}",
        f"- Hub-only offers: {report['summary']['hub_only_offers']}",
        f"- Suppress until backed: {report['summary']['suppress_until_backed']}",
        f"- Needs review: {report['summary']['needs_review']}",
        f"- Sister/conflict groups affected: {report['summary']['sister_conflict_groups_affected']}",
        "",
    ]

    for action in ACTION_ORDER:
        candidates = report["grouped_action_candidates"].get(action, [])
        lines.extend([f"## {action}", ""])
        if not candidates:
            lines.append("No candidates.")
            lines.append("")
            continue
        by_course: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for candidate in candidates:
            by_course[str(candidate.get("course_title") or candidate.get("course_key") or "Unknown course")].append(candidate)
        for course in sorted(by_course):
            lines.extend([f"### {course}", ""])
            by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for candidate in by_course[course]:
                by_date[str(candidate.get("date") or "Undated")].append(candidate)
            for date in sorted(by_date):
                lines.append(f"#### {date}")
                for candidate in sorted(by_date[date], key=lambda item: (str(item.get("sister_conflict_group_key") or ""), str(item.get("time") or ""), str(item.get("artifact_id") or "")))[:50]:
                    lines.append(f"- {candidate.get('time') or ''} - {candidate['artifact_id']}")
                    lines.append(f"  - Type: {candidate['public_artifact_type']}")
                    lines.append(f"  - Source: {candidate['current_source_file']}")
                    lines.append(f"  - Backing: {candidate['enrollware_backing_status']}")
                    lines.append(f"  - Confidence: {candidate['confidence']}")
                    lines.append(f"  - Reason: {candidate['reason']}")
                    if candidate.get("sister_conflict_group_key"):
                        lines.append(f"  - Sister/conflict group: {candidate['sister_conflict_group_key']}")
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
    report = build_action_report()
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
