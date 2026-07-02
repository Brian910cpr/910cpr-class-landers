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


def render_report(payload: dict[str, Any]) -> str:
    counts = payload["counts"]
    sample_offers = payload["offers"][:10]
    guard = payload.get("liveAvailabilityGuard", {})
    lines = [
        "# BLS Block-Based Schedule Pilot",
        "",
        "Local build artifact for the customer-facing BLS pilot. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.",
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
    .pilot-grid {
      display: grid;
      grid-template-columns: minmax(220px, 1.05fr) minmax(270px, 1.2fr) minmax(170px, .85fr) minmax(230px, 1fr);
      gap: 16px;
      align-items: start;
    }
    .panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      padding: 16px;
    }
    .button-list { display: grid; gap: 8px; }
    .choice-list { display: grid; gap: 8px; margin-bottom: 14px; }
    .option-tools { display: grid; gap: 12px; }
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
    .month-stack { display: grid; gap: 14px; }
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
    .course-list { display: grid; gap: 12px; }
    .course {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: var(--band);
    }
    .course-meta {
      color: var(--muted);
      font-size: .92rem;
      margin: 3px 0 12px;
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
      .pilot-grid { grid-template-columns: 1fr; }
      header, main { padding: 18px; }
      .panel { padding: 14px; }
    }
    """


def render_html(payload: dict[str, Any]) -> str:
    page_config = payload.get("pageConfig", {})
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
            "deepLinkAliases": [
                str(alias)
                for alias in ([option.get("variant")] + list(option.get("deep_link_aliases", [])))
                if alias
            ],
            "iconLabel": option.get("icon_label") or page_family,
            "clarification": option.get("clarification") or "",
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
    intro = html.escape(str(page_config.get("intro") or "Select a course, date, and start time."))
    compare_label = html.escape(str(page_config.get("compare_mode", {}).get("label") or "Show all options"))
    compare_enabled = page_config.get("compare_mode", {}).get("enabled") is True
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
    <p class="muted">{intro}</p>
    <p class="muted">Pilot proof: whole availability blocks are not shown as class times. Public-selectable offers: {counts['publicSelectableOfferCount']}.</p>
  </header>
  <main>
    <section class="pilot-grid" aria-label="BLS block-based schedule pilot">
      <div class="panel">
        <h2>Course</h2>
        <div id="course-option-list" class="choice-list"></div>
        <div class="option-tools">
          <label class="compare-toggle">
            <input id="compare-toggle" type="checkbox">
            <span>{compare_label}</span>
          </label>
        </div>
      </div>
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
    </section>
  </main>
  <script>
    const scheduleDates = {data_json};
    const courseOptions = {course_options_json};
    const optionGroups = {option_groups_json};
    let selectedCourseId = {json.dumps(first_course)};
    let compareMode = false;
    let selectedDate = '';
    let selectedStart = '';

    function byId(id) {{
      return document.getElementById(id);
    }}

    function normalizeDeepLink(value) {{
      return String(value || '').trim().toLowerCase().replace(/^#/, '');
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

    function activeCourseIds() {{
      const selected = courseOptions.find(course => course.courseId === selectedCourseId);
      if (!selected) {{
        return new Set();
      }}
      if (compareMode) {{
        const group = Object.values(optionGroups).find(item => item.courseIds?.includes(selectedCourseId));
        return new Set(group?.courseIds || optionGroups[selected.family]?.courseIds || [selectedCourseId]);
      }}
      return new Set([selectedCourseId]);
    }}

    function filteredCourses(slot) {{
      const ids = activeCourseIds();
      return slot.courses.filter(course => ids.has(course.courseId));
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
      if (!days.length) {{
        selectedDate = '';
        selectedStart = '';
        return days;
      }}
      if (!days.some(day => day.date === selectedDate)) {{
        selectedDate = days[0].date;
      }}
      const day = days.find(item => item.date === selectedDate);
      if (!day.startTimes.some(slot => slot.startTime === selectedStart)) {{
        selectedStart = day.startTimes[0]?.startTime || '';
      }}
      return days;
    }}

    function renderCourseOptions() {{
      const host = byId('course-option-list');
      host.innerHTML = '';
      courseOptions.forEach(course => {{
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
        const help = document.createElement('span');
        help.className = 'course-help';
        help.textContent = course.clarification || '';
        copy.append(title, help);
        button.append(icon, copy);
        button.addEventListener('click', () => {{
          selectedCourseId = course.courseId;
          renderAll();
        }});
        host.appendChild(button);
      }});
      byId('compare-toggle').checked = compareMode;
      byId('compare-toggle').disabled = {str(not compare_enabled).lower()};
    }}

    function renderDates() {{
      const host = byId('date-list');
      host.innerHTML = '';
      const days = syncSelection();
      if (!days.length) {{
        host.innerHTML = '<div class="empty">No public dates are available for this option.</div>';
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
      monthKeys.slice(0, 3).forEach(monthKey => {{
        const [year, month] = monthKey.split('-').map(Number);
        const first = new Date(year, month - 1, 1);
        const last = new Date(year, month, 0);
        const section = document.createElement('section');
        section.className = 'month';
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
            button.setAttribute('aria-label', `${{available.displayDate}} available`);
            button.setAttribute('aria-pressed', String(available.date === selectedDate));
            button.addEventListener('click', () => {{
              selectedDate = available.date;
              selectedStart = available.startTimes[0]?.startTime || '';
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
        host.innerHTML = '<div class="empty">Select another date.</div>';
        return;
      }}
      day.startTimes.forEach(slot => {{
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = slot.displayStartTime;
        button.setAttribute('aria-pressed', String(slot.startTime === selectedStart));
        button.addEventListener('click', () => {{
          selectedStart = slot.startTime;
          renderAll();
        }});
        host.appendChild(button);
      }});
    }}

    function renderCourses() {{
      const host = byId('course-list');
      host.innerHTML = '';
      const day = filteredDates().find(item => item.date === selectedDate);
      const slot = day?.startTimes.find(item => item.startTime === selectedStart);
      if (!slot || !slot.courses.length) {{
        host.innerHTML = '<div class="empty">Select a start time.</div>';
        return;
      }}
      slot.courses.forEach(course => {{
        const item = document.createElement('article');
        item.className = 'course';
        const title = document.createElement('h3');
        title.textContent = course.courseName;
        const meta = document.createElement('div');
        meta.className = 'course-meta';
        meta.textContent = `${{course.location}} · ${{course.displayStartTime}}`;
        const link = document.createElement('a');
        link.className = 'register-link';
        link.href = course.appointmentUrl;
        link.textContent = 'Register';
        item.append(title, meta, link);
        host.appendChild(item);
      }});
    }}

    function renderAll() {{
      syncSelection();
      renderCourseOptions();
      renderDates();
      renderStarts();
      renderCourses();
    }}

    byId('compare-toggle').addEventListener('change', event => {{
      compareMode = event.target.checked;
      renderAll();
    }});

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
