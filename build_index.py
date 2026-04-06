
from __future__ import annotations

import argparse
import html
import json
import re
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


SITE_TITLE = "910CPR"
SITE_PHONE = "910-395-5193"
SITE_PHONE_HREF = "tel:+19103955193"
ENROLLWARE_SCHEDULE = "https://coastalcprtraining.enrollware.com/site/coastalcprtraining/schedule"


PAGE_STYLE = """
:root{--bg:#eef4f8;--card:#fff;--text:#1f2937;--muted:#6b7280;--accent:#2563eb;--border:#dbe4ee;--cta:#ea580c}
*{box-sizing:border-box}
body{margin:0;font-family:Arial,sans-serif;background:linear-gradient(180deg,#f8fbfd 0%,var(--bg) 100%);color:var(--text)}
.wrap{max-width:1200px;margin:0 auto;padding:20px 18px 50px}
.hero,.card{background:var(--card);border:1px solid var(--border);border-radius:20px;box-shadow:0 8px 24px rgba(15,23,42,.06)}
.hero{padding:26px;margin-bottom:22px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.card{padding:18px}
h1{margin:0 0 8px;font-size:30px}
h2{margin:0 0 12px;font-size:22px}
h3{margin:0 0 10px;font-size:18px}
p,li{line-height:1.45}
.muted{color:var(--muted)}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.button{display:inline-block;padding:11px 15px;background:#5f6f82;color:#fff;border-radius:12px;font-weight:700;text-decoration:none}
.button:hover{background:#526170;text-decoration:none}
.crumbs{font-size:14px;margin:0 0 14px}
.list{margin:0;padding-left:18px}
.small{font-size:14px}
.section{margin-top:24px}
.split{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:800px){.split{grid-template-columns:1fr}h1{font-size:26px}}
"""


JSON_SCRIPT_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>\s*(\{.*?\})\s*</script>',
    re.IGNORECASE | re.DOTALL,
)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
REGISTER_RE = re.compile(r'https://coastalcprtraining\.enrollware\.com/enroll\?id=\d+', re.IGNORECASE)


@dataclass
class ClassPage:
    path: str
    class_id: str
    title: str
    start_dt: Optional[datetime]
    year: Optional[int]
    month_name: str
    location: str
    city: str
    enroll_url: Optional[str]
    topic: str
    sort_key: Tuple[int, str] = field(init=False)

    def __post_init__(self) -> None:
        if self.start_dt:
            self.sort_key = (int(self.start_dt.timestamp()), self.path)
        else:
            self.sort_key = (0, self.path)


@dataclass
class CoursePage:
    path: str
    slug: str
    title: str
    topic: str


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "index"


def html_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    return html.escape(" ".join(value.split()))


def read_zip_texts(zip_path: Path, prefix: str) -> Iterable[Tuple[str, str]]:
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.endswith(".html") or not name.startswith(prefix):
                continue
            yield name, zf.read(name).decode("utf-8", errors="ignore")


def parse_title(raw_html: str, fallback: str) -> str:
    m = TITLE_RE.search(raw_html)
    if m:
        return " ".join(re.sub(r"\s+", " ", m.group(1)).split())
    m = H1_RE.search(raw_html)
    if m:
        return " ".join(re.sub(r"\s+", " ", m.group(1)).split())
    return fallback


def parse_json_ld(raw_html: str) -> Optional[dict]:
    m = JSON_SCRIPT_RE.search(raw_html)
    if not m:
        return None
    blob = m.group(1).strip()
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return None


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    value = value.strip()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def classify_topic(text: str) -> str:
    t = text.lower()

    if "family & friends" in t or "family and friends" in t:
        return "Family & Friends"
    if "stop the bleed" in t:
        return "Stop the Bleed"
    if "aed maintenance" in t or re.search(r"\baed\b", t):
        return "AED / Maintenance"
    if "uscg" in t or "coast guard" in t or "captain first aid" in t:
        return "USCG / Coast Guard"
    if "red cross" in t or t.startswith("arc ") or " arc " in f" {t} ":
        return "Red Cross"
    if "hsi" in t:
        return "HSI"
    if "heartsaver" in t:
        return "Heartsaver"
    if "acls" in t:
        return "ACLS"
    if "pals" in t:
        return "PALS"
    if re.search(r"\bbls\b", t):
        return "BLS"
    if "instructor" in t:
        return "Instructor Courses"
    if "first aid" in t:
        return "First Aid"
    return "Other Courses"


