from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime, time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
PUBLIC_SELLABLE_OFFERS_PATH = AUDIT_DIR / "public_sellable_offers_preview.json"
SEED_POLICY_PATH = ROOT / "data" / "config" / "seed_strategy_policy.json"
COURSE_CATALOG_PATH = ROOT / "data" / "config" / "course_catalog.json"
APPOINTMENT_CONTAINERS_PATH = ROOT / "data" / "inventory" / "appointment_containers.json"
LOCATION_RESOURCE_MAP_PATH = ROOT / "data" / "config" / "location_resource_map.json"
SEEDS_PATH = AUDIT_DIR / "schedule_seeds_preview.json"
REPORT_PATH = AUDIT_DIR / "schedule_seeds_report.md"
AMY_STACK_FILL_PATH = AUDIT_DIR / "amy_stack_fill_candidates.json"
AMY_STRATEGY_REPORT_PATH = AUDIT_DIR / "amy_protected_pilot_strategy_report.md"
UNKNOWN = "UNKNOWN"
AHA_BLS_INITIAL_COURSE_ID = "209806"
AHA_BLS_RENEWAL_COURSE_ID = "359474"
AHA_BLS_HEARTCODE_COURSE_ID = "210549"


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
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%H:%M").time()
    except ValueError:
        return None


def parse_date(value: Any) -> date | None:
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def time_band(start_time: str) -> str:
    parsed = parse_time(start_time)
    if not parsed:
        return "unknown"
    if parsed < time(12, 0):
        return "morning"
    if parsed < time(17, 0):
        return "afternoon"
    return "evening"


def course_priority(offer: dict[str, Any], policy: dict[str, Any]) -> tuple[int, int, str]:
    family = str(offer.get("course_family") or UNKNOWN)
    band = time_band(str(offer.get("start_time") or ""))
    family_priority = policy.get("family_priority_by_time_band", {})
    preferred_families = family_priority.get(band, []) if isinstance(family_priority, dict) else []
    try:
        family_rank = preferred_families.index(family)
    except ValueError:
        family_rank = 999
    title = str(offer.get("course_title") or "")
    terms = policy.get("course_title_priority_terms", [])
    title_rank = 999
    if isinstance(terms, list):
        for index, term in enumerate(terms):
            if str(term).lower() in title.lower():
                title_rank = index
                break
    return family_rank, title_rank, title


def preferred_start_rank(offer: dict[str, Any], policy: dict[str, Any]) -> tuple[int, str]:
    family = str(offer.get("course_family") or UNKNOWN)
    start = str(offer.get("start_time") or UNKNOWN)
    preferred = policy.get("preferred_start_times_by_family", {})
    starts = preferred.get(family, []) if isinstance(preferred, dict) else []
    if isinstance(starts, list) and starts:
        try:
            return starts.index(start), start
        except ValueError:
            return 999, start
    return 0, start


def bls_variant_balance_rank(offer: dict[str, Any], policy: dict[str, Any], date_index: int) -> tuple[int, str]:
    balance = policy.get("bls_seed_variant_balance", {})
    if not isinstance(balance, dict) or balance.get("enabled") is not True:
        return (0, str(offer.get("course_id") or UNKNOWN))
    if str(offer.get("course_family") or "") != "BLS":
        return (0, str(offer.get("course_id") or UNKNOWN))
    course_id = str(offer.get("course_id") or UNKNOWN)
    if balance.get("mode") == "alternate_initial_renewal_by_bls_date":
        order = balance.get("course_id_order", [AHA_BLS_INITIAL_COURSE_ID, AHA_BLS_RENEWAL_COURSE_ID])
        if not isinstance(order, list) or not order:
            order = [AHA_BLS_INITIAL_COURSE_ID, AHA_BLS_RENEWAL_COURSE_ID]
        preferred_course_id = str(order[date_index % len(order)])
        if course_id == preferred_course_id:
            return (0, course_id)
        if course_id in {str(item) for item in order}:
            return (1, course_id)
        if course_id == AHA_BLS_HEARTCODE_COURSE_ID:
            return (2, course_id)
    return (3, course_id)


