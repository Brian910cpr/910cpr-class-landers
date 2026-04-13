import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "schedule.json"

DOCS_DIR = ROOT / "docs"
CLASSES_DIR = DOCS_DIR / "classes"
COURSES_DIR = DOCS_DIR / "courses"

SITE_BASE = "https://www.910cpr.com"


def parse_date(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except:
        return None


def build():
    if not DATA_FILE.exists():
        print("Missing schedule.json")
        return

    DOCS_DIR.mkdir(exist_ok=True)
    CLASSES_DIR.mkdir(exist_ok=True)
    COURSES_DIR.mkdir(exist_ok=True)

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    sessions = data.get("sessions", [])

    print(f"Loaded {len(sessions)} sessions")

    # -------------------------------------------------
    # CLASSES INDEX (ALL sessions, no filtering)
    # -------------------------------------------------
    class_lines = []

    for s in sessions:
        sid = str(s.get("session_id", ""))
        course = s.get("course_name", "CPR Class")
        date = s.get("start_at", "")
        loc = s.get("location_display", "")
        reg = s.get("registration_url", "")

        line = f'<li>{course} | {date} | {loc} | <a href="/classes/{sid}.html">Details</a>'

        if reg:
            line += f' | <a href="{reg}">Register</a>'

        line += "</li>"
        class_lines.append(line)

    (CLASSES_DIR / "index.html").write_text(f"""
<h1>All CPR Classes</h1>
<ul>
{chr(10).join(class_lines)}
</ul>
""", encoding="utf-8")

    # -------------------------------------------------
    # COURSE GROUPING
    # -------------------------------------------------
    courses = {}

    for s in sessions:
        course = s.get("course_name", "CPR Class")
        courses.setdefault(course, []).append(s)

    # -------------------------------------------------
    # COURSE PAGES
    # -------------------------------------------------
    for course, items in courses.items():
        slug = course.lower().replace(" ", "-")

        lines = []
        for s in items:
            sid = s.get("session_id", "")
            date = s.get("start_at", "")
            loc = s.get("location_display", "")

            lines.append(
                f'<li>{date} | {loc} | <a href="/classes/{sid}.html">Details</a></li>'
            )

        (COURSES_DIR / f"{slug}.html").write_text(f"""
<h1>{course}</h1>
<ul>
{chr(10).join(lines)}
</ul>
""", encoding="utf-8")

    # -------------------------------------------------
    # SITEMAP
    # -------------------------------------------------
    urls = []

    urls.append(f"{SITE_BASE}/")
    urls.append(f"{SITE_BASE}/classes/index.html")

    for s in sessions:
        sid = str(s.get("session_id", ""))
        if sid:
            urls.append(f"{SITE_BASE}/classes/{sid}.html")

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for u in urls:
        sitemap.append("<url>")
        sitemap.append(f"<loc>{u}</loc>")
        sitemap.append("</url>")

    sitemap.append("</urlset>")

    (DOCS_DIR / "sitemap.xml").write_text("\n".join(sitemap), encoding="utf-8")

    print(f"Built classes index with {len(class_lines)} entries")
    print(f"Built {len(courses)} course pages")
    print("Sitemap built")


if __name__ == "__main__":
    build()