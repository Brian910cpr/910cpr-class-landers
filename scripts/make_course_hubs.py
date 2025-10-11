#!/usr/bin/env python3
# make_course_hubs.py — generate docs/courses/<slug>/index.html from sessions.json + files

from pathlib import Path
import json, re
from datetime import datetime

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
COURSES = DOCS / "courses"
SESSIONS_JSON = DOCS / "sessions.json"

COURSE_TITLES = {
    "aha-bls-provider": "BLS Provider (AHA)",
    "aha-acls-provider": "ACLS Provider (AHA)",
    "aha-pals-provider": "PALS Provider (AHA)",
    "aha-heartsaver-first-aid-cpr-aed": "Heartsaver First Aid/CPR/AED (AHA)",
    "hsi-first-aid-cpr-aed": "First Aid/CPR/AED (HSI)",
}

HOVN = "https://www.hovn.app/910cpr/schedule"

STYLE = """
body{font-family:system-ui,Arial,sans-serif;margin:0;background:linear-gradient(180deg,#fff,#eef6ff);}
.wrap{max-width:980px;margin:0 auto;padding:24px 16px;}
.card{background:#fff;border-radius:16px;box-shadow:0 6px 24px rgba(0,0,0,.06);padding:18px 18px;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
a.cardlink{display:block;padding:12px;border-radius:12px;background:#fff;text-decoration:none;color:#111;box-shadow:0 6px 20px rgba(0,0,0,.06)}
a.cardlink:hover{box-shadow:0 10px 24px rgba(0,0,0,.1)}
.btn{display:inline-block;padding:12px 16px;border-radius:10px;background:#0b63e6;color:#fff;text-decoration:none}
small{color:#4a5568}
"""

def group_by_course(items):
    g = {}
    for it in items:
        g.setdefault(it["course_slug"], []).append(it)
    for k in g:
        g[k] = sorted(g[k], key=lambda x: x["start"])
    return g

def human_date(iso):
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%a, %b %d • %I:%M %p").lstrip("0").replace(" 0", " ")

def page(course_slug, entries):
    title = COURSE_TITLES.get(course_slug, course_slug.replace("-", " ").title())
    cards = []
    for it in entries[:24]:  # first 24 upcoming
        cards.append(f"<a class='cardlink' href='{it['url']}'><strong>{human_date(it['start'])}</strong><br><small>{it['city']}, {it['state']}</small></a>")
    grid = "<div class='grid'>" + "".join(cards) + "</div>" if cards else "<p><em>No upcoming classes. See HOVN schedule below.</em></p>"
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Upcoming Classes</title>
<link rel="canonical" href="https://www.910cpr.com/courses/{course_slug}/">
<meta name="robots" content="index,follow">
<style>{STYLE}</style>
</head>
<body>
<main class="wrap">
  <div class="card">
    <h1>{title}</h1>
    <p><small>Live availability updates on HOVN</small></p>
    {grid}
    <p style="margin-top:12px"><a class="btn" href="{HOVN}">See full schedule on HOVN</a></p>
  </div>
</main>
</body></html>
"""

def main():
    COURSES.mkdir(parents=True, exist_ok=True)
    if not SESSIONS_JSON.exists():
        print(f"Missing {SESSIONS_JSON}. Run build_from_hovn.py first.")
        return
    data = json.loads(SESSIONS_JSON.read_text(encoding="utf-8"))
    items = data.get("items", [])
    groups = group_by_course(items)
    count = 0
    for slug, entries in groups.items():
        out = COURSES / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(slug, entries), encoding="utf-8")
        count += 1
    print(f"Wrote {count} course hubs under {COURSES}")

if __name__ == "__main__":
    main()
