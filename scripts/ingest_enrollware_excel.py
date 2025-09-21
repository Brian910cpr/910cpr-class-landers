#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ingest_enrollware_excel.py
Reads Enrollware 'Class Report.xlsx' and outputs our normalized sessions CSV.

Input columns expected (case-insensitive; extra columns ignored):
  ID, Course, Start Date / Time, End Date / Time, Location, Registration Link

Output columns:
  course_title,course_family,agency,certification,format,
  start,end,city,venue,registration_url,source,location_id
"""
import argparse
import re
from datetime import datetime
import pandas as pd

TAG_RE = re.compile(r"<[^>]+>")
SP_RE  = re.compile(r"\s+")

def strip_html(s: str) -> str:
    if pd.isna(s): return ""
    return SP_RE.sub(" ", TAG_RE.sub("", str(s))).strip()

def U(s): return (s or "").upper()

def detect_agency(title:str) -> str:
    t = U(title)
    if "AHA" in t or "HEARTSAVER" in t: return "AHA"
    if "HSI" in t or "HEALTH & SAFETY INSTITUTE" in t: return "HSI"
    if "ARC" in t or "RED CROSS" in t: return "ARC"
    return ""

def detect_family(title:str) -> str:
    t = U(title)
    if " BLS" in t or "BASIC LIFE SUPPORT" in t: return "BLS"
    if " ACLS" in t or "ADVANCED CARDIO" in t:  return "ACLS"
    if " PALS" in t or "PEDIATRIC ADVANCED" in t: return "PALS"
    if "HEARTSAVER" in t or "FIRST AID" in t:   return "FA"
    return ""

def detect_cert(title:str, fam:str) -> str:
    t = U(title)
    keys = ["BLS PROVIDER","ACLS PROVIDER","PALS PROVIDER",
            "HEARTSAVER","FIRST AID / CPR / AED","FIRST AID","CPR / AED"]
    for k in keys:
        if k in t: return k.title()
    return {"BLS":"BLS Provider","ACLS":"ACLS Provider","PALS":"PALS Provider","FA":"First Aid / CPR / AED"}.get(fam,"")

def detect_format(title:str) -> str:
    t = U(title)
    if ("HEARTCODE" in t or "ONLINE + SKILLS" in t or "SKILLS SESSION" in t
        or "SKILLS ASSESSMENT" in t or "BLENDED" in t):
        return "Online + Skills"
    if "IN-PERSON" in t or "IN PERSON" in t or "CLASSROOM" in t or "INSTRUCTOR-LED" in t:
        return "In-Person"
    return ""

def parse_when(s):
    if pd.isna(s): return ""
    s = str(s).strip()
    if isinstance(s, datetime):
        return s.strftime("%Y-%m-%dT%H:%M:%S")
    for f in ("%m/%d/%Y %H:%M", "%m/%d/%Y %I:%M %p"):
        try: return datetime.strptime(s, f).strftime("%Y-%m-%dT%H:%M:%S")
        except Exception: pass
    try: return datetime.fromisoformat(s.replace(" ","T")).strftime("%Y-%m-%dT%H:%M:%S")
    except Exception: return s

def load_locations(loc_csv):
    if not loc_csv: return {}
    try:
        df = pd.read_csv(loc_csv)
        out = {}
        for _,r in df.iterrows():
            k = str(r.get("location_id","")).strip()
            if k:
                out[k] = {
                    "city":  str(r.get("city","")  or ""),
                    "venue": str(r.get("venue","") or ""),
                }
        return out
    except Exception:
        return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx_in", help="Path to Enrollware Class Report.xlsx")
    ap.add_argument("csv_out", help="Path to normalized CSV out")
    ap.add_argument("--locations", help="Optional locations map CSV (location_id,city,venue)")
    args = ap.parse_args()

    locmap = load_locations(args.locations)

    df = pd.read_excel(args.xlsx_in, sheet_name=0, engine="openpyxl")
    cols = {c.lower(): c for c in df.columns}
    def col(name): return cols.get(name.lower())

    required = ["id","course","start date / time","end date / time","location","registration link"]
    missing = [n for n in required if col(n) is None]
    if missing:
        raise SystemExit(f"Missing required columns in Excel: {missing}")

    rows = []
    for _, r in df.iterrows():
        title = strip_html(r[col("course")])
        fam   = detect_family(title)
        loc_id = str(r[col("location")]).strip() if col("location") else ""
        rows.append({
            "course_title": title,
            "course_family": fam,
            "agency": detect_agency(title),
            "certification": detect_cert(title, fam),
            "format": detect_format(title),
            "start": parse_when(r[col("start date / time")]),
            "end":   parse_when(r[col("end date / time")]),
            "city":  (locmap.get(loc_id, {}).get("city","")),
            "venue": (locmap.get(loc_id, {}).get("venue","")),
            "registration_url": str(r.get(col("registration link"),"") or "").strip(),
            "source": "enrollware",
            "location_id": loc_id,
        })

    out = pd.DataFrame(rows, columns=[
        "course_title","course_family","agency","certification","format",
        "start","end","city","venue","registration_url","source","location_id"
    ])
    out.to_csv(args.csv_out, index=False, encoding="utf-8")
    print(f"[enrollware] wrote {len(out)} rows -> {args.csv_out}")

if __name__ == "__main__":
    main()
