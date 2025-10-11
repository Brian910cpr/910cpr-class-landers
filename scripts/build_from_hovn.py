#!/usr/bin/env python3
# build_from_hovn.py — generate docs/sessions/*.html from data/sessions.csv (HOVN export)

import csv, os, re, hashlib, random, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
DOCS = REPO / "docs"
SESS_DIR = DOCS / "sessions"

# Allow override via env var or CLI arg
env_path = os.getenv("HOVN_SESSIONS")
CSV_PATH = Path(env_path) if env_path else (DATA / "sessions.csv")
import sys
if len(sys.argv) > 1:
    CSV_PATH = Path(sys.argv[1])

# Map text like "BLS Provider", "ACLS Provider", "PALS Provider - Heartcode", "Heartsaver ..."
COURSE_SLUG_MAP = {
    "bls":  ("aha-bls-provider", "aha"),
    "acls": ("aha-acls-provider", "aha"),
    "pals": ("aha-pals-provider", "aha"),
    "heartsaver": ("aha-heartsaver-first-aid-cpr-aed", "aha"),
    "first aid": ("hsi-first-aid-cpr-aed", "hsi"),
}

INTRO_BLOCKS = {
    "aha": [
        "Designed for busy clinical teams, this American Heart Association session focuses on current guidelines and hands-on team practice.",
        "Ideal for hospital units and clinical rotations—updated AHA curriculum with scenario practice you can use the same day.",
        "Built for real-world care environments—AHA-aligned skills with actionable, team-based drills."
    ],
    "hsi": [
        "Practical, OSHA-accepted training built for job sites and real workplaces.",
        "Straightforward, hands-on skills with clear steps you can remember under stress.",
        "Make your workforce safer with focused practice and plain-language guidance."
    ],
    "generic": [
        "Hands-on practice with clear steps you can remember under stress.",
        "Focused scenarios and feedback to help skills stick.",
        "Modern, practical training that respects your time and schedule."
    ]
}

LOCAL_BLOCKS = [
    "Convenient for teams around {city}, {state} and nearby neighborhoods.",
    "Popular with employers across {city}, {state} and surrounding communities.",
    "Easy access for staff in {city}, {state} and the greater area."
]

AUDIENCE_BLOCKS = {
    "aha-bls-provider": [
        "Great fit for nursing students, dental teams, techs, and hospital staff.",
        "Common for floor nurses, clinical students, dental practices, and outpatient clinics.",
        "Used by hospitals, outpatient centers, and allied health programs."
    ],
    "aha-acls-provider": [
        "Recommended for ED, ICU, telemetry, step-down, and rapid response teams.",
        "Common for advanced providers and hospital teams managing cardiac events.",
        "Ideal for clinicians who lead or support resuscitation events."
    ],
    "aha-pals-provider": [
        "Recommended for pediatric units, ED teams, and EMS with pediatric exposure.",
        "Designed for providers caring for infants and children.",
        "Ideal for clinicians who respond to pediatric emergencies."
    ],
    "aha-heartsaver-first-aid-cpr-aed": [
        "Popular with workplaces, childcare, retail and community groups.",
        "Great for OSHA-accepted CPR/AED skills in non-clinical settings.",
        "Designed for frontline staff, supervisors, and community members."
    ],
    "hsi-first-aid-cpr-aed": [
        "Common for construction, manufacturing, and service-industry teams.",
        "Built for job sites that need practical, OSHA-accepted skills.",
        "Great choice for supervisors and crews needing fast, focused training."
    ]
}

