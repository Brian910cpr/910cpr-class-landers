from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import openpyxl

from scripts import build_slug_hubs


from scripts.local_data_paths import public_sellable_offers_preview_path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "data" / "config"
AUDIT_DIR = ROOT / "data" / "audit"

COURSE_CATALOG_PATH = CONFIG_DIR / "course_catalog.json"
COURSE_MAP_PATH = CONFIG_DIR / "course_map.json"
COURSE_EXPORT_PATH = ROOT / "data" / "raw" / "course-export.xlsx"
SLUG_HUBS_PATH = CONFIG_DIR / "slug_hubs.json"
PUBLIC_SELLABLE_PATH = public_sellable_offers_preview_path(ROOT)
PUBLIC_OFFER_POLICY_PATH = CONFIG_DIR / "public_offer_policy.json"
CONSUMPTION_RULES_PATH = ROOT / "data" / "inventory" / "course_consumption_rules.json"
COURSE_VISIBILITY_PATH = CONFIG_DIR / "course_visibility_policy.json"

COURSE_MASTER_SCHEMA_PATH = CONFIG_DIR / "course_master.schema.json"
COURSE_MASTER_PATH = CONFIG_DIR / "course_master.json"
REPORT_JSON_PATH = AUDIT_DIR / "course_master_build_report.json"
REPORT_MD_PATH = AUDIT_DIR / "course_master_build_report.md"

UNKNOWN = "unknown"
NOT_APPLICABLE = "not_applicable"

COURSE_FIELDS = [
    "course_key",
    "enrollware_course_id",
    "enrollware_name",
    "internal_title",
    "public_short_title",
    "public_long_title",
    "course_family",
    "course_family_type",
    "provider",
    "discipline",
    "format",
    "audience",
    "status",
    "public_visibility",
    "slug_page",
    "hub_tab",
    "sort_priority",
    "cta_text",
    "description_short",
    "description_long",
    "prerequisites",
    "what_is_included",
    "what_to_bring",
    "classroom_duration_minutes",
    "skills_duration_minutes",
    "online_component_required",
    "scheduler_display_duration_minutes",
    "setup_buffer_minutes",
    "cleanup_buffer_minutes",
    "scheduler_consumption_minutes",
    "minimum_lead_time_hours",
    "maximum_lookahead_days",
    "allowed_days_of_week",
    "allowed_start_time_min",
    "allowed_start_time_max",
    "dynamic_offer_allowed",
    "appointment_seed_allowed",
    "requires_instructor_availability",
    "requires_existing_enrollware_class",
    "can_stack_with_same_course",
    "minimum_gap_minutes",
    "max_students_default",
    "min_students_default",
    "registration_backend",
    "enrollware_course_url",
    "appointment_course_id",
    "appointment_allowed",
    "appointment_day_id_strategy",
    "appointment_location_strategy",
    "allows_unscheduled_students",
    "base_price",
    "shipping_price",
    "add_ons",
    "add_on_policy",
    "manual_required",
    "manual_included",
    "discount_eligible",
    "certification_type",
    "certification_validity_months",
    "card_type",
    "secondary_card_type",
    "ecard_code",
    "keycode_bank",
    "allowed_instructor_ids",
    "allowed_location_ids",
    "required_equipment",
    "room_requirements",
    "notes_internal",
    "source_files",
    "data_quality_status",
    "missing_required_fields",
]

LIST_FIELDS = {
    "hub_tab",
    "prerequisites",
    "what_is_included",
    "what_to_bring",
    "allowed_days_of_week",
    "add_ons",
    "allowed_instructor_ids",
    "allowed_location_ids",
    "required_equipment",
    "room_requirements",
    "source_files",
    "missing_required_fields",
}
BOOLEAN_FIELDS = {
    "online_component_required",
    "dynamic_offer_allowed",
    "appointment_seed_allowed",
    "requires_instructor_availability",
    "requires_existing_enrollware_class",
    "can_stack_with_same_course",
    "appointment_allowed",
    "allows_unscheduled_students",
    "manual_required",
    "manual_included",
    "discount_eligible",
}
NUMERIC_FIELDS = {
    "sort_priority",
    "classroom_duration_minutes",
    "skills_duration_minutes",
    "scheduler_display_duration_minutes",
    "setup_buffer_minutes",
    "cleanup_buffer_minutes",
    "scheduler_consumption_minutes",
    "minimum_lead_time_hours",
    "maximum_lookahead_days",
    "minimum_gap_minutes",
    "max_students_default",
    "min_students_default",
    "base_price",
    "shipping_price",
    "certification_validity_months",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean_text(value).lower()).strip("_")


