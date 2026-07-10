import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

BASE_DIR = os.path.join("docs", "classes")
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.public_class_eligibility import is_public_class_location

SCHEDULE_PATH = os.path.join("docs", "data", "schedule_future.json")
LEGACY_SCHEDULE_PATH = os.path.join("data", "schedule.json")
MANIFEST_PATH = os.path.join("docs", "data", "generated_class_aggregate_manifest.json")
CONTROLLED_GENERATED_DIRS = (
    BASE_DIR,
    os.path.join(BASE_DIR, "months"),
    os.path.join(BASE_DIR, "cities"),
    os.path.join(BASE_DIR, "courses"),
    os.path.join(BASE_DIR, "course-at-city"),
)

def as_text(value, default="") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value).strip()

    if isinstance(value, dict):
        for key in ("name", "title", "label", "text", "value", "slug"):
            v = value.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return default

    if isinstance(value, list):
        parts = [as_text(v, "") for v in value]
        parts = [p for p in parts if p]
        return ", ".join(parts) if parts else default

    return str(value).strip()

def get_first(raw: dict, keys: tuple[str, ...], default=""):
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return default

def ensure_dirs():
    dirs = [
        BASE_DIR,
        os.path.join(BASE_DIR, "months"),
        os.path.join(BASE_DIR, "certifying-bodies"),
        os.path.join(BASE_DIR, "courses"),
        os.path.join(BASE_DIR, "cities"),
        os.path.join(BASE_DIR, "course-at-city"),
        os.path.join(BASE_DIR, "industries"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def slugify(text: str, max_length: int = 80) -> str:
    text = as_text(text, "")
    text = re.sub(r"<[^>]+>", " ", text)           # strip HTML tags
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", " and ")
    text = re.sub(r"https?://\S+", " ", text)      # strip URLs
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower())
    text = text.strip("-")

    if not text:
        text = "item"

    return text[:max_length].strip("-")

def safe_filename_slug(*parts: str, max_length: int = 120) -> str:
    cleaned = [slugify(p, max_length=60) for p in parts if as_text(p, "")]
    value = "--".join([p for p in cleaned if p]).strip("-")
    if not value:
        value = "item"
    return value[:max_length].strip("-")


def html_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def load_schedule():
    schedule_path = SCHEDULE_PATH if os.path.exists(SCHEDULE_PATH) else LEGACY_SCHEDULE_PATH
    with open(schedule_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    for key in ("sessions", "schedule", "classes", "items"):
        if key in data and isinstance(data[key], list):
            return data[key]

    raise ValueError(
        "Could not find a session list in schedule.json. "
        "Expected a top-level list or one of: sessions, schedule, classes, items."
    )


def parse_datetime(value: str) -> datetime:
    if not value:
        raise ValueError("Missing datetime value")

    value = value.strip()

    # Handle trailing Z
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    return datetime.fromisoformat(value)


def extract_city(location_name: str) -> str:
    if not location_name:
        return "Unknown City"

    # Example: "Wilmington; Shipyard Blvd"
    city = location_name.split(";")[0].strip()
    return city or location_name.strip()


def extract_certifying_body(course_name: str) -> str:
    name = (course_name or "").upper()
    if "AHA" in name:
        return "AHA"
    if "ASHI" in name:
        return "ASHI"
    if "RED CROSS" in name or "ARC" in name:
        return "Red Cross"
    if "HSI" in name:
        return "HSI"
    return "Other"


def infer_industries(course_name: str, description: str = "") -> list[str]:
    text = f"{course_name or ''} {description or ''}".lower()
    industries = set()

    if any(word in text for word in ("healthcare", "clinical", "hospital", "nursing", "bls", "cpr")):
        industries.add("healthcare")
    if any(word in text for word in ("dental",)):
        industries.add("dental")
    if any(word in text for word in ("ems", "emergency medical", "paramedic", "emt")):
        industries.add("ems")

    if not industries:
        industries.add("general")

    return sorted(industries)


def infer_current_public_destination(context: str) -> str:
    text = re.sub(r"<[^>]+>", " ", as_text(context, "")).lower()
    text = re.sub(r"\s+", " ", text).strip()
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


def class_or_fallback_url(session_id: str, *context_parts: str) -> str:
    class_path = os.path.join(BASE_DIR, f"{quote(session_id)}.html")
    if os.path.exists(class_path):
        return f"/classes/{quote(session_id)}.html"
    return infer_current_public_destination(" ".join(as_text(part, "") for part in context_parts))


def normalize_session(raw: dict) -> dict:
    session_id = as_text(
        get_first(raw, ("session_id", "id", "sessionId", "class_id", "classId"))
    )
    if not session_id:
        raise ValueError(f"Missing session id in record: {raw}")

    course_raw = get_first(raw, ("course_name", "course", "name", "title"), "Unknown Course")
    course_name = as_text(course_raw, "Unknown Course")

    course_slug = as_text(get_first(raw, ("course_slug", "courseSlug")))
    if not course_slug and isinstance(course_raw, dict):
        course_slug = as_text(course_raw.get("slug"))

    course_slug = slugify(course_slug or course_name)

    location_raw = get_first(raw, ("location_name", "location", "locationName", "venue"), "Unknown Location")
    location_name = as_text(location_raw, "Unknown Location")

    city_raw = get_first(raw, ("city", "city_name"), "")
    city = as_text(city_raw)
    if not city and isinstance(location_raw, dict):
        city = as_text(location_raw.get("city")) or as_text(location_raw.get("locality"))
    if not city:
        city = extract_city(location_name)

    city_slug = as_text(get_first(raw, ("city_slug", "citySlug"))) or slugify(city)

    start_raw = get_first(raw, ("startDate", "start_date", "start_at", "start", "datetime", "date_time"))
    start_raw = as_text(start_raw)

    if start_raw:
        dt = parse_datetime(start_raw)
        date_str = dt.strftime("%B %d, %Y")
        time_str = dt.strftime("%I:%M %p").lstrip("0")
        month_key = dt.strftime("%Y-%m")
        month_label = dt.strftime("%B %Y")
    else:
        date_str = as_text(get_first(raw, ("date",)), "")
        time_str = as_text(get_first(raw, ("time",)), "")
        month_key = as_text(get_first(raw, ("month_key",)), "") or "unknown"
        month_label = as_text(get_first(raw, ("month_label",)), "") or "Unknown"

    certifying_body = as_text(get_first(raw, ("certifying_body", "certifyingBody")))
    if not certifying_body:
        certifying_body = extract_certifying_body(course_name)

    description = as_text(get_first(raw, ("description", "summary")), "")

    industries = raw.get("industries")
    if not isinstance(industries, list) or not industries:
        industries = infer_industries(course_name, description)

    course_city_key = safe_filename_slug(course_slug, city_slug)

    return {
        "session_id": session_id,
        "course_name": course_name,
        "course_slug": course_slug,
        "location_name": location_name,
        "city": city,
        "city_slug": city_slug,
        "date": date_str,
        "time": time_str,
        "month_key": month_key,
        "month_label": month_label,
        "certifying_body": certifying_body,
        "certifying_body_slug": slugify(certifying_body),
        "industries": [slugify(as_text(x)) for x in industries if as_text(x)],
        "description": description,
        "url": class_or_fallback_url(session_id, course_name, description, certifying_body, city, location_name),
        "course_city_key": course_city_key,
    }


def page(title: str, description: str, canonical_path: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html_escape(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{html_escape(description)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://www.910cpr.com{html_escape(canonical_path)}">
<link rel="stylesheet" href="/css/lander.css">
</head>
<body>
<div class="wrap">
  <div class="card">
    {body_html}
  </div>
</div>
</body>
</html>
"""


def render_hero(title: str, subhead: str, eyebrow: str = "Classes Directory") -> str:
    return f"""
    <section class="hero">
      <div class="hero-main">
        <div class="eyebrow">{html_escape(eyebrow)}</div>
        <h1>{html_escape(title)}</h1>
        <p class="subhead">{html_escape(subhead)}</p>
      </div>
    </section>
    """


def render_link_list(items: list[tuple[str, str]]) -> str:
    links = "\n".join(
        f'<li><a class="text-link" href="{html_escape(href)}">{html_escape(label)}</a></li>'
        for href, label in items
    )
    return f"<ul>{links}</ul>"


def render_section(title: str, items: list[tuple[str, str]], intro: str | None = None) -> str:
    intro_html = f"<p>{html_escape(intro)}</p>" if intro else ""
    return f"""
    <section class="section-box">
      <div class="section-title-wrap" style="margin-bottom:12px;">
        <h2>{html_escape(title)}</h2>
      </div>
      {intro_html}
      {render_link_list(items)}
    </section>
    """


def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.normpath(path)


def repo_rel(path: str) -> str:
    try:
        return os.path.relpath(path, ".").replace(os.sep, "/")
    except ValueError:
        return os.path.normpath(path).replace(os.sep, "/")


def is_controlled_generated_html(path: str) -> bool:
    normalized = os.path.normpath(path)
    if not normalized.lower().endswith(".html"):
        return False
    directory = os.path.dirname(normalized)
    if directory == os.path.normpath(BASE_DIR):
        name = os.path.basename(normalized).lower()
        return bool(re.fullmatch(r"\d+\.html", name)) or name == "index.html"
    return directory in {os.path.normpath(d) for d in CONTROLLED_GENERATED_DIRS[1:]}


def cleanup_stale_generated_pages(expected_paths: set[str]) -> list[str]:
    expected = {os.path.normpath(path) for path in expected_paths}
    deleted: list[str] = []
    for directory in CONTROLLED_GENERATED_DIRS:
        if not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            path = os.path.normpath(os.path.join(directory, name))
            if not os.path.isfile(path) or not is_controlled_generated_html(path):
                continue
            if path in expected:
                continue
            os.remove(path)
            deleted.append(repo_rel(path))
    return sorted(deleted)


def write_generated_manifest(expected_paths: set[str], deleted_paths: list[str], sessions: list[dict]):
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    payload = {
        "generator": "scripts/build-classes-index.py",
        "public_location_rule": "trim location_name, require exact startsWith('::') via is_public_class_location(location_name)",
        "controlled_directories": [repo_rel(path) for path in CONTROLLED_GENERATED_DIRS],
        "source": SCHEDULE_PATH if os.path.exists(SCHEDULE_PATH) else LEGACY_SCHEDULE_PATH,
        "public_session_count": len(sessions),
        "expected_files": sorted(repo_rel(path) for path in expected_paths),
        "deleted_stale_files": deleted_paths,
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    return payload


def session_label(s: dict) -> str:
    return f"{s['course_name']} — {s['date']} at {s['time']} — {s['city']}"


def build_indexes(sessions: list[dict]):
    generated_paths: set[str] = set()
    by_month = defaultdict(list)
    by_cert = defaultdict(list)
    by_course = defaultdict(list)
    by_city = defaultdict(list)
    by_course_city = defaultdict(list)
    by_industry = defaultdict(list)

    for s in sessions:
        by_month[s["month_key"]].append(s)
        by_cert[s["certifying_body_slug"]].append(s)
        by_course[s["course_slug"]].append(s)
        by_city[s["city_slug"]].append(s)
        by_course_city[s["course_city_key"]].append(s)        
    for industry in s["industries"]:
            by_industry[industry].append(s)

    # Root index
    root_body = render_hero(
        "Browse CPR & BLS Classes",
        "Find upcoming classes by month, certifying body, course, city, course in city, and industry."
    )
    root_body += '<div class="stack">'
    root_body += render_section(
        "Browse by Course + City",
        sorted(
            [
                (
                    f"/classes/course-at-city/{k}.html",
                    f"{v[0]['course_name']} in {v[0]['city']}"
                )
                for k, v in by_course_city.items()
            ],
            key=lambda x: x[1].lower()
        )
    )
    root_body += render_section(
        "Browse by Course",
        sorted(
            [
                (f"/classes/courses/{k}.html", v[0]["course_name"])
                for k, v in by_course.items()
            ],
            key=lambda x: x[1].lower()
        )
    )
    root_body += render_section(
        "Browse by City",
        sorted(
            [
                (f"/classes/cities/{k}.html", v[0]["city"])
                for k, v in by_city.items()
            ],
            key=lambda x: x[1].lower()
        )
    )
    root_body += render_section(
        "Browse by Month",
        sorted(
            [
                (f"/classes/months/{k}.html", v[0]["month_label"])
                for k, v in by_month.items()
            ],
            key=lambda x: x[1].lower()
        )
    )
    root_body += render_section(
        "Browse by Certifying Body",
        sorted(
            [
                (f"/classes/certifying-bodies/{k}.html", v[0]["certifying_body"])
                for k, v in by_cert.items()
            ],
            key=lambda x: x[1].lower()
        )
    )
    root_body += render_section(
        "Browse by Industry",
        sorted(
            [
                (f"/classes/industries/{k}.html", k.replace("-", " ").title())
                for k in by_industry.keys()
            ],
            key=lambda x: x[1].lower()
        )
    )
    root_body += "</div>"

    generated_paths.add(write_file(
        os.path.join(BASE_DIR, "index.html"),
        page(
            "CPR Classes | 910CPR",
            "Browse CPR and BLS classes by month, certifying body, course, city, course in city, and industry.",
            "/classes/",
            root_body,
        ),
    ))
    for s in sessions:
        generated_paths.add(os.path.normpath(os.path.join(BASE_DIR, f"{quote(s['session_id'])}.html")))

    # Month pages
    for month_key, items in by_month.items():
        items = sorted(items, key=lambda s: (s["date"], s["time"], s["course_name"]))
        month_label = items[0]["month_label"]
        body = render_hero(month_label, f"Browse upcoming classes scheduled for {month_label}.", "Browse by Month")
        body += '<div class="stack">'
        body += render_section(
            f"{month_label} Classes",
            [(s["url"], session_label(s)) for s in items]
        )
        body += "</div>"

        generated_paths.add(write_file(
            os.path.join(BASE_DIR, "months", f"{month_key}.html"),
            page(
                f"{month_label} CPR Classes | 910CPR",
                f"Browse upcoming CPR and BLS classes for {month_label}.",
                f"/classes/months/{month_key}.html",
                body,
            ),
        ))

    # Certifying body pages
    for cert_slug, items in by_cert.items():
        items = sorted(items, key=lambda s: (s["course_name"], s["date"], s["time"]))
        cert_name = items[0]["certifying_body"]
        body = render_hero(
            f"{cert_name} Classes",
            f"Browse upcoming {cert_name} classes."
        )
        body += '<div class="stack">'
        body += render_section(
            f"{cert_name} Sessions",
            [(s["url"], session_label(s)) for s in items]
        )
        body += "</div>"

        write_file(
            os.path.join(BASE_DIR, "certifying-bodies", f"{cert_slug}.html"),
            page(
                f"{cert_name} Classes | 910CPR",
                f"Browse upcoming {cert_name} classes.",
                f"/classes/certifying-bodies/{cert_slug}.html",
                body,
            ),
        )

    # Course pages
    for course_slug, items in by_course.items():
        items = sorted(items, key=lambda s: (s["date"], s["time"], s["city"]))
        course_name = items[0]["course_name"]
        body = render_hero(
            f"{course_name} Classes",
            f"Browse upcoming {course_name} classes by city and date."
        )
        body += '<div class="stack">'
        body += render_section(
            "Upcoming Sessions",
            [(s["url"], session_label(s)) for s in items]
        )
        body += "</div>"

        generated_paths.add(write_file(
            os.path.join(BASE_DIR, "courses", f"{course_slug}.html"),
            page(
                f"{course_name} Classes | 910CPR",
                f"Browse upcoming {course_name} classes and compare dates and locations.",
                f"/classes/courses/{course_slug}.html",
                body,
            ),
        ))

    # City pages
    for city_slug, items in by_city.items():
        items = sorted(items, key=lambda s: (s["course_name"], s["date"], s["time"]))
        city = items[0]["city"]
        body = render_hero(
            f"Classes in {city}",
            f"Browse upcoming CPR and BLS classes in {city}."
        )
        body += '<div class="stack">'
        body += render_section(
            "Upcoming Sessions",
            [(s["url"], session_label(s)) for s in items]
        )
        body += "</div>"

        generated_paths.add(write_file(
            os.path.join(BASE_DIR, "cities", f"{city_slug}.html"),
            page(
                f"CPR Classes in {city} | 910CPR",
                f"Browse upcoming CPR and BLS classes in {city}.",
                f"/classes/cities/{city_slug}.html",
                body,
            ),
        ))

    # Course at city pages
    for key, items in by_course_city.items():
        items = sorted(items, key=lambda s: (s["date"], s["time"]))
        course_name = items[0]["course_name"]
        city = items[0]["city"]
        body = render_hero(
            f"{course_name} in {city}",
            f"Browse upcoming {course_name} sessions in {city}."
        )
        body += '<div class="stack">'
        body += render_section(
            "Upcoming Sessions",
            [(s["url"], f"{s['date']} at {s['time']}") for s in items]
        )
        body += "</div>"

        generated_paths.add(write_file(
            os.path.join(BASE_DIR, "course-at-city", f"{key}.html"),
            page(
                f"{course_name} in {city} | 910CPR",
                f"Browse upcoming {course_name} classes in {city}.",
                f"/classes/course-at-city/{key}.html",
                body,
            ),
        ))

    # Industry pages
    for industry, items in by_industry.items():
        items = sorted(items, key=lambda s: (s["course_name"], s["date"], s["time"]))
        industry_name = industry.replace("-", " ").title()
        body = render_hero(
            f"Classes for {industry_name}",
            f"Browse upcoming classes relevant to {industry_name.lower()}."
        )
        body += '<div class="stack">'
        body += render_section(
            "Upcoming Sessions",
            [(s["url"], session_label(s)) for s in items]
        )
        body += "</div>"

        write_file(
            os.path.join(BASE_DIR, "industries", f"{industry}.html"),
            page(
                f"Classes for {industry_name} | 910CPR",
                f"Browse upcoming classes relevant to {industry_name.lower()}.",
                f"/classes/industries/{industry}.html",
                body,
            ),
        )
    deleted_paths = cleanup_stale_generated_pages(generated_paths)
    manifest = write_generated_manifest(generated_paths, deleted_paths, sessions)
    return manifest


def main():
    ensure_dirs()
    raw_sessions = load_schedule()
    public_raw_sessions = [
        s for s in raw_sessions
        if is_public_class_location(as_text(get_first(s, ("location_name", "location", "locationName", "venue"), "")))
    ]
    sessions = [normalize_session(s) for s in public_raw_sessions]
    manifest = build_indexes(sessions)
    print(f"Built classes index system from {manifest['source']}")
    print(f"Public sessions included: {manifest['public_session_count']}")
    print(f"Stale generated class files deleted: {len(manifest['deleted_stale_files'])}")


if __name__ == "__main__":
    main()
