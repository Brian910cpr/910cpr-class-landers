from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"

INPUT_PATHS = {
    "course_catalog": ROOT / "data" / "config" / "course_catalog.json",
    "people_catalog": ROOT / "data" / "config" / "people_catalog.json",
    "location_resource_map": ROOT / "data" / "config" / "location_resource_map.json",
    "seed_strategy_policy": ROOT / "data" / "config" / "seed_strategy_policy.json",
    "appointment_containers": ROOT / "data" / "inventory" / "appointment_containers.json",
    "live_availability_snapshot": AUDIT_DIR / "live_availability_snapshot_preview.json",
    "instructor_availability": ROOT / "data" / "inventory" / "instructor_availability.json",
    "sessions_current": ROOT / "data" / "sessions_current.json",
    "schedule_future": ROOT / "docs" / "data" / "schedule_future.json",
}

OFFERS_PATH = AUDIT_DIR / "dynamic_offers_preview.json"
REPORT_PATH = AUDIT_DIR / "dynamic_offers_report.md"
CONSUMPTION_SUMMARY_PATH = AUDIT_DIR / "scheduler_consumption_window_summary.json"
CONSUMPTION_REPORT_PATH = AUDIT_DIR / "scheduler_consumption_window_report.md"
UNKNOWN = "UNKNOWN"
START_INCREMENT_MINUTES = 15
DEFAULT_SETUP_BUFFER_MINUTES = 15
DEFAULT_CLEANUP_BUFFER_MINUTES = 30


def clean_text(value: Any) -> str:
    text = str(value or "").strip()
    return re.sub(r"\s+", " ", text)


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean_text(value).lower()).strip("_")


def is_unknown(value: Any) -> bool:
    return value in (None, "", UNKNOWN)


