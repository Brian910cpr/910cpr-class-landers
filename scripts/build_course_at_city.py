import os
import json
from datetime import datetime
from pathlib import Path
from scripts.build_status import BuildStatusReporter
try:
    from tqdm import tqdm
except ModuleNotFoundError:
    def tqdm(iterable, **_kwargs):
        return iterable
from scripts.hub_utils import (
    SessionRecord,
    extract_city,
    normalize_course_family,
    upcoming_public_sessions,
    render_page,
    session_rows,
    slugify,
)
from scripts.public_class_eligibility import is_public_class_location

OUTPUT_DIR = os.path.join("docs", "course-at-city")
ROOT = Path(__file__).resolve().parents[1]
SESSIONS_INPUT = ROOT / "docs" / "public_schedule.json"


def load_public_schedule_sessions() -> list[SessionRecord]:
    payload = json.loads(SESSIONS_INPUT.read_text(encoding="utf-8"))
    rows = payload.get("sessions", []) if isinstance(payload, dict) else []
    sessions: list[SessionRecord] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        location = str(row.get("location_name") or row.get("location") or "")
        course_name = str(row.get("course") or row.get("title") or "")
        start_raw = str(row.get("start") or "")
        try:
            start_at = datetime.fromisoformat(start_raw.replace("Z", "+00:00")) if start_raw else None
            if start_at and start_at.tzinfo is not None:
                start_at = start_at.replace(tzinfo=None)
        except Exception:
            start_at = None
        sessions.append(SessionRecord(
            session_id=str(row.get("class_id") or row.get("session_id") or ""),
            course_html=course_name,
            course_name=course_name,
            course_family=normalize_course_family(course_name),
            course_id=str(row.get("course_id") or ""),
            cert_body="",
            body_course_title=course_name,
            delivery_code="",
            price="",
            start_at=start_at,
            end_at=None,
            location_raw=location,
            city=extract_city(location),
            instructor="",
            students=0,
            seats=0,
            registration_link=str(row.get("register_url") or ""),
            is_public=is_public_class_location(location),
            is_regional_private=False,
        ))
    return sessions


def valid_city(city: str) -> bool:
    value = str(city or "").strip()
    if not value:
        return False
    if value.lower() in {"nan", "none", "unknown"}:
        return False
    if value.isdigit():
        return False
    return True


def valid_family(family: str) -> bool:
    value = str(family or "").strip()
    return value in {
        "BLS",
        "ACLS",
        "PALS",
        "Heartsaver",
        "USCG Elementary First Aid | CPR",
    }


def purge_stale_outputs(output_dir: str) -> int:
    removed = 0
    for name in os.listdir(output_dir):
        if not name.lower().endswith(".html"):
            continue
        path = os.path.join(output_dir, name)
        if os.path.isfile(path):
            os.remove(path)
            removed += 1
    return removed


def eligible_course_at_city_sessions(sessions):
    eligible = []
    for s in sessions:
        location_name = str(
            getattr(s, "location_raw", "")
            or getattr(s, "location_name", "")
            or getattr(s, "location_display", "")
            or getattr(s, "location", "")
        )
        if not is_public_class_location(location_name):
            continue
        city = str(getattr(s, "city", "")).strip()
        family = str(getattr(s, "course_family", "")).strip()
        if not valid_city(city):
            continue
        if not valid_family(family):
            continue
        eligible.append(s)
    return eligible


def build_course_at_city():
    reporter = BuildStatusReporter("build_course_at_city")
    reporter.set_context(inputs=[SESSIONS_INPUT], outputs=[ROOT / OUTPUT_DIR])
    count = 0
    last_output = None
    try:
        sessions = load_public_schedule_sessions()
        future_public = upcoming_public_sessions(
            [s for s in sessions if getattr(s, "is_public", False)]
        )
        print(f"Loaded {len(sessions)} sessions")
        print(f"Found {len(future_public)} upcoming public sessions")

        combo_map = {}

        for s in eligible_course_at_city_sessions(future_public):
            city = str(getattr(s, "city", "")).strip()
            family = str(getattr(s, "course_family", "")).strip()

            key = (family, city)
            combo_map.setdefault(key, []).append(s)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        removed = purge_stale_outputs(OUTPUT_DIR)
        if removed:
            print(f"Removed {removed} stale course-at-city pages from {OUTPUT_DIR}")

        combos = sorted(combo_map.items())
        reporter.waiting(total=len(combos))
        reporter.start(total=len(combos))
        print(f"Building {len(combos)} course-at-city pages")

        for (family, city), group_sessions in tqdm(combos, desc="Building course-at-city pages", unit="page", miniters=1):
            filename = os.path.join(
                OUTPUT_DIR,
                f"{slugify(family)}-{slugify(city)}.html"
            )
            html = render_page(
                title=f"{family} Classes in {city}",
                body=f"""
<h1>{family} Classes in {city}</h1>
{session_rows(group_sessions)}
""",
                description=f"Upcoming {family} classes in {city}.",
                canonical_path="/" + filename.replace(os.sep, "/"),
            )
            last_output = filename

            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)

            count += 1
            reporter.update(current=count, total=len(combos), last_output_file=last_output)

        reporter.done(
            current=count,
            total=len(combos),
            last_output_file=last_output,
            pages_generated=count,
            counts={
                "sessions_loaded": len(sessions),
                "future_public_sessions": len(future_public),
                "course_at_city_pages": count,
            },
        )
        print(f"Wrote {count} filtered course-at-city pages to {OUTPUT_DIR}")
    except Exception:
        reporter.error(current=count, last_output_file=last_output)
        raise


if __name__ == "__main__":
    build_course_at_city()
