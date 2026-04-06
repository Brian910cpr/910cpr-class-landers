
from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from ew_ingest import location_slug, session_slug, topic_slug_for_session

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

def page_template(title: str, body_html: str, description: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{esc(title)} | 910CPR</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(description or title)}">
<style>
:root {{--bg:#eef4f8;--card:#ffffff;--soft:#f8fbfd;--text:#1f2937;--muted:#6b7280;--accent:#2563eb;--accent-dark:#1d4ed8;--cta:#ea580c;--cta-dark:#c2410c;--border:#dbe4ee;}}
*{{box-sizing:border-box}} body{{margin:0;font-family:Arial,sans-serif;background:linear-gradient(180deg,#f8fbfd 0%,var(--bg) 100%);color:var(--text)}}
.wrap{{max-width:1220px;margin:0 auto;padding:12px 18px 60px}} .hero{{background:var(--card);border:1px solid var(--border);border-radius:24px;padding:30px;box-shadow:0 10px 30px rgba(15,23,42,.08);margin-bottom:26px}}
.hero h1{{margin:0 0 10px 0;font-size:30px;line-height:1.1}} .hero p{{margin:0;font-size:18px;color:var(--muted)}} .section-title{{margin:26px 0 14px 0;font-size:20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px}} .card{{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:22px;box-shadow:0 8px 24px rgba(15,23,42,.06)}}
.card h2{{margin:0 0 10px 0;font-size:20px;line-height:1.15}} .muted{{color:var(--muted)}} .preview-list{{list-style:none;padding:0;margin:16px 0}} .preview-list li{{margin-bottom:10px;padding-bottom:10px;border-bottom:1px dashed var(--border)}} .preview-list li:last-child{{border-bottom:0;padding-bottom:0}}
.text-link{{color:var(--accent);text-decoration:none}} .text-link:hover{{text-decoration:underline}} .button{{display:inline-block;padding:12px 16px;border-radius:12px;text-decoration:none;font-weight:700}} .button.secondary{{background:#5f6f82;color:white}}
</style>
</head><body><div class="wrap">{body_html}</div></body></html>"""

def load_payload(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def build_discovery(schedule_json: Path, output_html: Path) -> None:
    payload = load_payload(schedule_json)
    sessions = payload.get("sessions", [])

    upcoming = []
    for s in sessions:
        try:
            s_date = datetime.fromisoformat(s.get("start"))
        except Exception:
            continue
        upcoming.append((s_date, s))
    upcoming.sort(key=lambda x: (x[0], x[1].get("id") or 0))
    upcoming_sessions = [s for _, s in upcoming]

    by_topic = defaultdict(list)
    by_location = defaultdict(list)
    for s in upcoming_sessions:
        topic = s.get("topic_slug") or topic_slug_for_session(s)
        by_topic[topic].append(s)
        by_location[s.get("location") or "Unknown Location"].append(s)

    course_cards = []
    for topic in sorted(by_topic):
        items = by_topic[topic][:6]
        lis = "".join(
            f'<li><a class="text-link" href="classes/{session_slug(i)}.html">{esc(pretty_dt(i.get("start","")))}</a> <span class="muted">• {esc(i.get("location",""))}</span></li>'
            for i in items
        )
        course_cards.append(
            f'<section class="card"><h2>{esc(TOPIC_LABELS.get(topic, topic.title()))}</h2><div class="muted">{len(by_topic[topic])} upcoming public sessions</div><ul class="preview-list">{lis}</ul><p><a class="button secondary" href="topics/{topic}.html">View all sessions</a></p></section>'
        )

    location_cards = []
    for location in sorted(by_location):
        items = by_location[location][:6]
        slug = location_slug(location)
        lis = "".join(
            f'<li><a class="text-link" href="classes/{session_slug(i)}.html">{esc(i.get("course_title") or i.get("course_display_title"))}</a> <span class="muted">• {esc(pretty_dt(i.get("start","")))}</span></li>'
            for i in items
        )
        location_cards.append(
            f'<section class="card"><h2>{esc(location)}</h2><div class="muted">{len(by_location[location])} upcoming public sessions</div><ul class="preview-list">{lis}</ul><p><a class="button secondary" href="locations/{slug}.html">View all sessions</a></p></section>'
        )

    body = (
        '<section class="hero"><h1>Find Your CPR Class</h1><p>Browse upcoming public 910CPR sessions by course type or by location.</p></section>'
        f'<h2 class="section-title">Browse by Course</h2><div class="grid">{"".join(course_cards)}</div>'
        f'<h2 class="section-title">Browse by Location</h2><div class="grid">{"".join(location_cards)}</div>'
    )
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(page_template("CPR Class Schedule", body, "Browse upcoming public CPR, BLS, ACLS, PALS, Heartsaver, and first aid classes with 910CPR."), encoding="utf-8")
    print(f"Wrote {output_html}")

def main() -> int:
    parser = argparse.ArgumentParser(description="Build human-readable discovery page from schedule.json")
    parser.add_argument("--schedule-json", required=True)
    parser.add_argument("--output-html", required=True)
    args = parser.parse_args()
    build_discovery(Path(args.schedule_json), Path(args.output_html))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
