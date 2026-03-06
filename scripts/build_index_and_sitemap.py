import json
import re
from html import unescape
from datetime import datetime
from pathlib import Path
import hashlib

from title_cleaner import normalize_course_title

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "schedule.json"
DOCS_DIR = ROOT / "docs"
INDEX_FILE = DOCS_DIR / "index.html"
SITEMAP_FILE = DOCS_DIR / "sitemap.xml"

SITE_BASE = "https://910cpr.com"
PUBLIC_LOCATION = "Wilmington; Shipyard Blvd"
PUBLIC_SEATS_SENTINEL = 555


def strip_html(text: str) -> str:
    if text is None:
        return ""
    text = unescape(str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_course_name(raw: str) -> str:
    return normalize_course_title(raw) or strip_html(raw) or "CPR Class"


def short_slug(text: str, max_len: int = 70) -> str:
    clean = clean_course_name(text).lower()
    clean = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
    digest = hashlib.md5(clean.encode("utf-8")).hexdigest()[:8]

    if len(clean) > max_len:
        clean = clean[:max_len].rstrip("-")

    return f"{clean}-{digest}" if clean else digest


def parse_start(start_value: str):
    raw = str(start_value).strip()

    dt = None
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
    ):
        try:
            dt = datetime.strptime(raw, fmt)
            break
        except ValueError:
            pass

    if dt is None:
        return raw, "", ""

    display_date = dt.strftime("%B %d, %Y")
    display_time = dt.strftime("%I:%M %p").lstrip("0")
    iso_date = dt.strftime("%Y-%m-%d")
    return display_date, display_time, iso_date


def is_public(session: dict) -> bool:
    location = str(session.get("location", "")).strip()
    seats = session.get("seats")

    try:
        seats = int(seats) if seats is not None else None
    except Exception:
        seats = None

    if location == PUBLIC_LOCATION:
        return True

    if location != PUBLIC_LOCATION and seats == PUBLIC_SEATS_SENTINEL:
        return True

    return False


with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

all_sessions = data["sessions"]
sessions = [s for s in all_sessions if is_public(s)]
sessions.sort(key=lambda s: str(s.get("start", "")))

course_groups = {}
location_groups = {}

for s in sessions:
    course_name = clean_course_name(s.get("course", "CPR Class"))
    location = str(s.get("location", "Wilmington NC")).strip()

    course_groups.setdefault(course_name, []).append(s)
    location_groups.setdefault(location, []).append(s)

COURSES_DIR = DOCS_DIR / "courses"
LOCATIONS_DIR = DOCS_DIR / "locations"
COURSES_DIR.mkdir(parents=True, exist_ok=True)
LOCATIONS_DIR.mkdir(parents=True, exist_ok=True)

course_blocks = []
for course_name, items in sorted(course_groups.items(), key=lambda x: x[0]):
    sample_links = []
    for s in items[:12]:
        session_id = s.get("session_id")
        display_date, display_time, _ = parse_start(s.get("start", ""))
        loc = str(s.get("location", "")).strip()
        sample_links.append(
            f'<li><a href="classes/{session_id}.html">{display_date} at {display_time} • {loc}</a></li>'
        )

    course_slug = short_slug(course_name)
    course_blocks.append(f"""
    <section class="card">
      <h2>{course_name}</h2>
      <p class="muted">{len(items)} upcoming public sessions</p>
      <ul>
        {''.join(sample_links)}
      </ul>
      <p><a class="button secondary" href="courses/{course_slug}.html">View all sessions</a></p>
    </section>
    """)

location_blocks = []
for location_name, items in sorted(location_groups.items(), key=lambda x: x[0]):
    sample_links = []
    for s in items[:10]:
        session_id = s.get("session_id")
        course_name = clean_course_name(s.get("course", "CPR Class"))
        display_date, display_time, _ = parse_start(s.get("start", ""))
        sample_links.append(
            f'<li><a href="classes/{session_id}.html">{course_name} • {display_date} at {display_time}</a></li>'
        )

    location_slug = short_slug(location_name)
    location_blocks.append(f"""
    <section class="card">
      <h2>{location_name}</h2>
      <p class="muted">{len(items)} upcoming public sessions</p>
      <ul>
        {''.join(sample_links)}
      </ul>
      <p><a class="button secondary" href="locations/{location_slug}.html">View all sessions</a></p>
    </section>
    """)

