#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sessions_to_periscope.py
Read sessions CSV and emit periscope_full.json for the homepage.

Keeps fields:
 title, course, certification, agency, format, start, end, city, url (registration_url), venue
"""
import sys, json
import pandas as pd

def main():
    if len(sys.argv) != 3:
        print("usage: sessions_to_periscope.py <sessions.csv> <periscope_full.json>")
        sys.exit(1)

    csv_path, json_out = sys.argv[1], sys.argv[2]
    df = pd.read_csv(csv_path)

    def pick(r, k, alt=""):
        v = r.get(k, "")
        return ("" if pd.isna(v) else str(v)) or alt

    out = []
    for _, r in df.iterrows():
        title = pick(r, "course_title")
        out.append({
            "title": title,
            "course": title,  # keep both for compatibility
            "certification": pick(r, "certification"),
            "agency": pick(r, "agency"),
            "format": pick(r, "format"),
            "start": pick(r, "start"),
            "end":   pick(r, "end"),
            "city":  pick(r, "city"),
            "venue": pick(r, "venue"),
            "url":   pick(r, "registration_url") or "#",
        })

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"[periscope] wrote {len(out)} items -> {json_out}")

if __name__ == "__main__":
    main()