def parse_class_page(path: str, raw_html: str) -> ClassPage:
    class_id = Path(path).stem
    title = parse_title(raw_html, class_id).replace(" | 910CPR", "")
    data = parse_json_ld(raw_html) or {}
    event_name = data.get("name") or title
    start_dt = parse_datetime(data.get("startDate"))
    location_blob = data.get("location") or {}
    if isinstance(location_blob, dict):
        location = location_blob.get("name") or "Unknown location"
        address = location_blob.get("address") or {}
        city = address.get("addressLocality") if isinstance(address, dict) else ""
    else:
        location = "Unknown location"
        city = ""
    if not city:
        city = location.split(";")[0].strip() if ";" in location else location.split(",")[0].strip()

    register_match = REGISTER_RE.search(raw_html)
    enroll_url = register_match.group(0) if register_match else None
    year = start_dt.year if start_dt else None
    month_name = start_dt.strftime("%B") if start_dt else "Unknown"
    topic = classify_topic(event_name)

    return ClassPage(
        path=path,
        class_id=class_id,
        title=event_name,
        start_dt=start_dt,
        year=year,
        month_name=month_name,
        location=location,
        city=city,
        enroll_url=enroll_url,
        topic=topic,
    )


def parse_course_page(path: str, raw_html: str) -> CoursePage:
    slug = Path(path).stem
    title = parse_title(raw_html, slug).replace(" | 910CPR", "").replace(" Classes", "").strip()
    if not title:
        title = slug.replace("-", " ").title()
    topic = classify_topic(f"{slug} {title}")
    return CoursePage(path=path, slug=slug, title=title, topic=topic)


def rel_link(from_page: Path, target: str) -> str:
    base = from_page.parent
    return str(Path(target).relative_to(".") if str(base) == "." else Path(target).relative_to(base)).replace("\\", "/")


def shell_page(title: str, body: str, description: str = "") -> str:
    desc_html = f'<meta name="description" content="{html.escape(description)}">' if description else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | 910CPR Structured Index</title>
<meta name="robots" content="index,follow">
{desc_html}
<style>{PAGE_STYLE}</style>
</head>
<body>
<div class="wrap">
{body}
</div>
</body>
</html>
"""


def card_link(title: str, muted: str, href: str, button: str = "Open") -> str:
    return f'<section class="card"><h3>{html.escape(title)}</h3><p class="muted">{html.escape(muted)}</p><p><a class="button" href="{html.escape(href)}">{html.escape(button)}</a></p></section>'


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_main_index(
    out_dir: Path,
    classes: List[ClassPage],
    courses: List[CoursePage],
    topics_map: Dict[str, List[ClassPage]],
    courses_by_topic: Dict[str, List[CoursePage]],
    years_map: Dict[int, List[ClassPage]],
    location_map: Dict[str, List[ClassPage]],
) -> None:
    topic_cards = []
    for topic in sorted(topics_map):
        topic_slug = safe_slug(topic)
        topic_cards.append(
            card_link(
                topic,
                f"{len(courses_by_topic.get(topic, []))} course files • {len(topics_map[topic])} class pages",
                f"topics/{topic_slug}.html",
                f"Open {topic} hub",
            )
        )

    year_cards = []
    for year in sorted(years_map):
        year_cards.append(card_link(str(year), f"{len(years_map[year])} class pages", f"years/{year}.html", f"Open {year} index"))

    location_cards = []
    for location, pages in sorted(location_map.items(), key=lambda item: (-len(item[1]), item[0].lower()))[:20]:
        location_cards.append(
            card_link(location, f"{len(pages)} class pages", f"locations/{safe_slug(location)}.html", "Open location index")
        )

    top_topic_links = []
    for topic in sorted(topics_map)[:5]:
        top_topic_links.append(f'<li><a href="topics/{safe_slug(topic)}.html">topics/{safe_slug(topic)}.html</a></li>')

    top_year = max(years_map) if years_map else None
    sample_year_link = f'<li><a href="years/{top_year}.html">years/{top_year}.html</a></li>' if top_year else ""
    sample_location = next(iter(sorted(location_map, key=lambda x: (-len(location_map[x]), x.lower()))), None)
    sample_location_link = (
        f'<li><a href="locations/{safe_slug(sample_location)}.html">locations/{safe_slug(sample_location)}.html</a></li>'
        if sample_location else ""
    )

    hero = f"""
