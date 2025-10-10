#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate individual session pages into an output folder (default: docs/classes).
Also supports aging banners for past sessions and optional course descriptions
pulled from a workbook (Excel).

Args:
  --sessions <csv>         sessions CSV (required)
  --workbook <xlsx>        optional, to enrich with course descriptions
  --template <html>        optional. If omitted, a built-in template is used
  --outdir <dir>           default: docs/classes
  --site-base <url>        absolute site base for canonical (default: "")
  --max-pages <n>          limit for debugging
  --emit-sitemaps          also write sitemap.xml in outdir
"""
import argparse, pathlib, re, json
from datetime import datetime, timezone
import pandas as pd

DEFAULT_OUTDIR = "docs/classes"

BUILTIN_TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>{page_title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{meta_description}">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%232563eb'/%3E%3Ctext x='32' y='40' text-anchor='middle' font-size='28' fill='white' font-family='Arial'%3E9%3C/text%3E%3C/svg%3E">
<style>
  :root{{--bg:#0b1220;--card:#0f172a;--text:#e5e7eb;--line:#1f2937;--muted:#9aa4af;--brand:#60a5fa}}
  html,body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,Segoe UI,Roboto,Arial,sans-serif}}
  .wrap{{max-width:860px;margin:0 auto;padding:22px}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}}
  .muted{{color:var(--muted)}}
  .btn{{display:inline-block;background:var(--brand);color:#0b1220;font-weight:800;padding:10px 14px;border-radius:10px;text-decoration:none}}
  .chips{{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}}
  .chip{{display:inline-block;padding:6px 10px;border-radius:9999px;background:rgba(96,165,250,.12);border:1px solid rgba(96,165,250,.4)}}
  .banner{{margin:10px 0 14px;padding:10px;border-radius:10px;border:1px solid #3b82f6;background:#0b2545}}
  h1{{margin:.3rem 0 0;font-size:clamp(22px,3.8vw,30px)}}
  h2{{margin:1rem 0 .5rem;font-size:clamp(18px,3vw,22px)}}
  .lede{{color:#cbd5e1}}
</style>
<script type="application/ld+json">
{json_ld}
</script>
</head>
<body>
<div class="wrap">
  <div class="card">
    <div class="muted">{breadcrumb}</div>
    <h1>{heading}</h1>
    {status_banner}
    <p class="lede">{lede}</p>
    <div class="chips">{meta_chips}</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 6px">
      <a class="btn" href="{register_url}">Register Now</a>
      <a class="btn" style="background:transparent;border:1px solid #3b82f6;color:#e5e7eb" href="{course_lander_url}">See upcoming {family} times</a>
    </div>
  </div>

  <div class="card" style="margin-top:14px">
    <h2>About this course</h2>
    {course_body}
  </div>

  <div class="card" style="margin-top:14px">
    <h2>Next available times</h2>
    <div id="next-times" class="chips"><span class="chip">Loading…</span></div>
  </div>

  <div class="muted" style="margin:18px 4px">© 910CPR</div>
</div>

<script>
(async () => {{
  const TRY = ["../periscope_full.json","../../periscope_full.json","/periscope_full.json"];
  let data = [];
  for (const u of TRY) {{
    try {{
      const r = await fetch(u, {{cache:"no-store"}});
      if (r.ok) {{ data = await r.json(); break; }}
    }} catch (_) {{}}
  }}
  const fam = "{family}".toUpperCase();
  const now = new Date();
  const items = data
    .map(x => ({{...x, _d: new Date((x.start||'').replace(' ','T')+':00')}}))
    .filter(x => x._d && x._d >= now && (String(x.course_family||'').toUpperCase()===fam))
    .sort((a,b) => a._d - b._d)
    .slice(0,6);

  const box = document.getElementById("next-times");
  if (!box) return;
  box.innerHTML = items.length
    ? items.map(x => {{
        const d = x._d; const mo = d.toLocaleString(undefined,{{month:'short'}});
        const day = String(d.getDate()).padStart(2,'0');
        let h=d.getHours(), m=d.getMinutes(), ap=h>=12?'p':'a'; h=h%12||12;
        const hm = m ? `${{h}}:${{String(m).padStart(2,'0')}}${{ap}}` : `${{h}}${{ap}}`;
        const label = `${{mo}} ${{day}}, ${{hm}} — ${{x.city||''}}`;
        return `<a class="chip" href="${{x.url||'#'}}">${{label}}</a>`;
      }}).join("")
    : "<span class='chip'>New dates posting—check back soon.</span>";
}})();
</script>
</body></html>
"""

