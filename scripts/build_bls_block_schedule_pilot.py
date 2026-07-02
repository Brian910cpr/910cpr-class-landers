from __future__ import annotations

import html
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.block_start_time_selector import ROOT, build_bls_pilot_schedule


REPORT_JSON_PATH = ROOT / "data" / "audit" / "bls_block_schedule_pilot.json"
REPORT_MD_PATH = ROOT / "data" / "audit" / "bls_block_schedule_pilot_report.md"
HTML_PATH = ROOT / "docs" / "bls-schedule.html"


def render_report(payload: dict[str, Any]) -> str:
    counts = payload["counts"]
    sample_offers = payload["offers"][:10]
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
      grid-template-columns: minmax(210px, 270px) minmax(180px, 250px) minmax(180px, 220px) minmax(0, 1fr);
      gap: 20px;
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
    .course-list { display: grid; gap: 12px; }
    .course {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: var(--band);
    }
    .course-meta {
      color: var(--muted);
      font-size: .92rem;
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
    }
    """


def render_html(payload: dict[str, Any]) -> str:
    course_options_by_id: dict[str, dict[str, Any]] = {}
    option_groups: dict[str, dict[str, Any]] = {}
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
                }
                courses.append(course_record)
                course_options_by_id.setdefault(course["courseId"], {
                    "courseId": course["courseId"],
                    "courseName": course["courseName"],
                    "family": family,
                })
                group = option_groups.setdefault(family, {
                    "family": family,
                    "label": f"All AHA {family} options",
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
    course_options = [
        course_options_by_id[course_id]
        for course_id in ("209806", "359474", "210549")
        if course_id in course_options_by_id
    ]
    course_options_json = json.dumps(course_options, ensure_ascii=False)
    option_groups_json = json.dumps(option_groups, ensure_ascii=False)
    counts = payload["counts"]
    first_course = course_options[0]["courseId"] if course_options else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BLS Schedule Pilot | 910CPR</title>
  <style>{css()}</style>
</head>
<body>
  <header>
    <h1>BLS Schedule Pilot</h1>
    <p class="muted">Select the BLS course format first, then choose a public date and start time.</p>
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
            <span>Need BLS ASAP? Show all AHA BLS options</span>
          </label>
        </div>
      </div>
      <div class="panel">
        <h2>Dates</h2>
        <div id="date-list" class="button-list"></div>
      </div>
      <div class="panel">
        <h2>Start Times</h2>
        <div id="start-list" class="button-list"></div>
      </div>
      <div class="panel">
        <h2>Register</h2>
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

    function activeCourseIds() {{
      const selected = courseOptions.find(course => course.courseId === selectedCourseId);
      if (!selected) {{
        return new Set();
      }}
      if (compareMode) {{
        return new Set(optionGroups[selected.family]?.courseIds || [selectedCourseId]);
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
        button.textContent = course.courseName;
        button.setAttribute('aria-pressed', String(course.courseId === selectedCourseId));
        button.addEventListener('click', () => {{
          selectedCourseId = course.courseId;
          renderAll();
        }});
        host.appendChild(button);
      }});
      byId('compare-toggle').checked = compareMode;
    }}

    function renderDates() {{
      const host = byId('date-list');
      host.innerHTML = '';
      const days = syncSelection();
      if (!days.length) {{
        host.innerHTML = '<div class="empty">No public dates are available for this option.</div>';
        return;
      }}
      days.forEach(day => {{
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = day.displayDate;
        button.setAttribute('aria-pressed', String(day.date === selectedDate));
        button.addEventListener('click', () => {{
          selectedDate = day.date;
          selectedStart = day.startTimes[0]?.startTime || '';
          renderAll();
        }});
        host.appendChild(button);
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
        meta.textContent = `${{course.displayStartTime}} · ${{course.durationMinutes}} min · appointmentDayId ${{course.appointmentDayId}} · courseId ${{course.courseId}}`;
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

    renderAll();
  </script>
</body>
</html>
"""


def run() -> dict[str, Any]:
    payload = build_bls_pilot_schedule()
    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(render_report(payload), encoding="utf-8")
    HTML_PATH.write_text(render_html(payload), encoding="utf-8")
    return {
        "counts": payload["counts"],
        "availability_source_used": payload["availability_source_used"],
        "availability_fallback_used": payload["availability_fallback_used"],
        "horizon_days": payload["horizonDays"],
        "top_rejection_reasons": dict(Counter(payload.get("rejectionReasonCounts", {})).most_common(10)),
        "output_paths": [REPORT_JSON_PATH, REPORT_MD_PATH, HTML_PATH],
    }


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
