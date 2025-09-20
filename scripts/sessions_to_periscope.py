import csv, json, re, sys
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# --- Paths (repo root inferred from this file) ---
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT  docs
DATA_OUT = DOCS  data
PERISCOPE_JSON = DOCS  periscope_full.json
SESSIONS_HTML = DOCS  sessions  index.html

# --- Helpers ---
def coalesce(row, keys)
    for k in keys
        v = row.get(k, )
        if v is not None and str(v).strip()
            return str(v).strip()
    return 

def guess_course_family(text str) - str
    t = (text or ).upper()
    if ACLS in t return ACLS
    if PALS in t return PALS
    if HEARTSAVER in t or FIRST AID in t or t == FA return FA
    return BLS

def parse_start(row) - str
    Return 'YYYY-MM-DDTHHMM' (no tz). Accepts ISO or date+time.
    iso = coalesce(row, start, start_iso, start_at, start_time_iso, Start, START)
    if iso
        iso = iso.replace( , T)
        m = re.match(r^(d{4}-d{2}-d{2}Td{2}d{2}), iso)
        return m.group(1) if m else iso

    d = coalesce(row, date, Date, session_date)
    t = coalesce(row, time, Time, start_time)
    if not (d and t)
        return 

    # normalize date
    dd = 
    for dfmt in (%Y-%m-%d, %m%d%Y, %m%d%y)
        try
            dd = datetime.strptime(d, dfmt).strftime(%Y-%m-%d)
            break
        except Exception
            pass
    if not dd
        dd = d  # last-resort

    # normalize time
    t = t.strip().lower().replace( , )
    for tfmt in (%H%M, %I%M%p, %I%M%p)
        try
            tt = datetime.strptime(t, tfmt).strftime(%H%M)
            break
        except Exception
            tt = t.upper()
    return f{dd}T{tt}

def label_for(start_iso str, city str) - str
    try
        dt = datetime.strptime(start_iso[16], %Y-%m-%dT%H%M)
        hm = dt.strftime(%-I%M%p) if hasattr(dt, strftime) else dt.strftime(%I%M%p)
        hm = hm.lower().replace(00,).replace(am,a).replace(pm,p)
        return f{dt.strftime('%b %d')}, {hm} • {city}
    except Exception
        return f{start_iso} • {city} if start_iso else city

def row_to_item(row dict) - dict
    start = parse_start(row)
    city = coalesce(row, city, City, location_city, LocationCity, location)
    url  = coalesce(row, url, enroll_url, EnrollURL, link, Link, hovn_url)
    course = coalesce(row, course_family, course, Course, title, Title)
    fam = (coalesce(row, course_family) or guess_course_family(course))
    item = {course_family fam, start start, city city, url url}
    lbl = coalesce(row, label) or label_for(start, city)
    if lbl item[label] = lbl
    return item

def load_csv(path Path)
    with path.open(newline=, encoding=utf-8-sig) as f
        rdr = csv.DictReader(f)
        for row in rdr
            yield { (k or ).strip() (v.strip() if isinstance(v, str) else v) for k, v in row.items() }

def main()
    # Pick CSV arg1 OR datasessions.csv OR sessions.csv
    candidates = []
    if len(sys.argv)  1
        candidates = [Path(sys.argv[1])]
    candidates += [ROOT  data  sessions.csv, ROOT  sessions.csv]
    src = next((p for p in candidates if p.exists()), None)
    if not src
        print([sessions_to_periscope] CSV not found. Looked for)
        for c in candidates print( -, c)
        sys.exit(1)

    rows = list(load_csv(src))
    items = [row_to_item(r) for r in rows if r]
    items = [x for x in items if x.get(start)]  # drop empties

    # sort by start time
    def key_iso(x)
        s = x.get(start, )
        try
            return datetime.strptime(s[16], %Y-%m-%dT%H%M)
        except Exception
            return datetime.max
    items.sort(key=key_iso)

    # 1) periscope_full.json (homepage chips)
    DOCS.mkdir(parents=True, exist_ok=True)
    PERISCOPE_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding=utf-8)
    print(f[sessions_to_periscope] wrote {PERISCOPE_JSON} ({len(items)} items))

    # 2) flat times list
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    times = [x[start] for x in items]
    (DATA_OUT  session-times.json).write_text(json.dumps(times, ensure_ascii=False, indent=2), encoding=utf-8)
    print(f[sessions_to_periscope] wrote {DATA_OUT  'session-times.json'} ({len(times)} datetimes))

    # 3) simple sessions index (optional)
    SESSIONS_HTML.parent.mkdir(parents=True, exist_ok=True)
    lis = []
    for it in items
        href = it.get(url) or #
        lab  = it.get(label, it[start])
        fam  = it.get(course_family,)
        city = it.get(city,)
        lis.append(flia href='{href}'{lab}a small style='color#666'&nbsp;[{fam} — {city}]smallli)
    html = [
        !doctype htmlmeta charset='utf-8',
        titleSessions  910CPRtitle,
        meta name='viewport' content='width=device-width, initial-scale=1',
        body style='font-familysystem-ui;margin24px',
        h1Sessionsh1ul,
        lis,
        ulbody,
    ]
    SESSIONS_HTML.write_text(n.join(html), encoding=utf-8)
    print(f[sessions_to_periscope] wrote {SESSIONS_HTML})

if __name__ == __main__
    main()
