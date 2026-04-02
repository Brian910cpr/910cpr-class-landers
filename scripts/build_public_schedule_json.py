import json
import re
import hashlib
import time as time_module
from datetime import datetime
from html import unescape, escape
from pathlib import Path

from title_cleaner import normalize_course_title, seo_title_for_session

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "schedule.json"
OUTPUT_DIR = ROOT / "docs" / "classes"
IMAGES_DIR = ROOT / "docs" / "images"
COURSE_ARCHIVE_DIR = IMAGES_DIR / "course-archive"

GTM_ID = "GTM-PQS8DCBH"
UPCOMING_LIMIT = 10
PROGRESS_EVERY = 250

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def render_gtm_head():
    if not GTM_ID:
        return ""
    return f"""<!-- Google Tag Manager -->
<script>
(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{GTM_ID}');
</script>
<!-- End Google Tag Manager -->"""


def render_gtm_body():
    if not GTM_ID:
        return ""
    return f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""


def strip_html(text):
    text = unescape(str(text or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def canonical_course_name(course_raw: str) -> str:
    return normalize_course_title(course_raw) or strip_html(course_raw) or "CPR Class"


def slugify(text: str) -> str:
    text = canonical_course_name(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "course"


def short_slug(text: str, max_len: int = 70) -> str:
    clean = slugify(text)
    digest = hashlib.md5(clean.encode("utf-8")).hexdigest()[:8]
    if len(clean) > max_len:
        clean = clean[:max_len].rstrip("-")
    return f"{clean}-{digest}" if clean else digest


def js_escape(value):
    if value is None:
        return ""
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def parse_dt(value):
    raw = str(value or "").strip()

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            pass

    return None


def location_to_city_state(location: str):
    raw = str(location or "").strip()

    if ";" in raw:
        city = raw.split(";")[0].strip()
        return city, "NC"

    if "," in raw:
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if len(parts) >= 2:
            return parts[0], parts[1]

    if raw:
        return raw, "NC"

    return "Wilmington", "NC"


def is_public_listing_location(location: str) -> bool:
    return str(location or "").strip().startswith("::")


def clean_location_display(location: str) -> str:
    value = str(location or "").strip()
    if value.startswith("::"):
        value = value[2:].strip()
    return value


def audience_blurb(course_name: str) -> str:
    lower = course_name.lower()

    if "acls" in lower:
        return (
            "This course is commonly taken by nurses, paramedics, respiratory therapists, "
            "ER staff, ICU staff, and other clinicians who need advanced cardiovascular life support training."
        )
    if "pals" in lower:
        return (
            "This course is commonly taken by pediatric nurses, emergency clinicians, paramedics, "
            "and other providers who care for infants and children."
        )
    if "bls" in lower:
        return (
            "This course is commonly taken by healthcare workers, nursing students, dental staff, "
            "EMS personnel, and others who need professional-level CPR certification."
        )
    if "heartsaver" in lower or "cpr" in lower or "aed" in lower:
        return (
            "This course is commonly taken by teachers, childcare staff, fitness professionals, "
            "security personnel, church staff, office teams, and other workplace responders."
        )

    return (
        "This class supports both individual certification needs and organizations that need reliable, "
        "repeatable safety training for employees."
    )


def corporate_blurb(city: str, course_name: str) -> str:
    return (
        f"910CPR also supports employers in {city} that need documented, renewable training for staff. "
        f"If you need multiple employees trained in {course_name}, group and workplace options may be available."
    )


def make_schema(course_name: str, session_dt, location_name: str, city: str, state: str, register_url: str):
    start_iso = session_dt.strftime("%Y-%m-%dT%H:%M:%S") if session_dt else ""
    return f"""
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": {json.dumps(course_name)},
  "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
  "eventStatus": "https://schema.org/EventScheduled",
  "startDate": {json.dumps(start_iso)},
  "location": {{
    "@type": "Place",
    "name": {json.dumps(location_name)},
    "address": {{
      "@type": "PostalAddress",
      "addressLocality": {json.dumps(city)},
      "addressRegion": {json.dumps(state)},
      "addressCountry": "US"
    }}
  }},
  "organizer": {{
    "@type": "Organization",
    "name": "910CPR",
    "url": "https://www.910cpr.com/"
  }},
  "offers": {{
    "@type": "Offer",
    "url": {json.dumps(register_url)},
    "availability": "https://schema.org/InStock",
    "priceCurrency": "USD"
  }}
}}
</script>
""".strip()


def sanitize_description_html(html_text: str) -> str:
    html_text = str(html_text or "").strip()
    if not html_text:
        return ""
    html_text = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", html_text, flags=re.I | re.S)
    html_text = re.sub(r"\s+", " ", html_text).strip()
    return html_text


def load_course_description_html(course_id: str, course_name: str) -> str:
    candidate_dirs = [
        ROOT / "data" / "course_descriptions",
        ROOT / "docs" / "course_descriptions",
        ROOT / "course_descriptions",
        ROOT / "raw" / "course_descriptions",
        ROOT / "raw" / "descriptions",
        ROOT / "data" / "descriptions",
        ROOT / "raw",
    ]

    candidate_names = []
    if course_id:
        candidate_names.append(course_id)

    candidate_names.extend(
        [
            short_slug(course_name),
            slugify(course_name),
            canonical_course_name(course_name),
        ]
    )

    exts = [".html", ".htm", ".txt"]

    for d in candidate_dirs:
        if not d.exists():
            continue

        for name in candidate_names:
            for ext in exts:
                p = d / f"{name}{ext}"
                if p.exists():
                    return sanitize_description_html(p.read_text(encoding="utf-8", errors="ignore"))

        if course_id:
            for ext in exts:
                matches = sorted(d.glob(f"{course_id}*{ext}"))
                if matches:
                    return sanitize_description_html(matches[0].read_text(encoding="utf-8", errors="ignore"))

    return ""


def default_logo_url() -> str:
    logo = IMAGES_DIR / "logo.png"
    if logo.exists():
        return "/images/logo.png"
    return ""


def detect_cert_logo(course_name: str) -> str:
    c = course_name.lower()

    if "red cross" in c or c.startswith("arc ") or "arc " in c:
        if (IMAGES_DIR / "_ARC.png").exists():
            return "/images/_ARC.png"

    if "hsi" in c or "ashi" in c:
        if (IMAGES_DIR / "_HSI.png").exists():
            return "/images/_HSI.png"

    if "aha" in c or "heartsaver" in c or "heartcode" in c or "acls" in c or "pals" in c or "bls" in c:
        if (IMAGES_DIR / "_AHA.png").exists():
            return "/images/_AHA.png"

    return ""


def find_course_archive_image(course_id: str) -> str:
    if not course_id or not COURSE_ARCHIVE_DIR.exists():
        return ""

    exts = [".png", ".jpg", ".jpeg", ".webp"]
    preferred = []

    for ext in exts:
        preferred.extend(sorted(COURSE_ARCHIVE_DIR.glob(f"course-{course_id}-raw_enrollware_html-*{ext}")))
        preferred.extend(sorted(COURSE_ARCHIVE_DIR.glob(f"course-{course_id}-original_html-*{ext}")))

    def score(path: Path):
        name = path.name.lower()
        penalty = 0
        if "scroll" in name:
            penalty += 1000000
        if "steps" in name:
            penalty += 500000
        if "icon" in name:
            penalty += 500000
        return penalty - path.stat().st_size

    if not preferred:
        return ""

    chosen = sorted(preferred, key=score)[0]
    return f"/images/course-archive/{chosen.name}"


def same_course(session_a: dict, session_b: dict) -> bool:
    a_course_id = str(session_a.get("course_id", "")).strip()
    b_course_id = str(session_b.get("course_id", "")).strip()

    if a_course_id and b_course_id and a_course_id != "0" and b_course_id != "0":
        return a_course_id == b_course_id

    a_name = canonical_course_name(session_a.get("course", ""))
    b_name = canonical_course_name(session_b.get("course", ""))
    return a_name == b_name


def get_upcoming_sessions(current_session: dict, sessions: list[dict], now_dt: datetime, limit: int = UPCOMING_LIMIT) -> list[dict]:
    current_id = str(current_session.get("session_id", "")).strip()
    matches = []

    for s in sessions:
        if not same_course(current_session, s):
            continue

        sid = str(s.get("session_id", "")).strip()
        if sid == current_id:
            continue

        dt = parse_dt(s.get("start"))
        if not dt or dt < now_dt:
            continue

        s_copy = dict(s)
        s_copy["_parsed_dt"] = dt
        matches.append(s_copy)

    matches.sort(key=lambda x: x["_parsed_dt"])
    return matches[:limit]


def render_upcoming_sessions_html(upcoming_sessions: list[dict], schedule_url: str) -> str:
    if not upcoming_sessions:
        return f"""
<section class="info-box upcoming-box">
  <h2>Upcoming Classes</h2>
  <p>No upcoming public sessions are listed right now.</p>
  <p><a class="text-link" href="{escape(schedule_url)}">See all current dates and times</a></p>
</section>
"""

    cards = []
    for s in upcoming_sessions:
        dt = s["_parsed_dt"]
        date_label = dt.strftime("%B %d, %Y")
        time_label = dt.strftime("%I:%M %p").lstrip("0")
        location_label = clean_location_display(s.get("location", "")) or "Location TBD"
        register_url = s.get("register_url", "#")

        cards.append(
            f"""
<div class="upcoming-card">
  <div class="upcoming-date">{escape(date_label)}</div>
  <div class="upcoming-time">{escape(time_label)}</div>
  <div class="upcoming-location">{escape(location_label)}</div>
  <div class="upcoming-actions">
    <a class="button small primary" href="{escape(register_url)}">Register</a>
  </div>
</div>
"""
        )

    return f"""
<section class="info-box upcoming-box">
  <div class="upcoming-head">
    <h2>Upcoming Classes</h2>
    <a class="text-link" href="{escape(schedule_url)}">See all current dates and times</a>
  </div>
  <div class="upcoming-grid">
    {''.join(cards)}
  </div>
</section>
"""


with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

all_sessions = data["sessions"]
sessions = [s for s in all_sessions if is_public_listing_location(s.get("location", ""))]

template = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{page_title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{meta_description}">
<meta name="robots" content="{robots_value}">
<link rel="canonical" href="{canonical_url}">
{gtm_head}
{schema_block}

<style>
:root {{
  --bg: #eef4f8;
  --bg2: #f8fbfd;
  --card: #ffffff;
  --soft: #f8fbfd;
  --text: #1f2937;
  --muted: #6b7280;
  --accent: #2563eb;
  --accent-dark: #1d4ed8;
  --cta: #ea580c;
  --cta-dark: #c2410c;
  --border: #dbe4ee;
  --warning-bg: #fff7d6;
  --warning-border: #f2df91;
  --warning-text: #6d5600;
}}

* {{
  box-sizing: border-box;
}}

body {{
  margin: 0;
  font-family: Arial, sans-serif;
  background: linear-gradient(180deg, var(--bg2) 0%, var(--bg) 100%);
  color: var(--text);
}}

body img {{
  max-width: 100%;
  height: auto;
}}

.wrap {{
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 16px 56px;
}}

.card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 28px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
}}

.notice {{
  background: var(--warning-bg);
  border: 1px solid var(--warning-border);
  color: var(--warning-text);
  padding: 16px 18px;
  border-radius: 14px;
  margin-bottom: 22px;
  font-size: 18px;
}}

.hero {{
  display: block;
}}

.hero-top {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
}}

.date-badge {{
  min-width: 96px;
  border-radius: 18px;
  background: linear-gradient(180deg, var(--accent) 0%, var(--accent-dark) 100%);
  color: white;
  text-align: center;
  padding: 14px 10px;
}}

.date-month {{
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.08em;
}}

.date-day {{
  font-size: 34px;
  font-weight: 800;
  line-height: 1.05;
  margin: 6px 0;
}}

.date-weekday {{
  font-size: 13px;
}}

.cert-badge {{
  min-width: 96px;
  min-height: 96px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--soft);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 10px;
}}

