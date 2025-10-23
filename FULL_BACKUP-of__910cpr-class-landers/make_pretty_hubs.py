import argparse, csv, re
from pathlib import Path

def slug(s:str)->str: return re.sub(r'[^a-z0-9]+','-', (s or '').strip().lower()).strip('-')
def infer_family(text:str)->str:
    t=(text or "").upper()
    if "BLS" in t or "BASIC LIFE SUPPORT" in t: return "BLS"
    if "ACLS" in t or "ADVANCED CARDIAC" in t:  return "ACLS"
    if "PALS" in t or "PEDIATRIC ADVANCED" in t:return "PALS"
    return "HEARTSAVER"

def pitch_from(fam, cert, fmt):
    cert=(cert or "").upper(); fmt=(fmt or "").upper()
    base = {"BLS":"Adult/child/infant CPR/AED; airway & team dynamics.",
            "ACLS":"Cardiac arrest & peri-arrest, rhythm, airway, team leadership.",
            "PALS":"Pediatric assessment, resp/shock, arrest algorithms.",
            "HEARTSAVER":"Workplace First Aid/CPR/AED; OSHA/client-accepted."}[fam]
    bits=[]
    if "HEARTCODE" in fmt or "BLENDED" in fmt: bits.append("HeartCode/Blended")
    if "AHA" in cert: bits.append("Same-day eCard")
    if cert: bits.append(f"{cert} accepted")
    return base + (" • " + " • ".join(bits) if bits else "")

def read_courses_csv(path: Path):
    rows=[]
    with path.open(newline='', encoding="utf-8-sig") as f:
        r=csv.DictReader(f)
        for row in r:
            status=(row.get("status") or "").strip().lower()
            if status in {"inactive","hidden","hide","off"}: continue
            label=(row.get("label") or "").strip()
            course=(row.get("course") or "").strip()
            cuid =(row.get("cuid") or "").strip()
            cert =(row.get("certification") or "").strip()
            fmt  =(row.get("format") or "").strip()
            price=(row.get("price") or "").strip()
            ctype=(row.get("type") or "").strip()
            link =(row.get("link") or "").strip()
            if not cuid: continue
            fam=infer_family(label or course)
            rows.append({
                "short": label or course, "long": course or label,
                "family": fam, "pitch": pitch_from(fam, cert, fmt),
                "hovn_url": link, "price": price, "format": fmt,
                "cert": cert, "cuid": cuid, "ctype": ctype,
            })
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--template", default="templates/course_hub.html")
    ap.add_argument("--docs", default="docs")
    ap.add_argument("--feed-url", default="/periscope_full.json")
    ap.add_argument("--courses", default="course-offerings.csv")
    args=ap.parse_args()

    tpl=Path(args.template).read_text(encoding="utf-8")
    outdir=Path(args.docs)/"courses"; outdir.mkdir(parents=True, exist_ok=True)

    csv_path=Path(args.courses)
    if not csv_path.exists():
        raise FileNotFoundError(f"courses CSV not found: {csv_path} (expected: label,course,cuid,certification,format,price,type,status,link)")
    courses=read_courses_csv(csv_path)
    if not courses: raise SystemExit("No active rows with cuid found in course-offerings.csv")

    # Build each course page (cuid URL) + slug alias redirect for backwards links
    for c in courses:
        slug_name=slug(c["short"])
        html=(tpl.replace("{COURSE_SHORT}", c["short"])
                 .replace("{COURSE_LONG}", c["long"])
                 .replace("{COURSE_PITCH}", c["pitch"])
                 .replace("{FAMILY}", c["family"])
                 .replace("{HOVN_COURSE_URL}", c["hovn_url"])
                 .replace("{FEED_URL}", args.feed_url))
        (outdir/f"{c['cuid']}.html").write_text(html, encoding="utf-8")

        # slug alias → meta refresh to the cuid page
        alias=f"""<!doctype html><meta http-equiv="refresh" content="0; url='/courses/{c['cuid']}.html'"><link rel="canonical" href="/courses/{c['cuid']}.html">"""
        (outdir/f"{slug_name}.html").write_text(alias, encoding="utf-8")

    # Courses index links go to cuid URLs
    cards=[]
    for c in courses:
        badges=[]
        if c["cert"]: badges.append(c["cert"])
        if c["format"]: badges.append(c["format"])
        if c["price"]: badges.append(f"${c['price']}")
        bhtml=" ".join(f"<span style='display:inline-block;border:1px solid #e5e7eb;border-radius:999px;padding:4px 8px;font-size:12px;background:#f8fbff;margin-right:6px'>{b}</span>" for b in badges)
        cards.append(f"""
        <article class="card">
          <h2 style="margin:6px 0">{c['short']} — {c['long']}</h2>
          <p style="color:#3f4753;margin:6px 0">{c['pitch']}</p>
          <div style="margin:6px 0">{bhtml}</div>
          <div style="display:flex;gap:10px;flex-wrap:wrap">
            <a class="timechip" href="/courses/{c['cuid']}.html">See dates & book</a>
            <a class="timechip" href="{c['hovn_url']}">All on HOVN</a>
          </div>
        </article>""")
    hub=f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Courses — 910CPR</title>
<style>:root{{--bg:#f8fafc;--text:#0f172a;--line:#e5e7eb}}html,body{{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}}
.wrap{{max-width:1100px;margin:0 auto;padding:22px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin:10px 0}}
.timechip{{display:inline-block;border:1px solid var(--line);background:#f9fbff;padding:6px 10px;border-radius:10px;text-decoration:none}}</style></head>
<body><div class="wrap">
  <h1 style="margin:.25rem 0;font-size:clamp(24px,4vw,34px)">Find Your Course</h1>
  {''.join(cards)}
</div></body></html>"""
    (outdir/"index.html").write_text(hub, encoding="utf-8")
    print(f"Built courses ({len(courses)}) → {outdir}")

if __name__=="__main__": main()
