from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
SCHEDULE_FILE = DOCS_DIR / "data" / "schedule.json"

TOPICS_DIR = DOCS_DIR / "topics"
TOPICS_YEAR_DIR = DOCS_DIR / "topics-year"
YEARS_DIR = DOCS_DIR / "years"

LOCAL_TZ = ZoneInfo("America/New_York")
SITE_NAME = "910CPR"
GTM_ID = "GTM-PQS8DCBH"
ENROLLWARE_SCHEDULE_URL = "https://coastalcprtraining.enrollware.com/site/coastalcprtraining/schedule"

TOPIC_LABELS = {
    "acls": "ACLS",
    "aed": "AED / Maintenance",
    "bls": "BLS",
    "family-friends": "Family & Friends",
    "first-aid": "First Aid",
    "heartsaver": "Heartsaver",
    "hsi": "HSI",
    "instructor": "Instructor Courses",
    "misc": "Other Courses",
    "pals": "PALS",
    "red-cross": "Red Cross",
    "stop-the-bleed": "Stop the Bleed",
    "uscg": "USCG / Coast Guard",
}

TOPIC_PRIMARY_DESTINATIONS = {
    "acls": "/acls.html",
    "bls": "/bls.html",
    "pals": "/pals.html",
    "heartsaver": "/heartsaver.html",
    "first-aid": "/heartsaver.html",
    "uscg": "/uscg-elementary-first-aid-cpr.html",
}


def render_gtm_head() -> str:
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


def render_gtm_body() -> str:
    if not GTM_ID:
        return ""
    return f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(text or ""))).strip()


def clean_location(value: str) -> str:
    location = strip_html(value)
    if location.startswith("::"):
        location = location[2:].strip()
    return location or "Location TBA"


def parse_dt(value: str) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(LOCAL_TZ)


def slugify(value: str) -> str:
    clean = strip_html(value).lower()
    clean = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
    return clean or "item"


def classify_topic(course_name: str, certifying_body: str = "") -> str:
    text = f"{course_name} {certifying_body}".lower()
    if "uscg" in text or "coast guard" in text or "maritime" in text or "elementary first aid" in text:
        return "uscg"
    if "stop the bleed" in text:
        return "stop-the-bleed"
    if "instructor" in text:
        return "instructor"
    if "red cross" in text or re.search(r"\barc\b", text):
        return "red-cross"
    if re.search(r"\bhsi\b|\bashi\b", text):
        return "hsi"
    if "family" in text:
        return "family-friends"
    if "acls" in text:
        return "acls"
    if "pals" in text:
        return "pals"
    if "bls" in text:
        return "bls"
    if "heartsaver" in text:
        return "heartsaver"
    if "first aid" in text:
        return "first-aid"
    if "aed" in text and "maintenance" in text:
        return "aed"
    return "misc"


def topic_label(slug: str) -> str:
    return TOPIC_LABELS.get(slug, slug.replace("-", " ").title())


def primary_destination(slug: str) -> str:
    return TOPIC_PRIMARY_DESTINATIONS.get(slug, "/index.html")


def primary_label(slug: str) -> str:
    if slug in TOPIC_PRIMARY_DESTINATIONS:
        return f"Browse current {topic_label(slug)} options"
    return "Find current classes"


def display_date(dt: datetime) -> str:
    return f"{dt.strftime('%A, %B')} {dt.day}, {dt.year}"


def display_time(dt: datetime) -> str:
    hour = dt.strftime("%I").lstrip("0") or "0"
    return f"{hour}{dt.strftime(':%M %p')}"


