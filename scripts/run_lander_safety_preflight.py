#!/usr/bin/env python3
"""Run report-only Lander safety preflight checks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_lander_offers_against_enrollware import build_report as build_offer_audit
from scripts.build_instructor_availability_report import DEBUG_DIR, SOURCE_MODES, TZ
from scripts.validate_hub_render_preview import validate_preview
from scripts.validate_public_artifact_cleanup_execution import build_validation_report as build_cleanup_validation


REPORT_JSON_PATH = DEBUG_DIR / "lander_safety_preflight.json"
REPORT_MD_PATH = DEBUG_DIR / "lander_safety_preflight.md"
PUBLIC_STATUS_PATHS = [
    "docs",
    "public_schedule.json",
    "live-schedule_future.json",
    "data/config/slug_hubs.json",
]


def git_status_for_public_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short", "--", *PUBLIC_STATUS_PATHS],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [f"git status failed: {result.stderr.strip()}"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def final_status(
    hub_validation: dict[str, Any],
    cleanup_validation: dict[str, Any],
    offer_audit: dict[str, Any],
    public_status_lines: list[str],
) -> str:
    if not hub_validation.get("validation_passed"):
        return "failed_validation"
    if public_status_lines:
        return "failed_validation"
    if cleanup_validation.get("summary", {}).get("executable_actions", 0):
        return "blocked_needs_review"
    audit_summary = offer_audit.get("summary", {})
    if audit_summary.get("missing", 0) or audit_summary.get("ambiguous", 0) or audit_summary.get("recommended_removals", 0):
        return "blocked_needs_review"
    return "safe_report_only"


def build_preflight(source_mode: str) -> dict[str, Any]:
    hub_validation = validate_preview(source_mode)
    cleanup_validation = build_cleanup_validation()
    offer_audit = build_offer_audit()
    public_status_lines = git_status_for_public_paths()
    cleanup_summary = cleanup_validation.get("summary", {})
    hub_summary = hub_validation.get("summary", {})
    audit_summary = offer_audit.get("summary", {})
    public_files_changed = bool(public_status_lines)
    status = final_status(hub_validation, cleanup_validation, offer_audit, public_status_lines)
    failed_checks: list[str] = []

    if not hub_validation.get("validation_passed"):
        failed_checks.append("hub_render_preview_validation")
    if cleanup_summary.get("executable_actions", 0):
        failed_checks.append("cleanup_actions_executable")
    if public_files_changed:
        failed_checks.append("public_files_dirty")
    if audit_summary.get("missing", 0) or audit_summary.get("ambiguous", 0) or audit_summary.get("recommended_removals", 0):
        failed_checks.append("lander_offer_enrollware_presence_needs_review")

    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "source_mode": source_mode,
        "summary": {
            "hub_preview_validation_passed": bool(hub_validation.get("validation_passed")),
            "hub_preview_violation_count": int(hub_validation.get("violation_count") or 0),
            "approved_seed_offers": int(hub_summary.get("approved_seed_offers") or 0),
            "held_needs_review_seed_offers": int(hub_summary.get("held_needs_review_seed_offers") or 0),
            "cleanup_executable_actions": int(cleanup_summary.get("executable_actions") or 0),
            "cleanup_blocked_actions": int(cleanup_summary.get("blocked_actions") or 0),
            "fallback_redirects_blocked": int(cleanup_summary.get("fallback_redirects_blocked") or 0),
            "stale_missing_enrollware_offers": int(audit_summary.get("missing") or 0),
            "ambiguous_enrollware_offers": int(audit_summary.get("ambiguous") or 0),
            "recommended_public_offer_removals": int(audit_summary.get("recommended_removals") or 0),
            "public_files_changed": public_files_changed,
            "final_preflight_status": status,
            "failed_checks": failed_checks,
        },
        "hub_render_preview_validation": {
            "validation_passed": hub_validation.get("validation_passed"),
            "violation_count": hub_validation.get("violation_count"),
            "violations_by_rule": hub_summary.get("violations_by_rule", {}),
            "arc_hsi_empty_state_confirmation": hub_validation.get("arc_hsi_empty_state_confirmation", {}),
        },
        "public_artifact_cleanup_execution_validation": {
            "summary": cleanup_summary,
            "approval_record_count": cleanup_validation.get("approval_record_count"),
        },
        "lander_offer_enrollware_presence_audit": {
            "summary": audit_summary,
            "source_files_inspected": offer_audit.get("source_files_inspected", []),
        },
        "public_git_status": public_status_lines,
        "safety_notes": [
            "Report-only preflight; no public files are written by this script.",
            "safe_report_only means report gates passed and no public-output paths are dirty.",
            "blocked_needs_review means report-only checks found stale/offending candidates or executable cleanup approvals that require operator review.",
            "failed_validation means a hard safety validation failed or public files are dirty.",
        ],
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary = report["summary"]
    lines = [
        "# Lander Safety Preflight",
        "",
        "> REPORT ONLY - NO PUBLIC PAGES, CTAS, ENROLLWARE LINKS, SCHEDULES, OR CLASS LANDERS MODIFIED",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Source mode: {report['source_mode']}",
        f"- Final preflight status: {summary['final_preflight_status']}",
        f"- Hub preview validation passed: {summary['hub_preview_validation_passed']}",
        f"- Hub preview violations: {summary['hub_preview_violation_count']}",
        f"- Approved seed offers: {summary['approved_seed_offers']}",
        f"- Held needs-review seed offers: {summary['held_needs_review_seed_offers']}",
        f"- Cleanup executable actions: {summary['cleanup_executable_actions']}",
        f"- Cleanup blocked actions: {summary['cleanup_blocked_actions']}",
        f"- Fallback redirects blocked: {summary['fallback_redirects_blocked']}",
        f"- Stale/missing Enrollware offers: {summary['stale_missing_enrollware_offers']}",
        f"- Ambiguous Enrollware offers: {summary['ambiguous_enrollware_offers']}",
        f"- Recommended public offer removals: {summary['recommended_public_offer_removals']}",
        f"- Public files changed: {summary['public_files_changed']}",
        f"- Failed checks: {', '.join(summary['failed_checks']) if summary['failed_checks'] else 'none'}",
        "",
        "## Hub Preview Validation",
        "",
        f"- Validation passed: {report['hub_render_preview_validation']['validation_passed']}",
        f"- Violations by rule: {json.dumps(report['hub_render_preview_validation']['violations_by_rule'], sort_keys=True)}",
        "",
        "## Cleanup Execution Validation",
        "",
        f"- Executable actions: {summary['cleanup_executable_actions']}",
        f"- Blocked actions: {summary['cleanup_blocked_actions']}",
        f"- Fallback redirects blocked: {summary['fallback_redirects_blocked']}",
        "",
        "## Enrollware Offer Audit",
        "",
        f"- Missing: {summary['stale_missing_enrollware_offers']}",
        f"- Ambiguous: {summary['ambiguous_enrollware_offers']}",
        f"- Recommended removals: {summary['recommended_public_offer_removals']}",
        "",
        "## Public Git Status",
        "",
    ]
    if report["public_git_status"]:
        lines.extend(f"- {line}" for line in report["public_git_status"])
    else:
        lines.append("No public-output path changes detected.")

    lines.extend(["", "## ARC/HSI Empty-State Confirmation", ""])
    for hub_key, row in sorted(report["hub_render_preview_validation"]["arc_hsi_empty_state_confirmation"].items()):
        lines.append(f"### {hub_key}")
        lines.append(f"- Display mode: {row.get('display_mode')}")
        lines.append(f"- Headline: {row.get('headline')}")
        lines.append(f"- CTA: {row.get('recommended_cta_label')} -> {row.get('recommended_cta_target')}")
        lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run report-only Lander safety preflight.")
    parser.add_argument("--source", choices=sorted(SOURCE_MODES), default="auto", help="Seed calendar source mode.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_preflight(args.source)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0 if report["summary"]["final_preflight_status"] != "failed_validation" else 1


if __name__ == "__main__":
    raise SystemExit(main())
