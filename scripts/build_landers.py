import json
import re
import hashlib
from datetime import datetime
from html import unescape, escape
from pathlib import Path

from title_cleaner import normalize_course_title, seo_title_for_session

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "schedule.json"
OUTPUT_DIR = ROOT / "docs" / "classes"
IMAGES_DIR = ROOT / "docs" / "images"

GTM_ID = "GTM-PQS8DCBH"

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


def find_existing_image(candidates):
    if not IMAGES_DIR.exists():
        return ""

    existing = {p.name.lower(): p.name for p in IMAGES_DIR.iterdir() if p.is_file()}
    for candidate in candidates:
        key = candidate.lower()
        if key in existing:
            return f"/images/{existing[key]}"
    return ""


def provider_logo_url(course_name: str) -> str:
    lower = course_name.lower()

    if "red cross" in lower or lower.startswith("arc") or " arc " in f" {lower} ":
        return find_existing_image(
            [
                "ARC_Logo.png",
                "arc_logo.png",
                "arc-logo.png",
                "red-cross-logo.png",
                "red_cross_logo.png",
                "arc.png",
            ]
        )

    if "hsi" in lower:
        return find_existing_image(
            [
                "HSI_Logo.png",
                "hsi_logo.png",
                "hsi-logo.png",
                "hsi.png",
            ]
        )

    if "aha" in lower or "acls" in lower or "pals" in lower or "bls" in lower or "heartsaver" in lower:
        return find_existing_image(
            [
                "AHA_Logo.png",
                "aha_logo.png",
                "aha-logo.png",
                "aha.png",
                "AHA.png",
            ]
        )

    return ""


def course_image_url(course_name: str) -> str:
    lower = course_name.lower()

    if "bls" in lower:
        return find_existing_image(
            [
                "BLS_action-Nurses-taking_blood_pressure_in-Wilmington-NC.jpg",
                "BLS_action.jpg",
                "BLS_Logo.png",
                "bls.jpg",
                "bls.png",
            ]
        )

    if "acls" in lower:
        return find_existing_image(
            [
                "ACLS_action.jpg",
                "ACLS_Logo.png",
                "acls.jpg",
                "acls.png",
            ]
        )

    if "pals" in lower:
        return find_existing_image(
            [
                "PALS_action.jpg",
                "PALS_Logo.png",
                "pals.jpg",
                "pals.png",
            ]
        )

    if "heartsaver" in lower:
        return find_existing_image(
            [
                "Heartsaver_action.jpg",
                "Heartsaver_Logo.png",
                "heartsaver.jpg",
                "heartsaver.png",
            ]
        )

    if "red cross" in lower or lower.startswith("arc"):
        return find_existing_image(
            [
                "ARC_BLS.jpg",
                "ARC_Logo.png",
                "arc.jpg",
                "arc.png",
            ]
        )

    if "hsi" in lower:
        return find_existing_image(
            [
                "HSI_action.jpg",
                "HSI_Logo.png",
                "hsi.jpg",
                "hsi.png",
            ]
        )

    return ""


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
  --success-bg: #ecfdf3;
  --success-border: #b7ebc7;
  --success-text: #166534;
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

.notice.live {{
  background: var(--success-bg);
  border-color: var(--success-border);
  color: var(--success-text);
}}

.hero {{
  display: grid;
  grid-template-columns: 96px 1fr;
  gap: 18px;
  align-items: start;
}}

.hero.past {{
  opacity: 0.72;
}}

.date-badge {{
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
}}

.brand-card img {{
  max-width: 140px;
  max-height: 90px;
  object-fit: contain;
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

.section-title {{
  margin: 30px 0 14px 0;
  font-size: 20px;
}}

.session-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}}

.session-card {{
  display: flex;
  gap: 14px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 14px;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.05);
}}

.small-date {{
  min-width: 74px;
  border-radius: 14px;
  background: linear-gradient(180deg, var(--accent) 0%, var(--accent-dark) 100%);
  color: white;
  text-align: center;
  padding: 10px 8px;
}}

.small-month {{
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}}

.small-day {{
  font-size: 26px;
  font-weight: 800;
  line-height: 1.05;
  margin: 4px 0;
}}

.small-weekday {{
  font-size: 12px;
}}

.session-main {{
  flex: 1;
}}

.session-time {{
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 6px;
}}

.session-location {{
  font-size: 15px;
  color: var(--text);
  margin-bottom: 10px;
}}

.session-actions {{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}}

.cta-small {{
  display: inline-block;
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--cta);
  color: white;
  text-decoration: none;
  font-weight: 700;
}}

