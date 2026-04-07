from __future__ import annotations
import argparse, json, html
from collections import defaultdict
from pathlib import Path
from datetime import datetime

TOPIC_LABELS={"bls":"BLS","acls":"ACLS","pals":"PALS","heartsaver":"Heartsaver","first-aid":"First Aid","red-cross":"Red Cross","hsi":"HSI","uscg":"USCG / Coast Guard","instructor":"Instructor Courses","family-friends":"Family & Friends","stop-the-bleed":"Stop the Bleed","aed":"AED / Maintenance","misc":"Other Courses"}
def fmt(iso):
    try: return datetime.fromisoformat(iso).strftime("%B %d, %Y at %I:%M %p").replace(" 0"," ")
    except Exception: return iso or ""
def shell(title, body):
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><meta name="robots" content="index,follow"><style>:root{{--bg:#eef4f8;--card:#fff;--text:#1f2937;--muted:#6b7280;--accent:#2563eb;--border:#dbe4ee}}*{{box-sizing:border-box}}body{{margin:0;font-family:Arial,sans-serif;background:linear-gradient(180deg,#f8fbfd 0%,var(--bg) 100%);color:var(--text)}}.wrap{{max-width:1200px;margin:0 auto;padding:20px 18px 50px}}.hero,.card{{background:var(--card);border:1px solid var(--border);border-radius:20px;box-shadow:0 8px 24px rgba(15,23,42,.06)}}.hero{{padding:26px;margin-bottom:22px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}}.card{{padding:18px}}h1{{margin:0 0 8px;font-size:30px}}h2{{margin:0 0 12px;font-size:22px}}p,li{{line-height:1.45}}.muted{{color:var(--muted)}}a{{color:var(--accent);text-decoration:none}}a:hover{{text-decoration:underline}}.preview-list{{list-style:none;padding:0;margin:12px 0 0}}.preview-list li{{margin:0 0 9px;padding-bottom:9px;border-bottom:1px dashed var(--border)}}.preview-list li:last-child{{border-bottom:0}}</style></head><body><div class="wrap">{body}</div></body></html>"""
def write(p: Path, title, body): p.write_text(shell(title, body), encoding="utf-8")
def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--schedule-json", required=True)
    ap.add_argument("--output-html", required=True)
    args=ap.parse_args()
    data=json.loads(Path(args.schedule_json).read_text(encoding="utf-8"))
    sessions=data.get("sessions", [])
    by_topic=defaultdict(list); by_loc=defaultdict(list)
    for s in sessions: by_topic[s.get("topic") or "misc"].append(s); by_loc[s.get("location") or "Unknown"].append(s)
    topic_cards=[]; loc_cards=[]
    for t,items in sorted(by_topic.items(), key=lambda kv:(-len(kv[1]), kv[0])):
        prev="".join(f'<li><a href="{html.escape(s["class_page"])}">{html.escape(s["title"])}</a> <span class="muted">• {html.escape(fmt(s.get("start")))}' + '</span></li>' for s in sorted(items, key=lambda s:s.get("start") or "")[:6])
        topic_cards.append(f'<section class="card"><h2>{html.escape(TOPIC_LABELS.get(t,t.title()))}</h2><div class="muted">{len(items)} sessions</div><ul class="preview-list">{prev}</ul></section>')
    for label,items in sorted(by_loc.items(), key=lambda kv:(-len(kv[1]), kv[0]))[:12]:
        prev="".join(f'<li><a href="{html.escape(s["class_page"])}">{html.escape(s["title"])}</a> <span class="muted">• {html.escape(fmt(s.get("start")))}' + '</span></li>' for s in sorted(items, key=lambda s:s.get("start") or "")[:6])
        loc_cards.append(f'<section class="card"><h2>{html.escape(label)}</h2><div class="muted">{len(items)} sessions</div><ul class="preview-list">{prev}</ul></section>')
    body=f'<div class="hero"><h1>Find Your CPR Class</h1><p class="muted">Browse public 910CPR sessions by course type or by location.</p></div><div><h2>Browse by Course</h2><div class="grid">{"".join(topic_cards)}</div></div><div><h2>Browse by Location</h2><div class="grid">{"".join(loc_cards)}</div></div>'
    p=Path(args.output_html); p.parent.mkdir(parents=True, exist_ok=True); write(p,"CPR Class Schedule | 910CPR", body)
    print(f"Wrote {p}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
