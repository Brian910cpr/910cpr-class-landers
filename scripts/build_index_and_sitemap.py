import json
import re
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from html import unescape
from collections import defaultdict

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_status import BuildStatusReporter
from scripts.build_course_landers import COURSE_SESSION_ALIASES, TITLE_OVERRIDES
from supervisor.status_snapshot import write_status_snapshot

ROOT = Path(__file__).resolve().parents[1]

DOCS_DIR = ROOT / "docs"
CLASSES_DIR = DOCS_DIR / "classes"
COURSES_DIR = DOCS_DIR / "courses"
LOCATIONS_DIR = DOCS_DIR / "locations"

INDEX_FILE = DOCS_DIR / "index.html"
CLASSES_INDEX_FILE = CLASSES_DIR / "index.html"
COURSES_INDEX_FILE = COURSES_DIR / "index.html"
SITEMAP_FILE = DOCS_DIR / "sitemap.xml"
SCHEDULE_FUTURE_FILE = DOCS_DIR / "data" / "schedule_future.json"
CANONICAL_CLASS_REPORT_FILE = DOCS_DIR / "data" / "canonical_schedule_from_class_report.json"
REVIEWS_FILE = ROOT / "data" / "raw" / "reviews" / "reviews.json"

SITE_BASE = "https://www.910cpr.com"
GTM_ID = "GTM-PQS8DCBH"
PHONE_DISPLAY = "910-395-5193"
PHONE_LINK = "tel:+19103955193"
ENROLLWARE_SCHEDULE_URL = "https://coastalcprtraining.enrollware.com/site/coastalcprtraining/schedule"
GOOGLE_REVIEWS_URL = "https://www.google.com/maps/search/?api=1&query=910CPR%204018%20Shipyard%20Blvd%20Wilmington%20NC%2028403"
LOCAL_TZ = ZoneInfo("America/New_York")
COURSE_PAGE_VISIBLE_BATCH = 10


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

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


def telemetry_script(page_type: str, page_name: str) -> str:
    safe_page_name = str(page_name).replace("\\", "\\\\").replace('"', '\\"')
    return f"""
<script>
window.dataLayer = window.dataLayer || [];
window.dataLayer.push({{
  event: "page_context",
  page_type: "{page_type}",
  page_name: "{safe_page_name}"
}});
</script>
"""


def html_escape(text: str) -> str:
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def load_google_review_stats() -> dict:
    fallback = {"label": "450+ 5-star reviews on Google", "themes": review_theme_summaries()}
    if not REVIEWS_FILE.exists():
        return fallback

    try:
        payload = json.loads(REVIEWS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback

    reviews = payload.get("reviews", payload) if isinstance(payload, dict) else payload
    if not isinstance(reviews, list):
        return fallback

    five_star = [
        review
        for review in reviews
        if review.get("rating") == 5 or str(review.get("starRating", "")).upper() == "FIVE"
    ]
    label = f"{len(five_star)} 5-star reviews on Google" if five_star else fallback["label"]
    return {"label": label, "themes": review_theme_summaries()}


def review_theme_summaries() -> list[str]:
    return [
        "Students often mention knowledgeable instructors who make certification requirements easy to understand.",
        "Renewing providers regularly describe the classes as organized, direct, and respectful of their time.",
        "Reviewers commonly point to clear explanations, hands-on practice, and a class experience that feels manageable.",
    ]


def render_google_trust_block() -> str:
    stats = load_google_review_stats()
    themes = "".join(
        f"""
          <article class="review-snippet">
            <p>{html_escape(theme)}</p>
          </article>
""".rstrip()
        for theme in stats["themes"]
    )
    themes_html = f'<div class="review-snippets" aria-label="Common themes from Google reviews"><div class="review-theme-label">Common themes from Google reviews</div>{themes}</div>' if themes else ""
    return f"""
      <section class="top-trust" aria-label="910CPR trust and reviews">
        <div class="top-trust-copy">
          <div class="home-status-label">Serving North And South Carolina</div>
          <p>From the mountains to the coast, 910CPR helps healthcare teams, dental offices, schools, workplaces, and students meet real certification requirements with clear, organized classes.</p>
        </div>
        <a class="google-review-card" href="{GOOGLE_REVIEWS_URL}" target="_blank" rel="noopener noreferrer" aria-label="Open 910CPR Google reviews in a new tab">
          <span class="review-stars review-stars-large" aria-hidden="true">★★★★★</span>
          <strong>Trusted by {html_escape(stats['label'])}</strong>
          <em>As of May 5, 2026</em>
          <span>Read 910CPR reviews on Google</span>
        </a>
        {themes_html}
      </section>
""".rstrip()


def strip_html(text: str) -> str:
    if text is None:
        return ""
    text = unescape(str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def short_slug(text: str, max_len: int = 80) -> str:
    clean = strip_html(text).lower()
    clean = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
    if len(clean) > max_len:
        clean = clean[:max_len].rstrip("-")
    return clean or "untitled"


def extract_first(pattern: str, text: str, flags=0, default: str = "") -> str:
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else default


def extract_meta(content: str, name: str) -> str:
    pattern = rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\'](.*?)["\']'
    return unescape(extract_first(pattern, content, flags=re.I | re.S))


def extract_link_href(content: str, rel_value: str) -> str:
    pattern = rf'<link[^>]+rel=["\']{re.escape(rel_value)}["\'][^>]+href=["\'](.*?)["\']'
    return unescape(extract_first(pattern, content, flags=re.I | re.S))


def extract_tag_text(content: str, tag: str) -> str:
    pattern = rf"<{tag}[^>]*>(.*?)</{tag}>"
    return strip_html(extract_first(pattern, content, flags=re.I | re.S))


def parse_page_context(content: str) -> dict:
    """
    Extract pageContext from:
      const pageContext = { ... };
    and convert it to JSON-ish.
    """
    m = re.search(r"const\s+pageContext\s*=\s*\{(.*?)\};", content, flags=re.S)
    if not m:
        return {}

    obj_text = "{" + m.group(1) + "}"

    # Quote bare keys: page_type: -> "page_type":
    obj_text = re.sub(r'([{\s,])([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', obj_text)

    # Remove trailing commas before } or ]
    obj_text = re.sub(r",(\s*[}\]])", r"\1", obj_text)

    try:
        return json.loads(obj_text)
    except json.JSONDecodeError:
        return {}


def parse_json_ld_event(content: str) -> dict:
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        content,
        flags=re.I | re.S,
    )

    for block in blocks:
        raw = block.strip()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict) and parsed.get("@type") == "Event":
            return parsed

        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and item.get("@type") == "Event":
                    return item

    return {}


def clean_location_name(location: str) -> str:
    value = strip_html(location)
    if value.startswith("::"):
        value = value[2:].strip()
    return value or "Unknown Location"


def normalize_course_key(value: str) -> str:
    return short_slug(value or "", max_len=120)