.cert-badge img {{
  max-width: 72px;
  max-height: 72px;
  object-fit: contain;
}}

.hero-content {{
  margin-top: 18px;
}}

.hero h1 {{
  margin: 0 0 12px 0;
  font-size: 30px;
  line-height: 1.1;
}}

.subhead {{
  margin: 0 0 14px 0;
  color: var(--muted);
  font-size: 15px;
}}

.meta-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 10px 18px;
  margin: 10px 0 0 0;
}}

.meta-item {{
  background: var(--soft);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px 14px;
}}

.meta-label {{
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}}

.meta-value {{
  font-size: 16px;
  font-weight: 700;
}}

.cta-row {{
  margin-top: 18px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}}

.button {{
  display: inline-block;
  padding: 13px 18px;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 700;
}}

.button.small {{
  padding: 10px 14px;
  font-size: 14px;
}}

.button.primary {{
  background: var(--cta);
  color: white;
}}

.button.primary:hover {{
  background: var(--cta-dark);
}}

.button.secondary {{
  background: #5f6f82;
  color: white;
}}

.button.secondary:hover {{
  background: #526170;
}}

.stack {{
  display: grid;
  gap: 18px;
  margin-top: 28px;
}}

.info-box {{
  background: var(--soft);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 18px;
}}

