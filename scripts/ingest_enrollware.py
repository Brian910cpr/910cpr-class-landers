#!/usr/bin/env python
"""
Normalize Enrollware export -> sessions schema our generators understand.

Input CSV columns (from Enrollware):
  ID, Course, Start Date / Time, End Date / Time, Location, Client, Instructor,
  Assistants, Students, Seats, Hours, Registration Link

Output CSV columns:
  course_title, course_family, agency, certification, format,
  start, end, city, venue, registration_url, source, location_id
"""
import csv, re, sys
from datetime import datetime

# -------- OPTIONAL: map Enrollware Location codes -> city/venue ----------
# If you have a locations CSV, replace this with a loader that reads:
# location_id,city,venue
LOCATION_MAP = {
    # "809": {"city": "Wilmington", "venue": "Shipyard Blvd"},
    # Add more as needed
}

TAG_RE = re.compile(r"<[^>]+>")
SP_RE  = re.compile(r"\s+")

def strip_html(s:str) -> str:
    if not s: return ""
    return SP_RE.sub(" ", TAG_RE.sub("", s)).strip()

def detect_agency(title:str) -> str:
    t = title.upper()
    if "AHA" in t or "HEARTSAVER" in t: return "AHA"
    if "HSI" in t or "HEALTH & SAFETY INSTITUTE" in t: return "HSI"
    if "ARC" in t or "RED CROSS" in t: return "ARC"
    return ""

def detect_family(title:str) -> str:
    t = title.upper()
    if " BLS" in t or "BASIC LIFE SUPPORT" in t: return "BLS"
    if " ACLS" in t or "ADVANCED CARDIO" in t: return "ACLS"
    if " PALS" in t or "PEDIATRIC ADVANCED" in t: return "PALS"
    if "HEARTSAVER" in t or "FIRST AID" in t:   return "FA"
    return ""

def detect_cert(title:str, fam:str) -> str:
    t = title.upper()
    # Try to keep whatever Enrollware said (e.g., "BLS Provider")
    for key in ["BLS PROVIDER", "ACLS PROVIDER", "PALS PROVIDER",
                "HEARTSAVER", "FIRST AID / CPR / AED", "FIRST AID", "CPR / AED"]:
        if key in t: return key.title()
    # Fallback by family
    return {"BLS":"BLS Provider","ACLS":"ACLS Provider","PALS":"PALS Provider","FA":"First Aid / CPR / AED"}.get(fam,"")

def detect_format(title:str) -> str:
    t = title.upper()
    if "HEARTCODE" in t or "ONLINE + SKILLS" in t or "SKILLS SESSION" in t or "SKILLS ASSESSMENT" in t or "BLENDED" in t:
        return "Online + Skills"
    if "IN-PERSON" in t or "IN PERSON" in t or "CLASSROOM" in t or "INSTRUCTOR-LED" in t:
        return "In-Person"
    return ""

def parse_when(s:str):
    """Accepts 'M/D/YYYY HH:MM' (24h) or 'M/D/YYYY H:MM AM/PM'"""
    if not s: return ""
    s = s.strip()
    for fmt in ("%m/%d/%Y %H:%M", "%m/%d/%Y %I:%M %p"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            pass
    # Last resort: try to let datetime guess (may depend on locale)
    try:
        return datetime.fromisoformat(s.replace(" ","T")).strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        return s  # return raw if we can’t parse—better than dropping the row

def row_to_normalized(r:dict) -> dict:
    raw_course = r.get("Course","")
    title = strip_html(raw_course)
    fam   = detect_family(title)
    agency= detect_agency(title)
    cert  = detect_cert(title, fam)
    fmt   = detect_format(title)

    loc_id = str(r.get("Location","") or "").strip()
    loc = LOCATION_MAP.get(loc_id, {})
    city  = loc.get("city","")
    venue = loc.get("venue","")

    return {
        "course_title": title,
        "course_family": fam,
        "agency": agency,
        "certification": cert,
        "format": fmt,
        "start": parse_when(r.get("Start Date / Time","")),
        "end":   parse_when(r.get("End Date / Time","")),
        "city":  city,
        "venue": venue,
        "registration_url": (r.get("Registration Link","") or "").strip(),
        "source": "enrollware",
        "location_id": loc_id,
    }

def main(inp, outp):
    with open(inp, newline="", encoding="utf-8-sig") as f, \
         open(outp, "w", newline="", encoding="utf-8") as g:
        rd = csv.DictReader(f)
        cols = ["course_title","course_family","agency","certification","format",
                "start","end","city","venue","registration_url","source","location_id"]
        wr = csv.DictWriter(g, fieldnames=cols)
        wr.writeheader()
        count = 0
        for r in rd:
            try:
                wr.writerow(row_to_normalized(r)); count += 1
            except Exception as e:
                # Don’t hard-fail on a single bad row
                sys.stderr.write(f"[skip] {e}\n")
        print(f"[enrollware] wrote {count} rows -> {outp}")

if __name__ == "__main__":
    if len(sys.argv)!=3:
        print("Usage: python scripts\\ingest_enrollware.py <enrollware_export.csv> <normalized_out.csv>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
