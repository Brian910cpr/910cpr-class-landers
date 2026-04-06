from pathlib import Path

repo_root = Path(r"D:\Users\ten77\Documents\GitHub\910cpr-class-landers")
docs_root = repo_root / "docs"

base_url = "https://www.910cpr.com"
output_file = docs_root / "sitemap.xml"

folders = [
    ("classes", docs_root / "classes"),
    ("courses", docs_root / "courses"),
]

urls = []

for url_prefix, folder in folders:
    if folder.exists():
        for file in sorted(folder.glob("*.html")):
            urls.append(f"{base_url}/{url_prefix}/{file.name}")
    else:
        print(f"Missing folder: {folder}")

with open(output_file, "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for url in urls:
        f.write("  <url>\n")
        f.write(f"    <loc>{url}</loc>\n")
        f.write("  </url>\n")
    f.write("</urlset>\n")

print(f"Generated {len(urls)} URLs")
print(f"Saved to: {output_file}")