.info-box h2 {{
  margin: 0 0 10px 0;
  font-size: 20px;
}}

.info-box p {{
  margin: 0 0 12px 0;
  line-height: 1.6;
}}

.upcoming-head {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}}

.upcoming-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}}

.upcoming-card {{
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 14px;
}}

.upcoming-date {{
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 4px;
}}

.upcoming-time {{
  font-size: 15px;
  margin-bottom: 4px;
}}

.upcoming-location {{
  color: var(--muted);
  font-size: 14px;
  margin-bottom: 12px;
}}

.upcoming-actions {{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}}

.brand-strip {{
  margin-top: 24px;
  display: grid;
  grid-template-columns: minmax(0, 180px) minmax(0, 1fr);
  gap: 18px;
  align-items: stretch;
}}

.brand-card,
.image-card {{
  background: var(--soft);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 16px;
}}

.brand-card {{
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 140px;
  text-align: center;
}}

.brand-card img {{
  max-width: 140px;
  max-height: 90px;
  object-fit: contain;
  margin: 0 auto;
  display: block;
}}

.image-card {{
  min-height: 140px;
}}

.image-card img {{
  width: 100%;
  height: 100%;
  max-height: 260px;
  object-fit: cover;
  border-radius: 12px;
  display: block;
}}

.description-box {{
  margin-top: 24px;
}}

