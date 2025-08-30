#!/usr/bin/env python3
import os, re, html, datetime, pathlib
BASE_URL = "https://www.910cpr.com"
JOB_SRC  = "landers/job"
COURSE_SRC = "courses"
OUT_JOB_INDEX, OUT_COURSE_INDEX, OUT_SITEMAP, OUT_ROBOTS = "job/index.html","courses/index.html","sitemap.xml","robots.txt"

def list_html(root): 
    root=pathlib.Path(root); 
    return sorted([p for p in root.rglob("*.html") if p.is_file()]) if root.exists() else []
def slug_from_job(p): 
    return p.parent.name.lower() if p.name.lower()=="index.html" and p.parent.name!="job" else p.stem.lower()
def title_from_file(p):
    try: txt=p.read_text(encoding="utf-8", errors="ignore")
    except: return None
    m=re.search(r"<title>(.*?)</title>", txt, re.I|re.S)
    return re.sub(r"\s+"," ",m.group(1)).strip() if m else None

def write_job_index(items):
    os.makedirs(os.path.dirname(OUT_JOB_INDEX), exist_ok=True)
    lis=[f'<li><a href="{html.escape(f"{BASE_URL}/job/{slug}")}">{html.escape(title or slug.title())}</a></li>' for slug,title in items] or ["<li>(none yet)</li>"]
    pathlib.Path(OUT_JOB_INDEX).write_text(f"""<!doctype html><html><head>
<meta charset="utf-8"><title>Who is CPR/BLS for? — Job Index | 910CPR</title>
<link rel="canonical" href="{BASE_URL}/job/"><meta name="robots" content="index,follow">
</head><body><h1>Who is CPR/BLS for? (Job Index)</h1><ul>
{chr(10).join(lis)}
</ul></body></html>""", encoding="utf-8")

def write_course_index(items):
    os.makedirs(os.path.dirname(OUT_COURSE_INDEX), exist_ok=True)
    lis=[f'<li><a href="{html.escape(f"{BASE_URL}/courses/{slug}.html")}">{html.escape(title or slug.upper())}</a></li>' for slug,title in items] or ["<li>(none yet)</li>"]
    pathlib.Path(OUT_COURSE_INDEX).write_text(f"""<!doctype html><html><head>
<meta charset="utf-8"><title>CPR & BLS Courses — Index | 910CPR</title>
<link rel="canonical" href="{BASE_URL}/courses/"><meta name="robots" content="index,follow">
</head><body><h1>Our CPR/First Aid Courses</h1><ul>
{chr(10).join(lis)}
</ul></body></html>""", encoding="utf-8")

def write_sitemap(job_urls, course_urls):
    today=datetime.date.today().isoformat()
    parts=[f"""  <url><loc>{html.escape(u)}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.6</priority></url>""" for u in (job_urls+course_urls)]
    pathlib.Path(OUT_SITEMAP).write_text(f"""<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(parts)}
</urlset>""", encoding="utf-8")

def write_robots(): pathlib.Path(OUT_ROBOTS).write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")

def main():
    job_files=list_html(JOB_SRC)
    job_items=[(slug_from_job(p), title_from_file(p) or f"CPR/BLS for {slug_from_job(p).title()}") for p in job_files]
    job_urls=[f"{BASE_URL}/job/{s}" for s,_ in job_items]

    course_files=[p for p in list_html(COURSE_SRC) if p.name.lower()!="index.html"]
    course_items=[(p.stem.lower(), title_from_file(p) or f"{p.stem.upper()} Course") for p in course_files]
    course_urls=[f"{BASE_URL}/courses/{s}.html" for s,_ in course_items]

    write_job_index(job_items); write_course_index(course_items)
    write_sitemap(job_urls, course_urls); write_robots()
    print("[ok] built indexes + sitemap + robots")

if __name__ == "__main__": main()
