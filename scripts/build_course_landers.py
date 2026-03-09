from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PATH = REPO_ROOT / "raw" / "course_archive_v4.json"
SCHEDULE_PATH = REPO_ROOT / "public_schedule.json"
OUTPUT_DIR = REPO_ROOT / "docs" / "courses"
INDEX_JSON_PATH = OUTPUT_DIR / "index.json"

SITE_NAME = "910CPR"
BASE_URL = "https://www.910cpr.com"

VISIBLE_SESSION_COUNT = 8
CURTAIN_SESSION_COUNT = 16

DEFAULT_IMAGE_BY_CERT = {
    "AHA": "/images/_AHA.png",
    "ARC": "/images/_ARC.png",
    "HSI / ASHI": "/images/_HSI.png",
    "HSI": "/images/_HSI.png",
    "STOP THE BLEED® / American College of Surgeons": "/images/stop-the-bleed-fallback.png",
}

GENERIC_FALLBACK = "/images/910cpr_round.png"

LOCATION_MAP = {
    "Wilmington; Shipyard Blvd": "Wilmington",
    "Holly Ridge; Sound Rd": "Holly Ridge",
    "115-3": "Jacksonville",
    "809": "Jacksonville",
    "Burgaw; 111 S Wright St": "Burgaw",
    "Merlot Crt": "Wilmington",
}

# Exact schedule-name aliases where we know the public_schedule feed is weird or verbose.
COURSE_SESSION_ALIASES: dict[str, list[str]] = {
    "209806": ["AHA - BLS Provider - In-person Initial"],
    "359474": ["AHA - BLS Provider - In-person Renewal"],
    "210549": ["AHA - BLS Provider - Online Class with in-Person Skill Session - Initial or Renewal"],
    "241108": ["AHA - ACLS Provider - In-person Initial"],
    "209818": ["AHA - ACLS Provider Renewal - In-Person"],
    "209811": ["AHA - ACLS Provider - Online or Skills Session"],
    "251496": ["AHA - PALS Provider - In Person - Renewal"],
    "209812": ["AHA - PALS Provider - Online or Skills Session - Initial or Renewal"],
    "344085": ["AHA - Heartsaver® CPR AED - In-person"],
    "329495": ["AHA - Heartsaver® First Aid / CPR / AED Online + In-Person Skills"],
    "351632": ["AHA - Heartsaver® Pediatric First Aid / CPR / AED In-person"],
    "248288": ["ARC - BLS - In-Person Classroom"],
    "248287": ["ARC - BLS - Blended Learning Online - Initial or Renewal"],
    "444919": ["ARC BLS Challenge - Renewal for experienced Providers"],
    "359827": ["Elementary First Aid ONLINE", "Elementary First Aid"],
    "445670": ["HSI BLS and Adult First Aid | Blended Learning"],
    "253588": ["AHA - BLS - Become an American Heart Association Instructor"],
    "252737": ["AHA - Family & Friends® CPR"],
    "209809": ["AHA - Heartsaver® First Aid / CPR / AED In-person"],
    "251545": ["AHA - Heartsaver® Pediatric First Aid / CPR / AED Online + In-Person Skills"],
    "374378": ["HSI Adult First Aid | Adult/Child/Infant CPR AED"],
    "448630": ["HSI BLS | Blended Learning"],
    "344486": ["STOP THE BLEED®"],
}