<div class="hero"><h1>Structured Index System for Classes and Courses</h1>
<p class="muted">This layer does not change your existing pages. It adds organized hub pages that point into every course file and every class file from the uploaded zips.</p>
<p><strong>Coverage:</strong> {len(courses)} course files and {len(classes)} class pages.</p></div>
<div class="split">
<section class="card"><h2>How this is organized</h2><ul class="list">
<li>Topic hubs such as BLS, ACLS, PALS, Heartsaver, Red Cross, HSI, and USCG</li>
<li>Year buckets for each class year found in the uploaded class files</li>
<li>Location hubs built from the location labels found in the class files</li>
<li>Topic + Year pages so the larger buckets still look intentional and readable</li>
</ul></section>
<section class="card"><h2>Main index paths</h2><ul class="list">{''.join(top_topic_links)}{sample_year_link}{sample_location_link}</ul></section>
</div>
<div class="section"><h2>Browse by topic</h2><div class="grid">{''.join(topic_cards)}</div></div>
<div class="section"><h2>Browse by year</h2><div class="grid">{''.join(year_cards)}</div></div>
<div class="section"><h2>Browse by location</h2><div class="grid">{''.join(location_cards)}</div></div>
<div class="section"><section class="card"><h2>Course file directory</h2><p class="muted">Every course HTML file from the zip is also listed in one place.</p><p><a class="button" href="courses/all-courses.html">Open all course files</a></p></section></div>
"""
    write_text(out_dir / "index.html", shell_page("Structured Index System", hero, "Structured index system for 910CPR classes and courses."))


def build_topic_pages(out_dir: Path, topics_map: Dict[str, List[ClassPage]], courses_by_topic: Dict[str, List[CoursePage]]) -> None:
    for topic, class_pages in topics_map.items():
        topic_slug = safe_slug(topic)
        page_path = out_dir / "topics" / f"{topic_slug}.html"
        class_pages = sorted(class_pages, key=lambda p: p.sort_key)
        year_map: Dict[int, List[ClassPage]] = defaultdict(list)
        location_map: Dict[str, List[ClassPage]] = defaultdict(list)
        for page in class_pages:
            if page.year is not None:
                year_map[page.year].append(page)
            location_map[page.location].append(page)

        year_links = ''.join(
            f'<li><a href="../topics-year/{topic_slug}-{year}.html">{topic} {year}</a> <span class="muted">• {len(pages)} pages</span></li>'
            for year, pages in sorted(year_map.items())
        )

        course_links = ''.join(
            f'<li><a href="../{html.escape(course.path)}">{html.escape(course.title)}</a></li>'
            for course in sorted(courses_by_topic.get(topic, []), key=lambda c: c.title.lower())
        )

        sample_links = ''.join(
            f'<li><a href="../{html.escape(page.path)}">{html.escape(page.title)}</a> <span class="muted">• {page.start_dt.strftime("%B %d, %Y at %I:%M %p") if page.start_dt else "Date unknown"} • {html.escape(page.location)}</span></li>'
            for page in class_pages[:120]
        )

        location_cards = ''.join(
            card_link(loc, f"{len(pages)} class pages", f"../locations/{safe_slug(loc)}.html", "Open location hub")
            for loc, pages in sorted(location_map.items(), key=lambda item: (-len(item[1]), item[0].lower()))[:12]
        )

        body = f"""
