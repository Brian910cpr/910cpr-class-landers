import json
import re
import hashlib
from html import unescape
from datetime import datetime
from pathlib import Path

from title_cleaner import normalize_course_title

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "schedule.json"
DOCS_DIR = ROOT / "docs"
INDEX_FILE = DOCS_DIR / "index.html"
SITEMAP_FILE = DOCS_DIR / "sitemap.xml"

SITE_BASE = "https://brian910cpr.github.io/910cpr-class-landers"
GTM_ID = "GTM-PQS8DCBH"

ACCENT = "#2563eb"
ACCENT_DARK = "#1d4ed8"
CTA = "#ea580c"
CTA_DARK = "#c2410c"
BG = "#eef4f8"
CARD = "#ffffff"
TEXT = "#1f2937"
MUTED = "#6b7280"
BORDER = "#dbe4ee"
SOFT = "#f8fbfd"


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

document.addEventListener("click", function(e) {{
  const a = e.target.closest("a");
  if (!a) return;

  const href = a.getAttribute("href") || "";
  const text = (a.textContent || "").trim();

  let eventName = "generic_link_click";

  if (href.includes("/classes/")) eventName = "session_link_click";
  else if (href.includes("/courses/")) eventName = "course_link_click";
  else if (href.includes("/locations/")) eventName = "location_link_click";
  else if (href.includes("enrollware.com/enroll?id=")) eventName = "register_click";
  else if (href.startsWith("tel:")) eventName = "phone_click";

  window.dataLayer.push({{
    event: eventName,
    page_type: "{page_type}",
    page_name: "{safe_page_name}",
    click_text: text,
    link_url: href
  }});
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


def short_slug(text: str, max_len: int = 70) -> str:
    clean = clean_course_name(text).lower()
    clean = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
    digest = hashlib.md5(clean.encode("utf-8")).hexdigest()[:8]

    if len(clean) > max_len:
        clean = clean[:max_len].rstrip("-")

    return f"{clean}-{digest}" if clean else digest


def parse_start_dt(start_value: str):
    raw = str(start_value).strip()

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
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
        return str(start_value).strip(), "", "", None, "Undated"

    display_date = dt.strftime("%B %d, %Y")
    display_time = dt.strftime("%I:%M %p").lstrip("0")
    iso_date = dt.strftime("%Y-%m-%d")
    month_label = dt.strftime("%B %Y")
    return display_date, display_time, iso_date, dt, month_label


def is_public_listing_location(location: str) -> bool:
    return str(location or "").strip().startswith("::")


def clean_location_display(location: str) -> str:
    value = str(location or "").strip()
    if value.startswith("::"):
        value = value[2:].strip()
    return value


def location_label(location: str) -> str:
    return clean_location_display(location) or "Wilmington, NC"


def session_card_html(session: dict, show_course: bool = False) -> str:
    display_date, display_time, _, dt, _ = parse_start(session.get("start", ""))
    register_url = session.get("register_url", "#")
    location = location_label(session.get("location", ""))
    course_name = clean_course_name(session.get("course", "CPR Class"))
    session_id = session.get("session_id")

    if dt:
        month_abbr = dt.strftime("%b").upper()
        day_num = dt.strftime("%d").lstrip("0")
        weekday = dt.strftime("%a")
    else:
        month_abbr = "TBD"
        day_num = "--"
        weekday = ""

    top_line = f'<div class="session-course">{course_name}</div>' if show_course else ""

    return f"""
    <article class="session-card">
      <div class="date-badge">
        <div class="date-month">{month_abbr}</div>
        <div class="date-day">{day_num}</div>
        <div class="date-weekday">{weekday}</div>
      </div>
      <div class="session-main">
        {top_line}
        <div class="session-meta"><strong>{display_time}</strong></div>
        <div class="session-meta">{location}</div>
        <div class="session-links">
          <a class="text-link" href="../classes/{session_id}.html">Details</a>
          <a class="cta-small" href="{register_url}">Register</a>
        </div>
      </div>
    </article>
    """


def grouped_session_blocks(items, show_course=False):
    groups = {}
    for s in items:
        _, _, _, dt, month_label = parse_start(s.get("start", ""))
        key = month_label if month_label else "Undated"
        groups.setdefault(key, []).append(s)

    month_names = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }

    def month_sort_key(label):
        try:
            month, year = label.split()
            return (int(year), month_names[month])
        except Exception:
            return (9999, 99)

    html_parts = []
    for month_label in sorted(groups.keys(), key=month_sort_key):
        cards = "".join(session_card_html(s, show_course=show_course) for s in groups[month_label])
        html_parts.append(f"""
        <section class="month-group">
          <h2 class="month-heading">{month_label}</h2>
          <div class="session-grid">
            {cards}
          </div>
        </section>
        """)
    return "\n".join(html_parts)


BASE_STYLES = f"""
<style>
:root {{
  --bg: {BG};
  --card: {CARD};
  --soft: {SOFT};
  --text: {TEXT};
  --muted: {MUTED};
  --accent: {ACCENT};
  --accent-dark: {ACCENT_DARK};
  --cta: {CTA};
  --cta-dark: {CTA_DARK};
  --border: {BORDER};
}}

* {{
  box-sizing: border-box;
}}

body {{
  margin: 0;
  font-family: Arial, sans-serif;
  background: linear-gradient(180deg, #f8fbfd 0%, var(--bg) 100%);
  color: var(--text);
}}

.site-header,
.site-footer {{
  max-width: 1220px;
  margin: 0 auto;
  padding: 16px 18px;
}}

.site-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}}

.site-brand a {{
  color: var(--text);
  text-decoration: none;
  font-weight: 800;
  font-size: 24px;
}}

.site-nav {{
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}}

.site-nav a,
.site-footer a {{
  color: var(--accent);
  text-decoration: none;
}}

.wrap {{
  max-width: 1220px;
  margin: 0 auto;
  padding: 12px 18px 60px;
}}

.hero {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  margin-bottom: 26px;
}}

.hero h1 {{
  margin: 0 0 10px 0;
  font-size: 30px;
  line-height: 1.1;
}}

.hero p {{
  margin: 0;
  font-size: 18px;
  color: var(--muted);
}}

.section-title {{
  margin: 26px 0 14px 0;
  font-size: 20px;
}}

.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 18px;
}}

.card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 22px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}}

.card h2 {{
  margin: 0 0 10px 0;
  font-size: 20px;
  line-height: 1.15;
}}

.muted {{
  color: var(--muted);
}}

.preview-list {{
  list-style: none;
  padding: 0;
  margin: 16px 0;
}}

.preview-list li {{
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px dashed var(--border);
}}

.preview-list li:last-child {{
  border-bottom: 0;
  padding-bottom: 0;
}}

.text-link {{
  color: var(--accent);
  text-decoration: none;
}}

.text-link:hover {{
  text-decoration: underline;
}}

.button {{
  display: inline-block;
  padding: 12px 16px;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 700;
}}

.button.secondary {{
  background: #5f6f82;
  color: white;
}}

.button.secondary:hover {{
  background: #526170;
}}

.back-link {{
  display: inline-block;
  margin: 2px 0 18px 0;
  color: var(--accent);
  text-decoration: none;
  font-size: 16px;
}}

.back-link:hover {{
  text-decoration: underline;
}}

.month-group {{
  margin-top: 24px;
}}

.month-heading {{
  margin: 0 0 14px 0;
  font-size: 22px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border);
}}

.session-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}}

.session-card {{
  display: flex;
  gap: 14px;
  align-items: stretch;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 14px;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.05);
}}

.date-badge {{
  min-width: 78px;
  border-radius: 16px;
  background: linear-gradient(180deg, var(--accent) 0%, var(--accent-dark) 100%);
  color: white;
  text-align: center;
  padding: 10px 8px;
}}

.date-month {{
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
}}

.date-day {{
  font-size: 28px;
  font-weight: 800;
  line-height: 1.1;
  margin: 4px 0;
}}

.date-weekday {{
  font-size: 12px;
  opacity: 0.95;
}}

.session-main {{
  flex: 1;
}}

.session-course {{
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 8px;
}}

.session-meta {{
  font-size: 15px;
  color: var(--text);
  margin-bottom: 6px;
}}

.session-links {{
  margin-top: 12px;
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}}

.cta-small {{
  display: inline-block;
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--cta);
  color: white;
  text-decoration: none;
  font-weight: 700;
}}

.cta-small:hover {{
  background: var(--cta-dark);
}}

.site-footer {{
  margin-top: 24px;
  color: var(--muted);
  font-size: 14px;
}}

@media (max-width: 640px) {{
  .hero h1 {{
    font-size: 26px;
  }}

  .wrap {{
    padding: 12px 12px 40px;
  }}
}}
</style>
"""

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

all_sessions = data["sessions"]
sessions = [s for s in all_sessions if is_public_listing_location(s.get("location", ""))]
sessions.sort(key=lambda s: str(s.get("start", "")))

course_groups = {}
location_groups = {}

for s in sessions:
    course_name = clean_course_name(s.get("course", "CPR Class"))
    location = location_label(s.get("location", "Wilmington NC"))

    course_groups.setdefault(course_name, []).append(s)
    location_groups.setdefault(location, []).append(s)

COURSES_DIR = DOCS_DIR / "courses"
LOCATIONS_DIR = DOCS_DIR / "locations"
COURSES_DIR.mkdir(parents=True, exist_ok=True)
LOCATIONS_DIR.mkdir(parents=True, exist_ok=True)

course_blocks = []
for course_name, items in sorted(course_groups.items(), key=lambda x: x[0]):
    preview_items = []
    for s in items[:6]:
        display_date, display_time, _, _, _ = parse_start(s.get("start", ""))
        loc = location_label(s.get("location", ""))
        session_id = s.get("session_id")
        preview_items.append(
            f'<li><a class="text-link" href="classes/{session_id}.html">{display_date} at {display_time}</a> <span class="muted">• {loc}</span></li>'
        )

    course_slug = short_slug(course_name)
    course_blocks.append(f"""
    <section class="card">
      <h2>{course_name}</h2>
      <div class="muted">{len(items)} upcoming public sessions</div>
      <ul class="preview-list">
        {''.join(preview_items)}
      </ul>
      <p><a class="button secondary" href="courses/{course_slug}.html">View all sessions</a></p>
    </section>
    """)

location_blocks = []
for location_name, items in sorted(location_groups.items(), key=lambda x: x[0]):
    preview_items = []
    for s in items[:6]:
        display_date, display_time, _, _, _ = parse_start(s.get("start", ""))
        course_name = clean_course_name(s.get("course", "CPR Class"))
        session_id = s.get("session_id")
        preview_items.append(
            f'<li><a class="text-link" href="classes/{session_id}.html">{course_name}</a> <span class="muted">• {display_date} at {display_time}</span></li>'
        )

    location_slug = short_slug(location_name)
    location_blocks.append(f"""
    <section class="card">
      <h2>{location_name}</h2>
      <div class="muted">{len(items)} upcoming public sessions</div>
      <ul class="preview-list">
        {''.join(preview_items)}
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
{render_gtm_head()}
{BASE_STYLES}
</head>
<body>
{render_gtm_body()}

<header class="site-header">
  <div class="site-brand">
    <a href="index.html">910CPR</a>
  </div>
  <nav class="site-nav">
    <a href="index.html">Find a Class</a>
    <a href="tel:+19103955193">Call 910-395-5193</a>
    <a href="https://coastalcprtraining.enrollware.com/site/coastalcprtraining/schedule">Schedule</a>
  </nav>
</header>

<div class="wrap">

  <section class="hero">
    <h1>Find Your CPR Class</h1>
    <p>Browse upcoming public 910CPR sessions by course type or by location.</p>
  </section>

  <h2 class="section-title">Browse by Course</h2>
  <div class="grid">
    {''.join(course_blocks)}
  </div>

  <h2 class="section-title">Browse by Location</h2>
  <div class="grid">
    {''.join(location_blocks)}
  </div>

</div>

<footer class="site-footer">
  <p><strong>910CPR</strong></p>
  <p>Public CPR, BLS, ACLS, PALS, and first aid classes.</p>
  <p><a href="tel:+19103955193">910-395-5193</a></p>
</footer>

{telemetry_script("home", "Find Your CPR Class")}
</body>
</html>
"""

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    f.write(index_html)

for course_name, items in course_groups.items():
    course_slug = short_slug(course_name)
    blocks = grouped_session_blocks(items, show_course=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{course_name} Classes | 910CPR</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Browse upcoming public {course_name} classes with 910CPR.">
{render_gtm_head()}
{BASE_STYLES}
</head>
<body>
{render_gtm_body()}

<header class="site-header">
  <div class="site-brand">
    <a href="../index.html">910CPR</a>
  </div>
  <nav class="site-nav">
    <a href="../index.html">Find a Class</a>
    <a href="tel:+19103955193">Call 910-395-5193</a>
    <a href="https://coastalcprtraining.enrollware.com/site/coastalcprtraining/schedule">Schedule</a>
  </nav>
</header>

<div class="wrap">
  <section class="hero">
    <h1>{course_name}</h1>
    <p>Upcoming public sessions listed by month for faster scanning and booking.</p>
  </section>

  <a class="back-link" href="../index.html">← Back to full schedule</a>

  {blocks}
</div>

<footer class="site-footer">
  <p><strong>910CPR</strong></p>
  <p>Public CPR, BLS, ACLS, PALS, and first aid classes.</p>
  <p><a href="tel:+19103955193">910-395-5193</a></p>
</footer>

{telemetry_script("course", course_name)}
</body>
</html>
"""
    with open(COURSES_DIR / f"{course_slug}.html", "w", encoding="utf-8") as f:
        f.write(html)

for location_name, items in location_groups.items():
    location_slug = short_slug(location_name)
    blocks = grouped_session_blocks(items, show_course=True)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CPR Classes in {location_name} | 910CPR</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Browse upcoming public CPR classes in {location_name} with 910CPR.">
{render_gtm_head()}
{BASE_STYLES}
</head>
<body>
{render_gtm_body()}

<header class="site-header">
  <div class="site-brand">
    <a href="../index.html">910CPR</a>
  </div>
  <nav class="site-nav">
    <a href="../index.html">Find a Class</a>
    <a href="tel:+19103955193">Call 910-395-5193</a>
    <a href="https://coastalcprtraining.enrollware.com/site/coastalcprtraining/schedule">Schedule</a>
  </nav>
</header>

<div class="wrap">
  <section class="hero">
    <h1>CPR Classes in {location_name}</h1>
    <p>Upcoming public sessions grouped by month with quick registration buttons.</p>
  </section>

  <a class="back-link" href="../index.html">← Back to full schedule</a>

  {blocks}
</div>

<footer class="site-footer">
  <p><strong>910CPR</strong></p>
  <p>Public CPR, BLS, ACLS, PALS, and first aid classes.</p>
  <p><a href="tel:+19103955193">910-395-5193</a></p>
</footer>

{telemetry_script("location", location_name)}
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