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
PRIMARY_FULL_DATA_FILE = ROOT / "data" / "sessions_current.json"
FALLBACK_FULL_DATA_FILE = ROOT / "docs" / "data" / "schedule.json"
FULL_DATA_FILE = PRIMARY_FULL_DATA_FILE if PRIMARY_FULL_DATA_FILE.exists() else FALLBACK_FULL_DATA_FILE
OUTPUT_DIR = ROOT / "docs" / "classes"
IMAGES_DIR = ROOT / "docs" / "images"
REVIEWS_SOURCE = ROOT / "data" / "raw" / "reviews"
COURSE_MAP_FILE = ROOT / "data" / "config" / "course_map.json"

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


def compact_course_name(course_raw: str) -> str:
    cleaned = display_course_name(course_raw)
    cleaned = re.sub(r"\s*\([^)]*\)\s*$", "", cleaned).strip()
    return cleaned or display_course_name(course_raw)


@lru_cache(maxsize=1)
def load_course_map() -> dict:
    if not COURSE_MAP_FILE.exists():
        return {"courses_by_id": {}, "courses_by_number": {}}
    try:
        return json.loads(COURSE_MAP_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"courses_by_id": {}, "courses_by_number": {}}


def course_map_entry(course_id: str, course_number: str = "") -> dict:
    course_map = load_course_map()
    by_id = course_map.get("courses_by_id", {}) if isinstance(course_map, dict) else {}
    by_number = course_map.get("courses_by_number", {}) if isinstance(course_map, dict) else {}
    cid = str(course_id or "").strip()
    cnum = str(course_number or "").strip()
    if cid and isinstance(by_id.get(cid), dict):
        return by_id[cid]
    mapped_id = by_number.get(cnum) if cnum else ""
    if mapped_id and isinstance(by_id.get(str(mapped_id)), dict):
        return by_id[str(mapped_id)]
    return {}


def nested_value(mapping: dict, path: tuple[str, ...], default=""):
    current = mapping
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current not in (None, "") else default


def normalize_session_record(session: dict) -> dict:
    if "course_name" in session and "registration_url" in session:
        return session

    course = session.get("course", {}) if isinstance(session.get("course"), dict) else {}
    timing = session.get("timing", {}) if isinstance(session.get("timing"), dict) else {}
    location = session.get("location", {}) if isinstance(session.get("location"), dict) else {}
    capacity = session.get("capacity", {}) if isinstance(session.get("capacity"), dict) else {}
    commerce = session.get("commerce", {}) if isinstance(session.get("commerce"), dict) else {}
    status = session.get("status", {}) if isinstance(session.get("status"), dict) else {}
    staffing = session.get("staffing", {}) if isinstance(session.get("staffing"), dict) else {}

    normalized = dict(session)
    normalized.update(
        {
            "session_id": str(session.get("session_id") or "").strip(),
            "course_id": str(course.get("course_id") or session.get("source_course_id") or "").strip(),
            "course_number": str(course.get("course_number") or course.get("course_id") or session.get("source_course_id") or "").strip(),
            "course_name": course.get("mapped_clean_title")
            or session.get("mapped_clean_title")
            or course.get("course_name_primary_clean")
            or course.get("course_name_primary_raw")
            or course.get("course_name_raw")
            or session.get("title")
            or "",
            "course_subtitle": course.get("course_subtitle_text") or "",
            "course_code": course.get("course_code_hint") or "",
            "certifying_body": session.get("mapped_certifying_body") or course.get("mapped_certifying_body") or "",
            "delivery_mode": session.get("mapped_delivery_mode") or course.get("mapped_delivery_mode") or course.get("delivery_mode_hint") or "",
            "start_at": timing.get("start_at") or session.get("start_at") or session.get("start") or session.get("start_datetime") or "",
            "end_at": timing.get("end_at") or session.get("end_at") or session.get("end") or session.get("end_datetime") or "",
            "location_name": location.get("location_name") or session.get("location_name") or session.get("location") or "",
            "location_display": location.get("location_display") or session.get("location_display") or session.get("location") or "",
            "lead_instructor_name": staffing.get("lead_instructor_name") or session.get("lead_instructor_name") or session.get("instructor") or "",
            "price": commerce.get("price") if commerce.get("price") not in (None, "") else session.get("price"),
            "max_students": capacity.get("max_students") if capacity.get("max_students") not in (None, "") else session.get("max_students"),
            "registered_count": capacity.get("registered_count") if capacity.get("registered_count") not in (None, "") else session.get("registered_count"),
            "enrolled_count": capacity.get("registered_count") if capacity.get("registered_count") not in (None, "") else session.get("enrolled_count"),
            "available_seats": capacity.get("available_seats") if capacity.get("available_seats") not in (None, "") else session.get("available_seats"),
            "is_full": capacity.get("is_full") if capacity.get("is_full") not in (None, "") else session.get("is_full"),
            "registration_url": commerce.get("registration_url") or session.get("registration_url") or session.get("registration_link") or "",
            "session_status": status.get("session_status") or session.get("session_status") or "",
            "mapped_family": session.get("mapped_family") or course.get("mapped_family") or "",
            "mapped_subtype": session.get("mapped_subtype") or course.get("mapped_subtype") or "",
            "mapped_certifying_body": session.get("mapped_certifying_body") or course.get("mapped_certifying_body") or "",
            "mapped_delivery_mode": session.get("mapped_delivery_mode") or course.get("mapped_delivery_mode") or "",
            "mapped_logo_key": session.get("mapped_logo_key") or course.get("mapped_logo_key") or "",
            "mapped_clean_title": session.get("mapped_clean_title") or course.get("mapped_clean_title") or "",
            "mapping_status": session.get("mapping_status") or course.get("mapping_status") or "unmapped",
            "mapping_notes": session.get("mapping_notes") or course.get("mapping_notes") or [],
        }
    )
    return normalized


