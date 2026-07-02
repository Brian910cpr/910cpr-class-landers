from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_flexible_inventory_preview import (
    TZ,
    clean_text,
    conflicts_for,
    location_key,
    normalize_availability_block,
    normalize_session,
    overlaps,
    read_availability,
    read_schedule,
)
from scripts.build_seed_appointment_url_preview import (
    active_containers,
    build_registration_url,
    matching_container,
    read_json,
)


COURSE_RULES_PATH = ROOT / "data" / "inventory" / "course_consumption_rules.json"
AVAILABILITY_PATH = ROOT / "data" / "inventory" / "instructor_availability.json"
LIVE_AVAILABILITY_PATH = ROOT / "data" / "audit" / "live_availability_snapshot_preview.json"
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
APPOINTMENT_CONTAINERS_PATH = ROOT / "data" / "inventory" / "appointment_containers.json"
LOCATION_RESOURCE_MAP_PATH = ROOT / "data" / "config" / "location_resource_map.json"
PUBLIC_LOCATION_POLICY_PATH = ROOT / "data" / "config" / "public_location_policy.json"
PUBLIC_OFFER_POLICY_PATH = ROOT / "data" / "config" / "public_offer_policy.json"
REPORT_MD_PATH = ROOT / "data" / "audit" / "block_start_time_prototype_report.md"
REPORT_JSON_PATH = ROOT / "data" / "audit" / "block_start_time_prototype_report.json"
HTML_PATH = ROOT / "debug" / "block_start_time_prototype.html"

START_STEP_MINUTES = 30
MINIMUM_LEAD_DAYS = 7
PUBLIC_HORIZON_DAYS = 180
PUBLIC_POLICY_AS_OF_DATE = date(2026, 7, 2)
SELECT_BEST_FIT = "best-fit"
SELECT_NEXT_PUBLIC_ELIGIBLE = "next-public-eligible-block"


class PrototypeInputError(RuntimeError):
    pass


def require_file(path: Path) -> None:
    if not path.exists():
        raise PrototypeInputError(f"Required real input is missing: {path}")


def load_required_json(path: Path) -> Any:
    require_file(path)
    payload, error = read_json(path)
    if error:
        raise PrototypeInputError(f"Required real input is unreadable: {path} ({error})")
    return payload


def parse_rule_minutes(value: Any, field: str, course_id: str) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise PrototypeInputError(f"Course {course_id} has non-numeric {field}: {value!r}")


def load_course_rules() -> list[dict[str, Any]]:
    payload = load_required_json(COURSE_RULES_PATH)
    defaults = payload.get("defaults", {}) if isinstance(payload, dict) else {}
    raw_rules = payload.get("rules", []) if isinstance(payload, dict) else []
    if not isinstance(raw_rules, list) or not raw_rules:
        raise PrototypeInputError(f"{COURSE_RULES_PATH} does not contain a non-empty rules list")

    rules: list[dict[str, Any]] = []
    for raw in raw_rules:
        if not isinstance(raw, dict):
            continue
        merged = {**defaults, **raw}
        course_id = clean_text(merged.get("course_id"))
        course_name = clean_text(merged.get("clean_course_name"))
        family = clean_text(merged.get("course_family"))
        if not course_id or not course_name or not family:
            raise PrototypeInputError(f"Course rule missing course_id, clean_course_name, or course_family: {raw}")
        duration = parse_rule_minutes(merged.get("duration_minutes"), "duration_minutes", course_id)
        setup = parse_rule_minutes(merged.get("setup_buffer_minutes"), "setup_buffer_minutes", course_id)
        cleanup = parse_rule_minutes(merged.get("cleanup_buffer_minutes"), "cleanup_buffer_minutes", course_id)
        minimum_reservation = parse_rule_minutes(
            merged.get("minimum_reservation_block_minutes"),
            "minimum_reservation_block_minutes",
            course_id,
        )
        total = max(duration + setup + cleanup, minimum_reservation)
        rules.append(
            {
                "courseId": course_id,
                "courseName": course_name,
                "courseFamily": family,
                "durationMinutes": duration,
                "setupBufferMinutes": setup,
                "cleanupBufferMinutes": cleanup,
                "minimumReservationBlockMinutes": minimum_reservation,
                "schedulerConsumptionMinutes": total,
                "appointmentEligible": merged.get("appointment_eligible") is True,
                "overlappingAllowed": merged.get("overlapping_allowed") is True,
                "publicPriority": int(merged.get("public_priority") or 0),
                "raw": merged,
            }
        )
    return rules