.description-box h2 {{
  margin: 0 0 14px 0;
  font-size: 22px;
}}

.description-html {{
  line-height: 1.7;
}}

.description-html p {{
  margin: 0 0 14px 0;
}}

.description-html ul,
.description-html ol {{
  margin: 0 0 14px 24px;
  padding: 0;
}}

.description-html li {{
  margin: 0 0 8px 0;
}}

.text-link {{
  color: var(--accent);
  text-decoration: none;
}}

.text-link:hover {{
  text-decoration: underline;
}}

.build-stamp {{
  margin-top: 26px;
  color: var(--muted);
  font-size: 11px;
}}

@media (max-width: 840px) {{
  .brand-strip {{
    grid-template-columns: 1fr;
  }}
}}

@media (max-width: 700px) {{
  .hero-top {{
    align-items: stretch;
  }}

  .date-badge,
  .cert-badge {{
    min-width: 82px;
    min-height: 82px;
  }}

  .hero h1 {{
    font-size: 25px;
  }}
}}
</style>
</head>
<body>
{gtm_body}
<div class="wrap">
  <div class="card">

    {state_notice}

    <section class="hero">
      <div class="hero-top">
        <div class="date-badge">
          <div class="date-month">{month_abbr}</div>
          <div class="date-day">{day_num}</div>
          <div class="date-weekday">{weekday}</div>
        </div>
        {cert_logo_html}
      </div>

      <div class="hero-content">
        <h1>{course}</h1>
        <p class="subhead">{hero_subhead}</p>

        <div class="meta-grid">
          <div class="meta-item">
            <div class="meta-label">Date</div>
            <div class="meta-value">{date}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Time</div>
            <div class="meta-value">{time}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Location</div>
            <div class="meta-value">{location}</div>
          </div>
        </div>

        <div class="cta-row">
          {button_html}
          <a class="button secondary" href="{schedule_url}">See All Dates/Times</a>
        </div>
      </div>
    </section>

    {upcoming_sessions_html}

    {brand_strip_html}

    {course_description_section}

    <div class="stack">
      <section class="info-box">
        <h2>Who This Class Is For</h2>
        <p>{audience_text}</p>
        <p>{corporate_text}</p>
      </section>
    </div>

    <div class="build-stamp">build: {build_stamp}</div>

  </div>
