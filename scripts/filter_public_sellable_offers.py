from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"

DYNAMIC_OFFERS_PATH = AUDIT_DIR / "dynamic_offers_preview.json"
COURSE_CATALOG_PATH = ROOT / "data" / "config" / "course_catalog.json"
APPOINTMENT_CONTAINERS_PATH = ROOT / "data" / "inventory" / "appointment_containers.json"
LOCATION_RESOURCE_MAP_PATH = ROOT / "data" / "config" / "location_resource_map.json"
PUBLIC_OFFER_POLICY_PATH = ROOT / "data" / "config" / "public_offer_policy.json"
SELLABLE_OFFERS_PATH = AUDIT_DIR / "public_sellable_offers_preview.json"
REPORT_PATH = AUDIT_DIR / "public_sellable_offers_report.md"
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


def parse_offer_start(offer: dict[str, Any]) -> datetime | None:
    date = offer.get("date")
    start = offer.get("start_time")
    if not date or not start:
        return None
    try:
        return datetime.fromisoformat(f"{date}T{start}")
    except ValueError:
        return None


def parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def normalize_key(value: Any) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def course_lookup(course_catalog: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(course_catalog, dict) or not isinstance(course_catalog.get("courses"), list):
        return {}
    return {
        str(course.get("course_id")): course
        for course in course_catalog["courses"]
        if isinstance(course, dict) and course.get("course_id")
    }


def as_set(policy: dict[str, Any], key: str) -> set[str]:
    value = policy.get(key)
    if not isinstance(value, list):
        return set()
    return {str(item).strip() for item in value}


def is_true(value: Any) -> bool:
    return value is True or str(value).strip().lower() == "true"


def active_containers(containers_payload: Any) -> list[dict[str, Any]]:
    if not isinstance(containers_payload, dict) or not isinstance(containers_payload.get("containers"), list):
        return []
    return [item for item in containers_payload["containers"] if isinstance(item, dict) and item.get("status") == "active"]


def location_alias_lookup(location_resource_map: Any) -> dict[str, str]:
    if not isinstance(location_resource_map, dict) or not isinstance(location_resource_map.get("locations"), list):
        return {}
    lookup: dict[str, str] = {}
    for location in location_resource_map["locations"]:
        if not isinstance(location, dict):
            continue
        canonical = str(location.get("canonical_public_location") or "").strip()
        aliases = list(location.get("aliases", [])) if isinstance(location.get("aliases"), list) else []
        resources = location.get("internal_resources", []) if isinstance(location.get("internal_resources"), list) else []
        values = [canonical, *aliases]
        values.extend(resource.get("resource_name") for resource in resources if isinstance(resource, dict))
        for value in values:
            text = str(value or "").strip()
            if text and canonical:
                lookup[normalize_key(text)] = canonical
    return lookup


def canonical_location(value: Any, location_resource_map: Any) -> str:
    text = str(value or "").strip()
    return location_alias_lookup(location_resource_map).get(normalize_key(text), text)


def instructor_matches_container(offer: dict[str, Any], container: dict[str, Any]) -> bool:
    container_name = str(container.get("instructor_name") or "").strip()
    offer_name = str(offer.get("instructor_display_name") or "").strip()
    if not container_name:
        return True
    if normalize_key(container_name) == normalize_key(offer_name):
        return True
    return normalize_key(offer_name).startswith(normalize_key(container_name) + "_")


def location_matches_container(offer: dict[str, Any], container: dict[str, Any], location_resource_map: Any = None) -> bool:
    container_location = canonical_location(container.get("location_name"), location_resource_map)
    offer_location = canonical_location(offer.get("location"), location_resource_map)
    if container_location and offer_location and container_location != offer_location:
        return False
    return True


def appointment_day_id_for(container: dict[str, Any], target_date: Any) -> int | None:
    parsed = parse_date(target_date)
    first = parse_date(container.get("first_valid_date"))
    if not parsed or not first:
        return None
    try:
        return int(container["first_valid_appointmentDayId"]) + (parsed - first).days
    except (KeyError, TypeError, ValueError):
        return None


def date_in_container_range(offer: dict[str, Any], container: dict[str, Any]) -> bool:
    target = parse_date(offer.get("date"))
    first = parse_date(container.get("first_valid_date"))
    last = parse_date(container.get("last_valid_date"))
    day_id = appointment_day_id_for(container, offer.get("date"))
    if not target or not first or not last or day_id is None:
        return False
    try:
        first_id = int(container.get("first_valid_appointmentDayId", -1))
        last_id = int(container.get("last_valid_appointmentDayId", -1))
        first_invalid = container.get("first_invalid_appointmentDayId")
        if not (first <= target <= last and first_id <= day_id <= last_id):
            return False
        return first_invalid is None or day_id < int(first_invalid)
    except (TypeError, ValueError):
        return False


def appointment_container_rejection_reason(offer: dict[str, Any], containers_payload: Any, location_resource_map: Any = None) -> str | None:
    containers = active_containers(containers_payload)
    if not containers:
        return "no_matching_appointment_container"
    instructor_matches = [container for container in containers if instructor_matches_container(offer, container)]
    if not instructor_matches:
        return "missing_container_for_instructor"
    location_matches = [container for container in instructor_matches if location_matches_container(offer, container, location_resource_map)]
    if not location_matches:
        return "location_mismatch"
    if not any(date_in_container_range(offer, container) for container in location_matches):
        return "date_outside_container_range"
    return None


def base_rejection_reasons(offer: dict[str, Any], course: dict[str, Any] | None, policy: dict[str, Any], now: datetime) -> list[str]:
    reasons: list[str] = []
    course_id = str(offer.get("course_id") or "")
    family = str(offer.get("course_family") or "")
    enabled_ids = as_set(policy, "enabled_course_ids")
    disabled_ids = as_set(policy, "disabled_course_ids")
    enabled_families = as_set(policy, "enabled_course_families")
    disabled_families = as_set(policy, "disabled_course_families")

    if course_id in disabled_ids:
        reasons.append("course_id_disabled")
    if disabled_families and family in disabled_families:
        reasons.append("course_family_disabled")
    if enabled_ids and course_id not in enabled_ids:
        reasons.append("course_id_not_enabled")
    if enabled_families and family not in enabled_families:
        reasons.append("course_family_not_enabled")

    start = parse_offer_start(offer)
    if not start:
        reasons.append("unknown_offer_start")
    else:
        minute = start.strftime("%M")
        allowed_minutes = as_set(policy, "allowed_start_minutes")
        if allowed_minutes and minute not in allowed_minutes:
            reasons.append("start_minute_not_allowed")
        minimum_lead_hours = int(policy.get("minimum_lead_hours", 0) or 0)
        maximum_days_out = int(policy.get("maximum_days_out", 0) or 0)
        if start < now + timedelta(hours=minimum_lead_hours):
            reasons.append("inside_minimum_lead_time")
        if maximum_days_out and start > now + timedelta(days=maximum_days_out):
            reasons.append("outside_maximum_days_out")
        preferred = policy.get("preferred_start_times_by_family")
        if isinstance(preferred, dict):
            family_times = preferred.get(family)
            if isinstance(family_times, list) and family_times and start.strftime("%H:%M") not in {str(item) for item in family_times}:
                reasons.append("not_preferred_family_start_time")

    if not course:
        reasons.append("course_not_found")
    else:
        if policy.get("hide_online_only") is True and is_true(course.get("online_only")):
            reasons.append("online_only_hidden")
        if policy.get("hide_manual_only") is True and is_true(course.get("manual_only")):
            reasons.append("manual_only_hidden")
    if policy.get("hide_low_capacity_offers") is True:
        try:
            capacity = int(offer.get("capacity"))
        except (TypeError, ValueError):
            capacity = 0
        if capacity <= 1:
            reasons.append("low_capacity_hidden")
    return reasons


def apply_offer_limits(offers: list[dict[str, Any]], policy: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    hidden: list[dict[str, Any]] = []
    per_course_day: Counter[tuple[str, str]] = Counter()
    per_day: Counter[str] = Counter()
    max_per_course_day = int(policy.get("max_offers_per_course_per_day", 0) or 0)
    max_total_day = int(policy.get("max_total_offers_per_day", 0) or 0)

    for offer in sorted(offers, key=lambda item: (item.get("date", ""), item.get("start_time", ""), item.get("course_id", ""))):
        date = str(offer.get("date") or UNKNOWN)
        course_id = str(offer.get("course_id") or UNKNOWN)
        if max_total_day and per_day[date] >= max_total_day:
            hidden.append({"offer": offer, "reason_codes": ["max_total_offers_per_day_exceeded"]})
            continue
        if max_per_course_day and per_course_day[(date, course_id)] >= max_per_course_day:
            hidden.append({"offer": offer, "reason_codes": ["max_offers_per_course_per_day_exceeded"]})
            continue
        kept.append(offer)
        per_day[date] += 1
        per_course_day[(date, course_id)] += 1
    return kept, hidden


def filter_offers(dynamic_payload: Any, course_catalog: Any, policy: dict[str, Any], now: datetime | None = None, appointment_containers: Any = None, location_resource_map: Any = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    now = now or datetime.now()
    offers = dynamic_payload.get("offers", []) if isinstance(dynamic_payload, dict) else []
    if not isinstance(offers, list):
        offers = []
    courses = course_lookup(course_catalog)
    prelim_kept: list[dict[str, Any]] = []
    hidden: list[dict[str, Any]] = []
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        course = courses.get(str(offer.get("course_id")))
        reasons = base_rejection_reasons(offer, course, policy, now)
        if policy.get("require_confirmed_appointment_container") is True:
            container_reason = appointment_container_rejection_reason(offer, appointment_containers, location_resource_map)
            if container_reason:
                reasons.append(container_reason)
        if reasons:
            hidden.append({"offer": offer, "reason_codes": reasons})
        else:
            prelim_kept.append(offer)
    limited_kept, limit_hidden = apply_offer_limits(prelim_kept, policy)
    hidden.extend(limit_hidden)
    stats = {
        "total_dynamic_offers_read": len(offers),
        "confirmed_container_policy_enabled": policy.get("require_confirmed_appointment_container") is True,
        "appointment_container_backed_offers_kept": len(limited_kept) if policy.get("require_confirmed_appointment_container") is True else None,
        "offers_hidden_by_container_reason": dict(Counter(
            reason for item in hidden for reason in item["reason_codes"]
            if reason in {
                "no_matching_appointment_container",
                "missing_container_for_instructor",
                "location_mismatch",
                "date_outside_container_range",
            }
        ).most_common()),
        "public_sellable_offers_kept": len(limited_kept),
        "hidden_offers_by_reason": dict(Counter(reason for item in hidden for reason in item["reason_codes"]).most_common()),
        "offers_by_date": dict(sorted(Counter(str(offer.get("date") or UNKNOWN) for offer in limited_kept).items())),
        "offers_by_course_family": dict(sorted(Counter(str(offer.get("course_family") or UNKNOWN) for offer in limited_kept).items())),
    }
    return limited_kept, hidden, stats


def render_report(kept: list[dict[str, Any]], hidden: list[dict[str, Any]], stats: dict[str, Any], missing: dict[str, str]) -> str:
    lines = [
        "# Public Sellable Offers Preview Report",
        "",
        "This is a read-only sellability filter for dynamic offers. It did not modify public pages, Enrollware behavior, appointment URLs, Worker settings, generated HTML, or the original dynamic offer preview.",
        "",
        "## Summary",
        "",
        f"- Total dynamic offers read: {stats['total_dynamic_offers_read']}",
        f"- Confirmed-container policy enabled: {stats['confirmed_container_policy_enabled']}",
        f"- Offers kept due to container support: {stats['appointment_container_backed_offers_kept']}",
        f"- Public sellable offers kept: {stats['public_sellable_offers_kept']}",
        "",
        "## Files Missing Or Unreadable",
        "",
    ]
    if missing:
        lines.extend(f"- `{name}`: {reason}" for name, reason in sorted(missing.items()))
    else:
        lines.append("- None")
    lines.extend(["", "## Hidden Offers By Appointment Container Reason", ""])
    if stats.get("offers_hidden_by_container_reason"):
        lines.extend(f"- `{reason}`: {count}" for reason, count in stats["offers_hidden_by_container_reason"].items())
    else:
        lines.append("- None")
    lines.extend(["", "## Hidden Offers By Reason", ""])
    if stats["hidden_offers_by_reason"]:
        lines.extend(f"- `{reason}`: {count}" for reason, count in stats["hidden_offers_by_reason"].items())
    else:
        lines.append("- None")
    lines.extend(["", "## Offers By Date", ""])
    if stats["offers_by_date"]:
        lines.extend(f"- `{date}`: {count}" for date, count in stats["offers_by_date"].items())
    else:
        lines.append("- None")
    lines.extend(["", "## Offers By Course Family", ""])
    if stats["offers_by_course_family"]:
        lines.extend(f"- `{family}`: {count}" for family, count in stats["offers_by_course_family"].items())
    else:
        lines.append("- None")
    lines.extend(["", "## Top 50 Sellable Examples", ""])
    if kept:
        lines.extend(["| Date | Time | Course | Family | Instructor |", "| --- | --- | --- | --- | --- |"])
        for offer in kept[:50]:
            lines.append(
                f"| {offer.get('date', UNKNOWN)} | {offer.get('start_time', UNKNOWN)}-{offer.get('end_time', UNKNOWN)} | "
                f"{offer.get('course_title', UNKNOWN)} | {offer.get('course_family', UNKNOWN)} | {offer.get('instructor_display_name', UNKNOWN)} |"
            )
    else:
        lines.append("- No sellable offers kept.")
    lines.extend([
        "",
        "## Next Safest Step",
        "",
        "- Brian should review whether the remaining volume per day/course is appropriate before any public UI or appointment bridge consumes these filtered offers.",
        "",
    ])
    return "\n".join(lines)


def run() -> dict[str, Any]:
    dynamic_payload, dynamic_error = read_json(DYNAMIC_OFFERS_PATH)
    course_catalog, course_error = read_json(COURSE_CATALOG_PATH)
    appointment_containers, containers_error = read_json(APPOINTMENT_CONTAINERS_PATH)
    location_resource_map, location_map_error = read_json(LOCATION_RESOURCE_MAP_PATH)
    policy, policy_error = read_json(PUBLIC_OFFER_POLICY_PATH)
    missing = {}
    if dynamic_error:
        missing["dynamic_offers_preview"] = dynamic_error
    if course_error:
        missing["course_catalog"] = course_error
    if policy_error:
        missing["public_offer_policy"] = policy_error
    if containers_error:
        missing["appointment_containers"] = containers_error
    if location_map_error:
        missing["location_resource_map"] = location_map_error
    if not isinstance(policy, dict):
        policy = {}
    kept, hidden, stats = filter_offers(dynamic_payload or {}, course_catalog or {}, policy, appointment_containers=appointment_containers or {}, location_resource_map=location_resource_map or {})
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    preview = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "public_site_affected": False,
        "enrollware_called": False,
        "google_calendar_called": False,
        "source_dynamic_offers": str(DYNAMIC_OFFERS_PATH),
        "source_policy": str(PUBLIC_OFFER_POLICY_PATH),
        "source_appointment_containers": str(APPOINTMENT_CONTAINERS_PATH),
        "source_location_resource_map": str(LOCATION_RESOURCE_MAP_PATH),
        "stats": stats,
        "offers": kept,
        "hidden_offers": hidden,
    }
    SELLABLE_OFFERS_PATH.write_text(json.dumps(preview, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(kept, hidden, stats, missing), encoding="utf-8")
    return {
        "stats": stats,
        "missing": missing,
        "output_paths": [SELLABLE_OFFERS_PATH, REPORT_PATH],
    }


def main() -> int:
    result = run()
    print("Public sellable offers filter complete (READ ONLY).")
    print("No public pages, Enrollware behavior, appointment URLs, Worker settings, generated HTML, or original dynamic offers were changed.")
    print("")
    print(f"Total dynamic offers read: {result['stats']['total_dynamic_offers_read']}")
    print(f"Confirmed-container policy enabled: {result['stats']['confirmed_container_policy_enabled']}")
    print(f"Offers kept due to container support: {result['stats']['appointment_container_backed_offers_kept']}")
    print(f"Public sellable offers kept: {result['stats']['public_sellable_offers_kept']}")
    print("")
    print("Output files:")
    for path in result["output_paths"]:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