def load_real_availability() -> tuple[list[dict[str, Any]], Path]:
    require_file(AVAILABILITY_PATH)
    warnings: list[str] = []
    raw, path = read_availability(warnings)
    if warnings:
        raise PrototypeInputError("Availability load warnings are fatal for this prototype: " + "; ".join(warnings))
    if path != AVAILABILITY_PATH:
        raise PrototypeInputError(f"Expected real availability from {AVAILABILITY_PATH}, got {path}")
    blocks = [normalize_availability_block(block, index) for index, block in enumerate(raw, start=1)]
    normalized = [block for block in blocks if block and block["raw"].get("availability_status") == "available"]
    if not normalized:
        raise PrototypeInputError(f"{AVAILABILITY_PATH} has no normalized available blocks")
    return normalized, path


def parse_block_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=TZ)
    return parsed.astimezone(TZ)


def normalize_live_availability_block(block: dict[str, Any], index: int) -> dict[str, Any] | None:
    if block.get("availability_status") != "available":
        return None
    start = parse_block_dt(block.get("start_datetime"))
    end = parse_block_dt(block.get("end_datetime"))
    if not start or not end or end <= start:
        return None
    instructor = clean_text(block.get("instructor_name") or block.get("owner") or "")
    if not instructor:
        return None
    location = clean_text(block.get("location_name") or block.get("location") or "")
    return {
        "block_id": clean_text(block.get("source_event_id")) or f"live_availability_{index}",
        "instructor": instructor,
        "instructor_key": "",
        "date": start.date(),
        "start": start,
        "end": end,
        "location": location,
        "location_key": location_key(location),
        "room": clean_text(block.get("room_or_resource_name") or block.get("resource") or ""),
        "notes": "; ".join(str(reason) for reason in block.get("reasons", []) if reason),
        "source": clean_text(block.get("source_calendar_id") or block.get("source_type") or "live_availability_snapshot"),
        "allowed_course_families": [clean_text(item) for item in block.get("allowed_course_families", []) if clean_text(item)],
        "preferred_course_families": [],
        "raw": block,
    }


def load_selected_availability() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if LIVE_AVAILABILITY_PATH.exists():
        payload = load_required_json(LIVE_AVAILABILITY_PATH)
        raw_blocks = payload.get("availability_blocks", []) if isinstance(payload, dict) else []
        live_blocks = [
            normalized
            for index, block in enumerate(raw_blocks, start=1)
            if isinstance(block, dict)
            for normalized in [normalize_live_availability_block(block, index)]
            if normalized
        ]
        if live_blocks:
            return live_blocks, {
                "availability_source_used": "live_availability_snapshot",
                "availability_fallback_used": False,
                "availability_source_path": str(LIVE_AVAILABILITY_PATH),
                "available_blocks_read": len(live_blocks),
                "live_available_blocks_read": len(live_blocks),
                "legacy_available_blocks_read": 0,
                "availability_source_reason": "valid_live_available_blocks_found",
            }

    legacy_blocks, legacy_path = load_real_availability()
    return legacy_blocks, {
        "availability_source_used": "legacy_instructor_availability_fallback",
        "availability_fallback_used": True,
        "availability_source_path": str(legacy_path),
        "available_blocks_read": len(legacy_blocks),
        "live_available_blocks_read": 0,
        "legacy_available_blocks_read": len(legacy_blocks),
        "availability_source_reason": "live_snapshot_missing_or_zero_available_blocks",
    }


def load_real_sessions() -> list[dict[str, Any]]:
    require_file(SCHEDULE_PATH)
    warnings: list[str] = []
    raw = read_schedule(warnings)
    if warnings:
        raise PrototypeInputError("Schedule load warnings are fatal for this prototype: " + "; ".join(warnings))
    sessions = [normalize_session(row) for row in raw]
    return [session for session in sessions if session]


def load_real_containers_and_location_map() -> tuple[list[dict[str, Any]], Any]:
    containers_payload = load_required_json(APPOINTMENT_CONTAINERS_PATH)
    location_resource_map = load_required_json(LOCATION_RESOURCE_MAP_PATH)
    containers = active_containers(containers_payload)
    if not containers:
        raise PrototypeInputError(f"{APPOINTMENT_CONTAINERS_PATH} has no active appointment containers")
    return containers, location_resource_map


def load_public_location_policy() -> dict[str, Any]:
    payload = load_required_json(PUBLIC_LOCATION_POLICY_PATH)
    if not isinstance(payload, dict):
        raise PrototypeInputError(f"{PUBLIC_LOCATION_POLICY_PATH} must be a JSON object")
    return payload


def load_public_offer_policy() -> dict[str, Any]:
    payload = load_required_json(PUBLIC_OFFER_POLICY_PATH)
    if not isinstance(payload, dict):
        raise PrototypeInputError(f"{PUBLIC_OFFER_POLICY_PATH} must be a JSON object")
    return payload