def is_mapped(session: dict) -> bool:
    return str(session.get("mapping_status") or "").strip().lower() == "mapped"


def structured_family(session: dict) -> str:
    return str(session.get("mapped_family") or "").strip()


def structured_certifying_body(session: dict) -> str:
    return str(session.get("mapped_certifying_body") or session.get("certifying_body") or "").strip()


def structured_subtype(session: dict) -> str:
    return str(session.get("mapped_subtype") or "").strip()


def structured_delivery(session: dict) -> str:
    return str(session.get("mapped_delivery_mode") or session.get("delivery_mode") or "").strip()


def certifying_body_label(value: str) -> str:
    key = str(value or "").strip().upper()
    return {
        "AHA": "American Heart Association",
        "ARC": "American Red Cross",
        "HSI": "Health & Safety Institute",
        "ASHI": "American Safety & Health Institute",
        "USCG": "U.S. Coast Guard",
    }.get(key, str(value or "").strip() or "Unmapped - needs review")


def delivery_type_label(value: str) -> str:
    key = str(value or "").strip().upper()
    return {
        "IP": "In-person classroom",
        "ILT": "In-person classroom",
        "BL": "Blended learning",
        "SS": "Online course + in-person skills session",
        "ONLINE": "Online",
    }.get(key, str(value or "").strip() or "Unmapped - needs review")


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


def course_family_label(course_name: str, session: dict | None = None) -> str:
    if session and is_mapped(session):
        mapped_family = structured_family(session)
        if mapped_family:
            return mapped_family

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


