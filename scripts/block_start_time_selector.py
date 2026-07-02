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


AUDIT_DIR = ROOT / "data" / "audit"
COURSE_RULES_PATH = ROOT / "data" / "inventory" / "course_consumption_rules.json"
COURSE_CATALOG_PATH = ROOT / "data" / "config" / "course_catalog.json"
PEOPLE_CATALOG_PATH = ROOT / "data" / "config" / "people_catalog.json"
LOCATION_RESOURCE_MAP_PATH = ROOT / "data" / "config" / "location_resource_map.json"
APPOINTMENT_CONTAINERS_PATH = ROOT / "data" / "inventory" / "appointment_containers.json"
PUBLIC_LOCATION_POLICY_PATH = ROOT / "data" / "config" / "public_location_policy.json"
PUBLIC_OFFER_POLICY_PATH = ROOT / "data" / "config" / "public_offer_policy.json"
LIVE_AVAILABILITY_PATH = AUDIT_DIR / "live_availability_snapshot_preview.json"
LEGACY_AVAILABILITY_PATH = ROOT / "data" / "inventory" / "instructor_availability.json"
SESSIONS_CURRENT_PATH = ROOT / "data" / "sessions_current.json"
SCHEDULE_FUTURE_PATH = ROOT / "docs" / "data" / "schedule_future.json"

BLS_PILOT_COURSE_IDS = ("209806", "359474", "210549")
START_STEP_MINUTES = 30
AS_OF_DATE = date(2026, 7, 2)
UNKNOWN = "UNKNOWN"


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


def window_datetimes(window: dict[str, Any]) -> tuple[datetime, datetime]:
    start, end, _source = generate_dynamic_offers.availability_window_datetimes(window)
    if not start or not end or end <= start:
        raise BlockSelectorInputError(f"Invalid availability window datetime shape: {window}")
    return start, end


def public_location_allowed(location: str, policy: dict[str, Any]) -> bool:
    exact = {clean_text(item) for item in policy.get("public_location_exact", [])}
    prefixes = tuple(clean_text(item) for item in policy.get("public_location_prefixes", []))
    if location in exact:
        return True
    if prefixes and location.startswith(prefixes):
        return True
    return "shipyard" in normalize_key(location)


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


def build_occupancy(loaded: dict[str, Any]) -> list[dict[str, Any]]:
    return (
        generate_dynamic_offers.normalize_occupancy(loaded.get("sessions_current"), "data/sessions_current.json")
        + generate_dynamic_offers.normalize_occupancy(loaded.get("schedule_future"), "docs/data/schedule_future.json")
    )


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
    loaded = {
        "live_availability_snapshot": read_required_json(LIVE_AVAILABILITY_PATH) if LIVE_AVAILABILITY_PATH.exists() else None,
        "instructor_availability": read_required_json(LEGACY_AVAILABILITY_PATH),
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
    windows, availability_stats = load_selected_windows(loaded)
    occupancy = build_occupancy(loaded)
    occupancy_index = generate_dynamic_offers.occupancy_by_date(occupancy)

    selected_courses: list[dict[str, Any]] = []
    for course_id in BLS_PILOT_COURSE_IDS:
        if course_id not in course_rules:
            raise BlockSelectorInputError(f"BLS pilot course {course_id} is missing from {COURSE_RULES_PATH}")
        if course_id not in course_catalog:
            raise BlockSelectorInputError(f"BLS pilot course {course_id} is missing from {COURSE_CATALOG_PATH}")
        selected_courses.append({**course_catalog[course_id], **course_rules[course_id]})

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
                    "courseName": clean_text(course.get("clean_course_name") or course.get("short_title") or course_id),
                    "availabilityBlockId": clean_text(window.get("source_availability_window") or f"availability[{window_index}]"),
                    "availabilityWindow": f"{window_start.strftime('%H:%M')}-{window_end.strftime('%H:%M')}",
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
                    set(BLS_PILOT_COURSE_IDS),
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
            start_group["courses"].sort(key=lambda item: (item["courseId"] != "209806", item["courseName"]))
            start_times.append(start_group)
        start_times.sort(key=lambda item: item["startTime"])
        dates.append({**date_group, "startTimes": start_times})
    dates.sort(key=lambda item: item["date"])

    rejected_counts = Counter(reason for item in rejections for reason in item["reasons"])
    block_windows = {offer["availabilityWindow"] for offer in offers}
    payload = {
        "generatedAt": datetime.now().astimezone().isoformat(),
        "pilot": "bls_block_start_time_selector",
        "readOnlyDataBuild": True,
        "publicPage": "docs/bls-schedule.html",
        "asOfDate": AS_OF_DATE.isoformat(),
        "availability_source_used": availability_stats["availability_source_used"],
        "availability_fallback_used": availability_stats["availability_fallback_used"],
        "availabilitySource": availability_stats,
        "whole_block_presented_as_class": False,
        "horizonDays": int(public_offer_policy.get("maximum_days_out") or 0),
        "minimumLeadHours": int(public_offer_policy.get("minimum_lead_hours") or 0),
        "inputFiles": {
            "liveAvailabilitySnapshot": str(LIVE_AVAILABILITY_PATH),
            "legacyAvailabilityFallback": str(LEGACY_AVAILABILITY_PATH),
            "courseConsumptionRules": str(COURSE_RULES_PATH),
            "courseCatalog": str(COURSE_CATALOG_PATH),
            "peopleCatalog": str(PEOPLE_CATALOG_PATH),
            "publicOfferPolicy": str(PUBLIC_OFFER_POLICY_PATH),
            "publicLocationPolicy": str(PUBLIC_LOCATION_POLICY_PATH),
            "appointmentContainers": str(APPOINTMENT_CONTAINERS_PATH),
            "sessionsCurrent": str(SESSIONS_CURRENT_PATH),
            "scheduleFuture": str(SCHEDULE_FUTURE_PATH),
        },
        "counts": {
            "availabilityBlocksFound": availability_stats["available_blocks_read"],
            "availabilityBlocksEvaluated": blocks_seen,
            "publicLocationBlocksEvaluated": public_blocks_seen,
            "publicSelectableOfferCount": len(offers),
            "publicSelectableDateCount": len(dates),
            "publicSelectableStartTimeCount": sum(len(item["startTimes"]) for item in dates),
            "rejectedOfferCount": len(rejections),
            "wholeBlockPresentedAsClass": False,
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