</div>

<script>
window.dataLayer = window.dataLayer || [];

const pageContext = {{
  page_type: "session",
  session_id: "{session_id}",
  course_id: "{course_id}",
  course_name: "{course_js}",
  course_slug: "{course_slug}",
  location_name: "{location_js}",
  is_past_session: {is_past_js},
  register_url: "{register_js}",
  schedule_url: "{schedule_url}",
  course_page_url: "{course_page_url}",
  build_stamp: "{build_stamp}"
}};

window.dataLayer.push({{
  event: "page_context",
  ...pageContext
}});

function pushLinkClick(eventName, extra = {{}}) {{
  window.dataLayer.push({{
    event: eventName,
    ...pageContext,
    ...extra
  }});
}}

document.addEventListener("click", function(e) {{
  const a = e.target.closest("a");
  if (!a) return;

  const href = a.getAttribute("href") || "";
  const text = (a.textContent || "").trim().toLowerCase();

  if (href.includes("enrollware.com/enroll?id=")) {{
    pushLinkClick("register_click", {{
      click_text: text,
      link_url: href
    }});
    return;
  }}

  if (text.includes("see all dates") || text.includes("see all dates/times") || text.includes("see upcoming classes")) {{
    pushLinkClick("view_upcoming_click", {{
      click_text: text,
      link_url: href
    }});
    return;
  }}

  if (href.includes("/courses/")) {{
    pushLinkClick("course_link_click", {{
      click_text: text,
      link_url: href
    }});
    return;
  }}

  if (href.includes("/classes/")) {{
    pushLinkClick("session_link_click", {{
      click_text: text,
      link_url: href
    }});
    return;
  }}
}});
</script>

</body>
</html>
"""

print(f"Loading schedule data from: {DATA_FILE}", flush=True)
print(f"Total sessions in schedule.json: {len(all_sessions)}", flush=True)
print(f"Public sessions to build: {len(sessions)}", flush=True)

count = 0
build_stamp = datetime.now().strftime("%Y-%m-%d %I:%M %p").lstrip("0")
now_dt = datetime.now()
started = time_module.time()

print("Starting class lander build...", flush=True)

for idx, s in enumerate(sessions, 1):
    session_id = s.get("session_id")
    course_raw = s.get("course", "")
    course = canonical_course_name(course_raw)
    raw_location = str(s.get("location", "")).strip()
    location = clean_location_display(raw_location) or "Wilmington; Shipyard Blvd"
    register = s.get("register_url", "#")
    dt = parse_dt(s.get("start"))

    if dt:
        date = dt.strftime("%B %d, %Y")
        time_label = dt.strftime("%I:%M %p").lstrip("0")
        month_abbr = dt.strftime("%b").upper()
        day_num = dt.strftime("%d").lstrip("0")
        weekday = dt.strftime("%a")
    else:
        date = "TBD"
        time_label = "TBD"
        month_abbr = "TBD"
        day_num = "--"
        weekday = ""

    city, state = location_to_city_state(location)
    page_title = f"{seo_title_for_session(course, city=city, state=state)} | 910CPR"
    meta_description = (
        f"{course} in {location}. View class details, current schedule options, and register online with 910CPR."
    )
    course_page_url = f"../courses/{short_slug(course)}.html"

    course_id = str(s.get("course_id", "")).strip()
    if course_id and course_id != "0":
        schedule_url = f"https://coastalcprtraining.enrollware.com/schedule#ct{course_id}"
    else:
        schedule_url = "https://coastalcprtraining.enrollware.com/site/coastalcprtraining/schedule"

    canonical_url = f"https://www.910cpr.com/classes/{session_id}.html"

    is_past = bool(dt and dt < now_dt)

    if is_past:
        state_notice = """
