#!/usr/bin/env python3
"""Build a report-only preview of what each hub would display.

This does not modify hub pages, public schedules, CTAs, Enrollware links, or
class landers.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_hub_offer_model_report import build_report
from scripts.build_instructor_availability_report import DEBUG_DIR, SOURCE_MODES, TZ
from scripts.build_proposed_seed_review import format_date


REPORT_JSON_PATH = DEBUG_DIR / "hub_render_preview.json"
REPORT_MD_PATH = DEBUG_DIR / "hub_render_preview.md"


def display_mode_for_hub(hub: dict[str, Any]) -> str:
    current_count = int(hub.get("current_enrollware_class_count") or 0)
    approved_count = int(hub.get("approved_seed_offer_count") or 0)
    empty_state_type = str(hub.get("empty_state_type") or "")

    if current_count and approved_count:
        return "mixed_current_and_seed"
    if current_count:
        return "current_classes"
    if approved_count:
        return "approved_seed_offers"
    if empty_state_type == "suppress_hub_offer_block":
        return "suppress_offer_block"
    if empty_state_type == "needs_review":
        return "needs_review"
    return "empty_state"


def preview_class_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": item.get("course_title"),
        "date": item.get("date"),
        "date_label": format_date(item.get("start_datetime")),
        "start_time": item.get("start_time"),
        "end_time": item.get("end_time"),
        "session_id": item.get("session_id"),
        "course_key": item.get("course_key"),
        "course_id": item.get("course_id"),
        "public_visibility_status": item.get("public_visibility_status"),
        "public_visibility_note": item.get("public_visibility_note"),
        "cutoff_hours": item.get("cutoff_hours"),
        "hours_until_start": item.get("hours_until_start"),
        "source": "Enrollware-backed",
        "display_note": "Current Enrollware-backed class/session offer.",
    }


def preview_seed_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": item.get("course_title"),
        "date": item.get("date"),
        "date_label": format_date(item.get("start_datetime")),
        "start_time": item.get("start_time"),
        "end_time": item.get("end_time"),
        "seed_id": item.get("seed_id"),
        "course_key": item.get("course_key"),
        "instructor_key": item.get("instructor_key"),
        "registration_target_key": item.get("registration_target_key"),
        "approval_status": item.get("approval_status"),
        "publishability_status": item.get("publishability_status"),
        "enrollware_presence_status": item.get("enrollware_presence_status"),
        "public_ready": item.get("public_ready"),
        "public_ready_block_reason": item.get("public_ready_block_reason"),
        "suppression_reason": item.get("reason"),
        "display_item_type": item.get("display_item_type"),
        "source": "Approved seed offer",
        "display_note": "Hub offer only; no standalone class lander.",
    }


def build_preview(source_mode: str) -> dict[str, Any]:
    model = build_report(source_mode)
    previews: list[dict[str, Any]] = []
    mode_counts: Counter[str] = Counter()
    held_needs_review = 0
    suppressed_total = 0
    suppressed_approved_but_not_public_ready = 0
    suppressed_cutoff_window = 0

    for hub in model.get("hubs", []):
        mode = display_mode_for_hub(hub)
        mode_counts[mode] += 1
        current_classes = [preview_class_item(item) for item in hub.get("current_enrollware_classes", [])[:10]]
        cutoff_suppressed_classes = [
            preview_class_item(item)
            for item in hub.get("cutoff_suppressed_current_enrollware_classes", [])[:10]
        ]
        approved_seed_offers = [preview_seed_item(item) for item in hub.get("approved_seed_offers", [])[:10]]
        held_seed_offers = [preview_seed_item(item) for item in hub.get("needs_review_seed_offers", [])[:10]]
        suppressed_seed_offers = [preview_seed_item(item) for item in hub.get("blocked_suppressed_seed_offers", [])[:10]]
        held_needs_review += int(hub.get("needs_review_seed_offer_count") or 0)
        suppressed_total += int(hub.get("blocked_suppressed_seed_offer_count") or 0)
        suppressed_cutoff_window += int(hub.get("cutoff_suppressed_current_enrollware_class_count") or 0)
        suppressed_approved_but_not_public_ready += sum(
            1
            for item in hub.get("blocked_suppressed_seed_offers", [])
            if item.get("display_item_type") == "suppressed_approved_but_not_public_ready"
        )

        previews.append(
            {
                "hub_key": hub.get("hub_key"),
                "hub_title": hub.get("title"),
                "hub_url": hub.get("hub_path"),
                "hub_source": hub.get("hub_source"),
                "display_mode": mode,
                "current_enrollware_class_count": hub.get("current_enrollware_class_count"),
                "cutoff_suppressed_current_enrollware_class_count": hub.get("cutoff_suppressed_current_enrollware_class_count"),
                "approved_seed_offer_count": hub.get("approved_seed_offer_count"),
                "held_needs_review_seed_offer_count": hub.get("needs_review_seed_offer_count"),
                "suppressed_offer_count": hub.get("blocked_suppressed_seed_offer_count"),
                "current_enrollware_classes_preview": current_classes,
                "cutoff_suppressed_current_enrollware_classes": cutoff_suppressed_classes,
                "approved_seed_offers_preview": approved_seed_offers,
                "needs_review_seed_offers_held_back": held_seed_offers,
                "suppressed_seed_offers": suppressed_seed_offers,
                "approved_but_not_public_ready_count": sum(
                    1
                    for item in hub.get("blocked_suppressed_seed_offers", [])
                    if item.get("display_item_type") == "suppressed_approved_but_not_public_ready"
                ),
                "empty_state": {
                    "empty_state_type": hub.get("empty_state_type"),
                    "headline": hub.get("empty_state_headline"),
                    "body": hub.get("empty_state_body"),
                    "recommended_cta_label": hub.get("recommended_cta_label"),
                    "recommended_cta_target": hub.get("recommended_cta_target"),
                }
                if mode in {"empty_state", "suppress_offer_block", "needs_review"}
                else None,
                "caution_flags": hub.get("caution_flags", []),
                "public_render_safety_notes": [
                    "No fake dates.",
                    "Generated seed offers remain hub offers only.",
                    "Approved seed offers require public_ready and present_in_enrollware.",
                    "Offers inside the public display cutoff window are suppressed from public preview only.",
                    "Needs-review seed offers are held back from public preview.",
                ],
            }
        )

    summary = {
        "hubs_previewed": len(previews),
        "current_class_hubs": mode_counts.get("current_classes", 0),
        "approved_seed_hubs": mode_counts.get("approved_seed_offers", 0),
        "mixed_hubs": mode_counts.get("mixed_current_and_seed", 0),
        "empty_state_hubs": mode_counts.get("empty_state", 0),
        "suppress_offer_block_hubs": mode_counts.get("suppress_offer_block", 0),
        "needs_review_hubs": mode_counts.get("needs_review", 0),
        "held_needs_review_offers": held_needs_review,
        "suppressed_offers": suppressed_total,
        "suppressed_cutoff_window": suppressed_cutoff_window,
        "current_enrollware_classes_suppressed_by_cutoff": suppressed_cutoff_window,
        "approved_but_not_public_ready": suppressed_approved_but_not_public_ready,
        "suppressed_approved_but_not_public_ready": suppressed_approved_but_not_public_ready,
        "display_mode_counts": dict(sorted(mode_counts.items())),
    }
    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "source_mode": source_mode,
        "inputs": model.get("inputs", {}),
        "summary": summary,
        "hubs": previews,
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Hub Render Preview",
        "",
        "> REPORT ONLY - NO PUBLIC HUB PAGES, CTAS, ENROLLWARE LINKS, SCHEDULES, OR CLASS LANDERS MODIFIED",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Source mode: {report['source_mode']}",
        f"- Hubs previewed: {report['summary']['hubs_previewed']}",
        f"- Current-class hubs: {report['summary']['current_class_hubs']}",
        f"- Approved-seed hubs: {report['summary']['approved_seed_hubs']}",
        f"- Mixed hubs: {report['summary']['mixed_hubs']}",
        f"- Empty-state hubs: {report['summary']['empty_state_hubs']}",
        f"- Held needs-review offers: {report['summary']['held_needs_review_offers']}",
        f"- Suppressed offers: {report['summary']['suppressed_offers']}",
        f"- Suppressed by cutoff window: {report['summary']['suppressed_cutoff_window']}",
        f"- Approved but not public ready: {report['summary']['approved_but_not_public_ready']}",
        f"- Display mode counts: {json.dumps(report['summary']['display_mode_counts'], sort_keys=True)}",
        "",
    ]

    for hub in report["hubs"]:
        lines.append(f"## {hub.get('hub_title') or hub.get('hub_key')}")
        lines.append(f"- Hub key: {hub.get('hub_key')}")
        lines.append(f"- URL: {hub.get('hub_url')}")
        lines.append(f"- Display mode: {hub.get('display_mode')}")
        lines.append(f"- Current classes: {hub.get('current_enrollware_class_count')}")
        lines.append(f"- Current classes suppressed by cutoff: {hub.get('cutoff_suppressed_current_enrollware_class_count')}")
        lines.append(f"- Approved seed offers: {hub.get('approved_seed_offer_count')}")
        lines.append(f"- Held for review: {hub.get('held_needs_review_seed_offer_count')}")
        lines.append(f"- Suppressed offers: {hub.get('suppressed_offer_count')}")
        lines.append(f"- Approved but not public ready: {hub.get('approved_but_not_public_ready_count')}")
        lines.append(f"- Caution flags: {', '.join(hub.get('caution_flags') or []) if hub.get('caution_flags') else 'none'}")
        lines.append("")
        lines.append("Preview:")
        if hub["current_enrollware_classes_preview"]:
            for item in hub["current_enrollware_classes_preview"][:5]:
                lines.append(f"- {item.get('title')} - {item.get('date_label')}, {item.get('start_time')} - Enrollware-backed")
        if hub["approved_seed_offers_preview"]:
            for item in hub["approved_seed_offers_preview"][:5]:
                lines.append(f"- {item.get('title')} - {item.get('date_label')}, {item.get('start_time')} - approved seed hub offer only")
        if hub["empty_state"]:
            empty = hub["empty_state"]
            lines.append(f"- Headline: {empty.get('headline')}")
            lines.append(f"- Body: {empty.get('body')}")
            lines.append(f"- CTA: {empty.get('recommended_cta_label')} -> {empty.get('recommended_cta_target')}")
        if not hub["current_enrollware_classes_preview"] and not hub["approved_seed_offers_preview"] and not hub["empty_state"]:
            lines.append("- No public offer block would be shown by this preview.")
        if hub["needs_review_seed_offers_held_back"]:
            lines.append("")
            lines.append("Held back for review:")
            for item in hub["needs_review_seed_offers_held_back"][:5]:
                lines.append(f"- {item.get('title')} - {item.get('date_label')}, {item.get('start_time')} - {item.get('approval_status')}")
        if hub["suppressed_seed_offers"]:
            lines.append("")
            lines.append("Suppressed from public preview:")
            for item in hub["suppressed_seed_offers"][:5]:
                lines.append(f"- {item.get('title')} - {item.get('date_label')}, {item.get('start_time')} - {item.get('display_item_type')}")
                lines.append(f"  - Reason: {item.get('suppression_reason')}")
                if item.get("public_ready_block_reason"):
                    lines.append(f"  - Public-ready block: {item.get('public_ready_block_reason')}")
        if hub["cutoff_suppressed_current_enrollware_classes"]:
            lines.append("")
            lines.append("Suppressed by public display cutoff:")
            for item in hub["cutoff_suppressed_current_enrollware_classes"][:5]:
                lines.append(f"- {item.get('title')} - {item.get('date_label')}, {item.get('start_time')} - {item.get('public_visibility_status')}")
                lines.append(f"  - Note: {item.get('public_visibility_note')}")
                lines.append(f"  - Hours until start: {item.get('hours_until_start')} / cutoff hours: {item.get('cutoff_hours')}")
        lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build report-only hub render preview.")
    parser.add_argument("--source", choices=sorted(SOURCE_MODES), default="auto", help="Seed calendar source mode.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_preview(args.source)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print("Hub render preview generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
