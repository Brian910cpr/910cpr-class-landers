
from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from ew_ingest import course_slug, location_slug, session_slug, topic_slug_for_session

TOPIC_LABELS = {
    "bls": "BLS",
    "acls": "ACLS",
    "pals": "PALS",
    "heartsaver": "Heartsaver",
    "red-cross": "Red Cross",
    "hsi": "HSI",
    "uscg": "USCG / Coast Guard",
    "instructor": "Instructor Courses",
    "family-friends": "Family & Friends",
    "aed": "AED / Maintenance",
    "first-aid": "First Aid",
    "misc": "Other Courses",
}

def esc(v: Any) -> str:
    return html.escape("" if v is None else str(v))

def pretty_dt(iso_text: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_text)
        return dt.strftime("%B %d, %Y at %-I:%M %p")
    except Exception:
        return str(iso_text or "")

def load_payload(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def page_template(title: str, body_html: str, description: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{esc(title)} | 910CPR</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(description or title)}">
<meta name="robots" content="index,follow">
<style>
:root{{--bg:#eef4f8;--card:#fff;--text:#1f2937;--muted:#6b7280;--accent:#2563eb;--border:#dbe4ee}}
*{{box-sizing:border-box}} body{{margin:0;font-family:Arial,sans-serif;background:linear-gradient(180deg,#f8fbfd 0%,var(--bg) 100%);color:var(--text)}}
.wrap{{max-width:1200px;margin:0 auto;padding:20px 18px 50px}} .hero,.card{{background:var(--card);border:1px solid var(--border);border-radius:20px;box-shadow:0 8px 24px rgba(15,23,42,.06)}}
.hero{{padding:26px;margin-bottom:22px}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}} .card{{padding:18px}}
h1{{margin:0 0 8px;font-size:30px}} h2{{margin:0 0 12px;font-size:22px}} h3{{margin:0 0 10px;font-size:18px}} p,li{{line-height:1.45}}
.muted{{color:var(--muted)}} a{{color:var(--accent);text-decoration:none}} a:hover{{text-decoration:underline}} .button{{display:inline-block;padding:11px 15px;background:#5f6f82;color:#fff;border-radius:12px;font-weight:700;text-decoration:none}}
.list{{margin:0;padding-left:18px}} .section{{margin-top:24px}}
</style>
</head>
<body><div class="wrap">{body_html}</div></body></html>"""

def write_page(path: Path, title: str, body_html: str, description: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page_template(title, body_html, description), encoding="utf-8")

def session_link(session: Dict[str, Any], relative_prefix: str = "../") -> str:
    href = f"{relative_prefix}classes/{session_slug(session)}.html"
    title = esc(session.get("course_title") or session.get("course_display_title"))
    meta = f"{esc(pretty_dt(session.get('start','')))} • {esc(session.get('location',''))}"
    return f'<li><a href="{href}">{title}</a> <span class="muted">• {meta}</span></li>'

def course_link(course: Dict[str, Any], relative_prefix: str = "../") -> str:
    href = f"{relative_prefix}courses/{course_slug(course)}.html"
    title = esc(course.get("title") or course.get("source_name"))
    meta = esc(course.get("family") or course.get("discipline") or "")
    return f'<li><a href="{href}">{title}</a> <span class="muted">• {meta}</span></li>'

def build_index(schedule_json: Path, output_dir: Path) -> None:
    payload = load_payload(schedule_json)
    sessions = payload.get("sessions", [])
    courses = payload.get("courses", [])

    by_topic = defaultdict(list)
    by_year = defaultdict(list)
    by_topic_year = defaultdict(list)
    by_location = defaultdict(list)

    for s in sessions:
        topic = s.get("topic_slug") or topic_slug_for_session(s)
        year = str(s.get("year") or "unknown")
        location = s.get("location") or "Unknown Location"
        by_topic[topic].append(s)
        by_year[year].append(s)
        by_topic_year[(topic, year)].append(s)
        by_location[location].append(s)

    for topic, items in by_topic.items():
        items = sorted(items, key=lambda x: (x.get("start") or "", x.get("id") or 0))
        year_links = []
        for year in sorted({str(i.get("year") or "unknown") for i in items}):
            year_links.append(f'<li><a href="../topics-year/{topic}-{year}.html">{esc(TOPIC_LABELS.get(topic, topic.title()))} {esc(year)}</a></li>')
        sessions_html = "".join(session_link(i) for i in items[:500])
        body = (
            '<p><a href="../index.html">Back to Index</a></p>'
            f'<section class="hero"><h1>{esc(TOPIC_LABELS.get(topic, topic.title()))}</h1><p class="muted">{len(items)} session pages in this topic bucket.</p></section>'
            f'<section class="card"><h2>Topic-year buckets</h2><ul class="list">{"".join(year_links) or "<li>No year buckets</li>"}</ul></section>'
            f'<section class="section card"><h2>Sessions</h2><ul class="list">{sessions_html or "<li>No sessions</li>"}</ul></section>'
        )
        write_page(output_dir / "topics" / f"{topic}.html", TOPIC_LABELS.get(topic, topic.title()), body)

    for year, items in by_year.items():
        items = sorted(items, key=lambda x: (x.get("start") or "", x.get("id") or 0))
        topic_links = []
        for topic in sorted({i.get("topic_slug") or topic_slug_for_session(i) for i in items}):
            topic_links.append(f'<li><a href="../topics-year/{topic}-{year}.html">{esc(TOPIC_LABELS.get(topic, topic.title()))} {esc(year)}</a></li>')
        body = (
            '<p><a href="../index.html">Back to Index</a></p>'
            f'<section class="hero"><h1>{esc(year)} Sessions</h1><p class="muted">{len(items)} session pages in this year bucket.</p></section>'
            f'<section class="card"><h2>Topic-year buckets</h2><ul class="list">{"".join(topic_links) or "<li>No topic-year buckets</li>"}</ul></section>'
            f'<section class="section card"><h2>Sessions</h2><ul class="list">{"".join(session_link(i) for i in items[:500]) or "<li>No sessions</li>"}</ul></section>'
        )
        write_page(output_dir / "years" / f"{year}.html", f"{year} Sessions", body)

    for (topic, year), items in by_topic_year.items():
        items = sorted(items, key=lambda x: (x.get("start") or "", x.get("id") or 0))
        body = (
            '<p><a href="../index.html">Back to Index</a></p>'
            f'<section class="hero"><h1>{esc(TOPIC_LABELS.get(topic, topic.title()))} {esc(year)}</h1><p class="muted">{len(items)} session pages in this topic-year bucket.</p></section>'
            f'<section class="card"><h2>Sessions</h2><ul class="list">{"".join(session_link(i) for i in items[:500]) or "<li>No sessions</li>"}</ul></section>'
        )
        write_page(output_dir / "topics-year" / f"{topic}-{year}.html", f"{TOPIC_LABELS.get(topic, topic.title())} {year}", body)

    for location, items in by_location.items():
        items = sorted(items, key=lambda x: (x.get("start") or "", x.get("id") or 0))
        slug = location_slug(location)
        body = (
            '<p><a href="../index.html">Back to Index</a></p>'
            f'<section class="hero"><h1>{esc(location)}</h1><p class="muted">{len(items)} session pages in this location bucket.</p></section>'
            f'<section class="card"><h2>Sessions</h2><ul class="list">{"".join(session_link(i) for i in items[:500]) or "<li>No sessions</li>"}</ul></section>'
        )
        write_page(output_dir / "locations" / f"{slug}.html", location, body)

    courses_sorted = sorted(courses, key=lambda c: (c.get("family") or "", c.get("title") or c.get("source_name") or ""))
    body = (
        '<p><a href="../index.html">Back to Index</a></p>'
        f'<section class="hero"><h1>All Course Files</h1><p class="muted">{len(courses_sorted)} course rows from course export.</p></section>'
        f'<section class="card"><h2>Courses</h2><ul class="list">{"".join(course_link(c) for c in courses_sorted) or "<li>No courses</li>"}</ul></section>'
    )
    write_page(output_dir / "courses" / "all-courses.html", "All Course Files", body)

    topic_cards = []
    for topic in sorted(by_topic):
        topic_cards.append(
            f'<section class="card"><h3>{esc(TOPIC_LABELS.get(topic, topic.title()))}</h3><p class="muted">{len(by_topic[topic])} session pages</p><p><a class="button" href="topics/{topic}.html">Open topic hub</a></p></section>'
        )
    year_cards = []
    for year in sorted(by_year):
        year_cards.append(
            f'<section class="card"><h3>{esc(year)}</h3><p class="muted">{len(by_year[year])} session pages</p><p><a class="button" href="years/{year}.html">Open year index</a></p></section>'
        )
    loc_cards = []
    for location in sorted(by_location):
        slug = location_slug(location)
        loc_cards.append(
            f'<section class="card"><h3>{esc(location)}</h3><p class="muted">{len(by_location[location])} session pages</p><p><a class="button" href="locations/{slug}.html">Open location index</a></p></section>'
        )

    body = (
        '<section class="hero">'
        '<h1>Structured Index System for Classes and Courses</h1>'
        '<p class="muted">This layer does not change your existing pages. It adds organized hub pages built from schedule.json and course-export / class-report data.</p>'
        f'<p><strong>Coverage:</strong> {len(courses)} course rows and {len(sessions)} session rows.</p>'
        '</section>'
        f'<div class="section"><h2>Browse by topic</h2><div class="grid">{"".join(topic_cards)}</div></div>'
        f'<div class="section"><h2>Browse by year</h2><div class="grid">{"".join(year_cards)}</div></div>'
        f'<div class="section"><h2>Browse by location</h2><div class="grid">{"".join(loc_cards)}</div></div>'
        '<div class="section"><section class="card"><h2>Course file directory</h2><p class="muted">Every course row from the course export is listed in one place.</p><p><a class="button" href="courses/all-courses.html">Open all course files</a></p></section></div>'
    )
    write_page(output_dir / "index.html", "Structured Index System", body)
    print(f"Wrote structured index pages to {output_dir}")

def main() -> int:
    parser = argparse.ArgumentParser(description="Build structured index pages from schedule.json")
    parser.add_argument("--schedule-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    build_index(Path(args.schedule_json), Path(args.output_dir))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
