# make_sitemap.py — writes docs/sitemap.xml with date-only <lastmod>
import argparse, datetime, re, xml.etree.ElementTree as ET
from pathlib import Path

LEGACY = re.compile(r'^(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})_([^_]+)_(.+?)_([a-z0-9\-]+)_[a-z0-9]+\.html$')
CUID   = re.compile(r'^([a-z0-9]{10,})_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})_([a-z0-9\-]+)_([a-z0-9\-]+)_[a-z0-9]+\.html$')

def lastmod_date(dt: datetime.datetime) -> str:
    return dt.date().isoformat()  # YYYY-MM-DD (Google-safe)

def guess_lastmod_from_name(name: str, mtime: float) -> tuple[datetime.datetime, float]:
    """Return (date_for_lastmod, priority). Falls back to file mtime."""
    dt = datetime.datetime.fromtimestamp(mtime)
    pr = 0.5
    m = CUID.match(name) or LEGACY.match(name)
    if m:
        parts = m.groups()
        if len(parts) == 5:   # CUID
            ymd, hhmm = parts[1], parts[2]
        else:                 # LEGACY
            ymd, hhmm = parts[0], parts[1]
        try:
            dt = datetime.datetime.strptime(f"{ymd} {hhmm.replace('-',':')}", "%Y-%m-%d %H:%M")
            pr = 0.8
        except Exception:
            pass
    return dt, pr

def add_url(urlset, loc, lastmod_dt: datetime.datetime, priority=None, changefreq=None):
    url = ET.SubElement(urlset, "url")
    ET.SubElement(url, "loc").text = loc
    ET.SubElement(url, "lastmod").text = lastmod_date(lastmod_dt)
    if changefreq: ET.SubElement(url, "changefreq").text = changefreq
    if priority is not None: ET.SubElement(url, "priority").text = f"{priority:.1f}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="docs")
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", default="sitemap.xml")
    args = ap.parse_args()

    docs = Path(args.docs)
    base = args.base.rstrip("/")
    out  = docs / args.out

    urlset = ET.Element("urlset", attrib={"xmlns":"http://www.sitemaps.org/schemas/sitemap/0.9"})

    def loc(fp: Path) -> str:
        return f"{base}/{fp.relative_to(docs).as_posix()}"

    # Root & hubs
    for rel in ["index.html", "courses/index.html", "locations/index.html"]:
        fp = docs / rel
        if fp.exists():
            add_url(urlset, loc(fp), datetime.datetime.fromtimestamp(fp.stat().st_mtime), 0.6, "daily")

    # Course pages
    cdir = docs / "courses"
    if cdir.exists():
        for fp in sorted(cdir.glob("*.html")):
            if fp.name.lower() == "index.html": continue
            add_url(urlset, loc(fp), datetime.datetime.fromtimestamp(fp.stat().st_mtime), 0.7, "daily")

    # Location pages
    ldir = docs / "locations"
    if ldir.exists():
        for fp in sorted(ldir.glob("*.html")):
            if fp.name.lower() == "index.html": continue
            add_url(urlset, loc(fp), datetime.datetime.fromtimestamp(fp.stat().st_mtime), 0.6, "weekly")

    # Session fliers
    fdir = docs / "fliers"
    if fdir.exists():
        for fp in sorted(fdir.glob("*.html")):
            lm_dt, pr = guess_lastmod_from_name(fp.name, fp.stat().st_mtime)
            add_url(urlset, loc(fp), lm_dt, pr, "daily")

    ET.indent(urlset)  # pretty print
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(urlset, encoding="unicode")
    out.write_text(xml, encoding="utf-8")
    print(f"Wrote {out} with {len(list(urlset))} URLs")

if __name__ == "__main__":
    main()
