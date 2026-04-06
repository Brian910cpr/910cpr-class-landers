
from __future__ import annotations

import argparse
import html
import json
import re
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional


SITE_PHONE = "910-395-5193"
SITE_PHONE_HREF = "tel:+19103955193"
ENROLLWARE_SCHEDULE = "https://coastalcprtraining.enrollware.com/site/coastalcprtraining/schedule"
SITE_NAME = "910CPR"


STYLE = """
:root {
  --bg: #eef4f8;
  --card: #ffffff;
  --soft: #f8fbfd;
  --text: #1f2937;
  --muted: #6b7280;
  --accent: #2563eb;
  --accent-dark: #1d4ed8;
  --cta: #ea580c;
  --cta-dark: #c2410c;
  --border: #dbe4ee;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Arial, sans-serif;
  background: linear-gradient(180deg, #f8fbfd 0%, var(--bg) 100%);
  color: var(--text);
}
.site-header,.site-footer { max-width: 1220px; margin: 0 auto; padding: 16px 18px; }
.site-header { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }
.site-brand a { color:var(--text); text-decoration:none; font-weight:800; font-size:24px; }
.site-nav { display:flex; gap:14px; flex-wrap:wrap; }
.site-nav a,.site-footer a { color:var(--accent); text-decoration:none; }
.wrap { max-width:1220px; margin:0 auto; padding:12px 18px 60px; }
.hero {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  margin-bottom: 26px;
}
.hero h1 { margin:0 0 10px 0; font-size:30px; line-height:1.1; }
.hero p { margin:0; font-size:18px; color:var(--muted); }
.section-title { margin:26px 0 14px 0; font-size:20px; }
.grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:18px; }
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 22px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}
.card h2 { margin:0 0 10px 0; font-size:20px; line-height:1.15; }
.muted { color:var(--muted); }
.preview-list { list-style:none; padding:0; margin:16px 0; }
.preview-list li { margin-bottom:10px; padding-bottom:10px; border-bottom:1px dashed var(--border); }
.preview-list li:last-child { border-bottom:0; padding-bottom:0; }
.text-link { color:var(--accent); text-decoration:none; }
.text-link:hover { text-decoration:underline; }
.button { display:inline-block; padding:12px 16px; border-radius:12px; text-decoration:none; font-weight:700; }
.button.secondary { background:#5f6f82; color:white; }
.button.secondary:hover { background:#526170; }
.site-footer { margin-top:24px; color:var(--muted); font-size:14px; }
@media (max-width: 640px) {
  .hero h1 { font-size:26px; }
  .wrap { padding:12px 12px 40px; }
}
"""


JSON_SCRIPT_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>\s*(\{.*?\})\s*</script>',
    re.IGNORECASE | re.DOTALL,
)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
REGISTER_RE = re.compile(r'https://coastalcprtraining\.enrollware\.com/enroll\?id=\d+', re.IGNORECASE)


@dataclass
class ClassPage:
    path: str
    title: str
    start_dt: Optional[datetime]
    location: str
    city: str
    course_slug: str


@dataclass
class CoursePage:
    path: str
    slug: str
    title: str


def read_zip_texts(zip_path: Path, prefix: str) -> Iterable[tuple[str, str]]:
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.endswith(".html") or not name.startswith(prefix):
                continue
            yield name, zf.read(name).decode("utf-8", errors="ignore")


def parse_title(raw_html: str, fallback: str) -> str:
    m = TITLE_RE.search(raw_html)
    if m:
        title = " ".join(re.sub(r"\s+", " ", m.group(1)).split())
        return title.replace(" | 910CPR", "").replace(" Classes", "").strip()
    return fallback


def parse_json_ld(raw_html: str) -> Optional[dict]:
    m = JSON_SCRIPT_RE.search(raw_html)
    if not m:
        return None
    try:
        return json.loads(m.group(1).strip())
    except json.JSONDecodeError:
        return None


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_course_slug(raw_html: str) -> str:
    match = re.search(r'href="([^"]*courses/[^"]+\.html)"', raw_html, re.IGNORECASE)
    if match:
        return Path(match.group(1)).name
    return ""


def parse_class_page(path: str, raw_html: str) -> ClassPage:
    data = parse_json_ld(raw_html) or {}
    title = (data.get("name") or parse_title(raw_html, Path(path).stem)).strip()
    start_dt = parse_datetime(data.get("startDate"))
    location_blob = data.get("location") or {}
    location = location_blob.get("name") if isinstance(location_blob, dict) else ""
    location = location or "Unknown location"
    address = location_blob.get("address") if isinstance(location_blob, dict) else {}
    city = address.get("addressLocality") if isinstance(address, dict) else ""
    if not city:
        city = location.split(";")[0].strip() if ";" in location else location.split(",")[0].strip()
    return ClassPage(
        path=path,
        title=title,
        start_dt=start_dt,
        location=location,
        city=city,
        course_slug=extract_course_slug(raw_html),
    )