def format_session_line(session: dict) -> str:
    dt = parse_dt(session.get("start_at"))
    course_name = escape(strip_html(session.get("course_name") or "Class"))
    date_bits = []
    if dt:
        date_bits.append(display_date(dt))
        date_bits.append(display_time(dt))
    location = escape(clean_location(session.get("location_display") or session.get("location_name")))
    details_path = f"/classes/{session.get('session_id')}.html"
    register_url = str(session.get("registration_url") or "").strip()
    detail_link = f'<a href="{details_path}">Details</a>'
    register_link = f' | <a href="{escape(register_url)}">Register</a>' if register_url else ""
    bits = " | ".join(escape(part) for part in date_bits if part)
    meta = f" <span class=\"archive-meta\">{bits} • {location}</span>" if bits or location else ""
    return f"<li>{course_name}{meta} | {detail_link}{register_link}</li>"


def page_shell(title: str, description: str, body_html: str, canonical_path: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <meta name="robots" content="noindex,follow">
  <link rel="canonical" href="https://www.910cpr.com{canonical_path}">
  <link rel="stylesheet" href="/css/lander.css">
  {render_gtm_head()}
  <style>
    body.archive-support {{
      background:
        radial-gradient(circle at top left, rgba(77, 192, 181, 0.22), transparent 35%),
        radial-gradient(circle at top right, rgba(255, 184, 108, 0.18), transparent 30%),
        linear-gradient(180deg, #f2fbff 0%, #fff9f1 100%);
      color: #17324d;
    }}
    .archive-shell {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 28px 18px 56px;
    }}
    .archive-topbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px 16px;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 18px;
      color: #355067;
      font-size: 0.95rem;
    }}
    .archive-topbar a {{
      color: #0f5e9c;
      font-weight: 700;
      text-decoration: none;
    }}
    .archive-panel, .archive-hero {{
      background: rgba(255,255,255,0.92);
      border: 1px solid rgba(23,50,77,0.10);
      border-radius: 24px;
      box-shadow: 0 20px 45px rgba(23,50,77,0.08);
      backdrop-filter: blur(8px);
    }}
    .archive-hero {{
      padding: 30px;
      margin-bottom: 22px;
    }}
    .archive-eyebrow {{
      margin: 0 0 10px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 0.82rem;
      font-weight: 800;
      color: #0f7a82;
    }}
    .archive-hero h1 {{
      margin: 0 0 10px;
      font-size: clamp(2rem, 4vw, 3rem);
      line-height: 1.05;
    }}
    .archive-hero p {{
      max-width: 760px;
      color: #496377;
      font-size: 1.02rem;
    }}
    .archive-cta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 18px;
    }}
    .archive-primary, .archive-secondary {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 46px;
      padding: 0 18px;
      border-radius: 999px;
      font-weight: 800;
      text-decoration: none;
      border: 1px solid transparent;
    }}
    .archive-primary {{
      background: linear-gradient(135deg, #1294a6 0%, #0f5e9c 100%);
      color: #fff;
    }}
    .archive-secondary {{
      background: #f7fbff;
      border-color: #cddae6;
      color: #17324d;
    }}
    .archive-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 22px;
    }}
    .archive-panel {{
      padding: 20px;
    }}
    .archive-panel h2 {{
      margin-top: 0;
    }}
    .archive-list, .archive-link-list {{
      margin: 0;
      padding-left: 18px;
    }}
    .archive-meta {{
      color: #58738a;
      font-size: 0.94rem;
    }}
    details.archive-details {{
      margin-top: 18px;
      border-top: 1px solid rgba(23,50,77,0.10);
      padding-top: 16px;
    }}
    details.archive-details summary {{
      cursor: pointer;
      font-weight: 800;
      color: #17324d;
    }}
    .archive-note {{
      color: #5b7388;
      font-size: 0.95rem;
    }}
    @media (max-width: 720px) {{
      .archive-shell {{
        padding: 20px 14px 40px;
      }}
      .archive-hero, .archive-panel {{
        padding: 18px;
      }}
    }}
  </style>
</head>
<body class="archive-support">
  {render_gtm_body()}
  <main class="archive-shell">
    {body_html}
  </main>
