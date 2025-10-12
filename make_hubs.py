import argparse, re, json, datetime
from pathlib import Path

STYLE="body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:0;padding:24px;color:#0a1b2a} .card{border:1px solid #dde8f5;border-radius:12px;padding:12px;background:#fff} .grid{display:grid;gap:10px}"

LEGACY = re.compile(r'^(\\d{4}-\\d{2}-\\d{2})_(\\d{2}-\\d{2})_([^_]+)_(.+?)_([a-z0-9\\-]+)_[a-z0-9]+\\.html$')
CUID   = re.compile(r'^([a-z0-9]{10,})_(\\d{4}-\\d{2}-\\d{2})_(\\d{2}-\\d{2})_([a-z0-9\\-]+)_([a-z0-9\\-]+)_[a-z0-9]+\\.html$')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base", default="https://www.910cpr.com")
    ap.add_argument("--docs", default="docs")
    args=ap.parse_args()

    docs=Path(args.docs); fliers=docs/"fliers"; out=docs/"courses"; out.mkdir(parents=True, exist_ok=True)
    buckets={}

    for fp in sorted(fliers.glob("*.html")):
        name=fp.name
        m=CUID.match(name)
        if m:
            cuid, ymd, hhmm, city, state = m.groups()
            key=("cuid", cuid)
        else:
            m=LEGACY.match(name)
            if not m: continue
            ymd, hhmm, course_slug, city, state = m.groups()
            key=("slug", course_slug)

        try: dt=datetime.datetime.strptime(f"{ymd} {hhmm.replace('-',':')}", "%Y-%m-%d %H:%M")
        except: dt=None
        buckets.setdefault(key, []).append({"file":name,"ymd":ymd,"hhmm":hhmm,"city":city,"state":state,"dt":dt})

    for key, items in buckets.items():
        items.sort(key=lambda x:(x["dt"] or datetime.datetime.max, x["file"]))
        if key[0]=="cuid":
            cuid=key[1]; title=f"{cuid.upper()} — Sessions"
            href=lambda it:f"{args.base}/fliers/{it['file']}"
            fname=f"{cuid}.html"
        else:
            slug=key[1]; title=f"{slug.upper()} — Sessions"
            href=lambda it:f"{args.base}/fliers/{it['file']}"
            fname=f"{slug}.html"
        schema=[{"@type":"ListItem","position":i+1,"url":href(it)} for i,it in enumerate(items)]
        cards=[f"<div class='card'><a href='{href(it)}'>{it['ymd']} {it['hhmm']} — {it['city']}, {it['state']}</a></div>" for it in items]
        html=f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>{title}</title><style>{STYLE}</style><script type='application/ld+json'>{json.dumps({'@context':'https://schema.org','@type':'ItemList','itemListElement':schema},separators=(',',':'))}</script></head><body><h1>{title}</h1><div class='grid'>{''.join(cards) or '<p>No sessions yet.</p>'}</div></body></html>"
        (out/fname).write_text(html, encoding="utf-8")

    print(f"Built hubs → {out}")

if __name__=="__main__": main()