def int_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or value in ("", None):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def money_or_none(value: Any) -> float | None:
    text = clean_text(value).replace("$", "").replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def bool_from_export(value: Any) -> bool | None:
    text = clean_text(value).lower()
    if text in {"yes", "true", "1"}:
        return True
    if text in {"no", "false", "0"}:
        return False
    return None


def split_list(value: Any) -> list[str]:
    text = clean_text(value)
    if not text:
        return []
    return [item.strip() for item in re.split(r",|;", text) if item.strip()]


def load_course_export() -> tuple[list[dict[str, Any]], list[str]]:
    if not COURSE_EXPORT_PATH.exists():
        return [], []
    workbook = openpyxl.load_workbook(COURSE_EXPORT_PATH, read_only=True, data_only=True)
    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return [], []
    headers = [clean_text(header) for header in rows[0]]
    records: list[dict[str, Any]] = []
    for row in rows[1:]:
        record = {headers[index]: row[index] if index < len(row) else None for index in range(len(headers))}
        record["_course_id_from_meta"] = course_id_from_export_description(record.get("Description"))
        records.append(record)
    return records, headers


def course_id_from_export_description(value: Any) -> str:
    text = clean_text(value)
    match = re.search(r'"course_id"\s*:\s*(\d+)', text)
    return match.group(1) if match else ""