</body>
</html>"""


def topic_page(slug: str, sessions: list[dict], canonical_path: str) -> str:
    label = topic_label(slug)
    primary_href = primary_destination(slug)
    future_count = sum(1 for item in sessions if (parse_dt(item.get("start_at")) or datetime.min.replace(tzinfo=LOCAL_TZ)) > datetime.now(LOCAL_TZ))
    session_lines = "\n".join(format_session_line(item) for item in sessions[:80]) or "<li>No archived sessions are currently grouped under this topic.</li>"
    body = f"""
<div class="archive-topbar">
  <div>Archive support page for legacy topic URLs</div>
  <div><a href="/index.html">Go to current class finder</a></div>
</div>
<section class="archive-hero">
  <p class="archive-eyebrow">Support URL, Not Primary Booking Path</p>
  <h1>{escape(label)} archive support</h1>
  <p>This URL stays live for crawl coverage and legacy references, but the real customer decision path starts on the homepage or the related modern hub.</p>
  <div class="archive-cta-row">
    <a class="archive-primary" href="{primary_href}">{escape(primary_label(slug))}</a>
    <a class="archive-secondary" href="{ENROLLWARE_SCHEDULE_URL}">Open full Enrollware schedule</a>
  </div>
</section>
<section class="archive-grid">
  <article class="archive-panel">
    <h2>What this page is for</h2>
    <p class="archive-note">This is an archive-support landing page. Humans should use the current booking hubs. Bots can still follow the preserved detail links below.</p>
  </article>
  <article class="archive-panel">
    <h2>Current snapshot</h2>
    <ul class="archive-link-list">
      <li>{len(sessions)} archived session links grouped here</li>
      <li>{future_count} future sessions still associated with this topic</li>
      <li>Search engines may crawl these links, but the page itself is marked <code>noindex,follow</code></li>
    </ul>
  </article>
</section>
<section class="archive-panel">
  <h2>Archive session links</h2>
  <p class="archive-note">The archive remains available below, but it is intentionally demoted behind the current booking CTAs.</p>
  <details class="archive-details">
    <summary>Open archived {escape(label)} session links</summary>
    <ul class="archive-list">
      {session_lines}
    </ul>
  </details>
</section>
"""
    return page_shell(f"{label} Archive Support | {SITE_NAME}", f"Archive support page for legacy {label} topic URLs.", body, canonical_path)


def topic_year_page(slug: str, year: str, sessions: list[dict], canonical_path: str) -> str:
    label = topic_label(slug)
    topic_href = f"/topics/{slug}.html"
    session_lines = "\n".join(format_session_line(item) for item in sessions[:120]) or "<li>No archived sessions are currently grouped in this bucket.</li>"
    body = f"""
<div class="archive-topbar">
  <div>Archive support page for legacy topic-year URLs</div>
  <div><a href="{topic_href}">Open topic support page</a></div>
</div>
<section class="archive-hero">
  <p class="archive-eyebrow">Legacy Year Bucket</p>
  <h1>{escape(label)} {escape(year)} archive support</h1>
  <p>This page keeps old topic-year URLs crawlable while redirecting real humans back to current decision pages and live scheduling paths.</p>
  <div class="archive-cta-row">
    <a class="archive-primary" href="{primary_destination(slug)}">{escape(primary_label(slug))}</a>
    <a class="archive-secondary" href="/index.html">Find current classes</a>
  </div>
</section>
<section class="archive-panel">
  <h2>Archive session links for {escape(year)}</h2>
  <details class="archive-details" open>
    <summary>Open archived {escape(label)} {escape(year)} sessions</summary>
    <ul class="archive-list">
      {session_lines}
    </ul>
  </details>
</section>
"""
    return page_shell(f"{label} {year} Archive Support | {SITE_NAME}", f"Archive support page for legacy {label} {year} URLs.", body, canonical_path)


def year_page(year: str, grouped: dict[str, list[dict]], canonical_path: str) -> str:
    cards = []
    for slug, sessions in sorted(grouped.items(), key=lambda item: (-len(item[1]), topic_label(item[0]).lower())):
        cards.append(
            f"""
