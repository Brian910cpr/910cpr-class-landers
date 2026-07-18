from __future__ import annotations

import html
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from scripts.block_start_time_selector import (
    ROOT,
    apply_final_live_availability_guard,
    build_block_schedule_page,
    build_bls_pilot_schedule,
    load_block_schedule_page_configs,
)


REPORT_JSON_PATH = ROOT / "data" / "audit" / "bls_block_schedule_pilot.json"
REPORT_MD_PATH = ROOT / "data" / "audit" / "bls_block_schedule_pilot_report.md"
HTML_PATH = ROOT / "docs" / "bls-schedule.html"
COURSE_DESCRIPTIONS_PATH = ROOT / "data" / "content" / "course_descriptions.json"
SELECTOR_AVAILABILITY_DIR = ROOT / "docs" / "data" / "block-selector-availability"


def load_course_descriptions() -> dict[str, dict[str, Any]]:
    if not COURSE_DESCRIPTIONS_PATH.exists():
        return {}
    payload = json.loads(COURSE_DESCRIPTIONS_PATH.read_text(encoding="utf-8"))
    courses = payload.get("courses", {}) if isinstance(payload, dict) else {}
    return {str(course_id): course for course_id, course in courses.items() if isinstance(course, dict)}


def selector_availability_path(page_key: str) -> Path:
    safe_key = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in str(page_key or "selector"))
    return SELECTOR_AVAILABILITY_DIR / f"{safe_key}.json"


def public_selector_availability_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": "selector-resolved-availability.v1",
        "generatedAt": payload.get("generatedAt"),
        "pageKey": payload.get("pageKey"),
        "publicPage": payload.get("publicPage"),
        "sourceArtifacts": {
            "hotSyncCurrentOccupancy": "data/sessions_current.json",
            "publicScheduleFuture": "docs/data/schedule_future.json",
            "liveAvailabilitySnapshot": payload.get("inputFiles", {}).get("liveAvailabilitySnapshot"),
            "courseConsumptionRules": payload.get("inputFiles", {}).get("courseConsumptionRules"),
        },
        "authority": {
            "name": "block_start_time_selector.build_block_schedule_page",
            "description": (
                "Resolved selector availability generated server-side from the same Work Order 1B "
                "occupancy, conflict, course-consumption, public-location, and public-offer rules. "
                "Browsers consume this result and do not run an independent conflict engine."
            ),
        },
        "counts": payload.get("counts", {}),
        "liveAvailabilityGuard": payload.get("liveAvailabilityGuard", {}),
        "dates": payload.get("dates", []),
    }


DEFAULT_COURSE_IMAGES = {
    "BLS": "/images/bls_general.png",
    "ACLS": "/images/acls_general.png",
    "PALS": "/images/pals_general.png",
    "Heartsaver": "/images/heartsaver_general.png",
    "HSI": "/images/Health_and_Safety_Institute_Logo.jpg",
    "ARC": "/images/ARCLTP.png",
}


DELIVERY_HELP = {
    "in-person": {
        "label": "IN-PERSON",
        "help": "Complete the entire course at our Wilmington training center.",
    },
    "skills-session": {
        "label": "ONLINE + SKILLS",
        "help": "Complete the online course first, then attend a shorter in-person skills session.",
    },
    "blended": {
        "label": "BLENDED",
        "help": "Complete assigned online coursework before the scheduled classroom session.",
    },
}


def delivery_label_for_config(value: Any) -> str:
    mode = str(value or "").strip().lower()
    if mode == "in-person":
        return "IN-PERSON"
    if mode in {"skills-session", "online-skills"}:
        return "ONLINE + SKILLS"
    if mode == "blended":
        return "BLENDED"
    return "COURSE"


def render_report(payload: dict[str, Any]) -> str:
    counts = payload["counts"]
    sample_offers = payload["offers"][:10]
    guard = payload.get("liveAvailabilityGuard", {})
    page_title = payload.get("pageConfig", {}).get("title") or "Block-Based Schedule Page"
    lines = [
        f"# {page_title}",
        "",
        "Local build artifact for a customer-facing block schedule page. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.",
        "",
        "## Summary",
        "",
        f"- Availability source used: `{payload['availability_source_used']}`",
        f"- Availability fallback used: `{payload['availability_fallback_used']}`",
        f"- Horizon days: `{payload['horizonDays']}`",
        f"- Minimum lead hours: `{payload['minimumLeadHours']}`",
        f"- Whole block presented as class: `{payload['whole_block_presented_as_class']}`",
        f"- Public-selectable offers: `{counts['publicSelectableOfferCount']}`",
        f"- Public-selectable dates: `{counts['publicSelectableDateCount']}`",
        f"- Public-selectable start times: `{counts['publicSelectableStartTimeCount']}`",
        f"- Rejected course/start evaluations: `{counts['rejectedOfferCount']}`",
        f"- Suppressed stale/orphaned offers: `{counts.get('suppressedStaleOrOrphanedOfferCount', 0)}`",
        "",
        "## Sample Public-Selectable URLs",
        "",
    ]
    if sample_offers:
        lines.extend(["| Date | Start | Course | appointmentDayId | URL |", "| --- | --- | --- | ---: | --- |"])
        for offer in sample_offers:
            lines.append(
                f"| {offer['date']} | {offer['displayStartTime']} | {offer['courseName']} "
                f"(`{offer['courseId']}`) | {offer['appointmentDayId']} | `{offer['appointmentUrl']}` |"
            )
    else:
        lines.append("- None")
    lines.extend(["", "## Top Rejection Reasons", ""])
    reasons = payload.get("rejectionReasonCounts", {})
    if reasons:
        lines.extend(f"- `{reason}`: {count}" for reason, count in list(reasons.items())[:20])
    else:
        lines.append("- None")
    lines.extend(["", "## Final Live Availability Guard", ""])
    lines.extend([
        f"- Enabled: `{guard.get('enabled') is True}`",
        f"- Rendered dates: `{', '.join(guard.get('renderedDates', [])) or 'none'}`",
        f"- Source blocks used: `{len(guard.get('sourceBlocksUsed', []))}`",
        f"- Suppressed available block dates: `{', '.join(guard.get('suppressedAvailableBlockDates', [])) or 'none'}`",
        f"- Suppressed stale/orphaned offer dates: `{', '.join(guard.get('suppressedDates', [])) or 'none'}`",
    ])
    lines.extend(["", "## Source Files", ""])
    lines.extend(f"- `{name}`: `{path}`" for name, path in payload["inputFiles"].items())
    return "\n".join(lines) + "\n"


