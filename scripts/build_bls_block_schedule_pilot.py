from __future__ import annotations

import html
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

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


def load_course_descriptions() -> dict[str, dict[str, Any]]:
    if not COURSE_DESCRIPTIONS_PATH.exists():
        return {}
    payload = json.loads(COURSE_DESCRIPTIONS_PATH.read_text(encoding="utf-8"))
    courses = payload.get("courses", {}) if isinstance(payload, dict) else {}
    return {str(course_id): course for course_id, course in courses.items() if isinstance(course, dict)}


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
      grid-auto-columns: minmax(250px, 1fr);
      gap: 10px;
      overflow-x: auto;
      overscroll-behavior-inline: contain;
      scroll-snap-type: x proximity;
      padding: 0 2px 8px;
      margin-bottom: 0;
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
      grid-template-columns: 36px 1fr;
      gap: 10px;
      width: 100%;
      padding: 12px;
      min-height: 118px;
      align-content: start;
      scroll-snap-align: start;
    }
    .course-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      border-radius: 6px;
      background: #e8f2f8;
      color: var(--accent-dark);
      font-weight: 700;
      font-size: .82rem;
    }
    .course-copy { display: grid; gap: 3px; }
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
      grid-column: 2;
      color: var(--muted);
      font-size: .84rem;
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
        scroll-snap-type: x mandatory;
      }
      .course-card {
        min-height: 112px;
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
                    "appointmentDayId": course["appointmentDayId"],
                    "appointmentUrl": course["appointmentUrl"],
                    "location": course["location"],
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
    data_json = json.dumps(page_dates, ensure_ascii=False)
    configured_course_ids = [str(option.get("course_id")) for option in page_config.get("course_options", []) if isinstance(option, dict)]
    course_options = [
        course_options_by_id[course_id]
        for course_id in configured_course_ids
        if course_id in course_options_by_id
    ]
    course_options_json = json.dumps(course_options, ensure_ascii=False)
    option_groups_json = json.dumps(option_groups, ensure_ascii=False)
    counts = payload["counts"]
    first_course = course_options[0]["courseId"] if course_options else ""
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
    <h1>{title}</h1>
    {f'<p class="page-subtitle">{subtitle}</p>' if subtitle else ''}
    <p class="muted">{intro}</p>
    <p class="muted">Pilot proof: whole availability blocks are not shown as class times. Public-selectable offers: {counts['publicSelectableOfferCount']}.</p>
  </header>
  <main>
    {context_html}
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
        <div id="course-option-list" class="choice-list"></div>
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
    const scheduleDates = {data_json};
    const courseOptions = {course_options_json};
    const optionGroups = {option_groups_json};
    let selectedCourseId = {json.dumps(first_course)};
    let showAllOptions = false;
    let compareMode = false;
    let selectedDate = '';
    let selectedStart = '';
    let mobileMonthIndex = 0;

    function byId(id) {{
      return document.getElementById(id);
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

    function showAllFromDeepLink() {{
      const params = new URLSearchParams(window.location.search);
      return ['1', 'true', 'yes'].includes(normalizeDeepLink(params.get('showAll')));
    }}

    function deliveryLabel(value) {{
      const bucket = publicDeliveryBucket(value);
      if (bucket === 'in-person') {{
        return 'In-person';
      }}
      if (bucket === 'online-skills') {{
        return 'Online + Skills';
      }}
      return 'All';
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
        button.setAttribute('aria-pressed', String(course.courseId === selectedCourseId));
        const icon = document.createElement('span');
        icon.className = 'course-icon';
        icon.textContent = course.iconLabel || course.family;
        icon.setAttribute('aria-hidden', 'true');
        const copy = document.createElement('span');
        copy.className = 'course-copy';
        const title = document.createElement('span');
        title.className = 'course-title';
        title.textContent = course.courseName;
        const delivery = document.createElement('span');
        delivery.className = 'course-delivery';
        delivery.textContent = deliveryLabel(course.deliveryMode);
        const help = document.createElement('span');
        help.className = 'course-help';
        help.textContent = course.clarification || '';
        copy.append(title, delivery, help);
        button.append(icon, copy);
        const details = course.details || {{}};
        if (details.short_description || details.who_this_is_for || (details.topics_covered || []).length || details.full_course_page) {{
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
          if (details.full_course_page) {{
            const link = document.createElement('a');
            link.className = 'course-page-link';
            link.href = details.full_course_page;
            link.textContent = 'Full course page';
            body.appendChild(link);
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

    window.addEventListener('resize', () => {{
      renderDates();
      renderStarts();
    }});

    showAllOptions = showAllFromDeepLink();
    selectedCourseId = courseIdFromDeepLink() || selectedCourseId;
    renderAll();
  </script>
</body>
</html>
"""


def run() -> dict[str, Any]:
    payload = build_bls_pilot_schedule()
    return write_page_outputs(payload, REPORT_JSON_PATH, REPORT_MD_PATH, HTML_PATH)


def write_page_outputs(payload: dict[str, Any], report_json_path: Path, report_md_path: Path, html_path: Path) -> dict[str, Any]:
    payload = apply_final_live_availability_guard(payload)
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    report_json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_md_path.write_text(render_report(payload), encoding="utf-8")
    html_path.write_text(render_html(payload), encoding="utf-8")
    return {
        "counts": payload["counts"],
        "availability_source_used": payload["availability_source_used"],
        "availability_fallback_used": payload["availability_fallback_used"],
        "horizon_days": payload["horizonDays"],
        "top_rejection_reasons": dict(Counter(payload.get("rejectionReasonCounts", {})).most_common(10)),
        "output_paths": [report_json_path, report_md_path, html_path],
    }


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
