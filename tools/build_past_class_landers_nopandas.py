#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Generates Past Class landers (HTML) from Enrollware CSV + HOVN course list.
# No external deps (stdlib only).
import os, sys, argparse, json, re, csv
from datetime import datetime, timedelta

def ensure_dir(path): os.makedirs(path, exist_ok=True)
def slugify(text):
    if not text: return ""
    s = re.sub(r"[^\w\s\-]+", "", text, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s.lower()
def html_escape(s):
    if s is None: return ""
    return (s.replace("&","&amp;").replace("<","&lt;")
             .replace(">","&gt;").replace('"',"&quot;").replace("'","&#39;"))

APPROVED = ["325 Sound Rd","111 S Wright St","115-3 Hinton Ave","4018 Shipyard Blvd","809 Gum Branch Rd","4902 Merlot Ct"]
def normalize_display_location(venue, city, state="NC"):
    venue = (venue or "").strip(); city = (city or "").strip()
    if not venue: return f"{city}, {state}".strip(", ")
    for allow in APPROVED:
        if allow.lower() in venue.lower():
            return ", ".join([p for p in [venue, city, state] if p])
    return f"{city}, {state}".strip(", ")

BASE_CSS = "\n".join([
":root{--bg1:#ffffff;--bg2:#eef7ff;--border:#e5e7eb;--accent:#0369a1;--accent2:#0ea5e9;}",
"*{box-sizing:border-box}",
"body{margin:0;font-family:system-ui,'Segoe UI',Roboto,Arial,sans-serif;line-height:1.5;background:linear-gradient(180deg,var(--bg1),var(--bg2));color:#0f172a}",
".container{max-width:1080px;margin:0 auto;padding:16px}",
".header{display:flex;flex-wrap:wrap;align-items:center;gap:12px;justify-content:space-between}",
".logo{display:flex;align-items:center;gap:10px}",
".logo img{width:40px;height:40px}",
".title{font-size:20px;font-weight:700}",
".banner{background:#fee2e2;border:1px solid #fecaca;padding:10px;border-radius:10px;margin:12px 0;color:#7f1d1d}",
".chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}",
".chip{padding:6px 10px;border:1px solid var(--border);border-radius:999px;text-decoration:none;color:#0f172a;background:#fff}",
".hero{display:grid;gap:16px;grid-template-columns:1.2fr .8fr;align-items:start}",
"@media(max-width:900px){.hero{grid-template-columns:1fr}}",
".card{background:#fff;border:1px solid var(--border);border-radius:16px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.04)}",
".btn{display:inline-block;padding:10px 14px;border-radius:10px;background:#0369a1;color:#fff;text-decoration:none}",
".btn.secondary{background:#111827}",
".upcoming ul{margin:0 0 12px 18px}",
"footer{margin:30px 0 40px;color:#475569}",
".float-call{position:fixed;right:12px;bottom:12px;padding:12px 14px;border-radius:999px;background:#0ea5e9;color:#fff;text-decoration:none;font-weight:700;box-shadow:0 4px 10px rgba(0,0,0,.18)}",
"img.responsive{max-width:100%;height:auto;display:block}",
".meta{font-size:14px;color:#475569}",
])

def render_chips(course_label, hovn_link):
    return f'''
<div class="chips">
  <a class="chip" href="{html_escape(hovn_link)}">All {html_escape(course_label)} Sessions</a>
  <a class="chip" href="/index.html#courses">All Courses</a>
  <a class="chip" href="/past-classes.html">Past Classes</a>
  <a class="chip" href="/locations.html">Locations</a>
</div>'''.strip()

def render_floating_phone():
    return '<a class="float-call" href="tel:+19103955193" aria-label="Call 910 CPR">Call 910 CPR</a>'

def render_jsonld(provider_name, course_name, course_desc, start_iso, end_iso, display_loc, course_url, image_url):
    obj = {
        "@context":"https://schema.org","@type":"Course",
        "name":course_name,"description":course_desc,
        "provider":{"@type":"Organization","name":provider_name,"url":"https://www.910cpr.com/","telephone":"+1-910-395-5193"},
        "hasCourseInstance":[{"@type":"Event","name":f"{course_name} (Past Session)","eventStatus":"https://schema.org/EventCancelled",
        "eventAttendanceMode":"https://schema.org/OfflineEventAttendanceMode","startDate":start_iso,"endDate":end_iso,
        "location":{"@type":"Place","name":display_loc},"image":image_url,"url":course_url}]
    }
    return f'<script type="application/ld+json">{json.dumps(obj, separators=(",", ":"), ensure_ascii=False)}</script>'

def read_csv_dicts(path):
    import io
    with open(path, "rb") as f:
        raw = f.read()
    # handle possible UTF-8 BOM or Windows-1252
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    return list(csv.DictReader(io.StringIO(text)))

def parse_dt(value):
    if not value: return None
    s = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M"):
        try: return datetime.strptime(s, fmt)
        except Exception: pass
    try:
        if len(s) >= 16 and s[10] in " T":
            return datetime.strptime(s[:16].replace("T"," "), "%Y-%m-%d %H:%M")
    except Exception: pass
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--enrollware_csv", required=True)
    ap.add_argument("--hovn_csv", required=True)
    ap.add_argument("--course_export", default="")
    ap.add_argument("--upcoming_csv", default="")
    args = ap.parse_args()

    out_dir = os.path.join(args.root, "past"); ensure_dir(out_dir)

    enroll = read_csv_dicts(args.enrollware_csv)
    hovn   = read_csv_dicts(args.hovn_csv)

    # label -> link
    hovn_by_label = {}
    for r in hovn:
        lab = (r.get("label") or "").strip()
        if lab: hovn_by_label[lab] = (r.get("link") or "").strip()

    # course descriptions from CSV only (xlsx not supported here)
    course_descs = {}
    if args.course_export and os.path.exists(args.course_export) and args.course_export.lower().endswith(".csv"):
        for r in read_csv_dicts(args.course_export):
            lab = (r.get("label") or "").strip()
            desc = (r.get("description_html") or "").strip()
            if lab and desc: course_descs[lab] = desc

    total = 0
    for r in enroll:
        course_title = (r.get("course_title") or "").strip()
        hovn_match   = (r.get("hovn_match") or "").strip()
        course_label = hovn_match if hovn_match else course_title

        start = parse_dt(r.get("start"))
        if not start: continue
        end = parse_dt(r.get("end")) or (start + timedelta(hours=1))

        city  = (r.get("city") or "").strip()
        venue = (r.get("venue") or "").strip()
        display_loc = normalize_display_location(venue, city, "NC")

        hovn_link = hovn_by_label.get(course_label, "")
        date_pretty = start.strftime("%A, %B %d, %Y %I:%M %p").replace(" 0", " ")

        page_title = f"{course_label} — {date_pretty} — {display_loc}"
        token = start.strftime("%Y-%m-%d_%H%M")
        file_slug = slugify(course_label)
        city_slug = slugify(city) if city else "nc"
        file_name = f"{token}_{file_slug}_{city_slug}.html"
        out_path = os.path.join(out_dir, file_name)

        img = f"/images/{slugify(course_label)}.jpg"
        img_fallback = "/images/910cpr_wave.png"

        course_desc = course_descs.get(course_label, f"This is a past session record for {course_label} held by 910 CPR. Browse current dates and register online.")
        start_iso = start.strftime("%Y-%m-%dT%H:%M:%S")
        end_iso   = end.strftime("%Y-%m-%dT%H:%M:%S")

        jsonld = render_jsonld("910 CPR", course_label, course_desc, start_iso, end_iso, display_loc, hovn_link, img)
        chips  = render_chips(course_label, hovn_link)
        phone  = render_floating_phone()
        meta_desc = f"Past class record for {course_label} on {date_pretty} at {display_loc}. See current schedule and upcoming sessions with 910 CPR."

        html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html_escape(page_title)} | 910 CPR</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{html_escape(meta_desc)}">
