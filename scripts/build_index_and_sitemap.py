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
COURSE_VISIBILITY_POLICY_FILE = ROOT / "data" / "config" / "course_visibility_policy.json"

SITE_BASE = "https://www.910cpr.com"
GTM_ID = "GTM-PQS8DCBH"
PHONE_DISPLAY = "910-395-5193"
PHONE_LINK = "tel:+19103955193"
ENROLLWARE_SCHEDULE_URL = "https://coastalcprtraining.enrollware.com/site/coastalcprtraining/schedule"
GOOGLE_REVIEWS_URL = "https://www.google.com/maps/search/?api=1&query=910CPR%204018%20Shipyard%20Blvd%20Wilmington%20NC%2028403"
LOCAL_TZ = ZoneInfo("America/New_York")
COURSE_PAGE_VISIBLE_BATCH = 10
STALE_CLASS_INDEX_DIRS = (
    CLASSES_DIR / "cities",
    CLASSES_DIR / "certifying-bodies",
    CLASSES_DIR / "courses",
    CLASSES_DIR / "course-at-city",
    CLASSES_DIR / "months",
    CLASSES_DIR / "industries",
)
STALE_CLASS_INDEX_FALLBACK_DESTINATIONS = {
    "/bls.html",
    "/acls.html",
    "/pals.html",
    "/heartsaver.html",
    "/arc.html",
    "/hsi.html",
    "/uscg-elementary-first-aid-cpr.html",
    "/group-training.html",
    "/classes/",
}


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


def strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", unescape(value)).strip()


def infer_current_public_destination(context: str) -> str:
    text = strip_html(context).lower()
    if not text:
        return "/classes/"
    if any(term in text for term in ("uscg", "maritime", "coast guard", "elementary first aid")):
        return "/uscg-elementary-first-aid-cpr.html"
    if any(term in text for term in ("red cross", "arc ")):
        return "/arc.html"
    if any(term in text for term in ("hsi", "ashi")):
        return "/hsi.html"
    if "acls" in text:
        return "/acls.html"
    if "pals" in text:
        return "/pals.html"
    if "bls" in text or "basic life support" in text:
        return "/bls.html"
    if any(term in text for term in ("heartsaver", "cpr aed", "cpr/aed", "first aid cpr", "pediatric")):
        return "/heartsaver.html"
    if any(term in text for term in ("group", "onsite", "on-site", "workplace", "company training")):
        return "/group-training.html"
    return "/classes/"


def contain_stale_class_index_links() -> dict[str, int]:
    stats = {
        "files_checked": 0,
        "files_changed": 0,
        "missing_numeric_class_links_rewritten": 0,
        "fallback_class_index_links_corrected": 0,
        "existing_numeric_class_links_kept": 0,
    }
    link_re = re.compile(
        r"""<a(?P<attrs_before>[^>]*?)href=(?P<quote>["'])(?P<href>(?:/classes/(?P<session_id>\d+)\.html(?:#[^"']*)?|/bls\.html|/acls\.html|/pals\.html|/heartsaver\.html|/arc\.html|/hsi\.html|/uscg-elementary-first-aid-cpr\.html|/group-training\.html|/classes/))(?P=quote)(?P<attrs_after>[^>]*)>(?P<label>.*?)</a>""",
        re.IGNORECASE | re.DOTALL,
    )

    for directory in STALE_CLASS_INDEX_DIRS:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*.html")):
            stats["files_checked"] += 1
            original = path.read_text(encoding="utf-8", errors="replace")

            def replace(match: re.Match[str]) -> str:
                href = match.group("href")
                context = " ".join(
                    [
                        path.stem.replace("-", " "),
                        strip_html(match.group("label")),
                    ]
                )
                fallback_href = infer_current_public_destination(context)
                if match.group("session_id"):
                    target_path = href.split("#", 1)[0]
                    target_file = DOCS_DIR / target_path.lstrip("/")
                    if target_file.exists():
                        stats["existing_numeric_class_links_kept"] += 1
                        return match.group(0)
                    stats["missing_numeric_class_links_rewritten"] += 1
                elif href in STALE_CLASS_INDEX_FALLBACK_DESTINATIONS and href != fallback_href:
                    stats["fallback_class_index_links_corrected"] += 1
                else:
                    return match.group(0)
                return (
                    f"<a{match.group('attrs_before')}href={match.group('quote')}{fallback_href}{match.group('quote')}"
                    f"{match.group('attrs_after')}>{match.group('label')}</a>"
                )

            updated = link_re.sub(replace, original)
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                stats["files_changed"] += 1
    return stats


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


