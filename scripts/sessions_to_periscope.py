#!/usr/bin/env python3

import csv, json, re, sys
from pathlib import Path
from datetime import datetime

# Paths
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA_OUT = DOCS / "data"
PERISCOPE_JSON = DOCS / "periscope_full.json"
SESSIONS_HTML = DOCS / "sessions" / "index.html"
REPORT = DATA_OUT / "session-parse-report.txt"

# ---------- helpers ----------
MONTHS = {m: i for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], start=1
)}

def normkey(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def coalesce(row, *keys):
    for k in keys:
        if k in row:
            v = row.get(k, "")
            if v is not None and str(v).strip():
                return str(v).strip()
    return ""

def guess_course_family(text: str) -> str:
    t = (text or "").upper()
    if "ACLS" in t: return "ACLS"
    if "PALS" in t: return "PALS"
    if "HEARTSAVER" in t or "FIRST AID" in t or " HSI" in t or t == "FA": return "FA"
    if "BLS" in t or "BASIC LIFE" in t: return "BLS"
    return "BLS"

def parse_date_any(s: str) -> str:
    if not s: return ""
    s = s.strip()
    for dfmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try: return datetime.strptime(s, dfmt).strftime("%Y-%m-%d")
        except Exception: pass
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", s)
    if m:
        mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if yy < 100: yy += 2000
        return f"{yy:04d}-{mm:02d}-{dd:02d}"
    return ""

def parse_time_any(s: str) -> str:
    if not s: return ""
    s = s.strip().lower().replace(" ", "")
    m = re.match(r"^(\d{1,2})(\d{2})?(am|pm)?$", s)
    if m:
        hh = int(m.group(1)); mm = int(m.group(2) or 0); ap = m.group(3)
        if ap == "pm" and hh < 12: hh += 12
        if ap == "am" and hh == 12: hh = 0
        return f"{hh:02d}:{mm:02d}"
    for tfmt in ("%H:%M", "%I:%M%p", "%I%M%p", "%I%p"):
        try: return datetime.strptime(s, tfmt).strftime("%H:%M")
        except Exception: pass
    return ""

def parse_js_date(s: str) -> str:
    """
    Accepts: 'Sat Sep 20 2025 17:00:00 GMT-0400 (Eastern Daylight Time)'
             'Mon Sep 22 2025 09:00:00 GMT-0400'
    Returns: 'YYYY-MM-DDTHH:MM'
    """
    if not s: return ""
    s = s.strip()
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s)  # drop trailing ' (Eastern Daylight Time)'
    for fmt in ("%a %b %d %Y %H:%M:%S GMT%z", "%a %b %d %Y %H:%M GMT%z"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%dT%H:%M")
        except Exception:
            pass
    m = re.match(
        r"^\w{3}\s+([A-Za-z]{3})\s+(\d{1,2})\s+(\d{4})\s+(\d{1,2}):(\d{2})(?::\d{2})?\s+GMT[+-]\d{4}$",
        s
    )
    if m:
        mon = MONTHS.get(m.group(1).title(), 0)
        day = int(m.group(2)); year = int(m.group(3))
        hh = int(m.group(4)); mm = int(m.group(5))
        if mon:
            return f"{year:04d}-{mon:02d}-{day:02d}T{hh:02d}:{mm:02d}"
    return ""

def label_for(start_iso: str, city: str) -> str:
    try:
        dt = datetime.strptime(start_iso[:16], "%Y-%m-%dT%H:%M")
        hm = dt.strftime("%I:%M%p").lstrip("0").lower().replace(":00","").replace("am","a").replace("pm","p")
        return f"{dt.strftime('%b %d')}, {hm} - {city}"
    except Exception:
        return f"{start_iso} - {city}" if start_iso else city

# ---------- parsing core ----------
def parse_start_from_headers(row, keys_norm):
    # ISO-ish or combined datetime fields
    for k in ("start","startiso","startat","starttimeiso","startdatetime","datetime","sessionstart"):
        if k in keys_norm:
            val = row[keys_norm[k]]
            if not val: continue
            val = str(val).strip().replace(" ", "T")
            m = re.match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?)", val)
            if m:
                d = parse_date_any(m.group(1)); t = parse_time_any(m.group(2))
                if d and t: return f"{d}T{t}"
            m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})", val)
            if m: return m.group(1)
    # HOVN-style date
    if "date" in keys_norm:
        jsd = row[keys_norm["date"]]
        iso = parse_js_date(jsd)
        if iso: return iso
    # split date+time fields
    date_keys = [k for k in ("date","sessiondate","startdate") if k in keys_norm]
    time_keys = [k for k in ("time","starttime") if k in keys_norm]
    if date_keys and time_keys:
        d = parse_date_any(row[keys_norm[date_keys[0]]])
        t = parse_time_any(row[keys_norm[time_keys[0]]])
        if d and t: return f"{d}T{t}"
    return ""

