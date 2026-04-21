import json
import re
from pathlib import Path
from html import unescape
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]

DOCS_DIR = ROOT / "docs"
CLASSES_DIR = DOCS_DIR / "classes"
COURSES_DIR = DOCS_DIR / "courses"
LOCATIONS_DIR = DOCS_DIR / "locations"

INDEX_FILE = DOCS_DIR / "index.html"
CLASSES_INDEX_FILE = CLASSES_DIR / "index.html"
COURSES_INDEX_FILE = COURSES_DIR / "index.html"
SITEMAP_FILE = DOCS_DIR / "sitemap.xml"

SITE_BASE = "https://www.910cpr.com"
GTM_ID = "GTM-PQS8DCBH"
PHONE_DISPLAY = "910-395-5193"
PHONE_LINK = "tel:+19103955193"
ENROLLWARE_SCHEDULE_URL = "https://coastalcprtraining.enrollware.com/site/coastalcprtraining/schedule"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def render_gtm_head() -> str:
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


def render_gtm_body() -> str:
    if not GTM_ID:
        return ""
    return f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""


def telemetry_script(page_type: str, page_name: str) -> str:
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


def html_escape(text: str) -> str:
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def strip_html(text: str) -> str:
    if text is None:
        return ""
    text = unescape(str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def short_slug(text: str, max_len: int = 80) -> str:
    clean = strip_html(text).lower()
    clean = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
    if len(clean) > max_len:
        clean = clean[:max_len].rstrip("-")
    return clean or "untitled"


def extract_first(pattern: str, text: str, flags=0, default: str = "") -> str:
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else default


def extract_meta(content: str, name: str) -> str:
    pattern = rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\'](.*?)["\']'
    return unescape(extract_first(pattern, content, flags=re.I | re.S))


def extract_link_href(content: str, rel_value: str) -> str:
    pattern = rf'<link[^>]+rel=["\']{re.escape(rel_value)}["\'][^>]+href=["\'](.*?)["\']'
    return unescape(extract_first(pattern, content, flags=re.I | re.S))


def extract_tag_text(content: str, tag: str) -> str:
    pattern = rf"<{tag}[^>]*>(.*?)</{tag}>"
    return strip_html(extract_first(pattern, content, flags=re.I | re.S))


def parse_page_context(content: str) -> dict:
    """
    Extract pageContext from:
      const pageContext = { ... };
    and convert it to JSON-ish.
    """
    m = re.search(r"const\s+pageContext\s*=\s*\{(.*?)\};", content, flags=re.S)
    if not m:
        return {}

    obj_text = "{" + m.group(1) + "}"

    # Quote bare keys: page_type: -> "page_type":
    obj_text = re.sub(r'([{\s,])([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', obj_text)

    # Remove trailing commas before } or ]
    obj_text = re.sub(r",(\s*[}\]])", r"\1", obj_text)

    try:
        return json.loads(obj_text)
    except json.JSONDecodeError:
        return {}


def parse_json_ld_event(content: str) -> dict:
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        content,
        flags=re.I | re.S,
    )

    for block in blocks:
        raw = block.strip()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict) and parsed.get("@type") == "Event":
            return parsed

        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and item.get("@type") == "Event":
                    return item

    return {}


def clean_location_name(location: str) -> str:
    value = strip_html(location)
    if value.startswith("::"):
        value = value[2:].strip()
    return value or "Unknown Location"


