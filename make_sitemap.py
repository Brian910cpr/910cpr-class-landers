# make_sitemap.py
import datetime
from pathlib import Path

BASE = "https://www.910cpr.com"
ROOT = Path(__file__).resolve().parent
FLIERS = ROOT / "docs" / "fliers"
OUT   = ROOT / "docs" / "sitemap.xml"

def main():
    urls = []
    hubs = ["/", "/wilmington/", "/burgaw/", "/bls/", "/families/", "/workplace/"]
    for h in hubs:
        urls.append(f"{BASE}{h}")
    for fp in sorted(FLIERS.glob("*.html")):
        urls.append(f"{BASE}/fliers/{fp.name}")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    items = "\n".join([f"  <url><loc>{u}</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq></url>" for u in urls])
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>\n'
    OUT.write_text(xml, encoding="utf-8")

if __name__ == "__main__":
    main()
