from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import generate_dynamic_offers
from scripts.build_seed_appointment_url_preview import (
    active_containers,
    build_registration_url,
    matching_container,
)
from scripts.public_class_eligibility import is_public_class_location


AUDIT_DIR = ROOT / "data" / "audit"
COURSE_RULES_PATH = ROOT / "data" / "inventory" / "course_consumption_rules.json"
COURSE_CATALOG_PATH = ROOT / "data" / "config" / "course_catalog.json"
PEOPLE_CATALOG_PATH = ROOT / "data" / "config" / "people_catalog.json"
LOCATION_RESOURCE_MAP_PATH = ROOT / "data" / "config" / "location_resource_map.json"
APPOINTMENT_CONTAINERS_PATH = ROOT / "data" / "inventory" / "appointment_containers.json"
PUBLIC_LOCATION_POLICY_PATH = ROOT / "data" / "config" / "public_location_policy.json"
PUBLIC_OFFER_POLICY_PATH = ROOT / "data" / "config" / "public_offer_policy.json"
BLOCK_SCHEDULE_PAGES_PATH = ROOT / "data" / "config" / "block_schedule_pages.json"
LIVE_AVAILABILITY_PATH = AUDIT_DIR / "live_availability_snapshot_preview.json"
LEGACY_AVAILABILITY_PATH = ROOT / "data" / "inventory" / "instructor_availability.json"
SESSIONS_CURRENT_PATH = ROOT / "data" / "sessions_current.json"
SCHEDULE_FUTURE_PATH = ROOT / "docs" / "data" / "schedule_future.json"

BLS_PILOT_COURSE_IDS = ("209806", "359474", "210549")
START_STEP_MINUTES = 30
AS_OF_DATE = date(2026, 7, 2)
UNKNOWN = "UNKNOWN"
APPROVED_INVERSE_AVAILABILITY_SOURCE_CALENDAR_IDS = {"brian_do_not_schedule"}


class BlockSelectorInputError(RuntimeError):
    pass


def read_required_json(path: Path) -> Any:
    if not path.exists():
        raise BlockSelectorInputError(f"Required real input is missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BlockSelectorInputError(f"Required real input is invalid JSON: {path} ({exc})") from exc


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean_text(value).lower()).strip("_")


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def display_time(value: datetime) -> str:
    return value.strftime("%I:%M %p").lstrip("0")


def display_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    return parsed.strftime("%A, %B %-d, %Y") if sys.platform != "win32" else parsed.strftime("%A, %B %#d, %Y")


def course_rules_by_id(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("rules"), list):
        raise BlockSelectorInputError(f"{COURSE_RULES_PATH} must contain a rules list")
    defaults = payload.get("defaults", {}) if isinstance(payload.get("defaults"), dict) else {}
    rules: dict[str, dict[str, Any]] = {}
    for raw_rule in payload["rules"]:
        if not isinstance(raw_rule, dict):
            continue
        rule = {**defaults, **raw_rule}
        course_id = clean_text(rule.get("course_id"))
        if not course_id:
            continue
        duration = int(rule.get("duration_minutes") or 0)
        setup = int(rule.get("setup_buffer_minutes") or 0)
        cleanup = int(rule.get("cleanup_buffer_minutes") or 0)
        minimum = int(rule.get("minimum_reservation_block_minutes") or 0)
        rules[course_id] = {
            **rule,
            "course_id": course_id,
            "duration_minutes": duration,
            "setup_buffer_minutes": setup,
            "cleanup_buffer_minutes": cleanup,
            "scheduler_consumption_minutes": max(duration + setup + cleanup, minimum),
            "minimum_reservation_block_minutes": minimum,
        }
    return rules


def courses_by_id(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("courses"), list):
        raise BlockSelectorInputError(f"{COURSE_CATALOG_PATH} must contain a courses list")
    return {
        str(course.get("course_id")): course
        for course in payload["courses"]
        if isinstance(course, dict) and course.get("course_id")
    }


def people_lookup(payload: Any) -> dict[str, dict[str, Any]]:
    people = generate_dynamic_offers.scheduler_enabled_people(payload)
    return generate_dynamic_offers.people_lookup(people)


