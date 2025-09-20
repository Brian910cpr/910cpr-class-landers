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
    if "HEARTSAVER" in t or "FIRST AID" in t or t == "FA": return "FA"
    if "BLS" in t or "BASIC LIFE" in t: return "BLS"
    # try from URL slugs
    if "acls" in t: return "ACLS"
    if "pals" in t: return "PALS"
    if "first" in t or "aid" in t or "hsi" in t: return "FA"
    return "BLS"

def parse_time_any(s: str) -> str:
    """Return HH:MM in 24h from many inputs."""
    if not s: return ""
    s = s.strip().lower().replace(" ", "").replace(".", "")
    # fold variants like "6p" or "630p"
    m = re.match(r"^(\d{1,2})(\d{2})?(am|pm)?$", s)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2) or 0)
        ap = m.group(3)
        if ap == "pm" and hh < 12: hh += 12
        if ap == "am" and hh == 12: hh = 0
        return f"{hh:02d}:{mm:02d}"
    for tfmt in ("%H:%M", "%I:%M%p", "%I%M%p", "%I%p"):
        try:
            dt = datetime.strptime(s, tfmt)
            return dt.strftime("%H:%M")
        except Exception:
            continue
    return ""

def parse_date_any(s: str) -> str:
    """Return YYYY-MM-DD from many inputs."""
    if not s: return ""
    s = s.strip()
    for dfmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(s, dfmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    # last resort: try to zero-pad 1/2/2025 style
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", s)
    if m:
        mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if yy < 100: yy += 2000
        return f"{yy:04d}-{mm:02d}-{dd:02d}"
    return ""

def parse_start(row) -> (str, str):
    """
    Return (start_iso, reason_if_blank).
    Accepts:
      - start/start_iso/start_at/start_time_iso
      - datetime/start_datetime/session_start
      - date + time in many formats
    """
    # 1) direct ISO-ish
    iso = coalesce(row, "start", "start_iso", "start_at", "start_time_iso", "Start", "START")
    if iso:
        iso = iso.replace(" ", "T")
        m = re.match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{1,2}:\d{2})", iso)
        if m:
            d = parse_date_any(m.group(1))
            t = parse_time_any(m.group(2))
            if d and t: return f"{d}T{t}", ""
        # if it looks like ISO but mismatched, carry through
        return iso, ""

    # 2) combined datetime fields
    dtxt = coalesce(row, "datetime", "start_datetime", "session_start", "StartDateTime", "startDateTime")
    if dtxt:
        # split common "YYYY-MM-DD HH:MM am" cases
        m = re.match(r"^(\d{4}-\d{2}-\d{2})[ T](\d{1,2}:\d{2}(?: ?[AaPp][Mm])?)$", dtxt.strip())
        if m:
            d, t = parse_date_any(m.group(1)), parse_time_any(m.group(2))
            if d and t: return f"{d}T{t}", ""
        # try slash dates too
        m = re.match(r"^(\d{1,2}/\d{1,2}/\d{2,4})[ T](\d{1,2}:?\d{0,2}(?: ?[AaPp][Mm])?)$", dtxt.strip())
        if m:
            d, t = parse_date_any(m.group(1)), parse_time_any(m.group(2))
            if d and t: return f"{d}T{t}", ""

    # 3) separate date/time
    d = coalesce(row, "date", "Date", "session_date")
    t = coalesce(row, "time", "Time", "start_time")
    dd, tt = parse_date_any(d), parse_time_any(t)
    if dd and tt: return f"{dd}T{tt}", ""
    reason = "missing or unparsable date/time"
    return "", reason

def row_to_item(row: dict, issues: list) -> dict:
    start, reason = parse_start(row)
    city = coalesce(row, "city", "City", "location_city", "LocationCity", "location")
    url  = coalesce(row, "url", "enroll_url", "EnrollURL", "link", "Link", "hovn_url")
    course = coalesce(row, "course_family", "course", "Course", "title", "Title", "CourseName")
    fam = coalesce(row, "course_family") or guess_course_family(course or url)
    item = {"course_family": fam, "start": start, "city": city, "url": url}
    # label
    if start and city:
        try:
            dt = datetime.strptime(start[:16], "%Y-%m-%dT%H:%M")
            hm = dt.strftime("%I:%M%p").lstrip("0").lower().replace(":00","").replace("am","a").replace("pm","p")
            item["label"] = f"{dt.strftime('%b %d')}, {hm} - {city}"
        except Exception:
            item["label"] = f"{start} - {city}"
    else:
        item["label"] = city or ""
    # issue tracking
    if not start:
        issues.append({"row": row, "reason": reason})
    return item

def load_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            yield {(k or "").strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}

def main():
    # Find CSV
    candidates = []
    if len(sys.argv) > 1:
        candidates = [Path(sys.argv[1])]
    candidates += [ROOT / "data" / "sessions.csv", ROOT / "sessions.csv"]
    src = next((p for p in candidates if p.exists()), None)
    if not src:
        print("[sessions_to_periscope] CSV not found. Looked for:")
        for c in candidates: print(" -", c)
        sys.exit(1)

    rows = list(load_csv(src))
    issues = []
    items = [row_to_item(r, issues) for r in rows if r]
    # keep only items with start
    items = [x for x in items if x.get("start")]

    # sort by start
    def key_iso(x):
        s = x.get("start","")
        try:
            return datetime.strptime(s[:16], "%Y-%m-%dT%H:%M")
        except Exception:
            return datetime.max
    items.sort(key=key_iso)

    # outputs
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
