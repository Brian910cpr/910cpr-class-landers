import json
import re
import hashlib
import random
import argparse
from datetime import datetime
from functools import lru_cache
from html import escape, unescape
from pathlib import Path
from zoneinfo import ZoneInfo
from zipfile import ZipFile

try:
    from tqdm import tqdm
except ModuleNotFoundError:
    def tqdm(iterable, **_kwargs):
        return iterable

try:
    from scripts.title_cleaner import normalize_course_title, seo_title_for_session
    from scripts.build_metadata import apply_build_metadata, current_build_metadata
except ModuleNotFoundError:
    from title_cleaner import normalize_course_title, seo_title_for_session
    from build_metadata import apply_build_metadata, current_build_metadata

TZ = ZoneInfo("America/New_York")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_FILE = ROOT / "docs" / "data" / "schedule_future.json"
PRIMARY_FULL_DATA_FILE = ROOT / "data" / "schedule.json"
FALLBACK_FULL_DATA_FILE = ROOT / "docs" / "data" / "schedule.json"
FULL_DATA_FILE = PRIMARY_FULL_DATA_FILE if PRIMARY_FULL_DATA_FILE.exists() else FALLBACK_FULL_DATA_FILE
OUTPUT_DIR = ROOT / "docs" / "classes"
IMAGES_DIR = ROOT / "docs" / "images"
REVIEWS_SOURCE = ROOT / "data" / "raw" / "reviews"