def course_type_url_for_session(session: dict, course_name: str) -> str:
    if is_mapped(session):
        entry = course_map_entry(session.get("course_id", ""), session.get("course_number", ""))
        url = str(entry.get("public_schedule_url") or "").strip()
        if url:
            return url
        label = structured_family(session)
        if label == "ACLS":
            return "/acls.html"
        if label == "PALS":
            return "/pals.html"
        if label == "BLS":
            return "/bls.html"
        if label == "Heartsaver":
            return "/heartsaver.html"
        if label == "USCG":
            return "/uscg-elementary-first-aid-cpr.html"
    return course_type_url(course_name)


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
    if is_mapped(session_a) and is_mapped(session_b):
        return (
            structured_certifying_body(session_a).upper() == structured_certifying_body(session_b).upper()
            and structured_family(session_a).lower() == structured_family(session_b).lower()
        )
    return same_course(session_a, session_b)


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
    if structured_certifying_body(current_session).upper() == structured_certifying_body(candidate).upper():
        score += 25
    if structured_subtype(current_session).lower() and structured_subtype(current_session).lower() == structured_subtype(candidate).lower():
        score += 22
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
        family = course_family_label(copy.get("course_name", ""), copy)
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
    family = course_family_label(current_session.get("course_name", ""), current_session)
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

    heading = f"Other upcoming {course_label} class times" if course_label and course_label != "Course" else "Need a different time?"
    return f"""
<section id="upcoming-times" class="section-box js-live-session-group" data-empty-link="{escape(course_url)}" data-empty-link-label="{escape(primary_label)}" data-full-schedule-link="{escape(full_schedule_url)}">
  <div class="upcoming-head">
    <h2>{escape(heading)}</h2>
    <p>These are nearby options from the same mapped course family and certifying body when that metadata is available.</p>
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


def session_enrolled_count(session: dict) -> int:
    try:
        return max(0, int(session.get("enrolled_count") or session.get("registered_count") or 0))
    except Exception:
        return 0


def certifying_body_key(session: dict) -> str:
    logo_key = str(session.get("mapped_logo_key") or "").strip().lower()
    if logo_key in {"aha", "arc", "hsi"}:
        return logo_key
    body = structured_certifying_body(session).upper()
    haystack = " ".join(
        str(session.get(key) or "")
        for key in ("course_name", "mapped_clean_title", "course_subtitle", "course_code")
    ).upper()
    text = f"{body} {haystack}"
    if "AMERICAN RED CROSS" in text or re.search(r"\bARC\b", text):
        return "arc"
    if "HEALTH & SAFETY INSTITUTE" in text or "HEALTH AND SAFETY INSTITUTE" in text or re.search(r"\bHSI\b", text):
        return "hsi"
    if "AMERICAN HEART ASSOCIATION" in text or re.search(r"\bAHA\b", text):
        return "aha"
    return ""


def certifying_logo_src(session: dict) -> str:
    return {
        "aha": "/images/0aha.png",
        "arc": "/images/0arc.png",
        "hsi": "/images/0hsi.png",
    }.get(certifying_body_key(session), "")


def format_slug_month(dt: datetime | None) -> str:
    return dt.strftime("%b").upper() if dt else "TBD"


def format_slug_day(dt: datetime | None) -> str:
    return dt.strftime("%d").lstrip("0") if dt else "--"


def format_slug_weekday(dt: datetime | None) -> str:
    return dt.strftime("%a") if dt else ""


def format_slug_date_line(dt: datetime | None) -> str:
    return dt.strftime("%A, %B ") + str(dt.day) if dt else "Date TBA"


def format_slug_time_line(dt: datetime | None) -> str:
    return dt.strftime("%I:%M %p").lstrip("0") if dt else "Time TBA"


def render_modern_day_groups(sessions: list[dict]) -> str:
    groups: list[dict] = []
    by_key: dict[str, dict] = {}
    for session in sessions:
        dt = session.get("_parsed_dt") or parse_dt(session.get("start_at"))
        key = dt.date().isoformat() if dt else f"unknown-{len(groups)}"
        if key not in by_key:
            group = {"key": key, "dt": dt, "sessions": []}
            by_key[key] = group
            groups.append(group)
        by_key[key]["sessions"].append(session)

    cards = []
    for group in groups:
        dt = group["dt"]
        cert_logos: dict[str, str] = {}
        rows = []
        for session in sorted(group["sessions"], key=lambda item: item.get("_parsed_dt") or parse_dt(item.get("start_at")) or datetime.max.replace(tzinfo=TZ)):
            row_dt = session.get("_parsed_dt") or parse_dt(session.get("start_at"))
            location = clean_location_display(session.get("location_display", "")) or "Location TBD"
            title = display_course_name(session.get("course_name", "")) or "910CPR Class"
            register_url = session.get("registration_url") or "#"
            session_id = str(session.get("session_id") or "")
            body_key = certifying_body_key(session)
            logo = certifying_logo_src(session)
            if body_key and logo and body_key not in cert_logos:
                cert_logos[body_key] = logo
            rows.append(
                f"""
          <div class="slug-time-row js-session-item" data-session-id="{escape(session_id, quote=True)}" data-session-start="{escape(row_dt.isoformat() if row_dt else '', quote=True)}" data-session-end="{escape(str(session.get('end_at') or ''), quote=True)}">
            <div class="slug-time-copy">
              <div class="slug-pill-meta-row slug-time-meta">
                <span class="slug-pill-chip">{escape(format_slug_time_line(row_dt))}</span>
                <span class="slug-pill-chip slug-pill-chip-location">{escape(location)}</span>
              </div>
              <div class="slug-time-subtitle">{escape(title)}</div>
            </div>
            <div class="slug-time-actions">
              <a class="button small primary" href="{escape(register_url, quote=True)}" data-original-href="{escape(register_url, quote=True)}" data-session-id="{escape(session_id, quote=True)}">Book Seat</a>
            </div>
          </div>