def parse_local_datetime(value: str) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(LOCAL_TZ)


def is_valid_course_token(value: str) -> bool:
    token = str(value or "").strip()
    return bool(token and token not in {"0", "None", "none", "null", "NULL"})


def extract_course_token_from_schedule_url(url: str) -> str:
    match = re.search(r"#ct([^&#]+)", str(url or ""))
    token = match.group(1).strip() if match else ""
    return token if is_valid_course_token(token) else ""


def build_exact_schedule_url(course_id: str, course_number: str) -> str:
    token = course_id if is_valid_course_token(course_id) else course_number
    token = str(token or "").strip()
    if token:
        return f"https://coastalcprtraining.enrollware.com/schedule#ct{token}"
    return ENROLLWARE_SCHEDULE_URL


def infer_parent_hub(course_name: str) -> str:
    upper = strip_html(course_name).upper()
    if "ACLS" in upper:
        return "/acls.html"
    if "PALS" in upper:
        return "/pals.html"
    if "HEARTSAVER" in upper:
        return "/heartsaver.html"
    if "USCG" in upper or "ELEMENTARY FIRST AID" in upper:
        return "/uscg-elementary-first-aid-cpr.html"
    if "BLS" in upper:
        return "/bls.html"
    if "GROUP" in upper or "ONSITE" in upper:
        return "/group-training.html"
    return "/index.html"


def course_description(course_name: str) -> str:
    title = strip_html(course_name)
    upper = title.upper()
    if "HEARTSAVER" in upper or "FIRST AID" in upper or "CPR AED" in upper or "CPR/AED" in upper:
        return f"See current upcoming dates for {title}, with direct registration links plus practical CPR, AED, choking, naloxone, stroke, seizure, asthma, heat illness, burn, and first aid response topics."
    if "BLS" in upper:
        return f"See current upcoming dates for {title}, with direct registration links and healthcare-provider CPR, AED, ventilation, choking response, and team communication practice."
    if "ACLS" in upper:
        return f"See upcoming {title} options with direct registration, scenario-based team response, cardiac arrest, stroke recognition, airway, rhythm, and postarrest care topics."
    if "PALS" in upper:
        return f"See upcoming {title} options with direct registration, pediatric assessment, respiratory support, shock, cardiac arrest, and team communication topics."
    if "HEARTCODE" in upper or "SKILLS" in upper:
        return f"Browse upcoming hands-on skills sessions for {title}. Choose a future date, register directly, or use the full course calendar for additional openings."
    if "RENEW" in upper or "UPDATE" in upper:
        return f"See upcoming renewal dates for {title}. These pages stay focused on current bookable sessions instead of historical archives."
    return f"See current upcoming dates for {title}, with direct registration links and a clean course-specific schedule view."


def load_schedule_future_sessions() -> list[dict]:
    source_file = SCHEDULE_FUTURE_FILE
    if CANONICAL_CLASS_REPORT_FILE.exists():
        try:
            canonical = json.loads(CANONICAL_CLASS_REPORT_FILE.read_text(encoding="utf-8"))
            if canonical.get("build", {}).get("source_mode") == "class_report_authoritative":
                source_file = CANONICAL_CLASS_REPORT_FILE
        except Exception:
            source_file = SCHEDULE_FUTURE_FILE
    if not source_file.exists():
        return []
    payload = json.loads(source_file.read_text(encoding="utf-8"))
    sessions = payload.get("sessions", []) if isinstance(payload, dict) else []
    out: list[dict] = []
    for session in sessions:
        if not isinstance(session, dict):
            continue
        enriched = dict(session)
        enriched["_parsed_start"] = parse_local_datetime(enriched.get("start_at", ""))
        enriched["_source_file"] = str(source_file)
        out.append(enriched)
    out.sort(key=lambda item: ((item.get("_parsed_start") or datetime.max.replace(tzinfo=LOCAL_TZ)), str(item.get("session_id", ""))))
    return out


def public_session_source_label(sessions: list[dict]) -> str:
    if not sessions:
        return str(SCHEDULE_FUTURE_FILE)
    source = str(sessions[0].get("_source_file") or SCHEDULE_FUTURE_FILE)
    try:
        return str(Path(source).relative_to(ROOT))
    except Exception:
        return source


def schedule_future_to_public_session(session: dict) -> dict | None:
    session_id = str(session.get("session_id") or session.get("id") or "").strip()
    if not session_id:
        return None

    start = session.get("_parsed_start") or parse_local_datetime(session.get("start_at", ""))
    if start:
        display_date = start.strftime("%B %d, %Y")
        display_time = start.strftime("%I:%M %p").lstrip("0")
        date_key = start.strftime("%Y-%m-%d")
        date_label = start.strftime("%a, %b %-d") if sys.platform != "win32" else start.strftime("%a, %b %#d")
        start_sort = start.isoformat()
    else:
        display_date = ""
        display_time = ""
        date_key = ""
        date_label = ""
        start_sort = ""

    course_name = str(session.get("course_name") or session.get("course") or session.get("title") or "CPR Class").strip()
    location_name = clean_location_name(
        str(session.get("location_display") or session.get("location_name") or session.get("location") or "").strip()
    )
    city = str(session.get("city") or "").strip()
    if not city:
        location_upper = location_name.upper()
        if "WILMINGTON" in location_upper:
            city = "Wilmington"
        elif "BURGAW" in location_upper:
            city = "Burgaw"
        elif "HOLLY RIDGE" in location_upper:
            city = "Holly Ridge"
        elif "JACKSONVILLE" in location_upper:
            city = "Jacksonville"
    price = session.get("price")
    if price in (None, ""):
        price_label = ""
    else:
        try:
            price_label = f"${float(price):.0f}"
        except Exception:
            price_label = str(price).strip()
    register_url = str(session.get("registration_url") or session.get("register_url") or session.get("registration_link") or "").strip()
    status = str(session.get("session_status") or "").strip().lower()
    if status not in {"published", "active"}:
        return None
    if not re.match(r"^https://coastalcprtraining\.enrollware\.com/enroll\?(?:.*&)?id=\d+(?:&.*)?$", register_url):
        return None
    if session.get("is_full") is True:
        return None
    try:
        seats = session.get("available_seats")
        if seats not in (None, "") and int(seats) <= 0:
            return None
    except Exception:
        pass
    course_id = str(session.get("course_id") or "").strip()
    course_number = str(session.get("course_number") or "").strip()

    return {
        "session_id": session_id,
        "course_id": course_id if is_valid_course_token(course_id) else "",
        "course_number": course_number if is_valid_course_token(course_number) else "",
        "course_name": course_name,
        "course_slug": short_slug(str(session.get("course_slug") or course_name)),
        "location_name": location_name or "Unknown Location",
        "title": course_name,
        "meta_description": str(session.get("description") or "").strip(),
        "display_date": display_date,
        "display_time": display_time,
        "date_key": date_key,
        "date_label": date_label,
        "start_sort": start_sort,
        "city": city,
        "price": price_label,
        "canonical": f"{SITE_BASE}/classes/{session_id}.html",
        "local_path": f"/classes/{session_id}.html",
        "register_url": register_url,
        "schedule_url": build_exact_schedule_url(course_id, course_number),
        "source_file": str(session.get("_source_file") or SCHEDULE_FUTURE_FILE),
    }