def slugify(text, maxlen=None):
    text = (text or "").lower()
    text = re.sub(r"&", " and ", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    if maxlen and len(text) > maxlen:
        cut = text[:maxlen]
        if "-" in cut:
            cut = cut[:cut.rfind("-")]
        text = cut or text[:maxlen]
    return text

def short_sid(sess_id, length=7):
    if not sess_id:
        return "s" + hashlib.md5(os.urandom(16)).hexdigest()[:length]
    h = hashlib.sha1(sess_id.encode("utf-8")).hexdigest()
    return "s" + h[:length]

def parse_hovn_date(s):
    """
    Accepts strings like:
    'Sat Oct 11 2025 08:30:00 GMT-0400 (Eastern Daylight Time)'
    Strategy: drop the parenthetical, drop literal 'GMT', keep numeric offset.
    """
    s = re.sub(r"\s*\(.*?\)\s*$", "", s)      # remove trailing " (Eastern Daylight Time)"
    s = s.replace("GMT", "")                  # remove literal GMT
    s = re.sub(r"\s{2,}", " ", s).strip()
    # Example after cleanup: 'Sat Oct 11 2025 08:30:00 -0400'
    for fmt in ["%a %b %d %Y %H:%M:%S %z", "%a %b %d %Y %H:%M %z"]:
        try:
            return datetime.datetime.strptime(s, fmt)
        except Exception:
            pass
    raise ValueError(f"Unrecognized HOVN date: {s}")

def map_course_slug(certification, course_text):
    text = f"{certification} {course_text}".lower()
    # ordered checks: pals/acls/bls/heartsaver/first aid
    if "pals" in text:
        return COURSE_SLUG_MAP["pals"]
    if "acls" in text:
        return COURSE_SLUG_MAP["acls"]
    if "bls" in text:
        return COURSE_SLUG_MAP["bls"]
    if "heartsaver" in text:
        return COURSE_SLUG_MAP["heartsaver"]
    if "first aid" in text:
        return COURSE_SLUG_MAP["first aid"]
    # fallback: generic
    return (slugify(certification or course_text, 32), "generic")

def canonical_filename(start_dt, course_slug, city, state, sid_short):
    date_part = start_dt.astimezone().strftime("%Y-%m-%d_%H-%M")  # localize to system tz for sort
    course_part = slugify(course_slug, 28)
    loc_part = slugify(f"{city}-{state}", 24)
    return f"{date_part}-{course_part}-{loc_part}_{sid_short}.html"

def pick_phrase(blocks):
    return random.choice(blocks) if blocks else ""

def render_html(title, provider_key, city, state, start_dt, enroll_url, intro, audience, local, agency, fmt):
    style = """
    body{font-family:system-ui,Arial,sans-serif;margin:0;background:linear-gradient(180deg,#fff,#eef6ff);}
    .wrap{max-width:980px;margin:0 auto;padding:24px 16px;}
    .card{background:#fff;border-radius:16px;box-shadow:0 6px 24px rgba(0,0,0,.06);padding:18px 18px;}
    .btn{display:inline-block;padding:12px 16px;border-radius:10px;background:#0b63e6;color:#fff;text-decoration:none}
    small{color:#4a5568}
    """
    dt_local = start_dt.astimezone()
    dt_human = dt_local.strftime("%A, %B %d, %Y • %I:%M %p").lstrip("0").replace(" 0", " ")
    provider_label = "American Heart Association" if provider_key=="aha" else ("HSI" if provider_key=="hsi" else agency or "910CPR")
    sub = f"{provider_label} • {fmt} • {city}, {state}"
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — {city}, {state}</title>
<link rel="canonical" href="https://www.910cpr.com/sessions/">
<meta name="robots" content="index,follow">
<style>{style}</style>
</head>
<body>
  <main class="wrap">
    <div class="card">
      <h1>{title}</h1>
      <p><small>{sub}</small></p>
      <p><strong>{dt_human}</strong></p>
      <p>{intro}</p>
      <p>{audience}</p>
      <p>{local}</p>
      <p><a class="btn" href="{enroll_url}">Register Now</a></p>
      <p><small>Need a different time? https://www.hovn.app/910cpr/schedule</small></p>
    </div>
  </main>
</body></html>
"""

def main():
    random.seed(0x910)
    SESS_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        raise SystemExit(f"Missing {CSV_PATH}")

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        created = 0
        for row in reader:
            # HOVN columns (from your sample):
            # cuid,date,agency,certification,course,format,location,location.city,location.state,client,instructor,currentBookings,seats,status,link
            sess_id = (row.get("cuid") or "").strip()
            date_raw = (row.get("date") or "").strip()
            agency = (row.get("agency") or "").strip()
            certification = (row.get("certification") or "").strip()
            course_text = (row.get("course") or "").strip()
            fmt = (row.get("format") or "").strip()
            city = (row.get("location.city") or row.get("city") or "").strip()
            state = (row.get("location.state") or row.get("state") or "").strip()
            enroll_url = (row.get("link") or "").strip()
            title = course_text or certification or "CPR Class"

            if not (sess_id and date_raw and city and state and enroll_url):
                continue

            try:
                start_dt = parse_hovn_date(date_raw)
            except Exception:
                continue

            course_slug, provider_key = map_course_slug(certification, course_text)
            sid_short = short_sid(sess_id, 7)
            filename = canonical_filename(start_dt, course_slug, city, state, sid_short)
            out_path = SESS_DIR / filename

            intro = pick_phrase(INTRO_BLOCKS.get(provider_key) or INTRO_BLOCKS["generic"])
            audience = pick_phrase(AUDIENCE_BLOCKS.get(course_slug) or AUDIENCE_BLOCKS.get("aha-heartsaver-first-aid-cpr-aed", []))
            local = pick_phrase(LOCAL_BLOCKS).format(city=city, state=state)

            html = render_html(
                title=title, provider_key=provider_key, city=city, state=state,
                start_dt=start_dt, enroll_url=enroll_url,
                intro=intro, audience=audience, local=local,
                agency=agency, fmt=fmt
            )
            out_path.write_text(html, encoding="utf-8")
            created += 1

    print(f"Built {created} session pages into {SESS_DIR}")

if __name__ == "__main__":
    main()
