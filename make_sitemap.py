# make_sitemap.py  — generates docs/sitemap.xml
import argparse, datetime, re, xml.etree.ElementTree as ET
from pathlib import Path

LEGACY = re.compile(r'^(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})_([^_]+)_(.+?)_([a-z0-9\-]+)_[a-z0-9]+\.html$')
CUID   = re.compile(r'^([a-z0-9]{10,})_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})_([a-z0-9\-]+)_([a-z0-9\-]+)_[a-z0-9]+\.html$')

def iso8601(dt): 
    # XML sitemaps prefer full ISO timestamps with Z (UTC) or local without tz
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

def guess_lastmod_from_name(name: str, mtime: float):
    """Returns (lastmod_dt, priority) by parsing dates from filename when possible."""
    # default to file mtime
    dt = datetime.datetime.fromtimestamp(mtime)
    pr = 0.5
    m = CUID.match(name) or LEGACY.match(name)
    if m:
        parts = m.groups()
        if len(parts) == 5:  # CUID pattern -> (cuid, ymd, hh-mm, city, state)
            ymd, hhmm = parts[1], parts[2]
        else:                # LEGACY pattern -> (ymd, hh-mm, course_slug, city, state)
            ymd, hhmm = parts[0], parts[1]
        try:
            dt = datetime.datetime.strptime(f"{ymd} {hhmm.replace('-',':')}", "%Y-%m-%d %H:%M")
            pr = 0.8  # sessions are important
        except Exception:
            pass
    return dt, pr

def add_url(urlset, loc, lastmod=None, priority=None, changefreq=None):
    url = ET.SubElement(urlset, "url")
    ET.SubElement(url, "loc").text = loc
    if lastmod:   ET.SubElement(url, "lastmod").text = lastmod
    if changefreq:ET.SubElement(url, "changefreq").text = changefreq
    if priority is not None: ET.SubElement(url, "priority").text = f"{priority:.1f}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="docs", help="Path to site docs/ root")
    ap.add_argument("--base", required=True, help="Absolute site base URL, e.g. https://www.910cpr.com")
    ap.add_argument("--out", default="sitemap.xml", help="Output filename (relative to docs/)")
    args = ap.parse_args()

    docs = Path(args.docs)
    base = args.base.rstrip("/")
    out  = docs / args.out

    urlset = ET.Element("urlset", attrib={"xmlns":"http://www.sitemaps.org/schemas/sitemap/0.9"})

    def rel_to_url(p: Path) -> str:
        rel = p.relative_to(docs).as_posix()
        return f"{base}/{rel}"

    # Home + hubs
    for rel in ["index.html", "courses/index.html", "locations/index.html"]:
        fp = docs / rel
        if fp.exists():
            add_url(urlset, rel_to_url(fp), iso8601(datetime.datetime.fromtimestamp(fp.stat().st_mtime)), 0.6, "daily")

    # Course pages
    for fp in (docs / "courses").glob("*.html"):
        if fp.name.lower() == "index.html": continue
        add_url(urlset, rel_to_url(fp), iso8601(datetime.datetime.fromtimestamp(fp.stat().st_mtime)), 0.7, "daily")

    # Location pages
    loc_dir = docs / "locations"
    if loc_dir.exists():
        for fp in loc_dir.glob("*.html"):
            if fp.name.lower() == "index.html": continue
            add_url(urlset, rel_to_url(fp), iso8601(datetime.datetime.fromtimestamp(fp.stat().st_mtime)), 0.6, "weekly")

    # Session fliers (important; infer lastmod from the embedded date if possible)
    fl_dir = docs / "fliers"
    if fl_dir.exists():
        for fp in fl_dir.glob("*.html"):
            lm_dt, pr = guess_lastmod_from_name(fp.name, fp.stat().st_mtime)
            add_url(urlset, rel_to_url(fp), iso8601(lm_dt), pr, "daily")

    # Write pretty XML
    ET.indent(urlset)  # Python 3.9+
    out.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(urlset, encoding="unicode"), encoding="utf-8")
    print(f"Wrote {out} with {len(list(urlset))} URLs")

if __name__ == "__main__":
    main()