"""
            )
        cert_html = ""
        if cert_logos:
            cert_html = (
                '<div class="slug-day-cert-logos" aria-label="Certifying body">'
                + "".join(
                    f'<img class="slug-day-cert-logo" src="{escape(src, quote=True)}" alt="" loading="lazy" data-certifying-body="{escape(body, quote=True)}">'
                    for body, src in cert_logos.items()
                )
                + "</div>"
            )
        cert_attr = f' data-certifying-body="{escape(next(iter(cert_logos)), quote=True)}"' if len(cert_logos) == 1 else ""
        cards.append(
            f"""
        <article class="slug-day-card"{f' data-session-date="{escape(group["key"], quote=True)}"' if dt else ''}{cert_attr}>
          {cert_html}
          <div class="slug-pill-date">
            <div class="slug-pill-month">{escape(format_slug_month(dt))}</div>
            <div class="slug-pill-day">{escape(format_slug_day(dt))}</div>
            <div class="slug-pill-weekday">{escape(format_slug_weekday(dt))}</div>
          </div>
          <div class="slug-day-main">
            <div class="slug-day-title">{escape(format_slug_date_line(dt))}</div>
            <div class="slug-time-list">{''.join(rows)}</div>
          </div>
        </article>
"""
        )
    return "".join(cards)


def render_modern_inventory_section(title: str, body: str, sessions: list[dict], section_class: str) -> str:
    if not sessions:
        return ""
    return f"""
<section class="slug-inventory-section {escape(section_class, quote=True)}">
  <div class="slug-inventory-head">
    <h3>{escape(title)}</h3>
    <p>{escape(body)}</p>
  </div>
  <div class="slug-pill-list">
    {render_modern_day_groups(sessions)}
  </div>
</section>
""".strip()


def render_past_current_inventory_html(upcoming_sessions: list[dict], course_url: str, course_label: str, full_schedule_url: str = "/schedule.html") -> str:
    full_label = f"See all {course_label} dates" if course_label and course_label != "Course" else "See all current dates"
    if not upcoming_sessions:
        return f"""
<section id="upcoming-times" class="section-box past-current-inventory js-live-session-group" data-empty-link="{escape(course_url, quote=True)}" data-empty-link-label="{escape(full_label, quote=True)}" data-full-schedule-link="{escape(full_schedule_url, quote=True)}">
  <div class="slug-empty">
    <strong>Need this class?</strong>
    <p>This session has passed, but we can help you find the right current option.</p>
    <div class="slug-empty-actions">
      <a class="button primary" href="{escape(course_url, quote=True)}">{escape(full_label)}</a>
      <a class="button secondary" href="tel:+19103955193">Call 910-395-5193</a>
    </div>
  </div>
</section>
""".strip()

    popular: list[dict] = []
    seen: set[str] = set()
    for session in sorted(upcoming_sessions, key=lambda item: (-session_enrolled_count(item), item.get("_parsed_dt") or parse_dt(item.get("start_at")) or datetime.max.replace(tzinfo=TZ))):
        if session_enrolled_count(session) <= 0:
            continue
        sid = str(session.get("session_id") or session.get("registration_url") or "")
        if sid in seen:
            continue
        seen.add(sid)
        popular.append(session)
        if len(popular) >= 4:
            break

    next_available: list[dict] = []
    for session in sorted(upcoming_sessions, key=lambda item: item.get("_parsed_dt") or parse_dt(item.get("start_at")) or datetime.max.replace(tzinfo=TZ)):
        sid = str(session.get("session_id") or session.get("registration_url") or "")
        if sid in seen:
            continue
        seen.add(sid)
        next_available.append(session)
        if len(next_available) >= 6:
            break

    popular_html = render_modern_inventory_section(
        "Popular upcoming classes",
        "Selected upcoming class times with active registrations.",
        popular,
        "slug-popular-section",
    )
    next_html = render_modern_inventory_section(
        "Next available classes",
        "More selected class times to help you compare dates.",
        next_available,
        "slug-scheduled-section",
    )
    return f"""