# Safer titles for skills-session pages so we do not imply the online course is included.
TITLE_OVERRIDES: dict[str, dict[str, str]] = {
    "210549": {
        "title": "AHA BLS Skills Session",
        "subtitle": "For students completing HeartCode BLS online",
        "price_label": "Skills session from ${price:.2f}",
        "clarifier": "HeartCode BLS online may be purchased separately if needed.",
    },
    "209811": {
        "title": "AHA ACLS Skills Session",
        "subtitle": "For students completing HeartCode ACLS online",
        "price_label": "Skills session from ${price:.2f}",
        "clarifier": "HeartCode ACLS online may be purchased separately if needed.",
    },
    "209812": {
        "title": "AHA PALS Skills Session",
        "subtitle": "For students completing HeartCode PALS online",
        "price_label": "Skills session from ${price:.2f}",
        "clarifier": "HeartCode PALS online may be purchased separately if needed.",
    },
    "248287": {
        "title": "Red Cross BLS Skills Session",
        "subtitle": "For students completing Red Cross BLS online",
        "price_label": "Skills session from ${price:.2f}",
        "clarifier": "The Red Cross online course may be separate if not already completed.",
    },
    "329495": {
        "title": "AHA Heartsaver First Aid CPR AED Skills Session",
        "subtitle": "For students completing the online course before hands-on testing",
        "price_label": "Skills session from ${price:.2f}",
        "clarifier": "The online Heartsaver course may be purchased separately if needed.",
    },
    "251545": {
        "title": "AHA Heartsaver Pediatric First Aid CPR AED Skills Session",
        "subtitle": "For students completing the online course before hands-on testing",
        "price_label": "Skills session from ${price:.2f}",
        "clarifier": "The online pediatric course may be purchased separately if needed.",
    },
    "445670": {
        "title": "HSI BLS and Adult First Aid Skills Session",
        "subtitle": "For students completing the blended online course before skills testing",
        "price_label": "Skills session from ${price:.2f}",
        "clarifier": "The online HSI course may be separate if not already included in your registration.",
    },
    "448630": {
        "title": "HSI BLS Skills Session",
        "subtitle": "For students completing the blended online course before skills testing",
        "price_label": "Skills session from ${price:.2f}",
        "clarifier": "The online HSI BLS course may be separate if not already included in your registration.",
    },
    "359827": {
        "title": "USCG Elementary First Aid and CPR Skills Session",
        "subtitle": "For mariners completing the required online coursework before hands-on testing",
        "price_label": "Skills session from ${price:.2f}",
        "clarifier": "The online coursework may be separate if not already included in your registration.",
    },
}