def page_template(title: str, description: str, body_html: str, page_type: str, page_name: str, canonical_path: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html_escape(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{html_escape(description)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{SITE_BASE}{canonical_path}">
{render_gtm_head()}
<style>
body {{
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
  color: #111827;
  background: #ffffff;
  line-height: 1.45;
}}
.wrap {{
  max-width: 1180px;
  margin: 0 auto;
  padding: 16px;
}}
header, footer {{
  border-bottom: 1px solid #e5e7eb;
}}
footer {{
  border-top: 1px solid #e5e7eb;
  border-bottom: 0;
  margin-top: 30px;
}}
h1, h2, h3 {{
  line-height: 1.2;
}}
a {{
  color: #1d4ed8;
}}
ul {{
  margin-top: 10px;
}}
.meta {{
  color: #4b5563;
}}
.small {{
  font-size: 14px;
  color: #4b5563;
}}
.nav a {{
  margin-right: 12px;
}}
.section {{
  margin-top: 28px;
}}
.columns {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
}}
.plain-card {{
  border: 1px solid #e5e7eb;
  padding: 14px;
  border-radius: 8px;
}}
</style>
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


# ---------------------------------------------------------------------
# Class page parsing
# ---------------------------------------------------------------------

def parse_class_page(path: Path) -> dict | None:
    content = path.read_text(encoding="utf-8", errors="ignore")

    canonical = extract_link_href(content, "canonical")
    title = extract_tag_text(content, "title")
    meta_description = extract_meta(content, "description")
    h1 = extract_tag_text(content, "h1")
    page_context = parse_page_context(content)
    event = parse_json_ld_event(content)

    # Ignore obvious non-class pages
    if not canonical or "/classes/" not in canonical:
        return None

    session_id = str(page_context.get("session_id", "")).strip()
    if not session_id:
        m = re.search(r"/classes/(\d+)\.html$", canonical)
        if m:
            session_id = m.group(1)

    if not session_id:
        return None

    course_name = (
        str(page_context.get("course_name", "")).strip()
        or str(event.get("name", "")).strip()
        or h1
        or title
    )

    # Prefer pageContext location, then JSON-LD Event location
    location_name = str(page_context.get("location_name", "")).strip()
    if not location_name:
        location_name = (
            event.get("location", {}).get("name", "")
            if isinstance(event.get("location"), dict)
            else ""
        )
    location_name = clean_location_name(location_name)

    register_url = str(page_context.get("register_url", "")).strip()
    if not register_url:
        offers = event.get("offers", {})
        if isinstance(offers, dict):
            register_url = str(offers.get("url", "")).strip()

    schedule_url = str(page_context.get("schedule_url", "")).strip()

    # Use visible meta values when possible
    display_date = extract_first(
        r'<div class="meta-label">Date</div>\s*<div class="meta-value">(.*?)</div>',
        content,
        flags=re.I | re.S,
    )
    display_date = strip_html(display_date)

    display_time = extract_first(
        r'<div class="meta-label">Time</div>\s*<div class="meta-value">(.*?)</div>',
        content,
        flags=re.I | re.S,
    )
    display_time = strip_html(display_time)

    if not display_date and event.get("startDate"):
        display_date = str(event.get("startDate"))

    course_slug = str(page_context.get("course_slug", "")).strip()
    if not course_slug and course_name:
        course_slug = short_slug(course_name)

    local_path = f"/classes/{session_id}.html"

    return {
        "session_id": session_id,
        "course_name": course_name or "CPR Class",
        "course_slug": course_slug,
        "location_name": location_name or "Unknown Location",
        "title": title or course_name or f"Class {session_id}",
        "meta_description": meta_description or "",
        "display_date": display_date or "",
        "display_time": display_time or "",
        "canonical": canonical,
        "local_path": local_path,
        "register_url": register_url,
        "schedule_url": schedule_url,
        "source_file": str(path),
    }


def build():
    if not CLASSES_DIR.exists():
        raise FileNotFoundError(f"Missing classes directory: {CLASSES_DIR}")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    CLASSES_DIR.mkdir(parents=True, exist_ok=True)
    COURSES_DIR.mkdir(parents=True, exist_ok=True)
    LOCATIONS_DIR.mkdir(parents=True, exist_ok=True)

    class_files = sorted(
        p for p in CLASSES_DIR.glob("*.html")
        if p.name.lower() != "index.html"
    )

    sessions = []
    for path in class_files:
        parsed = parse_class_page(path)
        if parsed and parsed.get("course_name", "").strip().lower() != "course":
            sessions.append(parsed)

    # Sort by best available date text, then session id
    sessions.sort(key=lambda s: (s.get("display_date", ""), s.get("display_time", ""), s.get("session_id", "")))

    course_groups: dict[str, list[dict]] = defaultdict(list)
    location_groups: dict[str, list[dict]] = defaultdict(list)

    for s in sessions:
        course_groups[s["course_name"]].append(s)
        location_groups[s["location_name"]].append(s)

    # -----------------------------------------------------------------
    # Root index
    # -----------------------------------------------------------------
    course_links = []
    for course_name, items in sorted(course_groups.items(), key=lambda x: x[0].lower()):
        slug = short_slug(course_name)
        course_links.append(
            f'<li><a href="/courses/{slug}.html">{html_escape(course_name)}</a> ({len(items)})</li>'
        )

    location_links = []
    for location_name, items in sorted(location_groups.items(), key=lambda x: x[0].lower()):
        slug = short_slug(location_name)
        location_links.append(
            f'<li><a href="/locations/{slug}.html">{html_escape(location_name)}</a> ({len(items)})</li>'
        )

    root_body = f"""
<h1>910CPR Class Reference Index</h1>
<p class="meta">This index is built from the actual HTML class pages found in <code>/docs/classes/</code>.</p>

<div class="section">
  <p><a href="/classes/index.html">Browse all class pages</a></p>
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
    <h2>Stats</h2>
    <ul>
      <li>Total class pages found: {len(sessions)}</li>
      <li>Course groups: {len(course_groups)}</li>
      <li>Location groups: {len(location_groups)}</li>
    </ul>
  </div>
</div>
"""
    INDEX_FILE.write_text(
        page_template(
            title="910CPR Class Reference Index",
            description="Class index built from actual generated class pages.",
            body_html=root_body,
            page_type="home",
            page_name="910CPR Class Reference Index",
            canonical_path="/",
        ),
        encoding="utf-8",
    )

    # -----------------------------------------------------------------
    # Classes index
    # -----------------------------------------------------------------
    class_lines = []
    for s in sessions:
        left_parts = [s["course_name"]]
        if s["display_date"]:
            left_parts.append(s["display_date"])
        if s["display_time"]:
            left_parts.append(s["display_time"])
        if s["location_name"]:
            left_parts.append(s["location_name"])

        line = " | ".join(html_escape(x) for x in left_parts if x)
        detail_link = f'<a href="{s["local_path"]}">Details</a>'
        register_link = f' | <a href="{s["register_url"]}">Register</a>' if s["register_url"] else ""

        class_lines.append(f"<li>{line} | {detail_link}{register_link}</li>")

    CLASSES_INDEX_FILE.write_text(
        page_template(
            title="All Class Pages | 910CPR",
            description="Index of all generated class pages.",
            body_html=f"""
<h1>All Class Pages</h1>
<p class="meta">Built directly from files in <code>/docs/classes/</code>.</p>
<ul>
{''.join(class_lines)}
</ul>
""",
            page_type="classes_index",
            page_name="All Class Pages",
            canonical_path="/classes/index.html",
        ),
        encoding="utf-8",
    )

    # -----------------------------------------------------------------
    # Courses index
    # -----------------------------------------------------------------
    course_sections = []
    for course_name, items in sorted(course_groups.items(), key=lambda x: x[0].lower()):
        slug = short_slug(course_name)

        preview = []
        for s in items[:10]:
            bits = []
            if s["display_date"]:
                bits.append(s["display_date"])
            if s["display_time"]:
                bits.append(s["display_time"])
            if s["location_name"]:
                bits.append(s["location_name"])

            line = " | ".join(html_escape(x) for x in bits if x)
            preview.append(f'<li>{line} | <a href="{s["local_path"]}">Details</a></li>')

        course_sections.append(f"""
<section class="section plain-card">
  <h2><a href="/courses/{slug}.html">{html_escape(course_name)}</a></h2>
  <p class="meta">{len(items)} class pages</p>
  <ul>
    {''.join(preview)}
  </ul>
</section>
""")

    COURSES_INDEX_FILE.write_text(
        page_template(
            title="Course Index | 910CPR",
            description="Course-type index built from actual class pages.",
            body_html=f"""
<h1>Course Index</h1>
<p class="meta">Grouped from the generated class pages in <code>/docs/classes/</code>.</p>
{''.join(course_sections)}
""",
            page_type="courses_index",
            page_name="Course Index",
            canonical_path="/courses/index.html",
        ),
        encoding="utf-8",
    )

    # -----------------------------------------------------------------
    # Course pages
    # -----------------------------------------------------------------
    for course_name, items in course_groups.items():
        slug = short_slug(course_name)

        lines = []
        for s in items:
            bits = []
            if s["display_date"]:
                bits.append(s["display_date"])
            if s["display_time"]:
                bits.append(s["display_time"])
            if s["location_name"]:
                bits.append(s["location_name"])

            line = " | ".join(html_escape(x) for x in bits if x)
            detail_link = f'<a href="{s["local_path"]}">Details</a>'
            register_link = f' | <a href="{s["register_url"]}">Register</a>' if s["register_url"] else ""

            lines.append(f"<li>{line} | {detail_link}{register_link}</li>")

        (COURSES_DIR / f"{slug}.html").write_text(
            page_template(
                title=f"{course_name} Classes | 910CPR",
                description=f"Index of generated class pages for {course_name}.",
                body_html=f"""
<h1>{html_escape(course_name)}</h1>
<p class="meta">Grouped from the generated class pages.</p>
<p><a href="/courses/index.html">Back to course index</a></p>
<ul>
{''.join(lines)}
</ul>
""",
                page_type="course",
                page_name=course_name,
                canonical_path=f"/courses/{slug}.html",
            ),
            encoding="utf-8",
        )

    # -----------------------------------------------------------------
    # Location pages
    # -----------------------------------------------------------------
    for location_name, items in location_groups.items():
        slug = short_slug(location_name)

        lines = []
        for s in items:
            bits = [s["course_name"]]
            if s["display_date"]:
                bits.append(s["display_date"])
            if s["display_time"]:
                bits.append(s["display_time"])

            line = " | ".join(html_escape(x) for x in bits if x)
            detail_link = f'<a href="{s["local_path"]}">Details</a>'
            register_link = f' | <a href="{s["register_url"]}">Register</a>' if s["register_url"] else ""

            lines.append(f"<li>{line} | {detail_link}{register_link}</li>")

        (LOCATIONS_DIR / f"{slug}.html").write_text(
            page_template(
                title=f"Classes in {location_name} | 910CPR",
                description=f"Index of generated class pages in {location_name}.",
                body_html=f"""
<h1>Classes in {html_escape(location_name)}</h1>
<p class="meta">Grouped from the generated class pages.</p>
<p><a href="/index.html">Back to main index</a></p>
<ul>
{''.join(lines)}
</ul>
""",
                page_type="location",
                page_name=location_name,
                canonical_path=f"/locations/{slug}.html",
            ),
            encoding="utf-8",
        )

    # -----------------------------------------------------------------
    # Sitemap
    # -----------------------------------------------------------------
    urls = [
        f"{SITE_BASE}/",
        f"{SITE_BASE}/index.html",
        f"{SITE_BASE}/classes/index.html",
        f"{SITE_BASE}/courses/index.html",
    ]

    for s in sessions:
        urls.append(f"{SITE_BASE}{s['local_path']}")

    for course_name in course_groups.keys():
        urls.append(f"{SITE_BASE}/courses/{short_slug(course_name)}.html")

    for location_name in location_groups.keys():
        urls.append(f"{SITE_BASE}/locations/{short_slug(location_name)}.html")

    # Deduplicate while preserving order
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

    print(f"Scanned class pages: {len(class_files)}")
    print(f"Parsed valid class pages: {len(sessions)}")
    print(f"Built root index: {INDEX_FILE}")
    print(f"Built classes index: {CLASSES_INDEX_FILE}")
    print(f"Built courses index: {COURSES_INDEX_FILE}")
    print(f"Built {len(course_groups)} course pages in: {COURSES_DIR}")
    print(f"Built {len(location_groups)} location pages in: {LOCATIONS_DIR}")
    print(f"Built sitemap: {SITEMAP_FILE}")


if __name__ == "__main__":
    build()