def index_export_records(records: list[dict[str, Any]], course_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed = {record["_course_id_from_meta"]: record for record in records if record.get("_course_id_from_meta")}
    by_name = {normalize_key(record.get("Name")): record for record in records if clean_text(record.get("Name"))}
    for course_id, course in course_map.get("courses_by_id", {}).items():
        if course_id in indexed:
            continue
        names = [
            course.get("official_title"),
            course.get("clean_title"),
            course.get("short_title"),
            *(course.get("title_aliases", []) if isinstance(course.get("title_aliases"), list) else []),
        ]
        for name in names:
            match = by_name.get(normalize_key(name))
            if match:
                indexed[course_id] = match
                break
    return indexed


def consumption_rules_by_id(payload: Any) -> dict[str, dict[str, Any]]:
    rules = payload.get("rules", []) if isinstance(payload, dict) else []
    return {clean_text(rule.get("course_id")): rule for rule in rules if isinstance(rule, dict) and clean_text(rule.get("course_id"))}


def course_map_by_id(payload: Any) -> dict[str, dict[str, Any]]:
    return payload.get("courses_by_id", {}) if isinstance(payload, dict) and isinstance(payload.get("courses_by_id"), dict) else {}


def public_sellable_course_ids(payload: Any) -> set[str]:
    offers = payload.get("offers", []) if isinstance(payload, dict) else []
    return {clean_text(offer.get("course_id")) for offer in offers if isinstance(offer, dict) and clean_text(offer.get("course_id"))}


def visibility_state(course_id: str, payload: Any) -> str:
    if not isinstance(payload, dict):
        return "active_public"
    courses = payload.get("courses", {}) if isinstance(payload.get("courses"), dict) else {}
    record = courses.get(course_id, {})
    return clean_text(record.get("state") if isinstance(record, dict) else record) or clean_text(payload.get("default_state")) or "active_public"


def slug_tab_mapping(course_map: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    manifest = read_json(SLUG_HUBS_PATH)
    pages = manifest.get("pages", []) if isinstance(manifest, dict) else manifest
    code_to_course_ids: dict[str, set[str]] = {}
    for course_id, course in course_map.items():
        code = clean_text(course.get("course_code"))
        if code:
            code_to_course_ids.setdefault(code, set()).add(course_id)
    mapping: dict[str, dict[str, Any]] = {}
    for page in pages:
        if not isinstance(page, dict):
            continue
        slug = clean_text(page.get("slug"))
        for tab in page.get("tabs", []):
            if not isinstance(tab, dict):
                continue
            tab_id = clean_text(tab.get("id"))
            for code in tab.get("course_codes", []) if isinstance(tab.get("course_codes"), list) else []:
                for course_id in code_to_course_ids.get(clean_text(code), set()):
                    entry = mapping.setdefault(course_id, {"slug_page": f"docs/{slug}.html", "hub_tab": set()})
                    entry["hub_tab"].add(tab_id)
    for course_id, course in course_map.items():
        course_key = clean_text(course.get("course_key"))
        family = clean_text(course.get("family"))
        slug = build_slug_hubs.APPOINTMENT_HUB_BY_FAMILY.get(family)
        tab_ids = build_slug_hubs.APPOINTMENT_COURSE_TAB_IDS.get(course_key, set())
        if slug and tab_ids:
            entry = mapping.setdefault(course_id, {"slug_page": f"docs/{slug}.html", "hub_tab": set()})
            entry["slug_page"] = entry.get("slug_page") or f"docs/{slug}.html"
            entry["hub_tab"].update(tab_ids)
    return {course_id: {"slug_page": value["slug_page"], "hub_tab": sorted(value["hub_tab"])} for course_id, value in mapping.items()}


def empty_record() -> dict[str, Any]:
    record: dict[str, Any] = {}
    for field in COURSE_FIELDS:
        if field in LIST_FIELDS:
            record[field] = []
        elif field in BOOLEAN_FIELDS:
            record[field] = False
        elif field in NUMERIC_FIELDS:
            record[field] = None
        else:
            record[field] = UNKNOWN
    record["registration_backend"] = "enrollware"
    record["appointment_day_id_strategy"] = UNKNOWN
    record["appointment_location_strategy"] = UNKNOWN
    record["add_on_policy"] = UNKNOWN
    record["status"] = "active"
    record["public_visibility"] = "active_public"
    return record


def build_course_record(
    catalog_course: dict[str, Any],
    map_course: dict[str, Any],
    export_record: dict[str, Any] | None,
    rule: dict[str, Any] | None,
    public_ids: set[str],
    visibility_policy: Any,
    mapping: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    course_id = clean_text(catalog_course.get("course_id") or map_course.get("course_id"))
    record = empty_record()
    record.update(
        {
            "course_key": clean_text(catalog_course.get("course_key") or map_course.get("course_key")) or UNKNOWN,
            "enrollware_course_id": course_id or UNKNOWN,
            "enrollware_name": clean_text((export_record or {}).get("Name") or catalog_course.get("official_title") or map_course.get("official_title")) or UNKNOWN,
            "internal_title": clean_text(catalog_course.get("official_title") or map_course.get("official_title")) or UNKNOWN,
            "public_short_title": clean_text(catalog_course.get("short_title") or map_course.get("clean_title") or map_course.get("official_title")) or UNKNOWN,
            "public_long_title": clean_text(map_course.get("official_title") or catalog_course.get("official_title")) or UNKNOWN,
            "course_family": clean_text(catalog_course.get("family") or map_course.get("family")) or UNKNOWN,
            "course_family_type": clean_text(catalog_course.get("subtype") or map_course.get("subtype")) or UNKNOWN,
            "provider": clean_text(catalog_course.get("provider") or map_course.get("provider") or map_course.get("certifying_body")) or UNKNOWN,
            "discipline": clean_text((export_record or {}).get("Discipline")) or UNKNOWN,
            "format": clean_text(catalog_course.get("delivery_type") or map_course.get("delivery_mode")) or UNKNOWN,
            "audience": clean_text(map_course.get("who_for") or map_course.get("who_class_for")) or UNKNOWN,
            "status": "active" if map_course.get("active", True) is not False else "inactive",
            "public_visibility": visibility_state(course_id, visibility_policy),
            "sort_priority": int_or_none((rule or {}).get("public_priority")),
            "cta_text": "Check this date/time" if catalog_course.get("appointment_allowed") is True else "Book Seat",
            "description_short": clean_text(map_course.get("short_description")) or UNKNOWN,
            "description_long": clean_text(map_course.get("long_description") or (export_record or {}).get("Description")) or UNKNOWN,
            "prerequisites": split_list(map_course.get("prerequisites")) or [],
            "what_is_included": split_list(map_course.get("what_to_expect")),
            "what_to_bring": [],
            "online_component_required": clean_text(catalog_course.get("blended_classroom_skills")).lower() == "blended"
            or clean_text(map_course.get("delivery_mode")).upper() == "BL",
            "requires_instructor_availability": True,
            "requires_existing_enrollware_class": False,
            "can_stack_with_same_course": False,
            "registration_backend": "enrollware",
            "enrollware_course_url": clean_text(map_course.get("public_schedule_url")) or f"https://coastalcprtraining.enrollware.com/schedule#ct{course_id}",
            "appointment_course_id": course_id or UNKNOWN,
            "appointment_allowed": catalog_course.get("appointment_allowed") is True,
            "appointment_day_id_strategy": "owned_container" if catalog_course.get("appointment_container_required") is True else UNKNOWN,
            "appointment_location_strategy": "location_resource_map",
            "allows_unscheduled_students": bool_from_export((export_record or {}).get("Allows Unscheduled Students?")) or False,
            "base_price": money_or_none((export_record or {}).get("Class Price") if export_record else map_course.get("price")),
            "shipping_price": money_or_none((export_record or {}).get("Shipping Price")) if export_record else None,
            "add_ons": split_list((export_record or {}).get("Add-ons")),
            "add_on_policy": "from_enrollware_export" if export_record and clean_text(export_record.get("Add-ons")) else UNKNOWN,
            "manual_required": "manual_required" in json.dumps(catalog_course).lower() or "MANUAL:" in clean_text((export_record or {}).get("Add-ons")),
            "manual_included": False,
            "discount_eligible": False,
            "certification_type": clean_text(map_course.get("certification_card") or (export_record or {}).get("Card Type")) or UNKNOWN,
            "certification_validity_months": 24 if "AHA" in clean_text(catalog_course.get("provider") or map_course.get("provider")) else None,
            "card_type": clean_text((export_record or {}).get("Card Type")) or UNKNOWN,
            "secondary_card_type": clean_text((export_record or {}).get("Secondary Card Type")) or NOT_APPLICABLE,
            "ecard_code": clean_text((export_record or {}).get("eCard Code")) or UNKNOWN,
            "keycode_bank": clean_text((export_record or {}).get("Keycode Bank")) or UNKNOWN,
            "allowed_instructor_ids": list(catalog_course.get("required_instructor_certifications", [])) if isinstance(catalog_course.get("required_instructor_certifications"), list) else [],
            "allowed_location_ids": [],
            "required_equipment": list(catalog_course.get("required_resources", [])) if isinstance(catalog_course.get("required_resources"), list) else [],
            "room_requirements": [],
            "notes_internal": "Generated from course_catalog.json; not authoritative for production behavior yet.",
            "source_files": ["data/config/course_catalog.json"],
        }
    )
    if map_course:
        record["source_files"].append("data/config/course_map.json")
    if export_record:
        record["source_files"].append("data/raw/course-export.xlsx")
    if rule:
        record["source_files"].append("data/inventory/course_consumption_rules.json")
    if course_id in mapping:
        record["slug_page"] = mapping[course_id]["slug_page"]
        record["hub_tab"] = mapping[course_id]["hub_tab"]
        record["source_files"].append("data/config/slug_hubs.json")
    duration = int_or_none(catalog_course.get("duration_minutes")) or int_or_none((rule or {}).get("duration_minutes"))
    setup = int_or_none(catalog_course.get("setup_buffer_minutes"))
    cleanup = int_or_none(catalog_course.get("cleanup_buffer_minutes"))
    record["classroom_duration_minutes"] = duration
    record["skills_duration_minutes"] = duration if record["online_component_required"] else None
    record["scheduler_display_duration_minutes"] = duration
    record["setup_buffer_minutes"] = setup
    record["cleanup_buffer_minutes"] = cleanup
    record["scheduler_consumption_minutes"] = duration + setup + cleanup if duration is not None and setup is not None and cleanup is not None else None
    policy = read_json(PUBLIC_OFFER_POLICY_PATH) if PUBLIC_OFFER_POLICY_PATH.exists() else {}
    window = policy.get("dynamic_public_start_time_window", {}) if isinstance(policy, dict) else {}
    record["minimum_lead_time_hours"] = int_or_none(policy.get("minimum_lead_hours"))
    record["maximum_lookahead_days"] = int_or_none(policy.get("maximum_days_out"))
    record["allowed_days_of_week"] = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    record["allowed_start_time_min"] = clean_text(window.get("earliest_start")) or UNKNOWN
    record["allowed_start_time_max"] = clean_text(window.get("latest_start")) or UNKNOWN
    record["minimum_gap_minutes"] = int_or_none((rule or {}).get("minimum_reservation_block_minutes"))
    record["max_students_default"] = int_or_none(catalog_course.get("default_capacity")) or int_or_none((rule or {}).get("default_capacity"))
    record["min_students_default"] = int_or_none(catalog_course.get("minimum_capacity")) or 1
    missing = missing_fields(record)
    scheduler_ready = all(record[field] is not None for field in ["classroom_duration_minutes", "setup_buffer_minutes", "cleanup_buffer_minutes", "scheduler_consumption_minutes"])
    public_dynamic_candidate = course_id in public_ids or record["appointment_allowed"] is True
    record["dynamic_offer_allowed"] = bool(public_dynamic_candidate and scheduler_ready and record["status"] == "active")
    record["appointment_seed_allowed"] = record["dynamic_offer_allowed"]
    if public_dynamic_candidate and not scheduler_ready:
        record["notes_internal"] += " Dynamic offers blocked until duration/setup/cleanup are reviewed."
    missing = missing_fields(record)
    record["missing_required_fields"] = missing
    if record["status"] == "inactive":
        record["data_quality_status"] = "inactive"
    elif not scheduler_ready or missing:
        record["data_quality_status"] = "needs_review" if len(missing) <= 12 else "incomplete"
    else:
        record["data_quality_status"] = "complete"
    return record


def missing_fields(record: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    important = [
        "course_key",
        "enrollware_course_id",
        "enrollware_name",
        "internal_title",
        "course_family",
        "provider",
        "format",
        "slug_page",
        "hub_tab",
        "classroom_duration_minutes",
        "setup_buffer_minutes",
        "cleanup_buffer_minutes",
        "scheduler_consumption_minutes",
        "minimum_lead_time_hours",
        "maximum_lookahead_days",
        "base_price",
        "card_type",
    ]
    for field in important:
        value = record.get(field)
        if value in (None, "", UNKNOWN) or value == []:
            missing.append(field)
    return missing


def build_schema() -> dict[str, Any]:
    properties: dict[str, Any] = {}
    for field in COURSE_FIELDS:
        if field in LIST_FIELDS:
            properties[field] = {"type": "array"}
        elif field in BOOLEAN_FIELDS:
            properties[field] = {"type": "boolean"}
        elif field in NUMERIC_FIELDS:
            properties[field] = {"type": ["number", "null"]}
        else:
            properties[field] = {"type": "string"}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "910CPR Course Master",
        "type": "object",
        "required": ["schema_version", "generated_at", "authoritative", "courses"],
        "properties": {
            "schema_version": {"type": "string"},
            "generated_at": {"type": "string"},
            "authoritative": {"type": "boolean"},
            "source_files": {"type": "array"},
            "courses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": COURSE_FIELDS,
                    "additionalProperties": False,
                    "properties": properties,
                },
            },
        },
    }


def build_report(master: dict[str, Any], export_headers: list[str], catalog_payload: Any, export_records: list[dict[str, Any]], public_payload: Any) -> dict[str, Any]:
    courses = master["courses"]
    catalog_fields = sorted({field for course in catalog_payload.get("courses", []) for field in course.keys()})
    export_fields = sorted(header for header in export_headers if header)
    public_ids = public_sellable_course_ids(public_payload)
    master_ids = {course["enrollware_course_id"] for course in courses}
    public_offers = public_payload.get("offers", []) if isinstance(public_payload, dict) else []
    missing_counts = Counter(field for course in courses for field in course["missing_required_fields"])
    scheduler_fields = ["setup_buffer_minutes", "cleanup_buffer_minutes", "scheduler_consumption_minutes"]
    render_fields = ["slug_page", "hub_tab"]
    return {
        "generated_at": master["generated_at"],
        "recommendation": {
            "course_catalog_should_be_promoted_or_renamed": False,
            "course_master_should_be_generated_from_course_catalog_plus_enrollware_export": True,
            "course_catalog_should_remain_legacy_source_input_only": False,
            "summary": "Use course_catalog.json as the preferred seed and current scheduler source, generate course_master.json as the normalized review layer, then promote after missing scheduler/rendering/export gaps are resolved.",
        },
        "counts": {
            "course_records_created": len(courses),
            "complete": sum(1 for course in courses if course["data_quality_status"] == "complete"),
            "needs_review": sum(1 for course in courses if course["data_quality_status"] == "needs_review"),
            "incomplete": sum(1 for course in courses if course["data_quality_status"] == "incomplete"),
            "inactive": sum(1 for course in courses if course["data_quality_status"] == "inactive"),
        },
        "field_comparison": {
            "course_catalog_fields": catalog_fields,
            "course_export_fields": export_fields,
            "fields_present_in_course_catalog_missing_from_course_export": sorted(set(catalog_fields) - set(export_fields)),
            "fields_present_in_course_export_missing_from_course_catalog": sorted(set(export_fields) - set(catalog_fields)),
            "scheduling_fields_neither_file_provides_fully": scheduler_fields,
            "public_rendering_fields_neither_file_provides_fully": render_fields,
        },
        "audit_answers": {
            "most_common_missing_fields": dict(missing_counts.most_common()),
            "courses_lacking_duration_or_scheduler_consumption": [
                course["enrollware_course_id"]
                for course in courses
                if any(course.get(field) is None for field in ["classroom_duration_minutes", "setup_buffer_minutes", "cleanup_buffer_minutes", "scheduler_consumption_minutes"])
            ],
            "courses_lacking_public_page_tab_mapping": [
                course["enrollware_course_id"] for course in courses if not course["slug_page"] or course["slug_page"] == UNKNOWN or not course["hub_tab"]
            ],
            "courses_lacking_enrollware_course_id": [course["course_key"] for course in courses if course["enrollware_course_id"] == UNKNOWN],
            "courses_used_by_public_sellable_offers": sorted(public_ids),
            "public_sellable_dynamic_offers_missing_course_master_data": [
                offer.get("offer_id")
                for offer in public_offers
                if clean_text(offer.get("course_id")) not in master_ids
            ],
            "every_public_sellable_dynamic_offer_resolves_to_course_master": public_ids.issubset(master_ids),
            "manual_review_fields_before_authoritative": sorted(set(missing_counts) | {"setup_buffer_minutes", "cleanup_buffer_minutes", "base_price", "card_type", "slug_page", "hub_tab"}),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    counts = report["counts"]
    recommendation = report["recommendation"]
    lines = [
        "# Course Master Build Report",
        "",
        "Generated inventory/schema report. Course Master is not authoritative for production behavior yet.",
        "",
        "## Recommendation",
        "",
        f"- Promote/rename `course_catalog.json` directly to `course_master.json`: `{recommendation['course_catalog_should_be_promoted_or_renamed']}`",
        f"- Generate `course_master.json` from `course_catalog.json` plus Enrollware export: `{recommendation['course_master_should_be_generated_from_course_catalog_plus_enrollware_export']}`",
        f"- Keep `course_catalog.json` as legacy/source input only: `{recommendation['course_catalog_should_remain_legacy_source_input_only']}`",
        f"- Summary: {recommendation['summary']}",
        "",
        "## Counts",
        "",
        f"- Course records created: `{counts['course_records_created']}`",
        f"- Complete: `{counts['complete']}`",
        f"- Needs review: `{counts['needs_review']}`",
        f"- Incomplete: `{counts['incomplete']}`",
        f"- Inactive: `{counts['inactive']}`",
        "",
        "## Field Comparison",
        "",
        f"- Fields present in `course_catalog.json` but missing from `course-export.xlsx`: `{', '.join(report['field_comparison']['fields_present_in_course_catalog_missing_from_course_export'])}`",
        f"- Fields present in `course-export.xlsx` but missing from `course_catalog.json`: `{', '.join(report['field_comparison']['fields_present_in_course_export_missing_from_course_catalog'])}`",
        f"- Scheduling fields neither file provides fully: `{', '.join(report['field_comparison']['scheduling_fields_neither_file_provides_fully'])}`",
        f"- Public rendering fields neither file provides fully: `{', '.join(report['field_comparison']['public_rendering_fields_neither_file_provides_fully'])}`",
        "",
        "## Audit Answers",
        "",
        f"- Every public sellable dynamic offer resolves to Course Master: `{report['audit_answers']['every_public_sellable_dynamic_offer_resolves_to_course_master']}`",
        f"- Courses used by public sellable offers: `{', '.join(report['audit_answers']['courses_used_by_public_sellable_offers'])}`",
        f"- Public sellable dynamic offers missing Course Master data: `{', '.join(str(x) for x in report['audit_answers']['public_sellable_dynamic_offers_missing_course_master_data']) or 'none'}`",
        f"- Courses lacking duration/scheduler consumption: `{', '.join(report['audit_answers']['courses_lacking_duration_or_scheduler_consumption'])}`",
        f"- Courses lacking public page/tab mapping: `{', '.join(report['audit_answers']['courses_lacking_public_page_tab_mapping'])}`",
        f"- Courses lacking Enrollware courseId: `{', '.join(report['audit_answers']['courses_lacking_enrollware_course_id']) or 'none'}`",
        f"- Manual review fields before authoritative: `{', '.join(report['audit_answers']['manual_review_fields_before_authoritative'])}`",
        "",
        "## Most Common Missing Fields",
        "",
    ]
    for field, count in report["audit_answers"]["most_common_missing_fields"].items():
        lines.append(f"- `{field}`: `{count}`")
    lines.append("")
    return "\n".join(lines)


def run() -> dict[str, Any]:
    catalog_payload = read_json(COURSE_CATALOG_PATH)
    map_payload = read_json(COURSE_MAP_PATH)
    rules_payload = read_json(CONSUMPTION_RULES_PATH)
    public_payload = read_json(PUBLIC_SELLABLE_PATH) if PUBLIC_SELLABLE_PATH.exists() else {}
    visibility_payload = read_json(COURSE_VISIBILITY_PATH) if COURSE_VISIBILITY_PATH.exists() else {}
    export_records, export_headers = load_course_export()
    map_courses = course_map_by_id(map_payload)
    export_by_id = index_export_records(export_records, map_payload)
    rules = consumption_rules_by_id(rules_payload)
    public_ids = public_sellable_course_ids(public_payload)
    mapping = slug_tab_mapping(map_courses)
    courses = []
    for catalog_course in catalog_payload.get("courses", []):
        if not isinstance(catalog_course, dict):
            continue
        course_id = clean_text(catalog_course.get("course_id"))
        courses.append(
            build_course_record(
                catalog_course,
                map_courses.get(course_id, {}),
                export_by_id.get(course_id),
                rules.get(course_id),
                public_ids,
                visibility_payload,
                mapping,
            )
        )
    courses.sort(key=lambda course: (course["course_family"], course["public_short_title"], course["enrollware_course_id"]))
    master = {
        "schema_version": "0.1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "authoritative": False,
        "source_files": [
            "data/config/course_catalog.json",
            "data/raw/course-export.xlsx",
            "data/config/course_map.json",
            "data/config/slug_hubs.json",
            "data/inventory/course_consumption_rules.json",
            "data/runtime/audit_previews/public_sellable_offers_preview.json",
        ],
        "courses": courses,
    }
    schema = build_schema()
    report = build_report(master, export_headers, catalog_payload, export_records, public_payload)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    COURSE_MASTER_SCHEMA_PATH.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    COURSE_MASTER_PATH.write_text(json.dumps(master, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> int:
    report = run()
    counts = report["counts"]
    print("Course Master build complete (READ ONLY / NOT AUTHORITATIVE).")
    print(f"Course records created: {counts['course_records_created']}")
    print(f"Complete: {counts['complete']}")
    print(f"Needs review: {counts['needs_review']}")
    print(f"Incomplete: {counts['incomplete']}")
    print(f"Every public sellable dynamic offer resolves: {report['audit_answers']['every_public_sellable_dynamic_offer_resolves_to_course_master']}")
    print("Output files:")
    print(f"- {COURSE_MASTER_SCHEMA_PATH}")
    print(f"- {COURSE_MASTER_PATH}")
    print(f"- {REPORT_MD_PATH}")
    print(f"- {REPORT_JSON_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
