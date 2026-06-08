#!/usr/bin/env python3
"""Build a Brian-readable report for stale Lander offers.

Report-only: this script does not modify public pages, schedules, class landers,
CTAs, or Enrollware links.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_lander_offers_against_enrollware import build_report as build_offer_audit
from scripts.audit_public_artifact_model import build_report as build_artifact_model
from scripts.build_instructor_availability_report import DEBUG_DIR, TZ
from scripts.build_public_artifact_action_candidates import build_action_report


REPORT_JSON_PATH = DEBUG_DIR / "stale_offer_review_report.json"
REPORT_MD_PATH = DEBUG_DIR / "stale_offer_review_report.md"
REVIEW_ACTIONS = {"remove_from_public_output", "suppress_until_enrollware_backed"}


def norm(value: Any) -> str:
    return str(value or "").strip()


def month_key(value: Any) -> str:
    text = norm(value)
    return text[:7] if len(text) >= 7 else "unknown"


def artifact_id_for_offer(offer: dict[str, Any]) -> str:
    session_id = norm(offer.get("session_id"))
    if session_id:
        return f"class:{session_id}"
    offer_key = norm(offer.get("offer_key"))
    if offer_key:
        return f"{offer.get('source_type')}:{offer_key}"
    return f"{offer.get('source_type')}:{offer.get('course_title')}:{offer.get('date')}:{offer.get('start_time')}"


def offer_id_for(offer: dict[str, Any]) -> str:
    raw = "|".join(
        [
            norm(offer.get("source_type")),
            norm(offer.get("offer_key")),
            norm(offer.get("session_id")),
            norm(offer.get("course_title")),
            norm(offer.get("date")),
            norm(offer.get("start_time")),
            norm(offer.get("source_file")),
        ]
    )
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", raw).strip("_").lower()
    return f"stale_offer_{slug[:96]}" if slug else "stale_offer_unknown"


def build_action_lookup(action_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for candidate in action_report.get("action_candidates", []):
        if not isinstance(candidate, dict):
            continue
        artifact_id = norm(candidate.get("artifact_id"))
        if artifact_id:
            lookup[artifact_id] = candidate
    return lookup


def build_artifact_lookup(model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for artifact in model.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        key = norm(artifact.get("artifact_key"))
        session_id = norm(artifact.get("session_id"))
        if key:
            lookup[key] = artifact
        if session_id:
            lookup.setdefault(f"class:{session_id}", artifact)
    return lookup


def class_lander_path(session_id: Any) -> str | None:
    session = norm(session_id)
    if not session:
        return None
    path = ROOT / "docs" / "classes" / f"{session}.html"
    return str(path) if path.exists() else None


def confidence_for(offer: dict[str, Any], action: dict[str, Any] | None, artifact: dict[str, Any] | None) -> str:
    if action and action.get("confidence"):
        return str(action["confidence"])
    if offer.get("session_id") and offer.get("recommended_action") == "remove_from_public_output":
        return "high"
    if artifact and artifact.get("enrollware_backing_status") == "missing_from_current_enrollware":
        return "high"
    return "medium"


def public_type_for(offer: dict[str, Any], action: dict[str, Any] | None, artifact: dict[str, Any] | None) -> str:
    if action and action.get("public_artifact_type"):
        return str(action["public_artifact_type"])
    if artifact and artifact.get("public_artifact_type"):
        return str(artifact["public_artifact_type"])
    source_type = norm(offer.get("source_type"))
    if source_type == "public_schedule_session":
        return "schedule_offer"
    if source_type == "customer_facing_offer":
        return "hub_offer"
    return "unknown"


def normalize_stale_offer(
    offer: dict[str, Any],
    action_lookup: dict[str, dict[str, Any]],
    artifact_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    artifact_id = artifact_id_for_offer(offer)
    action = action_lookup.get(artifact_id)
    artifact = artifact_lookup.get(artifact_id)
    class_path = class_lander_path(offer.get("session_id"))
    recommended_action = (
        action.get("recommended_public_action")
        if action and action.get("recommended_public_action") in REVIEW_ACTIONS
        else offer.get("recommended_action")
    )
    if recommended_action == "remove_from_public_output" and public_type_for(offer, action, artifact) == "hub_offer":
        recommended_action = "suppress_until_enrollware_backed"
    return {
        "offer_id": offer_id_for(offer),
        "artifact_id": artifact_id,
        "source_file": offer.get("source_file"),
        "source_type": offer.get("source_type"),
        "public_artifact_type": public_type_for(offer, action, artifact),
        "course_title": offer.get("course_title"),
        "course_key": offer.get("course_key"),
        "date": offer.get("date"),
        "month": month_key(offer.get("date")),
        "start_time": offer.get("start_time"),
        "location": offer.get("location"),
        "instructor": offer.get("instructor"),
        "has_class_lander_file": bool(class_path),
        "class_lander_file": class_path,
        "related_class_session_id": offer.get("session_id"),
        "matched_enrollware_key": offer.get("matched_enrollware_key"),
        "enrollware_presence_status": offer.get("enrollware_presence_status"),
        "recommended_action": recommended_action,
        "reason": offer.get("reason") or (action.get("reason") if action else None),
        "confidence": confidence_for(offer, action, artifact),
        "sister_conflict_group": action.get("sister_conflict_group_key") if action else None,
        "registration_url_present": bool(offer.get("registration_url")),
    }


def build_review_report() -> dict[str, Any]:
    offer_audit = build_offer_audit()
    artifact_model = build_artifact_model()
    action_report = build_action_report()
    action_lookup = build_action_lookup(action_report)
    artifact_lookup = build_artifact_lookup(artifact_model)

    stale = []
    for offer in offer_audit.get("offers", []):
        if offer.get("enrollware_presence_status") != "missing_from_enrollware":
            continue
        if offer.get("recommended_action") not in REVIEW_ACTIONS:
            continue
        stale.append(normalize_stale_offer(offer, action_lookup, artifact_lookup))

    stale.sort(
        key=lambda item: (
            str(item.get("recommended_action") or ""),
            str(item.get("course_title") or ""),
            str(item.get("date") or ""),
            str(item.get("start_time") or ""),
            str(item.get("artifact_id") or ""),
        )
    )
    action_counts = Counter(str(item.get("recommended_action") or "unknown") for item in stale)
    course_counts = Counter(str(item.get("course_title") or item.get("course_key") or "unknown") for item in stale)
    month_counts = Counter(str(item.get("month") or "unknown") for item in stale)
    source_counts = Counter(str(item.get("source_file") or "unknown") for item in stale)
    sister_groups = sorted({str(item.get("sister_conflict_group")) for item in stale if item.get("sister_conflict_group")})
    by_course_lower = defaultdict(list)
    for item in stale:
        by_course_lower[str(item.get("course_title") or "").lower()].append(item)

    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "banner": "REPORT ONLY - DO NOT REMOVE PUBLIC OFFERS YET",
        "source_reports": {
            "lander_offer_audit_generated_at": offer_audit.get("generated_at"),
            "public_artifact_model_generated_at": artifact_model.get("generated_at"),
            "action_candidates_generated_at": action_report.get("generated_at"),
        },
        "summary": {
            "total_stale_offers": len(stale),
            "by_recommended_action": dict(sorted(action_counts.items())),
            "by_course": dict(sorted(course_counts.items())),
            "by_month": dict(sorted(month_counts.items())),
            "by_source_file": dict(sorted(source_counts.items())),
            "with_class_lander_file": sum(1 for item in stale if item.get("has_class_lander_file")),
            "without_class_lander_file": sum(1 for item in stale if not item.get("has_class_lander_file")),
            "sister_conflict_groups_affected": len(sister_groups),
        },
        "top_examples": {
            "stale_bls_offers": [item for item in stale if "bls" in str(item.get("course_title") or "").lower()][:10],
            "stale_acls_pals_offers": [
                item
                for item in stale
                if "acls" in str(item.get("course_title") or "").lower()
                or "pals" in str(item.get("course_title") or "").lower()
            ][:10],
            "stale_heartsaver_offers": [item for item in stale if "heartsaver" in str(item.get("course_title") or "").lower()][:10],
            "sister_conflict_group_examples": [item for item in stale if item.get("sister_conflict_group")][:10],
        },
        "sister_conflict_groups_affected": sister_groups,
        "stale_offers": stale,
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    grouped: dict[str, dict[str, dict[str, dict[str, list[dict[str, Any]]]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    )
    for item in report["stale_offers"]:
        grouped[str(item.get("recommended_action") or "unknown")][str(item.get("course_title") or item.get("course_key") or "unknown")][
            str(item.get("date") or "unknown")
        ][str(item.get("source_file") or "unknown")].append(item)

    lines = [
        "# Stale Offer Review Report",
        "",
        "> REPORT ONLY - DO NOT REMOVE PUBLIC OFFERS YET",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Total stale offers: {report['summary']['total_stale_offers']}",
        f"- By recommended action: {json.dumps(report['summary']['by_recommended_action'], sort_keys=True)}",
        f"- With class lander file: {report['summary']['with_class_lander_file']}",
        f"- Without class lander file: {report['summary']['without_class_lander_file']}",
        f"- Sister/conflict groups affected: {report['summary']['sister_conflict_groups_affected']}",
        "",
        "## Top Examples",
        "",
        "### Stale BLS Offers",
    ]
    append_examples(lines, report["top_examples"]["stale_bls_offers"])
    lines.append("### Stale ACLS/PALS Offers")
    append_examples(lines, report["top_examples"]["stale_acls_pals_offers"])
    lines.append("### Stale Heartsaver Offers")
    append_examples(lines, report["top_examples"]["stale_heartsaver_offers"])
    lines.append("### Sister / Conflict Group Examples")
    append_examples(lines, report["top_examples"]["sister_conflict_group_examples"])

    lines.extend(["", "## Review Batches", ""])
    for action in sorted(grouped):
        lines.append(f"### Action: {action}")
        for course in sorted(grouped[action]):
            lines.append(f"#### {course}")
            for date in sorted(grouped[action][course]):
                lines.append(f"##### {date}")
                for source_file in sorted(grouped[action][course][date]):
                    lines.append(f"- Source: {source_file}")
                    for item in grouped[action][course][date][source_file][:50]:
                        lines.append(
                            f"  - {item.get('start_time') or ''} - {item.get('offer_id')} ({item.get('public_artifact_type')})"
                        )
                        lines.append(f"    - Artifact: {item.get('artifact_id')}")
                        lines.append(f"    - Location: {item.get('location')}")
                        lines.append(f"    - Instructor: {item.get('instructor')}")
                        lines.append(f"    - Class lander file: {item.get('class_lander_file') or 'none'}")
                        lines.append(f"    - Related session ID: {item.get('related_class_session_id') or 'none'}")
                        lines.append(f"    - Confidence: {item.get('confidence')}")
                        lines.append(f"    - Reason: {item.get('reason')}")
                        if item.get("sister_conflict_group"):
                            lines.append(f"    - Sister/conflict group: {item.get('sister_conflict_group')}")
                lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def append_examples(lines: list[str], examples: list[dict[str, Any]]) -> None:
    if not examples:
        lines.append("- None found in this batch.")
        lines.append("")
        return
    for item in examples[:10]:
        lines.append(
            f"- {item.get('date')} {item.get('start_time') or ''} - {item.get('course_title')} - {item.get('recommended_action')}"
        )
        lines.append(f"  - Source: {item.get('source_file')}")
        lines.append(f"  - Artifact: {item.get('artifact_id')}")
        lines.append(f"  - Reason: {item.get('reason')}")
    lines.append("")


def main() -> int:
    report = build_review_report()
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
