#!/usr/bin/env python3
import argparse, json, re, os
from datetime import datetime, timezone, timedelta
import pandas as pd

# Matches " ... GMT-0400 (Eastern Daylight Time)" or " ... GMT+0000"
JS_TZ_RE = re.compile(r'\s+GMT([+-]\d{4})(?:\s*\(.*\))?\s*$')

def _parse_js_date(s: str) -> str:
    """
    Parse strings like:
      "Sat Sep 20 2025 17:00:00 GMT-0400 (Eastern Daylight Time)"
    Return ISO8601 "2025-09-20T17:00:00-04:00" or "" if unparseable.
    """
    if not s or not isinstance(s, str):
        return ""
    s = s.strip()

    # peel off numeric GMT offset and optional tz name
    m = JS_TZ_RE.search(s)
    tzinfo = None
    if m:
        off = m.group(1)  # e.g. "-0400"
        sign = 1 if off[0] == '+' else -1
        hh = int(off[1:3])
        mm = int(off[3:5])
        tzinfo = timezone(sign * timedelta(hours=hh, minutes=mm))
        core = s[:m.start()].strip()  # e.g. "Sat Sep 20 2025 17:00:00"
    else:
        core = re.sub(r'\s*\(.*\)\s*$', '', s)            # remove "(EDT)" if present
        core = re.sub(r'\s+GMT[^\s]*$', '', core).strip() # remove trailing "GMT..."

    # try a handful of common formats
    for fmt in ("%a %b %d %Y %H:%M:%S",
                "%a %b %d %Y %H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%m/%d/%Y %H:%M",
                "%m/%d/%Y"):
        try:
            dt = datetime.strptime(core, fmt)
            if tzinfo:
                dt = dt.replace(tzinfo=tzinfo)
            return dt.isoformat()
        except Exception:
            pass

    # last-resort ISO-ish
    try:
        dt = datetime.fromisoformat(core)
        if tzinfo and dt.tzinfo is None:
            dt = dt.replace(tzinfo=tzinfo)
        return dt.isoformat()
    except Exception:
        return ""

def build_periscope(csv_path: str):
    """
    Emit rows with keys: title, course, certification, agency, format,
    start, end, city, venue, url
    """
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    out = []
    for _, row in df.iterrows():
        start = _parse_js_date(row.get("date", ""))  # your CSV has the JS-style date here
        out.append({
            "title": (row.get("course","") or "").strip(),
            "course": (row.get("course","") or "").strip(),
            "certification": (row.get("certification","") or "").strip(),
            "agency": (row.get("agency","") or "").strip(),
            "format": (row.get("format","") or "").strip(),
            "start": start,
            "end": "",
            "city": (row.get("location.city","") or "").strip(),
            "venue": (row.get("location","") or "").strip(),
            "url": (row.get("link","") or "").strip() or "#",
        })
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("out")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    rows = build_periscope(args.csv)

    # atomic write (prevents empty/truncated JSON on crash)
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    os.replace(tmp, args.out)

    if args.verbose:
        empty_starts = sum(1 for x in rows if not x.get("start"))
        empty_urls   = sum(1 for x in rows if not x.get("url"))
        print(f"[periscope] wrote {len(rows)} items -> {args.out}")
        print(f"[periscope] empty starts: {empty_starts}  |  empty urls: {empty_urls}")
        for i, x in enumerate(rows[:5]):
            print(f"[periscope] sample[{i}] start='{x['start']}' url='{x['url']}' city='{x['city']}' title='{x['title']}'")