def css() -> str:
    return """
    :root {
      color-scheme: light;
      --ink: #18212c;
      --muted: #647285;
      --line: #d8dee8;
      --surface: #ffffff;
      --band: #f5f7fa;
      --accent: #0a66a5;
      --accent-dark: #074f80;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: var(--surface);
      line-height: 1.45;
    }
    header, main { max-width: 1120px; margin: 0 auto; padding: 24px; }
    header { border-bottom: 1px solid var(--line); }
    h1 { margin: 0 0 8px; font-size: clamp(1.8rem, 3vw, 2.6rem); letter-spacing: 0; }
    h2 { margin: 0 0 12px; font-size: 1.25rem; letter-spacing: 0; }
    h3 { margin: 0 0 4px; font-size: 1rem; letter-spacing: 0; }
    p { margin: 0 0 12px; }
    .muted { color: var(--muted); }
    .page-subtitle {
      margin: 0 0 8px;
      color: var(--accent-dark);
      font-size: 1.12rem;
      font-weight: 800;
    }
    .back-link {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 14px;
      color: var(--accent-dark);
      font-weight: 800;
      text-decoration: none;
    }
    .back-link:hover,
    .back-link:focus {
      text-decoration: underline;
    }
    .page-heading-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(280px, 380px);
      gap: 24px;
      align-items: center;
    }
    .header-credential {
      display: grid;
      grid-template-columns: 92px minmax(0, 1fr);
      gap: 14px;
      align-items: center;
      padding: 14px 16px;
      border: 2px solid #d71920;
      border-radius: 14px;
      background: linear-gradient(135deg, #fff 0%, #fff7f7 100%);
      box-shadow: 0 10px 24px rgba(120, 18, 22, .12);
    }
    .header-credential img {
      display: block;
      width: 92px;
      max-height: 108px;
      object-fit: contain;
    }
    .header-credential strong {
      display: block;
      color: #9d1118;
      font-size: 1.02rem;
      line-height: 1.2;
    }
    .header-credential p {
      margin: 5px 0 0;
      color: var(--muted);
      font-size: .82rem;
      line-height: 1.35;
    }
    .header-credential-eyebrow {
      display: block;
      margin-bottom: 3px;
      color: #d71920;
      font-size: .7rem;
      font-weight: 900;
      letter-spacing: .08em;
      text-transform: uppercase;
    }
    .family-help {
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--band);
      padding: 14px;
      margin: 14px 0 0;
    }
    .family-help-title {
      margin-bottom: 8px;
      font-weight: 800;
      color: var(--accent-dark);
    }
    .delivery-help-list {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }
    .delivery-help-item {
      display: grid;
      gap: 4px;
      min-width: 0;
    }
    .delivery-help-label {
      font-size: .78rem;
      font-weight: 900;
      color: var(--accent-dark);
      letter-spacing: .02em;
    }
    .delivery-help-copy {
      color: var(--muted);
      font-size: .9rem;
      line-height: 1.35;
    }
    .page-context {
      display: grid;
      gap: 12px;
      margin: 0 0 18px;
    }
    .page-note {
      border: 1px solid var(--line);
      border-left: 4px solid var(--accent);
      border-radius: 8px;
      background: var(--band);
      padding: 14px;
    }
    .page-note h2 {
      font-size: 1.05rem;
      margin-bottom: 6px;
    }
    .page-note ul {
      margin: 8px 0 0;
      padding-left: 20px;
    }
    .selector-shell {
      display: grid;
      gap: 16px;
    }
    .course-selector-panel {
      display: grid;
      gap: 14px;
    }
    .course-selector-top {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    .selector-grid {
      display: grid;
      grid-template-columns: minmax(340px, 1.35fr) minmax(210px, .8fr) minmax(280px, 1fr);
      gap: 16px;
      align-items: start;
    }
    .panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      padding: 16px;
      min-width: 0;
    }
    .button-list { display: grid; gap: 8px; }
    .choice-list {
      display: grid;
      grid-auto-flow: column;
      grid-auto-columns: minmax(260px, 1fr);
      gap: 12px;
      overflow-x: auto;
      overscroll-behavior-inline: contain;
      scroll-snap-type: x proximity;
      padding: 0 0 10px;
      margin-bottom: 0;
    }
    .course-rail {
      position: relative;
      min-width: 0;
      padding: 0 52px;
    }
    .course-rail:not(.has-overflow) .rail-arrow {
      display: none;
    }
    .rail-arrow {
      position: absolute;
      top: 56px;
      z-index: 2;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 42px;
      min-height: 52px;
      padding: 0;
      transform: translateY(-50%);
      border-radius: 999px;
      border: 1px solid rgba(10, 102, 165, .22);
      background: rgba(255, 255, 255, .95);
      color: var(--accent-dark);
      box-shadow: 0 8px 24px rgba(24, 33, 44, .16);
      font-size: 1.5rem;
      font-weight: 900;
      line-height: 1;
      text-align: center;
    }
    .rail-arrow.previous {
      left: 4px;
    }
    .rail-arrow.next {
      right: 4px;
    }
    .rail-arrow:disabled {
      opacity: .32;
      cursor: not-allowed;
      box-shadow: none;
    }
    .option-tools {
      display: flex;
      gap: 14px;
      align-items: center;
      flex-wrap: wrap;
    }
    .disclosure-toggle {
      display: flex;
      gap: 9px;
      align-items: flex-start;
      color: var(--ink);
      font-size: .95rem;
    }
    .disclosure-toggle input {
      margin-top: 3px;
      width: 16px;
      height: 16px;
    }
    .compare-toggle {
      display: flex;
      gap: 9px;
      align-items: flex-start;
      color: var(--ink);
      font-size: .95rem;
    }
    .compare-toggle input {
      margin-top: 3px;
      width: 16px;
      height: 16px;
    }
    button, .register-link {
      min-height: 42px;
      border-radius: 6px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      font: inherit;
      text-align: left;
      padding: 9px 11px;
      cursor: pointer;
    }
    button[aria-pressed="true"] {
      border-color: var(--accent);
      box-shadow: inset 3px 0 0 var(--accent);
      background: #eef7fc;
    }
    .course-card {
      display: grid;
      grid-template-rows: 118px auto;
      gap: 12px;
      width: 100%;
      padding: 0;
      min-height: 258px;
      align-content: start;
      scroll-snap-align: start;
      overflow: hidden;
    }
    .course-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      min-height: 118px;
      border-radius: 6px 6px 0 0;
      background: linear-gradient(135deg, #e8f2f8, #f8fbfd);
      overflow: hidden;
    }
    .course-icon img {
      display: block;
      width: 100%;
      height: 118px;
      object-fit: contain;
      object-position: center;
      padding: 6px;
    }
    .course-icon img.course-image-cover {
      object-fit: cover;
      padding: 0;
    }
    .course-icon-fallback {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 56px;
      height: 56px;
      border-radius: 12px;
      background: #e8f2f8;
      color: var(--accent-dark);
      font-weight: 800;
      font-size: .92rem;
    }
    .course-copy {
      display: grid;
      gap: 6px;
      padding: 0 12px 12px;
    }
    .course-title { font-weight: 700; }
    .course-help {
      color: var(--muted);
      font-size: .86rem;
      line-height: 1.3;
    }
    .course-delivery {
      color: var(--accent-dark);
      font-size: .76rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0;
    }
    .course-details {
      color: var(--muted);
      font-size: .84rem;
      padding: 0 12px 12px;
    }
    .course-details summary {
      cursor: pointer;
      color: var(--accent-dark);
      font-weight: 700;
    }
    .course-details-body {
      display: grid;
      gap: 6px;
      margin-top: 6px;
    }
    .course-details-body ul {
      margin: 0;
      padding-left: 18px;
    }
    .course-page-link {
      color: var(--accent-dark);
      font-weight: 700;
    }
    .month-stack { display: grid; gap: 14px; }
    .month-nav {
      display: none;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }
    .month-nav button {
      min-height: 40px;
      padding: 8px 11px;
      text-align: center;
    }
    .month-nav-title {
      font-weight: 800;
      text-align: center;
    }
    .month-title {
      margin: 0 0 8px;
      font-size: .95rem;
      font-weight: 700;
    }
    .calendar-grid {
      display: grid;
      grid-template-columns: repeat(7, minmax(0, 1fr));
      gap: 4px;
    }
    .weekday, .calendar-pad {
      min-height: 30px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--muted);
      font-size: .75rem;
    }
    .day-button {
      min-height: 34px;
      padding: 0;
      text-align: center;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: .9rem;
    }
    .day-button.is-past,
    .start-grid button.is-past {
      color: #6b7280;
      border-color: #d1d5db;
      background: #f3f4f6;
      cursor: not-allowed;
      opacity: .72;
    }
    .day-button.is-past[aria-pressed="true"],
    .start-grid button.is-past[aria-pressed="true"] {
      border-color: #d1d5db;
      box-shadow: none;
      background: #f3f4f6;
    }
    .course-list { display: grid; gap: 12px; }
    .start-group {
      display: grid;
      gap: 8px;
    }
    .start-group + .start-group { margin-top: 12px; }
    .start-group-label {
      color: var(--muted);
      font-size: .82rem;
      font-weight: 800;
      text-transform: uppercase;
    }
    .start-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .start-grid button {
      min-width: 76px;
      text-align: center;
      justify-content: center;
    }
    .course {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: var(--band);
    }
    .selected-summary {
      display: grid;
      gap: 6px;
    }
    .selected-summary-row {
      color: var(--muted);
      font-size: .92rem;
    }
    .course-meta {
      color: var(--muted);
      font-size: .92rem;
      margin: 3px 0 12px;
    }
    .delivery-badge {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 3px 7px;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--accent-dark);
      background: #eef7fc;
      font-size: .78rem;
      font-weight: 700;
      margin-bottom: 10px;
    }
    .register-note {
      color: var(--muted);
      font-size: .88rem;
      margin-bottom: 12px;
    }
    .register-link {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 40px;
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
      text-decoration: none;
      font-weight: 700;
    }
    .register-link:hover { background: var(--accent-dark); }
    .empty {
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 16px;
      color: var(--muted);
      background: var(--band);
    }
    @media (max-width: 820px) {
      .page-heading-row { grid-template-columns: 1fr; }
      .header-credential { grid-template-columns: 76px minmax(0, 1fr); }
      .header-credential img { width: 76px; max-height: 92px; }
      .selector-grid { grid-template-columns: 1fr; }
      .selector-grid > *,
      .selector-shell > * { min-width: 0; }
      header, main { padding: 18px; }
      .panel { padding: 14px; }
      .course-selector-top {
        display: grid;
        gap: 12px;
      }
      .option-tools {
        display: grid;
        gap: 10px;
      }
      .choice-list {
        grid-auto-columns: minmax(238px, 82%);
        padding-left: 0;
        padding-right: 0;
        scroll-snap-type: x mandatory;
      }
      .course-rail {
        padding-left: 44px;
        padding-right: 44px;
      }
      .rail-arrow {
        width: 38px;
        min-height: 48px;
        top: 58px;
      }
      .course-card {
        min-height: 252px;
      }
      .delivery-help-list {
        grid-template-columns: 1fr;
      }
      .course-help {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
      .month-stack { gap: 0; }
      .month-nav { display: flex; }
      .month:not([data-mobile-visible="true"]) { display: none; }
      .calendar-grid { gap: 6px; }
      .weekday,
      .calendar-pad,
      .day-button {
        min-height: 42px;
      }
      .button-list {
        display: block;
      }
      .start-grid button {
        min-height: 42px;
        flex: 1 0 72px;
      }
      .register-link {
        width: 100%;
      }
    }
    """