.cta-small:hover {{
  background: var(--cta-dark);
}}

.month-group {{
  margin-top: 20px;
}}

.month-heading {{
  margin: 0 0 14px 0;
  font-size: 20px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border);
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
  .hero {{
    grid-template-columns: 1fr;
  }}

  .date-badge {{
    max-width: 96px;
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

    <section class="hero {hero_state_class}">
      <div class="date-badge">
        <div class="date-month">{month_abbr}</div>
        <div class="date-day">{day_num}</div>
        <div class="date-weekday">{weekday}</div>
      </div>

      <div>
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

    {brand_strip_html}

    {course_description_section}

    <div class="stack">
      <section class="info-box">
        <h2>Who This Class Is For</h2>
        <p>{audience_text}</p>
        <p>{corporate_text}</p>
      </section>
    </div>

    <h2 class="section-title">Next Available Classes</h2>
    <div id="futureSessions">Loading upcoming classes...</div>

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
  enrollware_feed_url: "{enrollware_feed_url}",
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

  if (text.includes("see all dates") || text.includes("see all dates/times")) {{
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

function escapeHtml(value) {{
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}}

function tryParseFeedDate(line) {{
  const text = String(line || "");
  const firstPart = text.split(" from ")[0].trim();
  const d = new Date(firstPart);
  if (isNaN(d.getTime())) return null;
  return d;
}}

function renderFeedItem(item) {{
  const id = item && item.id ? String(item.id) : "";
  if (id && id === String(pageContext.session_id)) {{
    return "";
  }}

  const dateLines = Array.isArray(item.dateTimes)
    ? item.dateTimes.filter(Boolean)
    : [item.dateTimes].filter(Boolean);

  const parsed = dateLines.length ? tryParseFeedDate(dateLines[0]) : null;

  let badgeHtml = "";
  if (parsed) {{
    const month = parsed.toLocaleString("en-US", {{ month: "short" }}).toUpperCase();
    const day = parsed.getDate();
    const weekday = parsed.toLocaleString("en-US", {{ weekday: "short" }});
    badgeHtml = `
      <div class="small-date">
        <div class="small-month">${{month}}</div>
        <div class="small-day">${{day}}</div>
        <div class="small-weekday">${{weekday}}</div>
      </div>
    `;
  }}

  const whenHtml = dateLines.length
    ? dateLines.map(x => `<div class="session-time">${{escapeHtml(x)}}</div>`).join("")
    : `<div class="session-time">Upcoming session</div>`;

  const locationHtml = item.location
    ? `<div class="session-location">${{escapeHtml(item.location)}}</div>`
    : "";

  const seatsHtml =
    item.seatsLeft === null || item.seatsLeft === undefined || item.seatsLeft === ""
      ? ""
      : `<div class="session-location">${{escapeHtml(item.seatsLeft)}} seats left</div>`;

  const closedHtml = item.closed
    ? `<div class="session-location">Registration closed</div>`
    : "";

  const regUrl = item.url || pageContext.schedule_url;

  return `
    <article class="session-card">
      ${{badgeHtml}}
      <div class="session-main">
        ${{whenHtml}}
        ${{locationHtml}}
        ${{seatsHtml}}
        ${{closedHtml}}
        <div class="session-actions">
          <a class="cta-small" href="${{escapeHtml(regUrl)}}">Register</a>
        </div>
      </div>
    </article>
  `;
}}

function renderNoSessions() {{
  document.getElementById("futureSessions").innerHTML =
    'No additional upcoming sessions are listed right now. <a class="text-link" href="' +
    pageContext.schedule_url +
    '">See all dates for this course</a>.';

  window.dataLayer.push({{
    event: "upcoming_sessions_empty",
    ...pageContext,
    upcoming_count: 0
  }});
}}

function loadEnrollwareFeed() {{
  const target = document.getElementById("futureSessions");

  if (!pageContext.course_id || !pageContext.enrollware_feed_url) {{
    renderNoSessions();
    return;
  }}

  const callbackName = "ewFeedCallback_" + String(pageContext.session_id).replace(/[^a-zA-Z0-9_]/g, "");
  const script = document.createElement("script");

  window[callbackName] = function(items) {{
    try {{
      const rows = Array.isArray(items) ? items : [];
      const cards = rows.map(renderFeedItem).filter(Boolean).slice(0, 10);

      if (!cards.length) {{
        renderNoSessions();
        return;
      }}

      target.innerHTML =
        `<div class="session-grid">${{cards.join("")}}</div>` +
        `<p style="margin-top:16px;"><a class="text-link" href="${{pageContext.schedule_url}}">See all dates for this course</a></p>`;

      window.dataLayer.push({{
        event: "upcoming_sessions_loaded",
        ...pageContext,
        upcoming_count: cards.length
      }});
    }} finally {{
      try {{ delete window[callbackName]; }} catch (e) {{}}
      if (script.parentNode) script.parentNode.removeChild(script);
    }}
  }};

  script.onerror = function(err) {{
    target.innerHTML =
      'Unable to load upcoming sessions right now. <a class="text-link" href="' +
      pageContext.schedule_url +
      '">See all dates for this course</a>.';

    window.dataLayer.push({{
      event: "upcoming_sessions_error",
      ...pageContext,
      error_message: String(err)
    }});

    try {{ delete window[callbackName]; }} catch (e) {{}}
    if (script.parentNode) script.parentNode.removeChild(script);
  }};

  const joiner = pageContext.enrollware_feed_url.includes("?") ? "&" : "?";
  script.src = pageContext.enrollware_feed_url + joiner + "callback=" + encodeURIComponent(callbackName);
  document.body.appendChild(script);
}}

loadEnrollwareFeed();
</script>

</body>
</html>
"""


count = 0
build_stamp = datetime.now().strftime("%Y-%m-%d %I:%M %p").lstrip("0")
now_dt = datetime.now()

for s in sessions:
    session_id = s.get("session_id")
    course_raw = s.get("course", "")
    course = canonical_course_name(course_raw)
    raw_location = str(s.get("location", "")).strip()
    location = clean_location_display(raw_location) or "Wilmington; Shipyard Blvd"
    register = s.get("register_url", "#")
    dt = parse_dt(s.get("start"))

    if dt:
        date = dt.strftime("%B %d, %Y")
        time = dt.strftime("%I:%M %p").lstrip("0")
        month_abbr = dt.strftime("%b").upper()
        day_num = dt.strftime("%d").lstrip("0")
        weekday = dt.strftime("%a")
    else:
        date = "TBD"
        time = "TBD"
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
    if course_id:
        schedule_url = f"https://coastalcprtraining.enrollware.com/schedule#ct{course_id}"
        enrollware_feed_url = (
            f"https://coastalcprtraining.enrollware.com/registration/schedule-feed.ashx?courseid={course_id}"
        )
    else:
        schedule_url = course_page_url
        enrollware_feed_url = ""

    canonical_url = f"https://www.910cpr.com/classes/{session_id}.html"

    is_past = bool(dt and dt < now_dt)

    if is_past:
        state_notice = """
<div class="notice">
This specific class date has passed. Use the current options below to choose a new session.
</div>
"""
        button_html = f'<a class="button secondary" href="{schedule_url}">See Current Dates</a>'
        robots_value = "index,follow"
        hero_state_class = "past"
        hero_subhead = (
            "This page stays active so you can quickly find the next available option for the same course."
        )
    else:
        state_notice = """
<div class="notice live">
Seats for this date are currently available. Register now or choose another date and time.
</div>
"""
        button_html = f'<a class="button primary" href="{register}">Register Now</a>'
        robots_value = "index,follow"
        hero_state_class = ""
        hero_subhead = "Need a different date or time? Use the button beside Register or the live schedule list below."

    logo_url = provider_logo_url(course)
    course_img_url = course_image_url(course)

    brand_parts = []
    if logo_url:
        brand_parts.append(
            f'''
<div class="brand-card">
  <img src="{escape(logo_url)}" alt="{escape(course)} provider logo" loading="lazy">
</div>
'''
        )

    if course_img_url:
        brand_parts.append(
            f'''
<div class="image-card">
  <img src="{escape(course_img_url)}" alt="{escape(course)} training image" loading="lazy">
</div>
'''
        )

    if brand_parts:
        if len(brand_parts) == 1 and 'image-card' in brand_parts[0]:
            brand_parts.insert(
                0,
                """
<div class="brand-card">
  <div style="font-weight:700; color:#6b7280;">910CPR Training</div>
</div>
""".strip(),
            )
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
        time=escape(time),
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
        hero_state_class=hero_state_class,
        hero_subhead=escape(hero_subhead),
        brand_strip_html=brand_strip_html,
        course_description_section=course_description_section,
        enrollware_feed_url=escape(enrollware_feed_url),
    )

    path = OUTPUT_DIR / f"{session_id}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    count += 1

print(f"Landers built: {count}")