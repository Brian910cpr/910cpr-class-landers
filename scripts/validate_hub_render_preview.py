#!/usr/bin/env python3
"""Validate report-only hub render preview safety rules."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_hub_render_preview import build_preview
from scripts.build_instructor_availability_report import DEBUG_DIR, SOURCE_MODES, TZ


REPORT_JSON_PATH = DEBUG_DIR / "hub_render_preview_validation.json"
REPORT_MD_PATH = DEBUG_DIR / "hub_render_preview_validation.md"


def add_violation(
    violations: list[dict[str, Any]],
    rule_key: str,
    hub: dict[str, Any],
    recommendation: str,
    item: dict[str, Any] | None = None,
    detail: str | None = None,
) -> None:
    violations.append(
        {
            "rule_key": rule_key,
            "hub_key": hub.get("hub_key"),
            "hub_url": hub.get("hub_url"),
            "seed_id": item.get("seed_id") if item else None,
            "offending_item": item,
            "detail": detail,
            "recommendation": recommendation,
        }
    )


def validate_preview(source_mode: str) -> dict[str, Any]:
    preview = build_preview(source_mode)
    violations: list[dict[str, Any]] = []
    arc_hsi_empty_state: dict[str, dict[str, Any]] = {}
    approved_seed_offers = 0
    held_needs_review = 0
    suppressed_approved_but_not_public_ready = int(preview.get("summary", {}).get("suppressed_approved_but_not_public_ready") or 0)
    suppressed_cutoff_window = int(preview.get("summary", {}).get("suppressed_cutoff_window") or 0)

    for hub in preview.get("hubs", []):
        hub_key = str(hub.get("hub_key") or "")
        display_mode = str(hub.get("display_mode") or "")
        approved_items = hub.get("approved_seed_offers_preview", [])
        held_items = hub.get("needs_review_seed_offers_held_back", [])
        suppressed_items = hub.get("suppressed_seed_offers", [])

        approved_seed_offers += len(approved_items)
        held_needs_review += int(hub.get("held_needs_review_seed_offer_count") or 0)

        for item in approved_items:
            is_appointment_seed = item.get("seed_publication_mode") == "appointment_seed_offer"
            if item.get("public_visibility_status") == "suppressed_cutoff_window":
                add_violation(
                    violations,
                    "no_public_display_inside_cutoff_window",
                    hub,
                    "Suppress this item from public display until it is outside the cutoff policy or handle manually.",
                    item,
                    "Approved seed offer appears publicly even though public_visibility_status is suppressed_cutoff_window.",
                )
            if item.get("public_ready") is not True:
                add_violation(
                    violations,
                    "approved_seed_requires_public_ready",
                    hub,
                    "Suppress this seed until public_ready is true.",
                    item,
                    "Approved seed offer appears in preview with public_ready != true.",
                )
            if is_appointment_seed:
                if item.get("enrollware_presence_status") != "not_required_for_appointment_seed":
                    add_violation(
                        violations,
                        "appointment_seed_presence_must_be_not_required",
                        hub,
                        "Appointment seed offers should mark Enrollware presence as not_required_for_appointment_seed.",
                        item,
                        "Appointment seed offer has the wrong Enrollware presence status.",
                    )
                if not item.get("appointment_registration_url"):
                    add_violation(
                        violations,
                        "appointment_seed_requires_registration_url",
                        hub,
                        "Suppress appointment seed offers until an appointment registration URL exists.",
                        item,
                        "Appointment seed offer appears without appointment registration URL.",
                    )
                if item.get("standalone_class_lander_allowed") is not False:
                    add_violation(
                        violations,
                        "appointment_seed_must_not_create_class_lander",
                        hub,
                        "Keep appointment seed offers hub-only and block standalone class landers.",
                        item,
                        "Appointment seed offer does not explicitly block standalone class landers.",
                    )
                if item.get("class_lander_created") is not False:
                    add_violation(
                        violations,
                        "appointment_seed_no_class_lander_created",
                        hub,
                        "Appointment seed render preview must report class_lander_created false.",
                        item,
                        "Appointment seed offer indicates a class lander was created.",
                    )
                if item.get("public_schedule_row_created") is not False:
                    add_violation(
                        violations,
                        "appointment_seed_no_public_schedule_row_created",
                        hub,
                        "Appointment seed render preview must report public_schedule_row_created false.",
                        item,
                        "Appointment seed offer indicates a public_schedule row was created.",
                    )
                if item.get("render_source") != "auto_public_appointment_seed":
                    add_violation(
                        violations,
                        "appointment_seed_render_source",
                        hub,
                        "Appointment seed hub display should identify render_source as auto_public_appointment_seed.",
                        item,
                        "Appointment seed offer has missing or incorrect render_source.",
                    )
            elif item.get("enrollware_presence_status") != "present_in_enrollware":
                add_violation(
                    violations,
                    "approved_seed_requires_enrollware_presence",
                    hub,
                    "Suppress real class/session seed mode until it is present in current Enrollware source data.",
                    item,
                    "Approved seed offer appears without present_in_enrollware.",
                )
            if item.get("display_note") and "class lander" not in str(item.get("display_note")).lower():
                add_violation(
                    violations,
                    "seed_offer_must_not_imply_class_lander",
                    hub,
                    "Make the preview explicitly state hub offer only and no standalone class lander.",
                    item,
                    "Seed display note does not clearly block standalone class lander creation.",
                )

        for item in hub.get("current_enrollware_classes_preview", []):
            if item.get("public_visibility_status") == "suppressed_cutoff_window":
                add_violation(
                    violations,
                    "no_public_display_inside_cutoff_window",
                    hub,
                    "Suppress this current class from public display because it is inside the cutoff window.",
                    item,
                    "Current Enrollware class appears publicly even though public_visibility_status is suppressed_cutoff_window.",
                )

        for item in held_items:
            if item.get("approval_status") == "needs_review" and item in approved_items:
                add_violation(
                    violations,
                    "needs_review_seed_not_public_display",
                    hub,
                    "Keep needs-review seed offers in held-back report sections only.",
                    item,
                    "Needs-review seed offer appears as a public display item.",
                )

        for item in suppressed_items:
            if item.get("display_item_type") == "suppressed_approved_but_not_public_ready":
                is_appointment_seed = item.get("seed_publication_mode") == "appointment_seed_offer"
                presence_ok = (
                    item.get("enrollware_presence_status") == "not_required_for_appointment_seed"
                    if is_appointment_seed
                    else item.get("enrollware_presence_status") == "present_in_enrollware"
                )
                if item.get("public_ready") is True and presence_ok:
                    add_violation(
                        violations,
                        "approved_public_ready_seed_should_not_be_suppressed",
                        hub,
                        "Classify this seed as approved_seed_offer if all public-ready gates pass.",
                        item,
                        "Suppressed approved seed appears to satisfy public-ready gates.",
                    )

        if display_mode == "mixed_current_and_seed":
            for item in approved_items:
                is_appointment_seed = item.get("seed_publication_mode") == "appointment_seed_offer"
                presence_ok = (
                    item.get("enrollware_presence_status") == "not_required_for_appointment_seed"
                    if is_appointment_seed
                    else item.get("enrollware_presence_status") == "present_in_enrollware"
                )
                if item.get("public_ready") is not True or not presence_ok:
                    add_violation(
                        violations,
                        "mixed_mode_requires_public_ready_seed_offers",
                        hub,
                        "Mixed display mode may include only public-ready seed offers with the correct presence rule for their publication mode.",
                        item,
                        "Mixed mode contains a seed that is not public-ready or has an invalid presence status.",
                    )

        if hub_key in {"arc", "hsi"}:
            empty_state = hub.get("empty_state") or {}
            arc_hsi_empty_state[hub_key] = {
                "display_mode": display_mode,
                "headline": empty_state.get("headline"),
                "recommended_cta_label": empty_state.get("recommended_cta_label"),
                "recommended_cta_target": empty_state.get("recommended_cta_target"),
                "caution_flags": hub.get("caution_flags", []),
            }
            has_fake_dates = bool(hub.get("current_enrollware_classes_preview") or hub.get("approved_seed_offers_preview"))
            if display_mode == "empty_state" and has_fake_dates:
                add_violation(
                    violations,
                    "arc_hsi_empty_hubs_no_fake_dates",
                    hub,
                    "Do not show dated offers on empty ARC/HSI hubs unless backed by current Enrollware or public-ready seeds.",
                    detail="ARC/HSI empty-state hub has dated preview items.",
                )
            if display_mode == "empty_state":
                empty_type = str(empty_state.get("empty_state_type") or "")
                cta_target = str(empty_state.get("recommended_cta_target") or "")
                if empty_type != "show_call_to_schedule" or "group-training" not in cta_target:
                    add_violation(
                        violations,
                        "arc_hsi_empty_hubs_call_to_schedule",
                        hub,
                        "Use call-to-schedule/request CTA messaging for empty ARC/HSI hubs.",
                        detail="ARC/HSI empty-state messaging is not call-to-schedule/request oriented.",
                    )

    by_rule = Counter(str(row["rule_key"]) for row in violations)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for violation in violations:
        grouped[str(violation["rule_key"])].append(violation)

    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "source_mode": source_mode,
        "validation_passed": not violations,
        "violation_count": len(violations),
        "summary": {
            "approved_seed_offers": approved_seed_offers,
            "held_needs_review_seed_offers": held_needs_review,
            "suppressed_approved_but_not_public_ready": suppressed_approved_but_not_public_ready,
            "suppressed_cutoff_window": suppressed_cutoff_window,
            "hubs_previewed": preview.get("summary", {}).get("hubs_previewed"),
            "display_mode_counts": preview.get("summary", {}).get("display_mode_counts", {}),
            "violations_by_rule": dict(sorted(by_rule.items())),
        },
        "arc_hsi_empty_state_confirmation": arc_hsi_empty_state,
        "violations_by_rule": dict(sorted(grouped.items())),
        "violations": violations,
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Hub Render Preview Validation",
        "",
        "> REPORT ONLY - NO PUBLIC HUB PAGES, CTAS, ENROLLWARE LINKS, SCHEDULES, OR CLASS LANDERS MODIFIED",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Source mode: {report['source_mode']}",
        f"- Validation passed: {report['validation_passed']}",
        f"- Violation count: {report['violation_count']}",
        f"- Approved seed offers: {report['summary']['approved_seed_offers']}",
        f"- Held needs-review seed offers: {report['summary']['held_needs_review_seed_offers']}",
        f"- Suppressed approved-but-not-public-ready: {report['summary']['suppressed_approved_but_not_public_ready']}",
        f"- Suppressed by cutoff window: {report['summary']['suppressed_cutoff_window']}",
        f"- Violations by rule: {json.dumps(report['summary']['violations_by_rule'], sort_keys=True)}",
        "",
        "## ARC/HSI Empty-State Confirmation",
        "",
    ]
    for hub_key, row in sorted(report["arc_hsi_empty_state_confirmation"].items()):
        lines.append(f"### {hub_key}")
        lines.append(f"- Display mode: {row.get('display_mode')}")
        lines.append(f"- Headline: {row.get('headline')}")
        lines.append(f"- CTA: {row.get('recommended_cta_label')} -> {row.get('recommended_cta_target')}")
        lines.append(f"- Caution flags: {', '.join(row.get('caution_flags') or []) if row.get('caution_flags') else 'none'}")
        lines.append("")

    lines.append("## Violations")
    lines.append("")
    if not report["violations"]:
        lines.append("No hub render preview safety-rule violations found.")
        lines.append("")
    else:
        for rule_key, violations in report["violations_by_rule"].items():
            lines.append(f"### {rule_key}")
            for violation in violations:
                lines.append(f"- Hub: {violation.get('hub_key')} ({violation.get('hub_url')})")
                if violation.get("seed_id"):
                    lines.append(f"  - Seed ID: {violation.get('seed_id')}")
                lines.append(f"  - Detail: {violation.get('detail')}")
                lines.append(f"  - Recommendation: {violation.get('recommendation')}")
            lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate report-only hub render preview safety rules.")
    parser.add_argument("--source", choices=sorted(SOURCE_MODES), default="auto", help="Seed calendar source mode.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = validate_preview(args.source)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(f"Validation passed: {report['validation_passed']}")
    print(f"Violation count: {report['violation_count']}")
    return 0 if report["validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
