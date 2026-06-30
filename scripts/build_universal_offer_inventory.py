from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote


from scripts.local_data_paths import dynamic_offers_preview_path, public_sellable_offers_preview_path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
CONFIG_DIR = ROOT / "data" / "config"
DOCS_DIR = ROOT / "docs"

SCHEDULE_FUTURE_PATH = DOCS_DIR / "data" / "schedule_future.json"
DYNAMIC_OFFERS_PATH = dynamic_offers_preview_path(ROOT)
PUBLIC_SELLABLE_OFFERS_PATH = public_sellable_offers_preview_path(ROOT)
SEED_APPOINTMENT_URL_PREVIEW_PATH = AUDIT_DIR / "seed_appointment_url_preview.json"
COURSE_CATALOG_PATH = CONFIG_DIR / "course_catalog.json"
COURSE_MAP_PATH = CONFIG_DIR / "course_map.json"
SLUG_HUBS_PATH = CONFIG_DIR / "slug_hubs.json"
COURSE_VISIBILITY_POLICY_PATH = CONFIG_DIR / "course_visibility_policy.json"
UNIVERSAL_OFFER_POLICY_PATH = CONFIG_DIR / "universal_offer_policy.json"

OUTPUT_PATH = AUDIT_DIR / "universal_offer_inventory.json"
REPORT_PATH = AUDIT_DIR / "universal_offer_inventory_report.md"
STACK_TRACE_JSON_PATH = ROOT / "debug" / "stacking_seeding_trace.json"
STACK_TRACE_MD_PATH = ROOT / "debug" / "stacking_seeding_trace.md"
UNKNOWN = "UNKNOWN"


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean_text(value).lower()).strip("_")


def normalize_match_text(value: Any) -> str:
    text = clean_text(value).lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
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
    text = clean_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def course_catalog_by_id(payload: Any) -> dict[str, dict[str, Any]]:
    courses = payload.get("courses", []) if isinstance(payload, dict) else []
    return {
        clean_text(course.get("course_id")): course
        for course in courses
        if isinstance(course, dict) and clean_text(course.get("course_id"))
    }


def course_map_by_id(payload: Any) -> dict[str, dict[str, Any]]:
    courses = payload.get("courses_by_id", {}) if isinstance(payload, dict) else {}
    return {
        clean_text(course_id): course
        for course_id, course in courses.items()
        if isinstance(course, dict)
    } if isinstance(courses, dict) else {}


