from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date, datetime, time
from pathlib import Path
from typing import Any
from urllib.parse import quote

from scripts.public_class_eligibility import public_location_rejection_reason

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
SEEDS_PATH = AUDIT_DIR / "schedule_seeds_preview.json"
COURSE_CATALOG_PATH = ROOT / "data" / "config" / "course_catalog.json"
APPOINTMENT_CONTAINERS_PATH = ROOT / "data" / "inventory" / "appointment_containers.json"
LOCATION_RESOURCE_MAP_PATH = ROOT / "data" / "config" / "location_resource_map.json"
PREVIEW_PATH = AUDIT_DIR / "seed_appointment_url_preview.json"
REPORT_PATH = AUDIT_DIR / "seed_appointment_url_report.md"
ENROLLWARE_ENROLL_BASE = "https://coastalcprtraining.enrollware.com/enroll"
UNKNOWN = "UNKNOWN"


def read_json(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid_json: {exc}"
    except OSError as exc:
        return None, f"read_error: {exc}"


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean_text(value).lower()).strip("_")


def location_alias_lookup(location_resource_map: Any) -> dict[str, str]:
    if not isinstance(location_resource_map, dict) or not isinstance(location_resource_map.get("locations"), list):
        return {}
    lookup: dict[str, str] = {}
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
            if text and canonical:
                lookup[normalize_key(text)] = canonical
    return lookup


def canonical_location(value: Any, location_resource_map: Any) -> str:
    text = clean_text(value)
    return location_alias_lookup(location_resource_map).get(normalize_key(text), text)


def parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def parse_time(value: Any) -> time | None:
    try:
        return datetime.strptime(str(value), "%H:%M").time()
    except ValueError:
        return None


def appointment_display_time(seed: dict[str, Any]) -> time | None:
    display_start = clean_text(seed.get("appointment_display_start"))
    if display_start:
        try:
            return datetime.fromisoformat(display_start).time()
        except ValueError:
            pass
    return parse_time(seed.get("start_time"))


def display_time(value: time) -> str:
    return datetime.combine(date(2000, 1, 1), value).strftime("%I:%M %p").lstrip("0")


def build_registration_url(appointment_day_id: int, start_time: time, course_id: str) -> str:
    return (
        f"{ENROLLWARE_ENROLL_BASE}?appointmentDayId={appointment_day_id}"
        f"&startTime={quote(display_time(start_time))}"
        f"&courseId={quote(str(course_id))}"
    )


