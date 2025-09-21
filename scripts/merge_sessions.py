#!/usr/bin/env python
"""
Merge HOVN sessions (current) with normalized Enrollware sessions (past).

Usage:
  python scripts/merge_sessions.py docs\sessions_latest.csv data\enrollware_normalized.csv docs\sessions_all.csv
"""
import sys, csv

def read_rows(p):
    with open(p, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def write_rows(p, rows, fields):
    with open(p, 'w', newline='', encoding='utf-8') as g:
        w = csv.DictWriter(g, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k,"") for k in fields})

def main(hovn_csv, enroll_csv, out_csv):
    hovn = read_rows(hovn_csv)
    enr  = read_rows(enroll_csv)
    # Harmonize headers (take union, keep stable order)
    base_fields = [
        "session_id","course_family","course_title","city","location_name","address","zip",
        "start","end","registration_url","course_slug","city_slug","status"
    ]
    extra = []
    for r in hovn + enr:
        for k in r.keys():
            if k not in base_fields and k not in extra:
                extra.append(k)
    fields = base_fields + extra

    # De-dup by session_id
    seen = set()
    merged = []
    for r in hovn + enr:
        sid = r.get("session_id") or ""
        if sid in seen: continue
        seen.add(sid)
        merged.append(r)

    write_rows(out_csv, merged, fields)
    print(f"[merge] wrote {len(merged)} rows -> {out_csv}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python scripts\\merge_sessions.py docs\\sessions_latest.csv data\\enrollware_normalized.csv docs\\sessions_all.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