def build_future_course_aliases(session: dict) -> set[str]:
    aliases: set[str] = set()
    course_name = str(session.get("course_name", "")).strip()
    course_id = str(session.get("course_id", "")).strip()
    course_upper = course_name.upper()
    if course_name:
        aliases.add(normalize_course_key(course_name))
    override = TITLE_OVERRIDES.get(course_id or "")
    if override:
        aliases.add(normalize_course_key(override.get("title", "")))
    for alias in COURSE_SESSION_ALIASES.get(course_id or "", []):
        aliases.add(normalize_course_key(alias))
    if "ACLS" in course_upper and "HEARTCODE" in course_upper:
        aliases.add(normalize_course_key("AHA ACLS HeartCode Skills Session"))
    if "BLS" in course_upper and "HEARTCODE" in course_upper:
        aliases.add(normalize_course_key("AHA BLS HeartCode Skills Session"))
    if "PALS" in course_upper and "HEARTCODE" in course_upper:
        aliases.add(normalize_course_key("AHA PALS HeartCode Skills Session"))
    if "HEARTSAVER" in course_upper and ("ONLINE" in course_upper or "SKILLS" in course_upper):
        aliases.add(normalize_course_key("AHA Heartsaver Skills Session"))
    return {alias for alias in aliases if alias}


def session_matches_course(session: dict, course_meta: dict) -> bool:
    session_course_id = str(session.get("course_id", "")).strip()
    session_course_number = str(session.get("course_number", "")).strip()

    course_ids = course_meta.get("course_ids", set())
    course_numbers = course_meta.get("course_numbers", set())
    if course_ids or course_numbers:
        return (session_course_id in course_ids and is_valid_course_token(session_course_id)) or (
            session_course_number in course_numbers and is_valid_course_token(session_course_number)
        )

    session_aliases = build_future_course_aliases(session)
    target_aliases = course_meta.get("normalized_aliases", set())
    return bool(session_aliases & target_aliases)


def render_course_session_rows(sessions: list[dict]) -> str:
    rows = []
    for index, session in enumerate(sessions):
        start = session.get("_parsed_start")
        if not start:
            continue
        hidden_attr = " hidden" if index >= COURSE_PAGE_VISIBLE_BATCH else ""
        date_label = start.strftime("%A, %B %d, %Y")
        time_label = start.strftime("%I:%M %p").lstrip("0")
        location = clean_location_name(session.get("location_display") or session.get("location_name") or "")
        register_url = str(session.get("registration_url", "")).strip()
        session_id = str(session.get("session_id", "")).strip()
        session_url = f"/classes/{session_id}.html#ForwardToEnrollware" if session_id else register_url
        register_html = (
            f'<a class="course-session-register" href="{html_escape(session_url)}" data-original-href="{html_escape(register_url)}">Book This Class</a>'
            if session_url
            else ""
        )
        end_raw = str(session.get("end_at", "")).strip()
        rows.append(
            f"""
<article class="course-session-row js-session-item" data-session-id="{html_escape(session_id)}" data-start="{html_escape(start.isoformat())}" data-end="{html_escape(end_raw)}" data-session-start="{html_escape(start.isoformat())}" data-course-session{hidden_attr}>
  <div class="course-session-when">
    <div class="course-session-date">{html_escape(date_label)}</div>
    <div class="course-session-time">{html_escape(time_label)}</div>
  </div>
  <div class="course-session-where">{html_escape(location)}</div>
  <div class="course-session-actions">{register_html}</div>
</article>
"""
        )
    return "".join(rows)


