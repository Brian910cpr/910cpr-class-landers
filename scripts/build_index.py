from __future__ import annotations
import argparse, json, html
from collections import defaultdict
from pathlib import Path
from datetime import datetime

TOPIC_LABELS={"bls":"BLS","acls":"ACLS","pals":"PALS","heartsaver":"Heartsaver","first-aid":"First Aid","red-cross":"Red Cross","hsi":"HSI","uscg":"USCG / Coast Guard","instructor":"Instructor Courses","family-friends":"Family & Friends","stop-the-bleed":"Stop the Bleed","aed":"AED / Maintenance","misc":"Other Courses"}

def ensure(p: Path): p.mkdir(parents=True, exist_ok=True)
def fmt(iso):
    try: return datetime.fromisoformat(iso).strftime("%B %d, %Y at %I:%M %p").replace(" 0"," ")
    except Exception: return iso or ""
def shell(title, body):
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><meta name="robots" content="index,follow"><style>:root{{--bg:#eef4f8;--card:#fff;--text:#1f2937;--muted:#6b7280;--accent:#2563eb;--border:#dbe4ee}}*{{box-sizing:border-box}}body{{margin:0;font-family:Arial,sans-serif;background:linear-gradient(180deg,#f8fbfd 0%,var(--bg) 100%);color:var(--text)}}.wrap{{max-width:1200px;margin:0 auto;padding:20px 18px 50px}}.hero,.card{{background:var(--card);border:1px solid var(--border);border-radius:20px;box-shadow:0 8px 24px rgba(15,23,42,.06)}}.hero{{padding:26px;margin-bottom:22px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}}.card{{padding:18px}}h1{{margin:0 0 8px;font-size:30px}}h2{{margin:0 0 12px;font-size:22px}}h3{{margin:0 0 10px;font-size:18px}}p,li{{line-height:1.45}}.muted{{color:var(--muted)}}a{{color:var(--accent);text-decoration:none}}a:hover{{text-decoration:underline}}.button{{display:inline-block;padding:11px 15px;background:#5f6f82;color:#fff;border-radius:12px;font-weight:700;text-decoration:none}}.button:hover{{background:#526170;text-decoration:none}}.preview-list{{list-style:none;padding:0;margin:12px 0 0}}.preview-list li{{margin:0 0 9px;padding-bottom:9px;border-bottom:1px dashed var(--border)}}.preview-list li:last-child{{border-bottom:0}}</style></head><body><div class="wrap">{body}</div></body></html>"""
def write(p: Path, title, body):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(shell(title, body), encoding="utf-8")

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--schedule-json", required=True)
    ap.add_argument("--output-dir", required=True)
    args=ap.parse_args()
    data=json.loads(Path(args.schedule_json).read_text(encoding="utf-8"))
    sessions=data.get("sessions", []); courses=data.get("courses", [])
    docs=Path(args.output_dir)
    for d in ["topics","topics-year","years","locations","courses","data"]: ensure(docs/d)
    by_topic=defaultdict(list); by_year=defaultdict(list); by_loc=defaultdict(list); by_ty=defaultdict(list)
    for s in sessions:
        t=s.get("topic") or "misc"; y=str(s.get("year") or "unknown"); l=s.get("location_slug") or "unknown-location"
        by_topic[t].append(s); by_year[y].append(s); by_loc[l].append(s); by_ty[(t,y)].append(s)
    topic_cards="".join(f'<section class="card"><h3>{html.escape(TOPIC_LABELS.get(t,t.title()))}</h3><p class="muted">{len(v)} session pages</p><p><a class="button" href="topics/{t}.html">Open hub</a></p></section>' for t,v in sorted(by_topic.items()))
    year_cards="".join(f'<section class="card"><h3>{html.escape(y)}</h3><p class="muted">{len(v)} session pages</p><p><a class="button" href="years/{y}.html">Open year</a></p></section>' for y,v in sorted(by_year.items()))
    loc_cards="".join(f'<section class="card"><h3>{html.escape(v[0].get("location") or k)}</h3><p class="muted">{len(v)} session pages</p><p><a class="button" href="locations/{k}.html">Open location</a></p></section>' for k,v in sorted(by_loc.items(), key=lambda kv:(-len(kv[1]), kv[0]))[:20])
    write(docs/"index.html","Structured Index System | 910CPR",f'<div class="hero"><h1>Structured Index System for Classes and Courses</h1><p class="muted">This layer adds organized hub pages that point into the generated docs pages.</p><p><strong>Coverage:</strong> {len(courses)} course records and {len(sessions)} session records.</p></div><div><h2>Browse by topic</h2><div class="grid">{topic_cards}</div></div><div><h2>Browse by year</h2><div class="grid">{year_cards}</div></div><div><h2>Browse by location</h2><div class="grid">{loc_cards}</div></div><div><section class="card"><h2>Course Record Directory</h2><p><a class="button" href="courses/all-courses.html">Open all course records</a></p></section></div>')
    for t,items in by_topic.items():
        lis="".join(f'<li><a href="../{html.escape(s["class_page"])}">{html.escape(s["title"])}</a> <span class="muted">• {html.escape(s.get("location") or "")} • {html.escape(fmt(s.get("start")))}' + '</span></li>' for s in sorted(items, key=lambda s:s.get("start") or "")[:50])
        years="".join(f'<li><a href="../topics-year/{t}-{y}.html">{html.escape(TOPIC_LABELS.get(t,t.title()))} {y}</a></li>' for y in sorted({str(s.get("year") or "unknown") for s in items}))
        write(docs/"topics"/f"{t}.html",f"{TOPIC_LABELS.get(t,t.title())} | 910CPR",f'<div class="hero"><h1>{html.escape(TOPIC_LABELS.get(t,t.title()))}</h1><p class="muted">{len(items)} sessions in this topic bucket.</p></div><div class="card"><h2>By year</h2><ul>{years}</ul></div><div class="card"><h2>Preview sessions</h2><ul class="preview-list">{lis}</ul></div>')
    for y,items in by_year.items():
        lis="".join(f'<li><a href="../{html.escape(s["class_page"])}">{html.escape(s["title"])}</a> <span class="muted">• {html.escape(s.get("location") or "")}</span></li>' for s in sorted(items, key=lambda s:s.get("start") or "")[:80])
        write(docs/"years"/f"{y}.html",f"{y} Sessions | 910CPR",f'<div class="hero"><h1>{html.escape(y)}</h1><p class="muted">{len(items)} sessions in this year bucket.</p></div><div class="card"><ul class="preview-list">{lis}</ul></div>')
    for (t,y),items in by_ty.items():
        lis="".join(f'<li><a href="../{html.escape(s["class_page"])}">{html.escape(s["title"])}</a> <span class="muted">• {html.escape(s.get("location") or "")}</span></li>' for s in sorted(items, key=lambda s:s.get("start") or "")[:80])
        lab=TOPIC_LABELS.get(t,t.title())
        write(docs/"topics-year"/f"{t}-{y}.html",f"{lab} {y} | 910CPR",f'<div class="hero"><h1>{html.escape(lab)} {html.escape(y)}</h1><p class="muted">{len(items)} sessions in this topic and year bucket.</p></div><div class="card"><ul class="preview-list">{lis}</ul></div>')
    for k,items in by_loc.items():
        label=items[0].get("location") or k
        lis="".join(f'<li><a href="../{html.escape(s["class_page"])}">{html.escape(s["title"])}</a> <span class="muted">• {html.escape(fmt(s.get("start")))}' + '</span></li>' for s in sorted(items, key=lambda s:s.get("start") or "")[:80])
        write(docs/"locations"/f"{k}.html",f"{label} | 910CPR",f'<div class="hero"><h1>{html.escape(label)}</h1><p class="muted">{len(items)} sessions in this location bucket.</p></div><div class="card"><ul class="preview-list">{lis}</ul></div>')
    course_lis="".join(f'<li>{html.escape(c.get("name") or c.get("meta_key") or c.get("slug") or "")} <span class="muted">• {html.escape(c.get("family") or "")} • {html.escape(c.get("certifying_body") or "")}</span></li>' for c in sorted(courses, key=lambda c:(c.get("family") or "", c.get("name") or "")))
    write(docs/"courses"/"all-courses.html","Course Record Directory | 910CPR",f'<div class="hero"><h1>Course Record Directory</h1><p class="muted">{len(courses)} course records found in the current course export.</p></div><div class="card"><ul class="preview-list">{course_lis}</ul></div>')
    (docs/"data"/"schedule.json").write_text(Path(args.schedule_json).read_text(encoding="utf-8"), encoding="utf-8")
    (docs/"STRUCTURE.txt").write_text("This docs bundle contains index.html, topics, topics-year, years, locations, and a course record directory.\n", encoding="utf-8")
    print(f"Wrote structured index pages to {docs}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
