import json
import re
from html import unescape
from datetime import datetime
from pathlib import Path

from title_cleaner import normalize_course_title

# ---------------------------------------------------------------------
# FULL FILE REPLACEMENT
#
# PUT THIS FILE AT:
#   scripts/build_index_and_sitemap.py
#
# RUN IT FROM REPO ROOT WITH:
#   python scripts/build_index_and_sitemap.py
#
# IT READS:
#   data/schedule.json
#
# IT WRITES:
#   docs/index.html
#   docs/classes/index.html
#   docs/courses/index.html
#   docs/courses/<course-slug>.html
#   docs/locations/<location-slug>.html
#   docs/sitemap.xml
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "schedule.json"

DOCS_DIR = ROOT / "docs"
INDEX_FILE = DOCS_DIR / "index.html"
SITEMAP_FILE = DOCS_DIR / "sitemap.xml"

CLASSES_DIR = DOCS_DIR / "classes"
COURSES_DIR = DOCS_DIR / "courses"
LOCATIONS_DIR = DOCS_DIR / "locations"

CLASSES_INDEX_FILE = CLASSES_DIR / "index.html"
COURSES_INDEX_FILE = COURSES_DIR / "index.html"

SITE_BASE = "https://www.910cpr.com"
GTM_ID = "GTM-PQS8DCBH"

PHONE_DISPLAY = "910-395-5193"
PHONE_LINK = "tel:+19103955193"
ENROLLWARE_SCHEDULE_URL = "https://coastalcprtraining.enrollware.com/site/coastalcprtraining/schedule"


def render_gtm_head():
    if not GTM_ID:
        return ""
    return f"""<!-- Google Tag Manager -->
<script>
(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{GTM_ID}');
</script>
<!-- End Google Tag Manager -->"""


def render_gtm_body():
    if not GTM_ID:
        return ""
    return f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""


def telemetry_script(page_type: str, page_name: str):
    safe_page_name = str(page_name).replace("\\", "\\\\").replace('"', '\\"')
    return f"""
<script>
window.dataLayer = window.dataLayer || [];
window.dataLayer.push({{
  event: "page_context",
  page_type: "{page_type}",
  page_name: "{safe_page_name}"
}});
</script>
"""


def strip_html(text: str) -> str:
    if text is None:
        return ""
    text = unescape(str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_course_name(raw: str) -> str:
    return normalize_course_title(raw) or strip_html(raw) or "CPR Class"


def short_slug(text: str, max_len: int = 80) -> str:
    clean = clean_course_name(text).lower()
    clean = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
    if len(clean) > max_len:
        clean = clean[:max_len].rstrip("-")
    return clean or "untitled"


def parse_start_dt(start_value: str):
    raw = str(start_value or "").strip()
    if not raw:
        return None

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            pass

    return None


def parse_start(start_value: str):
    dt = parse_start_dt(start_value)

    if dt is None:
        return "Undated", "", "", None, "Undated", ""

    display_date = dt.strftime("%B %d, %Y")
    display_time = dt.strftime("%I:%M %p").lstrip("0")
    iso_date = dt.strftime("%Y-%m-%d")
    month_label = dt.strftime("%B %Y")
    year_label = dt.strftime("%Y")
    return display_date, display_time, iso_date, dt, month_label, year_label


def is_public_listing_location(location: str) -> bool:
    return str(location or "").strip().startswith("::")


def clean_location_display(location: str) -> str:
    value = str(location or "").strip()
    if value.startswith("::"):
        value = value[2:].strip()
    return value


def location_label(location: str) -> str:
    return clean_location_display(location) or "Wilmington, NC"


def is_from_2019_forward(session: dict) -> bool:
    dt = parse_start_dt(session.get("start", ""))
    return bool(dt and dt.year >= 2019)


def html_escape(text: str) -> str:
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def session_detail_href(session_id) -> str:
    return f"/classes/{session_id}.html"


def simple_session_line(session: dict, show_course: bool = False, show_location: bool = False) -> str:
    display_date, display_time, _, _, _, _ = parse_start(session.get("start", ""))
    course_name = clean_course_name(session.get("course", "CPR Class"))
    location = location_label(session.get("location", ""))
    session_id = str(session.get("session_id", "")).strip()
    register_url = str(session.get("register_url", "")).strip()

    left_parts = []
    if show_course:
        left_parts.append(course_name)
    left_parts.append(display_date)
    if display_time:
        left_parts.append(display_time)
    if show_location:
        left_parts.append(location)

    left_text = " | ".join(p for p in left_parts if p)

    details_link = session_detail_href(session_id)
    details_html = f'<a href="{details_link}">Details</a>' if session_id else ""
    register_html = f'<a href="{register_url}">Register</a>' if register_url else ""

    tail_bits = [x for x in (details_html, register_html) if x]
    tail = " | ".join(tail_bits)

    if tail:
        return f"<li>{html_escape(left_text)} | {tail}</li>"
    return f"<li>{html_escape(left_text)}</li>"


def grouped_session_list(items, show_course=False, show_location=False):
    groups = {}
    for s in items:
        _, _, _, _, month_label, _ = parse_start(s.get("start", ""))
        groups.setdefault(month_label or "Undated", []).append(s)

    month_names = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }

    def month_sort_key(label):
        if label == "Undated":
            return (9999, 99)
        try:
            month, year = label.split()
            return (int(year), month_names[month])
        except Exception:
            return (9999, 99)

    blocks = []
    for month_label in sorted(groups.keys(), key=month_sort_key):
        lis = "\n".join(
            simple_session_line(s, show_course=show_course, show_location=show_location)
            for s in groups[month_label]
        )
        blocks.append(f"""
<h2 id="{short_slug(month_label)}">{html_escape(month_label)}</h2>
<ul>
{lis}
</ul>
""")
    return "\n".join(blocks)


