# build_sales_fliers.py  (DROP-IN REPLACEMENT)
# -----------------------------------------------------------------------------
# Generates per-session “sales flier” HTML pages from sessions.csv
# with per-session headlines, color themes, hero images, loud "More dates"
# button (Periscope/HOVN), and self-expiry behavior.
#
# USAGE (PowerShell):
#   $REPO    = "D:\Users\ten77\Documents\GitHub\910cpr-class-landers"
#   $CSV     = "$REPO\docs\sessions.csv"
#   $COURSES = "$REPO\course-offerings.csv"
#   python "$REPO\build_sales_fliers.py" --csv "$CSV" --out "$REPO\docs" `
#       --zip "$REPO\sales_fliers_bundle.zip" --courses "$COURSES" --naming cuid-first
# -----------------------------------------------------------------------------

import argparse, csv, datetime, hashlib, json, re, zipfile
from pathlib import Path
from collections import defaultdict

# ---------- helpers -----------------------------------------------------------

def norm(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', (s or '').strip().lower())

def slug(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', (s or '').strip().lower()).strip('-')

# Robust date parsing (ISO, US, JS-style)
def parse_date_time(date_s: str, time_s: str):
    s = (date_s or "").strip()
    t = (time_s or "").strip()

    m = re.match(r'^(\d{4}-\d{2}-\d{2})(?:[ T](\d{1,2})(?::(\d{2}))?)?$', s)
    if m:
        ymd = m.group(1)
        if m.group(2):
            hh = int(m.group(2)); mm = int(m.group(3) or 0)
        else:
            mt = re.search(r'(\d{1,2}):(\d{2})', t)
            if mt:
                hh, mm = int(mt.group(1)), int(mt.group(2))
                if re.search(r'pm', t, re.I) and hh < 12: hh += 12
                if re.search(r'am', t, re.I) and hh == 12: hh = 0
            else:
                hh, mm = 9, 0
        hhmm = f"{hh:02d}:{mm:02d}"
        try: dt = datetime.datetime.strptime(f"{ymd} {hhmm}", "%Y-%m-%d %H:%M")
        except: dt = None
        return ymd, hhmm, dt

    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', s)
    if m:
        mm_i, dd_i, yy_i = int(m.group(1)), int(m.group(2)), int(m.group(3))
        ymd = f"{yy_i:04d}-{mm_i:02d}-{dd_i:02d}"
        hh, mmn = 9, 0
        mt = re.search(r'(\d{1,2}):(\d{2})', t)
        if mt:
            hh, mmn = int(mt.group(1)), int(mt.group(2))
            if re.search(r'pm', t, re.I) and hh < 12: hh += 12
            if re.search(r'am', t, re.I) and hh == 12: hh = 0
        hhmm = f"{hh:02d}:{mmn:02d}"
        try: dt = datetime.datetime.strptime(f"{ymd} {hhmm}", "%Y-%m-%d %H:%M")
        except: dt = None
        return ymd, hhmm, dt

    m = re.search(r'\b([A-Za-z]{3})\s+([A-Za-z]{3})\s+(\d{1,2})\s+(\d{4})(?:\s+(\d{1,2}):(\d{2}))?', s)
    if m:
        MONTH = {'JAN':1,'FEB':2,'MAR':3,'APR':4,'MAY':5,'JUN':6,'JUL':7,'AUG':8,'SEP':9,'OCT':10,'NOV':11,'DEC':12}
        mon = MONTH.get(m.group(2).upper(), 1)
        day = int(m.group(3)); year = int(m.group(4))
        hh  = int(m.group(5) or 9); mm = int(m.group(6) or 0)
        ymd = f"{year:04d}-{mon:02d}-{day:02d}"; hhmm = f"{hh:02d}:{mm:02d}"
        try: dt = datetime.datetime.strptime(f"{ymd} {hhmm}", "%Y-%m-%d %H:%M")
        except: dt = None
        return ymd, hhmm, dt

    ymd = re.sub(r'[^0-9-]', '', s) or "2099-01-01"
    hhmm = "09:00"
    try: dt = datetime.datetime.strptime(f"{ymd} {hhmm}", "%Y-%m-%d %H:%M")
    except: dt = None
    return ymd, hhmm, dt

def iso_local(dt): return dt.strftime("%Y-%m-%dT%H:%M:%S") if dt else ''

def short_id_from_url(url: str) -> str:
    if not url: return 's' + hashlib.md5(b'default').hexdigest()[:8]
    m = re.search(r'/sessions/([a-z0-9]+)', url, re.I)
    return (m.group(1)[:12] if m else hashlib.md5(url.encode('utf-8')).hexdigest()[:12])

# Load course-offerings mapping (for CUID + periscope/hovn link)
def load_offers(path: Path) -> dict[str, dict]:
    meta = {}
    if path.exists():
        with path.open(newline='', encoding="utf-8-sig") as f:
            r = csv.DictReader(f)
            for row in r:
                if (row.get("status","").strip().lower() in {"inactive","hidden","hide","off"}): 
                    continue
                cuid = (row.get("cuid") or "").strip()
                link = (row.get("link") or "").strip()
                for key in (row.get("label"), row.get("course")):
                    k = norm(key or "")
                    if k:
                        meta[k] = {"cuid": cuid, "hovn": link}
    return meta

# Basic classifier for renewal/heartcode for headlines
def classify(text: str) -> dict:
    u = (text or "").upper()
    return {
        "renew": any(k in u for k in ["RENEW","RECERT","UPDATE"]),
        "heart": any(k in u for k in ["HEARTCODE","BLENDED","ONLINE","SKILLS"]),
    }

# Per-session headline variants (deterministic by filename hash)
VARIANTS = [
    "{COURSE}: Same-Day eCard. Get It Done.",
    "Book {CITY} {COURSE} — Hands-On. Fast. Done Right.",
    "{COURSE} that Sticks — Real Practice • Real Skills.",
    "Need {COURSE} Now? Seats Open — Grab Yours.",
    "{COURSE}: Instructor-Led • Practical • Confident.",
    "{COURSE}: Hospital-Ready Skills • Same-Day Card.",
]
VARIANTS_RENEW = [
    "{COURSE} Renewal — In & Out, Same-Day Card.",
    "Renew {COURSE} Fast — Keep Your Credentials Current.",
    "Stay Current: {COURSE} Renewal • Hands-On • Local.",
]
VARIANTS_HEART = [
    "HeartCode {COURSE} — Do Online, Finish Fast In-Person.",
    "Blended {COURSE}: Online + Skills — Same-Day Card.",
    "Fastest Path: HeartCode {COURSE} • Book Today.",
]

# Palettes (deterministic by filename hash)
PALETTES = [
    {"brand":"#0b63f6","accent":"#0a7d2a","bg1":"#ffffff","bg2":"#eef6ff"},
    {"brand":"#ef4444","accent":"#0ea5e9","bg1":"#ffffff","bg2":"#fff2f2"},
    {"brand":"#16a34a","accent":"#8b5cf6","bg1":"#ffffff","bg2":"#eefcf3"},
    {"brand":"#0ea5e9","accent":"#f59e0b","bg1":"#ffffff","bg2":"#eefaff"},
]

def choose_variant(filename: str, course: str, city: str, renew: bool, heart: bool) -> str:
    h = int(hashlib.md5(filename.encode('utf-8')).hexdigest(), 16)
    if renew: pool = VARIANTS_RENEW
    elif heart: pool = VARIANTS_HEART
    else: pool = VARIANTS
    tpl = pool[h % len(pool)]
    return tpl.replace("{COURSE}", course).replace("{CITY}", city or "Local")

def choose_palette(filename: str) -> dict:
    h = int(hashlib.md5(filename.encode('utf-8')).hexdigest(), 16)
    return PALETTES[h % len(PALETTES)]

# ---------- styles ------------------------------------------------------------

STYLE_BASE = '''body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:0;background:linear-gradient(180deg,var(--bg1),var(--bg2));color:#0a1b2a}
.wrap{max-width:1100px;margin:0 auto;padding:24px 16px}
.grid{display:grid;grid-template-columns:2fr 1.15fr;gap:18px}
@media(max-width:980px){.grid{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid #dde8f5;border-radius:16px;padding:20px;box-shadow:0 6px 24px rgba(0,0,0,.06)}
h1{margin:4px 0 8px;font-size:clamp(26px,4.6vw,40px);line-height:1.15}
.muted{color:#516c83}
.btn{display:inline-block;padding:12px 16px;border-radius:12px;background:var(--brand);color:#fff;text-decoration:none;font-weight:700;border:2px solid var(--brand)}
.btn.alt{background:#fff;color:var(--brand);border-color:var(--brand)}
.btn.ghost{background:#fff;color:var(--accent);border-color:var(--accent)}
.stack{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}
.hero{border:1px solid #dde8f5;border-radius:16px;overflow:hidden;min-height:220px;background:#fff}
.hero img{width:100%;height:100%;object-fit:cover;display:block}
.banner{padding:12px 16px;border:1px solid #e8b5b5;background:#fff5f5;border-radius:12px;color:#7a1c1c;margin:12px 0}
.note{font-size:12px;color:#516c83;margin-top:6px}'''

EXPIRE_JS = r"""<script>(function(){
  const m=document.getElementById('flier-meta'); if(!m) return;
  const s=m.getAttribute('data-start-iso');
  const dur=parseInt(m.getAttribute('data-duration-min')||'240',10);
  const next=m.getAttribute('data-next-url')||'/courses/index.html';
  const hub =m.getAttribute('data-hub-url') ||'/courses/index.html';
  const st = s?new Date(s):null, end= st?new Date(st.getTime()+dur*60000):null, now=new Date();

  if(end && now>end){
    const b=document.getElementById('status-banner');
    if(b){ b.style.display='block'; b.className='banner';
      b.innerHTML='<strong>This class has passed.</strong> '
        +'Next available session: <a style="color:var(--brand);text-decoration:underline" href="'+next+'">view & register</a>. '
        +'Or see all dates: <a style="color:var(--brand);text-decoration:underline" href="'+hub+'">course hub</a>.'; }
    document.querySelectorAll('a.btn.primary').forEach(a=>{ a.href=next; a.textContent='See Next Available Date'; });
  }

  const alt=document.getElementById('alt-sessions');
  if(alt){
    const items=alt.querySelectorAll('[data-start-iso]'); let f=0;
    items.forEach(li=>{const iso=li.getAttribute('data-start-iso'); const d=iso?new Date(iso):null; if(!d||d<now) li.style.display='none'; else f++;});
    if(f===0){ alt.innerHTML='<li><a href="'+hub+'">See more upcoming sessions</a></li>'; }
  }
})();</script>"""

# ---------- main --------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--zip', required=False)
    ap.add_argument('--duration', type=int, default=240)
    ap.add_argument('--allclasses', default='https://coastalcprtraining.enrollware.com/schedule')
    ap.add_argument('--courses', default='course-offerings.csv')
    ap.add_argument('--naming', choices=['cuid-first','legacy'], default='cuid-first')
    args = ap.parse_args()

    out = Path(args.out); (out/'fliers').mkdir(parents=True, exist_ok=True)
    wishlist = out / 'image-sales-fliers-wishlist.txt'

    offers = load_offers(Path(args.courses))

    with open(args.csv, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    headers = {h:norm(h) for h in (rows[0].keys() if rows else [])}

    def pick(*cands):
        wants=[norm(c) for c in cands]
        for original, n in headers.items():
            for w in wants:
                if w and w in n: return original
        return None

    col_course = pick('course','class','title','coursename','classname')
    col_date   = pick('date','classdate','startdate','start')
    col_time   = pick('time','starttime','classtime')
    col_city   = pick('city','locationcity','town')
    col_state  = pick('state','region','prov')
    col_addr   = pick('address','locationaddress','street','location')
    col_instr  = pick('instructor','teacher','trainer','facilitator')
    col_url    = pick('enroll','register','url','link','registrationlink','signup','hovn','enrollware')

    recs=[]; groups=defaultdict(list); images=set()

    for r in rows:
        course=(r.get(col_course) or 'CPR/AED Class').strip()
        ymd,h24,dt = parse_date_time(r.get(col_date) or '', r.get(col_time) or '')
        city=(r.get(col_city) or '').strip(); state=(r.get(col_state) or 'NC').strip()
        addr=(r.get(col_addr) or '').strip(); instr=(r.get(col_instr) or '').strip()
        reg=(r.get(col_url) or '').strip()

        meta = offers.get(norm(course), {}) or {}
        cuid = meta.get("cuid") or ('nocuid-'+hashlib.md5(norm(course).encode()).hexdigest()[:8])
        hovn = meta.get("hovn") or args.allclasses

        sid = short_id_from_url(reg)

        if args.naming=='cuid-first':
            fname=f"{cuid}_{ymd}_{h24.replace(':','-')}_{slug(city or 'local')}-{slug(state or 'nc')}_{sid}.html"
            key=cuid
        else:
            fname=f"{ymd}_{h24.replace(':','-')}_{slug(course)}_{slug(city or 'local')}_{slug(state or 'nc')}_{sid}.html"
            key=slug(course)

        rec = {
            "filename": fname, "cuid": cuid, "hovn": hovn,
            "course": course, "dt": dt, "date": ymd, "time": h24,
            "city": city, "state": state, "addr": addr, "instr": instr, "url": reg
        }
        recs.append(rec); groups[key].append(rec)

        # wishlist: prefer most specific → generic
        images.add(f"{slug(course)}_{slug(city)}_{state.lower()}_handson-aed.jpg")
        images.add(f"{slug(course)}_{state.lower()}_handson-aed.jpg")
        images.add(f"{slug(course)}_handson-aed.jpg")

    for k in groups:
        groups[k].sort(key=lambda x:(x['dt'] or datetime.datetime.max, x['filename']))

    # Emit pages
    for r in recs:
        dt=r['dt']; date_iso=iso_local(dt)
        key = r['cuid'] if args.naming=='cuid-first' else slug(r['course'])
        future=[x for x in groups[key] if (x['dt'] and dt and x['dt']>dt)]
        next_future=future[0] if future else None

        hub_url=f"/courses/{r['cuid']}.html"
        next_url=f"/fliers/{next_future['filename']}" if next_future else hub_url or r['hovn']

        # Build a strong "more dates" URL (Periscope/HOVN base + city/date hint)
        dparam = (dt.strftime("%Y-%m-%d") if dt else r['date'])
        more_url = f"{r['hovn']}" + (f"&city={slug(r['city'])}&date={dparam}" if r['city'] else f"&date={dparam}")

        # Alternates (future)
        alt_items = [
            f"<li data-start-iso=\"{iso_local(s['dt']) if s['dt'] else ''}\"><a href=\"/fliers/{s['filename']}\">{s['date']} {s['time']} — {s['city']}, {s['state']}</a></li>"
            for s in future[:5]
        ]
        alt_html = f"<div class='alt'><h3>Alternate Sessions</h3><ul id='alt-sessions'>{''.join(alt_items) or ''}</ul></div>"

        # Per-session headline + palette
        flags = classify(r['course'])
        headline = choose_variant(r['filename'], r['course'], r['city'], flags['renew'], flags['heart'])
        pal = choose_palette(r['filename'])

        # Hero image candidates (browser fails gracefully if not present)
        hero1 = f"/images/sales-fliers/{slug(r['course'])}_{slug(r['city'])}_{r['state'].lower()}_handson-aed.jpg"
        hero2 = f"/images/sales-fliers/{slug(r['course'])}_{r['state'].lower()}_handson-aed.jpg"
        hero3 = f"/images/sales-fliers/{slug(r['course'])}_handson-aed.jpg"

        title = f"{r['course']} — {r['city']}, {r['state']}" if r['city'] else r['course']
        desc  = f"{r['course']} in {r['city']}, {r['state']}. Register now — limited seats." if r['city'] else f"{r['course']} — Register now."

        schema={'@context':'https://schema.org','@type':'Event','name':r['course'],
                'startDate':r['date']+(f" {r['time']}" if r['time'] else ''),
                'eventAttendanceMode':'https://schema.org/OfflineEventAttendanceMode',
                'eventStatus':'https://schema.org/EventScheduled',
                'location':{'@type':'Place','name':f"{r['city']}, {r['state']}" if r['city'] else 'Local Area',
                            'address':{'@type':'PostalAddress','addressLocality':r['city'],'addressRegion':r['state'],'addressCountry':'US'}},
                'organizer':{'@type':'Organization','name':'910CPR'},
                'offers':{'@type':'Offer','url':r['url'],'availability':'https://schema.org/InStock'}}

        html=f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>{title}</title>
<link rel='canonical' href='/fliers/{r['filename']}'>
<meta name='description' content='{desc}'>
<style>:root{{--brand:{pal['brand']};--accent:{pal['accent']};--bg1:{pal['bg1']};--bg2:{pal['bg2']}}}{STYLE_BASE}</style>
<script type='application/ld+json'>{json.dumps(schema,separators=(',',':'))}</script>
</head><body>
<main class='wrap'>
  <div id='flier-meta' data-start-iso='{date_iso}' data-duration-min='{args.duration}' data-next-url='{next_url}' data-hub-url='{hub_url}' data-course-cuid='{r['cuid']}'></div>

  <div class='grid'>
    <section class='card'>
      <div id='status-banner' style='display:none'></div>
      <h1>{headline}</h1>
      <p class='muted'><strong>{r['course']}</strong> • {r['city']}, {r['state']}{(' • '+r['instr']) if r['instr'] else ''}</p>
      <p style="font-size:18px;margin:.25rem 0"><strong>{r['date']}{(' • '+r['time']) if r['time'] else ''}</strong></p>

      <div class="stack">
        <a class='btn primary' href='{r['url']}'>Register Now</a>
        <a class='btn ghost' href='{more_url}'>More Dates for {r['course']} →</a>
        <a class='btn alt' href='{hub_url}'>Course Hub</a>
      </div>

      {alt_html}
      <p class='note'>Same-day AHA eCard issued upon successful completion when applicable.</p>
    </section>

    <aside class='hero'>
      <img src="{hero1}" alt="{r['course']} training in {r['city']}, {r['state']}" loading="lazy"
           onerror="this.onerror=null;this.src='{hero2}';this.alt='{r['course']} training in {r['state']}';this.onerror=function(){{this.style.display='none'}};">
    </aside>
  </div>
</main>
{EXPIRE_JS}
</body></html>"""

        (out/'fliers'/r['filename']).write_text(html, encoding='utf-8')

    # Wishlist: now includes specific → regional → generic
    wishlist.write_text(
        '# Place these images in /docs/images/sales-fliers/\n'
        + '\n'.join(sorted(images)),
        encoding='utf-8'
    )

    if args.zip:
        with zipfile.ZipFile(args.zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for fp in (out/'fliers').glob('*.html'):
                z.write(fp, arcname=f"fliers/{fp.name}")
            z.write(wishlist, arcname='image-sales-fliers-wishlist.txt')

    print(f"Built {len(list((out/'fliers').glob('*.html')))} fliers → {(out/'fliers')}")
    print(f"Wishlist → {wishlist}")

if __name__ == '__main__':
    main()
