
import json
import re
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_REPORT = ROOT / "data" / "Class Report.xlsx"
CSS_PATH = "/css/lander.css"
GROUP_URL = "/request_group_session.html"
NEARBY_MAP_PATH = ROOT / "data" / "config" / "nearby_cities.json"
SITE_BASE = "https://www.910cpr.com"

COURSE_FAMILY_RULES = [
    ("ACLS", ["ACLS"]),
    ("PALS", ["PALS"]),
    ("USCG Elementary First Aid | CPR", ["USCG", "ELEMENTARY FIRST AID"]),
    ("Heartsaver / First Aid / CPR / AED", ["HEARTSAVER", "FIRST AID", "CPR AED", "CPR/AED"]),
    ("BLS", ["BLS"]),
]

CORE_CITIES = {"Wilmington", "Jacksonville", "Myrtle Beach", "Raleigh", "Holly Ridge"}

@dataclass
class SessionRecord:
    session_id: str
    course_html: str
    course_name: str
    course_family: str
    course_id: str
    cert_body: str
    body_course_title: str
    delivery_code: str
    price: str
    start_at: datetime
    end_at: datetime | None
    location_raw: str
    city: str
    instructor: str
    students: int
    seats: int
    registration_link: str
    is_public: bool
    is_regional_private: bool