index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CPR Class Schedule | 910CPR</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Browse upcoming public CPR, BLS, ACLS, PALS, Heartsaver, and first aid classes with 910CPR.">
<style>
body {{
  font-family: Arial, sans-serif;
  background: linear-gradient(#f5f6f7, #e9eef2);
  margin: 0;
  padding: 40px 20px;
  color: #222;
}}
.wrap {{
  max-width: 1100px;
  margin: 0 auto;
}}
.hero {{
  background: #f1f1f1;
  border-radius: 18px;
  padding: 32px;
  box-shadow: 0 3px 12px rgba(0,0,0,0.15);
  margin-bottom: 24px;
}}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
}}
.card {{
  background: #f1f1f1;
  border-radius: 14px;
  padding: 24px;
  box-shadow: 0 3px 12px rgba(0,0,0,0.12);
}}
.button {{
  display: inline-block;
  background: #2c73d2;
  color: white;
  padding: 12px 18px;
  border-radius: 10px;
  text-decoration: none;
  font-weight: bold;
}}
.button.secondary {{
  background: #5a6774;
}}
a {{
  color: #2c73d2;
  text-decoration: none;
}}
a:hover {{
  text-decoration: underline;
}}
ul {{
  padding-left: 20px;
}}
li {{
  margin-bottom: 8px;
}}
.muted {{
  color: #555;
}}
</style>
</head>
<body>
<div class="wrap">

  <section class="hero">
    <h1>Find Your CPR Class</h1>
    <p>Browse upcoming public 910CPR sessions by course type or by location.</p>
  </section>

  <h2>Browse by Course</h2>
  <div class="grid">
    {''.join(course_blocks)}
  </div>

  <h2 style="margin-top:32px;">Browse by Location</h2>
  <div class="grid">
    {''.join(location_blocks)}
  </div>

</div>
</body>
</html>
"""

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    f.write(index_html)

for course_name, items in course_groups.items():
    course_slug = short_slug(course_name)
    rows = []

    for s in items:
        session_id = s.get("session_id")
        location = str(s.get("location", "")).strip()
        display_date, display_time, _ = parse_start(s.get("start", ""))
        rows.append(
            f'<li><a href="../classes/{session_id}.html">{display_date} at {display_time} • {location}</a></li>'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{course_name} Classes | 910CPR</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Browse upcoming public {course_name} classes with 910CPR.">
<style>
body {{
  font-family: Arial, sans-serif;
  background: linear-gradient(#f5f6f7, #e9eef2);
  margin: 0;
  padding: 40px 20px;
}}
.wrap {{
  max-width: 900px;
  margin: 0 auto;
}}
.card {{
  background: #f1f1f1;
  border-radius: 14px;
  padding: 24px;
  box-shadow: 0 3px 12px rgba(0,0,0,0.12);
}}
a {{
  color: #2c73d2;
  text-decoration: none;
}}
li {{
  margin-bottom: 8px;
}}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <h1>{course_name}</h1>
    <p><a href="../index.html">← Back to full schedule</a></p>
    <ul>
      {''.join(rows)}
    </ul>
  </div>
</div>
</body>
</html>
"""
    with open(COURSES_DIR / f"{course_slug}.html", "w", encoding="utf-8") as f:
        f.write(html)

for location_name, items in location_groups.items():
    location_slug = short_slug(location_name)
    rows = []

    for s in items:
        session_id = s.get("session_id")
        course_name = clean_course_name(s.get("course", "CPR Class"))
        display_date, display_time, _ = parse_start(s.get("start", ""))
        rows.append(
            f'<li><a href="../classes/{session_id}.html">{course_name} • {display_date} at {display_time}</a></li>'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CPR Classes in {location_name} | 910CPR</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Browse upcoming public CPR classes in {location_name} with 910CPR.">
<style>
body {{
  font-family: Arial, sans-serif;
  background: linear-gradient(#f5f6f7, #e9eef2);
  margin: 0;
  padding: 40px 20px;
}}
.wrap {{
  max-width: 900px;
  margin: 0 auto;
}}
.card {{
  background: #f1f1f1;
  border-radius: 14px;
  padding: 24px;
  box-shadow: 0 3px 12px rgba(0,0,0,0.12);
}}
a {{
  color: #2c73d2;
  text-decoration: none;
}}
li {{
  margin-bottom: 8px;
}}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <h1>CPR Classes in {location_name}</h1>
    <p><a href="../index.html">← Back to full schedule</a></p>
    <ul>
      {''.join(rows)}
    </ul>
  </div>
</div>
</body>
</html>
"""
    with open(LOCATIONS_DIR / f"{location_slug}.html", "w", encoding="utf-8") as f:
        f.write(html)

urls = [f"{SITE_BASE}/", f"{SITE_BASE}/index.html"]

for s in sessions:
    session_id = s.get("session_id")
    urls.append(f"{SITE_BASE}/classes/{session_id}.html")

for course_name in course_groups.keys():
    urls.append(f"{SITE_BASE}/courses/{short_slug(course_name)}.html")

for location_name in location_groups.keys():
    urls.append(f"{SITE_BASE}/locations/{short_slug(location_name)}.html")

sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
sitemap_xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

for url in urls:
    sitemap_xml.append("  <url>")
    sitemap_xml.append(f"    <loc>{url}</loc>")
    sitemap_xml.append("  </url>")

sitemap_xml.append("</urlset>")

with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(sitemap_xml))

print(f"Built index, course pages, location pages, and sitemap for {len(sessions)} PUBLIC sessions.")