def generate_start_times(block: dict[str, Any]) -> list[datetime]:
    cursor = block["start"]
    starts = []
    while cursor < block["end"]:
        starts.append(cursor)
        cursor += timedelta(minutes=START_STEP_MINUTES)
    return starts


def display_time(value: datetime) -> str:
    return value.strftime("%I:%M %p").lstrip("0")


def public_location_allowed(block: dict[str, Any], policy: dict[str, Any]) -> bool:
    location = block["location"]
    exact = set(policy.get("public_location_exact", []))
    prefixes = tuple(policy.get("public_location_prefixes", []))
    if location in exact:
        return True
    if prefixes and location.startswith(prefixes):
        return True
    # The location resource map treats the Shipyard office as one public office while
    # public_location_policy lists room-level Enrollware locations.
    return "shipyard" in location_key(location)


def public_offer_policy_reasons(start: datetime, course: dict[str, Any], policy: dict[str, Any], as_of: date) -> list[str]:
    reasons = []
    enabled_ids = {str(item) for item in policy.get("enabled_course_ids", [])}
    disabled_ids = {str(item) for item in policy.get("disabled_course_ids", [])}
    enabled_families = {str(item) for item in policy.get("enabled_course_families", [])}
    disabled_families = {str(item) for item in policy.get("disabled_course_families", [])}
    course_id = str(course["courseId"])
    family = str(course["courseFamily"])
    explicitly_enabled = course_id in enabled_ids
    if course_id in disabled_ids:
        reasons.append("course_id_disabled_by_public_offer_policy")
    if enabled_ids and course_id not in enabled_ids:
        reasons.append("course_id_not_enabled_by_public_offer_policy")
    if disabled_families and family in disabled_families and not explicitly_enabled:
        reasons.append("course_family_disabled_by_public_offer_policy")
    if enabled_families and family not in enabled_families and not explicitly_enabled:
        reasons.append("course_family_not_enabled_by_public_offer_policy")
    allowed_minutes = {str(item) for item in policy.get("allowed_start_minutes", [])}
    if allowed_minutes and start.strftime("%M") not in allowed_minutes:
        reasons.append("start_minute_not_allowed_by_public_offer_policy")
    window = policy.get("dynamic_public_start_time_window", {})
    if isinstance(window, dict) and window.get("enabled") is True:
        earliest = time.fromisoformat(str(window.get("earliest_start")))
        latest = time.fromisoformat(str(window.get("latest_start")))
        current = start.time().replace(second=0, microsecond=0)
        if not (earliest <= current <= latest):
            reasons.append("outside_public_dynamic_hours")
    maximum_days_out = int(policy.get("maximum_days_out", 0) or 0)
    if maximum_days_out and start.date() > as_of + timedelta(days=maximum_days_out):
        reasons.append("outside_public_offer_policy_maximum_days_out")
    return reasons


def find_appointment(block: dict[str, Any], start: datetime, course: dict[str, Any], containers: list[dict[str, Any]], location_resource_map: Any) -> tuple[int | None, str | None, str | None]:
    seed = {
        "date": start.date().isoformat(),
        "start_time": start.strftime("%H:%M"),
        "appointment_display_start": start.isoformat(),
        "course_id": course["courseId"],
        "instructor_display_name": block["instructor"],
        "location": block["location"],
    }
    container, appointment_day_id, reason = matching_container(seed, containers, start.date(), location_resource_map)
    if not container or appointment_day_id is None:
        return appointment_day_id, None, reason
    return appointment_day_id, build_registration_url(appointment_day_id, start.time(), course["courseId"]), None