<link rel="canonical" href="https://910cpr.com/past/{html_escape(file_name)}">
<meta property="og:title" content="{html_escape(page_title)}">
<meta property="og:description" content="{html_escape(meta_desc)}">
<meta property="og:type" content="website">
<meta property="og:image" content="{img}">
<style>{BASE_CSS}</style>
{jsonld}
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="logo">
        <img src="/images/910cpr_round.png" alt="910 CPR logo">
        <div class="title">910 CPR</div>
      </div>
      <div class="meta">
        <strong>Call:</strong> <a href="tel:+19103955193">(910) 395-5193</a>
      </div>
    </div>

    {chips}

    <div class="banner"><strong>PAST CLASS:</strong> This session took place on {html_escape(date_pretty)} at {html_escape(display_loc)}. Looking for a seat? <a href="{html_escape(hovn_link)}">See current {html_escape(course_label)} dates</a>.</div>

    <div class="hero">
      <div class="card">
        <h1>{html_escape(course_label)}</h1>
        <p class="meta">{html_escape(date_pretty)} • {html_escape(display_loc)}</p>
        <div class="desc">{course_desc}</div>
        <p><a class="btn" href="{html_escape(hovn_link)}">See Current Schedule</a></p>
      </div>

      <div class="card">
        <img class="responsive" src="{img}" onerror="this.onerror=null;this.src='{img_fallback}';" alt="{html_escape(course_label)} training in {html_escape(display_loc)}">
        <p class="meta">Image represents the course type. Dates and availability change regularly.</p>
      </div>
    </div>

    <footer>
      © {datetime.now().year} 910 CPR • <a href="tel:+19103955193">(910) 395-5193</a> • <a href="mailto:info@910cpr.com">info@910cpr.com</a>
    </footer>
  </div>
  {phone}
</body>
</html>"""
        with open(out_path, "w", encoding="utf-8") as f: f.write(html)
        total += 1
        if total % 1000 == 0: print(f"Generated {total} pages...")

    print(f"Done. Generated {total} past class landers in: {out_dir}")

if __name__ == "__main__":
    main()