def courses_by_id(course_catalog: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(course_catalog, dict) or not isinstance(course_catalog.get("courses"), list):
        return {}
    return {
        str(course.get("course_id")): course
        for course in course_catalog["courses"]
        if isinstance(course, dict) and course.get("course_id")
    }


def active_containers(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("containers"), list):
        return []
    return [item for item in payload["containers"] if isinstance(item, dict) and item.get("status") == "active"]


def instructor_matches(seed: dict[str, Any], container: dict[str, Any]) -> bool:
    container_name = clean_text(container.get("instructor_name"))
    seed_name = clean_text(seed.get("instructor_display_name"))
    if not container_name:
        return True
    if normalize_key(container_name) == normalize_key(seed_name):
        return True
    # Brian Ennis in People/catalog maps to Brian in the owned appointment container.
    return normalize_key(seed_name).startswith(normalize_key(container_name) + "_")


def location_matches(seed: dict[str, Any], container: dict[str, Any], location_resource_map: Any = None) -> bool:
    container_location = canonical_location(container.get("location_name"), location_resource_map)
    seed_location = canonical_location(seed.get("location"), location_resource_map)
    if container_location and seed_location and container_location != seed_location:
        return False
    return True


def compute_appointment_day_id(container: dict[str, Any], target_date: date) -> int:
    first_date = parse_date(container.get("first_valid_date"))
    if not first_date:
        raise ValueError("container missing first_valid_date")
    return int(container["first_valid_appointmentDayId"]) + (target_date - first_date).days


def validate_container_day(container: dict[str, Any], target_date: date) -> tuple[bool, int | None, str]:
    appointment_day_id = compute_appointment_day_id(container, target_date)
    first_date = parse_date(container.get("first_valid_date"))
    last_date = parse_date(container.get("last_valid_date"))
    if not first_date or not last_date:
        return False, appointment_day_id, "container_missing_valid_date_range"
    if target_date < first_date:
        return False, appointment_day_id, "date_before_owned_appointment_range"
    if target_date > last_date:
        return False, appointment_day_id, "date_after_owned_appointment_range"
    if appointment_day_id < int(container.get("first_valid_appointmentDayId", -1)):
        return False, appointment_day_id, "appointmentDayId_before_owned_range"
    if appointment_day_id > int(container.get("last_valid_appointmentDayId", -1)):
        return False, appointment_day_id, "appointmentDayId_after_owned_range"
    first_invalid = container.get("first_invalid_appointmentDayId")
    if first_invalid is not None and appointment_day_id >= int(first_invalid):
        return False, appointment_day_id, "appointmentDayId_reaches_first_invalid_boundary"
    return True, appointment_day_id, "owned_appointment_container"


def matching_container(seed: dict[str, Any], containers: list[dict[str, Any]], target_date: date, location_resource_map: Any = None) -> tuple[dict[str, Any] | None, int | None, str]:
    candidates = [
        container for container in containers
        if instructor_matches(seed, container) and location_matches(seed, container, location_resource_map)
    ]
    if not candidates:
        return None, None, "no_matching_appointment_container"
    valid: list[tuple[int, str, dict[str, Any], int]] = []
    last_reason = "appointment_container_out_of_range"
    last_id: int | None = None
    for container in candidates:
        ok, appointment_day_id, reason = validate_container_day(container, target_date)
        last_reason = reason
        last_id = appointment_day_id
        if ok and appointment_day_id is not None:
            valid.append((int(container.get("priority", 0) or 0), str(container.get("container_id") or ""), container, appointment_day_id))
    if not valid:
        return None, last_id, last_reason
    valid.sort(reverse=True)
    _priority, _container_id, container, appointment_day_id = valid[0]
    return container, appointment_day_id, "owned_appointment_container"


def build_preview_records(seeds_payload: Any, course_catalog: Any, containers_payload: Any, location_resource_map: Any = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    seeds = seeds_payload.get("seeds", []) if isinstance(seeds_payload, dict) else []
    if not isinstance(seeds, list):
        seeds = []
    courses = courses_by_id(course_catalog)
    containers = active_containers(containers_payload)
    records: list[dict[str, Any]] = []
    for seed in seeds:
        if not isinstance(seed, dict):
            continue
        course_id = str(seed.get("course_id") or UNKNOWN)
        course = courses.get(course_id)
        target_date = parse_date(seed.get("date"))
        start = appointment_display_time(seed)
        base_record = {
            "seed_id": seed.get("seed_id", UNKNOWN),
            "source_offer_id": seed.get("source_offer_id", UNKNOWN),
            "date": seed.get("date", UNKNOWN),
            "start_time": seed.get("start_time", UNKNOWN),
            "appointment_display_start": seed.get("appointment_display_start", seed.get("start_time", UNKNOWN)),
            "appointment_display_end": seed.get("appointment_display_end", UNKNOWN),
            "scheduler_consumption_start": seed.get("scheduler_consumption_start", UNKNOWN),
            "scheduler_consumption_end": seed.get("scheduler_consumption_end", UNKNOWN),
            "scheduler_consumption_minutes": seed.get("scheduler_consumption_minutes", UNKNOWN),
            "instructor_lock_start": seed.get("instructor_lock_start", UNKNOWN),
            "instructor_lock_end": seed.get("instructor_lock_end", UNKNOWN),
            "resource_lock_start": seed.get("resource_lock_start", UNKNOWN),
            "resource_lock_end": seed.get("resource_lock_end", UNKNOWN),
            "course_id": course_id,
            "course_title": seed.get("course_title", UNKNOWN),
            "instructor_display_name": seed.get("instructor_display_name", UNKNOWN),
            "location": seed.get("location", UNKNOWN),
            "matched_container_id": None,
            "appointmentDayId": None,
            "appointment_url_preview": None,
            "confidence": "blocked",
            "reasons": ["read_only_preview", "not_fetched", "not_created"],
            "blocking_reason": None,
        }
        if not course:
            base_record["blocking_reason"] = "course_not_found"
            records.append(base_record)
            continue
        if course.get("appointment_allowed") is not True:
            base_record["blocking_reason"] = "appointment_not_allowed"
            records.append(base_record)
            continue
        location_reason = public_location_rejection_reason(seed.get("location"))
        if location_reason:
            base_record["blocking_reason"] = location_reason
            records.append(base_record)
            continue
        if course.get("appointment_container_required") is True and not containers:
            base_record["blocking_reason"] = "appointment_container_required_but_missing"
            records.append(base_record)
            continue
        if not target_date:
            base_record["blocking_reason"] = "invalid_seed_date"
            records.append(base_record)
            continue
        if not start:
            base_record["blocking_reason"] = "invalid_seed_start_time"
            records.append(base_record)
            continue
        container, appointment_day_id, reason = matching_container(seed, containers, target_date, location_resource_map)
        if not container or appointment_day_id is None:
            base_record["appointmentDayId"] = appointment_day_id
            base_record["blocking_reason"] = reason
            records.append(base_record)
            continue
        base_record.update({
            "matched_container_id": container.get("container_id", UNKNOWN),
            "appointmentDayId": appointment_day_id,
            "appointment_url_preview": build_registration_url(appointment_day_id, start, course_id),
            "confidence": "high",
            "reasons": [
                "read_only_preview",
                "course_appointment_allowed",
                "owned_appointment_container",
                "appointmentDayId_in_owned_range",
                "not_fetched",
                "not_created",
            ],
            "blocking_reason": None,
        })
        records.append(base_record)
    stats = {
        "seeds_read": len(seeds),
        "urls_previewed": sum(1 for item in records if item.get("appointment_url_preview")),
        "seeds_blocked": sum(1 for item in records if item.get("blocking_reason")),
        "blocked_by_reason": dict(Counter(item["blocking_reason"] for item in records if item.get("blocking_reason")).most_common()),
        "appointmentDayId_min": min((item["appointmentDayId"] for item in records if item.get("appointmentDayId")), default=None),
        "appointmentDayId_max": max((item["appointmentDayId"] for item in records if item.get("appointmentDayId")), default=None),
    }
    return records, stats


def render_report(records: list[dict[str, Any]], stats: dict[str, Any], missing: dict[str, str]) -> str:
    lines = [
        "# Seed Appointment URL Preview Report",
        "",
        "Preview only. These URLs were not fetched, not published, and did not create appointments. No public pages, Enrollware behavior, appointment URLs, or Worker settings were changed.",
        "",
        "## Summary",
        "",
        f"- Seeds read: {stats['seeds_read']}",
        f"- URLs previewed: {stats['urls_previewed']}",
        f"- Seeds blocked: {stats['seeds_blocked']}",
        f"- AppointmentDayId range used: {stats['appointmentDayId_min']} to {stats['appointmentDayId_max']}",
        "",
        "## Missing Inputs",
        "",
    ]
    if missing:
        lines.extend(f"- `{name}`: {reason}" for name, reason in sorted(missing.items()))
    else:
        lines.append("- None")
    lines.extend(["", "## Blocked By Reason", ""])
    if stats["blocked_by_reason"]:
        lines.extend(f"- `{reason}`: {count}" for reason, count in stats["blocked_by_reason"].items())
    else:
        lines.append("- None")
    lines.extend(["", "## Example URLs", ""])
    examples = [item for item in records if item.get("appointment_url_preview")][:20]
    if examples:
        lines.extend(["| Date | Time | Course | AppointmentDayId | Preview URL |", "| --- | --- | --- | ---: | --- |"])
        for item in examples:
            lines.append(
                f"| {item['date']} | {item['start_time']} | {item['course_title']} | "
                f"{item['appointmentDayId']} | `{item['appointment_url_preview']}` |"
            )
    else:
        lines.append("- None")
    lines.extend(["", "## Warning", "", "- Preview only: not public, not fetched, not created.", ""])
    return "\n".join(lines)


def run() -> dict[str, Any]:
    seeds_payload, seeds_error = read_json(SEEDS_PATH)
    course_catalog, course_error = read_json(COURSE_CATALOG_PATH)
    containers_payload, containers_error = read_json(APPOINTMENT_CONTAINERS_PATH)
    location_resource_map, location_map_error = read_json(LOCATION_RESOURCE_MAP_PATH)
    missing = {}
    if seeds_error:
        missing["schedule_seeds_preview"] = seeds_error
    if course_error:
        missing["course_catalog"] = course_error
    if containers_error:
        missing["appointment_containers"] = containers_error
    if location_map_error:
        missing["location_resource_map"] = location_map_error
    records, stats = build_preview_records(seeds_payload or {}, course_catalog or {}, containers_payload or {}, location_resource_map or {})
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "public_site_affected": False,
        "enrollware_called": False,
        "appointments_created": False,
        "appointment_urls_changed": False,
        "source_schedule_seeds": str(SEEDS_PATH),
        "source_course_catalog": str(COURSE_CATALOG_PATH),
        "source_appointment_containers": str(APPOINTMENT_CONTAINERS_PATH),
        "source_location_resource_map": str(LOCATION_RESOURCE_MAP_PATH),
        "stats": stats,
        "previews": records,
    }
    PREVIEW_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(records, stats, missing), encoding="utf-8")
    return {"stats": stats, "missing": missing, "output_paths": [PREVIEW_PATH, REPORT_PATH]}


def main() -> int:
    result = run()
    print("Seed appointment URL preview complete (READ ONLY).")
    print("No public pages, Enrollware calls, appointments, appointment URL changes, or Worker settings were changed.")
    print("")
    print(f"Seeds read: {result['stats']['seeds_read']}")
    print(f"URLs previewed: {result['stats']['urls_previewed']}")
    print(f"Seeds blocked: {result['stats']['seeds_blocked']}")
    print("")
    print("Output files:")
    for path in result["output_paths"]:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
