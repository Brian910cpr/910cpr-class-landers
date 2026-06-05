from pathlib import Path
import re

repo_root = Path(__file__).resolve().parents[1]
docs_root = repo_root / "docs"

base_url = "https://www.910cpr.com"
output_file = docs_root / "sitemap.xml"
canonical_file = docs_root / "data" / "canonical_schedule_from_class_report.json"

folders = [
    ("classes", docs_root / "classes"),
    ("courses", docs_root / "courses"),
]

excluded_relative_parts = {
    "proposed-sessions",
}


def has_noindex(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return bool(re.search(r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*noindex', text, flags=re.I))


def canonical_class_ids() -> set[str] | None:
    if not canonical_file.exists():
        return None
    try:
        import json

        payload = json.loads(canonical_file.read_text(encoding="utf-8"))
    except Exception:
        return None
    if payload.get("build", {}).get("source_mode") != "class_report_authoritative":
        return None
    return {str(session.get("session_id") or "").strip() for session in payload.get("sessions", []) if str(session.get("session_id") or "").strip()}


active_class_ids = canonical_class_ids()

urls = []

for url_prefix, folder in folders:
    if folder.exists():
        for file in sorted(folder.glob("*.html")):
            relative_parts = {part.lower() for part in file.relative_to(docs_root).parts}
            if relative_parts & excluded_relative_parts:
                continue
            if url_prefix == "classes" and active_class_ids is not None and file.stem not in active_class_ids:
                continue
            if has_noindex(file):
                continue
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
