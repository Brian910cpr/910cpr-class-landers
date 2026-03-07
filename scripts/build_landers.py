import json
import re
import hashlib
from datetime import datetime
from html import unescape
from pathlib import Path

from title_cleaner import normalize_course_title, seo_title_for_session

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "schedule.json"
OUTPUT_DIR = ROOT / "docs" / "classes"

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
    text = unescape(str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def canonical_course_name(course_raw: str) -> str:
    return normalize_course_title(course_raw) or strip_html(course_raw) or "CPR Class"


def short_slug(text: str, max_len: int = 70) -> str:
    clean = canonical_course_name(text).lower()
    clean = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
    digest = hashlib.md5(clean.encode("utf-8")).hexdigest()[:8]

    if len(clean) > max_len:
        clean = clean[:max_len].rstrip("-")

    return f"{clean}-{digest}" if clean else digest


def js_escape(value):
    if value is None:
        return ""
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def parse_dt(value):
    raw = str(value).strip()

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
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

    return "", "NC"


def is_public_listing_location(location: str) -> bool:
    return str(location or "").strip().startswith("::")


def clean_location_display(location: str) -> str:
    value = str(location or "").strip()
    if value.startswith("::"):
        value = value[2:].strip()
    return value


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
{gtm_head}

<style>
:root {{
  --bg: #eef4f8;
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
  background: linear-gradient(180deg, #f8fbfd 0%, var(--bg) 100%);
  color: var(--text);
}}

.wrap {{
  max-width: 1080px;
  margin: 0 auto;
  padding: 32px 16px 48px;
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
  display: grid;
  grid-template-columns: 92px 1fr;
  gap: 18px;
  align-items: start;
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
  font-size: 28px;
  line-height: 1.1;
}}

.meta-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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

.section-title {{
  margin: 28px 0 14px 0;
  font-size: 18px;
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

.text-link {{
  color: var(--accent);
  text-decoration: none;
}}

.text-link:hover {{
  text-decoration: underline;
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
  margin-top: 24px;
  color: var(--muted);
  font-size: 11px;
}}

@media (max-width: 700px) {{
  .hero {{
    grid-template-columns: 1fr;
  }}

  .date-badge {{
    max-width: 92px;
  }}

  .hero h1 {{
    font-size: 24px;
  }}
}}
</style>
</head>
<body>
{gtm_body}
<div class="wrap">
  <div class="card">

    {past_notice}

    <section class="hero">
      <div class="date-badge">
        <div class="date-month">{month_abbr}</div>
        <div class="date-day">{day_num}</div>
        <div class="date-weekday">{weekday}</div>
      </div>

      <div>
        <h1>{course}</h1>

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
        </div>
      </div>
    </section>

    <h2 class="section-title">Upcoming Classes</h2>

    <div id="futureSessions">Loading upcoming classes...</div>

    <div class="build-stamp">build: {build_stamp}</div>

  </div>
</div>

<script>
window.dataLayer = window.dataLayer || [];

const pageContext = {{
  page_type: "session",
  session_id: "{session_id}",
  course_name: "{course_js}",
  course_slug: "{course_slug}",
  location_name: "{location_js}",
  is_past_session: {is_past_js},
  register_url: "{register_js}",
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
  const text = (a.textContent || "").trim();

  if (href.includes("enrollware.com/enroll?id=")) {{
    pushLinkClick("register_click", {{
      click_text: text,
      link_url: href
    }});
    return;
  }}

  if (text.toLowerCase().includes("view upcoming classes")) {{
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

function monthKeyFromDate(d) {{
  return d.toLocaleString("en-US", {{ month: "long", year: "numeric" }});
}}

function renderSessionCard(s) {{
  const d = new Date(s.start);
  const month = d.toLocaleString("en-US", {{ month: "short" }}).toUpperCase();
  const day = d.getDate();
  const weekday = d.toLocaleString("en-US", {{ weekday: "short" }});
  const time = d.toLocaleTimeString("en-US", {{ hour: "numeric", minute: "2-digit" }});

  return `
    <article class="session-card">
      <div class="small-date">
        <div class="small-month">${{month}}</div>
        <div class="small-day">${{day}}</div>
        <div class="small-weekday">${{weekday}}</div>
      </div>
      <div class="session-main">
        <div class="session-time">${{time}}</div>
        <div class="session-location">${{s.location}}</div>
        <div class="session-actions">
          <a class="cta-small" href="${{s.register_url}}">Register</a>
        </div>
      </div>
    </article>
  `;
}}

fetch("../data/public_schedule.json")
.then(r => r.json())
.then(data => {{
  const now = new Date();

  const matches = data.sessions.filter(s => {{
    if (!s.course) return false;
    if (!s.course.toLowerCase().includes(pageContext.course_name.substring(0, 25).toLowerCase())) return false;
    if (String(s.session_id) === String(pageContext.session_id)) return false;

    const dt = new Date(s.start);
    return dt >= now;
  }});

  matches.sort((a, b) => new Date(a.start) - new Date(b.start));

  if (matches.length === 0) {{
    document.getElementById("futureSessions").innerHTML =
      'No upcoming sessions scheduled right now. <a class="text-link" href="{course_page_url}">View the full course page</a>.';

    window.dataLayer.push({{
      event: "upcoming_sessions_empty",
      ...pageContext,
      upcoming_count: 0
    }});
    return;
  }}

  const groups = {{}};

  matches.slice(0, 12).forEach(s => {{
    const d = new Date(s.start);
    const key = monthKeyFromDate(d);
    if (!groups[key]) groups[key] = [];
    groups[key].push(s);
  }});

  let html = "";

  Object.keys(groups).forEach(month => {{
    html += `<section class="month-group"><h3 class="month-heading">${{month}}</h3><div class="session-grid">`;
    groups[month].forEach(s => {{
      html += renderSessionCard(s);
    }});
    html += `</div></section>`;
  }});

  document.getElementById("futureSessions").innerHTML = html;

  window.dataLayer.push({{
    event: "upcoming_sessions_loaded",
    ...pageContext,
    upcoming_count: matches.length
  }});
}})
.catch((err) => {{
  document.getElementById("futureSessions").innerHTML =
    'Unable to load upcoming sessions right now. <a class="text-link" href="{course_page_url}">View the full course page</a>.';

  window.dataLayer.push({{
    event: "upcoming_sessions_error",
    ...pageContext,
    error_message: String(err)
  }});
}});
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
        date = ""
        time = ""
        month_abbr = "TBD"
        day_num = "--"
        weekday = ""

    city, state = location_to_city_state(location)
    page_title = f"{seo_title_for_session(course, city=city, state=state)} | 910CPR"
    meta_description = f"{course} in {location}. View class details and register online with 910CPR."
    course_page_url = f"../courses/{short_slug(course)}.html"

    is_past = bool(dt and dt < now_dt)

    if is_past:
        past_notice = """
<div class="notice">
This session has passed. See other upcoming sessions below.
</div>
"""
        button_html = f'<a class="button secondary" href="{course_page_url}">View Upcoming Classes</a>'
        robots_value = "noindex,follow"
    else:
        past_notice = ""
        button_html = f'<a class="button primary" href="{register}">Register Now</a>'
        robots_value = "index,follow"

    html = template.format(
        page_title=page_title,
        meta_description=meta_description,
        robots_value=robots_value,
        gtm_head=render_gtm_head(),
        gtm_body=render_gtm_body(),
        course=course,
        location=location,
        date=date,
        time=time,
        month_abbr=month_abbr,
        day_num=day_num,
        weekday=weekday,
        past_notice=past_notice,
        session_id=session_id,
        button_html=button_html,
        course_page_url=course_page_url,
        build_stamp=build_stamp,
        course_js=js_escape(course),
        course_slug=short_slug(course),
        location_js=js_escape(location),
        is_past_js="true" if is_past else "false",
        register_js=js_escape(register),
    )

    path = OUTPUT_DIR / f"{session_id}.html"

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    count += 1

print(f"Landers built: {count}")