def render_classes_finder_index(
    sessions: list[dict],
    *,
    title: str = "Find CPR Classes | 910CPR",
    h1: str = "Find CPR, BLS, ACLS, PALS, and First Aid classes",
    intro: str = "Find an upcoming CPR, BLS, ACLS, PALS, or First Aid class by course, date, and location. Filters work together, so choosing one option narrows the other dropdowns to available combinations.",
    canonical_path: str = "/classes/index.html",
    page_name: str = "Class Finder",
) -> str:
    course_options = sorted({s["course_name"] for s in sessions if s.get("course_name")}, key=str.lower)
    date_options = []
    seen_dates = set()
    for s in sorted(sessions, key=lambda item: (item.get("start_sort", ""), item.get("course_name", ""))):
        date_key = s.get("date_key", "")
        if date_key and date_key not in seen_dates:
            seen_dates.add(date_key)
            date_options.append((date_key, s.get("date_label") or s.get("display_date") or date_key))
    location_options = sorted({s["location_name"] for s in sessions if s.get("location_name")}, key=str.lower)

    def option_html(value: str, label: str) -> str:
        return f'<option value="{html_escape(value)}">{html_escape(label)}</option>'

    course_select_options = "\n".join([option_html("", "All courses")] + [option_html(course, course) for course in course_options])
    date_select_options = "\n".join([option_html("", "All dates")] + [option_html(value, label) for value, label in date_options])
    location_select_options = "\n".join([option_html("", "All locations")] + [option_html(location, location) for location in location_options])

    result_cards = []
    for s in sessions:
        bits = []
        if s.get("display_date"):
            bits.append(s["display_date"])
        if s.get("display_time"):
            bits.append(s["display_time"])
        if s.get("location_name"):
            bits.append(s["location_name"])
        if s.get("city") and s["city"].lower() not in str(s.get("location_name", "")).lower():
            bits.append(s["city"])
        meta_line = " | ".join(html_escape(bit) for bit in bits if bit)
        price_html = f'<span class="class-finder-price">{html_escape(s["price"])}</span>' if s.get("price") else ""
        detail_link = f'<a class="class-finder-secondary" href="{html_escape(s["local_path"])}">Details</a>'
        register_link = (
            f'<a class="class-finder-primary" href="{html_escape(s["register_url"])}">Book This Class</a>'
            if s.get("register_url")
            else ""
        )
        result_cards.append(
            f"""
<article class="class-finder-card js-class-result"
  data-course="{html_escape(s.get('course_name', ''))}"
  data-date="{html_escape(s.get('date_key', ''))}"
  data-location="{html_escape(s.get('location_name', ''))}"
>
  <div>
    <h2>{html_escape(s.get("course_name", "CPR Class"))}</h2>
    <p class="class-finder-meta">{meta_line}</p>
    {price_html}
  </div>
  <div class="class-finder-actions">
    {register_link}
    {detail_link}
  </div>
</article>
""".rstrip()
        )

    finder_styles = """
<style>
.class-finder-hero {
  border: 1px solid #dbe4ee;
  border-radius: 20px;
  padding: 24px;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
}
.class-finder-hero p {
  max-width: 760px;
  color: #475569;
  font-size: 1.03rem;
}
.class-filter-panel {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
  gap: 12px;
  align-items: end;
  margin: 22px 0;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  background: #ffffff;
}
.class-filter-field label {
  display: block;
  margin-bottom: 6px;
  color: #334155;
  font-weight: 800;
}
.class-filter-field select,
.class-filter-reset {
  width: 100%;
  min-height: 46px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  background: #ffffff;
  color: #0f172a;
  font-size: 1rem;
  padding: 0 12px;
}
.class-filter-reset {
  cursor: pointer;
  font-weight: 800;
  background: #f8fafc;
}
.class-filter-summary {
  margin: 8px 0 14px;
  color: #475569;
  font-weight: 700;
}
.class-finder-results {
  display: grid;
  gap: 12px;
}
.class-finder-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: center;
  padding: 16px;
  border: 1px solid #dbe4ee;
  border-radius: 18px;
  background: #ffffff;
}
.class-finder-card[hidden] {
  display: none;
}
.class-finder-card h2 {
  margin: 0 0 6px;
  font-size: 1.08rem;
}
.class-finder-meta {
  margin: 0;
  color: #475569;
}
.class-finder-price {
  display: inline-block;
  margin-top: 8px;
  font-weight: 800;
  color: #0f172a;
}
.class-finder-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}
.class-finder-primary,
.class-finder-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 46px;
  padding: 0 16px;
  border-radius: 999px;
  font-weight: 800;
  text-decoration: none;
}
.class-finder-primary {
  background: #0f5e9c;
  color: #ffffff;
}
.class-finder-secondary {
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #0f172a;
}
.class-filter-empty {
  border: 1px dashed #cbd5e1;
  border-radius: 16px;
  padding: 18px;
  color: #475569;
  background: #f8fafc;
}
@media (max-width: 760px) {
  .class-filter-panel {
    grid-template-columns: 1fr;
  }
  .class-finder-card {
    grid-template-columns: 1fr;
  }
  .class-finder-actions {
    justify-content: stretch;
  }
  .class-finder-primary,
  .class-finder-secondary {
    width: 100%;
  }
}
@media (max-width: 640px) {
  .class-finder-hero {
    padding: 16px;
    border-radius: 16px;
  }
  .class-finder-hero h1 {
    margin-bottom: 8px;
    font-size: 1.45rem;
  }
  .class-finder-hero p {
    font-size: 0.95rem;
  }
  .class-filter-panel {
    gap: 10px;
    margin: 14px 0;
    padding: 12px;
    border-radius: 14px;
  }
  .class-filter-field label {
    margin-bottom: 4px;
    font-size: 0.9rem;
  }
  .class-filter-field select,
  .class-filter-reset {
    min-height: 42px;
    border-radius: 10px;
    font-size: 0.95rem;
  }
  .class-filter-summary {
    margin: 6px 0 10px;
    font-size: 0.92rem;
  }
  .class-finder-results {
    gap: 8px;
  }
  .class-finder-card {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 8px;
    align-items: center;
    padding: 10px 10px;
    border-radius: 12px;
  }
  .class-finder-card h2 {
    margin-bottom: 3px;
    font-size: 0.94rem;
    line-height: 1.18;
  }
  .class-finder-meta {
    font-size: 0.82rem;
    line-height: 1.25;
  }
  .class-finder-actions {
    flex-direction: column;
    align-items: stretch;
    justify-content: center;
    gap: 6px;
  }
  .class-finder-primary,
  .class-finder-secondary {
    width: auto;
    min-height: 34px;
    padding: 0 10px;
    border-radius: 10px;
    font-size: 0.84rem;
    white-space: nowrap;
  }
}
</style>
""".rstrip()

    finder_script = """
<script>
(function () {
  const controls = {
    course: document.getElementById("class-filter-course"),
    date: document.getElementById("class-filter-date"),
    location: document.getElementById("class-filter-location")
  };
  const cards = Array.from(document.querySelectorAll(".js-class-result"));
  const count = document.getElementById("class-filter-count");
  const empty = document.getElementById("class-filter-empty");
  const reset = document.getElementById("class-filter-reset");

  function currentState() {
    return {
      course: controls.course.value,
      date: controls.date.value,
      location: controls.location.value
    };
  }

  function matches(card, state, ignoreKey) {
    return Object.keys(controls).every(function (key) {
      if (key === ignoreKey || !state[key]) return true;
      return card.dataset[key] === state[key];
    });
  }

  function updateOptions(state) {
    Object.keys(controls).forEach(function (key) {
      const select = controls[key];
      Array.from(select.options).forEach(function (option) {
        if (!option.value) {
          option.disabled = false;
          option.hidden = false;
          return;
        }
        const available = cards.some(function (card) {
          return card.dataset[key] === option.value && matches(card, state, key);
        });
        option.disabled = !available;
        option.hidden = !available && select.value !== option.value;
      });
      if (select.value && select.selectedOptions[0] && select.selectedOptions[0].disabled) {
        select.value = "";
      }
    });
  }

  function applyFilters() {
    let state = currentState();
    updateOptions(state);
    state = currentState();
    let visible = 0;
    cards.forEach(function (card) {
      const show = matches(card, state);
      card.hidden = !show;
      card.style.display = show ? "" : "none";
      if (show) visible += 1;
    });
    count.textContent = visible + " class" + (visible === 1 ? "" : "es") + " found";
    empty.hidden = visible !== 0;
  }

  Object.keys(controls).forEach(function (key) {
    controls[key].addEventListener("change", applyFilters);
  });
  reset.addEventListener("click", function () {
    Object.keys(controls).forEach(function (key) {
      controls[key].value = "";
    });
    applyFilters();
  });
  applyFilters();
})();
</script>
""".rstrip()

    body = f"""
{finder_styles}
<section class="class-finder-hero">
  <p class="course-eyebrow">Upcoming class finder</p>
  <h1>{html_escape(h1)}</h1>
  <p>{html_escape(intro)}</p>
</section>

<section class="class-filter-panel" aria-label="Class filters">
  <div class="class-filter-field">
    <label for="class-filter-course">Course</label>
    <select id="class-filter-course">
      {course_select_options}
    </select>
  </div>
  <div class="class-filter-field">
    <label for="class-filter-date">Date</label>
    <select id="class-filter-date">
      {date_select_options}
    </select>
  </div>
  <div class="class-filter-field">
    <label for="class-filter-location">Location</label>
    <select id="class-filter-location">
      {location_select_options}
    </select>
  </div>
  <button class="class-filter-reset" id="class-filter-reset" type="button">Reset filters</button>
</section>

<p class="class-filter-summary" id="class-filter-count">{len(sessions)} classes found</p>
<div class="class-filter-empty" id="class-filter-empty" hidden>No classes match those filters. Try changing the course, date, or location.</div>
<section class="class-finder-results" aria-label="Class results">
  {''.join(result_cards)}
</section>
{finder_script}
""".strip()

    return page_template(
        title=title,
        description="Find upcoming CPR, BLS, ACLS, PALS, and First Aid classes by course, date, and location.",
        body_html=body,
        page_type="classes_index",
        page_name=page_name,
        canonical_path=canonical_path,
        robots_content="index,follow",
    )