GTM_ID = "GTM-PQS8DCBH"
UPCOMING_LIMIT = 10
REVIEWS_PER_PAGE = 3
MIN_REVIEW_LENGTH = 35

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
    text = unescape(str(text or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def display_course_name(course_raw: str) -> str:
    cleaned = normalize_course_title(course_raw) or strip_html(course_raw) or "Course"
    cleaned = re.sub(
        r"\b(CPR\s+Class|Training\s+Class|Class)\b$",
        "",
        cleaned,
        flags=re.I,
    ).strip(" -–—,:;/")
    return cleaned or "Course"


def seo_course_phrase(course_name: str) -> str:
    base = display_course_name(course_name)
    lower = base.lower()

    if "bls" in lower and "cpr" not in lower:
        return f"{base} CPR Certification"
    if "acls" in lower and "training" not in lower:
        return f"{base} Training"
    if "pals" in lower and "training" not in lower:
        return f"{base} Training"
    if "heartsaver" in lower and "training" not in lower:
        return f"{base} Training"
    if "cpr" not in lower and "aed" in lower:
        return f"{base} Training"
    return base


def slugify(text: str) -> str:
    text = display_course_name(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "course"


def short_slug(text: str, max_len: int = 70) -> str:
    clean = slugify(text)
    digest = hashlib.md5(clean.encode("utf-8")).hexdigest()[:8]
    if len(clean) > max_len:
        clean = clean[:max_len].rstrip("-")
    return f"{clean}-{digest}" if clean else digest


def is_valid_schedule_anchor(value: str) -> bool:
    token = str(value or "").strip()
    return bool(token and token not in {"0", "None", "none", "null", "NULL"})


def js_escape(value: str) -> str:
    if value is None:
        return ""
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def parse_dt(value):
    raw = str(value or "").strip()
    if not raw:
        return None

    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
    )

    for fmt in formats:
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TZ)
            return dt.astimezone(TZ)
        except Exception:
            pass

    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        return dt.astimezone(TZ)
    except Exception:
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


def clean_location_display(location: str) -> str:
    value = str(location or "").strip()
    if value.startswith("::"):
        value = value[2:].strip()
    return value


def audience_blurb(course_name: str) -> str:
    lower = course_name.lower()

    if "acls" in lower:
        return (
            "This class is commonly taken by nurses, paramedics, respiratory therapists, "
            "ER staff, ICU staff, and other clinicians who need advanced cardiovascular life support training."
        )
    if "pals" in lower:
        return (
            "This class is commonly taken by pediatric nurses, emergency clinicians, paramedics, "
            "and other providers who care for infants and children."
        )
    if "bls" in lower:
        return (
            "This class is commonly taken by healthcare workers, nursing students, dental staff, "
            "EMS personnel, and others who need professional-level CPR certification."
        )
    if "heartsaver" in lower or "cpr" in lower or "aed" in lower:
        return (
            "This class is commonly taken by teachers, childcare staff, fitness professionals, "
            "security personnel, church staff, office teams, and other workplace responders."
        )

    return (
        "This class supports both individual certification needs and organizations that need reliable, "
        "repeatable safety training for employees."
    )


def corporate_blurb(city: str, course_name: str) -> str:
    return (
        f"910CPR also supports employers in {city} that need documented, renewable training for staff. "
        f"If you need multiple employees trained in {display_course_name(course_name)}, "
        f"group and workplace options may be available."
    )


def make_schema(course_name: str, session_dt, location_name: str, city: str, state: str, register_url: str) -> str:
    start_iso = session_dt.isoformat() if session_dt else ""
    schema_name = seo_course_phrase(course_name)
    return f"""
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": {json.dumps(schema_name)},
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
    html_text = re.sub(
        r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
        "",
        html_text,
        flags=re.I | re.S,
    )
    return re.sub(r"\s+", " ", html_text).strip()


@lru_cache(maxsize=512)
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
            display_course_name(course_name),
        ]
    )

    exts = [".html", ".htm", ".txt"]

    for directory in candidate_dirs:
        if not directory.exists():
            continue

        for name in candidate_names:
            for ext in exts:
                path = directory / f"{name}{ext}"
                if path.exists():
                    return sanitize_description_html(path.read_text(encoding="utf-8", errors="ignore"))

        if course_id:
            for ext in exts:
                matches = sorted(directory.glob(f"{course_id}*{ext}"))
                if matches:
                    return sanitize_description_html(matches[0].read_text(encoding="utf-8", errors="ignore"))

    return ""


@lru_cache(maxsize=256)
def first_existing_image(*names: str) -> str:
    for name in names:
        path = IMAGES_DIR / name
        if path.exists():
            return f"/images/{name}"
    return ""


def default_logo_url() -> str:
    return first_existing_image("logo.png", "Logo.png", "LOGO.png")


def detect_cert_logo(course_name: str) -> str:
    course = course_name.lower()

    if "red cross" in course or course.startswith("arc ") or "arc " in course:
        return first_existing_image("0arc.png", "0ARC.png", "arc.png", "ARC.png")

    if "hsi" in course or "ashi" in course:
        return first_existing_image("0hsi.png", "0HSI.png", "hsi.png", "HSI.png")

    if any(token in course for token in ("aha", "heartsaver", "heartcode", "acls", "pals", "bls")):
        return first_existing_image("0aha.png", "0AHA.png", "aha.png", "AHA.png")

    return ""


def get_course_type_image(course_name: str) -> str:
    course = course_name.lower()

    if "bls" in course:
        return first_existing_image("bls.jpg", "bls.jpeg", "bls.png", "BLS.jpg", "BLS.png")
    if "acls" in course:
        return first_existing_image("acls.jpg", "acls.jpeg", "acls.png", "ACLS.jpg", "ACLS.png")
    if "pals" in course:
        return first_existing_image("pals.jpg", "pals.jpeg", "pals.png", "PALS.jpg", "PALS.png")
    if "heartsaver" in course:
        return first_existing_image(
            "heartsaver.jpg",
            "heartsaver.jpeg",
            "heartsaver.png",
            "Heartsaver.jpg",
            "Heartsaver.png",
        )

    return ""


def course_family_label(course_name: str) -> str:
    lower = display_course_name(course_name).lower()
    if "acls" in lower:
        return "ACLS"
    if "pals" in lower:
        return "PALS"
    if "heartcode" in lower and "bls" in lower:
        return "BLS"
    if "bls" in lower:
        return "BLS"
    if "heartsaver" in lower or "first aid" in lower or "cpr aed" in lower or "cpr/aed" in lower:
        return "Heartsaver"
    return display_course_name(course_name)


def course_type_url(course_name: str) -> str:
    label = course_family_label(course_name)
    if label == "ACLS":
        return "/acls.html"
    if label == "PALS":
        return "/pals.html"
    if label == "BLS":
        return "/bls.html"
    if label == "Heartsaver":
        return "/heartsaver.html"
    return "/schedule.html"


def subtype_tokens(course_name: str) -> set[str]:
    lower = display_course_name(course_name).lower()
    tokens = set()
    for token in ("renewal", "initial", "heartcode", "skills", "blended", "instructor"):
        if token in lower:
            tokens.add(token)
    if "new or expired" in lower:
        tokens.add("initial")
    return tokens


def session_city(session: dict) -> str:
    location = clean_location_display(session.get("location_display", "") or session.get("location_name", ""))
    city, _state = location_to_city_state(location)
    return city.lower()


def is_cancelled_or_full(session: dict) -> bool:
    status = str(session.get("session_status") or "").lower()
    if "cancel" in status:
        return True
    if session.get("is_full") is True:
        return True
    seats = session.get("available_seats")
    try:
        return seats is not None and int(seats) <= 0
    except Exception:
        return False


def same_course(session_a: dict, session_b: dict) -> bool:
    a_course_id = str(session_a.get("course_id", "")).strip()
    b_course_id = str(session_b.get("course_id", "")).strip()

    if a_course_id and b_course_id:
        return a_course_id == b_course_id

    a_name = display_course_name(session_a.get("course_name", ""))
    b_name = display_course_name(session_b.get("course_name", ""))
    return a_name == b_name


def same_course_family(session_a: dict, session_b: dict) -> bool:
    return course_family_label(session_a.get("course_name", "")) == course_family_label(session_b.get("course_name", ""))


def replacement_score(current_session: dict, candidate: dict, now_dt: datetime) -> int:
    current_name = display_course_name(current_session.get("course_name", ""))
    candidate_name = display_course_name(candidate.get("course_name", ""))
    current_start = parse_dt(current_session.get("start_at"))
    candidate_start = candidate.get("_parsed_dt") or parse_dt(candidate.get("start_at"))
    score = 0

    if same_course(current_session, candidate):
        score += 120
    if subtype_tokens(current_name) & subtype_tokens(candidate_name):
        score += 45
    if str(current_session.get("certifying_body") or "").upper() == str(candidate.get("certifying_body") or "").upper():
        score += 25
    if current_start and candidate_start and current_start.weekday() == candidate_start.weekday():
        score += 15
    if current_start and candidate_start:
        minutes = abs((current_start.hour * 60 + current_start.minute) - (candidate_start.hour * 60 + candidate_start.minute))
        if minutes <= 60:
            score += 18
        elif minutes <= 180:
            score += 8
        days_out = max(0, (candidate_start - now_dt).days)
        score += max(0, 30 - min(days_out, 30))
    try:
        if int(candidate.get("registered_count") or candidate.get("enrolled_count") or 0) > 0:
            score += 10
    except Exception:
        pass
    if session_city(current_session) and session_city(current_session) == session_city(candidate):
        score += 18
    try:
        if int(candidate.get("available_seats") or 0) > 0:
            score += 15
    except Exception:
        pass
    return score


def build_future_replacement_index(sessions: list[dict], now_dt: datetime) -> dict[str, dict[str, list[dict]]]:
    index: dict[str, dict[str, list[dict]]] = {"family": {}, "course_id": {}, "course_name": {}}
    for session in sessions:
        dt = parse_dt(session.get("start_at"))
        if not is_future_session(dt, now_dt):
            continue
        if is_cancelled_or_full(session):
            continue
        copy = dict(session)
        copy["_parsed_dt"] = dt
        family = course_family_label(copy.get("course_name", ""))
        index["family"].setdefault(family, []).append(copy)
        course_id = str(copy.get("course_id") or "").strip()
        if course_id:
            index["course_id"].setdefault(course_id, []).append(copy)
        course_name = display_course_name(copy.get("course_name", "")).lower()
        if course_name:
            index["course_name"].setdefault(course_name, []).append(copy)
    for bucket in index.values():
        for rows in bucket.values():
            rows.sort(key=lambda item: item["_parsed_dt"])
    return index


def get_upcoming_sessions(
    current_session: dict,
    sessions: list[dict],
    now_dt: datetime,
    limit: int = UPCOMING_LIMIT,
    future_index: dict[str, dict[str, list[dict]]] | None = None,
) -> list[dict]:
    current_id = str(current_session.get("session_id", "")).strip()
    matches = []
    family = course_family_label(current_session.get("course_name", ""))
    if future_index is not None:
        course_id = str(current_session.get("course_id") or "").strip()
        course_name = display_course_name(current_session.get("course_name", "")).lower()
        exact = []
        if course_id:
            exact.extend(future_index["course_id"].get(course_id, []))
        if course_name:
            exact.extend(future_index["course_name"].get(course_name, []))
        seen_ids = set()
        candidates = []
        for item in exact + future_index["family"].get(family, [])[:200]:
            sid = str(item.get("session_id") or "")
            if sid in seen_ids:
                continue
            seen_ids.add(sid)
            candidates.append(item)
    else:
        candidates = sessions

    for session in candidates:
        if not same_course_family(current_session, session):
            continue

        sid = str(session.get("session_id", "")).strip()
        if sid == current_id:
            continue

        dt = session.get("_parsed_dt") or parse_dt(session.get("start_at"))
        if not is_future_session(dt, now_dt):
            continue
        if is_cancelled_or_full(session):
            continue

        copy = dict(session)
        copy["_parsed_dt"] = dt
        copy["_replacement_score"] = replacement_score(current_session, copy, now_dt)
        matches.append(copy)

    matches.sort(key=lambda item: (-item["_replacement_score"], item["_parsed_dt"]))
    return matches[:limit]


def is_future_session(session_start: datetime | None, now_dt: datetime) -> bool:
    return bool(session_start and session_start > now_dt)


def render_upcoming_sessions_html(upcoming_sessions: list[dict], course_url: str, course_label: str, full_schedule_url: str = "/schedule.html") -> str:
    primary_label = f"See upcoming {course_label} classes"
    if not upcoming_sessions:
        return f"""
<section id="upcoming-times" class="section-box js-live-session-group" data-empty-link="{escape(course_url)}" data-empty-link-label="{escape(primary_label)}" data-full-schedule-link="{escape(full_schedule_url)}">
  <h2>No upcoming sessions available</h2>
  <p>No upcoming sessions are available for this class type right now.</p>
  <div class="upcoming-footer-link">
    <a class="button primary" href="{escape(course_url)}">{escape(primary_label)}</a>
    <a class="button secondary" href="{escape(full_schedule_url)}">See all 910CPR classes</a>
  </div>
</section>
"""

    cards = []
    for session in upcoming_sessions:
        dt = session["_parsed_dt"]
        date_label = dt.strftime("%B %d, %Y")
        time_label = dt.strftime("%I:%M %p").lstrip("0")
        location_label = clean_location_display(session.get("location_display", "")) or "Location TBD"
        register_url = session.get("registration_url", "#")
        seats = session.get("available_seats")
        seats_label = ""
        if seats not in (None, ""):
            seats_label = f"<div class=\"upcoming-seats\">{escape(str(seats))} seats available</div>"

        cards.append(
            f"""
<div class="upcoming-card js-session-item" data-session-id="{escape(str(session.get('session_id') or ''), quote=True)}" data-start="{escape(dt.isoformat(), quote=True)}" data-end="{escape(str(session.get('end_at') or ''), quote=True)}" data-session-start="{escape(dt.isoformat(), quote=True)}">
  <div class="upcoming-date">{escape(date_label)}</div>
  <div class="upcoming-time">{escape(time_label)}</div>
  <div class="upcoming-location">{escape(location_label)}</div>
  {seats_label}
  <div class="upcoming-actions">
    <a class="button small primary" href="{escape(register_url)}">Register</a>
  </div>
</div>
"""
        )

    return f"""
<section id="upcoming-times" class="section-box js-live-session-group" data-empty-link="{escape(course_url)}" data-empty-link-label="{escape(primary_label)}" data-full-schedule-link="{escape(full_schedule_url)}">
  <div class="upcoming-head">
    <h2>Best replacement options</h2>
  </div>
  <div class="upcoming-grid">
    {''.join(cards)}
  </div>
  <div class="upcoming-footer-link">
    <a class="text-link strong-link" href="{escape(course_url)}">{escape(primary_label)}</a>
    <a class="text-link" href="{escape(full_schedule_url)}">See all 910CPR classes</a>
  </div>
</section>
"""


def clean_review_text(text: str) -> str:
    text = strip_html(text)
    text = normalize_whitespace(text)
    return text.strip(' "\'')


def compact_reviewer_name(name: str) -> str:
    name = normalize_whitespace(name)
    if not name:
        return "Google Review"

    parts = [p for p in re.split(r"\s+", name) if p]
    if len(parts) == 1:
        return parts[0]

    last_initial = parts[-1][0].upper() + "."
    return f"{parts[0]} {last_initial}"


def review_record_key(author: str, comment: str) -> str:
    raw = f"{author}|{comment}".lower()
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def review_matches_course(course_name: str, comment: str) -> bool:
    lower_course = display_course_name(course_name).lower()
    lower_comment = comment.lower()

    if "bls" in lower_course:
        return "bls" in lower_comment
    if "acls" in lower_course:
        return "acls" in lower_comment
    if "pals" in lower_course:
        return "pals" in lower_comment
    if "heartsaver" in lower_course:
        return "heartsaver" in lower_comment
    if "first aid" in lower_course:
        return "first aid" in lower_comment

    return False


def iter_review_payloads_from_json(data_obj):
    if isinstance(data_obj, dict):
        if isinstance(data_obj.get("reviews"), list):
            yield data_obj["reviews"]
        for value in data_obj.values():
            yield from iter_review_payloads_from_json(value)
    elif isinstance(data_obj, list):
        looks_like_reviews = False
        for item in data_obj:
            if isinstance(item, dict) and (
                "comment" in item
                or "text" in item
                or "reviewer" in item
                or "author_name" in item
                or "starRating" in item
                or "rating" in item
            ):
                looks_like_reviews = True
                break
        if looks_like_reviews:
            yield data_obj
        else:
            for item in data_obj:
                yield from iter_review_payloads_from_json(item)


def parse_review_objects(review_list: list) -> list[dict]:
    parsed = []
    seen = set()

    for item in review_list:
        if not isinstance(item, dict):
            continue

        if item.get("has_text") is False:
            continue

        comment = clean_review_text(item.get("comment", "") or item.get("text", ""))
        if len(comment) < MIN_REVIEW_LENGTH:
            continue

        reviewer = item.get("reviewer", {}) or {}
        author = normalize_whitespace(
            reviewer.get("displayName")
            or item.get("author_name")
            or item.get("name")
            or item.get("author")
            or "Google Review"
        )

        stars_raw = str(item.get("starRating", "")).upper()
        stars_lookup = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}
        stars = stars_lookup.get(stars_raw)

        if stars is None:
            try:
                stars = int(item.get("rating", 5))
            except Exception:
                stars = 5

        if stars < 4:
            continue

        key = review_record_key(author, comment)
        if key in seen:
            continue
        seen.add(key)

        parsed.append(
            {
                "author": compact_reviewer_name(author),
                "comment": comment,
                "stars": max(1, min(5, int(stars))),
                "created": str(
                    item.get("createTime", "")
                    or item.get("created_at", "")
                    or item.get("created_date", "")
                ).strip(),
            }
        )

    return parsed


def load_reviews() -> list[dict]:
    sources = []

    if REVIEWS_SOURCE.is_file():
        sources.append(REVIEWS_SOURCE)
    elif REVIEWS_SOURCE.exists():
        for ext in ("*.json", "*.zip"):
            sources.extend(sorted(REVIEWS_SOURCE.glob(ext)))

    all_reviews = []
    seen = set()

    for path in sources:
        try:
            if path.suffix.lower() == ".json":
                data_obj = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
                for review_list in iter_review_payloads_from_json(data_obj):
                    for review in parse_review_objects(review_list):
                        key = review_record_key(review["author"], review["comment"])
                        if key not in seen:
                            seen.add(key)
                            all_reviews.append(review)

            elif path.suffix.lower() == ".zip":
                with ZipFile(path) as zf:
                    for name in zf.namelist():
                        if not name.lower().endswith(".json"):
                            continue
                        try:
                            with zf.open(name) as handle:
                                data_obj = json.loads(handle.read().decode("utf-8", errors="ignore"))
                            for review_list in iter_review_payloads_from_json(data_obj):
                                for review in parse_review_objects(review_list):
                                    key = review_record_key(review["author"], review["comment"])
                                    if key not in seen:
                                        seen.add(key)
                                        all_reviews.append(review)
                        except Exception:
                            continue
        except Exception:
            continue

    return all_reviews


def pick_reviews_for_session(
    session_id: str,
    course_id: str,
    course_name: str,
    reviews: list[dict],
    count: int = REVIEWS_PER_PAGE,
) -> list[dict]:
    if not reviews:
        return []

    course_specific = [review for review in reviews if review_matches_course(course_name, review["comment"])]
    general = [review for review in reviews if review not in course_specific]

    seed_value = f"{session_id}|{course_id}|{display_course_name(course_name)}"
    rng = random.Random(hashlib.md5(seed_value.encode("utf-8")).hexdigest())

    chosen = []

    def pull(pool: list[dict], needed: int) -> list[dict]:
        if needed <= 0 or not pool:
            return []
        pool_copy = list(pool)
        rng.shuffle(pool_copy)
        return pool_copy[:needed]

    chosen.extend(pull(course_specific, count))

    if len(chosen) < count:
        already = {review_record_key(review["author"], review["comment"]) for review in chosen}
        remaining_general = [review for review in general if review_record_key(review["author"], review["comment"]) not in already]
        chosen.extend(pull(remaining_general, count - len(chosen)))

    return chosen[:count]


def truncate_review(text: str, max_chars: int = 220) -> str:
    text = normalize_whitespace(text)
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit(" ", 1)[0].strip()
    return cut + "..."


def render_reviews_html(selected_reviews: list[dict]) -> str:
    if not selected_reviews:
        return """
<section class="section-box">
  <h2>Why Students Choose 910CPR</h2>
  <div class="reviews-fallback">
    <p>Students consistently choose 910CPR for clear instruction, flexible scheduling, and a supportive learning environment.</p>
  </div>
</section>
"""

    cards = []
    for review in selected_reviews:
        stars = "★" * int(review.get("stars", 5))
        comment = truncate_review(review.get("comment", ""))
        author = review.get("author", "Google Review")
        cards.append(
            f"""
<div class="review-card">
  <div class="review-stars" aria-label="Five star review">{stars}</div>
  <p class="review-text">“{escape(comment)}”</p>
  <div class="review-author">{escape(author)}</div>
</div>
"""
        )

    return f"""
<section class="section-box">
  <h2>Why Students Choose 910CPR</h2>
  <div class="reviews-grid">
    {''.join(cards)}
  </div>
</section>
"""


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{page_title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{meta_description}">
<meta name="robots" content="{robots_value}">
<link rel="canonical" href="{canonical_url}">
<link rel="stylesheet" href="/css/lander.css">
{gtm_head}
{schema_block}
</head>
<body class="lander course-{course_slug}">
{gtm_body}
<div class="wrap">
  <div class="page-shell">
    <header class="site-brand-bar">
      <a class="site-brand-link" href="/index.html" aria-label="910CPR home">
        <img class="site-brand-logo" src="/images/logo.png" alt="910CPR logo" loading="eager" onerror="this.src='/images/910CPR_wave.jpg';this.onerror=null;">
        <span class="site-brand-wordmark">910CPR</span>
      </a>
    </header>

    {state_notice}

    <section class="hero">

      <div class="date-badge">
        <div class="date-month">{month_abbr}</div>
        <div class="date-day">{day_num}</div>
        <div class="date-weekday">{weekday}</div>
      </div>

      <div class="hero-main">
        <div class="eyebrow">{course}</div>
        <h1>{course}</h1>
        <p class="subhead">{hero_subhead}</p>
      </div>

      <div class="hero-side">
        {cert_logo_html}
        <div class="trust-badge">
          <strong>Same-Day Certification</strong>
          <span>Most students receive their certification the same day.</span>
        </div>
      </div>

    </section>

    <div class="hero-details">

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

      <div class="cta-panel">
        <p class="cta-panel-label">Reserve your seat</p>
        <p class="cta-panel-copy">{hero_subhead}</p>

        <div class="cta-row">
          {button_html}
        </div>
      </div>

    </div>

    {upcoming_sessions_html}

    {brand_strip_html}

    {reviews_html}

    {course_description_section}

    <section class="section-box">
      <h2>Who This Class Is For</h2>
      <p>{audience_text}</p>
      <p>{corporate_text}</p>
    </section>

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
</script>
<script src="/assets/live-sessions.js"></script>
<script src="/assets/session-expiry.js"></script>

</body>
</html>
"""


def resolve_data_file(dataset: str, data_file: str | None) -> Path:
    if data_file:
        return (ROOT / data_file).resolve()
    if dataset == "full":
        return FULL_DATA_FILE
    return DEFAULT_DATA_FILE


def main() -> None:
    parser = argparse.ArgumentParser(description="Build class lander pages")
    parser.add_argument(
        "--dataset",
        choices=("future", "full"),
        default="future",
        help="Choose the input dataset. Defaults to future to preserve current behavior.",
    )
    parser.add_argument(
        "--data-file",
        default="",
        help="Optional explicit input JSON path, relative to repo root.",
    )
    parser.add_argument(
        "--workers",
        default="",
        help="Accepted for compatibility with existing build commands. Not used by this builder.",
    )
    parser.add_argument(
        "--resume-stamped",
        action="store_true",
        help="Skip class pages that already contain BUILD_CODE from this generator.",
    )
    parser.add_argument("--shard-index", type=int, default=0, help="Zero-based shard index for parallel rebuilds.")
    parser.add_argument("--shard-count", type=int, default=1, help="Total shard count for parallel rebuilds.")
    args = parser.parse_args()

    data_file = resolve_data_file(args.dataset, args.data_file.strip() or None)

    with open(data_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    sessions = data["sessions"]
    all_reviews = load_reviews()
    build_meta = current_build_metadata("scripts/build_landers.py", str(data_file))
    build_stamp = build_meta.visible
    now_dt = datetime.now(TZ)
    future_replacement_index = build_future_replacement_index(sessions, now_dt)

    count = 0

    shard_count = max(1, int(args.shard_count or 1))
    shard_index = max(0, min(shard_count - 1, int(args.shard_index or 0)))

    for idx, session in enumerate(tqdm(sessions, desc="Building landers", unit="page", miniters=50)):
        if shard_count > 1 and idx % shard_count != shard_index:
            continue
        session_id = str(session.get("session_id", "")).strip()
        output_path = OUTPUT_DIR / f"{session_id}.html"
        if args.resume_stamped and output_path.exists():
            existing = output_path.read_text(encoding="utf-8", errors="ignore")
            if "<!-- BUILD_CODE:" in existing and "scripts/build_landers.py" in existing:
                continue
        course_raw = session.get("course_name", "")
        course_display = display_course_name(course_raw)
        course_seo = seo_course_phrase(course_raw)

        raw_location = str(session.get("location_display", "")).strip()
        location = clean_location_display(raw_location) or "Wilmington; Shipyard Blvd"
        register = session.get("registration_url", "#")
        dt = parse_dt(session.get("start_at"))

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
        page_title = f"{seo_title_for_session(course_seo, city=city, state=state)} | 910CPR"
        meta_description = (
            f"{course_seo} in {location}. View class details, current schedule options, "
            f"and register online with 910CPR."
        )

        course_id = str(session.get("course_id", "")).strip()
        course_number = str(session.get("course_number", "")).strip()
        course_label = course_family_label(course_display)
        type_page_url = course_type_url(course_display)
        schedule_anchor = course_id if is_valid_schedule_anchor(course_id) else course_number
        if is_valid_schedule_anchor(schedule_anchor):
            schedule_url = f"https://coastalcprtraining.enrollware.com/schedule#ct{schedule_anchor}"
        else:
            schedule_url = "https://coastalcprtraining.enrollware.com/site/coastalcprtraining/schedule"
        course_page_url = schedule_url

        canonical_url = f"https://www.910cpr.com/classes/{session_id}.html"
        is_past = bool(dt and dt <= now_dt)

        if is_past:
            state_notice = """
<div class="notice">
  This class has passed. Choose a current option below.
</div>
"""
            button_html = f'<a class="button secondary" href="{escape(type_page_url)}">See upcoming {escape(course_label)} classes</a>'
            hero_subhead = "This class is no longer bookable. Use the replacement options below to choose a current class."
        else:
            state_notice = ""
            button_html = f'<a class="button primary" href="{escape(register)}">Register Now</a>'
            hero_subhead = "Use the register button for this session or the upcoming list below for other dates and times."

        cert_logo = detect_cert_logo(course_display)
        if cert_logo:
            cert_logo_html = f"""
<div class="cert-badge">
  <img src="{escape(cert_logo)}" alt="Certifying body logo" loading="lazy">
</div>
"""
        else:
            cert_logo_html = """
<div class="cert-badge cert-badge-empty" aria-hidden="true"></div>
"""

        logo_url = default_logo_url()
        course_image_url = get_course_type_image(course_display)
        if course_image_url:
            logo_card = ""
            if logo_url:
                logo_card = f"""
  <div class="brand-card">
    <img src="{escape(logo_url)}" alt="910CPR logo" loading="lazy">
  </div>
"""
            brand_strip_html = f"""
<section class="brand-strip">
{logo_card}
  <div class="image-card">
    <img src="{escape(course_image_url)}" alt="{escape(course_display)}" loading="lazy">
  </div>
</section>
"""
        else:
            brand_strip_html = ""

        description_html = load_course_description_html(course_id or course_number, course_display)
        if description_html:
            course_description_section = f"""
<section class="section-box">
  <h2>Course Description</h2>
  <div class="description-html">
    {description_html}
  </div>
</section>
"""
        else:
            course_description_section = f"""
<section class="section-box">
  <h2>Course Description</h2>
  <div class="description-html">
    <p>{escape(audience_blurb(course_display))}</p>
  </div>
</section>
"""

        upcoming_sessions = get_upcoming_sessions(
            session,
            sessions,
            now_dt,
            limit=UPCOMING_LIMIT,
            future_index=future_replacement_index,
        )
        upcoming_sessions_html = render_upcoming_sessions_html(upcoming_sessions, type_page_url, course_label)

        selected_reviews = pick_reviews_for_session(
            session_id=session_id,
            course_id=course_id or course_number,
            course_name=course_display,
            reviews=all_reviews,
            count=REVIEWS_PER_PAGE,
        )
        reviews_html = render_reviews_html(selected_reviews)

        html_doc = TEMPLATE.format(
            page_title=escape(page_title),
            meta_description=escape(meta_description),
            robots_value="index,follow",
            canonical_url=escape(canonical_url),
            gtm_head=render_gtm_head(),
            gtm_body=render_gtm_body(),
            schema_block=make_schema(course_seo, dt, location, city, state, register),
            state_notice=state_notice,
            month_abbr=escape(month_abbr),
            day_num=escape(day_num),
            weekday=escape(weekday),
            course=escape(course_display),
            hero_subhead=escape(hero_subhead),
            cert_logo_html=cert_logo_html,
            date=escape(date),
            time=escape(time),
            location=escape(location),
            button_html=button_html,
            upcoming_sessions_html=upcoming_sessions_html,
            brand_strip_html=brand_strip_html,
            reviews_html=reviews_html,
            course_description_section=course_description_section,
            audience_text=escape(audience_blurb(course_display)),
            corporate_text=escape(corporate_blurb(city, course_display)),
            build_stamp=escape(build_stamp),
            session_id=escape(session_id),
            course_id=escape(course_id or course_number),
            course_js=js_escape(course_display),
            course_slug=short_slug(course_display),
            location_js=js_escape(location),
            is_past_js="true" if is_past else "false",
            register_js=js_escape(register),
            schedule_url=escape(schedule_url),
            course_page_url=escape(course_page_url),
        )
        html_doc = apply_build_metadata(html_doc, build_meta)

        output_path.write_text(html_doc, encoding="utf-8")
        count += 1

    print(f"Dataset used: {data_file}")
    print(f"Landers built: {count}")
    print(f"Reviews loaded: {len(all_reviews)}")


if __name__ == "__main__":
    main()
