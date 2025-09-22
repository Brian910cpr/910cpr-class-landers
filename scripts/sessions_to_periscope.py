import sys, json
from pathlib import Path
import pandas as pd

CANDS = {
    "title": ["title", "Title", "Course Name", "Name", "Session", "Class"],
    "course": ["course", "Course", "Course Type", "Program"],
    "certification": ["certification", "Certification", "Credential"],
    "agency": ["agency", "Agency", "Program Agency"],
    "format": ["format", "Format", "Delivery", "Class Type"],
    "start": [
        "start","Start","Start Date / Time","Start Date","StartDateTime",
        "start_time","Start Time","DateTime","datetime","Date/Time",
    ],
    "end": [
        "end","End","End Date / Time","End Date","EndDateTime",
        "end_time","End Time",
    ],
    "dateonly": ["Date","Class Date","Session Date"],
    "timeonly": ["Start Time","Time","Class Time","StartTime"],
    "city": ["city","City","Location City","Location_City","Site City"],
    "venue": ["venue","Venue","Location","Location Name","Site","Site Name","Address","Location Address"],
    "url": ["url","URL","Href","Link","Registration","Registration Link","Registration URL","Enroll Link","Signup","Signup Link"],
}

def pick(df, names):
    for n in names:
        if n in df.columns:
            return n
    return None

def parse_dt(val: str) -> str:
    if val is None: return ""
    s = str(val).strip()
    if not s: return ""
    s = s.replace(" at ", " ").replace("@", " ").replace("\u2013", "-").replace("\u2014", "-")
    try:
        dt = pd.to_datetime(s, errors="coerce", infer_datetime_format=True)
        if pd.isna(dt): return ""
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""

def main(inp_csv: str, out_json: str):
    p_in = Path(inp_csv); p_out = Path(out_json)
    if not p_in.exists():
        print(f"[periscope] ERROR: CSV not found: {p_in}"); sys.exit(1)

    df = pd.read_csv(p_in, dtype=str, keep_default_na=False).fillna("")
    m = {k: pick(df, CANDS[k]) for k in CANDS}

    print("[periscope] column mapping:")
    for k in ["title","course","certification","agency","format","start","end","dateonly","timeonly","city","venue","url"]:
        print(f"  {k:13} -> {m.get(k)}")

    rows = []; blanks_start = 0; blanks_url = 0
    for _, r in df.iterrows():
        title = r.get(m["title"], "") if m["title"] else ""
        course = r.get(m["course"], "") if m["course"] else ""
        cert = r.get(m["certification"], "") if m["certification"] else ""
        agency = r.get(m["agency"], "") if m["agency"] else ""
        fmt = r.get(m["format"], "") if m["format"] else ""

        start_raw = r.get(m["start"], "") if m["start"] else ""
        end_raw   = r.get(m["end"], "") if m["end"] else ""
        if not start_raw and (m["dateonly"] and m["timeonly"]):
            start_raw = f"{r.get(m['dateonly'], '')} {r.get(m['timeonly'], '')}"

        start_iso = parse_dt(start_raw)
        end_iso   = parse_dt(end_raw)

        city  = r.get(m["city"], "") if m["city"] else ""
        venue = r.get(m["venue"], "") if m["venue"] else ""
        if not city:
            u = f"{venue} {city}".upper()
            if "WILM" in u: city = "Wilmington"
            elif "BURGAW" in u: city = "Burgaw"

        url = r.get(m["url"], "") if m["url"] else ""
        if not url: url = "#"

        if not start_iso: blanks_start += 1
        if url == "#":    blanks_url += 1

        rows.append({
            "title": title, "course": course, "certification": cert, "agency": agency, "format": fmt,
            "start": start_iso, "end": end_iso, "city": city, "venue": venue, "url": url,
        })

    p_out.parent.mkdir(parents=True, exist_ok=True)
    with p_out.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)

    print(f"[periscope] wrote {len(rows)} items -> {p_out}")
    print(f"[periscope] empty starts: {blanks_start}  |  empty urls: {blanks_url}")
    for i, it in enumerate(rows[:5]):
        print(f"[periscope] sample[{i}] start='{it['start']}' url='{it['url']}' city='{it['city']}' title='{(it['title'] or it['course'])[:50]}'")

if __name__ == "__main__":
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print("usage: python scripts/sessions_to_periscope.py <input_csv> <output_json>"); sys.exit(2)
    main(sys.argv[1], sys.argv[2])