def render_course_page_body(course_meta: dict, future_sessions: list[dict]) -> str:
    title = course_meta["course_name"]
    description = course_description(title)
    parent_hub = course_meta.get("parent_hub") or infer_parent_hub(title)
    schedule_url = course_meta.get("schedule_url") or parent_hub
    course_lander_cta_url = parent_hub

    if future_sessions:
        sessions_html = render_course_session_rows(future_sessions)
        load_more_html = ""
        if len(future_sessions) > COURSE_PAGE_VISIBLE_BATCH:
            load_more_html = '<button class="course-load-more" type="button" data-load-more>Load 10 more</button>'
        schedule_block = f"""
<section class="course-sessions js-live-session-group" data-empty-link="{html_escape(course_lander_cta_url)}" data-empty-link-label="See related course hub">
  <div class="course-section-head">
    <h2>Upcoming Dates</h2>
    <p>Only future sessions for this exact course are shown here.</p>
  </div>
  <div class="course-session-list" data-session-list>
    {sessions_html}
  </div>
  <div class="course-more-row">{load_more_html}</div>
</section>
"""
    else:
        schedule_block = f"""
<section class="course-sessions course-empty js-live-session-group" data-empty-link="{html_escape(course_lander_cta_url)}" data-empty-link-label="See related course hub">
  <div class="course-section-head">
    <h2>Upcoming Dates</h2>
  </div>
  <div class="js-live-session-empty">
    <p>No upcoming dates are currently listed for this course. Please contact us and we'll help you find the right class.</p>
    <p><a class="course-help-cta" href="{html_escape(course_lander_cta_url)}">See related course hub</a></p>
  </div>
</section>
"""

    return f"""
<section class="course-hero">
  <div class="course-hero-copy">
    <p class="course-eyebrow">Course Details</p>
    <h1>{html_escape(title)}</h1>
    <p class="course-description">{html_escape(description)}</p>
    <div class="course-cta-row">
      <a class="course-primary-cta" href="{html_escape(course_lander_cta_url)}">See related course hub</a>
      <a class="course-secondary-cta" href="{html_escape(parent_hub)}">Back to related hub</a>
    </div>
  </div>
</section>
{schedule_block}
<script>
(function () {{
  function refreshCourseLists() {{
    document.querySelectorAll('[data-session-list]').forEach(function (list) {{
      var items = Array.from(list.querySelectorAll('[data-course-session]'));
      items.forEach(function (item, index) {{
        if (index < {COURSE_PAGE_VISIBLE_BATCH}) {{
          item.hidden = false;
        }}
      }});
      var button = list.parentElement.querySelector('[data-load-more]');
      if (!button) return;
      if (items.length <= {COURSE_PAGE_VISIBLE_BATCH}) {{
        button.hidden = true;
      }}
    }});
  }}

  function wireLoadMore() {{
    document.querySelectorAll('[data-load-more]').forEach(function (button) {{
      button.addEventListener('click', function () {{
        var section = button.closest('.course-sessions');
        if (!section) return;
        var hidden = Array.from(section.querySelectorAll('[data-course-session][hidden]')).slice(0, {COURSE_PAGE_VISIBLE_BATCH});
        hidden.forEach(function (item) {{ item.hidden = false; }});
        if (!section.querySelector('[data-course-session][hidden]')) {{
          button.hidden = true;
        }}
      }});
    }});
  }}

  window.addEventListener('DOMContentLoaded', function () {{
    if (window.pruneExpiredSessions) {{
      window.pruneExpiredSessions();
    }}
    refreshCourseLists();
    wireLoadMore();
  }});
}})();
</script>
"""


def page_template(
    title: str,
    description: str,
    body_html: str,
    page_type: str,
    page_name: str,
    canonical_path: str,
    robots_content: str = "index,follow",
) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html_escape(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{html_escape(description)}">
<meta name="robots" content="{html_escape(robots_content)}">
<link rel="canonical" href="{SITE_BASE}{canonical_path}">
<link rel="icon" type="image/png" href="/images/logo.png">
<link rel="shortcut icon" href="/images/logo.png">
<link rel="apple-touch-icon" href="/images/logo.png">
{render_gtm_head()}
<style>
body {{
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
  color: #111827;
  background: #ffffff;
  line-height: 1.45;
}}
.wrap {{
  max-width: 1180px;
  margin: 0 auto;
  padding: 16px;
}}
header, footer {{
  border-bottom: 1px solid #e5e7eb;
}}
footer {{
  border-top: 1px solid #e5e7eb;
  border-bottom: 0;
  margin-top: 30px;
}}
h1, h2, h3 {{
  line-height: 1.2;
}}
a {{
  color: #1d4ed8;
}}
ul {{
  margin-top: 10px;
}}
.meta {{
  color: #4b5563;
}}
.small {{
  font-size: 14px;
  color: #4b5563;
}}
.nav a {{
  margin-right: 12px;
}}
.section {{
  margin-top: 28px;
}}
.columns {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
}}
.plain-card {{
  border: 1px solid #e5e7eb;
  padding: 14px;
  border-radius: 8px;
}}
.course-hero, .course-sessions {{
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}}
.course-sessions {{
  margin-top: 22px;
}}
.course-eyebrow {{
  margin: 0 0 8px;
  color: #0f5e9c;
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}
.course-description {{
  max-width: 760px;
  color: #334155;
  font-size: 1.02rem;
}}
.course-cta-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 18px;
}}
.course-primary-cta, .course-secondary-cta, .course-session-register, .course-help-cta, .course-load-more {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 16px;
  border-radius: 999px;
  font-weight: 700;
  text-decoration: none;
  border: 1px solid transparent;
}}
.course-primary-cta, .course-session-register, .course-help-cta {{
  background: #0f5e9c;
  color: #ffffff;
}}
.course-secondary-cta, .course-load-more {{
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #0f172a;
}}
.course-section-head h2 {{
  margin-bottom: 4px;
}}
.course-section-head p {{
  margin-top: 0;
  color: #475569;
}}
.course-session-list {{
  display: grid;
  gap: 12px;
}}
.course-session-row {{
  display: grid;
  grid-template-columns: minmax(220px, 1.2fr) minmax(180px, 1fr) auto;
  gap: 16px;
  align-items: center;
  padding: 14px 16px;
  border: 1px solid #dbe4ee;
  border-radius: 16px;
  background: #f8fbff;
}}
.course-session-date {{
  font-weight: 800;
}}
.course-session-time, .course-session-where {{
  color: #475569;
}}
.course-more-row {{
  margin-top: 16px;
}}
.js-live-session-empty p {{
  color: #475569;
}}
@media (max-width: 760px) {{
  .course-session-row {{
    grid-template-columns: 1fr;
  }}
}}
</style>
</head>
<body>
{render_gtm_body()}
<header>
  <div class="wrap">
    <div class="site-brand-bar site-brand-bar-inline">
      <a class="site-brand-link" href="/index.html" aria-label="910CPR home">
        <img class="site-brand-logo" src="/images/logo.png" alt="910CPR logo" loading="eager" onerror="this.src='/images/910CPR_wave.jpg';this.onerror=null;">
        <span class="site-brand-wordmark">910CPR</span>
      </a>
    </div>
    <div class="nav small" style="margin-top:8px;">
      <a href="/index.html">Home</a>
      <a href="/bls.html">BLS</a>
      <a href="/acls.html">ACLS</a>
      <a href="/pals.html">PALS</a>
      <a href="/heartsaver.html">Heartsaver</a>
      <a href="{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
      <a href="{ENROLLWARE_SCHEDULE_URL}">Enrollware Schedule</a>
    </div>
  </div>