def render_html(payload: dict[str, Any]) -> str:
    page_config = payload.get("pageConfig", {})
    course_descriptions = load_course_descriptions()
    configured_options = {
        str(option.get("course_id")): option
        for option in page_config.get("course_options", [])
        if isinstance(option, dict) and option.get("course_id")
    }
    page_family = str(page_config.get("family") or "BLS")
    course_options_by_id: dict[str, dict[str, Any]] = {
        course_id: {
            "courseId": course_id,
            "courseName": option.get("display_label") or course_id,
            "family": page_family,
            "variant": option.get("variant") or "",
            "deliveryMode": option.get("delivery_mode") or "",
            "recommended": option.get("recommended", True) is not False,
            "deepLinkAliases": [
                str(alias)
                for alias in ([option.get("variant")] + list(option.get("deep_link_aliases", [])))
                if alias
            ],
            "iconLabel": option.get("icon_label") or page_family,
            "imageUrl": option.get("image_url") or DEFAULT_COURSE_IMAGES.get(page_family, "/images/logo.png"),
            "imageFit": option.get("image_fit") or "contain",
            "imageAlt": option.get("image_alt") or f"{option.get('display_label') or page_family} course option",
            "deliveryBadge": option.get("delivery_badge") or delivery_label_for_config(option.get("delivery_mode")),
            "clarification": option.get("clarification") or "",
            "details": course_descriptions.get(course_id, {}),
        }
        for course_id, option in configured_options.items()
    }
    option_groups: dict[str, dict[str, Any]] = {}
    configured_compare_groups = page_config.get("compare_mode", {}).get("groups", {})
    if isinstance(configured_compare_groups, dict):
        for group_key, group_config in configured_compare_groups.items():
            if not isinstance(group_config, dict):
                continue
            option_groups[group_key] = {
                "family": group_key,
                "label": group_config.get("label") or f"All {group_key} options",
                "courseIds": [str(item) for item in group_config.get("course_ids", [])],
            }
    page_dates = []
    for day in payload["dates"]:
        start_times = []
        for slot in day["startTimes"]:
            courses = []
            for course in slot["courses"]:
                family = course.get("courseFamily") or "BLS"
                course_record = {
                    "courseId": course["courseId"],
                    "courseName": course["courseName"],
                    "family": family,
                    "deliveryMode": configured_options.get(course["courseId"], {}).get("delivery_mode") or course.get("deliveryMode") or "",
                    "displayStartTime": course["displayStartTime"],
                    "durationMinutes": course["durationMinutes"],
                    "setupBufferMinutes": course.get("setupBufferMinutes"),
                    "cleanupBufferMinutes": course.get("cleanupBufferMinutes"),
                    "schedulerConsumptionMinutes": course.get("schedulerConsumptionMinutes"),
                    "schedulerConsumptionEnd": course.get("schedulerConsumptionEnd"),
                    "appointmentDayId": course["appointmentDayId"],
                    "appointmentUrl": course["appointmentUrl"],
                    "location": course["location"],
                    "availabilityBlockId": course.get("availabilityBlockId"),
                    "sourceAvailabilityBlock": course.get("sourceAvailabilityBlock", {}),
                    "offerType": course.get("offerType") or "dynamic_appointment",
                    "publicSelectable": course.get("publicSelectable") is True,
                }
                courses.append(course_record)
                course_options_by_id.setdefault(course["courseId"], {
                    "courseId": course["courseId"],
                    "courseName": configured_options.get(course["courseId"], {}).get("display_label") or course["courseName"],
                    "family": family,
                    "variant": configured_options.get(course["courseId"], {}).get("variant") or "",
                    "deliveryMode": configured_options.get(course["courseId"], {}).get("delivery_mode") or course.get("deliveryMode") or "",
                    "recommended": configured_options.get(course["courseId"], {}).get("recommended", True) is not False,
                    "deepLinkAliases": [
                        str(alias)
                        for alias in (
                            [configured_options.get(course["courseId"], {}).get("variant")]
                            + list(configured_options.get(course["courseId"], {}).get("deep_link_aliases", []))
                        )
                        if alias
                    ],
                    "iconLabel": configured_options.get(course["courseId"], {}).get("icon_label") or family,
                    "imageUrl": configured_options.get(course["courseId"], {}).get("image_url") or DEFAULT_COURSE_IMAGES.get(family, "/images/logo.png"),
                    "imageFit": configured_options.get(course["courseId"], {}).get("image_fit") or "contain",
                    "imageAlt": configured_options.get(course["courseId"], {}).get("image_alt") or f"{configured_options.get(course['courseId'], {}).get('display_label') or course['courseName']} course option",
                    "deliveryBadge": configured_options.get(course["courseId"], {}).get("delivery_badge") or delivery_label_for_config(configured_options.get(course["courseId"], {}).get("delivery_mode") or course.get("deliveryMode")),
                    "clarification": configured_options.get(course["courseId"], {}).get("clarification") or "",
                    "details": course_descriptions.get(course["courseId"], {}),
                })
                compare_groups = page_config.get("compare_mode", {}).get("groups", {})
                if isinstance(compare_groups, dict):
                    for group_key, group_config in compare_groups.items():
                        group_ids = [str(item) for item in group_config.get("course_ids", [])] if isinstance(group_config, dict) else []
                        if course["courseId"] in group_ids:
                            group = option_groups.setdefault(group_key, {
                                "family": group_key,
                                "label": group_config.get("label") or f"All {group_key} options",
                                "courseIds": group_ids,
                            })
                            break
                    else:
                        group = option_groups.setdefault(family, {
                            "family": family,
                            "label": f"All {family} options",
                            "courseIds": [],
                        })
                        if course["courseId"] not in group["courseIds"]:
                            group["courseIds"].append(course["courseId"])
            start_times.append({
                "startTime": slot["startTime"],
                "displayStartTime": slot["displayStartTime"],
                "courses": courses,
            })
        page_dates.append({
            "date": day["date"],
            "displayDate": day["displayDate"],
            "startTimes": start_times,
        })
    page_key = str(payload.get("pageKey") or page_config.get("page_key") or "selector")
    availability_version = str(payload.get("generatedAt") or datetime.now().astimezone().isoformat())
    availability_url = (
        "/"
        + str(selector_availability_path(page_key).relative_to(ROOT / "docs")).replace("\\", "/")
        + "?v="
        + quote(availability_version, safe="")
    )
    data_json = json.dumps([], ensure_ascii=False)
    configured_course_ids = [str(option.get("course_id")) for option in page_config.get("course_options", []) if isinstance(option, dict)]
    course_options = [
        course_options_by_id[course_id]
        for course_id in configured_course_ids
        if course_id in course_options_by_id
    ]
    course_options_json = json.dumps(course_options, ensure_ascii=False)
    option_groups_json = json.dumps(option_groups, ensure_ascii=False)
    availability_url_json = json.dumps(availability_url)
    unsupported_options = [
        option
        for option in page_config.get("unsupported_options", [])
        if isinstance(option, dict) and option.get("fragment") and option.get("display_label")
    ]
    unsupported_options_json = json.dumps(unsupported_options, ensure_ascii=False)
    counts = payload["counts"]
    configured_default_course = str(page_config.get("default_course_id") or "").strip()
    available_course_ids = {str(option.get("courseId") or "") for option in course_options}
    first_course = (
        configured_default_course
        if configured_default_course in available_course_ids
        else (course_options[0]["courseId"] if course_options else "")
    )
    title = html.escape(str(page_config.get("title") or "Block Schedule"))
    subtitle = html.escape(str(page_config.get("subtitle") or ""))
    intro = html.escape(str(page_config.get("intro") or "Select a course, date, and start time."))
    explanation = html.escape(str(page_config.get("explanation") or ""))
    documentation_note = page_config.get("documentation_note", {})
    student_note = html.escape(str(page_config.get("student_note") or ""))
    context_html = ""
    if explanation or isinstance(documentation_note, dict) or student_note:
        note_html = ""
        if isinstance(documentation_note, dict) and (documentation_note.get("title") or documentation_note.get("body") or documentation_note.get("bullets")):
            note_title = html.escape(str(documentation_note.get("title") or "Documentation note"))
            note_body = html.escape(str(documentation_note.get("body") or ""))
            bullet_items = [
                f"<li>{html.escape(str(item))}</li>"
                for item in documentation_note.get("bullets", [])
                if str(item).strip()
            ]
            bullet_html = f"<ul>{''.join(bullet_items)}</ul>" if bullet_items else ""
            note_html = f"""
      <div class="page-note">
        <h2>{note_title}</h2>
        <p>{note_body}</p>
        {bullet_html}
      </div>"""
        student_html = f'<p class="muted">{student_note}</p>' if student_note else ""
        explanation_html = f"<p>{explanation}</p>" if explanation else ""
        context_html = f"""
    <section class="page-context" aria-label="Course context">
      {explanation_html}
      {note_html}
      {student_html}
    </section>"""
    back_href = html.escape(str(page_config.get("back_link_href") or "/index.html#courses"), quote=True)
    back_label = html.escape(str(page_config.get("back_link_label") or "Back to All Courses"))
    header_credential = page_config.get("header_credential")
    header_credential_html = ""
    if isinstance(header_credential, dict) and header_credential.get("image_url") and header_credential.get("title"):
        credential_image = html.escape(str(header_credential["image_url"]), quote=True)
        credential_alt = html.escape(str(header_credential.get("image_alt") or header_credential["title"]), quote=True)
        credential_eyebrow = html.escape(str(header_credential.get("eyebrow") or "Credential"))
        credential_title = html.escape(str(header_credential["title"]))
        credential_body = html.escape(str(header_credential.get("body") or ""))
        header_credential_html = f"""
      <aside class="header-credential" aria-label="{credential_title}">
        <img src="{credential_image}" alt="{credential_alt}" loading="eager">
        <div>
          <span class="header-credential-eyebrow">{credential_eyebrow}</span>
          <strong>{credential_title}</strong>
          {f'<p>{credential_body}</p>' if credential_body else ''}
        </div>
      </aside>"""
    delivery_help_items = page_config.get("delivery_help")
    if not isinstance(delivery_help_items, list) or not delivery_help_items:
        seen_delivery_modes = []
        for option in page_config.get("course_options", []):
            mode = str(option.get("delivery_mode") or "")
            if mode and mode not in seen_delivery_modes and mode in DELIVERY_HELP:
                seen_delivery_modes.append(mode)
        delivery_help_items = [
            {
                "label": DELIVERY_HELP[mode]["label"],
                "text": DELIVERY_HELP[mode]["help"],
            }
            for mode in seen_delivery_modes
        ]
    delivery_help_html = ""
    if delivery_help_items:
        items = []
        for item in delivery_help_items:
            if not isinstance(item, dict):
                continue
            label = html.escape(str(item.get("label") or "Course option"))
            text = html.escape(str(item.get("text") or ""))
            if label and text:
                items.append(f"""
          <div class="delivery-help-item">
            <div class="delivery-help-label">{label}</div>
            <div class="delivery-help-copy">{text}</div>
          </div>""")
        if items:
            delivery_help_title = html.escape(str(page_config.get("delivery_help_title") or "Course format guide"))
            delivery_help_html = f"""
    <div class="family-help" aria-label="{delivery_help_title}">
      <div class="family-help-title">{delivery_help_title}</div>
      <div class="delivery-help-list">{''.join(items)}
      </div>
    </div>"""
    compare_label = html.escape(str(page_config.get("compare_mode", {}).get("label") or "Show all options"))
    compare_enabled = page_config.get("compare_mode", {}).get("enabled") is True
    show_all_label = html.escape(str(page_config.get("show_all_label") or "Show all course options"))
    show_all_enabled = page_config.get("show_all_enabled", True) is not False
    show_all_toggle_html = ""
    if show_all_enabled:
        show_all_toggle_html = f"""
          <label class="disclosure-toggle">
            <input id="show-all-toggle" type="checkbox">
            <span>{show_all_label}</span>
          </label>"""
    compare_toggle_html = ""
    if compare_enabled:
        compare_toggle_html = f"""
          <label class="compare-toggle">
            <input id="compare-toggle" type="checkbox">
            <span>{compare_label}</span>
          </label>"""
    unsupported_html = ""
    if unsupported_options:
        cards = []
        for option in unsupported_options:
            fragment = html.escape(str(option.get("fragment") or ""), quote=True)
            label = html.escape(str(option.get("display_label") or "Request option"))
            clarification = html.escape(str(option.get("clarification") or "Contact 910CPR for scheduling."))
            action_label = html.escape(str(option.get("action_label") or "Request scheduling"))
            action_href = html.escape(str(option.get("action_href") or "/request_group_session.html"), quote=True)
            aliases = html.escape(" ".join(str(alias) for alias in option.get("deep_link_aliases", []) if alias), quote=True)
            cards.append(f"""
        <article id="{fragment}" class="request-option-card" tabindex="-1" data-request-fragment="{fragment}" data-request-aliases="{aliases}">
          <h3>{label}</h3>
          <p>{clarification}</p>
          <a class="request-option-link" href="{action_href}">{action_label}</a>
        </article>""")
        unsupported_html = f"""
    <section class="request-options" aria-label="Request additional options">
      <h2>Other options</h2>
      <p class="muted">These options are not currently connected to validated public instant booking. Use the request action so an instructor can confirm the right path.</p>
      <div class="request-option-grid">{''.join(cards)}
      </div>
    </section>"""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | 910CPR</title>
  <style>{css()}</style>
