#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build 910CPR landers (course hubs + session pages) from a single Enrollware schedule HTML dump.

v1.3:
- Schedule links now point directly to Enrollware:
  https://coastalcprtraining.enrollware.com/schedule#ct######
- Force absolute enroll URLs if Enrollware returns relative /enroll?id=#####
- Keeps view-source parsing + Windows-safe slugs from earlier hotfixes.
"""

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict
from html import unescape

from bs4 import BeautifulSoup, NavigableString
from dateutil import parser as dtparser

# ------------------------------
# Config
# ------------------------------
ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com"

# ------------------------------
# Slug + path helpers
# ------------------------------
RESERVED_WIN = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}

def _normalize(text: str) -> str:
    text = re.sub(r"[’'“”]", "", text or "")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-")
    text = re.sub(r"-+", "-", text)
    return text.lower()

def _clamp_slug(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s or "item"
    cut = s[:max_len]
    hy = cut.rfind("-")
    if hy >= max_len // 2:
        cut = cut[:hy]
    return cut.strip("-") or "item"

def _avoid_reserved(s: str) -> str:
    return (s + "-x") if s in RESERVED_WIN else s

def slugify(text: str, max_len: int = 60) -> str:
    s = _normalize(text)
    s = _clamp_slug(s, max_len)
    s = _avoid_reserved(s)
    return s or "item"

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def clean_text(html_text: str) -> str:
    return re.sub(r"\s+", " ", html_text or "").strip()

def read_schedule_html(path: Path) -> str:
    """
    Supports syntax-highlighted 'view-source' HTML (table cells td.line-content with escaped tags).
    If detected, reconstruct original HTML by concatenating line-content text and unescaping.
    """
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if ('class="line-content"' in raw) and ('class="html-tag"' in raw):
        soup0 = BeautifulSoup(raw, "html.parser")
        chunks = [td.get_text("", strip=False) for td in soup0.select("td.line-content")]
        return unescape("".join(chunks))
    return raw

# ------------------------------
# Data Models
# ------------------------------
@dataclass
class Course:
    ct_id: str
    title: str
    slug: str

@dataclass
class Session:
    enroll_id: str
    enroll_url: str
    course_ct_id: str
    course_title: str
    course_slug: str
    start_iso: str
    start_display: str
    location_label: str
    location_slug: str

# ------------------------------
# Parsing functions
# ------------------------------
def parse_locations(soup: BeautifulSoup) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    sel = soup.find("select", id=re.compile(r"locationList$"))
    if not sel:
        return out
    for opt in sel.find_all("option"):
        value = (opt.get("value") or "").strip()
        label = clean_text(opt.get_text(" "))
        if label:
            out.append({"value": value, "label": label, "slug": slugify(label, 60)})
    return out

def parse_courses_and_sessions(soup: BeautifulSoup) -> (List[Course], List[Session]):
    courses: Dict[str, Course] = {}
    sessions: List[Session] = []

    for panel in soup.find_all("div", class_="enrpanel"):
        name_anchor = panel.find("a", attrs={"name": re.compile(r"^ct\d+")})
        if not name_anchor:
            continue
        ct_id = name_anchor.get("name", "").strip()

        title_el = panel.find("span", class_="enrpanel-title")
        title_full = clean_text(title_el.get_text(" ")) if title_el else ct_id
        cslug = slugify(title_full, 60)

        if ct_id not in courses:
            courses[ct_id] = Course(ct_id=ct_id, title=title_full, slug=cslug)

        body = panel.find("div", class_="enrpanel-body")
        if not body:
            continue
        ul = body.find("ul", class_="enrclass-list")
        if not ul:
            continue

        for li in ul.find_all("li"):
            a = li.find("a", href=True)
            if not a:
                continue
            href = a["href"]
            # Force absolute Enrollware URL if relative
            if href.startswith("/"):
                href = ENROLLWARE_BASE + href
            if "enroll?id=" not in href:
                continue

            dt_text = ""
            loc_label = ""
            for child in a.children:
                if isinstance(child, NavigableString):
                    dt_text += str(child)
                elif getattr(child, "name", None) == "span":
                    loc_label = clean_text(child.get_text(" "))
            dt_text = clean_text(dt_text)

            try:
                start_dt = dtparser.parse(dt_text, fuzzy=True)
                start_iso = start_dt.strftime("%Y-%m-%dT%H:%M")
            except Exception:
                start_iso = ""

            m = re.search(r"enroll\?id=(\d+)", href)
            if not m:
                continue
            enroll_id = m.group(1)

            lslug = slugify(loc_label or "unknown-location", 60)

            sessions.append(
                Session(
                    enroll_id=enroll_id,
                    enroll_url=href,
                    course_ct_id=ct_id,
                    course_title=title_full,
                    course_slug=cslug,
                    start_iso=start_iso,
                    start_display=dt_text,
                    location_label=loc_label,
                    location_slug=lslug,
                )
            )

    return list(courses.values()), sessions

# ------------------------------
# HTML templates
# ------------------------------
COURSE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | 910CPR</title>
  <meta name="description" content="Upcoming sessions for {title} with 910CPR. Hands-on, reliable scheduling in Wilmington, Burgaw, Jacksonville, and onsite.">
  <style>
    body {{ margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: linear-gradient(180deg, #ffffff 0%, #f2f8ff 100%); color:#0b2239; }}
    .wrap {{ max-width: 960px; margin: 0 auto; padding: 24px; }}
    .hero {{ display:flex; gap:18px; align-items:center; }}
    .hero img.logo {{ width:56px; height:56px; border-radius:50%; }}
    h1 {{ margin:0; font-size: 28px; }}
    .card {{ background:#fff; border:1px solid #e6eef7; border-radius:16px; padding:16px 18px; margin:16px 0; box-shadow: 0 1px 4px rgba(0,0,0,.05); }}
    .btn {{ display:inline-block; padding:10px 14px; border-radius:999px; border:1px solid #0b62d6; text-decoration:none; }}
    .btn.primary {{ background:#0b62d6; color:#fff; border-color:#0b62d6; }}
    .muted {{ color:#466079; font-size: 14px; }}
    ul.sessions {{ list-style:none; padding:0; margin:0; }}
    ul.sessions li {{ display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #eef4fb; gap: 10px; }}
    .alt {{ margin-top: 8px; display:block; }}
  </style>
  <script type="application/ld+json">{json_ld}</script>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <img class="logo" src="/images/910cpr_round.png" alt="910CPR logo" />
      <div>
        <h1>{title}</h1>
        <div class="muted">Top 5 upcoming sessions. Need another time? Use the schedule below.</div>
      </div>
    </div>

    <div class="card">
      <ul class="sessions">
        {session_items}
      </ul>
    </div>

    <div class="card">
      <strong>Did you need a different time?</strong>
      <div class="alt"><a class="btn" href="{schedule_url}">{title} — full schedule</a></div>
    </div>
  </div>
</body>
</html>
"""

