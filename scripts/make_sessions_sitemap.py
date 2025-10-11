#!/usr/bin/env python3
# make_sessions_sitemap.py — emit docs/sitemap-sessions.xml for FUTURE sessions only

from pathlib import Path
from datetime import datetime
import re

REPO = Path(__file__).resolve().parents[1]
SESS = REPO / "docs" / "sessions"
OUT  = REPO / "docs" / "sitemap-sessions.xml"

BASE = "https://www.910cpr.com/sessions/"
NOW  = datetime.now().astimezone()
LOCAL_TZ = NOW.tzinfo

def parse_from_filename(name: str):
    m = re.match(r"(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-", name)
    if not m: return None
    dt = datetime.strptime(f"{m.group(1)} {m.group(2)}:{m.group(3)}", "%Y-%m-%d %H:%M")
    return dt.replace(tzinfo=LOCAL_TZ)

def main():
    urls = []
    SESS.mkdir(parents=True, exist_ok=True)
    for p in sorted(SESS.glob("*.html")):
        dt = parse_from_filename(p.name)
        if dt and dt >= NOW.replace(second=0, microsecond=0):
            urls.append(f"  <url><loc>{BASE}{p.name}</loc></url>")

    xml = "<?xml version='1.0' encoding='UTF-8'?>\n" \
          "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n" + \
          "\n".join(urls) + "\n</urlset>\n"
    OUT.write_text(xml, encoding="utf-8")
    print(f"Wrote {OUT} with {len(urls)} future urls")

if __name__ == "__main__":
    main()