def family_goal(policy: dict[str, Any], family: str) -> tuple[int, bool, str | None]:
    goals = policy.get("required_seed_mix_by_date", {})
    if not isinstance(goals, dict):
        return 0, False, None
    raw = goals.get(family)
    if isinstance(raw, int):
        return raw, True, None
    if not isinstance(raw, dict):
        return 0, False, None
    try:
        count = int(raw.get("count", 0) or 0)
    except (TypeError, ValueError):
        count = 0
    return count, raw.get("required") is True, raw.get("not_before")


def max_family_count(policy: dict[str, Any], family: str) -> int:
    raw = policy.get("max_seeds_per_family_per_date", {})
    if isinstance(raw, dict):
        try:
            return int(raw.get(family, 0) or 0)
        except (TypeError, ValueError):
            return 0
    try:
        return int(raw or 0)
    except (TypeError, ValueError):
        return 0


def violates_family_not_before(offer: dict[str, Any], not_before: str | None) -> bool:
    if not not_before:
        return False
    cutoff = parse_time(not_before)
    start = parse_time(offer.get("start_time"))
    return cutoff is not None and start is not None and start < cutoff


def variant_key(offer: dict[str, Any]) -> tuple[str, str]:
    return (str(offer.get("date") or UNKNOWN), str(offer.get("start_time") or UNKNOWN))