def course_code_lookup(course_map: dict[str, dict[str, Any]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for course_id, course in course_map.items():
        values = [
            course_id,
            course.get("course_id"),
            course.get("course_number"),
            course.get("course_code"),
            course.get("course_key"),
            course.get("clean_title"),
            course.get("official_title"),
        ]
        values.extend(course.get("title_aliases", []) if isinstance(course.get("title_aliases"), list) else [])
        for value in values:
            key = normalize_match_text(value)
            if key:
                lookup[key] = course_id
    return lookup


def visibility_records(payload: Any) -> dict[str, dict[str, Any]]:
    courses = payload.get("courses", {}) if isinstance(payload, dict) else {}
    return courses if isinstance(courses, dict) else {}


def visibility_state(course_id: Any, visibility_policy: Any) -> str:
    records = visibility_records(visibility_policy)
    record = records.get(clean_text(course_id), {})
    if isinstance(record, dict) and clean_text(record.get("state")):
        return clean_text(record.get("state"))
    return clean_text(visibility_policy.get("default_state")) if isinstance(visibility_policy, dict) else "active_public"


def course_is_active_public(course_id: Any, visibility_policy: Any) -> bool:
    return visibility_state(course_id, visibility_policy) == "active_public"


def course_family(course: dict[str, Any], course_map_record: dict[str, Any] | None = None) -> str:
    return clean_text(course.get("family") or (course_map_record or {}).get("family") or UNKNOWN)


def course_key(course: dict[str, Any], course_map_record: dict[str, Any] | None = None) -> str:
    return clean_text(course.get("course_key") or (course_map_record or {}).get("course_key") or UNKNOWN)


def course_title(course: dict[str, Any], course_map_record: dict[str, Any] | None = None) -> str:
    return clean_text(
        course.get("short_title")
        or course.get("official_title")
        or (course_map_record or {}).get("clean_title")
        or (course_map_record or {}).get("official_title")
        or UNKNOWN
    )


def tab_course_ids(tab: dict[str, Any], lookup: dict[str, str]) -> set[str]:
    ids: set[str] = set()
    values = tab.get("course_codes", []) if isinstance(tab.get("course_codes"), list) else []
    for value in values:
        text = clean_text(value)
        if not text:
            continue
        if re.fullmatch(r"\d+", text):
            ids.add(text)
        mapped = lookup.get(normalize_match_text(text))
        if mapped:
            ids.add(mapped)
    return ids


def hub_tab_index(slug_hubs: Any, course_lookup: dict[str, str]) -> dict[str, list[dict[str, str]]]:
    pages = slug_hubs.get("pages", []) if isinstance(slug_hubs, dict) else []
    indexed: dict[str, list[dict[str, str]]] = defaultdict(list)
    for page in pages:
        if not isinstance(page, dict):
            continue
        hub_slug = clean_text(page.get("slug"))
        if not hub_slug:
            continue
        for tab in page.get("tabs", []) if isinstance(page.get("tabs"), list) else []:
            if not isinstance(tab, dict):
                continue
            tab_id = clean_text(tab.get("id"))
            if not tab_id:
                continue
            for course_id in tab_course_ids(tab, course_lookup):
                indexed[course_id].append({
                    "hub_slug": hub_slug,
                    "tab_id": tab_id,
                    "tab_label": clean_text(tab.get("label")),
                })
    return indexed


def fallback_hub_for_course(course: dict[str, Any], course_map_record: dict[str, Any] | None = None) -> str:
    family = course_family(course, course_map_record)
    provider = clean_text(course.get("provider") or (course_map_record or {}).get("provider"))
    title = normalize_match_text(course_title(course, course_map_record))
    if family == "BLS":
        return "bls"
    if family == "ACLS":
        return "acls"
    if family == "PALS":
        return "pals"
    if family == "Heartsaver":
        if "uscg" in title or "maritime" in title or provider.upper().startswith("USCG"):
            return "uscg-elementary-first-aid-cpr"
        return "heartsaver"
    if family == "ARC" or "red cross" in title:
        return "arc"
    if family == "HSI" or provider == "HSI":
        return "hsi"
    if family == "USCG":
        return "uscg-elementary-first-aid-cpr"
    return "classes"


def tab_ids_for_course(course_id: str, hubs: dict[str, list[dict[str, str]]], fallback_hub: str) -> tuple[str, list[str]]:
    matches = hubs.get(course_id, [])
    if matches:
        return matches[0]["hub_slug"], sorted({match["tab_id"] for match in matches})
    return fallback_hub, []


def configured_tab_ids(course: dict[str, Any], course_map_record: dict[str, Any] | None, policy: dict[str, Any]) -> list[str]:
    id_overrides = policy.get("course_id_tab_overrides", {}) if isinstance(policy, dict) else {}
    if isinstance(id_overrides, dict):
        values = id_overrides.get(clean_text(course.get("course_id") or (course_map_record or {}).get("course_id")))
        if isinstance(values, list):
            return [clean_text(value) for value in values if clean_text(value)]
    overrides = policy.get("course_key_tab_overrides", {}) if isinstance(policy, dict) else {}
    if not isinstance(overrides, dict):
        return []
    keys = [
        course_key(course, course_map_record),
        clean_text((course_map_record or {}).get("course_key")),
    ]
    for key in keys:
        values = overrides.get(key)
        if isinstance(values, list):
            return [clean_text(value) for value in values if clean_text(value)]
    return []


def hub_and_tabs_for_course(
    course_id: str,
    course: dict[str, Any],
    course_map_record: dict[str, Any] | None,
    hubs: dict[str, list[dict[str, str]]],
    policy: dict[str, Any],
) -> tuple[str, list[str]]:
    hub_slug, tab_ids = tab_ids_for_course(course_id, hubs, fallback_hub_for_course(course, course_map_record))
    override_tab_ids = configured_tab_ids(course, course_map_record, policy)
    if override_tab_ids:
        tab_ids = sorted(set([*tab_ids, *override_tab_ids]))
    return hub_slug, tab_ids


def request_url(course_title_value: str, date_value: Any, start_value: Any) -> str:
    program = quote(course_title_value)
    parts = [f"program={program}"]
    if clean_text(date_value):
        parts.append(f"preferred_date={quote(clean_text(date_value))}")
    if clean_text(start_value):
        parts.append(f"preferred_time={quote(clean_text(start_value))}")
    return "/request_group_session.html?" + "&".join(parts)


def future_request_url(course_title_value: str, course_key_value: str, delivery_bucket_value: str, preferred_month: str, location_name: str) -> str:
    parts = [
        f"program={quote(clean_text(course_title_value))}",
        f"course_key={quote(clean_text(course_key_value))}",
        f"delivery_bucket={quote(clean_text(delivery_bucket_value))}",
    ]
    if clean_text(preferred_month):
        parts.append(f"preferred_month={quote(clean_text(preferred_month))}")
    if clean_text(location_name):
        parts.append(f"location={quote(clean_text(location_name))}")
    parts.append("request_type=future_block")
    return "/request_group_session.html?" + "&".join(parts)


def session_counts_by_course(schedule_payload: Any) -> Counter[str]:
    sessions = schedule_payload.get("sessions", []) if isinstance(schedule_payload, dict) else []
    counts: Counter[str] = Counter()
    for session in sessions:
        if not isinstance(session, dict):
            continue
        course_id = clean_text(session.get("course_id") or session.get("course_number"))
        if course_id:
            counts[course_id] += 1
    return counts


def delivery_bucket(tab_ids: list[str]) -> str:
    return ",".join(sorted(clean_text(tab_id) for tab_id in tab_ids if clean_text(tab_id))) or UNKNOWN


def visible_inventory_key(course_key_value: str, hub_slug: str, tab_ids: list[str]) -> str:
    return "|".join([
        clean_text(course_key_value) or UNKNOWN,
        clean_text(hub_slug) or UNKNOWN,
        delivery_bucket(tab_ids),
    ])


def visible_item(
    source_type: str,
    source_id: Any,
    course_id: Any,
    course_key_value: Any,
    course_title_value: Any,
    hub_slug: Any,
    tab_ids: list[str],
    start_value: Any,
) -> dict[str, Any]:
    start = parse_dt(start_value)
    return {
        "source_type": clean_text(source_type) or UNKNOWN,
        "source_id": clean_text(source_id) or UNKNOWN,
        "course_id": clean_text(course_id),
        "course_key": clean_text(course_key_value) or UNKNOWN,
        "course_title": clean_text(course_title_value) or UNKNOWN,
        "hub_slug": clean_text(hub_slug) or UNKNOWN,
        "delivery_bucket": delivery_bucket(tab_ids),
        "start": start.isoformat() if start else UNKNOWN,
        "date": start.date().isoformat() if start else UNKNOWN,
    }


def visible_inventory_by_course_delivery_page(
    schedule_payload: Any,
    appointment_offers: list[dict[str, Any]],
    course_catalog: dict[str, dict[str, Any]],
    course_map: dict[str, dict[str, Any]],
    hubs: dict[str, list[dict[str, str]]],
    policy: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    inventory: dict[str, list[dict[str, Any]]] = defaultdict(list)
    sessions = schedule_payload.get("sessions", []) if isinstance(schedule_payload, dict) else []
    for session in sessions:
        if not isinstance(session, dict):
            continue
        course_id = clean_text(session.get("course_id") or session.get("course_number"))
        course = course_catalog.get(course_id)
        course_map_record = course_map.get(course_id)
        if not course:
            continue
        course_key_value = course_key(course, course_map_record)
        hub_slug, tab_ids = hub_and_tabs_for_course(course_id, course, course_map_record, hubs, policy)
        key = visible_inventory_key(course_key_value, hub_slug, tab_ids)
        inventory[key].append(visible_item(
            "real_ical",
            session.get("session_id") or session.get("id") or course_id,
            course_id,
            course_key_value,
            session.get("mapped_clean_title") or session.get("official_course_name") or session.get("course_name") or course_title(course, course_map_record),
            hub_slug,
            tab_ids,
            session.get("start_at") or session.get("start_datetime"),
        ))
    for offer in appointment_offers:
        course_key_value = clean_text(offer.get("course_key")) or UNKNOWN
        hub_slug = clean_text(offer.get("hub_slug")) or fallback_hub_for_course({}, {})
        tab_ids = [clean_text(tab_id) for tab_id in offer.get("tab_ids", []) if clean_text(tab_id)] if isinstance(offer.get("tab_ids"), list) else []
        key = visible_inventory_key(course_key_value, hub_slug, tab_ids)
        inventory[key].append(visible_item(
            "appointment_url",
            offer.get("public_offer_id") or offer.get("source_seed_id") or offer.get("source_offer_id"),
            offer.get("course_id"),
            course_key_value,
            offer.get("course_title"),
            hub_slug,
            tab_ids,
            offer.get("scheduler_consumption_start") or offer.get("start_datetime"),
        ))
    return inventory


def visible_items_in_scope(
    items: list[dict[str, Any]],
    candidate_start: datetime,
    lookahead_days: int | None,
) -> list[dict[str, Any]]:
    if lookahead_days is None or lookahead_days <= 0:
        return items
    now = datetime.now(candidate_start.tzinfo) if candidate_start.tzinfo else datetime.now()
    window_end = candidate_start + timedelta(days=lookahead_days)
    scoped: list[dict[str, Any]] = []
    for item in items:
        start = parse_dt(item.get("start"))
        if not start:
            scoped.append(item)
            continue
        if now <= start <= window_end:
            scoped.append(item)
    return scoped


def minimum_visible_rejection_context(
    visible_key: str,
    counted_items: list[dict[str, Any]],
    threshold: int,
    lookahead_days: int | None,
) -> dict[str, Any]:
    return {
        "visible_inventory_key": visible_key,
        "count_threshold_used": threshold,
        "counted_visible_offer_count": len(counted_items),
        "counted_visible_offer_keys": [clean_text(item.get("source_id")) for item in counted_items],
        "counted_visible_offer_course_keys": sorted({clean_text(item.get("course_key")) for item in counted_items if clean_text(item.get("course_key"))}),
        "counted_visible_offer_delivery_buckets": sorted({clean_text(item.get("delivery_bucket")) for item in counted_items if clean_text(item.get("delivery_bucket"))}),
        "counted_visible_offer_dates": sorted({clean_text(item.get("date")) for item in counted_items if clean_text(item.get("date"))}),
        "counted_visible_offer_sources": dict(sorted(Counter(clean_text(item.get("source_type")) or UNKNOWN for item in counted_items).items())),
        "minimum_visible_lookahead_days": lookahead_days if lookahead_days is not None else "all",
    }


def first_public_at_for_candidate(start_dt: datetime, family: str, policy: dict[str, Any]) -> tuple[datetime, int]:
    family_hours = policy.get("course_family_first_public_lead_hours", {}) if isinstance(policy, dict) else {}
    lead_hours = None
    if isinstance(family_hours, dict) and clean_text(family_hours.get(family)):
        lead_hours = int(family_hours.get(family) or 0)
    if lead_hours is None:
        raw_default = policy.get("default_first_public_lead_hours", policy.get("minimum_lead_hours", 0))
        lead_hours = int(raw_default or 0)
    return start_dt - timedelta(hours=lead_hours), lead_hours


def optimizer_score_fields(
    *,
    block_id: str,
    course_id: str,
    course_key_value: str,
    family: str,
    hub_slug: str,
    tab_ids: list[str],
    counted_items: list[dict[str, Any]],
    min_visible: int,
    locks: list[dict[str, Any]],
    offer: dict[str, Any],
    policy: dict[str, Any],
    appointment_url_available: bool,
    request_only: bool,
) -> dict[str, Any]:
    minute = clean_text(offer.get("start_time"))[-2:]
    preferred_minutes = [clean_text(item) for item in policy.get("preferred_start_minutes", []) if clean_text(item)]
    compatibility_group = compatibility_group_for_course_key(course_key_value, policy)
    same_location = any(
        normalize_key(lock.get("location")) == normalize_key(offer.get("offer_location") or offer.get("location"))
        for lock in locks
    )
    fields = {
        "fits_existing_stack": compatibility_group != UNKNOWN,
        "fills_low_inventory_course": len(counted_items) < min_visible,
        "same_location_as_existing_anchor": same_location,
        "clean_customer_start_time": minute in {"00", "15", "30", "45"} and (not preferred_minutes or minute in preferred_minutes),
        "supports_multiple_courses": compatibility_group != UNKNOWN,
        "avoids_one_off_low_value_class": compatibility_group != UNKNOWN or family in {"BLS", "ACLS", "PALS", "Heartsaver"},
        "appointment_url_available": appointment_url_available,
        "request_only_penalty": request_only,
    }
    score = sum(1 for key, value in fields.items() if value and key != "request_only_penalty")
    if fields["request_only_penalty"]:
        score -= 1
    return {
        "score": score,
        "score_fields": fields,
        "score_context": {
            "block_id": block_id,
            "course_id": course_id,
            "course_key": course_key_value,
            "hub_slug": hub_slug,
            "delivery_bucket": delivery_bucket(tab_ids),
            "visible_inventory_count": len(counted_items),
            "minimum_visible_threshold": min_visible,
        },
    }


def offer_sort_key(offer: dict[str, Any], preferred_minutes: list[str]) -> tuple[str, int, str, str]:
    minute = clean_text(offer.get("start_time"))[-2:]
    try:
        minute_rank = preferred_minutes.index(minute)
    except ValueError:
        minute_rank = 999
    return (
        clean_text(offer.get("date")),
        minute_rank,
        clean_text(offer.get("start_time")),
        clean_text(offer.get("offer_id")),
    )


def availability_block_id(offer: dict[str, Any]) -> str:
    source = clean_text(offer.get("source_availability_window"))
    if source:
        return source
    parts = [
        offer.get("date"),
        offer.get("instructor_person_id") or offer.get("instructor_display_name"),
        offer.get("offer_location") or offer.get("location"),
    ]
    key = "|".join(clean_text(part) for part in parts)
    return "derived-" + normalize_key(key or "unknown_block")


def block_page_key(hub_slug: str, tab_ids: list[str], block_id: str) -> tuple[str, str, str]:
    tab_key = ",".join(sorted(tab_ids)) if tab_ids else UNKNOWN
    return hub_slug, tab_key, block_id


def cooldown_hours_for_course(course: dict[str, Any], course_map_record: dict[str, Any] | None, policy: dict[str, Any]) -> int:
    by_course_id = policy.get("offer_again_cooldown_hours_by_course_id", {}) if isinstance(policy, dict) else {}
    course_id = clean_text(course.get("course_id") or (course_map_record or {}).get("course_id"))
    if isinstance(by_course_id, dict) and clean_text(by_course_id.get(course_id)):
        return int(by_course_id.get(course_id) or 0)
    by_family = policy.get("offer_again_cooldown_hours_by_family", {}) if isinstance(policy, dict) else {}
    family = course_family(course, course_map_record)
    if isinstance(by_family, dict) and clean_text(by_family.get(family)):
        return int(by_family.get(family) or 0)
    return int(policy.get("default_offer_again_cooldown_hours", 0) or 0)


def compatibility_group_for_course_key(course_key_value: str, policy: dict[str, Any]) -> str:
    groups = policy.get("stacking_compatibility_groups", {}) if isinstance(policy, dict) else {}
    if not isinstance(groups, dict):
        return UNKNOWN
    for group_name, course_keys in groups.items():
        if isinstance(course_keys, list) and course_key_value in {clean_text(item) for item in course_keys}:
            return clean_text(group_name) or UNKNOWN
    return UNKNOWN


def course_recently_visible(
    course_id: str,
    candidate_start: datetime,
    real_sessions_by_course: dict[str, list[datetime]],
    appointment_offers: list[dict[str, Any]],
    cooldown_hours: int,
) -> bool:
    if cooldown_hours <= 0:
        return False
    window = timedelta(hours=cooldown_hours)
    for start in real_sessions_by_course.get(course_id, []):
        if abs(candidate_start - start) <= window:
            return True
    for offer in appointment_offers:
        if clean_text(offer.get("course_id")) != course_id:
            continue
        start = parse_dt(offer.get("scheduler_consumption_start") or offer.get("start_datetime"))
        if start and abs(candidate_start - start) <= window:
            return True
    return False


def real_session_starts_by_course(schedule_payload: Any) -> dict[str, list[datetime]]:
    sessions = schedule_payload.get("sessions", []) if isinstance(schedule_payload, dict) else []
    starts: dict[str, list[datetime]] = defaultdict(list)
    for session in sessions:
        if not isinstance(session, dict):
            continue
        course_id = clean_text(session.get("course_id") or session.get("course_number"))
        start = parse_dt(session.get("start_at") or session.get("start_datetime"))
        if course_id and start:
            starts[course_id].append(start)
    return starts


def build_stack_trace(
    dynamic_payload: Any,
    accepted_offers: list[dict[str, Any]],
    rejections: list[dict[str, Any]],
    planned_offers: list[dict[str, Any]],
    appointment_offers: list[dict[str, Any]],
    schedule_payload: Any,
    policy: dict[str, Any],
) -> dict[str, Any]:
    dynamic_offers = [offer for offer in (dynamic_payload.get("offers", []) if isinstance(dynamic_payload, dict) else []) if isinstance(offer, dict)]
    blocks: dict[str, dict[str, Any]] = {}
    accepted_by_source = {clean_text(offer.get("source_offer_id")): offer for offer in accepted_offers if clean_text(offer.get("source_offer_id"))}
    rejections_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rejection in rejections:
        rejections_by_source[clean_text(rejection.get("source_offer_id"))].append(rejection)

    sessions = schedule_payload.get("sessions", []) if isinstance(schedule_payload, dict) else []
    real_sessions: list[dict[str, Any]] = []
    for session in sessions:
        if not isinstance(session, dict):
            continue
        real_sessions.append({
            "session_id": session.get("session_id"),
            "course_id": session.get("course_id"),
            "course_title": session.get("mapped_clean_title") or session.get("official_course_name") or session.get("course_name"),
            "start": session.get("start_at"),
            "end": session.get("end_at"),
            "location": session.get("location_display") or session.get("location_name"),
        })

    for offer in dynamic_offers:
        block_id = availability_block_id(offer)
        block = blocks.setdefault(block_id, {
            "block_id": block_id,
            "source_availability_window": clean_text(offer.get("source_availability_window")),
            "instructor": clean_text(offer.get("instructor_display_name")),
            "location": clean_text(offer.get("offer_location") or offer.get("location")),
            "block_start": None,
            "block_end": None,
            "candidate_count": 0,
            "candidate_start_times": [],
            "courses_evaluated": Counter(),
            "accepted_offer_ids": [],
            "rejection_reasons": Counter(),
            "real_ical_classes_near_block": [],
        })
        start = parse_dt(offer.get("scheduler_consumption_start") or offer.get("start_datetime"))
        end = parse_dt(offer.get("scheduler_consumption_end") or offer.get("end_datetime"))
        if start and (not block["block_start"] or start.isoformat() < block["block_start"]):
            block["block_start"] = start.isoformat()
        if end and (not block["block_end"] or end.isoformat() > block["block_end"]):
            block["block_end"] = end.isoformat()
        block["candidate_count"] += 1
        start_time = clean_text(offer.get("start_time"))
        if start_time and start_time not in block["candidate_start_times"]:
            block["candidate_start_times"].append(start_time)
        block["courses_evaluated"][clean_text(offer.get("course_id")) or UNKNOWN] += 1
        source_id = clean_text(offer.get("offer_id"))
        if source_id in accepted_by_source:
            block["accepted_offer_ids"].append(accepted_by_source[source_id].get("public_offer_id"))
        for rejection in rejections_by_source.get(source_id, []):
            block["rejection_reasons"][clean_text(rejection.get("reason_code")) or UNKNOWN] += 1

    for block in blocks.values():
        block_start = parse_dt(block.get("block_start"))
        block_end = parse_dt(block.get("block_end"))
        if block_start and block_end:
            near_start = block_start - timedelta(hours=2)
            near_end = block_end + timedelta(hours=2)
            block["real_ical_classes_near_block"] = [
                session for session in real_sessions
                if (dt := parse_dt(session.get("start"))) and near_start <= dt <= near_end
            ][:25]
        block["candidate_start_times"] = sorted(block["candidate_start_times"])
        block["courses_evaluated"] = dict(block["courses_evaluated"].most_common())
        block["rejection_reasons"] = dict(block["rejection_reasons"].most_common())

    stack_groups = []
    for block in blocks.values():
        accepted = [offer for offer in accepted_offers if offer.get("public_offer_id") in block["accepted_offer_ids"]]
        if not accepted:
            continue
        stack_groups.append({
            "stack_group_id": f"stack-{normalize_key(block['block_id'])}",
            "block_id": block["block_id"],
            "instructor": block.get("instructor"),
            "location": block.get("location"),
            "block_start": block.get("block_start"),
            "block_end": block.get("block_end"),
            "offer_count": len(accepted),
            "proposed_course_offers": [
                {
                    "public_offer_id": offer.get("public_offer_id"),
                    "offer_type": offer.get("offer_type"),
                    "course_id": offer.get("course_id"),
                    "course_title": offer.get("course_title"),
                    "compatibility_group": compatibility_group_for_course_key(clean_text(offer.get("course_key")), policy),
                    "hub_slug": offer.get("hub_slug"),
                    "tab_ids": offer.get("tab_ids"),
                    "display_start": offer.get("start_datetime"),
                    "display_end": offer.get("end_datetime"),
                    "scheduler_consumption_start": offer.get("scheduler_consumption_start"),
                    "scheduler_consumption_end": offer.get("scheduler_consumption_end"),
                    "deterministic_url_available": bool(offer.get("appointment_registration_url")),
                }
                for offer in accepted
            ],
        })

    trace_rejections = [
        {
            "source_offer_id": rejection.get("source_offer_id"),
            "course_id": rejection.get("course_id"),
            "course_key": rejection.get("course_key"),
            "course_title": rejection.get("course_title"),
            "delivery_bucket": rejection.get("delivery_bucket"),
            "target_hub": rejection.get("target_hub"),
            "target_page": rejection.get("target_page"),
            "target_tab_ids": rejection.get("target_tab_ids"),
            "offer_type": rejection.get("offer_type"),
            "reason_code": rejection.get("reason_code"),
            "detail": rejection.get("detail"),
            **({
                "visible_inventory_key": rejection.get("visible_inventory_key"),
                "count_threshold_used": rejection.get("count_threshold_used"),
                "counted_visible_offer_count": rejection.get("counted_visible_offer_count"),
                "counted_visible_offer_keys": rejection.get("counted_visible_offer_keys"),
                "counted_visible_offer_course_keys": rejection.get("counted_visible_offer_course_keys"),
                "counted_visible_offer_delivery_buckets": rejection.get("counted_visible_offer_delivery_buckets"),
                "counted_visible_offer_dates": rejection.get("counted_visible_offer_dates"),
                "counted_visible_offer_sources": rejection.get("counted_visible_offer_sources"),
                "minimum_visible_lookahead_days": rejection.get("minimum_visible_lookahead_days"),
            } if rejection.get("reason_code") == "minimum_visible_offers_already_met" else {}),
        }
        for rejection in rejections[:5000]
    ]
    minimum_visible_rejections = [
        rejection for rejection in trace_rejections
        if rejection.get("reason_code") == "minimum_visible_offers_already_met"
    ]
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "availability_blocks_considered": list(blocks.values()),
        "availability_block_count": len(blocks),
        "courses_evaluated_per_block": {
            block["block_id"]: block["courses_evaluated"]
            for block in blocks.values()
        },
        "candidate_start_times_by_block": {
            block["block_id"]: block["candidate_start_times"]
            for block in blocks.values()
        },
        "accepted_offers": accepted_offers,
        "public_now_offers": [
            offer for offer in accepted_offers
            if clean_text(offer.get("candidate_state")) in {"", "public_now"}
        ],
        "planned_future_visibility_offers": planned_offers,
        "rejected_offers": trace_rejections,
        "rejection_histogram": dict(Counter(clean_text(item.get("reason_code")) or UNKNOWN for item in rejections).most_common()),
        "candidate_state_counts": {
            "public_now": len(accepted_offers),
            "planned_future_visibility": len(planned_offers),
            "rejected": len(rejections),
        },
        "planned_future_visibility_by_course": dict(Counter(clean_text(item.get("course_title")) or UNKNOWN for item in planned_offers).most_common()),
        "planned_future_visibility_by_page": dict(Counter(clean_text(item.get("target_page") or item.get("hub_slug")) or UNKNOWN for item in planned_offers).most_common()),
        "planned_future_visibility_reasons": dict(Counter(clean_text(item.get("not_public_reason")) or UNKNOWN for item in planned_offers).most_common()),
        "minimum_visible_offer_rejections": minimum_visible_rejections,
        "minimum_visible_rejection_groups": {
            key: {
                "count": len(items),
                "course_keys": sorted({clean_text(item.get("course_key")) for item in items if clean_text(item.get("course_key"))}),
                "delivery_buckets": sorted({clean_text(item.get("delivery_bucket")) for item in items if clean_text(item.get("delivery_bucket"))}),
                "target_hubs": sorted({clean_text(item.get("target_hub")) for item in items if clean_text(item.get("target_hub"))}),
                "counted_sources": dict(sorted(Counter(
                    source
                    for item in items
                    for source, count in (item.get("counted_visible_offer_sources") or {}).items()
                    for _ in range(int(count or 0))
                ).items())),
                "counted_dates": sorted({
                    date
                    for item in items
                    for date in (item.get("counted_visible_offer_dates") or [])
                    if clean_text(date)
                }),
            }
            for key, items in sorted(
                defaultdict(list, {
                    group_key: [
                        item for item in minimum_visible_rejections
                        if clean_text(item.get("visible_inventory_key")) == group_key
                    ]
                    for group_key in sorted({clean_text(item.get("visible_inventory_key")) for item in minimum_visible_rejections})
                }).items()
            )
        },
        "cooldown_decisions": [
            rejection for rejection in trace_rejections
            if clean_text(rejection.get("reason_code")).startswith("offer_again_cooldown")
        ],
        "deterministic_url_successes": [
            {
                "public_offer_id": offer.get("public_offer_id"),
                "course_id": offer.get("course_id"),
                "course_title": offer.get("course_title"),
                "start_time": offer.get("start_time"),
                "url_present": bool(offer.get("appointment_registration_url")),
            }
            for offer in appointment_offers
        ],
        "deterministic_url_failures": [
            rejection for rejection in trace_rejections
            if rejection.get("offer_type") == "appointment_url"
        ],
        "request_only_fallback_reasons": dict(Counter(
            clean_text(offer.get("display_note")) or "request_only_fallback"
            for offer in accepted_offers
            if offer.get("offer_type") == "request_only_block"
        )),
        "stack_groups_created": stack_groups,
        "public_offers_by_course_delivery_page": {
            f"{offer.get('hub_slug')}|{','.join(offer.get('tab_ids', []) or [UNKNOWN])}|{offer.get('course_id')}": {
                "hub_slug": offer.get("hub_slug"),
                "tab_ids": offer.get("tab_ids"),
                "course_id": offer.get("course_id"),
                "course_title": offer.get("course_title"),
                "offer_type": offer.get("offer_type"),
            }
            for offer in accepted_offers
        },
    }


def intervals_overlap(a_start: Any, a_end: Any, b_start: Any, b_end: Any) -> bool:
    start_a = parse_dt(a_start)
    end_a = parse_dt(a_end)
    start_b = parse_dt(b_start)
    end_b = parse_dt(b_end)
    if not start_a or not end_a or not start_b or not end_b:
        return False
    return start_a < end_b and start_b < end_a


def build_appointment_url_offers(
    seed_preview_payload: Any,
    course_catalog: dict[str, dict[str, Any]],
    course_map: dict[str, dict[str, Any]],
    hubs: dict[str, list[dict[str, str]]],
    visibility_policy: Any,
    policy: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    offers: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    previews = seed_preview_payload.get("previews", []) if isinstance(seed_preview_payload, dict) else []
    for preview in previews:
        if not isinstance(preview, dict):
            continue
        course_id = clean_text(preview.get("course_id"))
        course = course_catalog.get(course_id)
        course_map_record = course_map.get(course_id)
        context = {
            "source_offer_id": preview.get("source_offer_id"),
            "course_id": course_id,
            "course_title": preview.get("course_title"),
            "offer_type": "appointment_url",
        }
        if preview.get("blocking_reason"):
            rejections.append({**context, "reason_code": "seed_url_blocked", "detail": preview.get("blocking_reason")})
            continue
        if not course:
            rejections.append({**context, "reason_code": "course_not_found"})
            continue
        if not course_is_active_public(course_id, visibility_policy):
            rejections.append({**context, "reason_code": f"course_visibility_{visibility_state(course_id, visibility_policy)}"})
            continue
        url = clean_text(preview.get("appointment_url_preview"))
        appointment_day_id = clean_text(preview.get("appointmentDayId"))
        if not url or not appointment_day_id:
            rejections.append({**context, "reason_code": "missing_appointment_url"})
            continue
        hub_slug, tab_ids = hub_and_tabs_for_course(course_id, course, course_map_record, hubs, policy)
        block_id = clean_text(preview.get("source_availability_window")) or clean_text(preview.get("source_offer_id")) or clean_text(preview.get("seed_id"))
        course_key_value = course_key(course, course_map_record)
        start_dt = parse_dt(preview.get("scheduler_consumption_start") or preview.get("appointment_display_start"))
        first_public_at, first_public_lead_hours = first_public_at_for_candidate(
            start_dt or datetime.now(),
            course_family(course, course_map_record),
            policy,
        )
        built_offer = {
            "public_offer_id": f"appointment-{clean_text(preview.get('seed_id')) or clean_text(preview.get('source_offer_id'))}",
            "offer_type": "appointment_url",
            "candidate_state": "public_now",
            "first_public_at": first_public_at.isoformat(),
            "first_public_lead_hours": first_public_lead_hours,
            "cta_label": policy.get("default_appointment_cta_label", "Check this date/time"),
            "course_id": course_id,
            "course_key": course_key_value,
            "course_title": clean_text(preview.get("course_title")) or course_title(course, course_map_record),
            "course_family": course_family(course, course_map_record),
            "stacking_compatibility_group": compatibility_group_for_course_key(course_key_value, policy),
            "hub_slug": hub_slug,
            "tab_ids": tab_ids,
            "date": preview.get("date"),
            "start_time": preview.get("start_time"),
            "start_datetime": preview.get("appointment_display_start"),
            "end_datetime": preview.get("appointment_display_end"),
            "scheduler_consumption_start": preview.get("scheduler_consumption_start"),
            "scheduler_consumption_end": preview.get("scheduler_consumption_end"),
            "location_name": clean_text(preview.get("location")),
            "instructor_display_name": clean_text(preview.get("instructor_display_name")),
            "appointment_registration_url": url,
            "request_url": None,
            "source_offer_id": preview.get("source_offer_id"),
            "source_seed_id": preview.get("seed_id"),
            "source_availability_window": block_id,
            "stack_group_id": f"stack-{normalize_key(block_id)}",
            "stack_candidate_role": "deterministic_appointment",
            "display_note": "Available appointment-backed class option.",
            "public_schedule_row_created": False,
            "standalone_class_lander_created": False,
        }
        built_offer.update(optimizer_score_fields(
            block_id=block_id,
            course_id=course_id,
            course_key_value=course_key_value,
            family=course_family(course, course_map_record),
            hub_slug=hub_slug,
            tab_ids=tab_ids,
            counted_items=[],
            min_visible=0,
            locks=[],
            offer={
                "start_time": preview.get("start_time"),
                "offer_location": preview.get("location"),
            },
            policy=policy,
            appointment_url_available=True,
            request_only=False,
        ))
        offers.append(built_offer)
    return offers, rejections


def selected_seed_locks(appointment_offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "course_id": offer.get("course_id"),
            "hub_slug": offer.get("hub_slug"),
            "start": offer.get("scheduler_consumption_start") or offer.get("start_datetime"),
            "end": offer.get("scheduler_consumption_end") or offer.get("end_datetime"),
            "location": offer.get("location_name"),
            "instructor": offer.get("instructor_display_name"),
        }
        for offer in appointment_offers
    ]


def build_request_block_offers(
    dynamic_payload: Any,
    real_session_starts: dict[str, list[datetime]],
    visible_inventory: dict[str, list[dict[str, Any]]],
    appointment_offers: list[dict[str, Any]],
    course_catalog: dict[str, dict[str, Any]],
    course_map: dict[str, dict[str, Any]],
    hubs: dict[str, list[dict[str, str]]],
    visibility_policy: Any,
    policy: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    offers = dynamic_payload.get("offers", []) if isinstance(dynamic_payload, dict) else []
    if not isinstance(offers, list):
        offers = []
    request_families = {clean_text(item) for item in policy.get("request_only_families", []) if clean_text(item)}
    min_visible = int(policy.get("minimum_visible_offers_per_course", 2) or 2)
    max_per_course = int(policy.get("max_request_block_offers_per_course", 3) or 3)
    max_block_offers_per_course = int(policy.get("max_block_offers_per_course", max_per_course) or max_per_course)
    max_per_week = int(policy.get("max_request_block_offers_per_course_per_week", 2) or 2)
    max_per_hub = int(policy.get("max_total_request_block_offers_per_hub", 12) or 12)
    max_start_times_per_block_per_page = int(policy.get("max_start_times_per_block_per_page", 3) or 3)
    preferred_minutes = [clean_text(item) for item in policy.get("preferred_start_minutes", []) if clean_text(item)]
    minimum_lead_hours = int(policy.get("minimum_lead_hours", 0) or 0)
    enable_planned_visibility = bool(policy.get("enable_planned_visibility", False))
    planned_visibility_audit_only = bool(policy.get("planned_visibility_audit_only", True))
    lookahead_raw = policy.get("minimum_visible_offer_lookahead_days")
    minimum_visible_lookahead_days = int(lookahead_raw) if clean_text(lookahead_raw) else None
    earliest_start = datetime.now() + timedelta(hours=minimum_lead_hours)
    selected_source_ids = {clean_text(offer.get("source_offer_id")) for offer in appointment_offers}
    course_request_counts: Counter[str] = Counter()
    course_block_counts: Counter[tuple[str, str]] = Counter()
    course_week_counts: Counter[tuple[str, str]] = Counter()
    hub_counts: Counter[str] = Counter()
    block_page_start_counts: Counter[tuple[str, str, str]] = Counter()
    locks = selected_seed_locks(appointment_offers)
    built: list[dict[str, Any]] = []
    planned: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []

    sorted_offers = sorted(
        [offer for offer in offers if isinstance(offer, dict)],
        key=lambda offer: offer_sort_key(offer, preferred_minutes),
    )
    for offer in sorted_offers:
        course_id = clean_text(offer.get("course_id"))
        course = course_catalog.get(course_id)
        course_map_record = course_map.get(course_id)
        context = {
            "source_offer_id": offer.get("offer_id"),
            "course_id": course_id,
            "course_title": offer.get("course_title"),
            "offer_type": "request_only_block",
        }
        if not course:
            rejections.append({**context, "reason_code": "course_not_found"})
            continue
        if not course_is_active_public(course_id, visibility_policy):
            rejections.append({**context, "reason_code": f"course_visibility_{visibility_state(course_id, visibility_policy)}"})
            continue
        family = course_family(course, course_map_record)
        if request_families and family not in request_families:
            rejections.append({**context, "reason_code": "family_not_request_offer_enabled"})
            continue
        if clean_text(offer.get("offer_id")) in selected_source_ids:
            rejections.append({**context, "reason_code": "already_exposed_as_appointment_url_offer"})
            continue
        start_dt = parse_dt(offer.get("scheduler_consumption_start") or offer.get("appointment_display_start") or offer.get("start_datetime"))
        if not start_dt:
            rejections.append({**context, "reason_code": "missing_start_datetime"})
            continue
        hub_slug, tab_ids = hub_and_tabs_for_course(course_id, course, course_map_record, hubs, policy)
        course_key_value = course_key(course, course_map_record)
        visible_key = visible_inventory_key(course_key_value, hub_slug, tab_ids)
        counted_items = visible_items_in_scope(visible_inventory.get(visible_key, []), start_dt, minimum_visible_lookahead_days)
        context = {
            **context,
            "course_key": course_key_value,
            "delivery_bucket": delivery_bucket(tab_ids),
            "target_hub": hub_slug,
            "target_page": hub_slug,
            "target_tab_ids": tab_ids,
        }
        if len(counted_items) >= min_visible:
            rejections.append({
                **context,
                "reason_code": "minimum_visible_offers_already_met",
                **minimum_visible_rejection_context(visible_key, counted_items, min_visible, minimum_visible_lookahead_days),
            })
            continue
        if course_request_counts[course_id] >= max_per_course:
            rejections.append({**context, "reason_code": "max_request_block_offers_per_course"})
            continue
        cooldown_hours = cooldown_hours_for_course(course, course_map_record, policy)
        if course_recently_visible(course_id, start_dt, real_session_starts, appointment_offers, cooldown_hours):
            rejections.append({**context, "reason_code": "offer_again_cooldown_window", "detail": f"{cooldown_hours}_hours"})
            continue
        week_key = f"{start_dt.isocalendar().year}-W{start_dt.isocalendar().week:02d}"
        if course_week_counts[(course_id, week_key)] >= max_per_week:
            rejections.append({**context, "reason_code": "max_request_block_offers_per_course_per_week"})
            continue
        block_id = availability_block_id(offer)
        if course_block_counts[(course_id, block_id)] >= max_block_offers_per_course:
            rejections.append({**context, "reason_code": "max_block_offers_per_course"})
            continue
        page_key = block_page_key(hub_slug, tab_ids, block_id)
        if block_page_start_counts[page_key] >= max_start_times_per_block_per_page:
            rejections.append({**context, "reason_code": "max_start_times_per_block_per_page"})
            continue
        if hub_counts[hub_slug] >= max_per_hub:
            rejections.append({**context, "reason_code": "max_total_request_block_offers_per_hub"})
            continue
        conflict = next((
            lock for lock in locks
            if normalize_key(lock.get("instructor")) == normalize_key(offer.get("instructor_display_name"))
            and normalize_key(lock.get("location")) == normalize_key(offer.get("location") or offer.get("offer_location"))
            and intervals_overlap(
                lock.get("start"),
                lock.get("end"),
                offer.get("scheduler_consumption_start") or offer.get("appointment_display_start"),
                offer.get("scheduler_consumption_end") or offer.get("appointment_display_end"),
            )
        ), None)
        if conflict:
            rejections.append({**context, "reason_code": "conflicts_with_selected_appointment_seed"})
            continue

        title = clean_text(offer.get("course_title")) or course_title(course, course_map_record)
        first_public_at, first_public_lead_hours = first_public_at_for_candidate(start_dt, family, policy)
        score = optimizer_score_fields(
            block_id=block_id,
            course_id=course_id,
            course_key_value=course_key_value,
            family=family,
            hub_slug=hub_slug,
            tab_ids=tab_ids,
            counted_items=counted_items,
            min_visible=min_visible,
            locks=locks,
            offer=offer,
            policy=policy,
            appointment_url_available=False,
            request_only=True,
        )
        if start_dt < earliest_start:
            lead_context = {
                **context,
                "reason_code": "inside_minimum_lead_time",
                "minimum_lead_hours": minimum_lead_hours,
                "candidate_start": start_dt.isoformat(),
                "first_public_at": first_public_at.isoformat(),
                "first_public_lead_hours": first_public_lead_hours,
                "would_otherwise_fit": True,
                "deterministic_appointment_url_available": False,
                "request_only_fallback_available": True,
                **score,
            }
            if enable_planned_visibility:
                planned.append({
                    "planned_offer_id": f"planned-{clean_text(offer.get('offer_id'))}",
                    "candidate_state": "planned_future_visibility",
                    "not_public_reason": "inside_minimum_lead_time",
                    "planned_visibility_audit_only": planned_visibility_audit_only,
                    "course_id": course_id,
                    "course_key": course_key_value,
                    "course_title": title,
                    "course_family": family,
                    "stacking_compatibility_group": compatibility_group_for_course_key(course_key_value, policy),
                    "hub_slug": hub_slug,
                    "target_page": hub_slug,
                    "tab_ids": tab_ids,
                    "delivery_bucket": delivery_bucket(tab_ids),
                    "date": offer.get("date"),
                    "start_time": offer.get("start_time"),
                    "start_datetime": offer.get("appointment_display_start") or offer.get("start_datetime"),
                    "end_datetime": offer.get("appointment_display_end") or offer.get("end_datetime"),
                    "scheduler_consumption_start": offer.get("scheduler_consumption_start"),
                    "scheduler_consumption_end": offer.get("scheduler_consumption_end"),
                    "location_name": clean_text(offer.get("offer_location") or offer.get("location")),
                    "instructor_display_name": clean_text(offer.get("instructor_display_name")),
                    "source_offer_id": offer.get("offer_id"),
                    "source_availability_window": offer.get("source_availability_window"),
                    "stack_group_id": f"stack-{normalize_key(block_id)}",
                    "stack_candidate_role": "planned_request_only_availability",
                    "minimum_lead_hours": minimum_lead_hours,
                    "candidate_start": start_dt.isoformat(),
                    "first_public_at": first_public_at.isoformat(),
                    "first_public_lead_hours": first_public_lead_hours,
                    "would_otherwise_fit": True,
                    "deterministic_appointment_url_available": False,
                    "request_only_fallback_available": True,
                    **score,
                })
            else:
                rejections.append(lead_context)
            continue
        built_offer = {
            "public_offer_id": f"request-{clean_text(offer.get('offer_id'))}",
            "offer_type": "request_only_block",
            "candidate_state": "public_now",
            "first_public_at": first_public_at.isoformat(),
            "first_public_lead_hours": first_public_lead_hours,
            "cta_label": policy.get("default_request_cta_label", "Ask about this time"),
            "course_id": course_id,
            "course_key": course_key(course, course_map_record),
            "course_title": title,
            "course_family": family,
            "stacking_compatibility_group": compatibility_group_for_course_key(course_key(course, course_map_record), policy),
            "hub_slug": hub_slug,
            "tab_ids": tab_ids,
            "date": offer.get("date"),
            "start_time": offer.get("start_time"),
            "start_datetime": offer.get("appointment_display_start") or offer.get("start_datetime"),
            "end_datetime": offer.get("appointment_display_end") or offer.get("end_datetime"),
            "scheduler_consumption_start": offer.get("scheduler_consumption_start"),
            "scheduler_consumption_end": offer.get("scheduler_consumption_end"),
            "location_name": clean_text(offer.get("offer_location") or offer.get("location")),
            "instructor_display_name": clean_text(offer.get("instructor_display_name")),
            "appointment_registration_url": None,
            "request_url": request_url(title, offer.get("date"), offer.get("start_time")),
            "source_offer_id": offer.get("offer_id"),
            "source_availability_window": offer.get("source_availability_window"),
            "stack_group_id": f"stack-{normalize_key(block_id)}",
            "stack_candidate_role": "request_only_availability",
            "display_note": policy.get("request_offer_copy"),
            "public_schedule_row_created": False,
            "standalone_class_lander_created": False,
            **score,
        }
        built.append(built_offer)
        visible_inventory.setdefault(visible_key, []).append(visible_item(
            "request_only",
            built_offer.get("public_offer_id"),
            course_id,
            course_key_value,
            title,
            hub_slug,
            tab_ids,
            built_offer.get("scheduler_consumption_start") or built_offer.get("start_datetime"),
        ))
        course_request_counts[course_id] += 1
        course_block_counts[(course_id, block_id)] += 1
        course_week_counts[(course_id, week_key)] += 1
        hub_counts[hub_slug] += 1
        block_page_start_counts[page_key] += 1
        locks.append({
            "course_id": course_id,
            "hub_slug": hub_slug,
            "start": built_offer.get("scheduler_consumption_start") or built_offer.get("start_datetime"),
            "end": built_offer.get("scheduler_consumption_end") or built_offer.get("end_datetime"),
            "location": built_offer.get("location_name"),
            "instructor": built_offer.get("instructor_display_name"),
        })
    return built, rejections, planned


def build_future_request_block_offers(
    dynamic_payload: Any,
    course_catalog: dict[str, dict[str, Any]],
    course_map: dict[str, dict[str, Any]],
    hubs: dict[str, list[dict[str, str]]],
    visibility_policy: Any,
    policy: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    offers = dynamic_payload.get("offers", []) if isinstance(dynamic_payload, dict) else []
    if not isinstance(offers, list):
        offers = []
    optimized_days = int(policy.get("optimized_offer_horizon_days", 60) or 60)
    future_days = int(policy.get("future_request_horizon_days", 120) or 120)
    if future_days <= optimized_days:
        return [], []
    request_families = {clean_text(item) for item in policy.get("request_only_families", []) if clean_text(item)}
    now = datetime.now()
    optimized_cutoff = now + timedelta(days=optimized_days)
    future_cutoff = now + timedelta(days=future_days)
    built_by_key: dict[str, dict[str, Any]] = {}
    rejections: list[dict[str, Any]] = []

    for offer in sorted([item for item in offers if isinstance(item, dict)], key=lambda item: parse_dt(item.get("scheduler_consumption_start") or item.get("appointment_display_start") or item.get("start_datetime")) or datetime.max):
        course_id = clean_text(offer.get("course_id"))
        course = course_catalog.get(course_id)
        course_map_record = course_map.get(course_id)
        context = {
            "source_offer_id": offer.get("offer_id"),
            "course_id": course_id,
            "course_title": offer.get("course_title"),
            "offer_type": "future_request_block",
        }
        if not course:
            rejections.append({**context, "reason_code": "course_not_found"})
            continue
        if not course_is_active_public(course_id, visibility_policy):
            rejections.append({**context, "reason_code": f"course_visibility_{visibility_state(course_id, visibility_policy)}"})
            continue
        family = course_family(course, course_map_record)
        if request_families and family not in request_families:
            rejections.append({**context, "reason_code": "family_not_request_offer_enabled"})
            continue
        start_dt = parse_dt(offer.get("scheduler_consumption_start") or offer.get("appointment_display_start") or offer.get("start_datetime"))
        if not start_dt:
            rejections.append({**context, "reason_code": "missing_start_datetime"})
            continue
        if start_dt <= optimized_cutoff:
            rejections.append({**context, "reason_code": "inside_optimized_offer_horizon"})
            continue
        if start_dt > future_cutoff:
            rejections.append({**context, "reason_code": "outside_future_request_horizon"})
            continue
        hub_slug, tab_ids = hub_and_tabs_for_course(course_id, course, course_map_record, hubs, policy)
        course_key_value = course_key(course, course_map_record)
        bucket = delivery_bucket(tab_ids)
        page_key = visible_inventory_key(course_key_value, hub_slug, tab_ids)
        if page_key in built_by_key:
            rejections.append({**context, "reason_code": "future_request_block_already_created", "visible_inventory_key": page_key})
            continue
        title = clean_text(offer.get("course_title")) or course_title(course, course_map_record)
        location_name = clean_text(offer.get("offer_location") or offer.get("location"))
        preferred_month = start_dt.strftime("%Y-%m")
        block_id = availability_block_id(offer)
        built_by_key[page_key] = {
            "public_offer_id": f"future-request-{normalize_key(page_key)}",
            "offer_type": "future_request_block",
            "candidate_state": "future_request_fallback",
            "cta_label": "Request a future block",
            "course_id": course_id,
            "course_key": course_key_value,
            "course_title": title,
            "course_family": family,
            "stacking_compatibility_group": compatibility_group_for_course_key(course_key_value, policy),
            "hub_slug": hub_slug,
            "tab_ids": tab_ids,
            "delivery_bucket": bucket,
            "date": start_dt.date().isoformat(),
            "preferred_month": preferred_month,
            "start_time": UNKNOWN,
            "start_datetime": start_dt.isoformat(),
            "end_datetime": offer.get("appointment_display_end") or offer.get("end_datetime"),
            "scheduler_consumption_start": offer.get("scheduler_consumption_start"),
            "scheduler_consumption_end": offer.get("scheduler_consumption_end"),
            "location_name": location_name,
            "instructor_display_name": clean_text(offer.get("instructor_display_name")),
            "appointment_registration_url": None,
            "request_url": future_request_url(title, course_key_value, bucket, preferred_month, location_name),
            "source_offer_id": offer.get("offer_id"),
            "source_availability_window": offer.get("source_availability_window"),
            "stack_group_id": f"future-stack-{normalize_key(block_id)}",
            "stack_candidate_role": "future_requestable_availability",
            "display_note": "We can often arrange this course beyond the currently listed schedule.",
            "public_schedule_row_created": False,
            "standalone_class_lander_created": False,
            "optimized_offer_horizon_days": optimized_days,
            "future_request_horizon_days": future_days,
            "assume_cooldown_reset_after_horizon": bool(policy.get("assume_cooldown_reset_after_horizon", True)),
        }
    return list(built_by_key.values()), rejections


def grouped_counts(offers: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(clean_text(offer.get(key)) or UNKNOWN for offer in offers).items()))


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Universal Offer Inventory Report",
        "",
        "Read-only build artifact. Real seated Enrollware classes remain in `docs/data/schedule_future.json`; generated appointment/request offers are hub-only display opportunities.",
        "",
        "## Summary",
        "",
        f"- Real seated classes read: {summary['real_seated_classes_read']}",
        f"- Dynamic offers read: {summary['dynamic_offers_read']}",
        f"- Deterministic appointment URL offers generated: {summary['appointment_url_offers_generated']}",
        f"- Request-only block offers generated: {summary['request_only_block_offers_generated']}",
        f"- Future request block offers generated: {summary.get('future_request_block_offers_generated', 0)}",
        f"- Total hub-only generated offers: {summary['total_generated_offers']}",
        f"- Planned future visibility candidates: {summary.get('planned_future_visibility_count', 0)}",
        f"- Stack groups created: {summary.get('stack_groups_created', 0)}",
        "",
        "## Offers By Hub",
        "",
    ]
    if summary["offers_by_hub"]:
        lines.extend(f"- `{hub}`: {count}" for hub, count in summary["offers_by_hub"].items())
    else:
        lines.append("- None")
    lines.extend(["", "## Offers By Course", ""])
    if summary["offers_by_course"]:
        lines.extend(f"- `{course}`: {count}" for course, count in summary["offers_by_course"].items())
    else:
        lines.append("- None")
    lines.extend(["", "## Future Request Blocks", ""])
    future_counts = summary.get("future_request_offers_by_course", {})
    if future_counts:
        lines.extend(f"- `{course}`: {count}" for course, count in future_counts.items())
    else:
        lines.append("- None")
    future_rejections = summary.get("future_request_rejections_by_reason", {})
    if future_rejections:
        lines.extend(["", "### Future Request Skip Reasons", ""])
        lines.extend(f"- `{reason}`: {count}" for reason, count in future_rejections.items())
    lines.extend(["", "## Rejection Reasons", ""])
    if summary["rejections_by_reason"]:
        lines.extend(f"- `{reason}`: {count}" for reason, count in summary["rejections_by_reason"].items())
    else:
        lines.append("- None")
    lines.extend(["", "## Low-Inventory Focus", ""])
    focus = ["heartsaver-first-aid-cpr-aed", "heartsaver-cpr-aed", "heartsaver-pediatric-first-aid-cpr-aed", "heartsaver-first-aid", "bloodborne-pathogens"]
    for key in focus:
        lines.append(f"- `{key}`: {summary.get('course_page_offer_counts', {}).get(key, 0)} generated hub-only offers")
    lines.extend(["", "## Example Generated Offers", ""])
    examples = payload.get("offers", [])[:30]
    if examples:
        lines.extend(["| Type | Hub | Course | Date | Time | CTA |", "| --- | --- | --- | --- | --- | --- |"])
        for offer in examples:
            lines.append(
                f"| {offer.get('offer_type')} | {offer.get('hub_slug')} | {offer.get('course_title')} | "
                f"{offer.get('date')} | {offer.get('start_time')} | {offer.get('cta_label')} |"
            )
    else:
        lines.append("- None")
    lines.extend(["", "## Planned Future Visibility", ""])
    planned = payload.get("planned_future_visibility", [])
    if planned:
        lines.extend(["| Course | Page | Date | Time | First Public At | Reason | Score |", "| --- | --- | --- | --- | --- | --- | ---: |"])
        for offer in planned[:30]:
            lines.append(
                f"| {offer.get('course_title')} | {offer.get('target_page') or offer.get('hub_slug')} | "
                f"{offer.get('date')} | {offer.get('start_time')} | {offer.get('first_public_at')} | "
                f"{offer.get('not_public_reason')} | {offer.get('score', 0)} |"
            )
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_stack_trace_report(trace: dict[str, Any], summary: dict[str, Any]) -> str:
    lines = [
        "# Stacking + Seeding Trace",
        "",
        "Read-only diagnostic for the universal offer engine. Real Enrollware iCal classes remain authoritative; generated offers are either deterministic appointment URLs or request-only availability offers.",
        "",
        "## Summary",
        "",
        f"- Availability blocks considered: {summary.get('availability_blocks_considered', 0)}",
        f"- Stack groups created: {summary.get('stack_groups_created', 0)}",
        f"- Appointment-backed offers generated: {summary.get('appointment_url_offers_generated', 0)}",
        f"- Request-only offers generated: {summary.get('request_only_block_offers_generated', 0)}",
        f"- Future request block offers generated: {summary.get('future_request_block_offers_generated', 0)}",
        f"- Total generated hub-only offers: {summary.get('total_generated_offers', 0)}",
        f"- Planned future visibility candidates: {summary.get('planned_future_visibility_count', 0)}",
        "",
        "## Rejection Histogram",
        "",
    ]
    histogram = trace.get("rejection_histogram", {})
    if histogram:
        lines.extend(f"- `{reason}`: {count}" for reason, count in histogram.items())
    else:
        lines.append("- None")

    lines.extend(["", "## Candidate States", ""])
    state_counts = trace.get("candidate_state_counts", {})
    if state_counts:
        lines.extend(f"- `{state}`: {count}" for state, count in state_counts.items())
    else:
        lines.append("- None")

    lines.extend(["", "## Planned Future Visibility", ""])
    planned = trace.get("planned_future_visibility_offers", [])
    if planned:
        lines.extend(["| Course | Page | Delivery | Candidate Start | First Public At | Reason | Score |", "| --- | --- | --- | --- | --- | --- | ---: |"])
        for offer in planned[:60]:
            lines.append(
                f"| {offer.get('course_title')} | {offer.get('target_page') or offer.get('hub_slug')} | "
                f"{offer.get('delivery_bucket')} | {offer.get('candidate_start')} | {offer.get('first_public_at')} | "
                f"{offer.get('not_public_reason')} | {offer.get('score', 0)} |"
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Minimum Visible Offer Rejection Detail", ""])
    min_groups = trace.get("minimum_visible_rejection_groups", {})
    if min_groups:
        lines.extend([
            "Minimum-visible checks are scoped by `course_key | hub | delivery bucket` and the configured lookahead window.",
            "",
            "| Visible inventory key | Rejections | Counted sources | Counted dates |",
            "| --- | ---: | --- | --- |",
        ])
        for key, item in sorted(min_groups.items()):
            sources = ", ".join(f"{source}: {count}" for source, count in (item.get("counted_sources") or {}).items()) or UNKNOWN
            dates = ", ".join((item.get("counted_dates") or [])[:8])
            if len(item.get("counted_dates") or []) > 8:
                dates += ", ..."
            lines.append(f"| `{key}` | {item.get('count', 0)} | {sources} | {dates or UNKNOWN} |")
    else:
        lines.append("- None")

    lines.extend(["", "## Stack Groups", ""])
    groups = trace.get("stack_groups_created", [])
    if groups:
        for group in groups:
            lines.extend([
                f"### {group.get('stack_group_id')}",
                "",
                f"- Block: `{group.get('block_id')}`",
                f"- Instructor: {group.get('instructor') or UNKNOWN}",
                f"- Location: {group.get('location') or UNKNOWN}",
                f"- Window: `{group.get('block_start')}` to `{group.get('block_end')}`",
                f"- Offers: {group.get('offer_count', 0)}",
                "",
            ])
            lines.extend(["| Type | Course | Display Start | Consumption Window | URL? |", "| --- | --- | --- | --- | --- |"])
            for offer in group.get("proposed_course_offers", []):
                lines.append(
                    f"| {offer.get('offer_type')} | {offer.get('course_title')} | {offer.get('display_start')} | "
                    f"{offer.get('scheduler_consumption_start')} to {offer.get('scheduler_consumption_end')} | "
                    f"{'yes' if offer.get('deterministic_url_available') else 'no'} |"
                )
            lines.append("")
    else:
        lines.append("- No stack groups created.")

    lines.extend(["", "## Availability Blocks Considered", ""])
    blocks = trace.get("availability_blocks_considered", [])
    if blocks:
        lines.extend(["| Block | Instructor | Location | Window | Candidates | Accepted | Top rejection reasons |", "| --- | --- | --- | --- | ---: | ---: | --- |"])
        for block in blocks[:100]:
            reasons = ", ".join(f"{reason}: {count}" for reason, count in list((block.get("rejection_reasons") or {}).items())[:5])
            lines.append(
                f"| `{block.get('block_id')}` | {block.get('instructor') or UNKNOWN} | {block.get('location') or UNKNOWN} | "
                f"{block.get('block_start')} to {block.get('block_end')} | {block.get('candidate_count', 0)} | "
                f"{len(block.get('accepted_offer_ids') or [])} | {reasons or 'None'} |"
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Public Offers By Course / Delivery Page", ""])
    by_page = trace.get("public_offers_by_course_delivery_page", {})
    if by_page:
        lines.extend(["| Page key | Hub | Course | Type |", "| --- | --- | --- | --- |"])
        for key, item in sorted(by_page.items()):
            lines.append(f"| `{key}` | {item.get('hub_slug')} | {item.get('course_title')} | {item.get('offer_type')} |")
    else:
        lines.append("- None")

    lines.extend(["", "## Notes", ""])
    lines.append("- Deterministic appointment URLs are only generated by the existing seed URL preview pipeline.")
    lines.append("- Request-only offers are not public seated classes and are not written into `docs/data/schedule_future.json`.")
    lines.append("- Cooldown decisions appear as `offer_again_cooldown_window` when configured policy suppresses a candidate.")
    return "\n".join(lines) + "\n"


def build_inventory(loaded: dict[str, Any]) -> dict[str, Any]:
    course_catalog = course_catalog_by_id(loaded.get("course_catalog"))
    course_map = course_map_by_id(loaded.get("course_map"))
    hubs = hub_tab_index(loaded.get("slug_hubs"), course_code_lookup(course_map))
    policy = loaded.get("universal_offer_policy") if isinstance(loaded.get("universal_offer_policy"), dict) else {}
    real_counts = session_counts_by_course(loaded.get("schedule_future"))
    real_starts = real_session_starts_by_course(loaded.get("schedule_future"))
    appointment_offers, appointment_rejections = build_appointment_url_offers(
        loaded.get("seed_appointment_url_preview"),
        course_catalog,
        course_map,
        hubs,
        loaded.get("course_visibility_policy") or {},
        policy,
    )
    visible_inventory = visible_inventory_by_course_delivery_page(
        loaded.get("schedule_future") or {},
        appointment_offers,
        course_catalog,
        course_map,
        hubs,
        policy,
    )
    request_offers, request_rejections, planned_request_offers = build_request_block_offers(
        loaded.get("dynamic_offers_preview"),
        real_starts,
        visible_inventory,
        appointment_offers,
        course_catalog,
        course_map,
        hubs,
        loaded.get("course_visibility_policy") or {},
        policy,
    )
    future_request_offers, future_request_rejections = build_future_request_block_offers(
        loaded.get("dynamic_offers_preview"),
        course_catalog,
        course_map,
        hubs,
        loaded.get("course_visibility_policy") or {},
        policy,
    )
    offers = sorted([*appointment_offers, *request_offers, *future_request_offers], key=lambda offer: (offer.get("hub_slug", ""), offer.get("date", ""), offer.get("start_time", ""), offer.get("course_id", "")))
    rejections = [*appointment_rejections, *request_rejections]
    stack_trace = build_stack_trace(
        loaded.get("dynamic_offers_preview") or {},
        offers,
        rejections,
        planned_request_offers,
        appointment_offers,
        loaded.get("schedule_future") or {},
        policy,
    )
    course_page_counts: Counter[str] = Counter()
    for offer in offers:
        course_key_value = clean_text(offer.get("course_key"))
        if course_key_value == "aha_heartsaver_first_aid_cpr_aed":
            course_page_counts["heartsaver-first-aid-cpr-aed"] += 1
        elif course_key_value == "aha_heartsaver_first_aid_cpr_aed_blended":
            course_page_counts["heartsaver-first-aid-cpr-aed"] += 1
        elif course_key_value == "aha_heartsaver_cpr_aed":
            course_page_counts["heartsaver-cpr-aed"] += 1
        elif course_key_value == "aha_heartsaver_cpr_aed_online":
            course_page_counts["heartsaver-cpr-aed"] += 1
        elif course_key_value in {"aha_heartsaver_pediatric_first_aid_cpr_aed_in_person", "aha_heartsaver_pediatric_first_aid_cpr_aed_online"}:
            course_page_counts["heartsaver-pediatric-first-aid-cpr-aed"] += 1

    summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "real_seated_classes_read": sum(real_counts.values()),
        "dynamic_offers_read": len(loaded.get("dynamic_offers_preview", {}).get("offers", [])) if isinstance(loaded.get("dynamic_offers_preview"), dict) else 0,
        "public_sellable_offers_read": len(loaded.get("public_sellable_offers_preview", {}).get("offers", [])) if isinstance(loaded.get("public_sellable_offers_preview"), dict) else 0,
        "appointment_url_offers_generated": len(appointment_offers),
        "request_only_block_offers_generated": len(request_offers),
        "future_request_block_offers_generated": len(future_request_offers),
        "total_generated_offers": len(offers),
        "public_now_offer_count": len(offers),
        "planned_future_visibility_count": len(planned_request_offers),
        "availability_blocks_considered": stack_trace.get("availability_block_count", 0),
        "stack_groups_created": len(stack_trace.get("stack_groups_created", [])),
        "offers_by_type": grouped_counts(offers, "offer_type"),
        "offers_by_hub": grouped_counts(offers, "hub_slug"),
        "offers_by_course": grouped_counts(offers, "course_title"),
        "future_request_offers_by_course": grouped_counts(future_request_offers, "course_title"),
        "future_request_rejections_by_reason": dict(Counter(clean_text(item.get("reason_code")) or UNKNOWN for item in future_request_rejections).most_common()),
        "course_page_offer_counts": dict(sorted(course_page_counts.items())),
        "rejections_by_reason": dict(Counter(clean_text(item.get("reason_code")) or UNKNOWN for item in rejections).most_common()),
    }
    return {
        "generated_at": summary["generated_at"],
        "read_only": True,
        "public_site_affected": False,
        "real_seated_classes_source": str(SCHEDULE_FUTURE_PATH),
        "dynamic_offers_source": str(DYNAMIC_OFFERS_PATH),
        "seed_appointment_url_source": str(SEED_APPOINTMENT_URL_PREVIEW_PATH),
        "policy_source": str(UNIVERSAL_OFFER_POLICY_PATH),
        "summary": summary,
        "offers": offers,
        "planned_future_visibility": planned_request_offers[:1000],
        "rejections": rejections[:1000],
        "stack_trace": stack_trace,
    }


def run() -> dict[str, Any]:
    paths = {
        "schedule_future": SCHEDULE_FUTURE_PATH,
        "dynamic_offers_preview": DYNAMIC_OFFERS_PATH,
        "public_sellable_offers_preview": PUBLIC_SELLABLE_OFFERS_PATH,
        "seed_appointment_url_preview": SEED_APPOINTMENT_URL_PREVIEW_PATH,
        "course_catalog": COURSE_CATALOG_PATH,
        "course_map": COURSE_MAP_PATH,
        "slug_hubs": SLUG_HUBS_PATH,
        "course_visibility_policy": COURSE_VISIBILITY_POLICY_PATH,
        "universal_offer_policy": UNIVERSAL_OFFER_POLICY_PATH,
    }
    loaded: dict[str, Any] = {}
    missing: dict[str, str] = {}
    for name, path in paths.items():
        payload, error = read_json(path)
        if error:
            missing[name] = error
        else:
            loaded[name] = payload
    payload = build_inventory(loaded)
    payload["files_missing_or_unreadable"] = missing
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(payload), encoding="utf-8")
    STACK_TRACE_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    STACK_TRACE_JSON_PATH.write_text(json.dumps(payload["stack_trace"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    STACK_TRACE_MD_PATH.write_text(render_stack_trace_report(payload["stack_trace"], payload["summary"]), encoding="utf-8")
    return {
        "summary": payload["summary"],
        "missing": missing,
        "output_paths": [OUTPUT_PATH, REPORT_PATH, STACK_TRACE_JSON_PATH, STACK_TRACE_MD_PATH],
    }


def main() -> int:
    result = run()
    summary = result["summary"]
    print("Universal offer inventory build complete.")
    print("Real seated Enrollware classes remain separate in docs/data/schedule_future.json.")
    print(f"Real seated classes read: {summary['real_seated_classes_read']}")
    print(f"Dynamic offers read: {summary['dynamic_offers_read']}")
    print(f"Appointment URL offers generated: {summary['appointment_url_offers_generated']}")
    print(f"Request-only block offers generated: {summary['request_only_block_offers_generated']}")
    print(f"Total generated hub-only offers: {summary['total_generated_offers']}")
    print("Output files:")
    for path in result["output_paths"]:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