</header>

<div class="wrap">
{body_html}
</div>

<footer>
  <div class="wrap small">
    <p><strong>910CPR</strong></p>
    <p>CPR, BLS, ACLS, PALS, Heartsaver, and first aid training.</p>
    <p><a href="{PHONE_LINK}">{PHONE_DISPLAY}</a></p>
  </div>
</footer>

{telemetry_script(page_type, page_name)}
<script src="/assets/live-sessions.js"></script>
<script src="/assets/session-expiry.js"></script>
</body>
</html>"""


def render_homepage() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Find the Right CPR or Medical Training Class | 910CPR</title>
<meta name="description" content="Choose the right CPR, BLS, ACLS, PALS, Heartsaver, Red Cross, HSI, or USCG training path before selecting matching class dates.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{SITE_BASE}/">
<link rel="icon" type="image/png" href="/images/logo.png">
<link rel="shortcut icon" href="/images/logo.png">
<link rel="apple-touch-icon" href="/images/logo.png">
<link rel="stylesheet" href="/css/lander.css">
{render_gtm_head()}
<script type="application/ld+json">
{json.dumps({
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "@id": f"{SITE_BASE}/#organization",
  "name": "910CPR",
  "url": f"{SITE_BASE}/",
  "description": "Authorized American Heart Association Training Site providing CPR, BLS, ACLS, PALS & Heartsaver courses throughout Coastal North Carolina.",
  "areaServed": ["Wilmington NC", "Holly Ridge NC", "Jacksonville NC", "Burgaw NC", "Leland NC", "Coastal North Carolina"],
}, indent=2)}
</script>
</head>
<body>
{render_gtm_body()}
<div class="wrap">
  <div class="page-shell">
    <main class="card home-shell">
      <header class="site-brand-bar">
        <a class="site-brand-link" href="/index.html" aria-label="910CPR home">
          <img class="site-brand-logo" src="/images/logo.png" alt="910CPR logo" loading="eager" onerror="this.src='/images/910CPR_wave.jpg';this.onerror=null;">
          <span class="site-brand-wordmark">910CPR</span>
        </a>
      </header>
      <section class="hero home-hero">
        <div class="hero-main">
          <div class="eyebrow">CPR, BLS, ACLS, PALS, First Aid</div>
          <h1>Find the CPR or medical training course you need</h1>
          <p class="subhead">Answer a few simple questions, choose the course format that fits your requirement, and then pick a matching class date.</p>
          <div class="hero-actions">
            <a class="button primary" href="#class-finder">Help me choose a course</a>
            <a class="button secondary" href="/group-training.html">Need training for a team?</a>
          </div>
        </div>
        <div class="hero-side">
          <div class="trust-badge">
            <strong>Choose Course First</strong>
            <span>Start with your requirement, then compare only the dates that match that course and format.</span>
          </div>
          <div class="trust-badge">
            <strong>Enrollware Registration</strong>
            <span>Course pages keep the existing Enrollware registration paths for posted class dates.</span>
          </div>
        </div>
      </section>
{render_google_trust_block()}

      <section class="home-jumps course-pathway-jumps" aria-label="Jump to course pathways">
        <a class="jump-chip" href="#healthcare">Healthcare / BLS, ACLS, PALS</a>
        <a class="jump-chip" href="#workplace">Workplace / First Aid CPR AED</a>
        <a class="jump-chip" href="#arc">American Red Cross</a>
        <a class="jump-chip" href="#hsi">HSI</a>
        <a class="jump-chip" href="#uscg">USCG / Maritime</a>
        <a class="jump-chip" href="#not-sure">Not sure what I need</a>
      </section>

      <section class="home-finder" id="class-finder">
        <div class="section-heading">
          <div>
            <div class="eyebrow">Course Finder</div>
            <h2>Choose your course path before viewing dates</h2>
          </div>
          <p class="section-copy">The homepage no longer shows every class date at once. Pick the course family and delivery format first, then the matching course page will show dates and registration buttons.</p>
        </div>

        <div class="finder-grid" data-home-sections>
          <article class="finder-card finder-card-loading">
            <div class="finder-card-head">
              <div>
                <h3>Loading course pathways</h3>
                <p class="finder-card-copy">Choose a course family first, then view matching class dates.</p>
              </div>
            </div>
          </article>
        </div>
      </section>
    </main>
  </div>
</div>

<noscript>
  <div class="wrap">
    <div class="card home-noscript">
      <h2>Quick class links</h2>
      <p>Course pathway cards could not load in this browser. You can still choose a course page below.</p>
      <p><a class="button primary" href="/bls.html">BLS</a> <a class="button secondary" href="/acls.html">ACLS</a> <a class="button secondary" href="/pals.html">PALS</a> <a class="button secondary" href="/heartsaver.html">Heartsaver</a> <a class="button secondary" href="/heartsaver.html?program=Pediatric%20First%20Aid%20CPR%20AED%20Blended">Pediatric First Aid CPR AED</a> <a class="button secondary" href="/arc.html">ARC</a> <a class="button secondary" href="/hsi.html">HSI</a> <a class="button secondary" href="/uscg-elementary-first-aid-cpr.html">USCG</a> <a class="button secondary" href="/group-training.html">Group Training</a></p>
    </div>
  </div>
</noscript>

<script src="/assets/booking-home.js"></script>
<script src="/assets/session-expiry.js"></script>
{telemetry_script("home", "910CPR Homepage")}
</body>
</html>"""