<p class="crumbs"><a href="../index.html">Structured Index</a> / {html.escape(topic)}</p>
<div class="hero">
<h1>{html.escape(topic)} Hub</h1>
<p class="muted">{len(courses_by_topic.get(topic, []))} course files • {len(class_pages)} class pages</p>
</div>
<div class="split">
<section class="card"><h2>Topic + Year</h2><ul class="list">{year_links or '<li>No dated class pages found.</li>'}</ul></section>
<section class="card"><h2>Course files in this topic</h2><ul class="list">{course_links or '<li>No course files found.</li>'}</ul></section>
</div>
<div class="section"><h2>Location hubs for {html.escape(topic)}</h2><div class="grid">{location_cards or '<section class="card"><p class="muted">No locations found.</p></section>'}</div></div>
<div class="section"><h2>Sample class links</h2><section class="card"><ul class="list">{sample_links or '<li>No class pages found.</li>'}</ul></section></div>
"""
        write_text(page_path, shell_page(f"{topic} Hub", body, f"{topic} index page for 910CPR class pages."))


def build_topic_year_pages(out_dir: Path, topics_map: Dict[str, List[ClassPage]]) -> None:
    grouped: Dict[Tuple[str, int], List[ClassPage]] = defaultdict(list)
    for topic, pages in topics_map.items():
        for page in pages:
            if page.year is not None:
                grouped[(topic, page.year)].append(page)

    for (topic, year), pages in grouped.items():
        topic_slug = safe_slug(topic)
        page_path = out_dir / "topics-year" / f"{topic_slug}-{year}.html"
        pages = sorted(pages, key=lambda p: p.sort_key)
        month_map: Dict[str, List[ClassPage]] = defaultdict(list)
        for page in pages:
            month_map[page.month_name].append(page)

        month_sections = []
        for month_name, month_pages in sorted(month_map.items(), key=lambda kv: datetime.strptime(kv[0], "%B").month if kv[0] != "Unknown" else 99):
            items = ''.join(
                f'<li><a href="../{html.escape(p.path)}">{html.escape(p.title)}</a> <span class="muted">• {p.start_dt.strftime("%B %d, %Y at %I:%M %p") if p.start_dt else "Date unknown"} • {html.escape(p.location)}</span></li>'
                for p in month_pages[:300]
            )
            month_sections.append(f'<section class="card"><h3>{html.escape(month_name)}</h3><ul class="list">{items}</ul></section>')

        body = f"""
<p class="crumbs"><a href="../index.html">Structured Index</a> / <a href="../topics/{topic_slug}.html">{html.escape(topic)}</a> / {year}</p>
<div class="hero"><h1>{html.escape(topic)} {year}</h1><p class="muted">{len(pages)} class pages</p></div>
<div class="grid">{''.join(month_sections) if month_sections else '<section class="card"><p class="muted">No class pages found.</p></section>'}</div>
"""
        write_text(page_path, shell_page(f"{topic} {year}", body, f"{topic} {year} class page index for 910CPR."))


def build_year_pages(out_dir: Path, years_map: Dict[int, List[ClassPage]]) -> None:
    for year, pages in sorted(years_map.items()):
        pages = sorted(pages, key=lambda p: p.sort_key)
        topic_map: Dict[str, List[ClassPage]] = defaultdict(list)
        for page in pages:
            topic_map[page.topic].append(page)

        cards = ''.join(
            card_link(topic, f"{len(topic_pages)} class pages", f"../topics-year/{safe_slug(topic)}-{year}.html", f"Open {topic} {year}")
            for topic, topic_pages in sorted(topic_map.items())
        )

        body = f"""
<p class="crumbs"><a href="../index.html">Structured Index</a> / {year}</p>
<div class="hero"><h1>{year} Class Index</h1><p class="muted">{len(pages)} total class pages</p></div>
<div class="section"><h2>Browse {year} by topic</h2><div class="grid">{cards}</div></div>
"""
        write_text(out_dir / "years" / f"{year}.html", shell_page(f"{year} Class Index", body, f"Class page buckets for {year}."))


def build_location_pages(out_dir: Path, location_map: Dict[str, List[ClassPage]]) -> None:
    for location, pages in sorted(location_map.items(), key=lambda item: (-len(item[1]), item[0].lower())):
        pages = sorted(pages, key=lambda p: p.sort_key)
        topic_map: Dict[str, List[ClassPage]] = defaultdict(list)
        for page in pages:
            topic_map[page.topic].append(page)

        topic_links = ''.join(
            f'<li>{html.escape(topic)} <span class="muted">• {len(topic_pages)} pages</span></li>'
            for topic, topic_pages in sorted(topic_map.items(), key=lambda item: (-len(item[1]), item[0].lower()))
        )

        class_links = ''.join(
            f'<li><a href="../{html.escape(page.path)}">{html.escape(page.title)}</a> <span class="muted">• {page.start_dt.strftime("%B %d, %Y at %I:%M %p") if page.start_dt else "Date unknown"}</span></li>'
            for page in pages[:250]
        )

        body = f"""