def evaluate_block(
    block: dict[str, Any],
    courses: list[dict[str, Any]],
    sessions: list[dict[str, Any]],
    containers: list[dict[str, Any]],
    location_resource_map: Any,
    public_location_policy: dict[str, Any],
    public_offer_policy: dict[str, Any],
    as_of: date,
) -> dict[str, Any]:
    start_rows = []
    rejected = []
    fit_eligible_total = 0
    public_eligible_total = 0
    rejection_counter: Counter[str] = Counter()
    horizon_cutoff = as_of + timedelta(days=PUBLIC_HORIZON_DAYS)
    lead_cutoff = as_of + timedelta(days=MINIMUM_LEAD_DAYS)

    for start in generate_start_times(block):
        row_offers = []
        for course in courses:
            reasons = []
            publication_reasons = []
            consumption_end = start + timedelta(minutes=course["schedulerConsumptionMinutes"])
            if not course["appointmentEligible"]:
                reasons.append("course_not_appointment_eligible")
            if course["courseFamily"] not in block["allowed_course_families"]:
                reasons.append("course_family_not_allowed_by_availability")
            if consumption_end > block["end"]:
                reasons.append("does_not_fit_inside_availability_after_duration_and_buffers")
            candidate_for_conflict = {
                "date": start.date().isoformat(),
                "start_time": start.strftime("%H:%M"),
                "end_time": consumption_end.strftime("%H:%M"),
                "instructor": block["instructor"],
                "location": block["location"],
                "room": block["room"],
                "_start_dt": start,
                "_end_dt": consumption_end,
            }
            conflicts = [] if course["overlappingAllowed"] else conflicts_for(candidate_for_conflict, sessions)
            if conflicts:
                reasons.append("conflicts_with_existing_enrollware_occupancy")
            appointment_day_id, url, appointment_block = find_appointment(block, start, course, containers, location_resource_map)
            if appointment_block:
                reasons.append(appointment_block)
            if not public_location_allowed(block, public_location_policy):
                reasons.append("location_not_allowed_by_public_policy")

            if start.date() < lead_cutoff:
                publication_reasons.append("inside_minimum_lead_time")
            if start.date() > horizon_cutoff:
                publication_reasons.append("outside_180_day_public_horizon")
            publication_reasons.extend(public_offer_policy_reasons(start, course, public_offer_policy, as_of))

            base = {
                "startTime": start.strftime("%H:%M"),
                "displayStartTime": display_time(start),
                "courseId": course["courseId"],
                "courseName": course["courseName"],
                "courseFamily": course["courseFamily"],
                "durationMinutes": course["durationMinutes"],
                "setupBufferMinutes": course["setupBufferMinutes"],
                "cleanupBufferMinutes": course["cleanupBufferMinutes"],
                "minimumReservationBlockMinutes": course["minimumReservationBlockMinutes"],
                "schedulerConsumptionMinutes": course["schedulerConsumptionMinutes"],
                "schedulerConsumptionEnd": consumption_end.strftime("%H:%M"),
                "appointmentDayId": appointment_day_id,
                "appointmentUrl": url,
                "conflicts": conflicts,
            }
            if reasons:
                item = {**base, "reasons": reasons, "publicationGateReasons": publication_reasons}
                rejected.append(item)
                rejection_counter.update(reasons)
            else:
                fit_eligible_total += 1
                offer = {
                    **base,
                    "publicSelectable": not publication_reasons,
                    "publicationGateReasons": publication_reasons,
                }
                if publication_reasons:
                    rejection_counter.update(publication_reasons)
                else:
                    public_eligible_total += 1
                row_offers.append(offer)
        start_rows.append(
            {
                "startTime": start.strftime("%H:%M"),
                "displayStartTime": display_time(start),
                "eligibleCourses": sorted(row_offers, key=lambda item: (-course_priority(courses, item["courseId"]), item["courseName"])),
            }
        )

    return {
        "inputAvailabilityBlock": {
            "blockId": block["block_id"],
            "source": block["source"],
            "instructor": block["instructor"],
            "date": block["date"].isoformat(),
            "start": block["start"].strftime("%H:%M"),
            "end": block["end"].strftime("%H:%M"),
            "location": block["location"],
            "room": block["room"],
            "allowedCourseFamilies": block["allowed_course_families"],
            "raw": block["raw"],
        },
        "generatedStartTimes": [row["displayStartTime"] for row in start_rows],
        "startTimeRows": start_rows,
        "rejectedCourseStartTimes": rejected,
        "counts": {
            "availabilityBlocksFound": None,
            "availabilityBlocksEvaluated": 1,
            "startTimesGenerated": len(start_rows),
            "courseRulesEvaluated": len(courses),
            "courseStartTimeEvaluations": len(start_rows) * len(courses),
            "fitEligibleCourseStartTimeOffers": fit_eligible_total,
            "publicSelectableCourseStartTimeOffers": public_eligible_total,
            "rejectedCourseStartTimeOffers": len(rejected),
            "rejectionReasons": dict(sorted(rejection_counter.items())),
            "wholeBlockPresentedAsClass": False,
        },
        "proof": {
            "wholeBlockPresentedAsClass": False,
            "availableWindowLabel": f"{display_time(block['start'])}-{display_time(block['end'])}",
            "customerSelectableModel": "startTime + courseId + appointmentDayId URL",
        },
        "publicationPolicy": {
            "asOfDate": as_of.isoformat(),
            "minimumLeadDays": MINIMUM_LEAD_DAYS,
            "publicHorizonDays": PUBLIC_HORIZON_DAYS,
            "publicHorizonCutoff": horizon_cutoff.isoformat(),
            "would180DayHorizonAffectPrototype": block["date"] > horizon_cutoff,
        },
    }


def course_priority(courses: list[dict[str, Any]], course_id: str) -> int:
    for course in courses:
        if course["courseId"] == course_id:
            return course["publicPriority"]
    return 0


