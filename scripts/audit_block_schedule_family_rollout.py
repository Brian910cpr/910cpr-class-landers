from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.block_start_time_selector import (
    PUBLIC_OFFER_POLICY_PATH,
    ROOT,
    BlockSelectorInputError,
    build_block_schedule_page,
    load_block_schedule_page_configs,
    read_required_json,
)
from scripts.build_bls_block_schedule_pilot import render_html, run_page


REPORT_JSON_PATH = ROOT / "data" / "audit" / "block_schedule_family_rollout_report.json"
REPORT_MD_PATH = ROOT / "data" / "audit" / "block_schedule_family_rollout_report.md"
NEXT_PUBLIC_PAGE_KEYS = ("acls", "pals", "heartsaver")


def course_ids(page_config: dict[str, Any]) -> list[str]:
    return [str(item.get("course_id")) for item in page_config.get("course_options", []) if item.get("course_id")]


def page_audit(payload: dict[str, Any]) -> dict[str, Any]:
    html = render_html(payload)
    urls = [offer["appointmentUrl"] for offer in payload.get("offers", [])]
    invalid_urls = [
        url for url in urls
        if "appointmentDayId=" not in url or "startTime=" not in url or "courseId=" not in url
    ]
    return {
        "invalid_register_urls": len(invalid_urls),
        "full_availability_block_labels_visible": "12:00 AM-6:00 PM" in html or "12:00 AM\u20136:00 PM" in html,
        "midnight_or_overnight_starts_visible": "12:00 AM" in html or "overnight" in html.lower(),
        "debug_metadata_visible": "appointmentDayId ${course.appointmentDayId}" in html or "courseId ${course.courseId}" in html,
        "hard_duration_text_visible": "durationMinutes} min" in html or " 120 min" in html,
        "course_first_default_supported": "let selectedCourseId =" in html and "function activeCourseIds()" in html,
        "compare_mode_supported": "compareMode" in html and "Need " in html,
        "show_all_mode_supported": "showAllOptions" in html and "showAllFromDeepLink" in html,
        "delivery_filter_supported": "deliveryFromDeepLink" in html and "delivery-filter" in html,
        "deep_links_supported": "courseIdFromDeepLink" in html and "deliveryFromDeepLink" in html and "showAllFromDeepLink" in html,
        "offsite_private_locations_visible": any(
            "offsite" in offer.get("location", "").lower() or "private" in offer.get("location", "").lower()
            for offer in payload.get("offers", [])
        ),
    }


def readiness_for_page(page_key: str, page_config: dict[str, Any], public_offer_policy: dict[str, Any]) -> dict[str, Any]:
    ids = course_ids(page_config)
    disabled_families = {str(item) for item in public_offer_policy.get("disabled_course_families", [])}
    issues: list[str] = []
    payload: dict[str, Any] | None = None
    audit: dict[str, Any] | None = None
    try:
        payload = build_block_schedule_page(page_config)
        audit = page_audit(payload)
    except BlockSelectorInputError as exc:
        issues.append(str(exc))
    except Exception as exc:  # pragma: no cover - retained for report safety.
        issues.append(f"{type(exc).__name__}: {exc}")

    if page_config.get("family") in disabled_families:
        issues.append("family_disabled_by_public_offer_policy_requires_explicit_approval")
    if payload:
        counts = payload["counts"]
        if counts["publicSelectableOfferCount"] <= 0:
            issues.append("no_public_selectable_offers")
        if audit:
            if audit["invalid_register_urls"]:
                issues.append("invalid_register_urls")
            if audit["full_availability_block_labels_visible"]:
                issues.append("full_availability_block_labels_visible")
            if audit["midnight_or_overnight_starts_visible"]:
                issues.append("midnight_or_overnight_starts_visible")
            if audit["debug_metadata_visible"]:
                issues.append("debug_metadata_visible")
            if audit["hard_duration_text_visible"]:
                issues.append("hard_duration_text_visible")
            if not audit["course_first_default_supported"]:
                issues.append("course_first_default_not_supported")
            if not audit["show_all_mode_supported"]:
                issues.append("show_all_mode_not_supported")
            if not audit["deep_links_supported"]:
                issues.append("deep_links_not_supported")
            if audit["offsite_private_locations_visible"]:
                issues.append("offsite_private_locations_visible")
    else:
        counts = {
            "publicSelectableOfferCount": 0,
            "publicSelectableDateCount": 0,
            "publicSelectableStartTimeCount": 0,
            "rejectedOfferCount": 0,
        }

    top_rejections = dict(Counter((payload or {}).get("rejectionReasonCounts", {})).most_common(10))
    release_recommendation = "ready_for_direct_url_release"
    if "no_public_selectable_offers" in issues:
        release_recommendation = "do_not_release_direct_url_page_yet"
    elif issues:
        release_recommendation = "fix_blockers_before_release"
    return {
        "page_key": page_key,
        "family": page_config.get("family"),
        "certifying_body": page_config.get("certifying_body"),
        "output_path": page_config.get("output_path"),
        "course_ids": ids,
        "course_rules_found": bool(payload),
        "counts": counts,
        "top_rejection_reasons": top_rejections,
        "page_audit": audit,
        "issues": issues,
        "release_recommendation": release_recommendation,
        "ready_for_generation": not issues,
    }


