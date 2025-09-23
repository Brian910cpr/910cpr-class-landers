# periscope-simple 1.0 — use the CSV 'date' column to produce 'start'
import sys, json
from pathlib import Path
import pandas as pd

def pick_series(df, *names):
    for n in names:
        if n in df.columns:
            return df[n]
    return pd.Series([""] * len(df))

def to_str(x): return "" if x is None else str(x)

def main(inp_csv, out_json):
    print("[periscope-simple] start")
    df = pd.read_csv(inp_csv, dtype=str, keep_default_na=False).fillna("")
    print("[periscope] columns:", list(df.columns))

    if "date" not in df.columns:
        print("[periscope] ERROR: 'date' column missing in CSV")
        sys.exit(1)

    dt = pd.to_datetime(df["date"], errors="coerce", infer_datetime_format=True)
    start = dt.dt.strftime("%Y-%m-%d %H:%M")
    start = start.where(dt.notna(), "")

    title   = pick_series(df, "course", "title", "certification")
    cert    = pick_series(df, "certification")
    agency  = pick_series(df, "agency")
    fmt     = pick_series(df, "format")
    city    = pick_series(df, "location.city", "city")
    venue   = pick_series(df, "location", "venue")
    urlcol  = pick_series(df, "link", "url", "href")

    rows = []
    blanks = 0
    for i in range(len(df)):
        s = to_str(start.iloc[i])
        if not s: blanks += 1
        u = to_str(urlcol.iloc[i]) or "#"
        rows.append({
            "title": to_str(title.iloc[i]),
            "course": to_str(title.iloc[i]),
            "certification": to_str(cert.iloc[i]),
            "agency": to_str(agency.iloc[i]),
            "format": to_str(fmt.iloc[i]),
            "start": s,
            "end": "",
            "city": to_str(city.iloc[i]),
            "venue": to_str(venue.iloc[i]),
            "url": u
        })

    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)

    print(f"[periscope] wrote {len(rows)} items -> {out_json}")
    print(f"[periscope] empty starts: {blanks}")
    for i in range(min(5, len(rows))):
        r = rows[i]
        print(f"[periscope] sample[{i}] start='{r['start']}' url='{r['url']}' city='{r['city']}' title='{r['title'][:60]}'")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python scripts/sessions_to_periscope.py <input_csv> <output_json>")
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