def up(s): return (s or "").upper()

def family_from(text):
    t = up(text)
    if re.search(r'(^|[^A-Z])BLS([^A-Z]|$)|BASIC\s+LIFE\s+SUPPORT', t): return "BLS"
    if re.search(r'(^|[^A-Z])ACLS([^A-Z]|$)|ADVANCED\s+CARDIO', t):      return "ACLS"
    if re.search(r'(^|[^A-Z])PALS([^A-Z]|$)|PEDIATRIC\s+ADVANCED', t):   return "PALS"
    if re.search(r'HEARTSAVER|FIRST\s*AID|CPR\s*/?\s*AED', t):           return "FA"
    return ""

def load_workbook_map(xlsx_path):
    if not xlsx_path: return {}
    try:
        df = pd.read_excel(xlsx_path)
    except Exception:
        return {}
    cols = {c.lower(): c for c in df.columns}
    name_c = cols.get("course_name") or cols.get("name") or list(cols.values())[0]
    body_c = cols.get("long_description") or cols.get("description") or list(cols.values())[-1]
    fam_c  = cols.get("course_family") or cols.get("family")
    m = {}
    for _, r in df.iterrows():
        key = str(r.get(name_c, "")).strip()
        body = str(r.get(body_c, "")).strip()
        fam = str(r.get(fam_c, "")).strip()
        if key: m[key] = {"body": body, "family": fam}
    return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", required=True)
    ap.add_argument("--workbook", default="")
    ap.add_argument("--template", default="")
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR)
    ap.add_argument("--site-base", default="")
    ap.add_argument("--max-pages", type=int, default=0)
    ap.add_argument("--emit-sitemaps", action="store_true")
    args = ap.parse_args()

    outdir = pathlib.Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    # template
    tpl = pathlib.Path(args.template) if args.template else None
    template_html = BUILTIN_TEMPLATE if not tpl else tpl.read_text(encoding="utf-8")

    # workbook map
    wbmap = load_workbook_map(args.workbook)

    df = pd.read_csv(args.sessions)
    # column sniff
    cols = {c.lower(): c for c in df.columns}
    def col(*names):
        for n in names:
            if n in cols: return cols[n]
        for n in names:
            for k in cols:
                if n in k: return cols[k]
        return None

    c_start = col("start") or col("date","start_time","startdatetime")
    c_city  = col("city","location_city","town")
    c_url   = col("url","registration_url","register_url","hovn_url")
    c_title = col("title","session_title","name")
    c_course= col("course","program","course_name")
    c_cert  = col("certification","cert","credential")
    c_agency= col("agency","brand","program_agency")
    c_format= col("format","delivery","type")
    c_id    = col("id","session_id","event_id","key")

    pages = []
    now = datetime.now(timezone.utc).astimezone()

    for i, r in df.iterrows():
        if args.max_pages and len(pages) >= args.max_pages: break

        title = str(r.get(c_title, "") or r.get(c_course, "") or r.get(c_cert, "")).strip()
        course = str(r.get(c_course, "")).strip()
        cert = str(r.get(c_cert, "")).strip()
        agency = str(r.get(c_agency, "")).strip()
        format_ = str(r.get(c_format, "")).strip()
        city = str(r.get(c_city, "")).strip()
        url = str(r.get(c_url, "")).strip()
        sid = str(r.get(c_id, "") or f"row{i}").strip()

        start_raw = str(r.get(c_start, "")).strip()
        try:
            dt = pd.to_datetime(start_raw, errors="coerce")
            if pd.isna(dt): raise ValueError
            local_dt = dt.tz_localize(None)
        except Exception:
            local_dt = None

        fam = family_from(" ".join([title, course, cert, agency])) or "Course"
        # course description
        course_body = ""
        if course in wbmap and wbmap[course].get("body"):
            course_body = wbmap[course]["body"]
        elif title in wbmap and wbmap[title].get("body"):
            course_body = wbmap[title]["body"]
        else:
            course_body = "<p>Hands-on, instructor-led training with same-day eCards.</p>"

        # status banner
        status_banner = ""
        if local_dt:
            past = local_dt < now.replace(tzinfo=None)
            if past:
                status_banner = (
                    f'<div class="banner"><strong>This class has passed.</strong> '
                    f'See upcoming {fam} times below.</div>'
                )

        # chips
        chips = []
        if agency: chips.append(f'<span class="chip">{agency}</span>')
        if cert:   chips.append(f'<span class="chip">{cert}</span>')
        if format_:chips.append(f'<span class="chip">{format_}</span>')
        if city:   chips.append(f'<span class="chip">{city}</span>')
        meta_chips = "".join(chips)

        # text bits
        when_str = local_dt.strftime("%A, %B %d, %Y · %I:%M %p").lstrip("0") if local_dt else start_raw
        heading = f"{title or course} — {when_str} — {city}"
        lede = f"{course or title} in {city}. Same-day eCard. Small groups."

        # SEO
        page_title = f"{title or course} | {when_str} | {city} | 910CPR"
        meta_description = f"{course or title} on {when_str} in {city}. Register now or see the next available sessions."

        # canonical + lander
        slug_city = re.sub(r'[^a-z0-9]+','-', city.lower()).strip("-") or "local"
        slug_dt = local_dt.strftime("%Y-%m-%d_%H-%M") if local_dt else "session"
        filename = f"{slug_dt}_{sid}_{slug_city}.html"
        canonical = (args.site_base.rstrip("/") + "/classes/" + filename) if args.site_base else ""
        course_lander_url = f"/courses/{fam.lower()}/"  # adjust if your lander path differs

        # JSON-LD
        json_ld = {
          "@context": "https://schema.org",
          "@type": "Event",
          "name": title or course,
          "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
          "eventStatus": "https://schema.org/EventScheduled",
          "startDate": local_dt.strftime("%Y-%m-%dT%H:%M:00") if local_dt else start_raw,
          "location": {
            "@type": "Place",
            "name": city,
            "address": { "@type": "PostalAddress", "addressLocality": city, "addressRegion": "NC", "addressCountry": "US" }
          },
          "organizer": { "@type":"Organization","name":"910CPR","url":"https://www.910cpr.com" },
          "offers": { "@type":"Offer","url": url or course_lander_url, "availability":"https://schema.org/InStock" }
        }

        html = template_html.format(
            page_title=page_title,
            meta_description=meta_description,
            canonical=canonical,
            breadcrumb=f"{fam} · {city}",
            heading=heading,
            status_banner=status_banner,
            lede=lede,
            meta_chips=meta_chips,
            register_url=url or course_lander_url,
            course_lander_url=course_lander_url,
            course_body=course_body,
            family=fam,
            json_ld=json.dumps(json_ld, ensure_ascii=False, indent=2)
        )

        (outdir / filename).write_text(html, encoding="utf-8")
        pages.append(filename)

    print(f"[sessions] Wrote {len(pages)} pages -> {outdir}")

    if args.emit_sitemaps and pages:
        sm = ['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for f in pages:
            loc = (args.site_base.rstrip("/") + "/classes/" + f) if args.site_base else ("/classes/" + f)
            sm.append(f"  <url><loc>{loc}</loc></url>")
        sm.append("</urlset>")
        (outdir / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")
        print(f"[sessions] Wrote sitemap -> {outdir/'sitemap.xml'}")

if __name__ == "__main__":
    main()