def select_block(
    blocks: list[dict[str, Any]],
    courses: list[dict[str, Any]],
    sessions: list[dict[str, Any]],
    containers: list[dict[str, Any]],
    location_resource_map: Any,
    policy: dict[str, Any],
    public_offer_policy: dict[str, Any],
    as_of: date,
) -> dict[str, Any]:
    evaluated = []
    for block in blocks:
        result = evaluate_block(block, courses, sessions, containers, location_resource_map, policy, public_offer_policy, as_of)
        counts = result["counts"]
        evaluated.append(
            (
                counts["publicSelectableCourseStartTimeOffers"],
                counts["fitEligibleCourseStartTimeOffers"],
                block["date"],
                block,
                result,
            )
        )
    evaluated.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    selected = evaluated[0][4]
    selected["counts"]["availabilityBlocksFound"] = len(blocks)
    selected["selectionMode"] = SELECT_BEST_FIT
    add_global_publication_policy_counts(selected, blocks, as_of)
    selected["blockSelection"] = {
        "reason": "selected block with highest public-selectable offer count, then highest fit-eligible offer count",
        "allBlocksScored": [
            {
                "blockId": item[3]["block_id"],
                "date": item[3]["date"].isoformat(),
                "window": f"{item[3]['start'].strftime('%H:%M')}-{item[3]['end'].strftime('%H:%M')}",
                "fitEligibleCourseStartTimeOffers": item[1],
                "publicSelectableCourseStartTimeOffers": item[0],
            }
            for item in evaluated
        ],
    }
    return selected


def attach_availability_metadata(result: dict[str, Any], availability_stats: dict[str, Any]) -> None:
    result["availability_source_used"] = availability_stats["availability_source_used"]
    result["availability_fallback_used"] = availability_stats["availability_fallback_used"]
    result["availabilitySource"] = availability_stats
    result["counts"]["availabilityBlocksFound"] = availability_stats["available_blocks_read"]


def block_has_occupancy(block: dict[str, Any], sessions: list[dict[str, Any]]) -> bool:
    candidate = {
        "date": block["date"].isoformat(),
        "start_time": block["start"].strftime("%H:%M"),
        "end_time": block["end"].strftime("%H:%M"),
        "instructor": block["instructor"],
        "location": block["location"],
        "room": block["room"],
        "_start_dt": block["start"],
        "_end_dt": block["end"],
    }
    return bool(conflicts_for(candidate, sessions))


def select_next_public_eligible_block(
    blocks: list[dict[str, Any]],
    courses: list[dict[str, Any]],
    sessions: list[dict[str, Any]],
    containers: list[dict[str, Any]],
    location_resource_map: Any,
    policy: dict[str, Any],
    public_offer_policy: dict[str, Any],
    as_of: date,
) -> dict[str, Any]:
    lead_cutoff = as_of + timedelta(days=MINIMUM_LEAD_DAYS)
    horizon_cutoff = as_of + timedelta(days=PUBLIC_HORIZON_DAYS)
    evaluated: list[tuple[datetime, dict[str, Any], dict[str, Any], list[str]]] = []
    for block in sorted(blocks, key=lambda item: (item["date"], item["start"])):
        criteria_failures = []
        if block["date"] < lead_cutoff:
            criteria_failures.append("inside_minimum_lead_time")
        if block["date"] > horizon_cutoff:
            criteria_failures.append("outside_180_day_public_horizon")
        if not public_location_allowed(block, policy):
            criteria_failures.append("location_not_allowed_by_public_policy")
        if block_has_occupancy(block, sessions):
            criteria_failures.append("availability_block_occupied")
        result = evaluate_block(block, courses, sessions, containers, location_resource_map, policy, public_offer_policy, as_of)
        if result["counts"]["publicSelectableCourseStartTimeOffers"] <= 0:
            criteria_failures.append("no_public_selectable_course_start_combination")
        evaluated.append((block["start"], block, result, criteria_failures))
        if not criteria_failures:
            result["counts"]["availabilityBlocksFound"] = len(blocks)
            result["selectionMode"] = SELECT_NEXT_PUBLIC_ELIGIBLE
            result["blockSelection"] = {
                "reason": "selected next block meeting public eligibility criteria",
                "criteria": [
                    "inside 180-day horizon",
                    "outside minimum lead time",
                    "public location policy passes",
                    "availability block is not occupied",
                    "at least one course/start combination is public-selectable",
                ],
                "evaluatedBlocks": block_selection_rows(evaluated),
            }
            add_global_publication_policy_counts(result, blocks, as_of)
            return result

    failure_counts = Counter(reason for _start, _block, _result, failures in evaluated for reason in failures)
    payload = {
        "generatedAt": datetime.now(TZ).isoformat(),
        "selectionMode": SELECT_NEXT_PUBLIC_ELIGIBLE,
        "overallStatus": "blocked_no_matching_public_eligible_availability_block",
        "error": "No real availability block matched --select next-public-eligible-block.",
        "counts": {
            "availabilityBlocksFound": len(blocks),
            "availabilityBlocksEvaluated": len(evaluated),
            "publicSelectableCourseStartTimeOffers": 0,
            "wholeBlockPresentedAsClass": False,
            "blockerCounts": dict(sorted(failure_counts.items())),
        },
        "criteria": [
            "inside 180-day horizon",
            "outside minimum lead time",
            "public location policy passes",
            "availability block is not occupied",
            "at least one course/start combination is public-selectable",
        ],
        "evaluatedBlocks": block_selection_rows(evaluated),
        "proof": {"wholeBlockPresentedAsClass": False},
    }
    raise PrototypeInputError(payload["error"], payload)


