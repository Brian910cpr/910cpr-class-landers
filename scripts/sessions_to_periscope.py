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
def normkey(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def coalesce(row, *keys):
    for k in keys:
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
    if "ACLS" in t.lower(): return "ACLS"
    if "pals" in t.lower(): return "PALS"
    if "first" in t.lower() or "aid" in t.lower() or "hsi" in t.lower(): return "FA"
    return "BLS"

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})")
TIME_RE = re.compile(r"(\d{1,2}:\d{2}\s*[ap]m|\d{1,2}\s*[ap]m|\d{1,2}:\d{2}|\d{3,4}\s*[ap]m)", re.I)

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

def label_for(start_iso: str, city: str) -> str:
    try:
        dt = datetime.strptime(start_iso[:16], "%Y-%m-%dT%H:%M")
        hm = dt.strftime("%I:%M%p").lstrip("0").lower().replace(":00","").replace("am","a").replace("pm","p")
        return f"{dt.strftime('%b %d')}, {hm} - {city}"
    except Exception:
        return f"{start_iso} - {city}" if start_iso else city

# ---------- parsing core ----------
def parse_start_from_headers(row, keys_norm):
    # direct ISO-ish
    for k in ("start","startiso","startat","starttimeiso","startdatetime","datetime","sessionstart"):
        if k in keys_norm:
            val = row[keys_norm[k]]
            if not val: continue
            val = str(val).strip().replace(" ", "T")
            m = re.match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?)", val)
            if m:
                d = parse_date_any(m.group(1)); t = parse_time_any(m.group(2))
                if d and t: return f"{d}T{t}"
            # try “YYYY-MM-DDTHH:MM” already
            m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})", val)
            if m: return m.group(1)

    # split date+time style headers
    date_keys = [k for k in ("date","sessiondate","startdate") if k in keys_norm]
    time_keys = [k for k in ("time","starttime") if k in keys_norm]
    if date_keys and time_keys:
        d = parse_date_any(row[keys_norm[date_keys[0]]])
        t = parse_time_any(row[keys_norm[time_keys[0]]])
        if d and t: return f"{d}T{t}"
    return ""

def parse_start_fallback_scan(row):
    """Scan all columns for a date and a time anywhere."""
    vals = [str(v or "") for v in row.values()]
    joined = " | ".join(vals)

    # combined "date time" fragments
    m = re.search(r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})[ T,]+(\d{1,2}(:\d{2})?\s*[AaPp]?[Mm]?)", joined)
    if m:
        d = parse_date_any(m.group(1))
        t = parse_time_any(m.group(2))
        if d and t: return f"{d}T{t}"

    # separate date and time anywhere
    md = DATE_RE.search(joined); mt = TIME_RE.search(joined)
    if md and mt:
        d = parse_date_any(md.group(1))
        t = parse_time_any(mt.group(1))
        if d and t: return f"{d}T{t}"
    return ""

def row_to_item(row: dict, issues: list):
    # map normalized keys to original names
    keys_norm = { normkey(k): k for k in row.keys() }

    start = parse_start_from_headers(row, keys_norm)
    if not start:
        start = parse_start_fallback_scan(row)
        if not start:
            issues.append({"row": row, "reason": "missing or unparsable date/time"})
            start = ""  # will get filtered later

    city = coalesce(row, "city", "City", "location_city", "LocationCity", "location")
    url  = coalesce(row, "url", "enroll_url", "EnrollURL", "link", "Link", "hovn_url")
    course = coalesce(row, "course_family", "course", "Course", "title", "Title", "CourseName")
    fam = coalesce(row, "course_family") or guess_course_family(course or url)
    item = {"course_family": fam, "start": start, "city": city, "url": url}
    item["label"] = label_for(start, city) if start else (city or "")
    return item

# ---------- CSV loader with delimiter sniffing ----------
def load_csv(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except Exception:
            class Dialect(csv.Dialect):
                delimiter = ","
                quotechar = '"'
                escapechar = None
                doublequote = True
                skipinitialspace = True
                lineterminator = "\n"
                quoting = csv.QUOTE_MINIMAL
            dialect = Dialect()
        rdr = csv.DictReader(f, dialect=dialect)
        rows = list(rdr)
        return rows, getattr(dialect, "delimiter", ","), rdr.fieldnames or []

# ---------- main ----------
def main():
    # locate CSV
    candidates = []
    if len(sys.argv) > 1:
        candidates = [Path(sys.argv[1])]
    candidates += [ROOT / "data" / "sessions.csv", ROOT / "sessions.csv"]
    src = next((p for p in candidates if p.exists()), None)
    if not src:
        print("[sessions_to_periscope] CSV not found. Looked for:")
        for c in candidates: print(" -", c)
        sys.exit(1)

    rows, delim, headers = load_csv(src)
    issues = []
    items = [row_to_item(r, issues) for r in rows if r]
    items = [x for x in items if x.get("start")]

    # sort by start
    def key_iso(x):
        s = x.get("start","")
        try: return datetime.strptime(s[:16], "%Y-%m-%dT%H:%M")
        except Exception: return datetime.max
    items.sort(key=key_iso)

    DOCS.mkdir(parents=True, exist_ok=True)
    DATA_OUT.mkdir(parents=True, exist_ok=True)

    PERISCOPE_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    times = [x["start"] for x in items]
    (DATA_OUT / "session-times.json").write_text(json.dumps(times, ensure_ascii=False, indent=2), encoding="utf-8")

    # simple HTML list
    SESSIONS_HTML.parent.mkdir(parents=True, exist_ok=True)
    lis = []
    for it in items:
        href = it.get("url") or "#"
        lab  = it.get("label", it["start"])
        fam  = it.get("course_family","")
        city = it.get("city","")
        lis.append(f"<li><a href='{href}'>{lab}</a> <small style='color:#666'>&nbsp;[{fam} - {city}]</small></li>")
    html = [
        "<!doctype html><meta charset='utf-8'>",
        "<title>Sessions | 910CPR</title>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<body style='font-family:system-ui;margin:24px'>",
        "<h1>Sessions</h1><ul>",
        *lis,
        "</ul></body>",
    ]
    SESSIONS_HTML.write_text("\n".join(html), encoding="utf-8")

    # debug report
    with REPORT.open("w", encoding="utf-8") as f:
        f.write(f"Source CSV: {src}\n")
        f.write(f"Delimiter: {delim}\n")
        f.write(f"Headers: {headers}\n")
        f.write(f"Rows read: {len(rows)}\n")
        f.write(f"Parsed items: {len(items)}\n")
        f.write(f"Skipped rows: {len(issues)}\n\n")
        for i, it in enumerate(issues[:50], 1):
            raw = json.dumps(it["row"], ensure_ascii=False)
            f.write(f"[{i}] {it['reason']}\n  row: {raw}\n\n")

    print(f"[sessions_to_periscope] wrote {PERISCOPE_JSON} ({len(items)} items)")
    print(f"[sessions_to_periscope] wrote {DATA_OUT / 'session-times.json'} ({len(times)} datetimes)")
    print(f"[sessions_to_periscope] wrote {SESSIONS_HTML}")
    print(f"[sessions_to_periscope] report: {REPORT}")

if __name__ == "__main__":
    main()
