from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"

INPUT_PATHS = {
    "course_catalog": ROOT / "data" / "config" / "course_catalog.json",
    "instructor_catalog": ROOT / "data" / "config" / "instructor_catalog.json",
    "people_catalog": ROOT / "data" / "config" / "people_catalog.json",
    "course_map": ROOT / "data" / "config" / "course_map.json",
    "course_consumption_rules": ROOT / "data" / "inventory" / "course_consumption_rules.json",
    "availability_window_policies": ROOT / "data" / "inventory" / "availability_window_policies.json",
    "calendar_sources": ROOT / "data" / "config" / "calendar_sources.json",
    "instructor_availability": ROOT / "data" / "inventory" / "instructor_availability.json",
    "sessions_current": ROOT / "data" / "sessions_current.json",
    "schedule_future": ROOT / "docs" / "data" / "schedule_future.json",
}

SUMMARY_PATH = AUDIT_DIR / "solver_audit_summary.json"
CANDIDATES_PATH = AUDIT_DIR / "solver_audit_candidates.json"
REJECTIONS_PATH = AUDIT_DIR / "solver_audit_rejections.json"
REPORT_PATH = AUDIT_DIR / "solver_audit_report.md"

UNKNOWN = "UNKNOWN"


def normalize_token(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def clean_text(value: Any) -> str:
    text = str(value or "").strip()
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def read_json(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid_json: {exc}"
    except OSError as exc:
        return None, f"read_error: {exc}"


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed.replace(tzinfo=None)


def parse_time(value: Any) -> time | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%H:%M", "%I:%M %p"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


def iso_date(value: datetime | None) -> str:
    return value.date().isoformat() if value else UNKNOWN


def iso_time(value: datetime | None) -> str:
    return value.strftime("%H:%M") if value else UNKNOWN


def combine_date_time(date_text: Any, time_text: Any) -> datetime | None:
    try:
        parsed_date = datetime.fromisoformat(str(date_text)).date()
    except ValueError:
        return None
    parsed_time = parse_time(time_text)
    if not parsed_time:
        return None
    return datetime.combine(parsed_date, parsed_time)


def intervals_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and start_b < end_a


def course_records(course_map: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(course_map, dict):
        return []
    courses = course_map.get("courses_by_id")
    if not isinstance(courses, dict):
        return []
    out: list[dict[str, Any]] = []
    for course_id, raw in courses.items():
        if not isinstance(raw, dict):
            continue
        record = dict(raw)
        record["course_id"] = str(record.get("course_id") or course_id)
        out.append(record)
    return out


def catalog_course_records(course_catalog: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(course_catalog, dict):
        return []
    courses = course_catalog.get("courses")
    if not isinstance(courses, list):
        return []
    return [course for course in courses if isinstance(course, dict)]


def rule_records(rules_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(rules_payload, dict):
        return []
    rules = rules_payload.get("rules")
    return [rule for rule in rules if isinstance(rule, dict)] if isinstance(rules, list) else []


def is_unknown(value: Any) -> bool:
    return value in (None, "", UNKNOWN)


def catalog_rule_records(courses: list[dict[str, Any]], legacy_rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    legacy_by_id = rules_by_course_id(legacy_rules)
    rules: list[dict[str, Any]] = []
    for course in courses:
        course_id = str(course.get("course_id") or "").strip()
        if not course_id:
            continue
        legacy = legacy_by_id.get(course_id, {})
        relationships = course.get("relationships") if isinstance(course.get("relationships"), dict) else {}
        rule = {
            "course_id": course_id,
            "clean_course_name": course.get("official_title") or course.get("short_title"),
            "course_family": course.get("family"),
            "duration_minutes": None if is_unknown(course.get("duration_minutes")) else course.get("duration_minutes"),
            "minimum_reservation_block_minutes": None if is_unknown(course.get("duration_minutes")) else course.get("duration_minutes"),
            "default_capacity": None if is_unknown(course.get("default_capacity")) else course.get("default_capacity"),
            "appointment_eligible": course.get("appointment_allowed"),
            "required_instructor_certifications": course.get("required_instructor_certifications"),
            "compatible_with": relationships.get("compatible_with", legacy.get("compatible_with", [])),
            "occupancy_pool": relationships.get("occupancy_pool", legacy.get("occupancy_pool")),
            "escalation_tier": relationships.get("escalation_tier", legacy.get("escalation_tier")),
        }
        rules.append(rule)
    return rules


def rules_by_course_id(rules: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for rule in rules:
        course_id = str(rule.get("course_id") or "").strip()
        if course_id:
            out[course_id] = rule
    return out


def rules_by_family(rules: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rule in rules:
        family = str(rule.get("course_family") or "").strip()
        if family:
            out[family].append(rule)
    return dict(out)


def best_rule_for_course(course: dict[str, Any], by_id: dict[str, dict[str, Any]], by_family: dict[str, list[dict[str, Any]]]) -> dict[str, Any] | None:
    course_id = str(course.get("course_id") or course.get("course_number") or "").strip()
    if course_id and course_id in by_id:
        return by_id[course_id]
    family = str(course.get("family") or "").strip()
    family_rules = by_family.get(family, [])
    return family_rules[0] if len(family_rules) == 1 else None


def normalize_occupancy_session(session: dict[str, Any], source_label: str) -> dict[str, Any]:
    start = parse_dt(session.get("start_at") or session.get("start") or session.get("start_datetime"))
    end = parse_dt(session.get("end_at") or session.get("end") or session.get("end_datetime"))
    course = session.get("course") if isinstance(session.get("course"), dict) else {}
    course_id = (
        session.get("course_id")
        or session.get("course_number")
        or course.get("course_id")
        or course.get("course_number")
        or None
    )
    title = (
        session.get("course_name")
        or session.get("official_course_name")
        or session.get("raw_course_name")
        or course.get("mapped_clean_title")
        or course.get("course_name_primary_clean")
        or course.get("course_name_raw")
        or UNKNOWN
    )
    return {
        "date": iso_date(start),
        "start_time": iso_time(start),
        "end_time": iso_time(end),
        "course_title": clean_text(title) or UNKNOWN,
        "course_id": str(course_id) if course_id else UNKNOWN,
        "location": clean_text(session.get("location_name") or session.get("location_display") or session.get("location") or UNKNOWN),
        "instructor": clean_text(session.get("lead_instructor_name") or session.get("instructor") or UNKNOWN),
        "source_file": source_label,
        "start_datetime": start.isoformat() if start else None,
        "end_datetime": end.isoformat() if end else None,
        "duration_status": "known" if start and end else "UNKNOWN",
    }


def occupancy_blocks(payload: Any, source_label: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    sessions = payload.get("sessions")
    if not isinstance(sessions, list):
        return []
    return [normalize_occupancy_session(session, source_label) for session in sessions if isinstance(session, dict)]


def local_availability_windows(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    windows = payload.get("availability_blocks")
    if not isinstance(windows, list):
        return []
    return [window for window in windows if isinstance(window, dict)]


def window_policy(window: dict[str, Any], policies_payload: Any) -> dict[str, Any]:
    if not isinstance(policies_payload, dict):
        return {}
    policy_id = str(window.get("policy_id") or "").strip()
    capacity_mode = str(window.get("capacity_mode") or "").strip()
    policies = policies_payload.get("policies") if isinstance(policies_payload.get("policies"), list) else []
    for policy in policies:
        if isinstance(policy, dict) and policy_id and str(policy.get("policy_id") or "") == policy_id:
            merged = dict(policy)
            merged.update({k: v for k, v in window.items() if v is not None})
            return merged
    modes = policies_payload.get("capacity_modes") if isinstance(policies_payload.get("capacity_modes"), dict) else {}
    if capacity_mode and capacity_mode in modes and isinstance(modes[capacity_mode], dict):
        merged = dict(modes[capacity_mode])
        merged.update({k: v for k, v in window.items() if v is not None})
        return merged
    defaults = policies_payload.get("defaults")
    return dict(defaults) if isinstance(defaults, dict) else {}


def course_allowed_by_window(course: dict[str, Any], rule: dict[str, Any], window: dict[str, Any], policy: dict[str, Any]) -> tuple[bool, str]:
    family = str(rule.get("course_family") or course.get("family") or "").strip()
    allowed = {str(value).strip() for value in window.get("allowed_course_families", [])}
    fallback = {str(value).strip() for value in window.get("fallback_course_families", [])}
    policy_allowed = {str(value).strip() for value in policy.get("allowed_course_families", [])}
    policy_fallback = {str(value).strip() for value in policy.get("fallback_course_families", [])}
    if not family:
        return False, "missing_course_family"
    if allowed or fallback:
        if family in allowed:
            return True, "course_family_allowed_by_availability_window"
        if family in fallback:
            return False, "course_family_only_available_as_manual_fallback"
        return False, "missing_instructor_qualification"
    if policy_allowed or policy_fallback:
        if family in policy_allowed:
            return True, "course_family_allowed_by_window_policy"
        if family in policy_fallback:
            return False, "course_family_only_available_as_policy_fallback"
        return False, "outside_configured_policy_window"
    return False, "missing_instructor_qualification"


def instructor_requirements_known(course: dict[str, Any], rule: dict[str, Any]) -> bool:
    requirements = course.get("required_instructor_certifications")
    if requirements is None:
        requirements = rule.get("required_instructor_certifications")
    if not isinstance(requirements, list) or not requirements:
        return False
    return not any(is_unknown(item) for item in requirements)


def required_instructor_certifications(course: dict[str, Any], rule: dict[str, Any]) -> list[str]:
    requirements = course.get("required_instructor_certifications")
    if requirements is None:
        requirements = rule.get("required_instructor_certifications")
    if not isinstance(requirements, list):
        return []
    return [str(item).strip() for item in requirements if not is_unknown(item)]


def instructor_records(instructor_catalog: Any) -> list[dict[str, Any]]:
    if not isinstance(instructor_catalog, dict):
        return []
    instructors = instructor_catalog.get("instructors")
    return [item for item in instructors if isinstance(item, dict)] if isinstance(instructors, list) else []


def instructor_lookup(instructor_catalog: Any) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for instructor in instructor_records(instructor_catalog):
        keys = {
            normalize_key(instructor.get("instructor_id")),
            normalize_key(instructor.get("display_name")),
        }
        aliases = instructor.get("aliases")
        if isinstance(aliases, list):
            keys.update(normalize_key(alias) for alias in aliases)
        for key in keys:
            if key:
                lookup[key] = instructor
    return lookup


def instructor_certification_codes(instructor: dict[str, Any] | None) -> list[str]:
    if not isinstance(instructor, dict):
        return []
    codes: list[str] = []
    top_level = instructor.get("certification_code")
    if not is_unknown(top_level):
        codes.append(str(top_level).strip())
    certifications = instructor.get("certifications")
    if isinstance(certifications, list):
        for certification in certifications:
            if isinstance(certification, dict):
                code = certification.get("certification_code")
            else:
                code = certification
            if not is_unknown(code):
                codes.append(str(code).strip())
            elif code == UNKNOWN:
                codes.append(UNKNOWN)
    return codes


def people_records(people_catalog: Any) -> list[dict[str, Any]]:
    if not isinstance(people_catalog, dict):
        return []
    people = people_catalog.get("people")
    return [item for item in people if isinstance(item, dict)] if isinstance(people, list) else []


def person_certification_codes(person: dict[str, Any] | None) -> list[str]:
    if not isinstance(person, dict):
        return []
    codes: list[str] = []
    certifications = person.get("certifications")
    if isinstance(certifications, list):
        for certification in certifications:
            if isinstance(certification, dict):
                code = certification.get("certification_code")
            else:
                code = certification
            if not is_unknown(code):
                codes.append(str(code).strip())
            elif code == UNKNOWN:
                codes.append(UNKNOWN)
    return codes


def people_lookup(people_catalog: Any) -> dict[str, dict[str, Any]]:
    direct: dict[str, dict[str, Any]] = {}
    first_names: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for person in people_records(people_catalog):
        display_name = clean_text(person.get("display_name"))
        email = clean_text(person.get("email"))
        person_id = clean_text(person.get("person_id"))
        email_local = email.split("@", 1)[0] if "@" in email else ""
        keys = {
            normalize_key(person_id),
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
            first_names[first].append(person)
    for first, matches in first_names.items():
        if len(matches) == 1 and first not in direct:
            direct[first] = matches[0]
    return direct


def match_person_for_instructor(instructor_name: str, people_by_key: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    key = normalize_key(instructor_name)
    return people_by_key.get(key)


def person_scheduler_enabled(person: dict[str, Any] | None) -> bool:
    if not isinstance(person, dict):
        return False
    return (
        person.get("dynamic_offer_eligible") is True
        and str(person.get("assignment_mode") or "").strip().upper() in {"PRIMARY", "SECONDARY"}
    )


def instructor_qualification_status(
    course: dict[str, Any],
    rule: dict[str, Any],
    instructor_name: str,
    instructors_by_key: dict[str, dict[str, Any]],
    people_by_key: dict[str, dict[str, Any]] | None = None,
    allow_availability_person_bridge: bool = False,
) -> dict[str, Any]:
    requirements = required_instructor_certifications(course, rule)
    if not requirements:
        return {
            "status": "unknown",
            "reason": "missing_instructor_requirement",
            "message": "Course is missing explicit required instructor certifications.",
            "qualification_source": "none",
            "scheduler_enabled": False,
        }

    if people_by_key:
        person = match_person_for_instructor(instructor_name, people_by_key)
        if person:
            person_codes = person_certification_codes(person)
            person_known_codes = {code for code in person_codes if code != UNKNOWN}
            scheduler_enabled = person_scheduler_enabled(person)
            allowed_by_bridge = scheduler_enabled or allow_availability_person_bridge
            if person_known_codes.intersection(requirements) and allowed_by_bridge:
                return {
                    "status": "matched",
                    "reason": "people_catalog_certification_match",
                    "message": "Instructor matched a People catalog record with a required certification code.",
                    "qualification_source": "people_catalog",
                    "matched_person_id": person.get("person_id", UNKNOWN),
                    "matched_person_name": person.get("display_name", UNKNOWN),
                    "assignment_mode": person.get("assignment_mode", UNKNOWN),
                    "dynamic_offer_eligible": person.get("dynamic_offer_eligible", False),
                    "scheduler_enabled": scheduler_enabled,
                    "availability_bridge_used": not scheduler_enabled and allow_availability_person_bridge,
                }
            if person_known_codes.intersection(requirements) and not allowed_by_bridge:
                return {
                    "status": "missing",
                    "reason": "missing_instructor_qualification",
                    "message": "Person has matching credentials but is not active for dynamic scheduling and is not tied to this availability window.",
                    "qualification_source": "people_catalog",
                    "matched_person_id": person.get("person_id", UNKNOWN),
                    "matched_person_name": person.get("display_name", UNKNOWN),
                    "assignment_mode": person.get("assignment_mode", UNKNOWN),
                    "dynamic_offer_eligible": person.get("dynamic_offer_eligible", False),
                    "scheduler_enabled": scheduler_enabled,
                }

    instructor = instructors_by_key.get(normalize_key(instructor_name))
    if not instructor:
        return {
            "status": "missing",
            "reason": "missing_instructor_qualification",
            "message": "Instructor is not present in data/config/instructor_catalog.json and did not match a scheduler-eligible People catalog record.",
            "qualification_source": "none",
            "scheduler_enabled": False,
        }
    codes = instructor_certification_codes(instructor)
    known_codes = {code for code in codes if code != UNKNOWN}
    if known_codes.intersection(requirements):
        return {
            "status": "matched",
            "reason": "instructor_certification_match",
            "message": "Instructor has a matching certification code in instructor_catalog.json.",
            "qualification_source": "instructor_catalog",
            "scheduler_enabled": False,
        }
    if UNKNOWN in codes or not codes:
        return {
            "status": "unknown",
            "reason": "instructor_qualification_unknown",
            "message": "Instructor exists in instructor_catalog.json, but exact certification code is UNKNOWN.",
            "qualification_source": "instructor_catalog",
            "scheduler_enabled": False,
        }
    return {
        "status": "missing",
        "reason": "missing_instructor_qualification",
        "message": "Instructor does not have a matching required certification code in instructor_catalog.json or people_catalog.json.",
        "qualification_source": "instructor_catalog",
        "scheduler_enabled": False,
    }


def has_known_conflict(start: datetime, end: datetime, occupancy: list[dict[str, Any]], location: str, instructor: str) -> tuple[bool, str | None]:
    for block in occupancy:
        block_start = parse_dt(block.get("start_datetime"))
        block_end = parse_dt(block.get("end_datetime"))
        if not block_start or not block_end:
            continue
        same_location = normalize_token(block.get("location")) == normalize_token(location)
        same_instructor = instructor != UNKNOWN and normalize_token(block.get("instructor")) == normalize_token(instructor)
        if (same_location or same_instructor) and intervals_overlap(start, end, block_start, block_end):
            return True, f"conflicts with existing scheduled class {block.get('course_title')} from {block.get('source_file')}"
    return False, None


def generate_candidate_id(course_id: str, window: dict[str, Any], start: datetime) -> str:
    instructor = normalize_token(window.get("instructor_name")) or "unknown-instructor"
    location = normalize_token(window.get("location_name"))[:24].replace(" ", "-") or "unknown-location"
    return f"solver-{course_id}-{instructor}-{location}-{start:%Y%m%d-%H%M}"


def generate_candidates_and_rejections(
    courses: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    policies_payload: Any,
    availability: list[dict[str, Any]],
    occupancy: list[dict[str, Any]],
    instructor_catalog: Any,
    people_catalog: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_id = rules_by_course_id(rules)
    by_family = rules_by_family(rules)
    instructors_by_key = instructor_lookup(instructor_catalog)
    people_by_key = people_lookup(people_catalog)
    candidates: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []

    if not availability:
        for course in courses:
            rejections.append({
                "course_id": str(course.get("course_id") or UNKNOWN),
                "course_title": clean_text(course.get("clean_title") or course.get("official_title") or UNKNOWN),
                "course_family": str(course.get("family") or UNKNOWN),
                "reason_code": "missing_instructor_availability",
                "message": "No explicit local availability windows were available; candidate generation intentionally skipped.",
            })
        return candidates, rejections

    for window_index, window in enumerate(availability, start=1):
        start = combine_date_time(window.get("date"), window.get("start_time"))
        window_end = combine_date_time(window.get("date"), window.get("end_time"))
        source_window = f"instructor_availability[{window_index}]"
        if not start or not window_end:
            rejections.append({
                "source_availability_window": source_window,
                "reason_code": "unknown_data_shape",
                "message": "Availability window is missing parseable date/start/end values.",
                "raw_window": window,
            })
            continue
        if window.get("availability_status") not in (None, "", "available"):
            rejections.append({
                "source_availability_window": source_window,
                "date": start.date().isoformat(),
                "start_time": start.strftime("%H:%M"),
                "end_time": window_end.strftime("%H:%M"),
                "reason_code": "outside_configured_policy_window",
                "message": f"Availability status is {window.get('availability_status')}; not treated as sellable.",
            })
            continue

        policy = window_policy(window, policies_payload)
        instructor = clean_text(window.get("instructor_name") or UNKNOWN) or UNKNOWN
        location = clean_text(window.get("location_name") or UNKNOWN) or UNKNOWN
        resource = clean_text(window.get("room_or_resource_name") or location or UNKNOWN) or UNKNOWN

        for course in courses:
            course_id = str(course.get("course_id") or "").strip()
            title = clean_text(course.get("clean_title") or course.get("official_title") or course.get("course_key") or UNKNOWN)
            family = str(course.get("family") or UNKNOWN)
            if not course_id:
                rejections.append({
                    "source_availability_window": source_window,
                    "course_id": UNKNOWN,
                    "course_title": title,
                    "course_family": family,
                    "reason_code": "missing_course_id",
                    "message": "Course is missing a confirmed course ID.",
                })
                continue
            rule = best_rule_for_course(course, by_id, by_family)
            if not rule:
                rejections.append({
                    "source_availability_window": source_window,
                    "course_id": course_id,
                    "course_title": title,
                    "course_family": family,
                    "reason_code": "missing_course_duration",
                    "message": "No unambiguous course consumption rule was found.",
                })
                continue
            duration = rule.get("duration_minutes") or rule.get("minimum_reservation_block_minutes")
            try:
                duration_minutes = int(duration)
            except (TypeError, ValueError):
                rejections.append({
                    "source_availability_window": source_window,
                    "course_id": course_id,
                    "course_title": title,
                    "course_family": family,
                    "reason_code": "missing_course_duration",
                    "message": "Course rule exists but duration is missing or not numeric.",
                })
                continue
            if not rule.get("default_capacity"):
                rejections.append({
                    "source_availability_window": source_window,
                    "course_id": course_id,
                    "course_title": title,
                    "course_family": family,
                    "reason_code": "missing_capacity_rule",
                    "message": "Course rule is missing default capacity.",
                })
                continue
            if rule.get("appointment_eligible") is not True:
                rejections.append({
                    "source_availability_window": source_window,
                    "course_id": course_id,
                    "course_title": title,
                    "course_family": family,
                    "reason_code": "missing_appointment_eligibility",
                    "message": "Course is not explicitly appointment-eligible in local rules.",
                })
                continue
            if not instructor_requirements_known(course, rule):
                rejections.append({
                    "source_availability_window": source_window,
                    "course_id": course_id,
                    "course_title": title,
                    "course_family": family,
                    "reason_code": "missing_instructor_requirement",
                    "message": "Course catalog is missing explicit required instructor certifications.",
                })
                continue

            qualification_status = instructor_qualification_status(
                course,
                rule,
                instructor,
                instructors_by_key,
                people_by_key,
                allow_availability_person_bridge=True,
            )
            if qualification_status["status"] == "missing":
                rejections.append({
                    "source_availability_window": source_window,
                    "course_id": course_id,
                    "course_title": title,
                    "course_family": family,
                    "instructor": instructor,
                    "required_instructor_certifications": required_instructor_certifications(course, rule),
                    "reason_code": qualification_status["reason"],
                    "message": qualification_status["message"],
                })
                continue

            allowed, allow_reason = course_allowed_by_window(course, rule, window, policy)
            if not allowed:
                rejections.append({
                    "source_availability_window": source_window,
                    "course_id": course_id,
                    "course_title": title,
                    "course_family": family,
                    "reason_code": allow_reason,
                    "message": "Course is not permitted by this local availability window/policy.",
                })
                continue

            end = start + timedelta(minutes=duration_minutes)
            if end > window_end:
                rejections.append({
                    "source_availability_window": source_window,
                    "course_id": course_id,
                    "course_title": title,
                    "course_family": family,
                    "duration_minutes": duration_minutes,
                    "reason_code": "outside_configured_policy_window",
                    "message": "Course duration does not fit inside the explicit local availability window.",
                })
                continue

            conflict, conflict_reason = has_known_conflict(start, end, occupancy, location, instructor)
            if conflict:
                rejections.append({
                    "source_availability_window": source_window,
                    "course_id": course_id,
                    "course_title": title,
                    "course_family": family,
                    "duration_minutes": duration_minutes,
                    "reason_code": "conflicts_with_existing_scheduled_class",
                    "message": conflict_reason or "Conflicts with existing scheduled class.",
                })
                continue

            confidence = "high" if instructor != UNKNOWN and location != UNKNOWN and course_id in by_id else "medium"
            if qualification_status["status"] == "matched" and not qualification_status.get("scheduler_enabled"):
                confidence = "medium"
            if qualification_status["status"] == "unknown":
                confidence = "low"
            candidates.append({
                "candidate_id": generate_candidate_id(course_id, window, start),
                "date": start.date().isoformat(),
                "start_time": start.strftime("%H:%M"),
                "end_time": end.strftime("%H:%M"),
                "course_id": course_id,
                "course_title": title,
                "course_family": str(rule.get("course_family") or family or UNKNOWN),
                "duration_minutes": duration_minutes,
                "location": location,
                "resource": resource,
                "instructor": instructor,
                "instructor_qualification_status": qualification_status["status"],
                "qualification_source": qualification_status.get("qualification_source", UNKNOWN),
                "matched_person_id": qualification_status.get("matched_person_id", UNKNOWN),
                "matched_person_name": qualification_status.get("matched_person_name", UNKNOWN),
                "person_scheduler_enabled": qualification_status.get("scheduler_enabled", False),
                "person_assignment_mode": qualification_status.get("assignment_mode", UNKNOWN),
                "person_dynamic_offer_eligible": qualification_status.get("dynamic_offer_eligible", False),
                "availability_bridge_used": qualification_status.get("availability_bridge_used", False),
                "required_instructor_certifications": required_instructor_certifications(course, rule),
                "source_availability_window": source_window,
                "confidence": confidence,
                "reasons": [
                    "explicit_local_availability_window",
                    allow_reason,
                    qualification_status["reason"],
                    "course_rule_has_duration_and_capacity",
                    "no_known_local_schedule_conflict",
                    "read_only_candidate_not_public_offer",
                ],
            })

    return candidates, rejections


def course_inventory_summary(courses: list[dict[str, Any]], rules: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = rules_by_course_id(rules)
    by_family = rules_by_family(rules)
    active_courses = [course for course in courses if course.get("active") is not False]
    missing_duration: list[dict[str, str]] = []
    missing_capacity: list[dict[str, str]] = []
    unsafe: list[dict[str, str]] = []
    for course in active_courses:
        course_id = str(course.get("course_id") or UNKNOWN)
        title = clean_text(course.get("clean_title") or course.get("official_title") or UNKNOWN)
        rule = best_rule_for_course(course, by_id, by_family)
        if not rule or not (rule.get("duration_minutes") or rule.get("minimum_reservation_block_minutes")):
            missing_duration.append({"course_id": course_id, "course_title": title, "reason": "missing duration rule"})
        if not rule or not rule.get("default_capacity"):
            missing_capacity.append({"course_id": course_id, "course_title": title, "reason": "missing capacity rule"})
        unsafe_reasons = []
        if course_id == UNKNOWN:
            unsafe_reasons.append("missing course ID")
        if not rule:
            unsafe_reasons.append("missing unambiguous rule")
        elif rule.get("appointment_eligible") is not True:
            unsafe_reasons.append("missing appointment eligibility")
        if rule and not instructor_requirements_known(course, rule):
            unsafe_reasons.append("missing instructor requirement")
        if unsafe_reasons:
            unsafe.append({"course_id": course_id, "course_title": title, "reason": "; ".join(unsafe_reasons)})
    return {
        "active_course_count": len(active_courses),
        "course_ids_found": sorted({str(course.get("course_id")) for course in active_courses if course.get("course_id")}),
        "course_families_found": sorted({str(course.get("family")) for course in active_courses if course.get("family")}),
        "duration_capacity_rules_found": len(rules),
        "primary_course_rule_source": "data/config/course_catalog.json",
        "courses_missing_duration_rules": missing_duration,
        "courses_missing_capacity_rules": missing_capacity,
        "courses_unsafe_for_appointment_generation": unsafe,
    }


def instructor_catalog_summary(instructor_catalog: Any, courses: list[dict[str, Any]], rules: list[dict[str, Any]], rejections: list[dict[str, Any]]) -> dict[str, Any]:
    instructors = instructor_records(instructor_catalog)
    active = [item for item in instructors if item.get("active") is True]
    known_codes: set[str] = set()
    unknown_certification_instructors: list[str] = []
    for instructor in instructors:
        codes = instructor_certification_codes(instructor)
        known_codes.update(code for code in codes if code != UNKNOWN)
        if not codes or UNKNOWN in codes:
            unknown_certification_instructors.append(str(instructor.get("display_name") or instructor.get("instructor_id") or UNKNOWN))

    by_id = rules_by_course_id(rules)
    by_family = rules_by_family(rules)
    no_qualified: list[dict[str, str]] = []
    for course in courses:
        rule = best_rule_for_course(course, by_id, by_family)
        if not rule:
            continue
        requirements = required_instructor_certifications(course, rule)
        if requirements and not known_codes.intersection(requirements):
            no_qualified.append({
                "course_id": str(course.get("course_id") or UNKNOWN),
                "course_title": clean_text(course.get("clean_title") or course.get("official_title") or UNKNOWN),
                "required_instructor_certifications": ", ".join(requirements),
            })

    rejection_counts = Counter(str(item.get("reason_code") or "other") for item in rejections)
    return {
        "instructors_found": len(instructors),
        "active_instructors": len(active),
        "certifications_known": sorted(known_codes),
        "certifications_unknown_instructors": sorted(unknown_certification_instructors),
        "certifications_unknown_count": len(unknown_certification_instructors),
        "courses_with_no_exact_qualified_instructor": no_qualified,
        "remaining_missing_instructor_qualification_count": rejection_counts.get("missing_instructor_qualification", 0),
    }


def people_catalog_summary(
    people_catalog: Any,
    availability_windows: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    rejections: list[dict[str, Any]],
) -> dict[str, Any]:
    people = people_records(people_catalog)
    people_by_key = people_lookup(people_catalog)
    credentialed = [person for person in people if any(code != UNKNOWN for code in person_certification_codes(person))]
    scheduler_enabled = [person for person in people if person_scheduler_enabled(person)]
    availability_instructor_names = sorted({
        clean_text(window.get("instructor_name"))
        for window in availability_windows
        if clean_text(window.get("instructor_name"))
    })
    matched: list[dict[str, Any]] = []
    for instructor_name in availability_instructor_names:
        person = match_person_for_instructor(instructor_name, people_by_key)
        if person:
            matched.append({
                "availability_instructor": instructor_name,
                "person_id": person.get("person_id", UNKNOWN),
                "display_name": person.get("display_name", UNKNOWN),
                "scheduler_enabled": person_scheduler_enabled(person),
                "assignment_mode": person.get("assignment_mode", UNKNOWN),
                "dynamic_offer_eligible": person.get("dynamic_offer_eligible", False),
                "certification_codes": sorted({code for code in person_certification_codes(person) if code != UNKNOWN}),
            })
    qualified_course_ids = sorted({
        str(candidate.get("course_id"))
        for candidate in candidates
        if candidate.get("qualification_source") == "people_catalog"
        and candidate.get("person_scheduler_enabled") is True
    })
    bridge_course_ids = sorted({
        str(candidate.get("course_id"))
        for candidate in candidates
        if candidate.get("qualification_source") == "people_catalog"
        and candidate.get("availability_bridge_used") is True
    })
    rejection_counts = Counter(str(item.get("reason_code") or "other") for item in rejections)
    return {
        "people_catalog_read": isinstance(people_catalog, dict),
        "people_count": len(people),
        "people_with_certifications": len(credentialed),
        "people_scheduler_enabled": len(scheduler_enabled),
        "availability_instructors": availability_instructor_names,
        "availability_instructors_matched_to_people": matched,
        "courses_with_qualified_scheduler_enabled_instructor": qualified_course_ids,
        "courses_with_availability_bridge_qualified_instructor": bridge_course_ids,
        "remaining_missing_instructor_qualification": rejection_counts.get("missing_instructor_qualification", 0),
    }


def availability_summary(calendar_sources: Any, availability_payload: Any) -> dict[str, Any]:
    sources = []
    if isinstance(calendar_sources, dict) and isinstance(calendar_sources.get("calendar_sources"), list):
        for source in calendar_sources["calendar_sources"]:
            if isinstance(source, dict):
                sources.append({
                    "calendar_source_key": source.get("calendar_source_key", UNKNOWN),
                    "display_name": source.get("display_name", UNKNOWN),
                    "calendar_mode": source.get("calendar_mode") or source.get("mode") or UNKNOWN,
                    "active": source.get("active", UNKNOWN),
                    "missing_access_policy": source.get("missing_access_policy", UNKNOWN),
                    "live_fetch_performed": False,
                })
    windows = local_availability_windows(availability_payload)
    statuses = Counter(str(window.get("availability_status") or UNKNOWN) for window in windows)
    return {
        "calendar_sources_declared": sources,
        "live_calendar_fetch_performed": False,
        "explicit_local_availability_window_count": len(windows),
        "availability_status_counts": dict(sorted(statuses.items())),
        "dns_or_do_not_schedule_markers": "UNKNOWN unless represented in local snapshots; live calendars were not fetched",
        "adr_or_employment_blocks": "UNKNOWN unless represented in local snapshots; live calendars were not fetched",
    }


def write_outputs(
    loaded: dict[str, Any],
    missing: dict[str, str],
    inventory: dict[str, Any],
    occupancy: list[dict[str, Any]],
    availability: dict[str, Any],
    instructors: dict[str, Any],
    people: dict[str, Any],
    candidates: list[dict[str, Any]],
    rejections: list[dict[str, Any]],
) -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    reason_counts = Counter(str(item.get("reason_code") or "other") for item in rejections)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "public_site_affected": False,
        "external_network_calls": False,
        "files_read": sorted(loaded.keys()),
        "files_missing_or_unreadable": missing,
        "course_inventory_summary": inventory,
        "instructor_catalog_summary": instructors,
        "people_catalog_summary": people,
        "existing_scheduled_occupancy_count": len(occupancy),
        "availability_input_summary": availability,
        "candidate_count": len(candidates),
        "rejection_count": len(rejections),
        "top_rejection_reasons": dict(reason_counts.most_common(10)),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    CANDIDATES_PATH.write_text(json.dumps({"candidates": candidates}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REJECTIONS_PATH.write_text(json.dumps({"rejections": rejections}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(summary, occupancy), encoding="utf-8")


def render_report(summary: dict[str, Any], occupancy: list[dict[str, Any]]) -> str:
    missing = summary["files_missing_or_unreadable"]
    inventory = summary["course_inventory_summary"]
    instructors = summary.get("instructor_catalog_summary", {})
    people = summary.get("people_catalog_summary", {})
    top_reasons = summary["top_rejection_reasons"]
    lines = [
        "# Solver Audit Report",
        "",
        "This is a read-only scheduler redesign audit. It did not modify public pages, runtime data, Enrollware behavior, appointments, Worker settings, or generated HTML.",
        "",
        "## Files Read",
        "",
    ]
    lines.extend(f"- `{name}`" for name in summary["files_read"])
    lines.extend(["", "## Files Missing Or Unreadable", ""])
    if missing:
        lines.extend(f"- `{name}`: {reason}" for name, reason in sorted(missing.items()))
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Assumptions Avoided",
        "",
        "- Did not invent Enrollware course IDs.",
        "- Did not assume overnight should or should not be offered.",
        "- Did not fetch Google Calendar or Enrollware live data.",
        "- Did not treat debug reports as source of truth.",
        "- Did not generate candidates without an explicit local availability window.",
        "",
        "## Summary",
        "",
        f"- Active courses understood: {inventory['active_course_count']}",
        f"- Course families found: {', '.join(inventory['course_families_found']) or UNKNOWN}",
        f"- Instructors found: {instructors.get('instructors_found', 0)}",
        f"- Active instructors: {instructors.get('active_instructors', 0)}",
        f"- Instructors with UNKNOWN certifications: {instructors.get('certifications_unknown_count', 0)}",
        f"- People catalog read: {people.get('people_catalog_read', False)}",
        f"- People with certifications: {people.get('people_with_certifications', 0)}",
        f"- People scheduler-enabled: {people.get('people_scheduler_enabled', 0)}",
        f"- Availability instructors matched to People: {len(people.get('availability_instructors_matched_to_people', []))}",
        f"- Remaining `missing_instructor_qualification` rejections: {instructors.get('remaining_missing_instructor_qualification_count', 0)}",
        f"- Existing occupancy blocks normalized: {summary['existing_scheduled_occupancy_count']}",
        f"- Candidates generated: {summary['candidate_count']}",
        f"- Rejections created: {summary['rejection_count']}",
        "",
        "## Top 10 Blockers",
        "",
    ])
    if top_reasons:
        lines.extend(f"- `{reason}`: {count}" for reason, count in top_reasons.items())
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## People Catalog Qualification Bridge",
        "",
    ])
    matches = people.get("availability_instructors_matched_to_people", [])
    if matches:
        lines.extend(["| Availability Instructor | Matched Person | Scheduler Enabled | Certification Codes |", "| --- | --- | --- | --- |"])
        for match in matches:
            codes = ", ".join(f"`{code}`" for code in match.get("certification_codes", [])) or UNKNOWN
            lines.append(
                f"| {match.get('availability_instructor', UNKNOWN)} | "
                f"{match.get('display_name', UNKNOWN)} (`{match.get('person_id', UNKNOWN)}`) | "
                f"{match.get('scheduler_enabled', False)} | {codes} |"
            )
    else:
        lines.append("- No availability instructors matched People catalog records.")
    lines.extend([
        "",
        f"- Courses with scheduler-enabled qualified instructor: {len(people.get('courses_with_qualified_scheduler_enabled_instructor', []))}",
        f"- Courses qualified only through availability bridge: {len(people.get('courses_with_availability_bridge_qualified_instructor', []))}",
    ])
    lines.extend([
        "",
        "## Occupancy Notes",
        "",
        f"- Occupancy examples inspected: {min(10, len(occupancy))}",
    ])
    for block in occupancy[:10]:
        lines.append(
            f"- {block['date']} {block['start_time']}-{block['end_time']} | "
            f"{block['course_title']} | {block['location']} | source `{block['source_file']}`"
        )
    lines.extend([
        "",
        "## Safest Next Steps",
        "",
        "1. Confirm the active source-of-truth files with Brian before promoting any solver output.",
        "2. Add a canonical course/format model that links course IDs, duration, capacity, appointment eligibility, and public labels.",
        "3. Replace prototype availability blocks with audited local snapshots from the intended calendar model.",
        "4. Add explicit room/resource conflict rules before using candidates publicly.",
        "5. Keep generated candidates read-only until click-time recheck and Enrollware bridge behavior are specified.",
        "",
    ])
    return "\n".join(lines)


def run_audit() -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    missing: dict[str, str] = {}
    for name, path in INPUT_PATHS.items():
        payload, error = read_json(path)
        if error:
            missing[name] = error
        else:
            loaded[name] = payload

    catalog_courses = catalog_course_records(loaded.get("course_catalog"))
    courses = catalog_courses or course_records(loaded.get("course_map"))
    legacy_rules = rule_records(loaded.get("course_consumption_rules"))
    rules = catalog_rule_records(courses, legacy_rules) if catalog_courses else legacy_rules
    occupancy = [
        *occupancy_blocks(loaded.get("sessions_current"), "data/sessions_current.json"),
        *occupancy_blocks(loaded.get("schedule_future"), "docs/data/schedule_future.json"),
    ]
    availability_windows = local_availability_windows(loaded.get("instructor_availability"))
    candidates, rejections = generate_candidates_and_rejections(
        courses,
        rules,
        loaded.get("availability_window_policies"),
        availability_windows,
        occupancy,
        loaded.get("instructor_catalog"),
        loaded.get("people_catalog"),
    )
    inventory = course_inventory_summary(courses, rules)
    availability = availability_summary(loaded.get("calendar_sources"), loaded.get("instructor_availability"))
    instructors = instructor_catalog_summary(loaded.get("instructor_catalog"), courses, rules, rejections)
    people = people_catalog_summary(loaded.get("people_catalog"), availability_windows, candidates, rejections)
    write_outputs(loaded, missing, inventory, occupancy, availability, instructors, people, candidates, rejections)
    return {
        "files_read": sorted(loaded.keys()),
        "files_missing_or_unreadable": missing,
        "candidate_count": len(candidates),
        "rejection_count": len(rejections),
        "output_paths": [SUMMARY_PATH, CANDIDATES_PATH, REJECTIONS_PATH, REPORT_PATH],
    }


def main() -> int:
    result = run_audit()
    print("Solver audit complete (READ ONLY).")
    print("No public pages, runtime data, Enrollware behavior, appointments, or Worker creation settings were changed.")
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
    print(f"Candidates generated: {result['candidate_count']}")
    print(f"Rejections generated: {result['rejection_count']}")
    print("")
    print("Output files:")
    for path in result["output_paths"]:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