def parse_course_page(path: str, raw_html: str) -> CoursePage:
    slug = Path(path).name
    title = parse_title(raw_html, slug)
    return CoursePage(path=path, slug=slug, title=title)


def format_dt(dt: Optional[datetime]) -> str:
    if not dt:
        return "Date unknown"
    return dt.strftime("%B %d, %Y at %I:%M %p")


def build_discovery(classes_zip: Path, courses_zip: Path, output_html: Path) -> None:
    classes = [parse_class_page(path, raw_html) for path, raw_html in read_zip_texts(classes_zip, "classes/")]
    courses = [parse_course_page(path, raw_html) for path, raw_html in read_zip_texts(courses_zip, "courses/")]

    course_title_map = {course.slug: course.title for course in courses}
    classes_by_course: Dict[str, List[ClassPage]] = defaultdict(list)
    classes_by_location: Dict[str, List[ClassPage]] = defaultdict(list)

    for page in classes:
        key = page.course_slug or page.title
        classes_by_course[key].append(page)
        classes_by_location[page.location].append(page)

    course_cards = []
    for key, pages in sorted(classes_by_course.items(), key=lambda item: (-len(item[1]), (course_title_map.get(item[0]) or item[0]).lower()))[:24]:
        pages = sorted([p for p in pages if p.start_dt], key=lambda p: p.start_dt) or pages[:]
        title = course_title_map.get(key) or key.replace(".html", "").replace("-", " ").title()
        items = []
        for page in pages[:6]:
            items.append(
                f'<li><a class="text-link" href="{html.escape(page.path)}">{html.escape(format_dt(page.start_dt))}</a> '
                f'<span class="muted">• {html.escape(page.location)}</span></li>'
            )
        card = f"""
        <section class="card">
          <h2>{html.escape(title)}</h2>
          <div class="muted">{len(pages)} public sessions found</div>
          <ul class="preview-list">{''.join(items)}</ul>
          <p><a class="button secondary" href="{html.escape(key if key.startswith('courses/') else 'courses/' + key)}">View all sessions</a></p>
        </section>
        """
        course_cards.append(card)

    location_cards = []
    for location, pages in sorted(classes_by_location.items(), key=lambda item: (-len(item[1]), item[0].lower()))[:12]:
        pages = sorted([p for p in pages if p.start_dt], key=lambda p: p.start_dt) or pages[:]
        items = []
        for page in pages[:6]:
            items.append(
                f'<li><a class="text-link" href="{html.escape(page.path)}">{html.escape(page.title)}</a> '
                f'<span class="muted">• {html.escape(format_dt(page.start_dt))}</span></li>'
            )
        card = f"""
        <section class="card">
          <h2>{html.escape(location)}</h2>
          <div class="muted">{len(pages)} public sessions found</div>
          <ul class="preview-list">{''.join(items)}</ul>
          <p><a class="button secondary" href="locations/{html.escape(re.sub(r'[^a-z0-9]+', '-', location.lower()).strip('-') or 'location')}.html">View location bucket</a></p>
        </section>
        """
        location_cards.append(card)

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CPR Class Schedule | {SITE_NAME}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Browse upcoming public CPR, BLS, ACLS, PALS, Heartsaver, and first aid classes with {SITE_NAME}.">
<style>{STYLE}</style>
</head>
<body>
<header class="site-header">
  <div class="site-brand">
    <a href="discovery.html">{SITE_NAME}</a>
  </div>
  <nav class="site-nav">
    <a href="discovery.html">Find a Class</a>
    <a href="{SITE_PHONE_HREF}">Call {SITE_PHONE}</a>
    <a href="{ENROLLWARE_SCHEDULE}">Schedule</a>
  </nav>
</header>

<div class="wrap">
  <section class="hero">
    <h1>Find Your CPR Class</h1>
    <p>Browse upcoming public {SITE_NAME} sessions by course type or by location.</p>
  </section>

  <h2 class="section-title">Browse by Course</h2>
  <div class="grid">
    {''.join(course_cards)}
  </div>

  <h2 class="section-title">Browse by Location</h2>
  <div class="grid">
    {''.join(location_cards)}
  </div>
</div>

<footer class="site-footer">
  <p><strong>{SITE_NAME}</strong></p>
  <p>Public CPR, BLS, ACLS, PALS, and first aid classes.</p>
  <p><a href="{SITE_PHONE_HREF}">{SITE_PHONE}</a></p>
</footer>
</body>
</html>
"""
    output_html.write_text(html_out, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a human-readable discovery page from classes.zip and courses.zip")
    parser.add_argument("--classes-zip", default="classes.zip", help="Path to classes.zip")
    parser.add_argument("--courses-zip", default="courses.zip", help="Path to courses.zip")
    parser.add_argument("--output-html", default="discovery.html", help="Output HTML file")
    args = parser.parse_args()

    build_discovery(Path(args.classes_zip), Path(args.courses_zip), Path(args.output_html))
    print(f"Wrote {args.output_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
