
import os, re, sys, time, json
from pathlib import Path
from urllib.parse import urljoin

# ===== CONFIG =====
SITE_BASE = "https://www.910cpr.com/"  # trailing slash required

# Resolve /docs no matter where we run from
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PERISCOPE = DOCS / "periscope_full.json"
SITEMAP = DOCS / "sitemap.xml"
ROBOTS = DOCS / "robots.txt"

# Where generated pages normally live
COURSES_DIR = DOCS / "courses"
JOB_LANDERS_SRC = DOCS / "landers" / "job"
JOB_INDEX_OUT = DOCS / "job" / "index.html"

# Periscope schema (homepage widget safety)
PRIMARY_KEYS = {"course_family","start","city","url"}
ALT_KEYS     = {"course","start_iso","city","enroll_url"}  # auto-convert

# ===== UTIL =====
def fail(msg):
    print(f"[build_indexes] ERROR: {msg}")
    sys.exit(1)

def read_html_title(path: Path) -> str:
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"<title>(.*?)</title>", txt, re.IGNORECASE | re.DOTALL)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
    except Exception:
        pass
    # Fallback to filename
    return path.stem.replace("-", " ").title()

def rel_url_to_site(rel: str) -> str:
    # Pretty URLs:
    #  - index.html at root -> /
    #  - any /path/index.html -> /path/
    if rel == "index.html":
        return SITE_BASE
    if rel.endswith("/index.html"):
        return urljoin(SITE_BASE, rel[:-10])  # strip trailing "index.html"
    return urljoin(SITE_BASE, rel)

def lastmod_of(path: Path) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(path.stat().st_mtime))

# ===== PERISCOPE SAFETY =====
def normalize_periscope_item(row):
    # Accept either the homepage shape or an alternate and normalize to homepage shape.
    if PRIMARY_KEYS.issubset(row.keys()):
        out = {
            "course_family": row["course_family"],
            "start": row["start"],
            "city": row["city"],
            "url": row["url"],
        }
        if "label" in row and row["label"]:
            out["label"] = row["label"]
        return out
    if ALT_KEYS.issubset(row.keys()):
        course = (row.get("course") or "").upper()
        if "BLS" in course: fam = "BLS"
        elif "ACLS" in course: fam = "ACLS"
        elif "PALS" in course: fam = "PALS"
        elif "FIRST AID" in course or "FA" in course: fam = "FA"
        else: fam = "BLS"
        out = {
            "course_family": fam,
            "start": row["start_iso"],
            "city": row["city"],
            "url": row["enroll_url"],
        }
        if "label" in row and row["label"]:
            out["label"] = row["label"]
        return out
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

# ===== INDEX PAGES (HIDE WHEN EMPTY) =====
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
    if not items:
        if index_path.exists():
            index_path.unlink()
            print("[build_indexes] removed empty /docs/courses/index.html")
        return

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
        rel = p.relative_to(DOCS).as_posix()     # landers/job/xxx.html
        href = "/" + rel
        items.append((title, href, lastmod_of(p)))

    out = JOB_INDEX_OUT
    if not items:
        if out.exists():
            out.unlink()
            print("[build_indexes] removed empty /docs/job/index.html")
        return

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

# ===== SITEMAP + ROBOTS =====
def discover_pages():
    pages = []
    for p in DOCS.rglob("*.html"):
        rel_parts = p.relative_to(DOCS).parts
        # skip hidden dirs/files
        if any(part.startswith(".") for part in rel_parts):
            continue
        # exclude 404 from sitemap
        if p.name.lower() == "404.html":
            continue
        rel = p.relative_to(DOCS).as_posix()
        url = rel_url_to_site(rel)
        pages.append((url, lastmod_of(p)))

    # ensure homepage entry if index.html exists
    if (DOCS / "index.html").exists():
        pages.append((SITE_BASE, lastmod_of(DOCS / "index.html")))

    # de-dupe to latest lastmod and sort
    latest = {}
    for url, lm in pages:
        latest[url] = max(latest.get(url, "0000-00-00"), lm)
    pages = sorted(latest.items(), key=lambda x: x[0])
    return pages

def bump_folder_lastmod(pages):
    # For any folder URLs like /courses/ or /job/ set lastmod to the newest child page
    newest_child = {}
    for url, lm in pages:
        if url.endswith(".html"):
            folder = url.rsplit("/", 1)[0] + "/"
            newest_child[folder] = max(newest_child.get(folder, "0000-00-00"), lm)
    bumped = []
    for url, lm in pages:
        if url.endswith("/"):
            lm = max(lm, newest_child.get(url, lm))
        bumped.append((url, lm))
    return bumped

def write_sitemap(pages):
    lines = ['<?xml version="1.0" encoding="UTF-8?>',
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

# ===== MAIN =====
def main():
    if not DOCS.exists():
        fail("docs/ not found")

    # Friendly warnings for expected core pages
    for must in ["index.html", "policies.html", "404.html"]:
        if not (DOCS / must).exists():
            print(f"[build_indexes] WARN: /docs/{must} not found (not fatal)")

    # Safety net for homepage widget
    validate_periscope()

    # Generate index pages (only when there are items)
    write_course_index()
    write_job_index()

    # Global discover => sitemap
    pages = discover_pages()
    pages = bump_folder_lastmod(pages)
    write_sitemap(pages)

    # Robots
    write_robots()

    print(f"[build_indexes] done: {len(pages)} pages in sitemap")

if __name__ == "__main__":
    main()