SESSION_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{course_title} — {start_display} | 910CPR</title>
  <meta name="description" content="Register for {course_title} on {start_display} at {location_label}.">
  <style>
    body {{ margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: linear-gradient(180deg, #ffffff 0%, #f2f8ff 100%); color:#0b2239; }}
    .wrap {{ max-width: 860px; margin: 0 auto; padding: 24px; }}
    h1 {{ margin: 0 0 8px 0; font-size: 28px; }}
    .card {{ background:#fff; border:1px solid #e6eef7; border-radius:16px; padding:18px; margin:16px 0; box-shadow: 0 1px 4px rgba(0,0,0,.05); }}
    .btn {{ display:inline-block; padding:12px 16px; border-radius:999px; border:1px solid #0b62d6; text-decoration:none; }}
    .btn.primary {{ background:#0b62d6; color:#fff; border-color:#0b62d6; }}
    .muted {{ color:#466079; }}
  </style>
  <script type="application/ld+json">{json_ld}</script>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>{course_title}</h1>
      <div class="muted">{start_display} • {location_label}</div>
      <div style="margin-top:14px;">
        <a class="btn primary" href="{enroll_url}">Register Now</a>
        <a class="btn" href="{site_root}/class/{course_slug}/">See other times</a>
      </div>
    </div>

    <div class="card">
      <strong>Note:</strong>
      <div class="muted">All registrations are prepaid. eCards issued as fast as possible, typically same day or next business day.</div>
    </div>
  </div>
</body>
</html>
"""

# ------------------------------
# Build functions
# ------------------------------
def build_json_ld_course(course: Course, sessions: List[Session], site_root: str) -> str:
    events = []
    for s in sessions[:5]:
        events.append({
            "@type": "Event",
            "name": f"{course.title}",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "startDate": s.start_iso,
            "location": {"@type": "Place", "name": s.location_label},
            "url": s.enroll_url,
        })
    data = {
        "@context": "https://schema.org",
        "@type": "Course",
        "name": course.title,
        "provider": {"@type": "Organization", "name": "910CPR", "url": site_root},
        "hasCourseInstance": events,
    }
    return json.dumps(data, ensure_ascii=False)

def build_json_ld_session(s: Session, site_root: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": s.course_title,
        "startDate": s.start_iso,
        "location": {"@type": "Place", "name": s.location_label},
        "organizer": {"@type": "Organization", "name": "910CPR", "url": site_root},
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "eventStatus": "https://schema.org/EventScheduled",
        "url": s.enroll_url,
    }
    return json.dumps(data, ensure_ascii=False)

def write_json(path: Path, data) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def render_course_page(course: Course, sessions: List[Session], out_dir: Path, site_root: str) -> None:
    ensure_dir(out_dir)
    def parse_iso(s: Session) -> dt.datetime:
        try:
            return dt.datetime.fromisoformat(s.start_iso)
        except Exception:
            return dt.datetime.max
    ordered = sorted(sessions, key=parse_iso)[:5]

    items = []
    for s in ordered:
        items.append(
            f"<li><div>{s.start_display} • {s.location_label}</div><div><a class=\"btn primary\" href=\"{s.enroll_url}\">Register</a></div></li>"
        )

    json_ld = build_json_ld_course(course, ordered, site_root)
    schedule_url = f"{ENROLLWARE_BASE}/schedule#{course.ct_id}"
    html = COURSE_TEMPLATE.format(
        title=course.title,
        session_items="\n".join(items) or "<li>No upcoming sessions listed here — call us to schedule.</li>",
        schedule_url=schedule_url,
        json_ld=json_ld,
    )
    (out_dir / "index.html").write_text(html, encoding="utf-8")

def render_session_page(s: Session, out_dir: Path, site_root: str) -> None:
    ensure_dir(out_dir)
    json_ld = build_json_ld_session(s, site_root)
    html = SESSION_TEMPLATE.format(
        course_title=s.course_title,
        start_display=s.start_display,
        location_label=s.location_label,
        enroll_url=s.enroll_url,
        course_slug=s.course_slug,
        site_root=site_root,
        json_ld=json_ld,
    )
    (out_dir / "index.html").write_text(html, encoding="utf-8")

def build_pages(courses: List[Course], sessions: List[Session], out_root: Path, site_root: str) -> None:
    write_json(out_root / "data" / "courses.json", [asdict(c) for c in courses])
    write_json(out_root / "data" / "sessions.json", [asdict(s) for s in sessions])

    by_course: Dict[str, List[Session]] = {}
    for s in sessions:
        by_course.setdefault(s.course_ct_id, []).append(s)

    # Course hubs
    for c in courses:
        course_dir = out_root / "class" / c.slug
        render_course_page(c, by_course.get(c.ct_id, []), course_dir, site_root)

    # Session pages
    for s in sessions:
        dt_part = s.start_iso.replace(":", "-").replace("T", "_") if s.start_iso else "unknown"
        course_part = _clamp_slug(s.course_slug, 40)
        loc_part = _clamp_slug(s.location_slug, 40)
        sess_dir_name = f"{dt_part}_{course_part}_{loc_part}_{s.enroll_id}"
        sess_dir = out_root / "session" / sess_dir_name
        render_session_page(s, sess_dir, site_root)

# ------------------------------
# Main
# ------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to Enrollware schedule HTML (view-source dump or raw)")
    ap.add_argument("--out-root", required=True, help="Output docs root (e.g., 910cpr-class-landers/docs)")
    ap.add_argument("--site-root", default="https://www.910cpr.com", help="Public site root for links")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.is_file():
        src = Path(args.input)

    html_text = read_schedule_html(src)
    soup = BeautifulSoup(html_text, "html.parser")

    locations = parse_locations(soup)
    courses, sessions = parse_courses_and_sessions(soup)

    out_root = Path(args.out_root)
    write_json(out_root / "data" / "locations.json", locations)

    build_pages(courses, sessions, out_root, args.site_root)

    print(f"Parsed courses: {len(courses)} | sessions: {len(sessions)} | locations: {len(locations)}")

if __name__ == "__main__":
    sys.exit(main())