BASE_STYLES = """
<style>
body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
  color: #111827;
  background: #ffffff;
  line-height: 1.45;
}
.wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 16px;
}
header, footer {
  border-bottom: 1px solid #e5e7eb;
}
footer {
  border-top: 1px solid #e5e7eb;
  border-bottom: 0;
  margin-top: 30px;
}
h1, h2, h3 {
  line-height: 1.2;
}
a {
  color: #1d4ed8;
}
ul {
  margin-top: 10px;
}
.meta {
  color: #4b5563;
}
.small {
  font-size: 14px;
  color: #4b5563;
}
.nav a {
  margin-right: 12px;
}
.section {
  margin-top: 28px;
}
.columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
}
.plain-card {
  border: 1px solid #e5e7eb;
  padding: 14px;
  border-radius: 8px;
}
</style>
"""


def page_template(title: str, description: str, body_html: str, page_type: str, page_name: str, canonical_path: str):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html_escape(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{html_escape(description)}">
<link rel="canonical" href="{SITE_BASE}{canonical_path}">
{render_gtm_head()}
{BASE_STYLES}
</head>
<body>
{render_gtm_body()}
<header>
  <div class="wrap">
    <div><strong><a href="/index.html">910CPR</a></strong></div>
    <div class="nav small" style="margin-top:8px;">
      <a href="/index.html">Home</a>
      <a href="/classes/index.html">Classes</a>
      <a href="/courses/index.html">Courses</a>
      <a href="{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
      <a href="{ENROLLWARE_SCHEDULE_URL}">Enrollware Schedule</a>
    </div>
  </div>
</header>

<div class="wrap">
{body_html}
</div>

<footer>
  <div class="wrap small">
    <p><strong>910CPR</strong></p>
    <p>CPR, BLS, ACLS, PALS, Heartsaver, and first aid training.</p>
    <p><a href="{PHONE_LINK}">{PHONE_DISPLAY}</a></p>
  </div>
</footer>

{telemetry_script(page_type, page_name)}
</body>
</html>"""


def build():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing data file: {DATA_FILE}")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    CLASSES_DIR.mkdir(parents=True, exist_ok=True)
    COURSES_DIR.mkdir(parents=True, exist_ok=True)
    LOCATIONS_DIR.mkdir(parents=True, exist_ok=True)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_sessions = data.get("sessions", [])

    sessions = [
        s for s in all_sessions
        if is_public_listing_location(s.get("location", "")) and is_from_2019_forward(s)
    ]
    sessions.sort(key=lambda s: str(s.get("start", "")))

    course_groups = {}
    location_groups = {}
    year_groups = {}

    for s in sessions:
        course_name = clean_course_name(s.get("course", "CPR Class"))
        location = location_label(s.get("location", "Wilmington, NC"))
        _, _, _, _, _, year_label = parse_start(s.get("start", ""))

        course_groups.setdefault(course_name, []).append(s)
        location_groups.setdefault(location, []).append(s)
        year_groups.setdefault(year_label or "Undated", []).append(s)

    course_links = []
    for course_name, items in sorted(course_groups.items(), key=lambda x: x[0]):
        slug = short_slug(course_name)
        course_links.append(
            f'<li><a href="/courses/{slug}.html">{html_escape(course_name)}</a> ({len(items)})</li>'
        )

    location_links = []
    for location_name, items in sorted(location_groups.items(), key=lambda x: x[0]):
        slug = short_slug(location_name)
        location_links.append(
            f'<li><a href="/locations/{slug}.html">{html_escape(location_name)}</a> ({len(items)})</li>'
        )

    year_links = []
    for year_label, items in sorted(year_groups.items(), key=lambda x: x[0]):
        year_links.append(f"<li>{html_escape(year_label)} ({len(items)})</li>")

    root_body = f"""
<h1>910CPR Class Reference Index</h1>
<p class="meta">Public listing sessions from 2019 forward. This is the rough, crawlable reference layer.</p>

<div class="section">
  <p><a href="/classes/index.html">Browse all listed classes</a></p>
  <p><a href="/courses/index.html">Browse course-type index</a></p>
</div>

<div class="section columns">
  <div class="plain-card">
    <h2>Course Types</h2>
    <ul>
      {''.join(course_links)}
    </ul>
  </div>

  <div class="plain-card">
    <h2>Locations</h2>
    <ul>
      {''.join(location_links)}
    </ul>
  </div>

  <div class="plain-card">
    <h2>Years</h2>
    <ul>
      {''.join(year_links)}
    </ul>
  </div>
</div>
"""
    INDEX_FILE.write_text(
        page_template(
            title="910CPR Class Reference Index",
            description="Index of public CPR class pages from 2019 forward.",
            body_html=root_body,
            page_type="home",
            page_name="910CPR Class Reference Index",
            canonical_path="/",
        ),
        encoding="utf-8",
    )

    class_lines = "\n".join(
        simple_session_line(s, show_course=True, show_location=True)
        for s in sessions
    )

    classes_body = f"""
<h1>All Listed Classes</h1>
<p class="meta">Public listing sessions from 2019 forward.</p>
<ul>
{class_lines}
</ul>
"""
    CLASSES_INDEX_FILE.write_text(
        page_template(
            title="All Listed Classes | 910CPR",
            description="All listed CPR class sessions from 2019 forward.",
            body_html=classes_body,
            page_type="classes_index",
            page_name="All Listed Classes",
            canonical_path="/classes/index.html",
        ),
        encoding="utf-8",
    )

    courses_index_lines = []
    for course_name, items in sorted(course_groups.items(), key=lambda x: x[0]):
        slug = short_slug(course_name)
        preview = "".join(
            simple_session_line(s, show_course=False, show_location=True)
            for s in items[:10]
        )
        courses_index_lines.append(f"""
<section class="section plain-card">
  <h2><a href="/courses/{slug}.html">{html_escape(course_name)}</a></h2>
  <p class="meta">{len(items)} listed sessions</p>
  <ul>
    {preview}
  </ul>
</section>
""")

    COURSES_INDEX_FILE.write_text(
        page_template(
            title="Course Index | 910CPR",
            description="Course-type index for public CPR classes from 2019 forward.",
            body_html="<h1>Course Index</h1><p class='meta'>Course-type hub pages.</p>" + "".join(courses_index_lines),
            page_type="courses_index",
            page_name="Course Index",
            canonical_path="/courses/index.html",
        ),
        encoding="utf-8",
    )

    for course_name, items in course_groups.items():
        slug = short_slug(course_name)
        blocks = grouped_session_list(items, show_course=False, show_location=True)
        body = f"""
<h1>{html_escape(course_name)}</h1>
<p class="meta">Public listed sessions from 2019 forward.</p>
<p><a href="/courses/index.html">Back to course index</a></p>
{blocks}
"""
        (COURSES_DIR / f"{slug}.html").write_text(
            page_template(
                title=f"{course_name} Classes | 910CPR",
                description=f"Public listed {course_name} sessions from 2019 forward.",
                body_html=body,
                page_type="course",
                page_name=course_name,
                canonical_path=f"/courses/{slug}.html",
            ),
            encoding="utf-8",
        )

    for location_name, items in location_groups.items():
        slug = short_slug(location_name)
        blocks = grouped_session_list(items, show_course=True, show_location=False)
        body = f"""
<h1>Classes in {html_escape(location_name)}</h1>
<p class="meta">Public listed sessions from 2019 forward.</p>
<p><a href="/index.html">Back to main index</a></p>
{blocks}
"""
        (LOCATIONS_DIR / f"{slug}.html").write_text(
            page_template(
                title=f"Classes in {location_name} | 910CPR",
                description=f"Public listed CPR classes in {location_name} from 2019 forward.",
                body_html=body,
                page_type="location",
                page_name=location_name,
                canonical_path=f"/locations/{slug}.html",
            ),
            encoding="utf-8",
        )

    urls = [
        f"{SITE_BASE}/",
        f"{SITE_BASE}/index.html",
        f"{SITE_BASE}/classes/index.html",
        f"{SITE_BASE}/courses/index.html",
    ]

    for s in sessions:
        session_id = str(s.get("session_id", "")).strip()
        if session_id:
            urls.append(f"{SITE_BASE}/classes/{session_id}.html")

    for course_name in course_groups.keys():
        urls.append(f"{SITE_BASE}/courses/{short_slug(course_name)}.html")

    for location_name in location_groups.keys():
        urls.append(f"{SITE_BASE}/locations/{short_slug(location_name)}.html")

    seen = set()
    deduped_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            deduped_urls.append(url)

    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url in deduped_urls:
        sitemap_xml.append("  <url>")
        sitemap_xml.append(f"    <loc>{html_escape(url)}</loc>")
        sitemap_xml.append("  </url>")
    sitemap_xml.append("</urlset>")

    SITEMAP_FILE.write_text("\n".join(sitemap_xml), encoding="utf-8")

    print(f"Built root index: {INDEX_FILE}")
    print(f"Built classes index: {CLASSES_INDEX_FILE}")
    print(f"Built courses index: {COURSES_INDEX_FILE}")
    print(f"Built {len(course_groups)} course pages in: {COURSES_DIR}")
    print(f"Built {len(location_groups)} location pages in: {LOCATIONS_DIR}")
    print(f"Built sitemap: {SITEMAP_FILE}")
    print(f"Included {len(sessions)} public listed sessions from 2019 forward.")


if __name__ == "__main__":
    build()