def safe_text(value: Any) -> str:
    return "" if value is None else str(value)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    value = value.replace("®", "").replace("™", "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def slugify(value: str) -> str:
    value = strip_tags(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-")


def normalize_course_name(value: str) -> str:
    value = strip_tags(value)
    value = value.lower()
    value = value.replace("heartcode", "heartcode")
    value = value.replace("in person", "in-person")
    value = value.replace("online class with in-person skill session", "online or skills session")
    value = value.replace("online + in-person skills", "online or skills session")
    value = value.replace("blended learning", "online or skills session")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def parse_dt(value: str) -> datetime | None:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def pick_image(course: dict[str, Any]) -> str:
    image_urls = course.get("image_urls") or []
    for item in image_urls:
        candidate = safe_text(item).strip()
        if not candidate:
            continue
        if candidate.startswith("/"):
            return candidate
        filename = os.path.basename(candidate)
        if filename:
            mirrored = f"/images/course-archive/{filename}"
            return mirrored

    cert = safe_text(course.get("cert_body")).strip()
    if cert in DEFAULT_IMAGE_BY_CERT:
        return DEFAULT_IMAGE_BY_CERT[cert]

    for key, fallback in DEFAULT_IMAGE_BY_CERT.items():
        if key and key in cert:
            return fallback

    return GENERIC_FALLBACK


def course_url_slug(course: dict[str, Any]) -> str:
    existing = safe_text(course.get("url_slug")).strip()
    if existing:
        return existing.lstrip("/")

    clean_title = safe_text(course.get("clean_title")).strip()
    if clean_title:
        return slugify(clean_title)

    course_id = safe_text(course.get("course_id")).strip()
    return f"course-{course_id}"


def derive_family(course: dict[str, Any], raw_name: str) -> tuple[str, str]:
    text = f"{safe_text(course.get('clean_title'))} {safe_text(course.get('lander_title'))} {raw_name}".lower()

    if "stop the bleed" in text:
        return "STOP THE BLEED", "stop-the-bleed"
    if "acls" in text:
        return "ACLS", "acls"
    if "pals" in text:
        return "PALS", "pals"
    if "bls" in text:
        return "BLS", "bls"
    if "first aid" in text and "cpr" in text:
        return "First Aid + CPR/AED", "first-aid"
    if "cpr" in text and "aed" in text:
        return "CPR/AED", "cpr-aed"
    if "first aid" in text:
        return "First Aid", "first-aid"
    if "family" in text:
        return "CPR/AED", "cpr-aed"
    if "instructor" in text:
        return "Instructor", "instructor"
    return "Courses", "courses"


def derive_variant(course: dict[str, Any], raw_name: str) -> str:
    course_id = safe_text(course.get("course_id")).strip()
    if course_id in TITLE_OVERRIDES:
        return "Skills Session"

    text = f"{safe_text(course.get('clean_title'))} {safe_text(course.get('lander_title'))} {raw_name}".lower()

    if "renewal" in text:
        return "Renewal"
    if "initial" in text:
        return "Initial"
    if "instructor" in text:
        return "Instructor"
    if "family" in text:
        return "Family Class"
    if "challenge" in text:
        return "Challenge"
    if "online" in text or "skills" in text or "heartcode" in text or "blended" in text:
        return "Skills Session"
    if "in-person" in text or "classroom" in text:
        return "In-Person"
    return "Overview"


def display_title(course: dict[str, Any], raw_name: str) -> tuple[str, str | None, str | None]:
    course_id = safe_text(course.get("course_id")).strip()
    price = course.get("price")

    if course_id in TITLE_OVERRIDES:
        cfg = TITLE_OVERRIDES[course_id]
        title = cfg["title"]
        subtitle = cfg.get("subtitle")
        clarifier = cfg.get("clarifier")
        return title, subtitle, clarifier

    lander = safe_text(course.get("lander_title")).strip()
    clean = safe_text(course.get("clean_title")).strip()
    title = lander or clean or strip_tags(raw_name)
    return title, None, None


def display_price_label(course: dict[str, Any], title: str) -> str:
    course_id = safe_text(course.get("course_id")).strip()
    price = course.get("price")

    if not isinstance(price, (int, float)):
        return "Contact us for details"

    if course_id in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[course_id]["price_label"].format(price=price)

    return f"From ${price:.2f}" if price > 0 else "Contact us for details"


def meta_description(course: dict[str, Any], title: str) -> str:
    seo = safe_text(course.get("seo_description")).strip()
    if seo:
        return seo
    return f"{title} from {SITE_NAME}. Find upcoming classes and direct registration options."


def course_aliases(course: dict[str, Any]) -> list[str]:
    cid = safe_text(course.get("course_id")).strip()
    aliases: list[str] = []

    if cid in COURSE_SESSION_ALIASES:
        aliases.extend(COURSE_SESSION_ALIASES[cid])

    for key in ("original_course_name", "clean_title", "lander_title", "raw_enrollware_block"):
        value = safe_text(course.get(key)).strip()
        if value:
            aliases.append(value)

    deduped: list[str] = []
    seen: set[str] = set()
    for alias in aliases:
        norm = normalize_course_name(alias)
        if norm and norm not in seen:
            seen.add(norm)
            deduped.append(alias)
    return deduped


def match_sessions(course: dict[str, Any], sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    alias_norms = {normalize_course_name(a) for a in course_aliases(course)}
    now = datetime.now()

    matched = []
    for session in sessions:
        session_name_raw = safe_text(session.get("course")).strip()
        session_name = normalize_course_name(session_name_raw)
        if not session_name:
            continue

        ok = session_name in alias_norms
        if not ok:
            for alias in alias_norms:
                if alias and (alias in session_name or session_name in alias):
                    ok = True
                    break

        if not ok:
            continue

        dt = parse_dt(safe_text(session.get("start")).strip())
        if dt and dt < now:
            continue

        session["_parsed_start"] = dt
        matched.append(session)

    matched.sort(key=lambda s: s.get("_parsed_start") or datetime.max)
    return matched


def human_location(value: str) -> str:
    value = safe_text(value).strip()
    if value in LOCATION_MAP:
        return LOCATION_MAP[value]
    if re.fullmatch(r"\d+", value):
        return "Location at checkout"
    if ";" in value:
        return value.split(";")[0].strip()
    return value or "Location at checkout"


def format_date(dt: datetime | None) -> str:
    if not dt:
        return ""
    return dt.strftime("%a %b %-d") if os.name != "nt" else dt.strftime("%a %b %#d")


def format_time(dt: datetime | None) -> str:
    if not dt:
        return ""
    return dt.strftime("%-I:%M %p") if os.name != "nt" else dt.strftime("%#I:%M %p")


def hierarchy_pills(course: dict[str, Any], raw_name: str) -> str:
    cert = safe_text(course.get("cert_body")).strip() or "Courses"
    family_name, _family_slug = derive_family(course, raw_name)
    variant = derive_variant(course, raw_name)

    pills = [
        f'<span class="crumb-pill">{html.escape(cert)}</span>',
        f'<span class="crumb-pill">{html.escape(family_name)}</span>',
        f'<span class="crumb-pill current">{html.escape(variant)}</span>',
    ]
    return '<div class="crumb-row">' + "".join(pills) + "</div>"


def session_card(session: dict[str, Any]) -> str:
    dt = session.get("_parsed_start")
    date_label = format_date(dt)
    time_label = format_time(dt)
    location_label = human_location(safe_text(session.get("location")))
    register_url = safe_text(session.get("register_url")).strip() or "#"

    return f"""
    <a class="session-pill" href="{html.escape(register_url)}">
      <span class="session-date">{html.escape(date_label)}</span>
      <span class="session-time">{html.escape(time_label)}</span>
      <span class="session-location">{html.escape(location_label)}</span>
      <span class="session-cta">Register</span>
    </a>
    """


def build_session_blocks(course: dict[str, Any], sessions: list[dict[str, Any]]) -> str:
    if not sessions:
        schedule_url = safe_text(course.get("schedule_url")).strip()
        if schedule_url:
            return f"""
            <section class="sessions">
              <div class="section-label">Upcoming Classes</div>
              <p class="empty-note">
                New dates are added regularly.
                <a href="{html.escape(schedule_url)}">View the full class calendar</a>.
              </p>
            </section>
            """
        return ""

    visible = sessions[:VISIBLE_SESSION_COUNT]
    curtain = sessions[VISIBLE_SESSION_COUNT:VISIBLE_SESSION_COUNT + CURTAIN_SESSION_COUNT]
    schedule_url = safe_text(course.get("schedule_url")).strip()

    visible_html = "".join(session_card(s) for s in visible)

    curtain_html = ""
    if curtain:
        curtain_html = f"""
        <details class="session-curtain">
          <summary>More upcoming classes</summary>
          <div class="session-grid extra">
            {''.join(session_card(s) for s in curtain)}
          </div>
        </details>
        """

    full_schedule_html = ""
    if schedule_url:
        full_schedule_html = f"""
        <div class="full-schedule-row">
          <a class="full-schedule-link" href="{html.escape(schedule_url)}">See the full class calendar</a>
        </div>
        """

    return f"""
    <section class="sessions">
      <div class="section-label">Upcoming Classes</div>
      <div class="session-grid">
        {visible_html}
      </div>
      {curtain_html}
      {full_schedule_html}
    </section>
    """


def build_body_html(course: dict[str, Any]) -> str:
    for key in ("lander_html", "raw_enrollware_html", "original_html"):
        value = safe_text(course.get(key)).strip()
        if value:
            return value
    return "<p>Course details coming soon.</p>"


def build_html(course: dict[str, Any], sessions: list[dict[str, Any]]) -> str:
    raw_name = safe_text(course.get("original_course_name")).strip()
    title, subtitle, clarifier = display_title(course, raw_name)
    cert_body = safe_text(course.get("cert_body")).strip() or "CPR Training"
    image_src = pick_image(course)
    price_label = display_price_label(course, title)
    body_html = build_body_html(course)
    page_slug = course_url_slug(course)
    canonical = f"{BASE_URL}/courses/{page_slug}.html"
    meta_desc = meta_description(course, title)
    pills_html = hierarchy_pills(course, raw_name)
    sessions_html = build_session_blocks(course, sessions)

    schema = {
        "@context": "https://schema.org",
        "@type": "Course",
        "name": title,
        "description": meta_desc,
        "provider": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": BASE_URL,
        },
        "url": canonical,
    }

    schedule_url = safe_text(course.get("schedule_url")).strip()
    if schedule_url:
        schema["hasCourseInstance"] = {
            "@type": "CourseInstance",
            "url": schedule_url,
        }

    subtitle_html = f'<p class="subtitle">{html.escape(subtitle)}</p>' if subtitle else ""
    clarifier_html = f'<p class="clarifier">{html.escape(clarifier)}</p>' if clarifier else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} | {SITE_NAME}</title>
  <meta name="description" content="{html.escape(meta_desc)}">
  <link rel="canonical" href="{html.escape(canonical)}">
  <style>
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.5;
      color: #1c2733;
      background: linear-gradient(to bottom, #ffffff 0%, #eef6ff 100%);
    }}
    .wrap {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 20px;
    }}
    .hero {{
      background: #ffffff;
      border-radius: 16px;
      box-shadow: 0 8px 28px rgba(0,0,0,0.08);
      padding: 20px;
      display: grid;
      grid-template-columns: 1.5fr 0.9fr;
      gap: 20px;
      align-items: start;
    }}
    .hero img {{
      max-width: 100%;
      width: 320px;
      height: auto;
      border-radius: 12px;
      display: block;
      margin-left: auto;
    }}
    .crumb-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }}
    .crumb-pill {{
      display: inline-block;
      padding: 7px 12px;
      border-radius: 999px;
      background: #eef3fa;
      color: #25476c;
      font-size: 0.92rem;
      font-weight: 700;
    }}
    .crumb-pill.current {{
      background: #dce9f8;
      color: #0d62c7;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 2rem;
      line-height: 1.15;
    }}
    .eyebrow {{
      font-size: 0.95rem;
      font-weight: 700;
      color: #3a5289;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .subtitle {{
      margin: 0 0 10px;
      font-size: 1.02rem;
      color: #39526d;
      font-weight: 600;
    }}
    .price {{
      font-size: 1.18rem;
      font-weight: 700;
      margin: 10px 0 8px;
    }}
    .clarifier {{
      margin: 0 0 12px;
      font-size: 0.95rem;
      color: #5d6c7c;
    }}
    .sessions, .content, .credibility {{
      background: #ffffff;
      border-radius: 16px;
      box-shadow: 0 8px 28px rgba(0,0,0,0.06);
      padding: 20px;
      margin-top: 20px;
    }}
    .section-label {{
      font-size: 1rem;
      font-weight: 800;
      margin-bottom: 12px;
      text-transform: uppercase;
      color: #26405e;
      letter-spacing: 0.03em;
    }}
    .session-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
    }}
    .session-pill {{
      display: grid;
      gap: 2px;
      padding: 12px 14px;
      border-radius: 14px;
      background: #f7fbff;
      border: 1px solid #d9e7f4;
      text-decoration: none;
      color: #102338;
      transition: transform 0.12s ease, box-shadow 0.12s ease;
    }}
    .session-pill:hover {{
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    }}
    .session-date {{
      font-weight: 800;
      font-size: 0.97rem;
    }}
    .session-time, .session-location {{
      font-size: 0.92rem;
      color: #4f5f71;
    }}
    .session-cta {{
      margin-top: 6px;
      font-size: 0.92rem;
      font-weight: 800;
      color: #0d62c7;
    }}
    .session-curtain {{
      margin-top: 14px;
    }}
    .session-curtain summary {{
      cursor: pointer;
      font-weight: 700;
      color: #244d79;
      margin-bottom: 10px;
    }}
    .session-grid.extra {{
      margin-top: 10px;
    }}
    .full-schedule-row {{
      margin-top: 14px;
    }}
    .full-schedule-link {{
      font-weight: 700;
      color: #0d62c7;
      text-decoration: none;
    }}
    .empty-note {{
      margin: 0;
    }}
    .credibility h2 {{
      margin-top: 0;
    }}
    a {{
      color: #0d62c7;
    }}
    @media (max-width: 860px) {{
      .hero {{
        grid-template-columns: 1fr;
      }}
      .hero img {{
        margin: 0 auto;
      }}
    }}
  </style>
  <script type="application/ld+json">
{json.dumps(schema, indent=2)}
  </script>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div>
        {pills_html}
        <div class="eyebrow">{html.escape(cert_body)}</div>
        <h1>{html.escape(title)}</h1>
        {subtitle_html}
        <div class="price">{html.escape(price_label)}</div>
        {clarifier_html}
      </div>
      <div>
        <img src="{html.escape(image_src)}" alt="{html.escape(title)}">
      </div>
    </section>

    {sessions_html}

    <section class="content">
      {body_html}
    </section>

    <section class="credibility">
      <h2>Need Training for a Team?</h2>
      <p>
        910CPR supports employers, schools, and facility leaders who need training that is defensible,
        predictable, documented, and renewable.
      </p>
      <p>
        We can help with recurring staff training, organized scheduling, and practical compliance-minded delivery.
      </p>
    </section>
  </div>