def load_selected_windows(loaded: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    windows, stats = generate_dynamic_offers.selected_availability_windows(loaded)
    if not windows:
        raise BlockSelectorInputError("No real availability blocks were found in live snapshot or legacy fallback")
    return windows, stats


def live_snapshot_generated_at(payload: dict[str, Any]) -> datetime | None:
    generated_at = payload.get("generated_at") or payload.get("generatedAt")
    return parse_dt(generated_at)


def require_current_live_availability_snapshot() -> dict[str, Any]:
    payload = read_required_json(LIVE_AVAILABILITY_PATH)
    if not isinstance(payload, dict):
        raise BlockSelectorInputError(f"{LIVE_AVAILABILITY_PATH} must contain a JSON object")
    generated_at = live_snapshot_generated_at(payload)
    if not generated_at:
        raise BlockSelectorInputError(f"{LIVE_AVAILABILITY_PATH} is missing a valid generated_at timestamp")
    if generated_at.date() < AS_OF_DATE:
        raise BlockSelectorInputError(
            f"{LIVE_AVAILABILITY_PATH} is stale: generated_at={generated_at.isoformat()} "
            f"is before required as-of date {AS_OF_DATE.isoformat()}. "
            "Run python -m scripts.export_calendar_snapshots and python -m scripts.build_live_availability_snapshot."
        )
    return payload


def live_snapshot_block_id(window: dict[str, Any], index: int) -> str:
    return clean_text(window.get("source_event_id") or window.get("source_availability_window") or f"live_availability_snapshot[{index}]")


def selected_public_page_live_windows(live_payload: dict[str, Any], location_resource_map: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_blocks = generate_dynamic_offers.availability_windows(live_payload)
    selected: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    approved_inverse_used: list[dict[str, Any]] = []
    for index, window in enumerate(raw_blocks, start=1):
        if not generate_dynamic_offers.valid_available_window(window):
            continue
        block_id = live_snapshot_block_id(window, index)
        source_calendar_id = clean_text(window.get("source_calendar_id"))
        inverse_generated = window.get("inverse_generated") is True
        if inverse_generated and source_calendar_id not in APPROVED_INVERSE_AVAILABILITY_SOURCE_CALENDAR_IDS:
            suppressed.append({
                "date": window.get("date"),
                "startTime": window.get("start_time"),
                "endTime": window.get("end_time"),
                "sourceAvailabilityBlockId": block_id,
                "sourceCalendarId": source_calendar_id,
                "reason": "inverse_generated_availability_source_not_approved_for_public_page",
            })
            continue
        if inverse_generated:
            approved_inverse_used.append({
                "date": window.get("date"),
                "startTime": window.get("start_time"),
                "endTime": window.get("end_time"),
                "sourceAvailabilityBlockId": block_id,
                "sourceCalendarId": source_calendar_id,
                "reason": "approved_inverse_generated_availability_source",
            })
        normalized = generate_dynamic_offers.normalize_live_availability_window(window, index, location_resource_map)
        normalized["source_availability_window"] = block_id
        normalized["approved_inverse_generated"] = inverse_generated
        normalized["source_live_availability_block"] = {
            "sourceAvailabilityBlockId": block_id,
            "date": window.get("date"),
            "startDateTime": window.get("start_datetime"),
            "endDateTime": window.get("end_datetime"),
            "instructor": window.get("instructor_name"),
            "location": window.get("location_name"),
            "sourceCalendarId": window.get("source_calendar_id"),
            "sourceType": window.get("source_type"),
            "inverseGenerated": inverse_generated,
            "approvedInverseGenerated": inverse_generated,
        }
        selected.append(normalized)
    stats = {
        "availability_source_used": "live_availability_snapshot",
        "availability_fallback_used": False,
        "available_blocks_read": len(selected),
        "live_available_blocks_read": len(selected),
        "legacy_available_blocks_read": 0,
        "availability_source_reason": "strict_current_live_snapshot_public_page",
        "suppressed_available_blocks_read": len(suppressed),
        "suppressed_available_block_dates": sorted({str(item["date"]) for item in suppressed if item.get("date")}),
        "suppressed_available_blocks": suppressed[:500],
        "approved_inverse_blocks_used": approved_inverse_used[:500],
        "approved_inverse_blocks_used_count": len(approved_inverse_used),
        "unapproved_inverse_blocks_suppressed_count": len(suppressed),
        "approved_inverse_source_calendar_ids": sorted(APPROVED_INVERSE_AVAILABILITY_SOURCE_CALENDAR_IDS),
    }
    return selected, stats


def current_public_live_block_index() -> dict[str, dict[str, Any]]:
    location_resource_map = read_required_json(LOCATION_RESOURCE_MAP_PATH)
    live_payload = require_current_live_availability_snapshot()
    windows, _stats = selected_public_page_live_windows(live_payload, location_resource_map)
    out: dict[str, dict[str, Any]] = {}
    for window in windows:
        block_id = clean_text(window.get("source_availability_window"))
        if not block_id:
            continue
        start, end = window_datetimes(window)
        out[block_id] = {
            "block": window,
            "start": start,
            "end": end,
        }
    return out


def rebuild_payload_dates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    page_config = payload.get("pageConfig", {})
    allowed_course_ids = [
        clean_text(item)
        for item in page_config.get("allowed_course_ids", [])
        if clean_text(item)
    ]
    if not allowed_course_ids:
        allowed_course_ids = sorted({clean_text(offer.get("courseId")) for offer in payload.get("offers", []) if clean_text(offer.get("courseId"))})
    grouped_dates: dict[str, dict[str, Any]] = {}
    for offer in payload.get("offers", []):
        date_group = grouped_dates.setdefault(
            offer["date"],
            {"date": offer["date"], "displayDate": offer["displayDate"], "startTimes": {}},
        )
        start_group = date_group["startTimes"].setdefault(
            offer["startTime"],
            {"startTime": offer["startTime"], "displayStartTime": offer["displayStartTime"], "courses": []},
        )
        start_group["courses"].append(offer)

    dates = []
    for date_group in grouped_dates.values():
        start_times = []
        for start_group in date_group["startTimes"].values():
            start_group["courses"].sort(
                key=lambda item: (
                    allowed_course_ids.index(item["courseId"]) if item["courseId"] in allowed_course_ids else 999,
                    item["courseName"],
                )
            )
            start_times.append(start_group)
        start_times.sort(key=lambda item: item["startTime"])
        dates.append({**date_group, "startTimes": start_times})
    dates.sort(key=lambda item: item["date"])
    return dates


def apply_final_live_availability_guard(payload: dict[str, Any]) -> dict[str, Any]:
    live_blocks = current_public_live_block_index()
    kept: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    for offer in payload.get("offers", []):
        if clean_text(offer.get("offerType")) == "seated_class":
            kept.append(offer)
            continue
        block_id = clean_text(offer.get("availabilityBlockId"))
        block = live_blocks.get(block_id)
        start = parse_dt(f"{offer.get('date')}T{offer.get('startTime')}")
        consumption_end = parse_dt(f"{offer.get('date')}T{offer.get('schedulerConsumptionEnd')}")
        reason = ""
        if not block:
            reason = "source_availability_block_missing_from_current_live_snapshot"
        elif not start or not consumption_end:
            reason = "invalid_offer_consumption_window"
        elif start < block["start"] or consumption_end > block["end"]:
            reason = "offer_consumption_window_no_longer_fits_current_live_block"
        if reason:
            suppressed.append({
                "date": offer.get("date"),
                "startTime": offer.get("startTime"),
                "courseId": offer.get("courseId"),
                "courseName": offer.get("courseName"),
                "sourceAvailabilityBlockId": block_id,
                "availabilityWindow": offer.get("availabilityWindow"),
                "reason": reason,
            })
        else:
            kept.append(offer)

    if not suppressed:
        payload.setdefault("liveAvailabilityGuard", {})
        payload["liveAvailabilityGuard"].update({
            "enabled": True,
            "renderedDates": sorted({offer["date"] for offer in kept}),
            "sourceBlocksUsed": sorted({clean_text(offer.get("availabilityBlockId")) for offer in kept if clean_text(offer.get("availabilityBlockId"))}),
            "suppressedStaleOrOrphanedOffers": [],
            "suppressedDates": [],
        })
        return payload

    payload = {**payload, "offers": kept}
    payload["dates"] = rebuild_payload_dates(payload)
    counts = {**payload["counts"]}
    counts["publicSelectableOfferCount"] = len(kept)
    counts["publicSelectableDateCount"] = len(payload["dates"])
    counts["publicSelectableStartTimeCount"] = sum(len(item["startTimes"]) for item in payload["dates"])
    counts["suppressedStaleOrOrphanedOfferCount"] = len(suppressed)
    payload["counts"] = counts
    payload["liveAvailabilityGuard"] = {
        **payload.get("liveAvailabilityGuard", {}),
        "enabled": True,
        "renderedDates": sorted({offer["date"] for offer in kept}),
        "sourceBlocksUsed": sorted({clean_text(offer.get("availabilityBlockId")) for offer in kept if clean_text(offer.get("availabilityBlockId"))}),
        "suppressedStaleOrOrphanedOffers": suppressed[:1000],
        "suppressedDates": sorted({str(item["date"]) for item in suppressed if item.get("date")}),
    }
    payload["proof"] = {
        **payload.get("proof", {}),
        "visibleStartLabels": sorted({offer["displayStartTime"] for offer in kept})[:20],
        "availabilityWindowsThatGeneratedOffers": sorted({offer["availabilityWindow"] for offer in kept}),
    }
    return payload


def window_datetimes(window: dict[str, Any]) -> tuple[datetime, datetime]:
    start, end, _source = generate_dynamic_offers.availability_window_datetimes(window)
    if not start or not end or end <= start:
        raise BlockSelectorInputError(f"Invalid availability window datetime shape: {window}")
    return start, end


def public_location_allowed(location: str, policy: dict[str, Any]) -> bool:
    return is_public_class_location(location)


def public_policy_reasons(
    start: datetime,
    course_id: str,
    course_family: str,
    policy: dict[str, Any],
    pilot_allowed_course_ids: set[str] | None = None,
) -> list[str]:
    reasons: list[str] = []
    enabled_ids = {str(item) for item in policy.get("enabled_course_ids", [])}
    disabled_ids = {str(item) for item in policy.get("disabled_course_ids", [])}
    enabled_families = {str(item) for item in policy.get("enabled_course_families", [])}
    disabled_families = {str(item) for item in policy.get("disabled_course_families", [])}
    pilot_allowed = course_id in (pilot_allowed_course_ids or set())
    explicit = course_id in enabled_ids or pilot_allowed
    if course_id in disabled_ids:
        reasons.append("course_id_disabled_by_public_offer_policy")
    if enabled_ids and course_id not in enabled_ids and not pilot_allowed:
        reasons.append("course_id_not_enabled_by_public_offer_policy")
    if disabled_families and course_family in disabled_families and not explicit:
        reasons.append("course_family_disabled_by_public_offer_policy")
    if enabled_families and course_family not in enabled_families and not explicit:
        reasons.append("course_family_not_enabled_by_public_offer_policy")
    allowed_minutes = {str(item) for item in policy.get("allowed_start_minutes", [])}
    if allowed_minutes and start.strftime("%M") not in allowed_minutes:
        reasons.append("start_minute_not_allowed_by_public_offer_policy")
    window = policy.get("dynamic_public_start_time_window", {})
    if isinstance(window, dict) and window.get("enabled") is True:
        earliest = time.fromisoformat(str(window.get("earliest_start")))
        latest = time.fromisoformat(str(window.get("latest_start")))
        current = start.time().replace(second=0, microsecond=0)
        if current < earliest or current > latest:
            reasons.append("outside_public_dynamic_hours")
    minimum_lead_hours = int(policy.get("minimum_lead_hours") or 0)
    if minimum_lead_hours and start < datetime.combine(AS_OF_DATE, time.min) + timedelta(hours=minimum_lead_hours):
        reasons.append("inside_minimum_lead_time")
    maximum_days_out = int(policy.get("maximum_days_out") or 0)
    if maximum_days_out and start.date() > AS_OF_DATE + timedelta(days=maximum_days_out):
        reasons.append("outside_maximum_days_out")
    return reasons


def candidate_starts(start: datetime, end: datetime) -> list[datetime]:
    values: list[datetime] = []
    cursor = start
    while cursor < end:
        values.append(cursor)
        cursor += timedelta(minutes=START_STEP_MINUTES)
    return values


def has_required_cert(person: dict[str, Any], course: dict[str, Any]) -> bool:
    requirements = {
        str(code).strip()
        for code in course.get("required_instructor_certifications", [])
        if clean_text(code) and str(code).strip() != UNKNOWN
    }
    if not requirements:
        return False
    return bool(generate_dynamic_offers.person_certification_codes(person).intersection(requirements))


def session_course_id(session: dict[str, Any]) -> str:
    course = session.get("course")
    if isinstance(course, dict):
        for key in ("course_id", "course_number", "courseId"):
            value = clean_text(course.get(key))
            if value:
                return value
    for key in ("course_id", "course_number", "courseId"):
        value = clean_text(session.get(key))
        if value:
            return value
    return ""


def occupancy_duration_overrides(payload: Any, course_rules: dict[str, dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("sessions"), list):
        return {}
    overrides: dict[tuple[str, str], dict[str, Any]] = {}
    for session in payload["sessions"]:
        if not isinstance(session, dict):
            continue
        start = parse_dt(session.get("start_at") or session.get("start") or session.get("start_datetime"))
        end = parse_dt(session.get("end_at") or session.get("end") or session.get("end_datetime"))
        course_id = session_course_id(session)
        rule = course_rules.get(course_id)
        if not start or not rule:
            continue
        if end and end > start:
            continue
        overrides[(start.isoformat(), course_id)] = {
            "end": start + timedelta(minutes=int(rule["scheduler_consumption_minutes"])),
            "course_id": course_id,
            "duration_rule_key": course_id,
            "duration_rule_source": str(COURSE_RULES_PATH),
            "duration_minutes": rule["duration_minutes"],
            "setup_buffer_minutes": rule["setup_buffer_minutes"],
            "cleanup_buffer_minutes": rule["cleanup_buffer_minutes"],
            "scheduler_consumption_minutes": rule["scheduler_consumption_minutes"],
            "duration_resolution": "course_id",
        }
    return overrides


def apply_occupancy_duration_rules(
    occupancy: list[dict[str, Any]],
    payload: Any,
    course_rules: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    overrides = occupancy_duration_overrides(payload, course_rules)
    if not overrides:
        return occupancy
    for block in occupancy:
        start = block.get("start")
        if not start:
            continue
        course_id = ""
        title = clean_text(block.get("course_title"))
        for candidate_id, rule in course_rules.items():
            if title == clean_text(rule.get("clean_course_name")):
                course_id = candidate_id
                break
        override = overrides.get((start.isoformat(), course_id))
        if not override:
            # Some imported titles include encoding artifacts. Match by start and
            # let the original session course id supply the rule when available.
            matching = [item for (start_key, _course_id), item in overrides.items() if start_key == start.isoformat()]
            override = matching[0] if len(matching) == 1 else None
        if override and (not block.get("end") or block["end"] <= start):
            block["end"] = override["end"]
            block["course_id"] = override["course_id"]
            block["duration_rule_key"] = override["duration_rule_key"]
            block["duration_rule_source"] = override["duration_rule_source"]
            block["duration_resolution"] = override["duration_resolution"]
            block["scheduler_consumption_minutes"] = override["scheduler_consumption_minutes"]
    return occupancy


def normalize_live_calendar_block_occupancy(payload: Any) -> list[dict[str, Any]]:
    """Treat authoritative blocked live-calendar windows as hard occupancy."""

    out: list[dict[str, Any]] = []
    for index, block in enumerate(generate_dynamic_offers.availability_windows(payload), start=1):
        if block.get("availability_status") != "blocked":
            continue
        start, end, _source = generate_dynamic_offers.availability_window_datetimes(block)
        if not start or not end:
            raise BlockSelectorInputError(
                "Blocked live-calendar occupancy has an invalid interval: "
                f"source_event_id={clean_text(block.get('source_event_id') or f'blocked[{index}]')}"
            )
        instructor = clean_text(block.get("instructor_name") or UNKNOWN)
        location = clean_text(block.get("location_name") or block.get("source_location") or UNKNOWN)
        if instructor == UNKNOWN and location == UNKNOWN:
            raise BlockSelectorInputError(
                "Blocked live-calendar occupancy is missing both instructor and location: "
                f"source_event_id={clean_text(block.get('source_event_id') or f'blocked[{index}]')}"
            )
        out.append({
            "start": start,
            "end": end,
            "location": location,
            "instructor": instructor,
            "course_title": clean_text(block.get("summary") or block.get("source_type") or "Authoritative calendar block"),
            "source_file": f"live_availability_snapshot.blocked[{index}]",
            "source_calendar_id": clean_text(block.get("source_calendar_id") or UNKNOWN),
            "source_event_id": clean_text(block.get("source_event_id") or UNKNOWN),
        })
    return out


def build_occupancy(loaded: dict[str, Any], course_rules: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    location_resource_map = loaded.get("location_resource_map")
    sessions_current = apply_occupancy_duration_rules(
        generate_dynamic_offers.normalize_occupancy(loaded.get("sessions_current"), "data/sessions_current.json"),
        loaded.get("sessions_current"),
        course_rules,
    )
    schedule_future = apply_occupancy_duration_rules(
        generate_dynamic_offers.normalize_occupancy(loaded.get("schedule_future"), "docs/data/schedule_future.json"),
        loaded.get("schedule_future"),
        course_rules,
    )
    calendar_blocks = normalize_live_calendar_block_occupancy(loaded.get("live_availability_snapshot"))
    occupancy = sessions_current + schedule_future + calendar_blocks
    for block in occupancy:
        canonical, resource, normalized = generate_dynamic_offers.normalize_location_resource(
            block.get("location"),
            block.get("location"),
            location_resource_map,
        )
        if normalized:
            block["raw_location"] = block.get("location")
            block["location"] = canonical
            block["resource"] = resource
            block["location_resolution"] = "location_resource_map"
    return occupancy


def public_direct_bookable_session(session: dict[str, Any]) -> bool:
    return session.get("public_direct_booking") is not False and clean_text(session.get("registration_status") or "open").lower() not in {"closed", "full"}


def seated_class_selector_offers(
    *,
    schedule_future_payload: Any,
    selected_courses: list[dict[str, Any]],
    selected_course_ids: set[str],
    course_rules: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(schedule_future_payload, dict) or not isinstance(schedule_future_payload.get("sessions"), list):
        return []
    courses_by_id = {str(course.get("course_id")): course for course in selected_courses}
    offers: list[dict[str, Any]] = []
    for session in schedule_future_payload["sessions"]:
        if not isinstance(session, dict):
            continue
        course_id = clean_text(session.get("course_id"))
        if course_id not in selected_course_ids or not public_direct_bookable_session(session):
            continue
        start = parse_dt(session.get("start_at"))
        end = parse_dt(session.get("end_at"))
        if not start or not end:
            continue
        course = courses_by_id.get(course_id, {})
        rule = course_rules.get(course_id, {})
        scheduler_minutes = int(rule.get("scheduler_consumption_minutes") or max(1, int((end - start).total_seconds() // 60)))
        consumption_end = start + timedelta(minutes=scheduler_minutes)
        registration_url = clean_text(session.get("registration_url"))
        if not registration_url:
            continue
        offers.append({
            "date": start.date().isoformat(),
            "displayDate": display_date(start.date().isoformat()),
            "startTime": start.strftime("%H:%M"),
            "displayStartTime": display_time(start),
            "courseId": course_id,
            "courseName": clean_text(session.get("course_name") or course.get("clean_course_name") or course.get("short_title") or course_id),
            "courseFamily": clean_text(course.get("course_family") or course.get("family") or session.get("mapped_family") or ""),
            "certifyingBody": clean_text(course.get("brand") or course.get("provider") or session.get("certifying_body") or UNKNOWN),
            "deliveryMode": clean_text(course.get("blended_classroom_skills") or course.get("delivery_type") or session.get("delivery_mode") or UNKNOWN),
            "durationMinutes": int(rule.get("duration_minutes") or max(1, int((end - start).total_seconds() // 60))),
            "setupBufferMinutes": int(rule.get("setup_buffer_minutes") or 0),
            "cleanupBufferMinutes": int(rule.get("cleanup_buffer_minutes") or 0),
            "schedulerConsumptionMinutes": scheduler_minutes,
            "schedulerConsumptionEnd": consumption_end.strftime("%H:%M"),
            "appointmentDayId": None,
            "matchedContainerId": None,
            "appointmentUrl": registration_url,
            "registrationUrl": registration_url,
            "availabilityBlockId": f"seated:{clean_text(session.get('session_id'))}",
            "availabilityWindow": "seated-class",
            "sourceAvailabilityBlock": {
                "source": "docs/data/schedule_future.json",
                "sessionId": clean_text(session.get("session_id")),
                "registrationStatus": clean_text(session.get("registration_status") or "open"),
                "publicDirectBooking": session.get("public_direct_booking") is not False,
            },
            "instructor": clean_text(session.get("lead_instructor_name") or UNKNOWN),
            "location": clean_text(session.get("location_name") or session.get("location_display") or UNKNOWN),
            "offerType": "seated_class",
            "publicSelectable": True,
        })
    return offers


def find_url(
    window: dict[str, Any],
    start: datetime,
    course_id: str,
    containers: list[dict[str, Any]],
    location_resource_map: Any,
) -> tuple[int | None, str | None, str | None, str | None]:
    seed = {
        "date": start.date().isoformat(),
        "start_time": start.strftime("%H:%M"),
        "appointment_display_start": start.isoformat(),
        "course_id": course_id,
        "instructor_display_name": window.get("instructor_name"),
        "location": window.get("location_name"),
    }
    container, appointment_day_id, reason = matching_container(seed, containers, start.date(), location_resource_map)
    if not container or appointment_day_id is None:
        return appointment_day_id, None, None, reason
    return (
        appointment_day_id,
        str(container.get("container_id") or UNKNOWN),
        build_registration_url(appointment_day_id, start.time(), course_id),
        None,
    )


def build_bls_pilot_schedule() -> dict[str, Any]:
    return build_block_schedule_page(load_block_schedule_page_configs()["bls"])


def load_block_schedule_page_configs() -> dict[str, dict[str, Any]]:
    payload = read_required_json(BLOCK_SCHEDULE_PAGES_PATH)
    pages = payload.get("pages") if isinstance(payload, dict) else None
    if not isinstance(pages, dict):
        raise BlockSelectorInputError(f"{BLOCK_SCHEDULE_PAGES_PATH} must contain a pages object")
    normalized: dict[str, dict[str, Any]] = {}
    for key, page in pages.items():
        if not isinstance(page, dict):
            continue
        page_key = normalize_key(page.get("page_key") or key)
        course_options = page.get("course_options")
        if not page_key or not isinstance(course_options, list) or not course_options:
            raise BlockSelectorInputError(f"Block schedule page {key} must define course_options")
        allowed_course_ids = []
        for option in course_options:
            if not isinstance(option, dict) or not clean_text(option.get("course_id")):
                raise BlockSelectorInputError(f"Block schedule page {key} has an invalid course option")
            allowed_course_ids.append(clean_text(option["course_id"]))
        normalized[page_key] = {
            **page,
            "page_key": page_key,
            "allowed_course_ids": allowed_course_ids,
        }
    return normalized


def build_block_schedule_page(page_config: dict[str, Any]) -> dict[str, Any]:
    page_key = normalize_key(page_config.get("page_key"))
    if not page_key:
        raise BlockSelectorInputError("Block schedule page config is missing page_key")
    allowed_course_ids = [clean_text(item) for item in page_config.get("allowed_course_ids", []) if clean_text(item)]
    if not allowed_course_ids:
        raise BlockSelectorInputError(f"Block schedule page {page_key} has no allowed course IDs")

    live_availability_snapshot = require_current_live_availability_snapshot()
    loaded = {
        "live_availability_snapshot": live_availability_snapshot,
        "location_resource_map": read_required_json(LOCATION_RESOURCE_MAP_PATH),
        "course_catalog": read_required_json(COURSE_CATALOG_PATH),
        "people_catalog": read_required_json(PEOPLE_CATALOG_PATH),
        "appointment_containers": read_required_json(APPOINTMENT_CONTAINERS_PATH),
        "sessions_current": read_required_json(SESSIONS_CURRENT_PATH),
        "schedule_future": read_required_json(SCHEDULE_FUTURE_PATH),
    }
    course_rules = course_rules_by_id(read_required_json(COURSE_RULES_PATH))
    course_catalog = courses_by_id(loaded["course_catalog"])
    people = people_lookup(loaded["people_catalog"])
    public_location_policy = read_required_json(PUBLIC_LOCATION_POLICY_PATH)
    public_offer_policy = read_required_json(PUBLIC_OFFER_POLICY_PATH)
    containers = active_containers(loaded["appointment_containers"])
    if not containers:
        raise BlockSelectorInputError(f"{APPOINTMENT_CONTAINERS_PATH} has no active appointment containers")
    windows, availability_stats = selected_public_page_live_windows(live_availability_snapshot, loaded["location_resource_map"])
    occupancy = build_occupancy(loaded, course_rules)
    occupancy_index = generate_dynamic_offers.occupancy_by_date(occupancy)

    selected_courses: list[dict[str, Any]] = []
    config_course_options = {
        clean_text(option.get("course_id")): option
        for option in page_config.get("course_options", [])
        if isinstance(option, dict) and clean_text(option.get("course_id"))
    }
    for course_id in allowed_course_ids:
        if course_id not in course_rules:
            raise BlockSelectorInputError(f"Block schedule page {page_key} course {course_id} is missing from {COURSE_RULES_PATH}")
        if course_id not in course_catalog:
            raise BlockSelectorInputError(f"Block schedule page {page_key} course {course_id} is missing from {COURSE_CATALOG_PATH}")
        selected_courses.append({
            **course_catalog[course_id],
            **course_rules[course_id],
            "schedule_page_option": config_course_options.get(course_id, {}),
        })

    rejections: list[dict[str, Any]] = []
    blocks_seen = 0
    public_blocks_seen = 0
    offers: list[dict[str, Any]] = []
    for window_index, window in enumerate(sorted(windows, key=lambda item: (str(item.get("date")), str(item.get("start_time")))), start=1):
        blocks_seen += 1
        window_start, window_end = window_datetimes(window)
        location = clean_text(window.get("location_name") or UNKNOWN)
        instructor_name = clean_text(window.get("instructor_name") or UNKNOWN)
        person = people.get(normalize_key(window.get("person_id"))) or people.get(normalize_key(instructor_name))
        allowed_families = {str(item).strip() for item in window.get("allowed_course_families", [])}
        block_public_ok = public_location_allowed(location, public_location_policy)
        if block_public_ok:
            public_blocks_seen += 1
        for start in candidate_starts(window_start, window_end):
            for course in selected_courses:
                course_id = str(course["course_id"])
                course_family = str(course.get("course_family") or course.get("family") or "")
                consumption_end = start + timedelta(minutes=int(course["scheduler_consumption_minutes"]))
                context = {
                    "date": start.date().isoformat(),
                    "startTime": start.strftime("%H:%M"),
                    "displayStartTime": display_time(start),
                    "courseId": course_id,
                    "courseName": clean_text(
                        course.get("schedule_page_option", {}).get("display_label")
                        or course.get("clean_course_name")
                        or course.get("short_title")
                        or course_id
                    ),
                    "availabilityBlockId": clean_text(window.get("source_availability_window") or f"availability[{window_index}]"),
                    "availabilityWindow": f"{window_start.strftime('%H:%M')}-{window_end.strftime('%H:%M')}",
                    "sourceAvailabilityBlock": window.get("source_live_availability_block", {}),
                    "instructor": instructor_name,
                    "location": location,
                }
                reasons: list[str] = []
                if course.get("appointment_eligible") is not True or course.get("appointment_allowed") is not True:
                    reasons.append("course_not_appointment_eligible")
                if allowed_families and course_family not in allowed_families:
                    reasons.append("course_family_not_allowed_by_availability")
                if not person:
                    reasons.append("missing_scheduler_enabled_person")
                elif not has_required_cert(person, course):
                    reasons.append("instructor_lacks_required_certification")
                if consumption_end > window_end:
                    reasons.append("does_not_fit_inside_availability_after_duration_and_buffers")
                if not block_public_ok:
                    reasons.append("location_not_allowed_by_public_policy")
                conflict, conflict_reason = generate_dynamic_offers.has_conflict(
                    start,
                    consumption_end,
                    generate_dynamic_offers.occupancy_candidates(occupancy_index, start, consumption_end),
                    location,
                    person or {},
                )
                if conflict:
                    reasons.append("conflicts_with_existing_enrollware_occupancy")
                appointment_day_id, container_id, url, url_blocker = find_url(
                    window,
                    start,
                    course_id,
                    containers,
                    loaded["location_resource_map"],
                )
                if url_blocker:
                    reasons.append(url_blocker)
                public_reasons = public_policy_reasons(
                    start,
                    course_id,
                    course_family,
                    public_offer_policy,
                    set(allowed_course_ids),
                )
                if reasons or public_reasons:
                    rejections.append({
                        **context,
                        "appointmentDayId": appointment_day_id,
                        "reasons": reasons + public_reasons,
                        "conflictReason": conflict_reason,
                    })
                    continue
                offers.append({
                    **context,
                    "displayDate": display_date(start.date().isoformat()),
                    "courseFamily": course_family,
                    "certifyingBody": clean_text(course.get("brand") or course.get("provider") or page_config.get("certifying_body") or UNKNOWN),
                    "deliveryMode": clean_text(course.get("blended_classroom_skills") or course.get("delivery_type") or UNKNOWN),
                    "durationMinutes": course["duration_minutes"],
                    "setupBufferMinutes": course["setup_buffer_minutes"],
                    "cleanupBufferMinutes": course["cleanup_buffer_minutes"],
                    "schedulerConsumptionMinutes": course["scheduler_consumption_minutes"],
                    "schedulerConsumptionEnd": consumption_end.strftime("%H:%M"),
                    "appointmentDayId": appointment_day_id,
                    "matchedContainerId": container_id,
                    "appointmentUrl": url,
                    "publicSelectable": True,
                })

    if page_config.get("include_seated_classes") is True:
        offers.extend(
            seated_class_selector_offers(
                schedule_future_payload=loaded.get("schedule_future"),
                selected_courses=selected_courses,
                selected_course_ids=set(allowed_course_ids),
                course_rules=course_rules,
            )
        )

    grouped_dates: dict[str, dict[str, Any]] = {}
    for offer in offers:
        date_group = grouped_dates.setdefault(
            offer["date"],
            {"date": offer["date"], "displayDate": offer["displayDate"], "startTimes": {}},
        )
        start_group = date_group["startTimes"].setdefault(
            offer["startTime"],
            {"startTime": offer["startTime"], "displayStartTime": offer["displayStartTime"], "courses": []},
        )
        start_group["courses"].append(offer)

    dates = []
    for date_group in grouped_dates.values():
        start_times = []
        for start_group in date_group["startTimes"].values():
            start_group["courses"].sort(key=lambda item: (allowed_course_ids.index(item["courseId"]) if item["courseId"] in allowed_course_ids else 999, item["courseName"]))
            start_times.append(start_group)
        start_times.sort(key=lambda item: item["startTime"])
        dates.append({**date_group, "startTimes": start_times})
    dates.sort(key=lambda item: item["date"])

    rejected_counts = Counter(reason for item in rejections for reason in item["reasons"])
    block_windows = {offer["availabilityWindow"] for offer in offers}
    source_generated_at = live_snapshot_generated_at(live_availability_snapshot)
    payload = {
        "generatedAt": source_generated_at.isoformat() if source_generated_at else AS_OF_DATE.isoformat(),
        "pilot": "block_start_time_selector",
        "pageKey": page_key,
        "pageConfig": page_config,
        "readOnlyDataBuild": True,
        "publicPage": clean_text(page_config.get("output_path") or ""),
        "asOfDate": AS_OF_DATE.isoformat(),
        "availability_source_used": availability_stats["availability_source_used"],
        "availability_fallback_used": availability_stats["availability_fallback_used"],
        "availabilitySource": availability_stats,
        "whole_block_presented_as_class": False,
        "horizonDays": int(public_offer_policy.get("maximum_days_out") or 0),
        "minimumLeadHours": int(public_offer_policy.get("minimum_lead_hours") or 0),
        "inputFiles": {
            "liveAvailabilitySnapshot": str(LIVE_AVAILABILITY_PATH),
            "courseConsumptionRules": str(COURSE_RULES_PATH),
            "courseCatalog": str(COURSE_CATALOG_PATH),
            "peopleCatalog": str(PEOPLE_CATALOG_PATH),
            "publicOfferPolicy": str(PUBLIC_OFFER_POLICY_PATH),
            "publicLocationPolicy": str(PUBLIC_LOCATION_POLICY_PATH),
            "appointmentContainers": str(APPOINTMENT_CONTAINERS_PATH),
            "sessionsCurrent": str(SESSIONS_CURRENT_PATH),
            "scheduleFuture": str(SCHEDULE_FUTURE_PATH),
            "blockSchedulePages": str(BLOCK_SCHEDULE_PAGES_PATH),
        },
        "counts": {
            "availabilityBlocksFound": availability_stats["available_blocks_read"],
            "availabilityBlocksEvaluated": blocks_seen,
            "publicLocationBlocksEvaluated": public_blocks_seen,
            "publicSelectableOfferCount": len(offers),
            "publicSelectableDateCount": len(dates),
            "publicSelectableStartTimeCount": sum(len(item["startTimes"]) for item in dates),
            "rejectedOfferCount": len(rejections),
            "suppressedStaleOrOrphanedOfferCount": 0,
            "wholeBlockPresentedAsClass": False,
        },
        "liveAvailabilityGuard": {
            "enabled": True,
            "liveAvailabilitySnapshot": str(LIVE_AVAILABILITY_PATH),
            "renderedDates": sorted(grouped_dates),
            "sourceBlocksUsed": sorted(
                {
                    offer["availabilityBlockId"]
                    for offer in offers
                    if clean_text(offer.get("availabilityBlockId"))
                }
            ),
            "approvedInverseSourceCalendarIds": availability_stats.get("approved_inverse_source_calendar_ids", []),
            "approvedInverseBlocksUsed": availability_stats.get("approved_inverse_blocks_used", []),
            "approvedInverseBlocksUsedCount": availability_stats.get("approved_inverse_blocks_used_count", 0),
            "unapprovedInverseBlocksSuppressedCount": availability_stats.get("unapproved_inverse_blocks_suppressed_count", 0),
            "suppressedAvailableBlocks": availability_stats.get("suppressed_available_blocks", []),
            "suppressedAvailableBlockDates": availability_stats.get("suppressed_available_block_dates", []),
            "suppressedStaleOrOrphanedOffers": [],
            "suppressedDates": [],
        },
        "proof": {
            "whole_block_presented_as_class": False,
            "availability_windows_are_not_rendered_as_class_times": True,
            "availabilityWindowsThatGeneratedOffers": sorted(block_windows),
            "visibleStartLabels": sorted({offer["displayStartTime"] for offer in offers})[:20],
        },
        "dates": dates,
        "offers": offers,
        "rejectedCourseStartTimes": rejections[:500],
        "rejectionReasonCounts": dict(rejected_counts.most_common()),
    }
    return payload