def parse_start_fallback_scan(row):
    vals = [str(v or "") for v in row.values()]
    joined = " | ".join(vals)
    m = re.search(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}).{0,5}(\d{4}).{0,5}(\d{1,2}):(\d{2})",
        joined, re.I
    )
    if m:
        mon = MONTHS.get(m.group(1).title(), 0)
        if mon:
            return f"{int(m.group(3)):04d}-{mon:02d}-{int(m.group(2)):02d}T{int(m.group(4)):02d}:{int(m.group(5)):02d}"
    m = re.search(r"(\d{4}-\d{2}-\d{2})[ T](\d{1,2}:\d{2})", joined)
    if m: return f"{m.group(1)}T{m.group(2)}"
    m = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4}).{0,3}(\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?)", joined)
    if m:
        d = parse_date_any(m.group(1)); t = parse_time_any(m.group(2))
        if d and t: return f"{d}T{t}"
    return ""

def row_to_item(row: dict, issues: list):
    keys_norm = { normkey(k): k for k in row.keys() }
    start = parse_start_from_headers(row, keys_norm)
    if not start:
        start = parse_start_fallback_scan(row)
        if not start:
            issues.append({"row": row, "reason": "missing or unparsable date/time"})
            start = ""  # filtered later

    # city (support dotted header)
    city = coalesce(row, "location.city", "Location.City", "city", "City", "location_city", "LocationCity", "location")
    url  = coalesce(row, "url", "enroll_url", "EnrollURL", "link", "Link", "hovn_url")
    title = coalesce(row, "course", "Course", "title", "Title")
    certification = coalesce(row, "certification", "Certification")
    agency = coalesce(row, "agency", "Agency")

    fam = coalesce(row, "course_family") or guess_course_family(title or certification or url)

    item = {
        "course_family": fam,
        "start": start,
        "city": city,
        "url": url,
        "title": title,
        "certification": certification,
        "agency": agency
    }
    item["label"] = label_for(start, city) if start else (city or "")
    return item

# ---------- CSV loader ----------
def load_csv(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        rdr = csv.DictReader(f)
        rows = list(rdr)
        return rows, rdr.fieldnames or []

# ---------- group pages ----------
def write_group_page(slug: str, title: str):
    out = DOCS / "courses" / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    html = f"""<!doctype html><meta charset="utf-8">
<title>{title} | 910CPR</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 24px; }}
  h1 {{ margin-bottom: 8px; }}
  .sub {{ color:#555; margin-bottom: 20px; }}
  .filters {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin: 10px 0 20px; }}
  input, select {{ padding:8px; font-size:14px; }}
  ul {{ list-style:none; padding:0; margin:0; }}
  li {{ padding:14px 0; border-bottom:1px solid #eee; display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; }}
  .meta {{ color:#666; font-size:14px; }}
  .cta {{ text-decoration:none; padding:8px 12px; border:1px solid #222; border-radius:8px; }}
</style>
<body>
  <a href="/" style="text-decoration:none">&larr; Home</a>
  <h1>{title}</h1>
  <div class="sub">Live schedule pulled from HOVN. Filter by city or search.</div>

  <div class="filters">
    <label>City:
      <select id="citySel"><option value="">All</option></select>
    </label>
    <input id="q" type="search" placeholder="Search title/certification…">
  </div>

  <ul id="list"></ul>

<script>
const GROUP = "{slug}";
const FEED = "/periscope_full.json";

function inGroup(it) {{
  const fam = (it.course_family||"").toUpperCase();
  const title = ((it.title||"") + " " + (it.certification||"")).toUpperCase();
  if (GROUP === "medical") return ["BLS","ACLS","PALS"].includes(fam);
  if (GROUP === "workplaces") return fam === "FA" && !/PEDIATRIC/.test(title);
  if (GROUP === "parents") return /PEDIATRIC|INFANT|FAMILY/.test(title) || (fam==="FA" && /PEDIATRIC/.test(title));
  return true;
}}
function parseISO(s) {{ try {{ return new Date(s.replace('T',' ') + ':00'); }} catch(e) {{ return null; }} }}
function fmtDate(d) {{
  return d.toLocaleString(undefined, {{ month:'short', day:'2-digit' }});
}}
function fmtTime(d) {{
  let h=d.getHours(), m=d.getMinutes();
  const ap = h>=12?'p':'a'; h = h%12||12;
  return m?`${{h}}:${{String(m).padStart(2,'0')}}${{ap}}`:`${{h}}${{ap}}`;
}}

function uniqueCities(items) {{
  const set = new Set(items.map(x => (x.city||'').trim()).filter(Boolean));
  return Array.from(set).sort((a,b)=>a.localeCompare(b));
}}

function applyFilters(items) {{
  const city = new URLSearchParams(location.search).get('city') || document.getElementById('citySel').value || '';
  const q = (document.getElementById('q').value||'').trim().toLowerCase();
  return items.filter(it => {{
    if (city && String(it.city||'').toLowerCase() !== city.toLowerCase()) return false;
    if (q) {{
      const blob = (it.title||'') + ' ' + (it.certification||'') + ' ' + (it.city||'');
      if (!blob.toLowerCase().includes(q)) return false;
    }}
    return true;
  }});
}}

function render(items) {{
  const ul = document.getElementById('list');
  ul.innerHTML = '';
  for (const it of items) {{
    const d = parseISO(it.start);
    const when = d ? `${{fmtDate(d)}}, ${{fmtTime(d)}}` : it.start;
    const meta = `${{it.certification||it.title||it.course_family||''}} — ${{it_