<section id="upcoming-times" class="section-box past-current-inventory js-live-session-group" data-empty-link="{escape(course_url, quote=True)}" data-empty-link-label="{escape(full_label, quote=True)}" data-full-schedule-link="{escape(full_schedule_url, quote=True)}">
  {popular_html}
  {next_html}
  <section class="slug-escape-hatch">
    <div class="slug-escape-copy">
      <strong>Need a different date or time?</strong>
      <span>These are selected current options. More dates and locations may be available on the full schedule.</span>
    </div>
    <a class="button primary slug-full-schedule-button" href="{escape(course_url, quote=True)}">{escape(full_label)}</a>
  </section>
</section>
""".strip()


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


def render_review_snippet_html(selected_reviews: list[dict]) -> str:
    if selected_reviews:
        review = selected_reviews[0]
        author = review.get("author", "Google Review")
        comment = truncate_review(review.get("comment", ""), 150)
        return f"""
<section class="trust-snippet" aria-label="Student review">
  <div class="trust-snippet-score">
    <span class="review-stars" aria-label="Five star review">★★★★★</span>
    <strong>Trusted by local students and teams</strong>
  </div>
  <p>“{escape(comment)}” <span>{escape(author)}</span></p>
</section>
"""

    return """
<section class="trust-snippet" aria-label="Student trust">
  <div class="trust-snippet-score">
    <span class="review-stars" aria-label="Five star review">★★★★★</span>
    <strong>Clear instruction. Direct registration. Local training.</strong>
  </div>
  <p>910CPR helps individuals, schools, healthcare teams, and workplaces keep certification current.</p>
</section>
"""


def certification_outcome(session: dict) -> str:
    if not is_mapped(session):
        return "Outcome not mapped - review course metadata before making certification claims."

    family = structured_family(session)
    body = structured_certifying_body(session).upper()
    subtype = structured_subtype(session).lower()
    delivery = structured_delivery(session).upper()

    if body == "AHA" and family in {"BLS", "ACLS", "PALS"}:
        if "heartcode" in subtype or delivery in {"BL", "SS"}:
            return "Provider eCard after successful online coursework and in-person skills completion; commonly valid for 2 years."
        return "Provider eCard after successful completion; commonly valid for 2 years."

    if body == "AHA" and family == "Heartsaver":
        return "Heartsaver completion card after successful completion; commonly valid for 2 years."

    if family == "USCG":
        return "Course documentation for the listed USCG-aligned first aid and CPR session."

    return "Certification or completion documentation as listed for this mapped course."


def same_day_note(session: dict) -> str:
    if not is_mapped(session):
        return ""
    family = structured_family(session)
    body = structured_certifying_body(session).upper()
    if body == "AHA" and family in {"BLS", "ACLS", "PALS", "Heartsaver"}:
        return "Same-day card processing when course requirements and roster details are complete."
    return ""


def render_confidence_block(session: dict) -> str:
    if is_mapped(session):
        family = structured_family(session) or "Mapped course"
        subtype = structured_subtype(session)
        course_type = f"{family} - {subtype}" if subtype else family
        cert_body = certifying_body_label(structured_certifying_body(session))
        delivery = delivery_type_label(structured_delivery(session))
        outcome = certification_outcome(session)
        same_day = same_day_note(session)
    else:
        cert_body = "Unmapped - needs review"
        course_type = "Unmapped course metadata"
        delivery = "Unmapped - needs review"
        outcome = "Course outcome not shown because the structured course mapping is missing."
        same_day = ""

    same_day_html = f"<li>{escape(same_day)}</li>" if same_day else ""
    return f"""
<section class="confidence-block" aria-label="Course confidence">
  <div class="confidence-item">
    <span>Certifying body</span>
    <strong>{escape(cert_body)}</strong>
  </div>
  <div class="confidence-item">
    <span>Course type</span>
    <strong>{escape(course_type)}</strong>
  </div>
  <div class="confidence-item">
    <span>Delivery</span>
    <strong>{escape(delivery)}</strong>
  </div>
  <div class="confidence-item confidence-outcome">
    <span>What you receive</span>
    <ul>
      <li>{escape(outcome)}</li>
      {same_day_html}
    </ul>
  </div>
