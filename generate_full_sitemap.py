from pathlib import Path
from html import escape

REPO_ROOT = Path(r"D:\Users\ten77\Documents\GitHub\910cpr-class-landers")
DOCS_ROOT = REPO_ROOT / "docs"
BASE_URL = "https://www.910cpr.com"

OUTPUT_FILE = DOCS_ROOT / "sitemap.xml"
FOLDERS = [
    ("classes", DOCS_ROOT / "classes"),
    ("courses", DOCS_ROOT / "courses"),
]

def iter_html_urls():
    for url_prefix, folder in FOLDERS:
        if not folder.exists():
            print(f"Missing folder: {folder}")
            continue
        for file in sorted(folder.glob("*.html")):
            yield f"{BASE_URL}/{url_prefix}/{file.name}"

def main():
    urls = list(iter_html_urls())
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for url in urls:
            f.write("  <url>\n")
            f.write(f"    <loc>{escape(url)}</loc>\n")
            f.write("  </url>\n")
        f.write("</urlset>\n")
    print(f"Generated {len(urls)} URLs")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