</head>
<body>
  <header>
    <a class="back-link" href="{back_href}">← {back_label}</a>
    <div class="page-heading-row">
      <div>
        <h1>{title}</h1>
        {f'<p class="page-subtitle">{subtitle}</p>' if subtitle else ''}
        <p class="muted">{intro}</p>
      </div>
      {header_credential_html}
    </div>
    {delivery_help_html}
  </header>
  <main>
    {context_html}
    {unsupported_html}
    <section class="selector-shell" aria-label="Block-based schedule selector">
      <div class="panel course-selector-panel">
        <div class="course-selector-top">
          <div>
            <h2>Course</h2>
            <p class="muted">Choose the course or delivery format first.</p>
          </div>
          <div class="option-tools">
            {show_all_toggle_html}
            {compare_toggle_html}
          </div>
        </div>
        <div class="course-rail" data-course-rail>
          <button type="button" class="rail-arrow previous" data-course-rail-prev aria-label="Previous course options">‹</button>
          <div id="course-option-list" class="choice-list" tabindex="0" aria-label="Course options"></div>
          <button type="button" class="rail-arrow next" data-course-rail-next aria-label="More course options">›</button>
        </div>
      </div>
      <div class="selector-grid">
        <div class="panel">
          <h2>Calendar</h2>
          <div id="date-list" class="month-stack"></div>
        </div>
        <div class="panel">
          <h2>Start Times</h2>
          <div id="start-list" class="button-list"></div>
        </div>
        <div class="panel">
          <h2>Register</h2>
          <p class="register-note">Times shown are start times. Please allow enough time for the course you selected.</p>
          <div id="course-list" class="course-list"></div>
        </div>
      </div>
    </section>
  </main>
  <script>
    const embeddedScheduleDates = {data_json};
    const availabilityUrl = {availability_url_json};
    const courseOptions = {course_options_json};
    const optionGroups = {option_groups_json};
    const unsupportedOptions = {unsupported_options_json};
    let scheduleDates = embeddedScheduleDates;
    let availabilityState = 'checking';
    let availabilityMessage = 'Checking current class times…';
    let resolvedAvailability = null;
    let selectedCourseId = {json.dumps(first_course)};
    let showAllOptions = false;
    let compareMode = false;
    let selectedDate = '';
    let selectedStart = '';
    let mobileMonthIndex = 0;

    function byId(id) {{
      return document.getElementById(id);
    }}

    function setAvailabilityMessage(message) {{
      availabilityMessage = message || 'Checking current class times…';
    }}

    function renderAvailabilityPlaceholder(message = availabilityMessage) {{
      ['date-list', 'start-list', 'course-list'].forEach(id => {{
        const host = byId(id);
        if (host) {{
          host.innerHTML = '';
          const box = document.createElement('div');
          box.className = 'empty';
          box.setAttribute('role', id === 'start-list' ? 'status' : 'note');
          box.textContent = message;
          host.appendChild(box);
        }}
      }});
    }}

    function availabilityReady() {{
      return availabilityState === 'ready';
    }}

    function isMobileLayout() {{
      return window.matchMedia('(max-width: 820px)').matches;
    }}

    function normalizeDeepLink(value) {{
      return String(value || '').trim().toLowerCase().replace(/^#/, '');
    }}

    function publicDeliveryBucket(value) {{
      const normalized = normalizeDeepLink(value).replace(/[\\s_]+/g, '-').replace(/\\+/g, '-');
      if (!normalized) {{
        return '';
      }}
      if (normalized === 'in-person' || normalized === 'inperson' || normalized === 'classroom') {{
        return 'in-person';
      }}
      if ([
        'blended',
        'heartcode',
        'skills-session',
        'skills',
        'online-skills',
        'online-learning-skills',
        'online-in-person-skills',
        'online-plus-skills',
        'online-and-skills',
        'online-hands-on-skills',
        'online-learning-in-person-skills'
      ].includes(normalized) || (normalized.includes('online') && normalized.includes('skills'))) {{
        return 'online-skills';
      }}
      return normalized;
    }}

    function courseIdFromDeepLink() {{
      const params = new URLSearchParams(window.location.search);
      const requested = normalizeDeepLink(params.get('course')) || normalizeDeepLink(window.location.hash);
      if (!requested) {{
        return '';
      }}
      const matched = courseOptions.find(course =>
        course.courseId === requested ||
        normalizeDeepLink(course.variant) === requested ||
        (course.deepLinkAliases || []).some(alias => normalizeDeepLink(alias) === requested)
      );
      return matched?.courseId || '';
    }}

    function requestOptionFromDeepLink() {{
      const params = new URLSearchParams(window.location.search);
      const requested = normalizeDeepLink(params.get('course')) || normalizeDeepLink(window.location.hash);
      if (!requested) {{
        return null;
      }}
      return unsupportedOptions.find(option =>
        normalizeDeepLink(option.fragment) === requested ||
        (option.deep_link_aliases || []).some(alias => normalizeDeepLink(alias) === requested)
      ) || null;
    }}

    function focusDeepLinkedElement() {{
      const params = new URLSearchParams(window.location.search);
      const requested = normalizeDeepLink(params.get('course')) || normalizeDeepLink(window.location.hash);
      if (!requested) {{
        return;
      }}
      const requestOption = requestOptionFromDeepLink();
      const courseOption = courseOptions.find(course =>
        course.courseId === selectedCourseId &&
        (normalizeDeepLink(course.variant) === requested || (course.deepLinkAliases || []).some(alias => normalizeDeepLink(alias) === requested))
      );
      const target = requestOption
        ? document.querySelector(`[data-request-fragment="${{CSS.escape(requestOption.fragment)}}"]`)
        : courseOption
          ? document.querySelector(`[data-course-id="${{CSS.escape(courseOption.courseId)}}"]`)
          : null;
      if (target) {{
        target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        target.focus({{ preventScroll: true }});
      }}
    }}

    function showAllFromDeepLink() {{
      const params = new URLSearchParams(window.location.search);
      return ['1', 'true', 'yes'].includes(normalizeDeepLink(params.get('showAll')));
    }}

    function deliveryLabel(value) {{
      const bucket = publicDeliveryBucket(value);
      if (bucket === 'in-person') {{
        return 'IN-PERSON';
      }}
      if (bucket === 'online-skills') {{
        return 'ONLINE + SKILLS';
      }}
      if (bucket === 'blended') {{
        return 'BLENDED';
      }}
      return 'All';
    }}

    function updateCourseRailControls() {{
      const rail = document.querySelector('[data-course-rail]');
      const list = byId('course-option-list');
      const previous = document.querySelector('[data-course-rail-prev]');
      const next = document.querySelector('[data-course-rail-next]');
      if (!rail || !list || !previous || !next) {{
        return;
      }}
      const tolerance = 4;
      const maxScroll = Math.max(0, list.scrollWidth - list.clientWidth);
      const endTolerance = Math.max(tolerance, Math.min(24, list.clientWidth * 0.06));
      const hasOverflow = maxScroll > tolerance;
      const atStart = list.scrollLeft <= tolerance;
      const atEnd = list.scrollLeft >= maxScroll - endTolerance;
      rail.classList.toggle('has-overflow', hasOverflow);
      previous.disabled = !hasOverflow || atStart;
      next.disabled = !hasOverflow || atEnd;
      previous.setAttribute('aria-disabled', String(previous.disabled));
      next.setAttribute('aria-disabled', String(next.disabled));
    }}

    function scheduleCourseRailUpdate() {{
      updateCourseRailControls();
      window.requestAnimationFrame(updateCourseRailControls);
    }}

    function scrollCourseRail(direction) {{
      const list = byId('course-option-list');
      if (!list) {{
        return;
      }}
      const firstCard = list.querySelector('.course-card');
      const cardWidth = firstCard ? firstCard.getBoundingClientRect().width : Math.max(240, list.clientWidth * 0.75);
      const gap = 12;
      const maxScroll = Math.max(0, list.scrollWidth - list.clientWidth);
      const target = Math.max(0, Math.min(maxScroll, list.scrollLeft + (direction * (cardWidth + gap))));
      list.scrollTo({{ left: target, behavior: 'smooth' }});
      window.setTimeout(updateCourseRailControls, 260);
    }}

    function selectedDateLabel() {{
      const day = filteredDates().find(item => item.date === selectedDate);
      return day?.displayDate || '';
    }}

    function selectedCourseLabel() {{
      const course = courseOptions.find(item => item.courseId === selectedCourseId);
      return course?.courseName || '';
    }}

    function visibleCourseOptions() {{
      return courseOptions.filter(course => showAllOptions || course.recommended !== false);
    }}

    function syncCourseSelection() {{
      const visibleOptions = visibleCourseOptions();
      if (!visibleOptions.length) {{
        selectedCourseId = '';
        return;
      }}
      if (!visibleOptions.some(course => course.courseId === selectedCourseId)) {{
        selectedCourseId = visibleOptions[0].courseId;
      }}
    }}

    function activeCourseIds() {{
      syncCourseSelection();
      const selected = courseOptions.find(course => course.courseId === selectedCourseId);
      if (!selected) {{
        return new Set();
      }}
      if (compareMode) {{
        const group = Object.values(optionGroups).find(item => item.courseIds?.includes(selectedCourseId));
        const groupIds = group?.courseIds || optionGroups[selected.family]?.courseIds || [selectedCourseId];
        return new Set(groupIds.filter(courseId => {{
          const course = courseOptions.find(option => option.courseId === courseId);
          return Boolean(course);
        }}));
      }}
      return new Set([selectedCourseId]);
    }}

    function filteredCourses(slot) {{
      const ids = activeCourseIds();
      return slot.courses.filter(course => ids.has(course.courseId));
    }}

    const scheduleTimezone = 'America/New_York';

    function businessNow() {{
      const parts = new Intl.DateTimeFormat('en-CA', {{
        timeZone: scheduleTimezone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      }}).formatToParts(new Date()).reduce((values, part) => {{
        values[part.type] = part.value;
        return values;
      }}, {{}});
      const hour = Number(parts.hour === '24' ? '0' : parts.hour);
      return {{
        dateKey: `${{parts.year}}-${{parts.month}}-${{parts.day}}`,
        minutes: (hour * 60) + Number(parts.minute)
      }};
    }}

    function startMinutes(startTime) {{
      const [hour, minute] = String(startTime || '').split(':').map(Number);
      return (hour * 60) + minute;
    }}

    function isPastStart(day, slot, now = businessNow()) {{
      if (!day || !slot) {{
        return true;
      }}
      if (day.date < now.dateKey) {{
        return true;
      }}
      if (day.date > now.dateKey) {{
        return false;
      }}
      return startMinutes(slot.startTime) <= now.minutes;
    }}

    function selectableStartTimes(day, now = businessNow()) {{
      return (day?.startTimes || []).filter(slot => !isPastStart(day, slot, now));
    }}

    function isSelectableDate(day, now = businessNow()) {{
      return Boolean(day && day.date >= now.dateKey && selectableStartTimes(day, now).length);
    }}

    function filteredDates() {{
      if (!availabilityReady()) {{
        return [];
      }}
      return scheduleDates.map(day => {{
        const startTimes = day.startTimes.map(slot => ({{
          ...slot,
          courses: filteredCourses(slot)
        }})).filter(slot => slot.courses.length);
        return {{ ...day, startTimes }};
      }}).filter(day => day.startTimes.length);
    }}

    function syncSelection() {{
      const days = filteredDates();
      const now = businessNow();
      const selectableDays = days.filter(day => isSelectableDate(day, now));
      if (!days.length) {{
        selectedDate = '';
        selectedStart = '';
        return days;
      }}
      if (!selectableDays.length) {{
        selectedDate = '';
        selectedStart = '';
        return days;
      }}
      if (!selectableDays.some(day => day.date === selectedDate)) {{
        selectedDate = selectableDays[0].date;
        mobileMonthIndex = Math.max(0, [...new Set(days.map(day => day.date.slice(0, 7)))].indexOf(selectedDate.slice(0, 7)));
      }}
      const day = days.find(item => item.date === selectedDate);
      const starts = selectableStartTimes(day, now);
      if (!starts.some(slot => slot.startTime === selectedStart)) {{
        selectedStart = starts[0]?.startTime || '';
      }}
      return days;
    }}

    function renderCourseOptions() {{
      const host = byId('course-option-list');
      host.innerHTML = '';
      visibleCourseOptions().forEach(course => {{
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'course-card';
        button.dataset.courseId = course.courseId;
        button.setAttribute('aria-pressed', String(course.courseId === selectedCourseId));
        const icon = document.createElement('span');
        icon.className = 'course-icon';
        if (course.imageUrl) {{
          const image = document.createElement('img');
          image.src = course.imageUrl;
          image.alt = course.imageAlt || course.courseName;
          image.loading = 'lazy';
          if (course.imageFit === 'cover') image.className = 'course-image-cover';
          icon.appendChild(image);
        }} else {{
          const fallback = document.createElement('span');
          fallback.className = 'course-icon-fallback';
          fallback.textContent = course.iconLabel || course.family;
          fallback.setAttribute('aria-hidden', 'true');
          icon.appendChild(fallback);
        }}
        const copy = document.createElement('span');
        copy.className = 'course-copy';
        const title = document.createElement('span');
        title.className = 'course-title';
        title.textContent = course.courseName;
        const delivery = document.createElement('span');
        delivery.className = 'course-delivery';
        delivery.textContent = course.deliveryBadge || deliveryLabel(course.deliveryMode);
        const help = document.createElement('span');
        help.className = 'course-help';
        help.textContent = course.clarification || '';
        copy.append(title, delivery, help);
        button.append(icon, copy);
        const details = course.details || {{}};
        if (details.short_description || details.who_this_is_for || (details.topics_covered || []).length) {{
          const detailBox = document.createElement('details');
          detailBox.className = 'course-details';
          const summary = document.createElement('summary');
          summary.textContent = 'Course details';
          const body = document.createElement('div');
          body.className = 'course-details-body';
          if (details.short_description) {{
            const short = document.createElement('div');
            short.textContent = details.short_description;
            body.appendChild(short);
          }}
          if (details.who_this_is_for) {{
            const audience = document.createElement('div');
            audience.textContent = details.who_this_is_for;
            body.appendChild(audience);
          }}
          if ((details.topics_covered || []).length) {{
            const topics = document.createElement('ul');
            details.topics_covered.slice(0, 5).forEach(topic => {{
              const item = document.createElement('li');
              item.textContent = topic;
              topics.appendChild(item);
            }});
            body.appendChild(topics);
          }}
          if (details.certification_issued) {{
            const cert = document.createElement('div');
            cert.textContent = details.certification_issued;
            body.appendChild(cert);
          }}
          detailBox.append(summary, body);
          button.appendChild(detailBox);
        }}
        button.addEventListener('click', () => {{
          selectedCourseId = course.courseId;
          renderAll();
        }});
        host.appendChild(button);
      }});
      if (!host.children.length) {{
        host.innerHTML = '<div class="empty">No matching times are currently available.</div>';
      }}
      scheduleCourseRailUpdate();
      const showAllToggle = byId('show-all-toggle');
      if (showAllToggle) {{
        showAllToggle.checked = showAllOptions;
      }}
      const compareToggle = byId('compare-toggle');
      if (compareToggle) {{
        compareToggle.checked = compareMode;
      }}
    }}

    function renderDates() {{
      const host = byId('date-list');
      host.innerHTML = '';
      if (!availabilityReady()) {{
        renderAvailabilityPlaceholder();
        return;
      }}
      const days = syncSelection();
      const now = businessNow();
      if (!days.length) {{
        host.innerHTML = '<div class="empty">No matching times are currently available.</div>';
        return;
      }}
      const availableByDate = new Map(days.map(day => [day.date, day]));
      const monthKeys = [];
      days.forEach(day => {{
        const monthKey = day.date.slice(0, 7);
        if (!monthKeys.includes(monthKey)) {{
          monthKeys.push(monthKey);
        }}
      }});
      if (mobileMonthIndex >= monthKeys.length) {{
        mobileMonthIndex = Math.max(0, monthKeys.length - 1);
      }}
      const activeMonthKey = isMobileLayout() ? monthKeys[mobileMonthIndex] : (selectedDate ? selectedDate.slice(0, 7) : monthKeys[mobileMonthIndex]);
      const activeMonthIndex = monthKeys.includes(activeMonthKey) ? monthKeys.indexOf(activeMonthKey) : mobileMonthIndex;
      if (isMobileLayout()) {{
        mobileMonthIndex = activeMonthIndex;
        const nav = document.createElement('div');
        nav.className = 'month-nav';
        const previous = document.createElement('button');
        previous.type = 'button';
        previous.textContent = 'Previous';
        previous.disabled = mobileMonthIndex <= 0;
        previous.addEventListener('click', () => {{
          mobileMonthIndex = Math.max(0, mobileMonthIndex - 1);
          renderDates();
        }});
        const navTitle = document.createElement('div');
        navTitle.className = 'month-nav-title';
        const [activeYear, activeMonth] = monthKeys[mobileMonthIndex].split('-').map(Number);
        navTitle.textContent = new Date(activeYear, activeMonth - 1, 1).toLocaleDateString(undefined, {{ month: 'long', year: 'numeric' }});
        const next = document.createElement('button');
        next.type = 'button';
        next.textContent = 'Next';
        next.disabled = mobileMonthIndex >= monthKeys.length - 1;
        next.addEventListener('click', () => {{
          mobileMonthIndex = Math.min(monthKeys.length - 1, mobileMonthIndex + 1);
          renderDates();
        }});
        nav.append(previous, navTitle, next);
        host.appendChild(nav);
      }}
      const renderedMonthKeys = isMobileLayout() ? [monthKeys[mobileMonthIndex]] : monthKeys.slice(0, 3);
      renderedMonthKeys.forEach(monthKey => {{
        const [year, month] = monthKey.split('-').map(Number);
        const first = new Date(year, month - 1, 1);
        const last = new Date(year, month, 0);
        const section = document.createElement('section');
        section.className = 'month';
        section.dataset.mobileVisible = String(monthKey === monthKeys[mobileMonthIndex]);
        const title = document.createElement('h3');
        title.className = 'month-title';
        title.textContent = first.toLocaleDateString(undefined, {{ month: 'long', year: 'numeric' }});
        const grid = document.createElement('div');
        grid.className = 'calendar-grid';
        ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].forEach(label => {{
          const item = document.createElement('div');
          item.className = 'weekday';
          item.textContent = label;
          grid.appendChild(item);
        }});
        for (let i = 0; i < first.getDay(); i += 1) {{
          const pad = document.createElement('div');
          pad.className = 'calendar-pad';
          grid.appendChild(pad);
        }}
        for (let dayNum = 1; dayNum <= last.getDate(); dayNum += 1) {{
          const dateKey = `${{monthKey}}-${{String(dayNum).padStart(2, '0')}}`;
          const available = availableByDate.get(dateKey);
          if (available) {{
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'day-button';
            button.textContent = String(dayNum);
            const disabled = !isSelectableDate(available, now);
            if (disabled) {{
              button.classList.add('is-past');
            }}
            button.disabled = disabled;
            button.setAttribute('aria-disabled', String(disabled));
            button.setAttribute('aria-label', available.displayDate + ' ' + (disabled ? 'not bookable; past date or no future ' + scheduleTimezone + ' start times' : 'available'));
            button.setAttribute('aria-pressed', String(available.date === selectedDate));
            button.addEventListener('click', () => {{
              if (!isSelectableDate(available)) {{
                return;
              }}
              selectedDate = available.date;
              mobileMonthIndex = monthKeys.indexOf(available.date.slice(0, 7));
              selectedStart = selectableStartTimes(available)[0]?.startTime || '';
              renderAll();
            }});
            grid.appendChild(button);
          }} else {{
            const pad = document.createElement('div');
            pad.className = 'calendar-pad';
            pad.textContent = String(dayNum);
            grid.appendChild(pad);
          }}
        }}
        section.append(title, grid);
        host.appendChild(section);
      }});
    }}

    function renderStarts() {{
      const host = byId('start-list');
      host.innerHTML = '';
      if (!availabilityReady()) {{
        renderAvailabilityPlaceholder();
        return;
      }}
      const day = filteredDates().find(item => item.date === selectedDate);
      if (!day || !day.startTimes.length) {{
        host.innerHTML = '<div class="empty">No matching times are currently available.</div>';
        return;
      }}
      const groups = new Map();
      day.startTimes.forEach(slot => {{
        const [hourText] = slot.startTime.split(':');
        const hour = Number.parseInt(hourText, 10);
        const label = hour < 12 ? 'AM' : 'PM';
        if (!groups.has(label)) {{
          groups.set(label, []);
        }}
        groups.get(label).push(slot);
      }});
      groups.forEach((slots, label) => {{
        const group = document.createElement('div');
        group.className = 'start-group';
        const groupLabel = document.createElement('div');
        groupLabel.className = 'start-group-label';
        groupLabel.textContent = label;
        const grid = document.createElement('div');
        grid.className = 'start-grid';
        slots.forEach(slot => {{
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = slot.displayStartTime;
        const disabled = isPastStart(day, slot);
        if (disabled) {{
          button.classList.add('is-past');
        }}
        button.disabled = disabled;
        button.setAttribute('aria-disabled', String(disabled));
        button.setAttribute('aria-label', slot.displayStartTime + ' ' + (disabled ? 'not bookable; past ' + scheduleTimezone + ' start time' : 'available'));
        button.setAttribute('aria-pressed', String(slot.startTime === selectedStart));
        button.addEventListener('click', () => {{
          if (isPastStart(day, slot)) {{
            return;
          }}
          selectedStart = slot.startTime;
          renderAll();
        }});
          grid.appendChild(button);
        }});
        group.append(groupLabel, grid);
        host.appendChild(group);
      }});
    }}

    function renderCourses() {{
      const host = byId('course-list');
      host.innerHTML = '';
      if (!availabilityReady()) {{
        renderAvailabilityPlaceholder();
        return;
      }}
      const day = filteredDates().find(item => item.date === selectedDate);
      const slot = day?.startTimes.find(item => item.startTime === selectedStart);
      if (!slot || isPastStart(day, slot) || !slot.courses.length) {{
        host.innerHTML = '<div class="empty">No matching times are currently available.</div>';
        return;
      }}
      slot.courses.forEach(course => {{
        const item = document.createElement('article');
        item.className = 'course';
        const summary = document.createElement('div');
        summary.className = 'selected-summary';
        const title = document.createElement('h3');
        title.textContent = course.courseName;
        const dateRow = document.createElement('div');
        dateRow.className = 'selected-summary-row';
        dateRow.textContent = selectedDateLabel();
        const timeRow = document.createElement('div');
        timeRow.className = 'selected-summary-row';
        timeRow.textContent = course.displayStartTime;
        const locationRow = document.createElement('div');
        locationRow.className = 'selected-summary-row';
        locationRow.textContent = course.location;
        summary.append(title, dateRow, timeRow, locationRow);
        const badge = document.createElement('div');
        badge.className = 'delivery-badge';
        badge.textContent = deliveryLabel(course.deliveryMode);
        const link = document.createElement('a');
        link.className = 'register-link';
        link.href = course.appointmentUrl;
        link.textContent = 'Register';
        item.append(summary, badge, link);
        host.appendChild(item);
      }});
    }}

    function renderAll() {{
      syncCourseSelection();
      if (!availabilityReady()) {{
        renderCourseOptions();
        renderAvailabilityPlaceholder();
        return;
      }}
      syncSelection();
      renderCourseOptions();
      renderDates();
      renderStarts();
      renderCourses();
    }}

    const compareToggle = byId('compare-toggle');
    if (compareToggle) {{
      compareToggle.addEventListener('change', event => {{
        compareMode = event.target.checked;
        renderAll();
      }});
    }}

    const showAllToggle = byId('show-all-toggle');
    if (showAllToggle) {{
      showAllToggle.addEventListener('change', event => {{
        showAllOptions = event.target.checked;
        renderAll();
      }});
    }}

    const courseRailList = byId('course-option-list');
    const courseRailPrevious = document.querySelector('[data-course-rail-prev]');
    const courseRailNext = document.querySelector('[data-course-rail-next]');
    if (courseRailList) {{
      courseRailList.addEventListener('scroll', updateCourseRailControls, {{ passive: true }});
    }}
    if (courseRailPrevious) {{
      courseRailPrevious.addEventListener('click', () => scrollCourseRail(-1));
    }}
    if (courseRailNext) {{
      courseRailNext.addEventListener('click', () => scrollCourseRail(1));
    }}

    window.addEventListener('resize', () => {{
      if (availabilityReady()) {{
        renderDates();
        renderStarts();
      }}
      updateCourseRailControls();
    }});

    showAllOptions = showAllFromDeepLink();
    selectedCourseId = courseIdFromDeepLink() || selectedCourseId;
    renderAll();
    setTimeout(focusDeepLinkedElement, 0);

    window.addEventListener('hashchange', () => {{
      const requestedCourse = courseIdFromDeepLink();
      if (requestedCourse) {{
        selectedCourseId = requestedCourse;
      }}
      renderAll();
      setTimeout(focusDeepLinkedElement, 0);
    }});

    async function loadResolvedAvailability() {{
      availabilityState = 'checking';
      setAvailabilityMessage('Checking current class times…');
      renderAll();
      try {{
        const response = await fetch(availabilityUrl, {{ cache: 'no-store' }});
        if (!response.ok) {{
          throw new Error(`availability fetch failed: ${{response.status}}`);
        }}
        const payload = await response.json();
        if (!payload || payload.schemaVersion !== 'selector-resolved-availability.v1' || !Array.isArray(payload.dates)) {{
          throw new Error('availability payload has an unexpected shape');
        }}
        resolvedAvailability = payload;
        scheduleDates = payload.dates;
        availabilityState = 'ready';
        setAvailabilityMessage('');
        renderAll();
      }} catch (error) {{
        console.error(error);
        resolvedAvailability = null;
        scheduleDates = [];
        availabilityState = 'failed';
        setAvailabilityMessage('Current class times are temporarily unavailable. Please retry in a moment or contact 910CPR.');
        renderAll();
      }}
    }}

    loadResolvedAvailability();
  </script>
