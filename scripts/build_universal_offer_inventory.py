from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
CONFIG_DIR = ROOT / "data" / "config"
DOCS_DIR = ROOT / "docs"

SCHEDULE_FUTURE_PATH = DOCS_DIR / "data" / "schedule_future.json"
DYNAMIC_OFFERS_PATH = AUDIT_DIR / "dynamic_offers_preview.json"
PUBLIC_SELLABLE_OFFERS_PATH = AUDIT_DIR / "public_sellable_offers_preview.json"
SEED_APPOINTMENT_URL_PREVIEW_PATH = AUDIT_DIR / "seed_appointment_url_preview.json"
COURSE_CATALOG_PATH = CONFIG_DIR / "course_catalog.json"
COURSE_MAP_PATH = CONFIG_DIR / "course_map.json"
SLUG_HUBS_PATH = CONFIG_DIR / "slug_hubs.json"
COURSE_VISIBILITY_POLICY_PATH = CONFIG_DIR / "course_visibility_policy.json"
UNIVERSAL_OFFER_POLICY_PATH = CONFIG_DIR / "universal_offer_policy.json"

OUTPUT_PATH = AUDIT_DIR / "universal_offer_inventory.json"
REPORT_PATH = AUDIT_DIR / "universal_offer_inventory_report.md"
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
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
        offers.append({
            "public_offer_id": f"appointment-{clean_text(preview.get('seed_id')) or clean_text(preview.get('source_offer_id'))}",
            "offer_type": "appointment_url",
            "cta_label": policy.get("default_appointment_cta_label", "Check this date/time"),
            "course_id": course_id,
            "course_key": course_key(course, course_map_record),
            "course_title": clean_text(preview.get("course_title")) or course_title(course, course_map_record),
            "course_family": course_family(course, course_map_record),
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
            "display_note": "Available appointment-backed class option.",
            "public_schedule_row_created": False,
            "standalone_class_lander_created": False,
        })
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
    real_counts: Counter[str],
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
    max_per_week = int(policy.get("max_request_block_offers_per_course_per_week", 2) or 2)
    max_per_hub = int(policy.get("max_total_request_block_offers_per_hub", 12) or 12)
    preferred_minutes = [clean_text(item) for item in policy.get("preferred_start_minutes", []) if clean_text(item)]
    minimum_lead_hours = int(policy.get("minimum_lead_hours", 0) or 0)
    earliest_start = datetime.now() + timedelta(hours=minimum_lead_hours)
    selected_source_ids = {clean_text(offer.get("source_offer_id")) for offer in appointment_offers}
    visible_counts = Counter(real_counts)
    visible_counts.update(clean_text(offer.get("course_id")) for offer in appointment_offers if clean_text(offer.get("course_id")))
    course_request_counts: Counter[str] = Counter()
    course_week_counts: Counter[tuple[str, str]] = Counter()
    hub_counts: Counter[str] = Counter()
    locks = selected_seed_locks(appointment_offers)
    built: list[dict[str, Any]] = []
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
        if visible_counts[course_id] >= min_visible:
            rejections.append({**context, "reason_code": "minimum_visible_offers_already_met"})
            continue
        if course_request_counts[course_id] >= max_per_course:
            rejections.append({**context, "reason_code": "max_request_block_offers_per_course"})
            continue
        start_dt = parse_dt(offer.get("scheduler_consumption_start") or offer.get("appointment_display_start") or offer.get("start_datetime"))
        if not start_dt:
            rejections.append({**context, "reason_code": "missing_start_datetime"})
            continue
        if start_dt < earliest_start:
            rejections.append({**context, "reason_code": "inside_minimum_lead_time"})
            continue
        week_key = f"{start_dt.isocalendar().year}-W{start_dt.isocalendar().week:02d}"
        if course_week_counts[(course_id, week_key)] >= max_per_week:
            rejections.append({**context, "reason_code": "max_request_block_offers_per_course_per_week"})
            continue
        hub_slug, tab_ids = hub_and_tabs_for_course(course_id, course, course_map_record, hubs, policy)
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
        built_offer = {
            "public_offer_id": f"request-{clean_text(offer.get('offer_id'))}",
            "offer_type": "request_only_block",
            "cta_label": policy.get("default_request_cta_label", "Ask about this time"),
            "course_id": course_id,
            "course_key": course_key(course, course_map_record),
            "course_title": title,
            "course_family": family,
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
            "display_note": policy.get("request_offer_copy"),
            "public_schedule_row_created": False,
            "standalone_class_lander_created": False,
        }
        built.append(built_offer)
        visible_counts[course_id] += 1
        course_request_counts[course_id] += 1
        course_week_counts[(course_id, week_key)] += 1
        hub_counts[hub_slug] += 1
        locks.append({
            "course_id": course_id,
            "hub_slug": hub_slug,
            "start": built_offer.get("scheduler_consumption_start") or built_offer.get("start_datetime"),
            "end": built_offer.get("scheduler_consumption_end") or built_offer.get("end_datetime"),
            "location": built_offer.get("location_name"),
            "instructor": built_offer.get("instructor_display_name"),
        })
    return built, rejections


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
        f"- Total hub-only generated offers: {summary['total_generated_offers']}",
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
    lines.append("")
    return "\n".join(lines)


def build_inventory(loaded: dict[str, Any]) -> dict[str, Any]:
    course_catalog = course_catalog_by_id(loaded.get("course_catalog"))
    course_map = course_map_by_id(loaded.get("course_map"))
    hubs = hub_tab_index(loaded.get("slug_hubs"), course_code_lookup(course_map))
    policy = loaded.get("universal_offer_policy") if isinstance(loaded.get("universal_offer_policy"), dict) else {}
    real_counts = session_counts_by_course(loaded.get("schedule_future"))
    appointment_offers, appointment_rejections = build_appointment_url_offers(
        loaded.get("seed_appointment_url_preview"),
        course_catalog,
        course_map,
        hubs,
        loaded.get("course_visibility_policy") or {},
        policy,
    )
    request_offers, request_rejections = build_request_block_offers(
        loaded.get("dynamic_offers_preview"),
        real_counts,
        appointment_offers,
        course_catalog,
        course_map,
        hubs,
        loaded.get("course_visibility_policy") or {},
        policy,
    )
    offers = sorted([*appointment_offers, *request_offers], key=lambda offer: (offer.get("hub_slug", ""), offer.get("date", ""), offer.get("start_time", ""), offer.get("course_id", "")))
    rejections = [*appointment_rejections, *request_rejections]
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
        "total_generated_offers": len(offers),
        "offers_by_type": grouped_counts(offers, "offer_type"),
        "offers_by_hub": grouped_counts(offers, "hub_slug"),
        "offers_by_course": grouped_counts(offers, "course_title"),
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
        "rejections": rejections[:1000],
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
    return {
        "summary": payload["summary"],
        "missing": missing,
        "output_paths": [OUTPUT_PATH, REPORT_PATH],
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