</body>
</html>
"""


def build_index_row(course: dict[str, Any], title: str, page_slug: str, session_count: int) -> dict[str, Any]:
    return {
        "course_id": safe_text(course.get("course_id")),
        "clean_title": safe_text(course.get("clean_title")),
        "lander_title": safe_text(course.get("lander_title")),
        "display_title": title,
        "slug": page_slug,
        "url": f"/courses/{page_slug}.html",
        "schedule_url": safe_text(course.get("schedule_url")),
        "cert_body": safe_text(course.get("cert_body")),
        "price": course.get("price"),
        "upcoming_sessions_found": session_count,
    }


def main() -> None:
    if not ARCHIVE_PATH.exists():
        raise FileNotFoundError(f"Archive not found: {ARCHIVE_PATH}")
    if not SCHEDULE_PATH.exists():
        raise FileNotFoundError(f"Schedule feed not found: {SCHEDULE_PATH}")

    ensure_dir(OUTPUT_DIR)

    archive = load_json(ARCHIVE_PATH)
    schedule_payload = load_json(SCHEDULE_PATH)
    sessions = schedule_payload.get("sessions", [])
    if not isinstance(sessions, list):
        raise ValueError("public_schedule.json must contain a top-level 'sessions' list.")

    courses = archive.get("courses", [])
    if not isinstance(courses, list):
        raise ValueError("Archive must contain a top-level 'courses' array.")

    index_rows = []

    for course in courses:
        raw_name = safe_text(course.get("original_course_name")).strip()
        title, _subtitle, _clarifier = display_title(course, raw_name)
        page_slug = course_url_slug(course)
        output_path = OUTPUT_DIR / f"{page_slug}.html"

        matched_sessions = match_sessions(course, sessions)
        html_out = build_html(course, matched_sessions)
        output_path.write_text(html_out, encoding="utf-8")

        index_rows.append(build_index_row(course, title, page_slug, len(matched_sessions)))
        print(f"Wrote: {output_path}")

    INDEX_JSON_PATH.write_text(json.dumps(index_rows, indent=2), encoding="utf-8")
    print(f"Wrote: {INDEX_JSON_PATH}")
    print(f"Built {len(index_rows)} course landers.")


if __name__ == "__main__":
    main()