# ---------------------------------------------------------------------
# Class page parsing
# ---------------------------------------------------------------------

def parse_class_page(path: Path) -> dict | None:
    content = path.read_text(encoding="utf-8", errors="ignore")

    canonical = extract_link_href(content, "canonical")
    title = extract_tag_text(content, "title")
    meta_description = extract_meta(content, "description")
    h1 = extract_tag_text(content, "h1")
    page_context = parse_page_context(content)
    event = parse_json_ld_event(content)

    # Ignore obvious non-class pages
    if not canonical or "/classes/" not in canonical:
        return None

    session_id = str(page_context.get("session_id", "")).strip()
    if not session_id:
        m = re.search(r"/classes/(\d+)\.html$", canonical)
        if m:
            session_id = m.group(1)

    if not session_id:
        return None

    course_name = (
        str(page_context.get("course_name", "")).strip()
        or str(event.get("name", "")).strip()
        or h1
        or title
    )

    raw_course_id = str(page_context.get("course_id", "")).strip()
    course_id = raw_course_id if is_valid_course_token(raw_course_id) else ""

    # Prefer pageContext location, then JSON-LD Event location
    location_name = str(page_context.get("location_name", "")).strip()
    if not location_name:
        location_name = (
            event.get("location", {}).get("name", "")
            if isinstance(event.get("location"), dict)
            else ""
        )
    location_name = clean_location_name(location_name)

    register_url = str(page_context.get("register_url", "")).strip()
    if not register_url:
        offers = event.get("offers", {})
        if isinstance(offers, dict):
            register_url = str(offers.get("url", "")).strip()

    schedule_url = str(page_context.get("schedule_url", "")).strip()
    schedule_course_token = extract_course_token_from_schedule_url(schedule_url)
    course_number = schedule_course_token or course_id

    # Use visible meta values when possible
    display_date = extract_first(
        r'<div class="meta-label">Date</div>\s*<div class="meta-value">(.*?)</div>',
        content,
        flags=re.I | re.S,
    )
    display_date = strip_html(display_date)

    display_time = extract_first(
        r'<div class="meta-label">Time</div>\s*<div class="meta-value">(.*?)</div>',
        content,
        flags=re.I | re.S,
    )
    display_time = strip_html(display_time)

    if not display_date and event.get("startDate"):
        display_date = str(event.get("startDate"))

    course_slug = str(page_context.get("course_slug", "")).strip()
    if not course_slug and course_name:
        course_slug = short_slug(course_name)

    local_path = f"/classes/{session_id}.html"

    return {
        "session_id": session_id,
        "course_id": course_id,
        "course_number": course_number,
        "course_name": course_name or "CPR Class",
        "course_slug": course_slug,
        "location_name": location_name or "Unknown Location",
        "title": title or course_name or f"Class {session_id}",
        "meta_description": meta_description or "",
        "display_date": display_date or "",
        "display_time": display_time or "",
        "canonical": canonical,
        "local_path": local_path,
        "register_url": register_url,
        "schedule_url": schedule_url,
        "source_file": str(path),
    }