</section>
"""


def course_description_paragraphs(session: dict) -> list[str]:
    if not is_mapped(session):
        return [
            "This session is present in the 910CPR schedule, but its structured course mapping is missing or uncertain.",
            "To avoid routing students to the wrong certifying body or course family, this page does not infer certification details from the raw Enrollware title.",
        ]

    body = structured_certifying_body(session).upper()
    family = structured_family(session)
    subtype = structured_subtype(session).lower()
    delivery = structured_delivery(session).upper()

    if body == "AHA" and family == "BLS":
        if "heartcode" in subtype or delivery in {"BL", "SS"}:
            return [
                "This is the American Heart Association BLS Provider HeartCode skills session. Students complete the AHA online HeartCode BLS coursework first, then use this appointment for hands-on skills practice and testing.",
                "It is built for healthcare and clinical roles that need AHA BLS Provider certification while using the blended-learning pathway.",
            ]
        if "renewal" in subtype:
            return [
                "This is the American Heart Association BLS Provider renewal class for students who already work at the healthcare-provider level and need to keep their BLS current.",
                "The class focuses on high-quality CPR, AED use, ventilations, and team response for adult, child, and infant emergencies.",
            ]
        return [
            "This is the American Heart Association BLS Provider course for healthcare providers and students entering clinical programs.",
            "The class covers high-quality CPR, AED use, ventilations, choking response, and team-based basic life support for adult, child, and infant patients.",
        ]

    if body == "AHA" and family == "ACLS":
        if "heartcode" in subtype or delivery in {"BL", "SS"}:
            return [
                "This is the American Heart Association ACLS HeartCode skills session. Students complete the online ACLS portion first, then attend this session for hands-on skills testing.",
                "It is intended for clinicians who manage or participate in adult cardiovascular emergency response and need the AHA ACLS Provider pathway.",
            ]
        return [
            "This is the American Heart Association ACLS Provider course for clinicians involved in adult cardiovascular emergency care.",
            "The class reinforces systematic assessment, effective team dynamics, rhythm recognition, pharmacology concepts, and management of cardiac arrest and peri-arrest situations.",
        ]

    if body == "AHA" and family == "PALS":
        return [
            "This is the American Heart Association PALS Provider course for clinicians who respond to pediatric respiratory, shock, and cardiac emergencies.",
            "The class emphasizes pediatric assessment, high-performance team response, and treatment priorities for infants and children in urgent care settings.",
        ]

    if body == "AHA" and family == "Heartsaver":
        if "pediatric" in subtype:
            return [
                "This AHA Heartsaver Pediatric First Aid CPR AED session is designed for childcare providers, caregivers, teachers, and others responsible for children.",
                "It combines practical first aid, CPR, and AED training in the format listed for this session.",
            ]
        if "cpr" in subtype and "first aid" not in subtype:
            return [
                "This AHA Heartsaver CPR AED class is for workplace and community responders who need CPR and AED training without the first aid module.",
                "It is a practical non-healthcare-provider course for adults who need a recognized CPR AED credential for work, school, or volunteering.",
            ]
        return [
            "This AHA Heartsaver First Aid CPR AED class is for workplace, school, childcare, fitness, church, and community responders.",
            "It combines first aid, CPR, and AED training in a practical format for people who need a recognized non-healthcare-provider certification.",
        ]

    if family == "USCG":
        return [
            "This USCG Elementary First Aid | CPR session is the maritime-focused first aid and CPR option listed in the 910CPR schedule.",
            "It is intended for students who need the specific USCG-aligned course shown here, with the delivery format and registration link preserved from the source session.",
        ]

    return [
        f"This is a mapped {certifying_body_label(body)} {family} session from the 910CPR schedule.",
        "The page uses structured course metadata for certifying body, course family, delivery type, and registration routing.",
    ]


def who_for_paragraphs(session: dict, course_display: str) -> list[str]:
    if not is_mapped(session):
        return [
            "This page needs course mapping review before a specific audience recommendation is shown.",
            "Use the registration link only after confirming the course is the version your employer, school, or agency requested.",
        ]

    body = structured_certifying_body(session).upper()
    family = structured_family(session)
    subtype = structured_subtype(session).lower()

    if body == "AHA" and family == "BLS":
        return [
            "This is the class most nursing, EMS, dental, hospital, and clinical programs mean when they ask for AHA BLS.",
            "Good fit if your employer or school specifically asked for American Heart Association BLS Provider. If you are not sure which version you need, BLS is usually the safer choice for healthcare roles.",
        ]
    if body == "AHA" and family == "ACLS":
        return [
            "Good fit for nurses, paramedics, respiratory therapists, physicians, advanced-practice providers, and clinical teams involved in adult cardiac emergency response.",
            "Choose this when your employer, hospital, or program specifically asks for American Heart Association ACLS Provider.",
        ]
    if body == "AHA" and family == "PALS":
        return [
            "Good fit for pediatric, emergency, transport, ICU, and clinical roles that may respond to seriously ill or injured infants and children.",
            "Choose this when your employer, hospital, or program specifically asks for American Heart Association PALS Provider.",
        ]
    if body == "AHA" and family == "Heartsaver":
        if "pediatric" in subtype:
            return [
                "Good fit for childcare providers, teachers, camp staff, babysitters, foster/adoptive parents, and teams responsible for children.",
                "If your requirement says AHA Heartsaver Pediatric First Aid CPR AED, this is the right family to compare against.",
            ]
        return [
            "Good fit for teachers, childcare staff, fitness professionals, security teams, office staff, church teams, construction crews, and other workplace responders.",
            "If your role is not healthcare but you need a recognized CPR, AED, and first aid card, Heartsaver is usually the version employers mean.",
        ]
    if family == "USCG":
        return [
            "Good fit for maritime students and working crews who were told to complete Elementary First Aid | CPR for a Coast Guard-related requirement.",
            "Use this page when the requested course specifically matches the USCG Elementary First Aid | CPR wording shown here.",
        ]
    return [audience_blurb(course_display), corporate_blurb("your area", course_display)]


def render_course_description_section(session: dict, fallback_html: str) -> str:
    description_html = fallback_html if is_mapped(session) else ""
    if description_html:
        return f"""