def int_or_default(value: Any, default: int) -> int:
    if is_unknown(value):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def read_json(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid_json: {exc}"
    except OSError as exc:
        return None, f"read_error: {exc}"


def parse_time(value: Any) -> time | None:
    text = clean_text(value)
    if not text:
        return None
    for fmt in ("%H:%M", "%I:%M %p"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = clean_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def combine_date_time(date_value: Any, time_value: Any) -> datetime | None:
    try:
        parsed_date = datetime.fromisoformat(str(date_value)).date()
    except ValueError:
        return None
    parsed_time = parse_time(time_value)
    if not parsed_time:
        return None
    return datetime.combine(parsed_date, parsed_time)


def availability_window_datetimes(window: dict[str, Any]) -> tuple[datetime | None, datetime | None, str]:
    start = parse_dt(window.get("start_datetime") or window.get("start_at"))
    end = parse_dt(window.get("end_datetime") or window.get("end_at"))
    if start and end:
        return start, end, "full_datetime"
    return (
        combine_date_time(window.get("date"), window.get("start_time")),
        combine_date_time(window.get("end_date") or window.get("date"), window.get("end_time")),
        "date_time_fields",
    )


def intervals_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and start_b < end_a


def person_certification_codes(person: dict[str, Any]) -> set[str]:
    codes: set[str] = set()
    certifications = person.get("certifications")
    if isinstance(certifications, list):
        for certification in certifications:
            code = certification.get("certification_code") if isinstance(certification, dict) else certification
            if not is_unknown(code):
                codes.add(str(code).strip())
    return codes


def scheduler_enabled_people(people_catalog: Any) -> list[dict[str, Any]]:
    if not isinstance(people_catalog, dict) or not isinstance(people_catalog.get("people"), list):
        return []
    people = []
    for person in people_catalog["people"]:
        if not isinstance(person, dict):
            continue
        assignment_mode = str(person.get("assignment_mode") or "").upper()
        if person.get("dynamic_offer_eligible") is True and assignment_mode in {"PRIMARY", "SECONDARY"}:
            people.append(person)
    return people


def people_lookup(people: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    direct: dict[str, dict[str, Any]] = {}
    first_names: dict[str, list[dict[str, Any]]] = {}
    for person in people:
        display_name = clean_text(person.get("display_name"))
        email = clean_text(person.get("email"))
        email_local = email.split("@", 1)[0] if "@" in email else ""
        keys = {
            normalize_key(person.get("person_id")),
            normalize_key(display_name),
            normalize_key(email),
            normalize_key(email_local),
        }
        external_ids = person.get("external_ids") if isinstance(person.get("external_ids"), dict) else {}
        keys.add(normalize_key(external_ids.get("instructor_id")))
        for key in keys:
            if key:
                direct[key] = person
        first = normalize_key(display_name.split(" ")[0]) if display_name else ""
        if first:
            first_names.setdefault(first, []).append(person)
    for first, matches in first_names.items():
        if len(matches) == 1 and first not in direct:
            direct[first] = matches[0]
    return direct


def courses(course_catalog: Any) -> list[dict[str, Any]]:
    if not isinstance(course_catalog, dict) or not isinstance(course_catalog.get("courses"), list):
        return []
    return [course for course in course_catalog["courses"] if isinstance(course, dict)]


def availability_windows(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("availability_blocks"), list):
        return []
    return [window for window in payload["availability_blocks"] if isinstance(window, dict)]


def active_appointment_containers(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("containers"), list):
        return []
    return [item for item in payload["containers"] if isinstance(item, dict) and item.get("status") == "active"]


def location_alias_lookup(location_resource_map: Any) -> dict[str, dict[str, str]]:
    if not isinstance(location_resource_map, dict) or not isinstance(location_resource_map.get("locations"), list):
        return {}
    lookup: dict[str, dict[str, str]] = {}
    for location in location_resource_map["locations"]:
        if not isinstance(location, dict):
            continue
        canonical = clean_text(location.get("canonical_public_location"))
        aliases = list(location.get("aliases", [])) if isinstance(location.get("aliases"), list) else []
        resources = location.get("internal_resources", []) if isinstance(location.get("internal_resources"), list) else []
        values = [canonical, *aliases]
        values.extend(resource.get("resource_name") for resource in resources if isinstance(resource, dict))
        for value in values:
            text = clean_text(value)
            if text:
                lookup[normalize_key(text)] = {
                    "canonical_public_location": canonical,
                    "resource_name": text,
                }
    return lookup


def normalize_location_resource(location_value: Any, resource_value: Any, location_resource_map: Any) -> tuple[str, str, bool]:
    location = clean_text(location_value or UNKNOWN) or UNKNOWN
    resource = clean_text(resource_value or location) or location
    lookup = location_alias_lookup(location_resource_map)
    location_match = lookup.get(normalize_key(location))
    resource_match = lookup.get(normalize_key(resource))
    match = location_match or resource_match
    if not match:
        return location, resource, False
    canonical = match["canonical_public_location"] or location
    resource_name = resource_match["resource_name"] if resource_match else (location_match["resource_name"] if location_match and normalize_key(location) != normalize_key(canonical) else resource)
    return canonical, resource_name, True


def instructor_matches_container(person: dict[str, Any], container: dict[str, Any]) -> bool:
    container_name = clean_text(container.get("instructor_name"))
    if not container_name:
        return True
    person_name = clean_text(person.get("display_name"))
    if normalize_key(container_name) == normalize_key(person_name):
        return True
    return normalize_key(person_name).startswith(normalize_key(container_name) + "_")


def parse_date(value: Any):
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def appointment_day_id_for(container: dict[str, Any], target_date: Any) -> int | None:
    target = parse_date(target_date)
    first = parse_date(container.get("first_valid_date"))
    if not target or not first:
        return None
    try:
        return int(container["first_valid_appointmentDayId"]) + (target - first).days
    except (KeyError, TypeError, ValueError):
        return None


def container_date_in_range(container: dict[str, Any], target_date: Any) -> bool:
    target = parse_date(target_date)
    first = parse_date(container.get("first_valid_date"))
    last = parse_date(container.get("last_valid_date"))
    day_id = appointment_day_id_for(container, target_date)
    if not target or not first or not last or day_id is None:
        return False
    try:
        first_id = int(container.get("first_valid_appointmentDayId", -1))
        last_id = int(container.get("last_valid_appointmentDayId", -1))
        first_invalid = container.get("first_invalid_appointmentDayId")
        return first <= target <= last and first_id <= day_id <= last_id and (first_invalid is None or day_id < int(first_invalid))
    except (TypeError, ValueError):
        return False


def valid_available_window(window: dict[str, Any]) -> bool:
    if window.get("availability_status") != "available":
        return False
    start, end, _source = availability_window_datetimes(window)
    return bool(start and end)


def normalize_live_availability_window(window: dict[str, Any], index: int, location_resource_map: Any = None) -> dict[str, Any]:
    raw_location = clean_text(window.get("location_name") or window.get("location") or UNKNOWN) or UNKNOWN
    raw_resource = clean_text(window.get("room_or_resource_name") or window.get("resource") or raw_location)
    location, resource, normalized = normalize_location_resource(raw_location, raw_resource, location_resource_map)
    reasons = list(window.get("reasons") or []) if isinstance(window.get("reasons"), list) else []
    if normalized:
        reasons.append("location_resource_map_normalized")
    return {
        "instructor_name": clean_text(window.get("instructor_name") or UNKNOWN),
        "person_id": clean_text(window.get("person_id") or UNKNOWN),
        "date": window.get("date"),
        "end_date": window.get("end_date"),
        "start_datetime": window.get("start_datetime"),
        "end_datetime": window.get("end_datetime"),
        "start_time": window.get("start_time"),
        "end_time": window.get("end_time"),
        "availability_status": "available",
        "availability_location_mode": clean_text(window.get("availability_location_mode") or "location_specific"),
        "source_location": clean_text(window.get("source_location") or raw_location),
        "location_name": location,
        "room_or_resource_name": resource,
        "raw_location_name": raw_location,
        "allowed_course_families": window.get("allowed_course_families") if isinstance(window.get("allowed_course_families"), list) else [],
        "source_availability_window": clean_text(window.get("source_event_id") or f"live_availability_snapshot[{index}]"),
        "source_calendar_id": window.get("source_calendar_id", UNKNOWN),
        "source_type": window.get("source_type", UNKNOWN),
        "reasons": [str(reason) for reason in reasons],
    }


def selected_availability_windows(loaded: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    live_payload = loaded.get("live_availability_snapshot")
    location_resource_map = loaded.get("location_resource_map")
    live_error = None
    if live_payload is not None and not isinstance(live_payload, dict):
        live_error = "invalid_live_snapshot_shape"
    live_raw_blocks = availability_windows(live_payload)
    live_blocks = [
        normalize_live_availability_window(window, index, location_resource_map)
        for index, window in enumerate(live_raw_blocks, start=1)
        if valid_available_window(window)
    ]
    if live_blocks:
        return live_blocks, {
            "availability_source_used": "live_availability_snapshot",
            "availability_fallback_used": False,
            "available_blocks_read": len(live_blocks),
            "live_available_blocks_read": len(live_blocks),
            "legacy_available_blocks_read": 0,
            "availability_source_reason": "valid_live_available_blocks_found",
        }

    legacy_raw_blocks = availability_windows(loaded.get("instructor_availability"))
    legacy_blocks = [window for window in legacy_raw_blocks if valid_available_window(window)]
    reason = "live_snapshot_missing"
    if live_payload is not None:
        reason = live_error or "live_snapshot_zero_available_blocks"
    return legacy_blocks, {
        "availability_source_used": "legacy_instructor_availability_fallback",
        "availability_fallback_used": True,
        "available_blocks_read": len(legacy_blocks),
        "live_available_blocks_read": len(live_blocks),
        "legacy_available_blocks_read": len(legacy_blocks),
        "availability_source_reason": reason,
    }


def normalize_occupancy(payload: Any, source_file: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("sessions"), list):
        return []
    out: list[dict[str, Any]] = []
    for session in payload["sessions"]:
        if not isinstance(session, dict):
            continue
        start = parse_dt(session.get("start_at") or session.get("start") or session.get("start_datetime"))
        end = parse_dt(session.get("end_at") or session.get("end") or session.get("end_datetime"))
        out.append({
            "start": start,
            "end": end,
            "location": clean_text(session.get("location_name") or session.get("location_display") or session.get("location")),
            "instructor": clean_text(session.get("lead_instructor_name") or session.get("instructor")),
            "course_title": clean_text(session.get("course_name") or session.get("official_course_name") or session.get("raw_course_name") or UNKNOWN),
            "source_file": source_file,
        })
    return out


def course_allowed_by_window(course: dict[str, Any], window: dict[str, Any]) -> bool:
    family = str(course.get("family") or "").strip()
    allowed = {str(item).strip() for item in window.get("allowed_course_families", [])}
    return bool(family and (not allowed or family in allowed))


def reject(rejections: list[dict[str, Any]], reason_code: str, message: str, context: dict[str, Any]) -> None:
    item = dict(context)
    item.update({"reason_code": reason_code, "message": message})
    rejections.append(item)


def candidate_starts(start: datetime, latest_start: datetime) -> list[datetime]:
    values = []
    cursor = start
    while cursor <= latest_start:
        values.append(cursor)
        cursor += timedelta(minutes=START_INCREMENT_MINUTES)
    return values


def consumption_window(start: datetime, duration_minutes: int, setup_buffer_minutes: int, cleanup_buffer_minutes: int) -> tuple[datetime, datetime, int]:
    total = duration_minutes + setup_buffer_minutes + cleanup_buffer_minutes
    return start, start + timedelta(minutes=total), total


def has_conflict(start: datetime, end: datetime, occupancy: list[dict[str, Any]], location: str, person: dict[str, Any]) -> tuple[bool, str | None]:
    person_names = {
        normalize_key(person.get("display_name")),
        normalize_key(str(person.get("display_name") or "").split(" ")[0]),
    }
    for block in occupancy:
        block_start = block.get("start")
        block_end = block.get("end")
        if not block_start or not block_end:
            continue
        same_location = location and normalize_key(block.get("location")) == normalize_key(location)
        same_instructor = normalize_key(block.get("instructor")) in person_names
        if (same_location or same_instructor) and intervals_overlap(start, end, block_start, block_end):
            return True, f"conflicts with {block.get('course_title')} from {block.get('source_file')}"
    return False, None


def occupancy_by_date(occupancy: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    indexed: dict[str, list[dict[str, Any]]] = {}
    for block in occupancy:
        block_start = block.get("start")
        block_end = block.get("end")
        if not block_start or not block_end:
            continue
        cursor = block_start.date()
        last = block_end.date()
        while cursor <= last:
            indexed.setdefault(cursor.isoformat(), []).append(block)
            cursor += timedelta(days=1)
    return indexed


def occupancy_candidates(indexed: dict[str, list[dict[str, Any]]], start: datetime, end: datetime) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[int] = set()
    cursor = start.date()
    last = end.date()
    while cursor <= last:
        for block in indexed.get(cursor.isoformat(), []):
            marker = id(block)
            if marker in seen:
                continue
            seen.add(marker)
            candidates.append(block)
        cursor += timedelta(days=1)
    return candidates


def offer_id(course_id: str, person_id: str, start: datetime) -> str:
    return f"offer-{course_id}-{normalize_key(person_id)}-{start:%Y%m%d-%H%M}"


def generate_offers(loaded: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    course_list = courses(loaded.get("course_catalog"))
    seed_strategy_policy = loaded.get("seed_strategy_policy") if isinstance(loaded.get("seed_strategy_policy"), dict) else {}
    default_setup_buffer_minutes = int_or_default(seed_strategy_policy.get("default_setup_buffer_minutes"), DEFAULT_SETUP_BUFFER_MINUTES)
    default_cleanup_buffer_minutes = int_or_default(seed_strategy_policy.get("default_cleanup_buffer_minutes"), DEFAULT_CLEANUP_BUFFER_MINUTES)
    windows, availability_stats = selected_availability_windows(loaded)
    people = scheduler_enabled_people(loaded.get("people_catalog"))
    people_by_key = people_lookup(people)
    appointment_containers = active_appointment_containers(loaded.get("appointment_containers"))
    occupancy = [
        *normalize_occupancy(loaded.get("sessions_current"), "data/sessions_current.json"),
        *normalize_occupancy(loaded.get("schedule_future"), "docs/data/schedule_future.json"),
    ]
    occupancy_index = occupancy_by_date(occupancy)
    offers: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []

    for window_index, window in enumerate(windows, start=1):
        source_window = clean_text(window.get("source_availability_window")) or f"{availability_stats['availability_source_used']}[{window_index}]"
        context = {
            "source_availability_window": source_window,
            "availability_instructor": clean_text(window.get("instructor_name") or UNKNOWN),
            "availability_source_used": availability_stats["availability_source_used"],
        }
        if window.get("availability_status") not in (None, "", "available"):
            reject(rejections, "availability_window_not_available", "Availability window status is not available.", context)
            continue
        window_start, window_end, window_time_source = availability_window_datetimes(window)
        if not window_start or not window_end:
            reject(rejections, "unknown_availability_window_time", "Availability window is missing parseable date/start/end values.", context)
            continue
        if window_end <= window_start:
            reject(rejections, "invalid_time_range", "Availability window end is not after start.", {
                **context,
                "window_time_source": window_time_source,
                "start_datetime": window_start.isoformat(),
                "end_datetime": window_end.isoformat(),
            })
            continue
        person = people_by_key.get(normalize_key(window.get("person_id"))) or people_by_key.get(normalize_key(window.get("instructor_name")))
        if not person:
            reject(rejections, "missing_scheduler_enabled_person", "Availability instructor did not match a scheduler-enabled People record.", context)
            continue

        person_codes = person_certification_codes(person)
        source_location = clean_text(window.get("source_location") or window.get("raw_location_name") or window.get("location_name") or UNKNOWN) or UNKNOWN
        location_targets = [{
            "location": clean_text(window.get("location_name") or UNKNOWN) or UNKNOWN,
            "resource": clean_text(window.get("room_or_resource_name") or window.get("location_name") or UNKNOWN) or UNKNOWN,
            "matched_container_id": None,
            "appointmentDayId": None,
            "target_reason": "source_location_specific_window",
        }]
        if clean_text(window.get("availability_location_mode")) == "instructor_time_only":
            matching_containers = [
                container for container in appointment_containers
                if instructor_matches_container(person, container) and container_date_in_range(container, window_start.date().isoformat())
            ]
            location_targets = [{
                "location": clean_text(container.get("location_name") or UNKNOWN) or UNKNOWN,
                "resource": clean_text(container.get("room_or_resource_name") or container.get("location_name") or UNKNOWN) or UNKNOWN,
                "matched_container_id": container.get("container_id"),
                "appointmentDayId": appointment_day_id_for(container, window_start.date().isoformat()),
                "target_reason": "instructor_time_only_confirmed_container_target",
            } for container in matching_containers]
            if not location_targets:
                reject(rejections, "no_matching_appointment_container", "Instructor-time availability has no active appointment container target for this date.", context)
                continue
        for course in course_list:
            course_id = str(course.get("course_id") or UNKNOWN)
            title = clean_text(course.get("official_title") or course.get("short_title") or UNKNOWN)
            family = str(course.get("family") or UNKNOWN)
            course_context = {
                **context,
                "course_id": course_id,
                "course_title": title,
                "course_family": family,
                "person_id": person.get("person_id", UNKNOWN),
                "person_name": person.get("display_name", UNKNOWN),
            }
            if course.get("appointment_allowed") is not True:
                reject(rejections, "appointment_not_allowed", "Course is not appointment-allowed in course_catalog.json.", course_context)
                continue
            if not course_allowed_by_window(course, window):
                reject(rejections, "course_family_not_allowed_by_window", "Course family is not allowed by this availability window.", course_context)
                continue
            duration = course.get("duration_minutes")
            capacity = course.get("default_capacity")
            try:
                duration_minutes = int(duration)
            except (TypeError, ValueError):
                reject(rejections, "missing_course_duration", "Course is missing numeric duration_minutes.", course_context)
                continue
            if not isinstance(capacity, int):
                try:
                    capacity = int(capacity)
                except (TypeError, ValueError):
                    reject(rejections, "missing_course_capacity", "Course is missing numeric default_capacity.", course_context)
                    continue
            requirements = {
                str(code).strip()
                for code in course.get("required_instructor_certifications", [])
                if not is_unknown(code)
            }
            if not requirements:
                reject(rejections, "missing_required_instructor_certification", "Course lacks required_instructor_certifications.", course_context)
                continue
            if not person_codes.intersection(requirements):
                reject(rejections, "instructor_lacks_required_certification", "Instructor lacks required certification for this course.", course_context)
                continue
            setup_buffer_minutes = int_or_default(course.get("setup_buffer_minutes"), default_setup_buffer_minutes)
            cleanup_buffer_minutes = int_or_default(course.get("cleanup_buffer_minutes"), default_cleanup_buffer_minutes)
            scheduler_consumption_minutes = duration_minutes + setup_buffer_minutes + cleanup_buffer_minutes
            latest_start = window_end - timedelta(minutes=scheduler_consumption_minutes)
            if latest_start < window_start:
                reject(rejections, "course_does_not_fit_window", "Course duration does not fit inside this availability window.", course_context)
                continue
            for target in location_targets:
                location = target["location"]
                resource = target["resource"]
                for start in candidate_starts(window_start, latest_start):
                    appointment_display_end = start + timedelta(minutes=duration_minutes)
                    lock_start, lock_end, lock_minutes = consumption_window(start, duration_minutes, setup_buffer_minutes, cleanup_buffer_minutes)
                    conflict, reason = has_conflict(lock_start, lock_end, occupancy_candidates(occupancy_index, lock_start, lock_end), location, person)
                    if conflict:
                        reject(rejections, "conflicts_with_existing_occupancy", reason or "Conflicts with existing occupancy.", {
                            **course_context,
                            "date": lock_start.date().isoformat(),
                            "start_time": lock_start.strftime("%H:%M"),
                            "end_time": lock_end.strftime("%H:%M"),
                        })
                        continue
                    offers.append({
                        "offer_id": offer_id(course_id, str(person.get("person_id") or UNKNOWN), start),
                        "start_datetime": start.isoformat(),
                        "end_datetime": appointment_display_end.isoformat(),
                        "date": start.date().isoformat(),
                        "start_time": start.strftime("%H:%M"),
                        "end_time": appointment_display_end.strftime("%H:%M"),
                        "appointment_display_start": start.isoformat(),
                        "appointment_display_end": appointment_display_end.isoformat(),
                        "scheduler_consumption_start": lock_start.isoformat(),
                        "scheduler_consumption_end": lock_end.isoformat(),
                        "scheduler_consumption_minutes": lock_minutes,
                        "setup_buffer_minutes": setup_buffer_minutes,
                        "cleanup_buffer_minutes": cleanup_buffer_minutes,
                        "instructor_lock_start": lock_start.isoformat(),
                        "instructor_lock_end": lock_end.isoformat(),
                        "resource_lock_start": lock_start.isoformat(),
                        "resource_lock_end": lock_end.isoformat(),
                        "course_id": course_id,
                        "course_title": title,
                        "course_family": family,
                        "duration_minutes": duration_minutes,
                        "capacity": capacity,
                        "instructor_person_id": person.get("person_id", UNKNOWN),
                        "instructor_display_name": person.get("display_name", UNKNOWN),
                        "instructor_assignment_mode": person.get("assignment_mode", UNKNOWN),
                        "location": location,
                        "offer_location": location,
                        "resource": resource,
                        "source_location": source_location,
                        "travel_buffer_needed": True if normalize_key(source_location) != normalize_key(location) and source_location != UNKNOWN else False,
                        "travel_buffer_status": "not_calculated",
                        "matched_container_id": target.get("matched_container_id"),
                        "appointmentDayId": target.get("appointmentDayId"),
                        "source_availability_window": source_window,
                        "confidence": "high",
                        "reasons": [
                            "live_calendar_availability_window" if availability_stats["availability_source_used"] == "live_availability_snapshot" else "explicit_local_availability_window",
                            target["target_reason"],
                            "scheduler_enabled_person",
                            "course_catalog_duration_capacity_appointment_allowed",
                            "instructor_has_required_certification",
                            "no_known_local_occupancy_conflict",
                            "travel_buffer_not_calculated",
                            "read_only_preview_not_public_offer",
                        ],
                    })

    stats = {
        **availability_stats,
        "availability_windows_read": len(windows),
        "scheduler_enabled_instructors_considered": len(people),
        "courses_considered": len(course_list),
        "occupancy_blocks_read": len(occupancy),
        "active_appointment_containers_read": len(appointment_containers),
        "default_setup_buffer_minutes": default_setup_buffer_minutes,
        "default_cleanup_buffer_minutes": default_cleanup_buffer_minutes,
        "offers_generated": len(offers),
        "offers_rejected_by_reason": dict(Counter(item["reason_code"] for item in rejections).most_common()),
    }
    return offers, rejections, stats


def consumption_warnings(offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for offer in offers:
        duration = int_or_default(offer.get("duration_minutes"), 0)
        total = int_or_default(offer.get("scheduler_consumption_minutes"), duration)
        if total > duration:
            warnings.append({
                "offer_id": offer.get("offer_id", UNKNOWN),
                "course_id": offer.get("course_id", UNKNOWN),
                "course_title": offer.get("course_title", UNKNOWN),
                "date": offer.get("date", UNKNOWN),
                "appointment_display_start": offer.get("appointment_display_start", UNKNOWN),
                "appointment_display_end": offer.get("appointment_display_end", UNKNOWN),
                "scheduler_consumption_start": offer.get("scheduler_consumption_start", UNKNOWN),
                "scheduler_consumption_end": offer.get("scheduler_consumption_end", UNKNOWN),
                "appointment_display_minutes": duration,
                "scheduler_consumption_minutes": total,
                "warning_code": "appointment_display_shorter_than_scheduler_consumption",
            })
    return warnings


def render_consumption_report(warnings: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# Scheduler Consumption Window Report",
        "",
        "Read-only audit. Lander scheduling uses course duration plus setup/cleanup buffers for lock windows; Enrollware appointment display time remains URL/display-only.",
        "",
        "## Summary",
        "",
        f"- Offers with scheduler consumption windows: {summary['offers_with_scheduler_consumption_windows']}",
        f"- Warnings where appointment display is shorter than scheduler consumption: {summary['display_shorter_than_consumption_warnings']}",
        f"- Default setup buffer minutes: {summary['default_setup_buffer_minutes']}",
        f"- Default cleanup buffer minutes: {summary['default_cleanup_buffer_minutes']}",
        "",
        "## Warnings",
        "",
    ]
    if warnings:
        lines.extend(["| Date | Course | Display | Scheduler lock | Warning |", "| --- | --- | --- | --- | --- |"])
        for item in warnings[:100]:
            lines.append(
                f"| {item['date']} | {item['course_title']} | {item['appointment_display_start']} to {item['appointment_display_end']} | "
                f"{item['scheduler_consumption_start']} to {item['scheduler_consumption_end']} | `{item['warning_code']}` |"
            )
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Travel-Aware TODO",
        "",
        "- Future trimming should consider cleanup after a prior class, travel time from prior/blocking event address to the target class location, setup before the target class, and different target locations such as Wilmington, Burgaw, and Holly Ridge.",
        "",
    ])
    return "\n".join(lines)


def render_report(offers: list[dict[str, Any]], rejections: list[dict[str, Any]], stats: dict[str, Any], loaded: dict[str, Any], missing: dict[str, str]) -> str:
    lines = [
        "# Dynamic Offers Preview Report",
        "",
        "This is a read-only V0 dynamic offer generator. It did not modify public pages, Enrollware behavior, appointment URLs, Worker settings, generated HTML, or docs output.",
        "",
        "## Files Read",
        "",
    ]
    lines.extend(f"- `{name}`" for name in sorted(loaded))
    lines.extend(["", "## Files Missing Or Unreadable", ""])
    if missing:
        lines.extend(f"- `{name}`: {reason}" for name, reason in sorted(missing.items()))
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Summary",
        "",
        f"- Availability source used: {stats['availability_source_used']}",
        f"- Availability fallback used: {stats['availability_fallback_used']}",
        f"- Available blocks read from selected source: {stats['available_blocks_read']}",
        f"- Availability source reason: {stats['availability_source_reason']}",
        f"- Availability windows read: {stats['availability_windows_read']}",
        f"- Scheduler-enabled instructors considered: {stats['scheduler_enabled_instructors_considered']}",
        f"- Courses considered: {stats['courses_considered']}",
        f"- Local occupancy blocks read: {stats['occupancy_blocks_read']}",
        f"- Offers generated: {stats['offers_generated']}",
        "",
        "## Offers Rejected By Reason",
        "",
    ])
    if stats["offers_rejected_by_reason"]:
        lines.extend(f"- `{reason}`: {count}" for reason, count in stats["offers_rejected_by_reason"].items())
    else:
        lines.append("- None")
    lines.extend(["", "## Top 20 Example Offers", ""])
    if offers:
        lines.extend(["| Date | Time | Course | Instructor | Location |", "| --- | --- | --- | --- | --- |"])
        for offer in offers[:20]:
            lines.append(
                f"| {offer['date']} | {offer['start_time']}-{offer['end_time']} | "
                f"{offer['course_title']} | {offer['instructor_display_name']} | {offer['location']} |"
            )
    else:
        lines.append("- No offers generated.")
    blockers = Counter(item["reason_code"] for item in rejections).most_common(10)
    lines.extend(["", "## Blockers Preventing More Offers", ""])
    if blockers:
        lines.extend(f"- `{reason}`: {count}" for reason, count in blockers)
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Next Safest Step",
        "",
        "- Review the generated offer list with Brian, then add a read-only policy layer for which course families/formats should be public sellable before any public UI or appointment bridge uses these offers.",
        "",
    ])
    return "\n".join(lines)


def run() -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    missing: dict[str, str] = {}
    for name, path in INPUT_PATHS.items():
        payload, error = read_json(path)
        if error:
            missing[name] = error
        else:
            loaded[name] = payload
    offers, rejections, stats = generate_offers(loaded)
    warnings = consumption_warnings(offers)
    consumption_summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "public_site_affected": False,
        "offers_with_scheduler_consumption_windows": sum(1 for offer in offers if offer.get("scheduler_consumption_start") and offer.get("scheduler_consumption_end")),
        "display_shorter_than_consumption_warnings": len(warnings),
        "default_setup_buffer_minutes": stats.get("default_setup_buffer_minutes", DEFAULT_SETUP_BUFFER_MINUTES),
        "default_cleanup_buffer_minutes": stats.get("default_cleanup_buffer_minutes", DEFAULT_CLEANUP_BUFFER_MINUTES),
        "warning_codes": dict(Counter(item["warning_code"] for item in warnings)),
        "warnings": warnings[:250],
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    preview = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "public_site_affected": False,
        "enrollware_called": False,
        "google_calendar_called": False,
        "files_read": sorted(loaded),
        "files_missing_or_unreadable": missing,
        "stats": stats,
        "offers": offers,
        "rejections": rejections,
    }
    OFFERS_PATH.write_text(json.dumps(preview, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(offers, rejections, stats, loaded, missing), encoding="utf-8")
    CONSUMPTION_SUMMARY_PATH.write_text(json.dumps(consumption_summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    CONSUMPTION_REPORT_PATH.write_text(render_consumption_report(warnings, consumption_summary), encoding="utf-8")
    return {
        "files_read": sorted(loaded),
        "files_missing_or_unreadable": missing,
        "availability_source_used": stats["availability_source_used"],
        "availability_fallback_used": stats["availability_fallback_used"],
        "available_blocks_read": stats["available_blocks_read"],
        "offers_generated": len(offers),
        "rejections_generated": len(rejections),
        "output_paths": [OFFERS_PATH, REPORT_PATH, CONSUMPTION_SUMMARY_PATH, CONSUMPTION_REPORT_PATH],
    }


def main() -> int:
    result = run()
    print("Dynamic offers preview complete (READ ONLY).")
    print("No public pages, Enrollware behavior, appointment URLs, Worker settings, generated HTML, docs output, or live calendars were changed.")
    print("")
    print("Files read:")
    for name in result["files_read"]:
        print(f"- {name}: {INPUT_PATHS[name]}")
    if result["files_missing_or_unreadable"]:
        print("")
        print("Files missing or unreadable:")
        for name, reason in sorted(result["files_missing_or_unreadable"].items()):
            print(f"- {name}: {reason}")
    print("")
    print(f"Availability source used: {result['availability_source_used']}")
    print(f"Available blocks read: {result['available_blocks_read']}")
    print(f"Fallback used: {result['availability_fallback_used']}")
    print(f"Offers generated: {result['offers_generated']}")
    print(f"Rejections generated: {result['rejections_generated']}")
    print("")
    print("Output files:")
    for path in result["output_paths"]:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