<article class="archive-panel">
  <h2>{escape(topic_label(slug))}</h2>
  <p class="archive-note">{len(sessions)} archived session links in this year bucket.</p>
  <div class="archive-cta-row">
    <a class="archive-primary" href="{primary_destination(slug)}">{escape(primary_label(slug))}</a>
    <a class="archive-secondary" href="/topics-year/{slug}-{year}.html">Open archive support bucket</a>
  </div>
</article>
"""
        )
    body = f"""
<div class="archive-topbar">
  <div>Archive support page for legacy yearly indexes</div>
  <div><a href="/index.html">Return to the live booking homepage</a></div>
</div>
<section class="archive-hero">
  <p class="archive-eyebrow">Legacy Year Index</p>
  <h1>{escape(year)} archive support</h1>
  <p>This year index stays crawlable, but humans should use the current homepage, hubs, and exact-course pages instead of browsing historical buckets.</p>
  <div class="archive-cta-row">
    <a class="archive-primary" href="/index.html">Find current classes</a>
    <a class="archive-secondary" href="{ENROLLWARE_SCHEDULE_URL}">Open full Enrollware schedule</a>
  </div>
</section>
<section class="archive-grid">
  {''.join(cards) or '<article class="archive-panel"><h2>No grouped topics</h2><p class="archive-note">No sessions were found for this year bucket.</p></article>'}
</section>
"""
    return page_shell(f"{year} Archive Support | {SITE_NAME}", f"Archive support page for legacy {year} class indexes.", body, canonical_path)


def load_sessions() -> list[dict]:
    data = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
    return data.get("sessions") or []


def main() -> None:
    sessions = load_sessions()
    for directory in (TOPICS_DIR, TOPICS_YEAR_DIR, YEARS_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    by_topic: dict[str, list[dict]] = defaultdict(list)
    by_topic_year: dict[tuple[str, str], list[dict]] = defaultdict(list)
    by_year: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))

    for session in sessions:
        dt = parse_dt(session.get("start_at"))
        year = str(dt.year) if dt else "undated"
        topic = classify_topic(session.get("course_name") or "", session.get("certifying_body") or "")
        by_topic[topic].append(session)
        by_topic_year[(topic, year)].append(session)
        by_year[year][topic].append(session)

    existing_topic_slugs = {path.stem for path in TOPICS_DIR.glob("*.html")}
    existing_topic_year_pairs = set()
    for path in TOPICS_YEAR_DIR.glob("*.html"):
        stem = path.stem
        if "-" in stem:
            topic_slug, year = stem.rsplit("-", 1)
            existing_topic_year_pairs.add((topic_slug, year))
    existing_years = {path.stem for path in YEARS_DIR.glob("*.html")}

    all_topics = sorted(existing_topic_slugs | set(by_topic.keys()))
    for slug in all_topics:
        html = topic_page(slug, sorted(by_topic.get(slug, []), key=lambda item: item.get("start_at") or ""), f"/topics/{slug}.html")
        (TOPICS_DIR / f"{slug}.html").write_text(html, encoding="utf-8")

    all_topic_years = sorted(existing_topic_year_pairs | set(by_topic_year.keys()))
    for slug, year in all_topic_years:
        html = topic_year_page(
            slug,
            year,
            sorted(by_topic_year.get((slug, year), []), key=lambda item: item.get("start_at") or ""),
            f"/topics-year/{slug}-{year}.html",
        )
        (TOPICS_YEAR_DIR / f"{slug}-{year}.html").write_text(html, encoding="utf-8")

    all_years = sorted(existing_years | set(by_year.keys()))
    for year in all_years:
        html = year_page(year, by_year.get(year, {}), f"/years/{year}.html")
        (YEARS_DIR / f"{year}.html").write_text(html, encoding="utf-8")

    print(f"Built {len(all_topics)} topic support pages")
    print(f"Built {len(all_topic_years)} topic-year support pages")
    print(f"Built {len(all_years)} year support pages")


if __name__ == "__main__":
    main()