<section class="section-box course-description-priority">
  <h2>Course Description</h2>
  <div class="description-html">
    {description_html}
  </div>
</section>
"""

    paragraphs = "\n".join(f"    <p>{escape(text)}</p>" for text in course_description_paragraphs(session))
    return f"""
<section class="section-box course-description-priority">
  <h2>Course Description</h2>
  <div class="description-html">
{paragraphs}
  </div>
</section>
"""


def render_who_for_section(session: dict, course_display: str) -> str:
    paragraphs = "\n".join(f"  <p>{escape(text)}</p>" for text in who_for_paragraphs(session, course_display))
    return f"""
<section class="section-box">
  <h2>Who This Class Is For</h2>
{paragraphs}
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
<link rel="icon" type="image/png" href="/images/logo.png">
<link rel="shortcut icon" href="/images/logo.png">
<link rel="apple-touch-icon" href="/images/logo.png">
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

    {top_inventory_html}

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
          <strong>{trust_badge_title}</strong>
          <span>{trust_badge_copy}</span>
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
        <p class="cta-panel-label">{cta_panel_label}</p>
        <p class="cta-panel-copy">{hero_subhead}</p>

        <div class="cta-row">
          {button_html}
        </div>
      </div>

    </div>

    {confidence_block_html}

    {review_snippet_html}

    {course_description_section}

    {upcoming_sessions_html}

    {brand_strip_html}

    {who_for_section}

    {reviews_html}

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
    parser.add_argument(
        "--resume-product-layout",
        action="store_true",
        help="Skip class pages that already contain the upgraded product-page layout markers.",
    )
    parser.add_argument("--shard-index", type=int, default=0, help="Zero-based shard index for parallel rebuilds.")
    parser.add_argument("--shard-count", type=int, default=1, help="Total shard count for parallel rebuilds.")
    args = parser.parse_args()

    data_file = resolve_data_file(args.dataset, args.data_file.strip() or None)

    with open(data_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    sessions = [normalize_session_record(item) for item in data["sessions"]]
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
        if args.resume_product_layout and output_path.exists():
            existing = output_path.read_text(encoding="utf-8", errors="ignore")
            if all(marker in existing for marker in ("confidence-block", "trust-snippet", "course-description-priority")):
                continue
        if args.resume_stamped and output_path.exists():
            existing = output_path.read_text(encoding="utf-8", errors="ignore")
            session_dt_for_resume = parse_dt(session.get("start_at"))
            became_past = bool(session_dt_for_resume and session_dt_for_resume <= now_dt)
            needs_past_refresh = became_past and "past-current-inventory" not in existing
            if "<!-- BUILD_CODE:" in existing and "scripts/build_landers.py" in existing and not needs_past_refresh:
                continue
        course_raw = session.get("course_name", "")
        course_id = str(session.get("course_id", "")).strip()
        course_number = str(session.get("course_number", "")).strip()
        mapped_entry = course_map_entry(course_id, course_number)
        if is_mapped(session):
            course_display = (
                str(mapped_entry.get("official_title") or "").strip()
                or str(session.get("mapped_clean_title") or "").strip()
                or display_course_name(course_raw)
            )
        else:
            course_display = display_course_name(course_raw)
        course_seo = seo_course_phrase(course_raw)

        raw_location = str(session.get("location_display", "")).strip()
        location = clean_location_display(raw_location) or "Wilmington; Shipyard Blvd"
        register = session.get("registration_url", "#") or "#"
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

        course_label = course_family_label(course_display, session)
        type_page_url = course_type_url_for_session(session, course_display)
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
            button_html = f'<a class="button secondary" href="{escape(register, quote=True)}">Source registration record</a>'
            cta_panel_label = "Historical class record"
            hero_subhead = "This class is no longer bookable. Current options are shown above; this record remains for validation."
        else:
            state_notice = ""
            button_html = f'<a class="button primary" href="{escape(register)}">Register Now</a>'
            cta_panel_label = "Reserve your seat"
            hero_subhead = "Use the register button for this session or the upcoming list below for other dates and times."

        logo_key = str(session.get("mapped_logo_key") or mapped_entry.get("logo_key") or "").strip().lower()
        if logo_key == "aha":
            cert_logo = first_existing_image("0aha.png", "0AHA.png", "aha.png", "AHA.png")
        elif logo_key == "arc":
            cert_logo = first_existing_image("0arc.png", "0ARC.png", "arc.png", "ARC.png")
        elif logo_key == "hsi":
            cert_logo = first_existing_image("0hsi.png", "0HSI.png", "hsi.png", "HSI.png")
        elif logo_key == "uscg":
            cert_logo = first_existing_image("stripes.png", "uscg.png", "USCG.png")
        else:
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
        course_description_section = render_course_description_section(session, description_html)

        upcoming_sessions = get_upcoming_sessions(
            session,
            sessions,
            now_dt,
            limit=UPCOMING_LIMIT,
            future_index=future_replacement_index,
        )
        if is_past:
            top_inventory_html = render_past_current_inventory_html(upcoming_sessions, type_page_url, course_label)
            upcoming_sessions_html = ""
        else:
            top_inventory_html = ""
            upcoming_sessions_html = render_upcoming_sessions_html(upcoming_sessions, type_page_url, course_label)

        selected_reviews = pick_reviews_for_session(
            session_id=session_id,
            course_id=course_id or course_number,
            course_name=course_display,
            reviews=all_reviews,
            count=REVIEWS_PER_PAGE,
        )
        reviews_html = render_reviews_html(selected_reviews)
        review_snippet_html = render_review_snippet_html(selected_reviews)
        confidence_block_html = render_confidence_block(session)
        who_for_section = render_who_for_section(session, course_display)
        trust_badge_title = "Mapped course details" if is_mapped(session) else "Mapping review needed"
        trust_badge_copy = same_day_note(session) or "Structured course metadata is shown before schedule alternatives."

        html_doc = TEMPLATE.format(
            page_title=escape(page_title),
            meta_description=escape(meta_description),
            robots_value="index,follow",
            canonical_url=escape(canonical_url),
            gtm_head=render_gtm_head(),
            gtm_body=render_gtm_body(),
            schema_block=make_schema(course_seo, dt, location, city, state, register),
            state_notice=state_notice,
            top_inventory_html=top_inventory_html,
            month_abbr=escape(month_abbr),
            day_num=escape(day_num),
            weekday=escape(weekday),
            course=escape(course_display),
            hero_subhead=escape(hero_subhead),
            cert_logo_html=cert_logo_html,
            trust_badge_title=escape(trust_badge_title),
            trust_badge_copy=escape(trust_badge_copy),
            date=escape(date),
            time=escape(time),
            location=escape(location),
            cta_panel_label=escape(cta_panel_label),
            button_html=button_html,
            confidence_block_html=confidence_block_html,
            review_snippet_html=review_snippet_html,
            upcoming_sessions_html=upcoming_sessions_html,
            brand_strip_html=brand_strip_html,
            reviews_html=reviews_html,
            course_description_section=course_description_section,
            who_for_section=who_for_section,
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