def block_selection_rows(evaluated: list[tuple[datetime, dict[str, Any], dict[str, Any], list[str]]]) -> list[dict[str, Any]]:
    return [
        {
            "blockId": block["block_id"],
            "date": block["date"].isoformat(),
            "window": f"{block['start'].strftime('%H:%M')}-{block['end'].strftime('%H:%M')}",
            "instructor": block["instructor"],
            "location": block["location"],
            "publicSelectableCourseStartTimeOffers": result["counts"]["publicSelectableCourseStartTimeOffers"],
            "fitEligibleCourseStartTimeOffers": result["counts"]["fitEligibleCourseStartTimeOffers"],
            "criteriaFailures": failures,
        }
        for _start, block, result, failures in evaluated
    ]


def add_global_publication_policy_counts(result: dict[str, Any], blocks: list[dict[str, Any]], as_of: date) -> None:
    horizon_cutoff = as_of + timedelta(days=PUBLIC_HORIZON_DAYS)
    outside_horizon = [block for block in blocks if block["date"] > horizon_cutoff]
    inside_lead = [block for block in blocks if block["date"] < as_of + timedelta(days=MINIMUM_LEAD_DAYS)]
    result["publicationPolicy"]["availabilityBlocksOutside180DayHorizon"] = len(outside_horizon)
    result["publicationPolicy"]["availabilityBlocksInsideMinimumLeadTime"] = len(inside_lead)
    result["publicationPolicy"]["would180DayHorizonAffectAnyRealAvailabilityBlock"] = bool(outside_horizon)