</body>
</html>
"""


def run() -> dict[str, Any]:
    payload = build_bls_pilot_schedule()
    return write_page_outputs(payload, REPORT_JSON_PATH, REPORT_MD_PATH, HTML_PATH)


def write_page_outputs(payload: dict[str, Any], report_json_path: Path, report_md_path: Path, html_path: Path) -> dict[str, Any]:
    payload = apply_final_live_availability_guard(payload)
    page_config = payload.get("pageConfig", {})
    availability_path = selector_availability_path(str(payload.get("pageKey") or "selector"))
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)
    availability_path.parent.mkdir(parents=True, exist_ok=True)
    report_json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_md_path.write_text(render_report(payload), encoding="utf-8")
    availability_path.write_text(
        json.dumps(public_selector_availability_payload(payload), separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    output_paths = [report_json_path, report_md_path, availability_path]
    if page_config.get("render_html") is not False:
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(render_html(payload), encoding="utf-8")
        output_paths.append(html_path)
    legacy_schedule_path = page_config.get("legacy_schedule_path")
    if legacy_schedule_path and page_config.get("render_html") is not False:
        legacy_path = ROOT / str(legacy_schedule_path)
        legacy_path.parent.mkdir(parents=True, exist_ok=True)
        legacy_path.write_text(render_redirect_html(legacy_path, html_path, str(page_config.get("title") or "Schedule")), encoding="utf-8")
        output_paths.append(legacy_path)
    return {
        "counts": payload["counts"],
        "availability_source_used": payload["availability_source_used"],
        "availability_fallback_used": payload["availability_fallback_used"],
        "horizon_days": payload["horizonDays"],
        "top_rejection_reasons": dict(Counter(payload.get("rejectionReasonCounts", {})).most_common(10)),
        "output_paths": output_paths,
    }


def render_redirect_html(source_path: Path, target_path: Path, title: str) -> str:
    relative_target = "/" + target_path.relative_to(ROOT / "docs").as_posix()
    escaped_title = html.escape(title)
    escaped_target = html.escape(relative_target, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <meta http-equiv="refresh" content="0; url={escaped_target}">
  <title>{escaped_title} moved | 910CPR</title>
  <script>
    (function() {{
      var target = {json.dumps(relative_target)};
      var query = window.location.search || "";
      var hash = window.location.hash || "";
      window.location.replace(target + query + hash);
    }}());
  </script>
</head>
<body>
  <p>This schedule moved to <a href="{escaped_target}">{escaped_target}</a>.</p>
</body>
</html>
"""


def run_page(page_key: str) -> dict[str, Any]:
    page_config = load_block_schedule_page_configs()[page_key]
    payload = build_block_schedule_page(page_config)
    report_json_path = ROOT / page_config.get("report_json_path", f"data/audit/{page_key}_block_schedule.json")
    report_md_path = ROOT / page_config.get("report_md_path", f"data/audit/{page_key}_block_schedule_report.md")
    html_path = ROOT / page_config["output_path"]
    return write_page_outputs(payload, report_json_path, report_md_path, html_path)


def main() -> int:
    result = run()
    print("BLS block schedule pilot built.")
    print(f"Availability source used: {result['availability_source_used']}")
    print(f"Availability fallback used: {result['availability_fallback_used']}")
    print(f"Horizon days: {result['horizon_days']}")
    for key, value in result["counts"].items():
        print(f"{key}: {value}")
    print("Output files:")
    for path in result["output_paths"]:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