def load_course_visibility_policy() -> dict:
    if not COURSE_VISIBILITY_POLICY_FILE.exists():
        return {}
    try:
        payload = json.loads(COURSE_VISIBILITY_POLICY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def course_visibility_record(course_id: str | None, policy: dict | None = None) -> dict:
    policy = policy if isinstance(policy, dict) else load_course_visibility_policy()
    courses = policy.get("courses", {}) if isinstance(policy, dict) else {}
    record = courses.get(str(course_id or "").strip(), {}) if isinstance(courses, dict) else {}
    return record if isinstance(record, dict) else {}


def course_visibility_state(course_id: str | None, policy: dict | None = None) -> str:
    record = course_visibility_record(course_id, policy)
    state = str(record.get("state") or "").strip()
    if state:
        return state
    policy = policy if isinstance(policy, dict) else load_course_visibility_policy()
    return str(policy.get("default_state") or "active_public").strip() or "active_public"


def course_allows_classes_inventory(course_id: str | None, policy: dict | None = None) -> bool:
    state = course_visibility_state(course_id, policy)
    if state == "hidden":
        return False
    if state == "menu_only_suppressed":
        return False
    return True


def review_theme_summaries() -> list[str]:
    return [
        "Clear guidance when students are unsure which class they need.",
        "Organized classes that respect renewing providers' time.",
        "Hands-on practice that helps the skills feel manageable.",
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
    themes_html = f'<div class="review-snippets" aria-label="Review highlights">{themes}</div>' if themes else ""
    return f"""
      <section class="top-trust" aria-label="910CPR trust and reviews">
        <div class="top-trust-copy">
          <div class="home-status-label">Training that fits real requirements</div>
          <p>910CPR helps healthcare workers, students, dental offices, schools, childcare teams, workplaces, and maritime crews meet certification requirements without making the process harder than it needs to be.</p>
        </div>
        <a class="google-review-card" href="{GOOGLE_REVIEWS_URL}" target="_blank" rel="noopener noreferrer" aria-label="Open 910CPR Google reviews in a new tab">
          <span class="review-stars review-stars-large" aria-hidden="true">★★★★★</span>
          <strong>Trusted by {html_escape(stats['label']).replace(' on Google', '')}</strong>
          <span>Students and professionals often mention clear explanations, organized classes, and instructors who make the skills feel manageable.</span>
          <span>Read Google reviews</span>
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
    visibility_policy = load_course_visibility_policy()
    visibility_token = course_id if is_valid_course_token(course_id) else course_number
    if not course_allows_classes_inventory(visibility_token, visibility_policy):
        return None

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
    eyebrow: str = "Upcoming class inventory",
    show_category_cards: bool = False,
    show_inventory: bool = True,
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

    category_cards = [
        {
            "title": "Healthcare Provider",
            "description": "For nurses, EMTs, dental teams, clinical staff, healthcare students, and providers who need BLS, ACLS, or PALS.",
            "image": "/images/nurse%20doing%20CPR.jpg",
            "href": "/bls.html",
            "action": "Find BLS, ACLS, or PALS",
            "label": "Common requirements",
            "common": [
                {"label": "BLS", "href": "/bls.html"},
                {"label": "ACLS", "href": "/acls.html"},
                {"label": "PALS", "href": "/pals.html"},
                {"label": "HeartCode skills", "href": "/bls.html"},
            ],
            "link_label": "Choose your class",
            "links": [("BLS classes", "/bls.html"), ("ACLS classes", "/acls.html"), ("PALS classes", "/pals.html")],
        },
        {
            "title": "Workplace, Daycare, School, or Coach",
            "description": "For childcare, school staff, coaches, foster care, workplace safety, camps, and general CPR or First Aid requirements.",
            "image": "/images/HS-FA-CPR-AED.jpeg",
            "href": "/heartsaver.html",
            "action": "Find CPR / First Aid classes",
            "label": "Common requirements",
            "common": [
                {"label": "First Aid CPR AED", "href": "/heartsaver.html#hs-fa-cpr-aed-ip"},
                {"label": "CPR AED", "href": "/heartsaver.html#hs-cpr-aed-ip"},
                {"label": "Pediatric First Aid", "href": "/heartsaver.html?program=Pediatric%20First%20Aid%20CPR%20AED%20Blended"},
                {"label": "Family & Friends", "href": "/heartsaver.html"},
            ],
            "link_label": "Choose your class",
            "links": [
                ("First Aid CPR AED", "/heartsaver.html#hs-fa-cpr-aed-ip"),
                ("CPR AED", "/heartsaver.html#hs-cpr-aed-ip"),
                ("Pediatric First Aid CPR AED", "/heartsaver.html?program=Pediatric%20First%20Aid%20CPR%20AED%20Blended"),
                ("Family & Friends CPR", "/heartsaver.html"),
            ],
        },
        {
            "title": "Red Cross Required",
            "description": "Use this option only if your employer, school, or program specifically says American Red Cross.",
            "image": "/images/bystanderAED_JPEG.jpg",
            "href": "/arc.html",
            "action": "Find Red Cross classes",
            "label": "Common requirements",
            "common": [
                {"label": "ARC BLS", "href": "/arc.html"},
                {"label": "ARC First Aid CPR AED", "href": "/arc.html"},
                "Blended learning",
            ],
            "link_label": "Choose your class",
            "links": [("Red Cross BLS", "/arc.html"), ("Red Cross First Aid CPR AED", "/arc.html")],
        },
        {
            "title": "HSI Required",
            "description": "Use this option if your employer or program specifically asks for HSI, ASHI, or Health & Safety Institute training.",
            "image": "/images/4_cards_.jpg",
            "href": "/hsi.html",
            "action": "Find HSI classes",
            "label": "Common requirements",
            "common": [
                {"label": "HSI CPR AED", "href": "/hsi.html"},
                {"label": "HSI First Aid CPR AED", "href": "/hsi.html"},
                "Blended learning",
            ],
            "link_label": "Choose your class",
            "links": [("HSI CPR AED", "/hsi.html"), ("HSI First Aid CPR AED", "/hsi.html")],
        },
        {
            "title": "USCG / Maritime",
            "description": "For captains, mariners, vessel crews, and maritime employers who need USCG-aligned First Aid and CPR training.",
            "image": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 360'%3E%3Cdefs%3E%3ClinearGradient id='s' x1='0' x2='0' y1='0' y2='1'%3E%3Cstop offset='0' stop-color='%23dff3ff'/%3E%3Cstop offset='1' stop-color='%23f8fbff'/%3E%3C/linearGradient%3E%3ClinearGradient id='w' x1='0' x2='1' y1='0' y2='1'%3E%3Cstop offset='0' stop-color='%230f5e9c'/%3E%3Cstop offset='1' stop-color='%2338bdf8'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='640' height='360' fill='url(%23s)'/%3E%3Ccircle cx='520' cy='78' r='42' fill='%23facc15' opacity='.85'/%3E%3Cpath d='M0 250c58-28 110-28 168 0s110 28 168 0 110-28 168 0 88 30 136 6v104H0z' fill='url(%23w)'/%3E%3Cpath d='M72 228h398l-54 74H140z' fill='%230f172a'/%3E%3Cpath d='M138 168h196l58 60H104z' fill='%23fff' stroke='%230f172a' stroke-width='8' stroke-linejoin='round'/%3E%3Cpath d='M188 126h96v42h-96z' fill='%230f5e9c'/%3E%3Cpath d='M388 112h80v92h-80z' fill='%23fff' stroke='%230f172a' stroke-width='7' rx='10'/%3E%3Cpath d='M424 132v52M398 158h52' stroke='%23dc2626' stroke-width='16' stroke-linecap='round'/%3E%3Cpath d='M166 198h42M238 198h42M310 198h42' stroke='%230f5e9c' stroke-width='12' stroke-linecap='round'/%3E%3Cpath d='M28 300c48-18 86-18 134 0s86 18 134 0 86-18 134 0 86 18 134 0' fill='none' stroke='%23e0f2fe' stroke-width='12' stroke-linecap='round' opacity='.9'/%3E%3C/svg%3E",
            "href": "/uscg-elementary-first-aid-cpr.html",
            "action": "Find maritime classes",
            "label": "Common requirement",
            "common": [
                {"label": "USCG Elementary First Aid CPR AED", "href": "/uscg-elementary-first-aid-cpr.html"},
            ],
            "link_label": "Choose your class",
            "links": [("USCG Elementary First Aid CPR AED", "/uscg-elementary-first-aid-cpr.html")],
        },
        {
            "title": "Not Sure What I Need",
            "description": "Use this if the wording from your job, school, agency, or licensing board is unclear. We can help you avoid choosing the wrong class.",
            "image": "/images/confused-frustrated.png",
            "href": "/group-training.html",
            "action": "Help me choose",
            "label": "Best when",
            "common": [
                "Unclear requirement",
                {"label": "Group training", "href": "/group-training.html"},
                {"label": "Private class", "href": "/group-training.html"},
                "Employer request",
            ],
            "link_label": "Contact us",
            "links": [
                ("Call 910-395-5193", "tel:9103955193"),
                ("Request help choosing", "/request_group_session.html"),
                ("Group training request", "/group-training.html"),
            ],
        },
    ]
    category_cards_html = []
    for card in category_cards:
        common_items = []
        for item in card["common"]:
            if isinstance(item, dict) and item.get("href"):
                common_items.append(
                    f'<li><a class="class-category-chip-link" href="{html_escape(item["href"])}">{html_escape(item["label"])}</a></li>'
                )
            else:
                common_items.append(f'<li><span class="class-category-chip-muted">{html_escape(item)}</span></li>')
        common_html = "".join(common_items)
        links_html = "".join(
            f'<a href="{html_escape(href)}">{html_escape(label)}</a>'
            for label, href in card.get("links", [])
        )
        category_cards_html.append(
            f"""
<article class="class-category-card">
  <img src="{html_escape(card["image"])}" alt="" loading="lazy">
  <div class="class-category-copy">
    <h2>{html_escape(card["title"])}</h2>
    <p>{html_escape(card["description"])}</p>
    <strong>{html_escape(card["label"])}</strong>
    <ul>{common_html}</ul>
    <a class="class-category-action" href="{html_escape(card["href"])}">{html_escape(card["action"])}</a>
    <div class="class-category-links"><span>{html_escape(card["link_label"])}</span>{links_html}</div>
  </div>
</article>
""".rstrip()
        )

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
  padding: 18px 20px;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
}
.class-finder-hero h1 {
  margin-bottom: 8px;
}
.class-finder-hero p {
  max-width: 760px;
  color: #475569;
  font-size: 0.98rem;
}
.class-trust-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin: 14px 0 18px;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  background: #ffffff;
  color: #334155;
  font-size: 0.92rem;
}
.class-trust-strip strong {
  color: #0f172a;
}
.class-trust-strip .review-stars {
  color: #f59e0b;
  letter-spacing: 0.03em;
}
.class-category-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin: 16px 0 20px;
}
.class-category-card {
  overflow: hidden;
  border: 1px solid #dbe4ee;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
  min-width: 0;
}
.class-category-card img {
  display: block;
  width: 100%;
  height: 108px;
  object-fit: cover;
  background: #e2e8f0;
}
.class-category-copy {
  padding: 13px;
  min-width: 0;
}
.class-category-copy h2 {
  margin: 0 0 6px;
  font-size: 1rem;
}
.class-category-copy p {
  margin: 0;
  color: #475569;
  font-size: 0.9rem;
  line-height: 1.35;
}
.class-category-copy strong {
  display: block;
  margin-top: 10px;
  color: #0f172a;
  font-size: 0.78rem;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}
.class-category-copy ul {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 10px 0 12px;
  padding: 0;
  list-style: none;
}
.class-category-copy li {
  display: flex;
  min-width: 0;
}
.class-category-chip-link,
.class-category-chip-muted {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 3px 7px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
  max-width: 100%;
  overflow-wrap: anywhere;
  white-space: normal;
  text-decoration: none;
}
.class-category-chip-link {
  background: #e0f2fe;
  color: #0f5e9c;
  border: 1px solid #bae6fd;
}
.class-category-chip-link:hover,
.class-category-chip-link:focus-visible {
  background: #0f5e9c;
  color: #ffffff;
  outline: 2px solid #93c5fd;
  outline-offset: 2px;
}
.class-category-chip-muted {
  background: #f1f5f9;
  color: #64748b;
}
.class-category-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 0 12px;
  border-radius: 999px;
  background: #0f5e9c;
  color: #ffffff;
  font-weight: 800;
  text-decoration: none;
  font-size: 0.88rem;
  max-width: 100%;
  box-sizing: border-box;
  text-align: center;
}
.class-category-links {
  display: grid;
  gap: 5px;
  margin-top: 10px;
  font-size: 0.82rem;
}
.class-category-links span {
  color: #64748b;
  font-weight: 800;
}
.class-category-links a {
  color: #0f5e9c;
  font-weight: 800;
  text-decoration: none;
}
.class-category-links a:hover,
.class-category-links a:focus-visible {
  text-decoration: underline;
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
  .class-category-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
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
    padding: 14px;
    border-radius: 16px;
  }
  .class-finder-hero h1 {
    margin-bottom: 8px;
    font-size: 1.45rem;
  }
  .class-finder-hero p {
    font-size: 0.95rem;
  }
  .class-trust-strip {
    margin: 10px 0 12px;
    border-radius: 14px;
    font-size: 0.84rem;
  }
  .class-category-grid {
    grid-template-columns: 1fr;
    gap: 10px;
    margin: 12px 0 14px;
  }
  .class-category-card {
    display: grid;
    grid-template-columns: 72px minmax(0, 1fr);
    border-radius: 14px;
  }
  .class-category-card img {
    height: 100%;
    min-height: 118px;
  }
  .class-category-copy {
    padding: 9px;
  }
  .class-category-copy h2 {
    font-size: 0.96rem;
  }
  .class-category-copy p {
    font-size: 0.84rem;
  }
  .class-category-copy ul {
    gap: 4px;
    margin: 7px 0;
  }
  .class-category-copy li {
    line-height: 1.18;
  }
  .class-category-chip-link,
  .class-category-chip-muted {
    min-height: 40px;
    padding: 6px 8px;
    font-size: 0.7rem;
  }
  .class-category-action {
    min-height: 32px;
    padding: 0 9px;
    font-size: 0.8rem;
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

    category_section = (
        f"""
<section class="class-category-grid" aria-label="Choose the right training path">
  {''.join(category_cards_html)}
</section>
""".strip()
        if show_category_cards
        else ""
    )
    inventory_section = (
        f"""
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
        if show_inventory
        else ""
    )

    body = f"""
{finder_styles}
<section class="class-finder-hero">
  <p class="course-eyebrow">{html_escape(eyebrow)}</p>
  <h1>{html_escape(h1)}</h1>
  <p>{html_escape(intro)}</p>
</section>

<div class="class-trust-strip" aria-label="910CPR trust">
  <span class="review-stars" aria-hidden="true">★★★★★</span>
  <strong>Trusted by 450+ 5-star Google reviews</strong>
  <span>Serving healthcare, workplace, school, childcare, and maritime training needs.</span>
</div>

{category_section}
{inventory_section}
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


def render_heartsaver_bridge_course_page(*, title: str, description: str, canonical_path: str, primary_anchor: str) -> str:
    options = [
        {
            "title": "In-person class",
            "copy": "Choose this if you want the full classroom session with hands-on practice and instructor guidance.",
            "href": primary_anchor,
        },
        {
            "title": "Online + skills session",
            "copy": "Choose this when the course is available as blended learning: complete the online portion first, then attend the in-person skills session.",
            "href": primary_anchor.replace("-ip", "-bl"),
        },
        {
            "title": "See all Heartsaver options",
            "copy": "Compare First Aid CPR AED, CPR AED, Pediatric First Aid CPR AED, and related workplace/community training paths.",
            "href": "/heartsaver.html",
        },
    ]
    cards = "".join(
        f"""
<article class="training-option-card">
  <h3>{html_escape(option["title"])}</h3>
  <p>{html_escape(option["copy"])}</p>
  <a class="text-link strong-link" href="{html_escape(option["href"])}">View this option</a>
</article>
""".strip()
        for option in options
    )
    body = f"""
<section class="course-hero">
  <div class="course-hero-copy">
    <p class="course-eyebrow">Heartsaver Course Options</p>
    <h1>{html_escape(title)}</h1>
    <p class="course-description">{html_escape(description)}</p>
    <div class="course-cta-row">
      <a class="course-primary-cta" href="{html_escape(primary_anchor)}">See dates and options</a>
      <a class="course-secondary-cta" href="/classes/">Browse all classes</a>
    </div>
  </div>
</section>
<section class="slug-training-options">
  <div class="section-heading">
    <div>
      <div class="eyebrow">Choose delivery format</div>
      <h2>Pick the option that matches your requirement</h2>
    </div>
    <p class="section-copy">The Heartsaver hub shows the available delivery choices and upcoming dates from the current schedule.</p>
  </div>
  <div class="training-option-grid">
    {cards}
  </div>
</section>
""".strip()
    return page_template(
        title=f"{title} | 910CPR",
        description=description,
        body_html=body,
        page_type="course_bridge",
        page_name=title,
        canonical_path=canonical_path,
        robots_content="index,follow",
    )


def write_heartsaver_bridge_course_pages() -> None:
    bridges = [
        {
            "path": COURSES_DIR / "aha-heartsaver-cpr-aed.html",
            "title": "AHA Heartsaver CPR AED",
            "description": "Choose Heartsaver CPR AED in-person or blended options, then view upcoming dates on the Heartsaver hub.",
            "canonical_path": "/courses/aha-heartsaver-cpr-aed.html",
            "primary_anchor": "/heartsaver.html#hs-cpr-aed-ip",
        },
        {
            "path": COURSES_DIR / "heartsaver-first-aid.html",
            "title": "Heartsaver First Aid CPR AED",
            "description": "Choose Heartsaver First Aid CPR AED in-person or blended options, then view upcoming dates on the Heartsaver hub.",
            "canonical_path": "/courses/heartsaver-first-aid.html",
            "primary_anchor": "/heartsaver.html#hs-fa-cpr-aed-ip",
        },
    ]
    for bridge in bridges:
        bridge["path"].write_text(
            render_heartsaver_bridge_course_page(
                title=bridge["title"],
                description=bridge["description"],
                canonical_path=bridge["canonical_path"],
                primary_anchor=bridge["primary_anchor"],
            ),
            encoding="utf-8",
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
header .wrap {{
  padding-top: 10px;
  padding-bottom: 10px;
}}
.site-brand-link {{
  display: inline-flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}}
.site-brand-logo {{
  display: block;
  width: 92px;
  height: auto;
}}
.site-brand-wordmark {{
  font-weight: 800;
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
.nav {{
  margin-top: 6px;
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
  header .wrap {{
    padding-top: 6px;
    padding-bottom: 6px;
  }}
  .site-brand-logo {{
    width: 46px;
  }}
  .site-brand-link {{
    gap: 5px;
  }}
  .site-brand-wordmark {{
    font-size: 0.84rem;
  }}
  .nav {{
    margin-top: 0 !important;
    line-height: 1.18;
  }}
  .nav a {{
    display: inline-block;
    margin-right: 8px;
    margin-bottom: 2px;
  }}
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
      <a href="{ENROLLWARE_SCHEDULE_URL}">Full class schedule</a>
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
<meta name="description" content="Find the right CPR, First Aid, BLS, ACLS, PALS, Red Cross, HSI, or USCG training class for your job, school, employer, licensing board, or agency.">
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
          <div class="eyebrow home-hero-links" aria-label="Quick course links"><a href="/heartsaver.html">CPR</a><span aria-hidden="true">•</span><a href="/heartsaver.html">First Aid</a><span aria-hidden="true">•</span><a href="/bls.html">BLS</a><span aria-hidden="true">•</span><a href="/acls.html">ACLS</a><span aria-hidden="true">•</span><a href="/pals.html">PALS</a></div>
          <h1>Find the right CPR or medical training class</h1>
          <p class="subhead">Tell us what your job, school, employer, or licensing board asked for. We'll help you find the right class and the next available dates.</p>
          <div class="hero-actions">
            <a class="button primary" href="#class-finder">Choose your class</a>
            <a class="button secondary" href="/classes/">See upcoming classes</a>
          </div>
        </div>
        <div class="hero-side">
          <div class="trust-badge">
            <strong>Not sure what they meant?</strong>
            <span>Use the exact wording from your email, form, or job requirement. If it says BLS, ACLS, PALS, First Aid, Red Cross, HSI, or USCG, start below.</span>
          </div>
        </div>
      </section>

      <section class="home-finder" id="class-finder">
        <div class="section-heading">
          <div>
            <h2>Choose your class to see dates</h2>
          </div>
          <p class="section-copy">Pick the course name you were told to take. Each option opens the matching course page with delivery options and upcoming dates.</p>
        </div>

        <div class="finder-grid" data-home-sections>
          <article class="finder-card finder-card-loading">
            <div class="finder-card-head">
              <div>
                <h3>Loading course links</h3>
                <p class="finder-card-copy">Choose your class to see available dates.</p>
              </div>
            </div>
          </article>
        </div>
      </section>
{render_google_trust_block()}
    </main>
  </div>
</div>

<noscript>
  <div class="wrap">
    <div class="card home-noscript">
      <h2>Quick class links</h2>
      <p>Course links could not load in this browser. You can still choose a class below.</p>
      <p><a class="button primary" href="/bls.html">AHA BLS</a> <a class="button secondary" href="/acls.html">AHA ACLS</a> <a class="button secondary" href="/pals.html">AHA PALS</a> <a class="button secondary" href="/heartsaver.html">First Aid CPR AED</a> <a class="button secondary" href="/arc.html">Red Cross</a> <a class="button secondary" href="/hsi.html">HSI</a> <a class="button secondary" href="/uscg-elementary-first-aid-cpr.html">USCG / Maritime</a></p>
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
    CLASSES_INDEX_FILE.write_text(
        render_classes_finder_index(
            sessions,
            title="Upcoming CPR Classes | 910CPR",
            h1="Upcoming CPR, BLS, ACLS, PALS, and First Aid classes",
            intro="Use the filters to narrow current scheduled classes by course, date, and location. This page is for available class inventory; use Courses if you still need help choosing the right class.",
            canonical_path="/classes/index.html",
            page_name="Class Inventory",
            eyebrow="Upcoming class inventory",
            show_category_cards=False,
            show_inventory=True,
        ),
        encoding="utf-8",
    )

    # -----------------------------------------------------------------
    # Courses index
    # -----------------------------------------------------------------
    COURSES_INDEX_FILE.write_text(
        render_classes_finder_index(
            sessions,
            title="Find a Course | 910CPR",
            h1="Find a Course",
            intro="Choose the course family your job, school, employer, or licensing board named. If the wording is unclear, use Help me choose and we will help you avoid the wrong class.",
            canonical_path="/courses/index.html",
            page_name="Course Finder",
            eyebrow="Course chooser",
            show_category_cards=True,
            show_inventory=False,
        ),
        encoding="utf-8",
    )
    write_heartsaver_bridge_course_pages()

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
      <a class="course-secondary-cta" href="{ENROLLWARE_SCHEDULE_URL}">Open full class schedule</a>
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

    stale_class_index_containment = contain_stale_class_index_links()

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
            "stale_class_index_files_checked": stale_class_index_containment["files_checked"],
            "stale_class_index_files_changed": stale_class_index_containment["files_changed"],
            "missing_numeric_class_links_rewritten": stale_class_index_containment["missing_numeric_class_links_rewritten"],
            "fallback_class_index_links_corrected": stale_class_index_containment["fallback_class_index_links_corrected"],
            "existing_numeric_class_links_kept": stale_class_index_containment["existing_numeric_class_links_kept"],
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
    print(
        "Contained stale class index links: "
        f"{stale_class_index_containment['missing_numeric_class_links_rewritten']} rewritten, "
        f"{stale_class_index_containment['fallback_class_index_links_corrected']} corrected, "
        f"{stale_class_index_containment['existing_numeric_class_links_kept']} kept"
    )
    print(f"Built sitemap: {SITEMAP_FILE}")


if __name__ == "__main__":
    build()