def render_markdown(result: dict[str, Any]) -> str:
    block = result["inputAvailabilityBlock"]
    lines = [
        "# Block Start Time Prototype Report",
        "",
        "Local proof only. No `docs/*.html` files were modified, nothing was deployed, and Enrollware was not called.",
        "",
        "## Real Inputs",
        "",
        f"- Course consumption rules: `{COURSE_RULES_PATH.relative_to(ROOT)}`",
        f"- Availability source used: `{result.get('availability_source_used')}`",
        f"- Availability fallback used: `{result.get('availability_fallback_used')}`",
        f"- Availability source path: `{result.get('availabilitySource', {}).get('availability_source_path')}`",
        f"- Occupancy/session data: `{SCHEDULE_PATH.relative_to(ROOT)}`",
        f"- Appointment containers: `{APPOINTMENT_CONTAINERS_PATH.relative_to(ROOT)}`",
        f"- Public offer policy: `{PUBLIC_OFFER_POLICY_PATH.relative_to(ROOT)}`",
        f"- URL builder: `scripts/build_seed_appointment_url_preview.py::build_registration_url`",
        "",
        "## Input Availability Block",
        "",
        f"- Instructor: {block['instructor']}",
        f"- Date: {block['date']}",
        f"- Window: {block['start']} to {block['end']}",
        f"- Location: {block['location']}",
        f"- Allowed course families: {', '.join(block['allowedCourseFamilies'])}",
        "",
        "## Proof",
        "",
        f"- Whole block presented as class: `{result['proof']['wholeBlockPresentedAsClass']}`",
        f"- Available window label: {result['proof']['availableWindowLabel']}",
        "- Generated offers are per start time + courseId + appointmentDayId URL.",
        "",
        "## Generated Start Times",
        "",
    ]
    for row in result["startTimeRows"]:
        lines.append(f"### {row['displayStartTime']}")
        offers = row["eligibleCourses"]
        if not offers:
            lines.append("- No fit-eligible courses at this start time.")
        for offer in offers:
            public_status = "public selectable" if offer["publicSelectable"] else "fit eligible; publication-gated"
            gate = ", ".join(offer["publicationGateReasons"]) or "none"
            lines.append(
                f"- {offer['courseName']} (`courseId={offer['courseId']}`): {public_status}; "
                f"appointmentDayId `{offer['appointmentDayId']}`; gates: {gate}; URL: `{offer['appointmentUrl']}`"
            )
        lines.append("")
    lines.extend(["## Sample Rejections", ""])
    for item in result["rejectedCourseStartTimes"][:40]:
        lines.append(
            f"- {item['displayStartTime']} / {item['courseName']} (`courseId={item['courseId']}`): "
            + ", ".join(item["reasons"])
        )
    lines.extend(["", "## Counts", ""])
    for key, value in result["counts"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## 180-Day Horizon", ""])
    policy = result["publicationPolicy"]
    lines.append(f"- As-of date: `{policy['asOfDate']}`")
    lines.append(f"- Horizon cutoff: `{policy['publicHorizonCutoff']}`")
    lines.append(f"- Would 180-day horizon affect selected block: `{policy['would180DayHorizonAffectPrototype']}`")
    lines.append(f"- Real availability blocks outside 180-day horizon: `{policy['availabilityBlocksOutside180DayHorizon']}`")
    lines.append(f"- Raw availability rows outside 180-day horizon: `{policy['rawAvailabilityBlocksOutside180DayHorizon']}`")
    lines.append(f"- Would 180-day horizon affect any real availability block: `{policy['would180DayHorizonAffectAnyRealAvailabilityBlock']}`")
    return "\n".join(lines) + "\n"


def render_html(result: dict[str, Any]) -> str:
    sections = []
    for row in result["startTimeRows"]:
        if row["eligibleCourses"]:
            items = "".join(
                f"<li><strong>{html.escape(offer['courseName'])}</strong> "
                f"<code>courseId={html.escape(offer['courseId'])}</code> "
                f"<code>appointmentDayId={html.escape(str(offer['appointmentDayId']))}</code><br>"
                f"<a href=\"{html.escape(offer['appointmentUrl'] or '')}\">{html.escape(offer['appointmentUrl'] or '')}</a><br>"
                f"<span>{'public selectable' if offer['publicSelectable'] else 'fit eligible; publication-gated'}</span></li>"
                for offer in row["eligibleCourses"]
            )
        else:
            items = "<li>No fit-eligible courses</li>"
        sections.append(f"<section><h2>{html.escape(row['displayStartTime'])}</h2><ul>{items}</ul></section>")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Block Start Time Prototype</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.45; color: #1d2733; }}
    header {{ border-bottom: 1px solid #ccd3dd; padding-bottom: 12px; margin-bottom: 20px; }}
    section {{ border-bottom: 1px solid #e2e6ec; padding: 10px 0; }}
    code {{ background: #eef2f7; padding: 2px 4px; border-radius: 4px; }}
    a {{ color: #075fa8; overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <header>
    <h1>Block Start Time Prototype</h1>
    <p>Local proof only. The whole availability window is not presented as a class.</p>
    <p><strong>Whole block presented as class:</strong> false</p>
  </header>
  {''.join(sections)}
</body>
</html>
"""


def render_blocked_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Block Start Time Prototype Report",
        "",
        "Status: blocked. No public pages were modified, nothing was deployed, and Enrollware was not called.",
        "",
        f"- Selection mode: `{payload['selectionMode']}`",
        f"- Availability source used: `{payload.get('availability_source_used')}`",
        f"- Availability fallback used: `{payload.get('availability_fallback_used')}`",
        f"- Error: {payload['error']}",
        f"- Whole block presented as class: `{payload['proof']['wholeBlockPresentedAsClass']}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in payload["counts"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Criteria", ""])
    lines.extend(f"- {item}" for item in payload["criteria"])
    lines.extend(["", "## Evaluated Blocks", "", "| Date | Window | Instructor | Public Selectable | Fit Eligible | Criteria Failures |", "| --- | --- | --- | ---: | ---: | --- |"])
    for item in payload["evaluatedBlocks"]:
        lines.append(
            f"| {item['date']} | {item['window']} | {item['instructor']} | "
            f"{item['publicSelectableCourseStartTimeOffers']} | {item['fitEligibleCourseStartTimeOffers']} | "
            f"{', '.join(item['criteriaFailures']) or 'none'} |"
        )
    return "\n".join(lines) + "\n"


def render_blocked_html(payload: dict[str, Any]) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(item['date'])}</td><td>{html.escape(item['window'])}</td>"
        f"<td>{html.escape(item['instructor'])}</td><td>{item['publicSelectableCourseStartTimeOffers']}</td>"
        f"<td>{item['fitEligibleCourseStartTimeOffers']}</td><td>{html.escape(', '.join(item['criteriaFailures']) or 'none')}</td></tr>"
        for item in payload["evaluatedBlocks"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Block Start Time Prototype - Blocked</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.45; color: #1d2733; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d7dde5; padding: 6px 8px; text-align: left; }}
    code {{ background: #eef2f7; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Block Start Time Prototype</h1>
  <p><strong>Status:</strong> blocked_no_matching_public_eligible_availability_block</p>
  <p><strong>Whole block presented as class:</strong> false</p>
  <p>{html.escape(payload['error'])}</p>
  <table>
    <thead><tr><th>Date</th><th>Window</th><th>Instructor</th><th>Public selectable</th><th>Fit eligible</th><th>Criteria failures</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
"""


def write_blocked_outputs(payload: dict[str, Any]) -> None:
    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(render_blocked_markdown(payload), encoding="utf-8")
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(render_blocked_html(payload), encoding="utf-8")


def run(select_mode: str = SELECT_BEST_FIT, write_outputs: bool = True) -> dict[str, Any]:
    courses = load_course_rules()
    availability, availability_stats = load_selected_availability()
    sessions = load_real_sessions()
    containers, location_resource_map = load_real_containers_and_location_map()
    policy = load_public_location_policy()
    public_offer_policy = load_public_offer_policy()
    try:
        if select_mode == SELECT_NEXT_PUBLIC_ELIGIBLE:
            result = select_next_public_eligible_block(availability, courses, sessions, containers, location_resource_map, policy, public_offer_policy, PUBLIC_POLICY_AS_OF_DATE)
        elif select_mode == SELECT_BEST_FIT:
            result = select_block(availability, courses, sessions, containers, location_resource_map, policy, public_offer_policy, PUBLIC_POLICY_AS_OF_DATE)
        else:
            raise PrototypeInputError(f"Unknown --select mode: {select_mode}")
    except PrototypeInputError as exc:
        if len(exc.args) > 1 and isinstance(exc.args[1], dict):
            exc.args[1]["availability_source_used"] = availability_stats["availability_source_used"]
            exc.args[1]["availability_fallback_used"] = availability_stats["availability_fallback_used"]
            exc.args[1]["availabilitySource"] = availability_stats
        raise
    attach_availability_metadata(result, availability_stats)
    raw_availability = load_required_json(AVAILABILITY_PATH).get("availability_blocks", [])
    raw_outside_horizon = [
        block for block in raw_availability
        if isinstance(block, dict)
        and date.fromisoformat(str(block.get("date"))) > PUBLIC_POLICY_AS_OF_DATE + timedelta(days=PUBLIC_HORIZON_DAYS)
    ]
    result["publicationPolicy"]["rawAvailabilityBlocksOutside180DayHorizon"] = len(raw_outside_horizon)
    result["generatedAt"] = datetime.now(TZ).isoformat()
    result["overallStatus"] = "ok"
    result["sourceFiles"] = {
        "courseConsumptionRules": str(COURSE_RULES_PATH),
        "availability": availability_stats["availability_source_path"],
        "legacyAvailability": str(AVAILABILITY_PATH),
        "liveAvailabilitySnapshot": str(LIVE_AVAILABILITY_PATH),
        "sessions": str(SCHEDULE_PATH),
        "appointmentContainers": str(APPOINTMENT_CONTAINERS_PATH),
        "locationResourceMap": str(LOCATION_RESOURCE_MAP_PATH),
        "publicLocationPolicy": str(PUBLIC_LOCATION_POLICY_PATH),
        "publicOfferPolicy": str(PUBLIC_OFFER_POLICY_PATH),
    }
    result["sessionsLoadedForOccupancy"] = len(sessions)
    if write_outputs:
        REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        REPORT_MD_PATH.write_text(render_markdown(result), encoding="utf-8")
        HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
        HTML_PATH.write_text(render_html(result), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local proof report for block-based appointment start selection.")
    parser.add_argument(
        "--select",
        choices=[SELECT_BEST_FIT, SELECT_NEXT_PUBLIC_ELIGIBLE],
        default=SELECT_BEST_FIT,
        help="Block selection mode.",
    )
    parser.add_argument(
        "--refresh-live-snapshot",
        action="store_true",
        help="Run the safe local calendar snapshot refresh before selecting: export_calendar_snapshots, then build_live_availability_snapshot.",
    )
    args = parser.parse_args()
    if args.refresh_live_snapshot:
        for module in ("scripts.export_calendar_snapshots", "scripts.build_live_availability_snapshot"):
            subprocess.run([sys.executable, "-m", module], cwd=ROOT, check=True)
    try:
        result = run(select_mode=args.select)
    except PrototypeInputError as exc:
        if len(exc.args) > 1 and isinstance(exc.args[1], dict):
            write_blocked_outputs(exc.args[1])
            print(json.dumps(exc.args[1]["counts"], indent=2, ensure_ascii=False))
        print(f"ERROR: {exc.args[0]}")
        return 1
    else:
        print(json.dumps(result["counts"], indent=2, ensure_ascii=False))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