def parse_datetime(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def windows_overlap(start_a: Any, end_a: Any, start_b: Any, end_b: Any) -> bool:
    parsed_start_a = parse_datetime(start_a)
    parsed_end_a = parse_datetime(end_a)
    parsed_start_b = parse_datetime(start_b)
    parsed_end_b = parse_datetime(end_b)
    if not parsed_start_a or not parsed_end_a or not parsed_start_b or not parsed_end_b:
        return False
    return parsed_start_a < parsed_end_b and parsed_start_b < parsed_end_a


def reject(hidden: list[dict[str, Any]], offer: dict[str, Any], reason: str, message: str) -> None:
    hidden.append({
        "source_offer_id": offer.get("offer_id", UNKNOWN),
        "date": offer.get("date", UNKNOWN),
        "start_time": offer.get("start_time", UNKNOWN),
        "course_title": offer.get("course_title", UNKNOWN),
        "course_family": offer.get("course_family", UNKNOWN),
        "instructor_display_name": offer.get("instructor_display_name", UNKNOWN),
        "source_availability_window": offer.get("source_availability_window", UNKNOWN),
        "reason_code": reason,
        "message": message,
    })


def normalize_key(value: Any) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def courses_by_id(course_catalog: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(course_catalog, dict) or not isinstance(course_catalog.get("courses"), list):
        return {}
    return {
        str(course.get("course_id")): course
        for course in course_catalog["courses"]
        if isinstance(course, dict) and course.get("course_id")
    }


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


def container_backing_reason(offer: dict[str, Any], course_catalog: Any, containers_payload: Any, location_resource_map: Any = None) -> str | None:
    courses = courses_by_id(course_catalog)
    course = courses.get(str(offer.get("course_id") or UNKNOWN))
    if not course:
        return "course_not_found"
    if course.get("appointment_allowed") is not True:
        return "course_not_appointment_allowed"
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


def filter_container_backed_offers(
    offers: list[dict[str, Any]],
    course_catalog: Any,
    containers_payload: Any,
    hidden: list[dict[str, Any]],
    location_resource_map: Any = None,
) -> list[dict[str, Any]]:
    if course_catalog is None and containers_payload is None:
        return offers
    kept = []
    for offer in offers:
        reason = container_backing_reason(offer, course_catalog, containers_payload, location_resource_map)
        if reason:
            reject(hidden, offer, reason, "Offer cannot match a known active appointment container.")
            continue
        kept.append(offer)
    return kept


def violates_amy_advanced_rule(offer: dict[str, Any], policy: dict[str, Any]) -> bool:
    instructor = str(offer.get("instructor_display_name") or "")
    family = str(offer.get("course_family") or "")
    advanced = set(policy.get("advanced_families", []))
    cutoff = parse_time(policy.get("amy_advanced_not_before"))
    start = parse_time(offer.get("start_time"))
    return instructor == "Amy Arnold" and family in advanced and cutoff is not None and start is not None and start < cutoff


def title_matches_any(title: str, terms: list[Any]) -> bool:
    lowered = title.lower()
    return any(str(term).lower() in lowered for term in terms)


def classify_amy_protected_pilot_offer(offer: dict[str, Any], policy: dict[str, Any]) -> str | None:
    if policy.get("amy_mode") != "protected_pilot":
        return None
    if str(offer.get("instructor_display_name") or "") != "Amy Arnold":
        return None
    family = str(offer.get("course_family") or "")
    if family not in set(policy.get("advanced_families", [])):
        return None
    title = str(offer.get("course_title") or "")
    start = str(offer.get("start_time") or "")
    if title_matches_any(title, policy.get("amy_heartcode_stack_fill_courses", [])):
        if start >= str(policy.get("amy_heartcode_stack_fill_start") or "13:00"):
            return "amy_stack_fill_candidate"
        return "amy_stack_fill_before_allowed_start"
    if title_matches_any(title, policy.get("amy_advanced_public_seed_courses", [])):
        if start == str(policy.get("amy_advanced_seed_start") or "14:00"):
            return None
        return "amy_advanced_seed_not_at_protected_start"
    return "amy_course_not_in_protected_pilot_allowlist"


def seed_from_offer(offer: dict[str, Any]) -> dict[str, Any]:
    start_time = str(offer.get("start_time") or UNKNOWN)
    start_minute = start_time[-2:] if len(start_time) >= 2 else UNKNOWN
    quarter_hour_start = start_minute in {"15", "45"}
    return {
        "seed_id": f"seed-{offer.get('offer_id', UNKNOWN)}",
        "source_offer_id": offer.get("offer_id", UNKNOWN),
        "date": offer.get("date", UNKNOWN),
        "start_time": start_time,
        "start_minute": start_minute,
        "quarter_hour_start": quarter_hour_start,
        "selection_timing_note": "quarter_hour_start_allowed_for_stack_fit" if quarter_hour_start else "standard_hour_or_half_hour_start",
        "end_time": offer.get("end_time", UNKNOWN),
        "appointment_display_start": offer.get("appointment_display_start", UNKNOWN),
        "appointment_display_end": offer.get("appointment_display_end", UNKNOWN),
        "scheduler_consumption_start": offer.get("scheduler_consumption_start", UNKNOWN),
        "scheduler_consumption_end": offer.get("scheduler_consumption_end", UNKNOWN),
        "scheduler_consumption_minutes": offer.get("scheduler_consumption_minutes", UNKNOWN),
        "setup_buffer_minutes": offer.get("setup_buffer_minutes", UNKNOWN),
        "cleanup_buffer_minutes": offer.get("cleanup_buffer_minutes", UNKNOWN),
        "instructor_lock_start": offer.get("instructor_lock_start", UNKNOWN),
        "instructor_lock_end": offer.get("instructor_lock_end", UNKNOWN),
        "resource_lock_start": offer.get("resource_lock_start", UNKNOWN),
        "resource_lock_end": offer.get("resource_lock_end", UNKNOWN),
        "course_id": offer.get("course_id", UNKNOWN),
        "course_title": offer.get("course_title", UNKNOWN),
        "course_family": offer.get("course_family", UNKNOWN),
        "duration_minutes": offer.get("duration_minutes", UNKNOWN),
        "capacity": offer.get("capacity", UNKNOWN),
        "instructor_person_id": offer.get("instructor_person_id", UNKNOWN),
        "instructor_display_name": offer.get("instructor_display_name", UNKNOWN),
        "instructor_assignment_mode": offer.get("instructor_assignment_mode", UNKNOWN),
        "location": offer.get("location", UNKNOWN),
        "resource": offer.get("resource", UNKNOWN),
        "source_location": offer.get("source_location", UNKNOWN),
        "offer_location": offer.get("offer_location", offer.get("location", UNKNOWN)),
        "source_availability_window": offer.get("source_availability_window", UNKNOWN),
        "confidence": offer.get("confidence", UNKNOWN),
        "reasons": [
            "public_sellable_offer",
            "selected_as_stack_seed",
            "read_only_seed_preview_not_public_menu",
        ],
    }


def select_seeds(public_preview: Any, policy: dict[str, Any], course_catalog: Any = None, containers_payload: Any = None, location_resource_map: Any = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    offers = public_preview.get("offers", []) if isinstance(public_preview, dict) else []
    if not isinstance(offers, list):
        offers = []
    hidden_source_offers = []
    if isinstance(public_preview, dict) and isinstance(public_preview.get("hidden_offers"), list):
        hidden_source_offers = [
            item.get("offer")
            for item in public_preview["hidden_offers"]
            if isinstance(item, dict) and isinstance(item.get("offer"), dict)
        ]
    input_offers_read = len(offers)
    hidden: list[dict[str, Any]] = []
    amy_stack_fill_candidates: list[dict[str, Any]] = []
    seen_stack_fill_ids: set[str] = set()
    for offer in [*offers, *hidden_source_offers]:
        if not isinstance(offer, dict):
            continue
        if classify_amy_protected_pilot_offer(offer, policy) == "amy_stack_fill_candidate":
            source_offer_id = str(offer.get("offer_id", UNKNOWN))
            if source_offer_id in seen_stack_fill_ids:
                continue
            seen_stack_fill_ids.add(source_offer_id)
            amy_stack_fill_candidates.append({
                "source_offer_id": offer.get("offer_id", UNKNOWN),
                "date": offer.get("date", UNKNOWN),
                "start_time": offer.get("start_time", UNKNOWN),
                "end_time": offer.get("end_time", UNKNOWN),
                "course_id": offer.get("course_id", UNKNOWN),
                "course_title": offer.get("course_title", UNKNOWN),
                "course_family": offer.get("course_family", UNKNOWN),
                "instructor_display_name": offer.get("instructor_display_name", UNKNOWN),
                "location": offer.get("location", UNKNOWN),
                "resource": offer.get("resource", UNKNOWN),
                "source_availability_window": offer.get("source_availability_window", UNKNOWN),
                "reason": "stack_fill_candidate_not_public_seed",
            })
    container_filter_enabled = course_catalog is not None or containers_payload is not None
    offers = filter_container_backed_offers([offer for offer in offers if isinstance(offer, dict)], course_catalog, containers_payload, hidden, location_resource_map)
    container_backed_kept = len(offers)
    candidates: list[dict[str, Any]] = []
    amy_violations = 0
    amy_protected_hidden: Counter[str] = Counter()
    for offer in offers:
        amy_classification = classify_amy_protected_pilot_offer(offer, policy)
        if amy_classification == "amy_stack_fill_candidate":
            amy_protected_hidden[amy_classification] += 1
            reject(hidden, offer, amy_classification, "Amy HeartCode/skills offer is stack-fill only during protected pilot.")
            continue
        if amy_classification:
            amy_protected_hidden[amy_classification] += 1
            reject(hidden, offer, amy_classification, "Amy offer does not satisfy protected pilot public-seed rules.")
            continue
        if violates_amy_advanced_rule(offer, policy):
            amy_violations += 1
            reject(hidden, offer, "amy_advanced_before_1300", "Amy ACLS/PALS seed starts before 13:00.")
            continue
        candidates.append(offer)

    by_date_family: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for offer in candidates:
        by_date_family[(str(offer.get("date") or UNKNOWN), str(offer.get("course_family") or UNKNOWN))].append(offer)

    max_per_window = int(policy.get("max_seeds_per_instructor_window", 1) or 1)
    max_per_date = int(policy.get("max_seeds_per_date", 0) or 0)
    avoid_same_start = policy.get("avoid_same_start_time_per_date") is True
    allow_same_time_variants = policy.get("allow_multiple_course_variants_same_time") is True
    date_counts: Counter[str] = Counter()
    family_date_counts: Counter[tuple[str, str]] = Counter()
    window_counts: Counter[tuple[str, str, str]] = Counter()
    date_start_counts: Counter[tuple[str, str]] = Counter()
    lane_locks: list[dict[str, Any]] = []
    selected_variants: set[tuple[str, str]] = set()
    seeds: list[dict[str, Any]] = []
    mix_status: dict[str, dict[str, Any]] = {}

    dates = sorted({date for date, _family in by_date_family})
    bls_seed_date_index = {
        date: index
        for index, date in enumerate(sorted(date for date, family in by_date_family if family == "BLS"))
    }
    goal_families = list((policy.get("required_seed_mix_by_date") or {}).keys())
    for date in dates:
        mix_status[date] = {}
        for family in goal_families:
            target, required, not_before = family_goal(policy, family)
            if target <= 0:
                continue
            max_for_family = max_family_count(policy, family) or target
            target = min(target, max_for_family)
            group = by_date_family.get((date, family), [])
            group = [
                offer for offer in group
                if not violates_family_not_before(offer, not_before)
            ]
            group = sorted(
                group,
                key=lambda offer: (
                    preferred_start_rank(offer, policy),
                    bls_variant_balance_rank(offer, policy, bls_seed_date_index.get(date, 0)),
                    course_priority(offer, policy),
                    offer.get("start_time", ""),
                    offer.get("offer_id", ""),
                ),
            )
            selected_count = 0
            blocked_reasons: Counter[str] = Counter()
            for offer in group:
                if selected_count >= target:
                    reject(hidden, offer, "family_mix_target_already_met", "Family mix target already met for this date.")
                    continue
                start = str(offer.get("start_time") or UNKNOWN)
                window_key = (
                    str(offer.get("date") or UNKNOWN),
                    str(offer.get("instructor_person_id") or offer.get("instructor_display_name") or UNKNOWN),
                    str(offer.get("source_availability_window") or UNKNOWN),
                )
                if max_per_date and date_counts[date] >= max_per_date:
                    blocked_reasons["max_seeds_per_date_exceeded"] += 1
                    reject(hidden, offer, "max_seeds_per_date_exceeded", "Date already reached seed limit.")
                    continue
                if max_per_window and window_counts[window_key] >= max_per_window:
                    blocked_reasons["max_seeds_per_instructor_window_exceeded"] += 1
                    reject(hidden, offer, "max_seeds_per_instructor_window_exceeded", "Instructor/window already reached seed limit.")
                    continue
                if max_for_family and family_date_counts[(date, family)] >= max_for_family:
                    blocked_reasons["max_seeds_per_family_per_date_exceeded"] += 1
                    reject(hidden, offer, "max_seeds_per_family_per_date_exceeded", "Family already reached date seed limit.")
                    continue
                if avoid_same_start and date_start_counts[(date, start)] > 0:
                    blocked_reasons["same_start_time_already_seeded"] += 1
                    reject(hidden, offer, "same_start_time_already_seeded", "Avoiding multiple seeds at the same start time on the same date.")
                    continue
                if not allow_same_time_variants and variant_key(offer) in selected_variants:
                    blocked_reasons["same_time_variant_already_seeded"] += 1
                    reject(hidden, offer, "same_time_variant_already_seeded", "Avoiding multiple course variants at the same time.")
                    continue
                lane_key = (
                    str(offer.get("date") or UNKNOWN),
                    str(offer.get("instructor_person_id") or offer.get("instructor_display_name") or UNKNOWN),
                    normalize_key(offer.get("resource") or offer.get("location") or UNKNOWN),
                )
                conflicting_lock = next((
                    lock for lock in lane_locks
                    if lock["lane_key"] == lane_key and windows_overlap(
                        lock["start"],
                        lock["end"],
                        offer.get("scheduler_consumption_start") or offer.get("appointment_display_start"),
                        offer.get("scheduler_consumption_end") or offer.get("appointment_display_end"),
                    )
                ), None)
                if conflicting_lock:
                    blocked_reasons["scheduler_consumption_window_overlap"] += 1
                    reject(hidden, offer, "scheduler_consumption_window_overlap", "Offer overlaps a previously selected scheduler consumption window in the same instructor/resource lane.")
                    continue
                seeds.append(seed_from_offer(offer))
                lane_locks.append({
                    "lane_key": lane_key,
                    "start": offer.get("scheduler_consumption_start") or offer.get("appointment_display_start"),
                    "end": offer.get("scheduler_consumption_end") or offer.get("appointment_display_end"),
                    "source_offer_id": offer.get("offer_id", UNKNOWN),
                })
                selected_count += 1
                date_counts[date] += 1
                family_date_counts[(date, family)] += 1
                window_counts[window_key] += 1
                date_start_counts[(date, start)] += 1
                selected_variants.add(variant_key(offer))
            available_after_rules = len(group)
            mix_status[date][family] = {
                "target": target,
                "required": required,
                "selected": selected_count,
                "met": selected_count >= target or (not required and available_after_rules == 0),
                "available_after_hard_rules": available_after_rules,
                "blocked_reasons": dict(blocked_reasons),
            }
            if selected_count < target and available_after_rules == 0:
                reason = "optional_mix_not_available" if not required else "required_mix_not_available"
                placeholder = {
                    "offer_id": f"{date}-{family}-mix-placeholder",
                    "date": date,
                    "start_time": UNKNOWN,
                    "course_title": f"{family} seed",
                    "course_family": family,
                    "instructor_display_name": UNKNOWN,
                    "source_availability_window": UNKNOWN,
                }
                reject(hidden, placeholder, reason, "No source offer satisfied this family mix goal.")

    selected_offer_ids = {seed["source_offer_id"] for seed in seeds}
    for offer in candidates:
        if offer.get("offer_id") not in selected_offer_ids and not any(item.get("source_offer_id") == offer.get("offer_id") for item in hidden):
            reject(hidden, offer, "not_selected_by_seed_mix", "Offer was valid but not selected by the daily seed mix strategy.")

    stats = {
        "input_offers_read": input_offers_read,
        "appointment_container_filter_enabled": container_filter_enabled,
        "appointment_container_backed_offers_kept": container_backed_kept,
        "offers_hidden_by_container_reason": dict(Counter(
            item["reason_code"] for item in hidden
            if item["reason_code"] in {
                "no_matching_appointment_container",
                "missing_container_for_instructor",
                "location_mismatch",
                "date_outside_container_range",
                "course_not_appointment_allowed",
                "course_not_found",
            }
        ).most_common()),
        "seeds_selected": len(seeds),
        "offers_hidden_by_strategy_reason": dict(Counter(item["reason_code"] for item in hidden).most_common()),
        "amy_advanced_course_violations_removed": amy_violations,
        "amy_mode": policy.get("amy_mode", "off"),
        "amy_protected_pilot_hidden_by_reason": dict(amy_protected_hidden),
        "amy_stack_fill_candidates_found": len(amy_stack_fill_candidates),
        "amy_stack_fill_candidates": amy_stack_fill_candidates,
        "seeds_by_date": dict(sorted(Counter(seed["date"] for seed in seeds).items())),
        "seeds_by_family": dict(sorted(Counter(seed["course_family"] for seed in seeds).items())),
        "quarter_hour_seeds_selected": sum(1 for seed in seeds if seed.get("quarter_hour_start") is True),
        "seeds_by_start_minute": dict(sorted(Counter(seed.get("start_minute", UNKNOWN) for seed in seeds).items())),
        "mix_goal_status_by_date": mix_status,
    }
    return seeds, hidden, stats


def render_report(seeds: list[dict[str, Any]], hidden: list[dict[str, Any]], stats: dict[str, Any], missing: dict[str, str]) -> str:
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for seed in seeds:
        by_date[str(seed.get("date") or UNKNOWN)].append(seed)
    lines = [
        "# Schedule Seeds Preview Report",
        "",
        "This is a read-only seed strategy preview. Seeds are stack seeds, not a final public menu. No public pages, Enrollware calls, appointments, appointment URLs, Worker settings, or docs output were changed.",
        "",
        "## Summary",
        "",
        f"- Input offers read: {stats['input_offers_read']}",
        f"- Appointment-container filter enabled: {stats['appointment_container_filter_enabled']}",
        f"- Appointment-container-backed offers kept: {stats['appointment_container_backed_offers_kept']}",
        f"- Seeds selected: {stats['seeds_selected']}",
        f"- Amy advanced-course violations removed: {stats['amy_advanced_course_violations_removed']}",
        f"- Amy mode: {stats.get('amy_mode', 'off')}",
        f"- Amy stack-fill candidates found: {stats.get('amy_stack_fill_candidates_found', 0)}",
        f"- Seeds by date: {stats['seeds_by_date']}",
        f"- Seeds by family: {stats['seeds_by_family']}",
        f"- Seeds by start minute: {stats.get('seeds_by_start_minute', {})}",
        f"- Quarter-hour seeds selected: {stats.get('quarter_hour_seeds_selected', 0)}",
        "",
        "## Missing Inputs",
        "",
    ]
    if missing:
        lines.extend(f"- `{name}`: {reason}" for name, reason in sorted(missing.items()))
    else:
        lines.append("- None")
    lines.extend(["", "## Offers Hidden By Strategy Reason", ""])
    if stats["offers_hidden_by_strategy_reason"]:
        lines.extend(f"- `{reason}`: {count}" for reason, count in stats["offers_hidden_by_strategy_reason"].items())
    else:
        lines.append("- None")
    lines.extend(["", "## Amy Protected Pilot Hidden By Reason", ""])
    if stats.get("amy_protected_pilot_hidden_by_reason"):
        lines.extend(f"- `{reason}`: {count}" for reason, count in stats["amy_protected_pilot_hidden_by_reason"].items())
    else:
        lines.append("- None")
    lines.extend(["", "## Offers Hidden By Appointment Container Reason", ""])
    if stats.get("offers_hidden_by_container_reason"):
        lines.extend(f"- `{reason}`: {count}" for reason, count in stats["offers_hidden_by_container_reason"].items())
    else:
        lines.append("- None")
    lines.extend(["", "## Mix Goal Status By Date", ""])
    mix_status = stats.get("mix_goal_status_by_date", {})
    if mix_status:
        for date in sorted(mix_status):
            lines.extend([f"### {date}", "", "| Family | Target | Selected | Required | Met | Available After Hard Rules |", "| --- | ---: | ---: | --- | --- | ---: |"])
            for family in sorted(mix_status[date]):
                item = mix_status[date][family]
                lines.append(
                    f"| {family} | {item.get('target', 0)} | {item.get('selected', 0)} | "
                    f"{item.get('required', False)} | {item.get('met', False)} | {item.get('available_after_hard_rules', 0)} |"
                )
            lines.append("")
    else:
        lines.append("- No mix goals evaluated.")
    lines.extend(["", "## Examples By Date", ""])
    if by_date:
        for date in sorted(by_date):
            lines.extend([f"### {date}", "", "| Time | Course | Family | Instructor | Source Offer |", "| --- | --- | --- | --- | --- |"])
            for seed in sorted(by_date[date], key=lambda item: (item["start_time"], item["course_family"], item["course_title"])):
                lines.append(
                    f"| {seed['start_time']}-{seed['end_time']} | {seed['course_title']} | {seed['course_family']} | "
                    f"{seed['instructor_display_name']} | `{seed['source_offer_id']}` |"
                )
            lines.append("")
    else:
        lines.append("- No seeds selected.")
    lines.extend(["", "## Quarter-Hour Stack Fit Notes", ""])
    quarter_hour_seeds = [seed for seed in seeds if seed.get("quarter_hour_start") is True]
    if quarter_hour_seeds:
        lines.extend(["| Date | Time | Course | Note |", "| --- | --- | --- | --- |"])
        for seed in quarter_hour_seeds:
            lines.append(f"| {seed['date']} | {seed['start_time']} | {seed['course_title']} | {seed.get('selection_timing_note', UNKNOWN)} |")
    else:
        lines.append("- No `:15` or `:45` seeds were selected in this run. They remain allowed and can win when they create a better stack.")
    lines.extend([
        "## Next Step",
        "",
        "- Build a deterministic appointment URL preview from these seeds without creating appointments or changing public pages.",
        "",
    ])
    return "\n".join(lines)


def render_amy_strategy_report(stats: dict[str, Any]) -> str:
    lines = [
        "# Amy Protected Pilot Strategy Report",
        "",
        "Read-only strategy report. Amy protected-pilot logic does not publish offers, create appointments, call Enrollware, change public pages, or enable Worker routes.",
        "",
        "## Summary",
        "",
        f"- Amy mode: {stats.get('amy_mode', 'off')}",
        f"- Amy protected pilot seeds selected: {sum(1 for date_items in stats.get('mix_goal_status_by_date', {}).values() for _family, item in date_items.items() if item.get('selected', 0) and _family in {'ACLS', 'PALS'})}",
        f"- Amy stack-fill candidates found: {stats.get('amy_stack_fill_candidates_found', 0)}",
        "",
        "## Hidden By Protected Pilot Reason",
        "",
    ]
    hidden = stats.get("amy_protected_pilot_hidden_by_reason", {})
    if hidden:
        lines.extend(f"- `{reason}`: {count}" for reason, count in hidden.items())
    else:
        lines.append("- None")
    candidates = stats.get("amy_stack_fill_candidates", [])
    lines.extend(["", "## Stack-Fill Candidates", ""])
    if candidates:
        lines.extend(["| Date | Time | Course | Location | Source Offer |", "| --- | --- | --- | --- | --- |"])
        for item in candidates:
            lines.append(
                f"| {item.get('date', UNKNOWN)} | {item.get('start_time', UNKNOWN)}-{item.get('end_time', UNKNOWN)} | "
                f"{item.get('course_title', UNKNOWN)} | {item.get('location', UNKNOWN)} | `{item.get('source_offer_id', UNKNOWN)}` |"
            )
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Rule",
        "",
        "- Amy ACLS/PALS Initial/Renewal can become protected pilot public seeds only at 14:00.",
        "- Amy HeartCode/skills at or after 13:00 are stack-fill candidates only and are not publicly exposed yet.",
        "- Existing Enrollware/session occupancy remains a hard blocker upstream in dynamic offer generation.",
        "",
    ])
    return "\n".join(lines)


def run() -> dict[str, Any]:
    public_preview, public_error = read_json(PUBLIC_SELLABLE_OFFERS_PATH)
    policy, policy_error = read_json(SEED_POLICY_PATH)
    course_catalog, course_error = read_json(COURSE_CATALOG_PATH)
    containers_payload, containers_error = read_json(APPOINTMENT_CONTAINERS_PATH)
    location_resource_map, location_map_error = read_json(LOCATION_RESOURCE_MAP_PATH)
    missing = {}
    if public_error:
        missing["public_sellable_offers_preview"] = public_error
    if policy_error:
        missing["seed_strategy_policy"] = policy_error
    if course_error:
        missing["course_catalog"] = course_error
    if containers_error:
        missing["appointment_containers"] = containers_error
    if location_map_error:
        missing["location_resource_map"] = location_map_error
    if not isinstance(policy, dict):
        policy = {}
    seeds, hidden, stats = select_seeds(public_preview or {}, policy, course_catalog or {}, containers_payload or {}, location_resource_map or {})
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    preview = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "public_site_affected": False,
        "enrollware_called": False,
        "appointments_created": False,
        "appointment_urls_changed": False,
        "source_public_sellable_offers": str(PUBLIC_SELLABLE_OFFERS_PATH),
        "source_policy": str(SEED_POLICY_PATH),
        "source_course_catalog": str(COURSE_CATALOG_PATH),
        "source_appointment_containers": str(APPOINTMENT_CONTAINERS_PATH),
        "source_location_resource_map": str(LOCATION_RESOURCE_MAP_PATH),
        "stats": stats,
        "seeds": seeds,
        "hidden_offers": hidden,
    }
    SEEDS_PATH.write_text(json.dumps(preview, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(seeds, hidden, stats, missing), encoding="utf-8")
    AMY_STACK_FILL_PATH.write_text(json.dumps({
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "public_site_affected": False,
        "stack_fill_publicly_exposed": False,
        "amy_mode": stats.get("amy_mode"),
        "candidates": stats.get("amy_stack_fill_candidates", []),
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    AMY_STRATEGY_REPORT_PATH.write_text(render_amy_strategy_report(stats), encoding="utf-8")
    return {
        "stats": stats,
        "missing": missing,
        "output_paths": [SEEDS_PATH, REPORT_PATH, AMY_STACK_FILL_PATH, AMY_STRATEGY_REPORT_PATH],
    }


def main() -> int:
    result = run()
    print("Schedule seed selection complete (READ ONLY).")
    print("No public pages, Enrollware calls, appointments, appointment URLs, Worker settings, docs output, or public menus were changed.")
    print("")
    print(f"Input offers read: {result['stats']['input_offers_read']}")
    print(f"Appointment-container-backed offers kept: {result['stats']['appointment_container_backed_offers_kept']}")
    print(f"Seeds selected: {result['stats']['seeds_selected']}")
    print(f"Amy advanced-course violations removed: {result['stats']['amy_advanced_course_violations_removed']}")
    print("")
    print("Output files:")
    for path in result["output_paths"]:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
