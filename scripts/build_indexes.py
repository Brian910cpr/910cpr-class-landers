import os, re, sys, time, json
from pathlib import Path
from urllib.parse import urljoin

SITE_BASE = "https://www.910cpr.com/"  # trailing slash required

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PERISCOPE = DOCS / "periscope_full.json"
SITEMAP = DOCS / "sitemap.xml"
ROBOTS = DOCS / "robots.txt"

COURSES_DIR = DOCS / "courses"
JOB_LANDERS_SRC = DOCS / "landers" / "job"
JOB_INDEX_OUT = DOCS / "job" / "index.html"

PRIMARY_KEYS = {"course_family","start","city","url"}
ALT_KEYS     = {"course","start_iso","city","enroll_url"}  # auto-convert

def fail(msg):
    print(f"[build_indexes] ERROR: {msg}")
    sys.exit(1)

def read_html_title(path: Path) -> str:
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"<title>(.*?)</title>", txt, re.IGNORECASE | re.DOTALL)
        if m:
            import re as _re
            return _re.sub(r"\s+", " ", m.group(1)).strip()
    except Exception:
        pass
    return path.stem.replace('-', ' ').title()

def rel_url_to_site(rel: str) -> str:
    if rel == "index.html":
        return SITE_BASE
    return urljoin(SITE_BASE, rel)

def lastmod_of(path: Path) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(path.stat().st_mtime))

def normalize_periscope_item(row):
    if PRIMARY_KEYS.issubset(row.keys()):
        return {
            "course_family": row["course_family"],
            "start": row["start"],
            "city": row["city"],
            "url": row["url"],
            **({"label": row.get("label")} if "label" in row else {})
        }
    if ALT_KEYS.issubset(row.keys()):
        course = (row.get("course") or "").upper()
        if "BLS" in course: fam = "BLS"
        elif "ACLS" in course: fam = "ACLS"
        elif "PALS" in course: fam = "PALS"
        elif "FIRST AID" in course or "FA" in course: fam = "FA"
        else: fam = "BLS"
        return {
            "course_family": fam,
            "start": row["start_iso"],
            "city": row["city"],
            "url": row["enroll_url"],
            **({"label": row.get("label")} if "label" in row else {})
        }
    raise ValueError("periscope item missing required keys")

def validate_periscope():
    if not PERISCOPE.exists():
        print("[build_indexes] periscope_full.json missing; writing empty []")
        PERISCOPE.write_text("[]", encoding="utf-8")
        return
    try:
        data = json.loads(PERISCOPE.read_text(encoding="utf-8") or "[]")
        if not isinstance(data, list):
            fail("periscope_full.json must be a JSON array")
        normalized = []
        for i, row in enumerate(data):
            if not isinstance(row, dict):
                fail(f"periscope_full.json item {i} must be an object")
            normalized.append(normalize_periscope_item(row))
        PERISCOPE.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        fail(f"periscope_full.json invalid JSON: {e}")

def write_course_index():
    if not COURSES_DIR.exists():
        print("[build_indexes] NOTE: /docs/courses not found; skipping course index")
        return
    items = []
    for p in sorted(COURSES_DIR.glob("*.html")):
        if p.name.lower() == "index.html":
            continue
        title = read_html_title(p)
        href = "/courses/" + p.name
        items.append((title, href, lastmod_of(p)))
    index_path = COURSES_DIR / "index.html"
    html = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<title>Courses | 910CPR</title>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "</head><body style='font-family:system-ui;margin:24px'>",
        "<h1>Courses</h1><ul>"
    ]
    for title, href, lm in items:
        html.append(f"<li><a href='{href}'>{title}</a> <small style='color:#666'>&nbsp;{lm}</small></li>")
    html += ["</ul></body></html>"]
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(html), encoding="utf-8")
    print(f"[build_indexes] wrote {index_path} ({len(items)} items)")

def write_job_index():
    if not JOB_LANDERS_SRC.exists():
        print("[build_indexes] NOTE: /docs/landers/job not found; skipping job index")
        return
    items = []
    for p in sorted(JOB_LANDERS_SRC.rglob("*.html")):
        if p.name.lower() == "index.html":
            continue
        title = read_html_title(p)
        rel = p.relative_to(DOCS).as_posix()
        href = "/" + rel
        items.append((title, href, lastmod_of(p)))
    out = JOB_INDEX_OUT
    html = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<title>Jobs & Occupations | 910CPR</title>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "</head><body style='font-family:system-ui;margin:24px'>",
        "<h1>Jobs & Occupations</h1><ul>"
    ]
    for title, href, lm in items:
        html.append(f"<li><a href='{href}'>{title}</a> <small style='color:#666'>&nbsp;{lm}</small></li>")
    html += ["</ul></body></html>"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(html), encoding="utf-8")
    print(f"[build_indexes] wrote {out} ({len(items)} items)")

def discover_pages():
    pages = []
    for p in DOCS.rglob("*.html"):
        parts = p.relative_to(DOCS).parts
        if any(part.startswith(".") for part in parts):
            continue
        if p.name.lower() == "404.html":
            continue
        rel = p.relative_to(DOCS).as_posix()
        url = rel_url_to_site(rel)
        pages.append((url, lastmod_of(p)))
    if (DOCS / "index.html").exists():
        pages.append((SITE_BASE, lastmod_of(DOCS / "index.html")))
    # de-dupe, sort
    seen = {}
    for url, lm in pages:
        seen[url] = lm
    return sorted(seen.items(), key=lambda x: x[0])

def write_sitemap(pages):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, lm in pages:
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")
        lines.append(f"    <lastmod>{lm}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>\n")
    SITEMAP.write_text("\n".join(lines), encoding="utf-8")
    print(f"[build_indexes] wrote {SITEMAP} with {len(pages)} URLs")

def write_robots():
    ROBOTS.write_text(
        f"User-agent: *\nAllow: /\nSitemap: {urljoin(SITE_BASE, 'sitemap.xml')}\n",
        encoding="utf-8"
    )
    print(f"[build_indexes] wrote {ROBOTS}")

def main():
    if not DOCS.exists():
        fail("docs/ not found")
    for must in ["index.html", "policies.html", "404.html"]:
        if not (DOCS / must).exists():
            print(f"[build_indexes] WARN: /docs/{must} not found (not fatal)")
    validate_periscope()
    write_course_index()
    write_job_index()
    pages = discover_pages()
    write_sitemap(pages)
    write_robots()
    print(f"[build_indexes] done: {len(pages)} pages in sitemap")

if __name__ == "__main__":
    main()