<div class="notice">
This specific session has passed. See upcoming classes below.
</div>
"""
        button_html = f'<a class="button secondary" href="{schedule_url}">See Upcoming Classes</a>'
        robots_value = "index,follow"
        hero_subhead = "Use the schedule button or the upcoming list below to pick the next available class."
    else:
        state_notice = ""
        button_html = f'<a class="button primary" href="{register}">Register Now</a>'
        robots_value = "index,follow"
        hero_subhead = "Use the register button for this session or the upcoming list below for other dates and times."

    cert_logo = detect_cert_logo(course)
    if cert_logo:
        cert_logo_html = f'''
<div class="cert-badge">
  <img src="{escape(cert_logo)}" alt="Certifying body logo" loading="lazy">
</div>
'''
    else:
        cert_logo_html = '<div class="cert-badge"></div>'

    logo_url = default_logo_url()
    course_img_url = find_course_archive_image(course_id)

    brand_parts = []
    if logo_url:
        brand_parts.append(
            f'''
<div class="brand-card">
  <img src="{escape(logo_url)}" alt="910CPR logo" loading="lazy">
</div>
'''
        )

    if course_img_url:
        brand_parts.append(
            f'''
<div class="image-card">
  <img src="{escape(course_img_url)}" alt="{escape(course)} course image" loading="lazy">
</div>
'''
        )

    if brand_parts:
        brand_strip_html = f'<section class="brand-strip">{"".join(brand_parts)}</section>'
    else:
        brand_strip_html = ""

    description_html = load_course_description_html(course_id, course)
    if description_html:
        course_description_section = f"""
<section class="info-box description-box">
  <h2>Course Description</h2>
  <div class="description-html">
    {description_html}
  </div>
</section>
"""
    else:
        course_description_section = f"""
<section class="info-box description-box">
  <h2>Course Description</h2>
  <div class="description-html">
    <p>{escape(audience_blurb(course))}</p>
  </div>
</section>
"""

    upcoming_sessions = get_upcoming_sessions(s, sessions, now_dt, limit=UPCOMING_LIMIT)
    upcoming_sessions_html = render_upcoming_sessions_html(upcoming_sessions, schedule_url)

    html = template.format(
        page_title=escape(page_title),
        meta_description=escape(meta_description),
        robots_value=robots_value,
        canonical_url=escape(canonical_url),
        gtm_head=render_gtm_head(),
        gtm_body=render_gtm_body(),
        schema_block=make_schema(course, dt, location, city, state, register),
        course=escape(course),
        location=escape(location),
        date=escape(date),
        time=escape(time_label),
        month_abbr=escape(month_abbr),
        day_num=escape(day_num),
        weekday=escape(weekday),
        state_notice=state_notice,
        session_id=escape(str(session_id)),
        button_html=button_html,
        course_page_url=escape(course_page_url),
        schedule_url=escape(schedule_url),
        build_stamp=escape(build_stamp),
        course_js=js_escape(course),
        course_id=escape(course_id),
        course_slug=short_slug(course),
        location_js=js_escape(location),
        is_past_js="true" if is_past else "false",
        register_js=js_escape(register),
        audience_text=escape(audience_blurb(course)),
        corporate_text=escape(corporate_blurb(city, course)),
        hero_subhead=escape(hero_subhead),
        cert_logo_html=cert_logo_html,
        brand_strip_html=brand_strip_html,
        course_description_section=course_description_section,
        upcoming_sessions_html=upcoming_sessions_html,
    )

    path = OUTPUT_DIR / f"{session_id}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    count += 1

    if idx % PROGRESS_EVERY == 0 or idx == len(sessions):
        elapsed = time_module.time() - started
        rate = idx / elapsed if elapsed > 0 else 0
        remaining = (len(sessions) - idx) / rate if rate > 0 else 0
        print(
            f"[{idx}/{len(sessions)}] {(idx / len(sessions)) * 100:.1f}% | "
            f"elapsed {elapsed:.1f}s | eta {remaining:.1f}s",
            flush=True,
        )

print(f"Landers built: {count}", flush=True)