<p class="crumbs"><a href="../index.html">Structured Index</a> / {html.escape(location)}</p>
<div class="hero"><h1>{html.escape(location)}</h1><p class="muted">{len(pages)} class pages</p></div>
<div class="split">
<section class="card"><h2>Topics at this location</h2><ul class="list">{topic_links}</ul></section>
<section class="card"><h2>Sample class links</h2><ul class="list">{class_links}</ul></section>
</div>
"""
        write_text(out_dir / "locations" / f"{safe_slug(location)}.html", shell_page(f"{location} Index", body, f"Class pages for {location}."))


def build_all_courses_page(out_dir: Path, courses: List[CoursePage]) -> None:
    grouped: Dict[str, List[CoursePage]] = defaultdict(list)
    for course in courses:
        grouped[course.topic].append(course)

    sections = []
    for topic, topic_courses in sorted(grouped.items()):
        items = ''.join(f'<li><a href="../{html.escape(course.path)}">{html.escape(course.title)}</a></li>' for course in sorted(topic_courses, key=lambda c: c.title.lower()))
        sections.append(f'<section class="card"><h3>{html.escape(topic)}</h3><ul class="list">{items}</ul></section>')

    body = f"""
<p class="crumbs"><a href="../index.html">Structured Index</a> / All Courses</p>
<div class="hero"><h1>All Course Files</h1><p class="muted">{len(courses)} course HTML files</p></div>
<div class="grid">{''.join(sections)}</div>
"""
    write_text(out_dir / "courses" / "all-courses.html", shell_page("All Course Files", body, "All 910CPR course files found in the uploaded zip."))


def build_structure_txt(out_dir: Path, courses: List[CoursePage], classes: List[ClassPage]) -> None:
    years = sorted({page.year for page in classes if page.year is not None})
    summary = [
        "Structured Index System",
        f"Course files: {len(courses)}",
        f"Class files: {len(classes)}",
        f"Years: {', '.join(str(y) for y in years)}",
        "",
        "Top-level outputs:",
        "- index.html",
        "- topics/*.html",
        "- topics-year/*.html",
        "- years/*.html",
        "- locations/*.html",
        "- courses/all-courses.html",
    ]
    write_text(out_dir / "STRUCTURE.txt", "\n".join(summary) + "\n")


def build_from_zips(classes_zip: Path, courses_zip: Path, out_dir: Path) -> None:
    classes = [parse_class_page(path, raw_html) for path, raw_html in read_zip_texts(classes_zip, "classes/")]
    courses = [parse_course_page(path, raw_html) for path, raw_html in read_zip_texts(courses_zip, "courses/")]

    topics_map: Dict[str, List[ClassPage]] = defaultdict(list)
    courses_by_topic: Dict[str, List[CoursePage]] = defaultdict(list)
    years_map: Dict[int, List[ClassPage]] = defaultdict(list)
    location_map: Dict[str, List[ClassPage]] = defaultdict(list)

    for page in classes:
        topics_map[page.topic].append(page)
        if page.year is not None:
            years_map[page.year].append(page)
        location_map[page.location].append(page)

    for course in courses:
        courses_by_topic[course.topic].append(course)

    out_dir.mkdir(parents=True, exist_ok=True)
    build_main_index(out_dir, classes, courses, topics_map, courses_by_topic, years_map, location_map)
    build_topic_pages(out_dir, topics_map, courses_by_topic)
    build_topic_year_pages(out_dir, topics_map)
    build_year_pages(out_dir, years_map)
    build_location_pages(out_dir, location_map)
    build_all_courses_page(out_dir, courses)
    build_structure_txt(out_dir, courses, classes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build structured SEO index pages from classes.zip and courses.zip")
    parser.add_argument("--classes-zip", default="classes.zip", help="Path to classes.zip")
    parser.add_argument("--courses-zip", default="courses.zip", help="Path to courses.zip")
    parser.add_argument("--output-dir", default="structured-index", help="Directory for generated HTML")
    args = parser.parse_args()

    build_from_zips(Path(args.classes_zip), Path(args.courses_zip), Path(args.output_dir))
    print(f"Wrote structured index pages to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