def render_report(report: dict[str, Any]) -> str:
    lines = [
        "# Block Schedule Family Rollout Report",
        "",
        "Read-only rollout audit for config-driven block schedule pages. Enrollware course IDs and appointment URL behavior were not changed.",
        "",
        "## Summary",
        "",
    ]
    for item in report["families"]:
        counts = item["counts"]
        ready = "ready" if item["ready_for_generation"] else "blocked"
        lines.append(
            f"- `{item['page_key']}` ({item['family']}): {ready}; "
            f"offers `{counts.get('publicSelectableOfferCount', 0)}`, "
            f"dates `{counts.get('publicSelectableDateCount', 0)}`, "
            f"start times `{counts.get('publicSelectableStartTimeCount', 0)}`"
        )
    lines.extend(["", "## Details", ""])
    for item in report["families"]:
        lines.extend([
            f"### {item['page_key']}",
            "",
            f"- Family: `{item['family']}`",
            f"- Certifying body: `{item['certifying_body']}`",
            f"- Output path: `{item['output_path']}`",
            f"- Course IDs: `{', '.join(item['course_ids'])}`",
            f"- Ready for generation: `{item['ready_for_generation']}`",
            f"- Release recommendation: `{item.get('release_recommendation', 'UNKNOWN')}`",
            f"- Public-selectable offers: `{item['counts'].get('publicSelectableOfferCount', 0)}`",
            f"- Public-selectable dates: `{item['counts'].get('publicSelectableDateCount', 0)}`",
            f"- Public-selectable start times: `{item['counts'].get('publicSelectableStartTimeCount', 0)}`",
            f"- Rejected course/start evaluations: `{item['counts'].get('rejectedOfferCount', 0)}`",
            "",
            "Issues:",
        ])
        if item["issues"]:
            lines.extend(f"- `{issue}`" for issue in item["issues"])
        else:
            lines.append("- None")
        lines.extend(["", "Top rejection reasons:"])
        if item["top_rejection_reasons"]:
            lines.extend(f"- `{reason}`: {count}" for reason, count in item["top_rejection_reasons"].items())
        else:
            lines.append("- None")
        lines.append("")
    if report["generated_pages"]:
        lines.extend(["## Generated Pages", ""])
        lines.extend(f"- `{page}`" for page in report["generated_pages"])
    return "\n".join(lines).rstrip() + "\n"


def run() -> dict[str, Any]:
    configs = load_block_schedule_page_configs()
    public_offer_policy = read_required_json(PUBLIC_OFFER_POLICY_PATH)
    families = [readiness_for_page(key, config, public_offer_policy) for key, config in configs.items()]
    by_key = {item["page_key"]: item for item in families}
    generated_pages: list[str] = []
    for key in NEXT_PUBLIC_PAGE_KEYS:
        if by_key.get(key, {}).get("ready_for_generation"):
            result = run_page(key)
            generated_pages.append(str(result["output_paths"][-1]))

    report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "generated_pages": generated_pages,
        "families": families,
    }
    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(render_report(report), encoding="utf-8")
    return report


def main() -> int:
    report = run()
    print("Block schedule family rollout audit complete.")
    for item in report["families"]:
        counts = item["counts"]
        print(
            f"{item['page_key']}: ready={item['ready_for_generation']} "
            f"offers={counts.get('publicSelectableOfferCount', 0)} "
            f"dates={counts.get('publicSelectableDateCount', 0)} "
            f"starts={counts.get('publicSelectableStartTimeCount', 0)}"
        )
    print("Generated pages:")
    for page in report["generated_pages"]:
        print(f"- {page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
