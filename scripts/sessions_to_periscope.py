import sys, json, re
from pathlib import Path
import pandas as pd

# ---------- helpers ----------
TAG_RE = re.compile(r"<[^>]+>")
HTTP_RE = re.compile(r"https?://", re.I)
DATE_LIKE_RE = re.compile(r"\b(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Za-z]{3,9}\s+\d{1,2},\s*\d{4})\b")
TIME_LIKE_RE = re.compile(r"\b(\d{1,2}:\d{2}\s*(AM|PM)?|\d{1,2}\s*(AM|PM))\b", re.I)

def strip_html(s: str) -> str:
    if not isinstance(s, str): return ""
    return TAG_RE.sub("", s).strip()

def to_str(s):
    return "" if s is None else str(s)

def coerce_dt(s: str) -> str:
    s = to_str(s).strip()
    if not s:
        return ""
    # normalize common junk
    s = (s.replace(" at ", " ")
           .replace("@", " ")
           .replace("\u2013", "-")
           .replace("\u2014", "-"))
    try:
        dt = pd.to_datetime(s, errors="coerce", infer_datetime_format=True)
        if pd.isna(dt):
            return ""
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""

def best_date_column(df: pd.DataFrame) -> str | None:
    """Pick the column whose values most often parse as datetimes."""
    best, best_cnt = None, -1
    for c in df.columns:
        series = df[c].astype(str).fillna("")
        # quick screen: must look like date in at least a few rows
        if not series.str.contains(DATE_LIKE_RE).any():
            continue
        sample = series.head(400)  # limit work
        parsed = pd.to_datetime(sample, errors="coerce", infer_datetime_format=True)
        cnt = parsed.notna().sum()
        if cnt > best_cnt:
            best, best_cnt = c, cnt
    return best

def find_date_and_time_columns(df: pd.DataFrame) -> tuple[str|None, str|None]:
    """Find separate date and time columns if a single datetime column wasn’t found."""
    date_col = None
    time_col = None
    for c in df.columns:
        s = df[c].astype(str).fillna("")
        if s.str.contains(DATE_LIKE_RE).any() and (date_col is None):
            date_col = c
        if s.str.contains(TIME_LIKE_RE).any() and (time_col is None):
            time_col = c
    return date_col, time_col

def find_url_column(df: pd.DataFrame) -> str | None:
    # header hints
    prefer = [r"url", r"href", r"link", r"registration", r"enroll", r"signup"]
    lc = {c: c.lower() for c in df.columns}
    for pat in prefer:
        for c in df.columns:
            if re.search(pat, lc[c], re.I):
                return c
    # value-based fallback
    for c in df.columns:
        if df[c].astype(str).str.contains(HTTP_RE).any():
            return c
    return None

def find_title_column(df: pd.DataFrame) -> str | None:
    prefer = [r"title", r"course name", r"name", r"session", r"class"]
    lc = {c: c.lower() for c in df.columns}
    for pat in prefer:
        for c in df.columns:
            if re.search(pat, lc[c], re.I):
                return c
    # last resort: "course"
    for c in df.columns:
        if lc[c] == "course":
            return c
    return None

def find_city_column(df: pd.DataFrame) -> str | None:
    prefer = [r"\bcity\b", r"location city", r"site city"]
    lc = {c: c.lower() for c in df.columns}
    for pat in prefer:
        for c in df.columns:
            if re.search(pat, lc[c], re.I):
                return c
    return None

def find_venue_column(df: pd.DataFrame) -> str | None:
    prefer = [r"venue", r"location name", r"location", r"site", r"address"]
    lc = {c: c.lower() for c in df.columns}
    for pat in prefer:
        for c in df.columns:
            if re.search(pat, lc[c], re.I):
                return c
    return None

def guess_city_from_text(txt: str) -> str:
    if not isinstance(txt, str): return ""
    u = txt.upper()
    if "WILM" in u: return "Wilmington"
    if "BURGAW" in u: return "Burgaw"
    if "JACKSONVILLE" in u or "CAMP LEJEUNE" in u: return "Jacksonville"
    return ""

# ---------- main ----------
def main(inp_csv: str, out_json: str):
    p_in = Path(inp_csv); p_out = Path(out_json)
    if not p_in.exists():
        print(f"[periscope] ERROR: CSV not found: {p_in}")
        sys.exit(1)

    df = pd.read_csv(p_in, dtype=str, keep_default_na=False).fillna("")
    cols = list(df.columns)
    print(f"[periscope] columns detected ({len(cols)}): {cols}")

    # detect columns
    title_col = find_title_column(df)
    url_col   = find_url_column(df)
    city_col  = find_city_column(df)
    venue_col = find_venue_column(df)

    start_col = best_date_column(df)
    date_col, time_col = (None, None)
    if not start_col:
        date_col, time_col = find_date_and_time_columns(df)

    print("[periscope] mapping:")
    print(f"  title -> {title_col}")
    print(f"  url   -> {url_col}")
    print(f"  start -> {start_col}")
    print(f"  date  -> {date_col}")
    print(f"  time  -> {time_col}")
    print(f"  city  -> {city_col}")
    print(f"  venue -> {venue_col}")

    rows = []
    blanks_start = 0
    blanks_url   = 0

    for _, r in df.iterrows():
        raw_title = r.get(title_col, "") if title_col else r.get("course", "")
        title = strip_html(to_str(raw_title)) or to_str(r.get("course", ""))

        # datetime
        start_iso = ""
        if start_col:
            start_iso = coerce_dt(r.get(start_col, ""))
        elif date_col:
            date_val = to_str(r.get(date_col, "")).strip()
            time_val = to_str(r.get(time_col, "")).strip() if time_col else ""
            start_iso = coerce_dt((date_val + " " + time_val).strip())

        # location bits
        city  = to_str(r.get(city_col, "")) if city_col else ""
        venue = to_str(r.get(venue_col, "")) if venue_col else ""
        if not city:
            city = guess_city_from_text(venue) or guess_city_from_text(" ".join([title, venue]))

        # url
        url = to_str(r.get(url_col, "")) if url_col else ""
        if not url or not HTTP_RE.search(url):
            url = "#"

        if not start_iso: blanks_start += 1
        if url == "#":    blanks_url   += 1

        rows.append({
            "title": title,
            "course": to_str(r.get("course", "")),
            "certification": to_str(r.get("certification", "")),
            "agency": to_str(r.get("agency", "")),
            "format": to_str(r.get("format", "")),
            "start": start_iso,
            "end": "",  # not used on homepage
            "city": city,
            "venue": venue,
            "url": url,
        })

    p_out.parent.mkdir(parents=True, exist_ok=True)
    with p_out.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)

    print(f"[periscope] wrote {len(rows)} items -> {p_out}")
    print(f"[periscope] empty starts: {blanks_start}  |  empty urls: {blanks_url}")
    for i, it in enumerate(rows[:5]):
        print(f"[periscope] sample[{i}] start='{it['start']}' url='{it['url']}' city='{it['city']}' title='{(it['title'])[:60]}'")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python scripts/sessions_to_periscope.py <input_csv> <output_json>")
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