def build():
    reporter = BuildStatusReporter("build_index_and_sitemap")
    reporter.set_context(
        inputs=[CLASSES_DIR, SCHEDULE_FUTURE_FILE, REVIEWS_FILE],
        outputs=[INDEX_FILE, CLASSES_INDEX_FILE, COURSES_INDEX_FILE, COURSES_DIR, LOCATIONS_DIR, SITEMAP_FILE],
    )
    reporter.waiting(total=0)
    if not CLASSES_DIR.exists():
        raise FileNotFoundError(f"Missing classes directory: {CLASSES_DIR}")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    CLASSES_DIR.mkdir(parents=True, exist_ok=True)
    COURSES_DIR.mkdir(parents=True, exist_ok=True)
    LOCATIONS_DIR.mkdir(parents=True, exist_ok=True)

    class_files = sorted(
        p for p in CLASSES_DIR.glob("*.html")
        if p.name.lower() != "index.html"
    )
    reporter.start(total=len(class_files))

    parsed_class_page_sessions = []
    for path in class_files:
        parsed = parse_class_page(path)
        if parsed and parsed.get("course_name", "").strip().lower() != "course":
            parsed_class_page_sessions.append(parsed)

    future_sessions = load_schedule_future_sessions()
    future_session_source = public_session_source_label(future_sessions)
    sessions = [
        public_session
        for public_session in (schedule_future_to_public_session(session) for session in future_sessions)
        if public_session is not None
    ]

    # Sort by best available date text, then session id
    sessions.sort(key=lambda s: (s.get("display_date", ""), s.get("display_time", ""), s.get("session_id", "")))

    course_groups: dict[str, list[dict]] = defaultdict(list)
    location_groups: dict[str, list[dict]] = defaultdict(list)

    for s in sessions:
        course_groups[s["course_name"]].append(s)
        location_groups[s["location_name"]].append(s)

    course_pages: list[dict] = []
    for course_name, items in sorted(course_groups.items(), key=lambda x: x[0].lower()):
        slug = short_slug(course_name)
        course_ids = {str(item.get("course_id", "")).strip() for item in items if is_valid_course_token(item.get("course_id", ""))}
        course_numbers = {str(item.get("course_number", "")).strip() for item in items if is_valid_course_token(item.get("course_number", ""))}
        normalized_aliases = {normalize_course_key(course_name)}
        normalized_aliases.update(normalize_course_key(item.get("title", "")) for item in items if item.get("title"))
        page_meta = {
            "course_name": course_name,
            "slug": slug,
            "course_ids": course_ids,
            "course_numbers": course_numbers,
            "normalized_aliases": {alias for alias in normalized_aliases if alias},
            "primary_course_id": sorted(course_ids)[0] if course_ids else "",
            "primary_course_number": sorted(course_numbers)[0] if course_numbers else "",
            "parent_hub": infer_parent_hub(course_name),
        }
        page_meta["schedule_url"] = (
            build_exact_schedule_url(page_meta["primary_course_id"], page_meta["primary_course_number"])
            if page_meta["primary_course_id"] or page_meta["primary_course_number"]
            else page_meta["parent_hub"]
        )
        matched_future = [session for session in future_sessions if session_matches_course(session, page_meta)]
        if matched_future and not (page_meta["primary_course_id"] or page_meta["primary_course_number"]):
            first_match = matched_future[0]
            page_meta["primary_course_id"] = str(first_match.get("course_id", "")).strip()
            page_meta["primary_course_number"] = str(first_match.get("course_number", "")).strip()
            if page_meta["primary_course_id"] or page_meta["primary_course_number"]:
                page_meta["schedule_url"] = build_exact_schedule_url(page_meta["primary_course_id"], page_meta["primary_course_number"])
        course_pages.append({"meta": page_meta, "future_sessions": matched_future})

    # -----------------------------------------------------------------
    # Root index
    # -----------------------------------------------------------------
    INDEX_FILE.write_text(render_homepage(), encoding="utf-8")

    # -----------------------------------------------------------------
    # Classes index
    # -----------------------------------------------------------------
    CLASSES_INDEX_FILE.write_text(render_classes_finder_index(sessions), encoding="utf-8")

    # -----------------------------------------------------------------
    # Courses index
    # -----------------------------------------------------------------
    COURSES_INDEX_FILE.write_text(
        render_classes_finder_index(
            sessions,
            title="Find a Course | 910CPR",
            h1="Find a Course",
            intro="Find upcoming CPR, BLS, ACLS, PALS, and First Aid classes by course, date, and location.",
            canonical_path="/courses/index.html",
            page_name="Course Finder",
        ),
        encoding="utf-8",
    )

    # Individual /courses/ pages are generated by scripts.build_courses.
    # This script owns the root index, archive indexes, locations, and sitemap.

    # -----------------------------------------------------------------
    # Location pages
    # -----------------------------------------------------------------
    current_location_files = {
        LOCATIONS_DIR / f"{short_slug(location_name)}.html"
        for location_name in location_groups.keys()
    }
    removed_stale_location_pages = 0
    for existing_location_page in LOCATIONS_DIR.glob("*.html"):
        if existing_location_page not in current_location_files:
            existing_location_page.unlink()
            removed_stale_location_pages += 1

    for location_name, items in location_groups.items():
        slug = short_slug(location_name)

        lines = []
        for s in items:
            bits = [s["course_name"]]
            if s["display_date"]:
                bits.append(s["display_date"])
            if s["display_time"]:
                bits.append(s["display_time"])

            line = " | ".join(html_escape(x) for x in bits if x)
            detail_link = f'<a href="{s["local_path"]}">Details</a>'
            session_forward = f'{s["local_path"]}#ForwardToEnrollware'
            register_link = f' | <a href="{session_forward}" data-original-href="{s["register_url"]}">Book This Class</a>' if s["register_url"] else ""

            lines.append(
                f"<li class=\"js-session-item\" data-session-id=\"{html_escape(str(s.get('session_id', '')).strip())}\" data-start=\"{html_escape(str(s.get('display_date', '')).strip())}\">{line} | {detail_link}{register_link}</li>"
            )

        (LOCATIONS_DIR / f"{slug}.html").write_text(
            page_template(
                title=f"Classes in {location_name} | 910CPR",
                description=f"Archive support index of generated class pages in {location_name}.",
                body_html=f"""
<h1>Classes in {html_escape(location_name)}</h1>
<p class="meta">Archive support page for generated location listings. Use the homepage and hub pages for current public availability.</p>
<section class="course-hero">
  <div class="course-hero-copy">
    <p class="course-eyebrow">Archive Support Page</p>
    <h2>Looking for a current class instead of historical listings?</h2>
    <p class="course-description">This page remains available for archive support and crawl coverage, but current public booking flows live on the homepage and family hubs.</p>
    <div class="course-cta-row">
      <a class="course-primary-cta" href="/index.html">Find current classes</a>
      <a class="course-secondary-cta" href="{ENROLLWARE_SCHEDULE_URL}">Open full Enrollware schedule</a>
    </div>
  </div>
</section>
<section class="course-sessions">
  <div class="course-section-head">
    <h2>Archive listings</h2>
    <p>These are preserved support links, not the recommended path for booking.</p>
  </div>
  <details>
    <summary>View archived location sessions</summary>
    <ul>
{''.join(lines)}
    </ul>
  </details>
</section>
""",
                page_type="location",
                page_name=location_name,
                canonical_path=f"/locations/{slug}.html",
                robots_content="noindex,follow",
            ),
            encoding="utf-8",
        )

    # -----------------------------------------------------------------
    # Sitemap
    # -----------------------------------------------------------------
    urls = [
        f"{SITE_BASE}/",
        f"{SITE_BASE}/index.html",
        f"{SITE_BASE}/bls.html",
        f"{SITE_BASE}/acls.html",
        f"{SITE_BASE}/pals.html",
        f"{SITE_BASE}/heartsaver.html",
        f"{SITE_BASE}/arc",
        f"{SITE_BASE}/hsi",
        f"{SITE_BASE}/uscg-elementary-first-aid-cpr.html",
        f"{SITE_BASE}/group-training.html",
        f"{SITE_BASE}/request_group_session.html",
        f"{SITE_BASE}/classes/index.html",
        f"{SITE_BASE}/courses/index.html",
    ]

    for s in sessions:
        urls.append(f"{SITE_BASE}{s['local_path']}")

    for course_page in sorted(COURSES_DIR.glob("*.html")):
        if course_page.name.lower() == "index.html":
            continue
        urls.append(f"{SITE_BASE}/courses/{course_page.name}")

    for location_name in location_groups.keys():
        urls.append(f"{SITE_BASE}/locations/{short_slug(location_name)}.html")

    # Deduplicate while preserving order
    seen = set()
    deduped_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            deduped_urls.append(url)

    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for url in deduped_urls:
        sitemap_xml.append("  <url>")
        sitemap_xml.append(f"    <loc>{html_escape(url)}</loc>")
        sitemap_xml.append("  </url>")

    sitemap_xml.append("</urlset>")

    SITEMAP_FILE.write_text("\n".join(sitemap_xml), encoding="utf-8")
    reporter.done(
        current=len(class_files),
        total=len(class_files),
        last_output_file=SITEMAP_FILE,
        pages_generated=3 + len(course_groups) + len(location_groups),
        counts={
            "class_pages_scanned": len(class_files),
            "valid_class_pages": len(parsed_class_page_sessions),
            "public_sessions_from_canonical_source": len(sessions),
            "public_session_source": future_session_source,
            "course_pages": len([p for p in COURSES_DIR.glob("*.html") if p.name.lower() != "index.html"]),
            "location_pages": len(location_groups),
            "stale_location_pages_removed": removed_stale_location_pages,
            "sitemap_urls": len(deduped_urls),
        },
    )
    write_status_snapshot()

    print(f"Scanned class pages: {len(class_files)}")
    print(f"Parsed valid class pages: {len(parsed_class_page_sessions)}")
    print(f"Public sessions source: {future_session_source}")
    print(f"Public sessions from canonical source: {len(sessions)}")
    print(f"Built root index: {INDEX_FILE}")
    print(f"Built classes index: {CLASSES_INDEX_FILE}")
    print(f"Built courses index: {COURSES_INDEX_FILE}")
    print(f"Scanned course pages in: {COURSES_DIR}")
    print(f"Built {len(location_groups)} location pages in: {LOCATIONS_DIR}")
    print(f"Removed stale location pages: {removed_stale_location_pages}")
    print(f"Built sitemap: {SITEMAP_FILE}")


if __name__ == "__main__":
    build()
