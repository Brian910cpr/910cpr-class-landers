
import json
import re
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_REPORT = ROOT / "data" / "raw" / "Class Report.xlsx"
CSS_PATH = "/css/lander.css"
GROUP_URL = "/request_group_session.html"
NEARBY_MAP_PATH = ROOT / "data" / "config" / "nearby_cities.json"

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

def render_page(title: str, body: str, description: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>{title}</title>
<meta name=\"description\" content=\"{description or title}\">
<link rel=\"stylesheet\" href=\"{CSS_PATH}\">
<style>
.tabs {{ display:flex; gap:8px; flex-wrap:wrap; margin:0 0 16px; }}
.tab-btn {{ padding:10px 14px; border-radius:999px; border:1px solid #c7d3ea; background:#fff; cursor:pointer; }}
.tab-btn.active {{ background:#3a5289; color:#fff; border-color:#3a5289; }}
.tab-panel {{ display:none; }}
.tab-panel.active {{ display:block; }}
.table-lite {{ width:100%; border-collapse:collapse; margin-top:12px; }}
.table-lite th,.table-lite td {{ padding:10px; border-bottom:1px solid #dde4f1; text-align:left; }}
.muted {{ color:#5c6c87; }}
.button {{ display:inline-block; padding:10px 14px; border-radius:8px; background:#3a5289; color:#fff; text-decoration:none; }}
.button.secondary {{ background:#eef3fb; color:#25364f; }}
.callout {{ background:#f6f8fc; border:1px solid #dde4f1; border-radius:14px; padding:16px; margin:16px 0; }}
.grid-2 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; }}
.field {{ display:flex; flex-direction:column; gap:6px; margin-bottom:12px; }}
input, select, textarea {{ padding:12px; border:1px solid #cbd5e1; border-radius:8px; font:inherit; }}
textarea {{ min-height:140px; }}
.badge {{ display:inline-block; padding:4px 8px; border-radius:999px; background:#eef3fb; color:#25364f; font-size:12px; margin-right:6px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="page-shell">
    {body}
  </div>
</div>
<script>
document.querySelectorAll('[data-tab-target]').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const scope = btn.closest('[data-tabs]');
    scope.querySelectorAll('.tab-btn').forEach(x => x.classList.remove('active'));
    scope.querySelectorAll('.tab-panel').forEach(x => x.classList.remove('active'));
    btn.classList.add('active');
    scope.querySelector(btn.getAttribute('data-tab-target')).classList.add('active');
    const program = btn.getAttribute('data-program');
    const input = document.querySelector('#program');
    if (input) input.value = program;
  }});
}});
</script>
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
        tr.append(f"<tr><td>{fmt_dt(s.start_at)}</td><td>{s.city}</td><td>{s.cert_body or ''} {s.course_family}</td><td><a class='button secondary' href='{s.registration_link}'>Register</a></td></tr>")
    return "<table class='table-lite'><thead><tr><th>Date / Time</th><th>City</th><th>Program</th><th></th></tr></thead><tbody>" + "".join(tr) + "</tbody></table>"