def strip_html(text: str) -> str:
    text = unescape(str(text or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def parse_img_metadata(course_html: str) -> dict:
    html = str(course_html or "")
    meta = {}
    for attr in ("alt", "title", "name", "longdesc"):
        m = re.search(fr'{attr}="([^"]*)"', html, flags=re.I)
        if m:
            meta[attr] = m.group(1)
    longdesc = meta.get("longdesc", "")
    for piece in longdesc.split("|"):
        if ":" in piece:
            k, v = piece.split(":", 1)
            meta[k] = v
    return meta

def normalize_course_family(text: str) -> str:
    t = strip_html(text).upper()
    for family, needles in COURSE_FAMILY_RULES:
        if any(n in t for n in needles):
            return family
    return strip_html(text)

def extract_city(location: str) -> str:
    raw = strip_html(location)
    if raw.startswith("::"):
        raw = raw[2:].strip()
    if ";" in raw:
        left = raw.split(";")[0].strip()
        if left:
            return left
    # prefer explicit city before comma
    m = re.search(r'([A-Za-z .\'-]+),\s*[A-Z]{2}\b', raw)
    if m:
        return m.group(1).strip().title()
    # catch city after colon
    m = re.search(r':\s*([A-Za-z .\'-]+?)(?:\s*/|\s*$)', raw)
    if m:
        candidate = m.group(1).strip().title()
        if candidate and len(candidate) > 2:
            return candidate
    # common city hints
    for city in ["Wilmington","Jacksonville","Holly Ridge","Myrtle Beach","Raleigh","Beaufort","Morehead City","Burgaw","Leland","Whiteville","Supply","Longs","Ocean Isle","Hampstead"]:
        if city.lower() in raw.lower():
            return city
    return raw.strip().title() if raw.strip() else "Wilmington"

def load_nearby_map() -> dict:
    if NEARBY_MAP_PATH.exists():
        return json.loads(NEARBY_MAP_PATH.read_text(encoding="utf-8"))
    return {}

def load_sessions(path: Path | None = None) -> list[SessionRecord]:
    report = path or RAW_REPORT
    df = pd.read_excel(report)
    sessions = []
    for _, row in df.iterrows():
        course_html = str(row.get("Course", "") or "")
        md = parse_img_metadata(course_html)
        reg = str(row.get("Registration Link", "") or "").strip()
        if "id=" in reg:
            session_id = reg.split("id=")[-1].strip()
        else:
            session_id = str(row.get("ID", "") or "").strip()
        start_at = pd.to_datetime(row.get("Start Date / Time"), errors="coerce")
        end_at = pd.to_datetime(row.get("End Date / Time"), errors="coerce")
        seats = int(row.get("Seats") or 0)
        students = int(row.get("Students") or 0)
        loc = str(row.get("Location", "") or "")
        city = extract_city(loc)
        is_public = loc.strip().startswith("::") and seats < 100 and bool(reg)
        sessions.append(SessionRecord(
            session_id=session_id,
            course_html=course_html,
            course_name=strip_html(course_html),
            course_family=normalize_course_family(course_html),
            course_id=str(md.get("r") or md.get("name") or row.get("ID") or "").strip(),
            cert_body=str(md.get("cb") or md.get("alt") or "").strip(),
            body_course_title=str(md.get("title") or "").strip(),
            delivery_code=str(md.get("d") or "").strip(),
            price=str(md.get("p") or "").strip(),
            start_at=start_at.to_pydatetime() if not pd.isna(start_at) else None,
            end_at=end_at.to_pydatetime() if not pd.isna(end_at) else None,
            location_raw=loc,
            city=city,
            instructor=str(row.get("Instructor", "") or "").strip(),
            students=students,
            seats=seats,
            registration_link=reg,
            is_public=is_public,
            is_regional_private=(not is_public and seats >= 100),
        ))
    return sessions

def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", strip_html(text).lower()).strip("-")
    return text or "page"

def session_sort_key(s: SessionRecord):
    return s.start_at or datetime.max

def upcoming_public_sessions(sessions: list[SessionRecord], *, city=None, family=None, now=None) -> list[SessionRecord]:
    now = now or datetime.now()
    filtered = []
    for s in sessions:
        if not s.is_public:
            continue
        if s.start_at and s.start_at < now:
            continue
        if city and s.city != city:
            continue
        if family and s.course_family != family:
            continue
        filtered.append(s)
    return sorted(filtered, key=session_sort_key)

def nearby_public_sessions(sessions: list[SessionRecord], city: str, *, family=None, now=None):
    nearby_map = load_nearby_map()
    nearby = set(nearby_map.get(city, []))
    return [s for s in upcoming_public_sessions(sessions, family=family, now=now) if s.city in nearby]

def regional_private_sessions(sessions: list[SessionRecord], city: str, *, family=None, now=None):
    nearby_map = load_nearby_map()
    nearby = set(nearby_map.get(city, [])) | {city}
    now = now or datetime.now()
    out = []
    for s in sessions:
        if family and s.course_family != family:
            continue
        if s.city not in nearby:
            continue
        if not s.is_regional_private:
            continue
        if s.start_at and s.start_at < now:
            continue
        out.append(s)
    return sorted(out, key=session_sort_key)

def render_page(title: str, body: str, description: str = "", canonical_path: str = "") -> str:
    canonical = f"{SITE_BASE}{canonical_path}" if canonical_path else ""
    canonical_html = f'<link rel="canonical" href="{canonical}">' if canonical else ""
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>{title}</title>
<meta name=\"description\" content=\"{description or title}\">
<meta name=\"robots\" content=\"index,follow\">
{canonical_html}
<link rel=\"stylesheet\" href=\"{CSS_PATH}\">
</head>
<body>
<div class="wrap">
  <div class="page-shell">
    {body}
  </div>
</div>
<script src="/assets/hub-ui.js"></script>
<script src="/assets/session-expiry.js"></script>
</body>
</html>"""

def fmt_dt(dt):
    if not dt:
        return "TBD"
    return dt.strftime("%b %d, %Y %I:%M %p").replace(" 0", " ")

def session_rows(rows: list[SessionRecord], limit=20):
    rows = rows[:limit]
    if not rows:
        return '<p class="muted">No upcoming public sessions are listed right now.</p>'
    tr = []
    for s in rows:
        start_iso = s.start_at.isoformat() if s.start_at else ""
        end_iso = s.end_at.isoformat() if s.end_at else ""
        session_url = f"/classes/{s.session_id}.html#ForwardToEnrollware" if s.session_id else (s.registration_link or "#")
        tr.append(
            f"<tr class='js-session-item' data-session-id='{s.session_id}' data-start='{start_iso}' data-end='{end_iso}' data-session-start='{start_iso}'>"
            f"<td>{fmt_dt(s.start_at)}</td><td>{s.city}</td><td>{s.cert_body or ''} {s.course_family}</td><td><a class='button secondary' href='{session_url}' data-original-href='{s.registration_link}'>Book Seat</a></td></tr>"
        )
    return "<table class='table-lite'><thead><tr><th>Date / Time</th><th>City</th><th>Program</th><th></th></tr></thead><tbody data-session-container>" + "".join(tr) + "</tbody></table>"


def guideline_topic_block(family: str) -> str:
    text = strip_html(family).lower()
    if not any(term in text for term in ["heartsaver", "first aid", "cpr", "aed", "bls", "pals", "acls", "uscg"]):
        return ""
    if "acls" in text or "pals" in text:
        points = [
            "Scenario-based practice keeps recognition, assessment, ventilation, CPR quality, defibrillation, and team communication connected to real clinical response.",
            "Stroke content should be framed as a time-sensitive emergency, with FAST recognition and EMS activation included where layperson wording appears.",
        ]
    elif "bls" in text:
        points = [
            "BLS pages should preserve high-quality CPR, AED use, ventilations, choking response, and team-based response language.",
            "Opioid-related respiratory arrest needs CPR with breaths when breathing is absent or abnormal. Hands-only CPR is not always enough, and naloxone should be used when available.",
        ]
    else:
        points = [
            "First aid topics now emphasize practical recognition and early EMS activation, not just certification wording.",
            "Choking response should say adults and children receive 5 back blows and 5 abdominal thrusts, while infants receive 5 back blows and 5 chest thrusts.",
            "Updated first aid language includes naloxone access, seizures, asthma spacer support, stroke FAST recognition, severe heat illness cooling, safe rewarming, burns, eye injuries, ticks, stings, poison ivy/oak, and pulse oximetry limitations.",
        ]
    items = "".join(f"<li>{p}</li>" for p in points)
    return f"<section class='section-box'><h2>Current CPR and First Aid Focus</h2><ul>{items}</ul></section>"
