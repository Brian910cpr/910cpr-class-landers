from __future__ import annotations

import json
import base64
import hashlib
import hmac
import os
import re
import sys
from datetime import datetime, timedelta
from html import escape, unescape
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlencode, urlparse

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_metadata import apply_build_metadata, current_build_metadata
from scripts.build_hub_offer_model_report import build_report as build_hub_offer_model_report
from scripts.build_seed_appointment_url_preview import (
    build_registration_url,
    matching_container,
    parse_date as parse_seed_date,
    appointment_display_time,
)
from scripts.build_status import BuildStatusReporter
from scripts.hybrid_inventory import (
    APPOINTMENT_ENDPOINT,
    build_appointment_page_url,
    extract_schedule_course_id,
    seed_dates_from_sessions,
    session_enrolled_count,
    sort_by_momentum,
    sort_by_start,
)
from supervisor.status_snapshot import write_status_snapshot
from zoneinfo import ZoneInfo


from scripts.local_data_paths import public_sellable_offers_preview_path
from scripts.public_class_eligibility import is_public_class_location, session_has_public_class_location

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "config" / "slug_hubs.json"
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
CANONICAL_CLASS_REPORT_PATH = ROOT / "docs" / "data" / "canonical_schedule_from_class_report.json"
CUSTOMER_FACING_OFFERS_PATH = ROOT / "docs" / "data" / "customer_facing_offers.json"
FREE_TIME_SCHEDULER_CONFIG_PATH = ROOT / "docs" / "data" / "free_time_scheduler_config.json"
SEED_APPOINTMENT_URL_PREVIEW_PATH = ROOT / "data" / "audit" / "seed_appointment_url_preview.json"
PUBLIC_SELLABLE_OFFERS_PREVIEW_PATH = public_sellable_offers_preview_path(ROOT)
PRESENTATION_POLICY_PREVIEW_PATH = ROOT / "data" / "audit" / "dynamic_offer_presentation_policy_report.json"
UNIVERSAL_OFFER_INVENTORY_PATH = ROOT / "data" / "audit" / "universal_offer_inventory.json"
COURSE_CATALOG_PATH = ROOT / "data" / "config" / "course_catalog.json"
APPOINTMENT_CONTAINERS_PATH = ROOT / "data" / "inventory" / "appointment_containers.json"
LOCATION_RESOURCE_MAP_PATH = ROOT / "data" / "config" / "location_resource_map.json"
COURSE_VISIBILITY_POLICY_PATH = ROOT / "data" / "config" / "course_visibility_policy.json"
COURSE_MAP_PATH = ROOT / "data" / "config" / "course_map.json"
REVIEWS_FILE = ROOT / "data" / "raw" / "reviews" / "reviews.json"
OUTPUT_DIR = ROOT / "docs"
COURSES_OUTPUT_DIR = OUTPUT_DIR / "courses"
USCG_SELECTOR_PAGE = COURSES_OUTPUT_DIR / "uscg-first-aid-cpr-aed.html"
USCG_OLD_PUBLIC_PAGE = OUTPUT_DIR / "uscg-elementary-first-aid-cpr.html"
STATE_DIR = ROOT / "data" / "state"
RUNTIME_DIR = ROOT / "data" / "runtime"
SESSIONS_CURRENT_PATH = ROOT / "data" / "sessions_current.json"
TZ = ZoneInfo("America/New_York")
DATE_LIMIT = 6
POPULAR_LIMIT = 4
HUB_INITIAL_VISIBLE_LIMIT = 30
HUB_REVEAL_INCREMENT = 15
CURATED_OFFER_LIMIT = 8
CURATED_OFFER_MIN = 5
EMPTY_FALLBACK_TITLE = "No selected times showing here, but you still have options."
EMPTY_FALLBACK_BODY = "View the full schedule for additional dates, request a class time, or ask about on-site training for your team."
DEBUG_SOURCE_TIMES_ENV = "LANDER_DEBUG_SOURCE_TIMES"
EMERGENCY_REGISTRATION_EMAIL = "info@910cpr.com"
EMERGENCY_ALERT_TITLE = "⚠️ Our Schedule Platform Vendor Is Experiencing Technical Difficulties"
EMERGENCY_ALERT_LINES = (
    "Classes listed on this page WILL still be held.",
    "If a registration button does not load, stalls, or fails, please email us at info@910cpr.com with your name, phone number, and the class date/time you want.",
    "We will help get you registered manually and make sure you can still get your certification.",
    "Sorry for the inconvenience. We will help you get your cert.",
)
GOOGLE_REVIEWS_URL = "https://www.google.com/maps/search/?api=1&query=910CPR%204018%20Shipyard%20Blvd%20Wilmington%20NC%2028403"
PRIVATE_HINTS = (
    "private",
    "onsite",
    "on-site",
    "client",
    "residence",
    "business",
    "organization",
    "appointment",
    "custom group",
    "custom session",
    "tbd",
)
BLS_REQUESTABLE_COURSE_KEYS = {"bls", "bls-renewal", "heartcode-bls-skills"}
BLS_TAB_REQUESTABLE_COURSE_KEYS = {
    "bls-provider": "bls",
    "bls-renewal": "bls-renewal",
    "bls-heartcode": "heartcode-bls-skills",
}
APPOINTMENT_COURSE_TAB_IDS = {
    "aha_bls_initial": {"bls-provider"},
    "aha_bls_renewal": {"bls-renewal"},
    "aha_bls_heartcode_skills": {"bls-heartcode"},
    "aha_acls_heartcode_skills": {"acls-heartcode"},
    "aha_pals_heartcode_skills": {"pals-heartcode"},
    "aha_heartsaver_fa_cpr_aed": {"hs-fa-cpr-aed-ip", "hs-fa-cpr-aed-bl"},
    "aha_heartsaver_first_aid_cpr_aed": {"hs-fa-cpr-aed-ip"},
    "aha_heartsaver_first_aid_cpr_aed_blended": {"hs-fa-cpr-aed-bl"},
    "aha_heartsaver_cpr_aed": {"hs-cpr-aed-ip", "hs-cpr-aed-bl"},
    "aha_heartsaver_cpr_aed_online": {"hs-cpr-aed-bl"},
    "aha_heartsaver_pediatric_first_aid_cpr_aed_online": {"hs-pediatric-bl"},
    "hsi_bls_adult_first_aid_blended": {"hsi-bls-fa"},
}
APPOINTMENT_HUB_BY_FAMILY = {
    "ACLS": "acls",
    "AHA ACLS": "acls",
    "PALS": "pals",
    "AHA PALS": "pals",
    "BLS": "bls",
    "AHA BLS": "bls",
    "Heartsaver": "heartsaver",
    "AHA Heartsaver": "heartsaver",
    "ARC": "arc",
    "American Red Cross": "arc",
    "HSI": "hsi",
    "USCG": "uscg-elementary-first-aid-cpr",
}


def authoritative_schedule_path() -> Path:
    if CANONICAL_CLASS_REPORT_PATH.exists():
        try:
            payload = json.loads(CANONICAL_CLASS_REPORT_PATH.read_text(encoding="utf-8"))
            if payload.get("build", {}).get("source_mode") == "class_report_authoritative":
                return CANONICAL_CLASS_REPORT_PATH
        except Exception:
            pass
    return SCHEDULE_PATH


def schedule_source_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(path)


def is_public_direct_bookable_session(session: dict[str, Any]) -> bool:
    return session.get("public_direct_booking") is not False and normalize_space(session.get("registration_status")).lower() not in {"closed", "full"}


def load_authoritative_schedule() -> tuple[list[dict[str, Any]], Path]:
    source_path = authoritative_schedule_path()
    schedule = json.loads(source_path.read_text(encoding="utf-8"))
    sessions = schedule.get("sessions", []) if isinstance(schedule, dict) else []
    return [
        session
        for session in sessions
        if isinstance(session, dict)
        and session_has_public_class_location(session)
        and is_public_direct_bookable_session(session)
    ], source_path


def load_customer_facing_offers() -> dict[str, list[dict[str, Any]]]:
    if not CUSTOMER_FACING_OFFERS_PATH.exists():
        return {}
    try:
        payload = json.loads(CUSTOMER_FACING_OFFERS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    courses = payload.get("courses", []) if isinstance(payload, dict) else []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for course in courses:
        if not isinstance(course, dict):
            continue
        course_key = normalize_space(course.get("course_key"))
        course_title = normalize_space(course.get("course_title"))
        course_display_name = normalize_space(course.get("course_display_name"))
        options = course.get("offered_options", [])
        if not course_key or not isinstance(options, list):
            continue
        for option in options:
            if not isinstance(option, dict):
                continue
            if normalize_space(option.get("session_status")) != "proposed":
                continue
            offer = dict(option)
            offer["course_key"] = normalize_space(offer.get("course_key")) or course_key
            offer["course_title"] = normalize_space(offer.get("course_title")) or course_title
            offer["course_display_name"] = normalize_space(offer.get("course_display_name")) or course_display_name or offer["course_title"]
            offer["enrollware_enroll_url"] = None
            grouped.setdefault(offer["course_key"], []).append(offer)

    for course_offers in grouped.values():
        course_offers.sort(key=lambda offer: parse_dt(offer.get("start_time")) or datetime.max.replace(tzinfo=TZ))
    return grouped


def load_hub_appointment_seed_offers() -> dict[str, list[dict[str, Any]]]:
    """Return validated auto-public appointment seed offers keyed by slug hub."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    try:
        report = build_hub_offer_model_report("auto")
    except Exception as exc:
        print(f"WARNING: Appointment seed hub offer report failed; continuing without appointment seed offers: {exc}")
        report = {}

    for hub in report.get("hubs", []):
        if hub.get("hub_source") != "slug_hubs":
            continue
        hub_key = normalize_space(hub.get("hub_key"))
        if not hub_key:
            continue
        offers: list[dict[str, Any]] = []
        for offer in hub.get("approved_seed_offers", []):
            if not is_renderable_appointment_seed_offer(offer):
                continue
            offers.append(dict(offer))
        if offers:
            grouped[hub_key] = sorted(offers, key=lambda item: parse_dt(item.get("start_datetime")) or datetime.max.replace(tzinfo=TZ))

    preview_offers = load_public_seed_appointment_url_previews()
    for hub_key, offers in preview_offers.items():
        grouped.setdefault(hub_key, []).extend(offers)

    for hub_key, offers in list(grouped.items()):
        grouped[hub_key] = sorted(offers, key=lambda item: parse_dt(item.get("start_datetime")) or datetime.max.replace(tzinfo=TZ))
    return grouped


def load_course_catalog_by_id() -> dict[str, dict[str, Any]]:
    if not COURSE_CATALOG_PATH.exists():
        return {}
    try:
        payload = json.loads(COURSE_CATALOG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    courses = payload.get("courses", []) if isinstance(payload, dict) else []
    catalog: dict[str, dict[str, Any]] = {}
    for course in courses:
        if isinstance(course, dict):
            course_id = normalize_space(course.get("course_id"))
            if course_id:
                catalog[course_id] = course
    return catalog


def load_active_appointment_containers() -> list[dict[str, Any]]:
    if not APPOINTMENT_CONTAINERS_PATH.exists():
        return []
    try:
        payload = json.loads(APPOINTMENT_CONTAINERS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    containers = payload.get("containers", []) if isinstance(payload, dict) else []
    return [container for container in containers if isinstance(container, dict) and container.get("status") == "active"]


def load_location_resource_map() -> dict[str, Any]:
    if not LOCATION_RESOURCE_MAP_PATH.exists():
        return {}
    try:
        payload = json.loads(LOCATION_RESOURCE_MAP_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_public_sellable_offer_index() -> dict[str, dict[str, Any]]:
    if PRESENTATION_POLICY_PREVIEW_PATH.exists():
        try:
            presentation_payload = json.loads(PRESENTATION_POLICY_PREVIEW_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            presentation_payload = {}
        presentation_offers = presentation_payload.get("render_offers", []) if isinstance(presentation_payload, dict) else []
        indexed: dict[str, dict[str, Any]] = {}
        for offer in presentation_offers:
            if isinstance(offer, dict):
                offer_id = normalize_space(offer.get("offer_id"))
                if offer_id:
                    indexed[offer_id] = offer
        if indexed:
            return indexed
    if not PUBLIC_SELLABLE_OFFERS_PREVIEW_PATH.exists():
        return {}
    try:
        payload = json.loads(PUBLIC_SELLABLE_OFFERS_PREVIEW_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    offers = payload.get("offers", []) if isinstance(payload, dict) else []
    indexed: dict[str, dict[str, Any]] = {}
    for offer in offers:
        if isinstance(offer, dict):
            offer_id = normalize_space(offer.get("offer_id"))
            if offer_id:
                indexed[offer_id] = offer
    return indexed


def load_public_seed_appointment_url_previews() -> dict[str, list[dict[str, Any]]]:
    """Return selected seed appointment URL previews that are safe for hub-only display."""
    if not SEED_APPOINTMENT_URL_PREVIEW_PATH.exists():
        return {}
    try:
        payload = json.loads(SEED_APPOINTMENT_URL_PREVIEW_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    public_sellable_by_id = load_public_sellable_offer_index()
    course_catalog_by_id = load_course_catalog_by_id()
    previews = payload.get("previews", []) if isinstance(payload, dict) else []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for preview in previews:
        if not isinstance(preview, dict):
            continue
        offer = build_hub_seed_offer_from_url_preview(preview, public_sellable_by_id, course_catalog_by_id)
        if not offer:
            continue
        hub_slug = normalize_space(offer.get("hub_slug"))
        if hub_slug:
            grouped.setdefault(hub_slug, []).append(offer)
    return grouped


def load_public_sellable_appointment_seed_offers() -> dict[str, list[dict[str, Any]]]:
    """Return every public-sellable dynamic appointment offer as a renderable hub row."""
    public_sellable_by_id = load_public_sellable_offer_index()
    if not public_sellable_by_id:
        return {}
    course_catalog_by_id = load_course_catalog_by_id()
    containers = load_active_appointment_containers()
    location_resource_map = load_location_resource_map()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for source_offer_id, public_offer in public_sellable_by_id.items():
        offer = build_hub_seed_offer_from_public_sellable(
            source_offer_id,
            public_offer,
            course_catalog_by_id,
            containers,
            location_resource_map,
        )
        if not offer:
            continue
        hub_slug = normalize_space(offer.get("hub_slug"))
        if hub_slug:
            grouped.setdefault(hub_slug, []).append(offer)
    for hub_slug, offers in list(grouped.items()):
        grouped[hub_slug] = sorted(offers, key=lambda item: parse_dt(item.get("start_datetime")) or datetime.max.replace(tzinfo=TZ))
    return grouped


def merge_appointment_seed_offers(
    *grouped_sources: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    merged: dict[str, list[dict[str, Any]]] = {}
    seen_by_hub: dict[str, set[str]] = {}
    for grouped in grouped_sources:
        for hub_slug, offers in grouped.items():
            hub_key = normalize_space(hub_slug)
            if not hub_key:
                continue
            seen = seen_by_hub.setdefault(hub_key, set())
            for offer in offers:
                href = normalize_space(offer.get("appointment_registration_url"))
                dedupe_key = href or "|".join(
                    normalize_space(offer.get(key))
                    for key in ("course_id", "start_datetime", "location_name", "instructor_display_name")
                )
                if not dedupe_key or dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                merged.setdefault(hub_key, []).append(offer)
    for hub_slug, offers in list(merged.items()):
        merged[hub_slug] = sorted(offers, key=lambda item: parse_dt(item.get("start_datetime")) or datetime.max.replace(tzinfo=TZ))
    return merged


def load_universal_offer_inventory() -> dict[str, list[dict[str, Any]]]:
    """Return hub-only generated offers keyed by slug hub.

    This file is an internal build artifact. It may contain appointment URL offers
    and request-only availability block offers, but it must never create real
    schedule rows or standalone class landers.
    """
    if not UNIVERSAL_OFFER_INVENTORY_PATH.exists():
        return {}
    try:
        payload = json.loads(UNIVERSAL_OFFER_INVENTORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    offers = payload.get("offers", []) if isinstance(payload, dict) else []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        public_offer = normalize_universal_offer_for_hub(offer)
        if not public_offer:
            continue
        hub_slug = normalize_space(public_offer.get("hub_slug"))
        if hub_slug:
            grouped.setdefault(hub_slug, []).append(public_offer)

    for hub_slug, hub_offers in list(grouped.items()):
        grouped[hub_slug] = sorted(hub_offers, key=lambda item: parse_dt(item.get("start_datetime")) or datetime.max.replace(tzinfo=TZ))
    return grouped


def normalize_universal_offer_for_hub(offer: dict[str, Any]) -> dict[str, Any] | None:
    offer_type = normalize_space(offer.get("offer_type"))
    hub_slug = normalize_space(offer.get("hub_slug"))
    course_id = normalize_space(offer.get("course_id"))
    title = normalize_space(offer.get("course_title"))
    start_datetime = normalize_space(offer.get("start_datetime"))
    if offer_type not in {"appointment_url", "request_only_block", "future_request_block"}:
        return None
    if not hub_slug or not course_id or not title or not start_datetime:
        return None

    tab_ids = offer.get("tab_ids") if isinstance(offer.get("tab_ids"), list) else []
    base = {
        "hub_slug": hub_slug,
        "tab_ids": [normalize_space(tab_id) for tab_id in tab_ids if normalize_space(tab_id)],
        "course_id": course_id,
        "course_key": normalize_space(offer.get("course_key")),
        "course_title": title,
        "course_family": normalize_space(offer.get("course_family")),
        "start_datetime": start_datetime,
        "end_datetime": normalize_space(offer.get("end_datetime")),
        "scheduler_consumption_start": normalize_space(offer.get("scheduler_consumption_start")),
        "scheduler_consumption_end": normalize_space(offer.get("scheduler_consumption_end")),
        "location_name": clean_location(offer.get("location_name")),
        "instructor_display_name": normalize_space(offer.get("instructor_display_name")),
        "display_note": normalize_space(offer.get("display_note")),
        "cta_label": normalize_space(offer.get("cta_label")),
        "preferred_month": normalize_space(offer.get("preferred_month")),
        "delivery_bucket": normalize_space(offer.get("delivery_bucket")),
        "optimized_offer_horizon_days": offer.get("optimized_offer_horizon_days"),
        "future_request_horizon_days": offer.get("future_request_horizon_days"),
        "public_schedule_row_created": False,
        "standalone_class_lander_created": False,
        "render_source": "universal_offer_inventory",
    }
    if offer_type == "appointment_url":
        url = normalize_space(offer.get("appointment_registration_url"))
        if not is_valid_appointment_seed_registration_url(url):
            return None
        return {
            **base,
            "public_display_item_type": "appointment_seed_offer",
            "display_item_type": "appointment_seed_offer",
            "seed_publication_mode": "appointment_seed_offer",
            "approval_status": "auto_approved_by_rules",
            "public_ready": True,
            "appointment_registration_url": url,
            "standalone_class_lander_allowed": False,
            "class_lander_created": False,
        }
    request_url_value = normalize_space(offer.get("request_url"))
    if not request_url_value.startswith("/request_group_session.html?"):
        return None
    if offer_type == "future_request_block":
        return {
            **base,
            "public_display_item_type": "future_request_block",
            "display_item_type": "future_request_block",
            "request_url": request_url_value,
            "public_ready": True,
            "standalone_class_lander_allowed": False,
            "class_lander_created": False,
        }
    return {
        **base,
        "public_display_item_type": "request_only_availability_offer",
        "display_item_type": "request_only_availability_offer",
        "request_url": request_url_value,
        "public_ready": True,
        "standalone_class_lander_allowed": False,
        "class_lander_created": False,
    }


def build_hub_seed_offer_from_url_preview(
    preview: dict[str, Any],
    public_sellable_by_id: dict[str, dict[str, Any]],
    course_catalog_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    if preview.get("blocking_reason"):
        return None
    course_id = normalize_space(preview.get("course_id"))
    source_offer_id = normalize_space(preview.get("source_offer_id"))
    url = normalize_space(preview.get("appointment_url_preview"))
    appointment_day_id = normalize_space(preview.get("appointmentDayId"))
    if not course_id or not source_offer_id or not url or not appointment_day_id:
        return None
    public_offer = public_sellable_by_id.get(source_offer_id, {})

    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)
    url_course_id = normalize_space((query.get("courseId") or [""])[0])
    start_time_query = normalize_space((query.get("startTime") or [""])[0])
    url_appointment_day_id = normalize_space((query.get("appointmentDayId") or [""])[0])
    if parsed_url.netloc != "coastalcprtraining.enrollware.com" or not parsed_url.path.startswith("/enroll"):
        return None
    if url_course_id != course_id or url_appointment_day_id != appointment_day_id or not start_time_query:
        return None

    catalog = course_catalog_by_id.get(course_id, {})
    if catalog and catalog.get("appointment_allowed") is False:
        return None
    course_key = normalize_space(catalog.get("course_key"))
    course_family = normalize_space(public_offer.get("course_family") or catalog.get("family") or preview.get("course_family"))
    hub_slug = APPOINTMENT_HUB_BY_FAMILY.get(course_family)
    if not hub_slug:
        return None

    start_datetime = normalize_space(preview.get("appointment_display_start") or public_offer.get("appointment_display_start") or public_offer.get("start_datetime"))
    end_datetime = normalize_space(preview.get("appointment_display_end") or public_offer.get("appointment_display_end") or public_offer.get("end_datetime"))
    if not start_datetime:
        return None

    return {
        "hub_slug": hub_slug,
        "tab_ids": sorted(appointment_seed_tab_ids(course_key, course_id)),
        "course_id": course_id,
        "course_key": course_key,
        "course_title": normalize_space(preview.get("course_title") or public_offer.get("course_title") or catalog.get("official_title")),
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "location_name": clean_location(preview.get("location") or public_offer.get("offer_location") or public_offer.get("location")),
        "instructor_display_name": normalize_space(preview.get("instructor_display_name") or public_offer.get("instructor_display_name")),
        "appointment_registration_url": url,
        "public_display_item_type": "appointment_seed_offer",
        "display_item_type": "appointment_seed_offer",
        "seed_publication_mode": "appointment_seed_offer",
        "approval_status": "auto_approved_by_rules",
        "public_ready": True,
        "standalone_class_lander_allowed": False,
        "class_lander_created": False,
        "public_schedule_row_created": False,
        "appointmentDayId": int(appointment_day_id),
        "seed_id": normalize_space(preview.get("seed_id")),
        "source_offer_id": source_offer_id,
        "render_source": "seed_appointment_url_preview",
    }


def appointment_seed_tab_ids(course_key: str, course_id: str | None = None) -> set[str]:
    """Map selected appointment seed rows to their existing slug hub tabs."""
    direct = APPOINTMENT_COURSE_TAB_IDS.get(normalize_space(course_key), set())
    if direct:
        return set(direct)
    return {
        "209806": {"bls-provider"},
        "359474": {"bls-renewal"},
        "210549": {"bls-heartcode"},
    }.get(normalize_space(course_id), set())


def build_hub_seed_offer_from_public_sellable(
    source_offer_id: str,
    public_offer: dict[str, Any],
    course_catalog_by_id: dict[str, dict[str, Any]],
    containers: list[dict[str, Any]],
    location_resource_map: dict[str, Any],
) -> dict[str, Any] | None:
    course_id = normalize_space(public_offer.get("course_id"))
    appointment_day_id = normalize_space(public_offer.get("appointmentDayId"))
    if not source_offer_id or not course_id:
        return None
    catalog = course_catalog_by_id.get(course_id, {})
    if catalog and catalog.get("appointment_allowed") is False:
        return None
    course_key = normalize_space(catalog.get("course_key"))
    course_family = normalize_space(public_offer.get("course_family") or catalog.get("family"))
    hub_slug = APPOINTMENT_HUB_BY_FAMILY.get(course_family)
    if not hub_slug:
        return None
    target_date = parse_seed_date(public_offer.get("date"))
    start_time = appointment_display_time(public_offer)
    if not target_date or not start_time:
        return None
    if not appointment_day_id:
        container, computed_day_id, _reason = matching_container(public_offer, containers, target_date, location_resource_map)
        if not container or computed_day_id is None:
            return None
        appointment_day_id = normalize_space(computed_day_id)
    url = build_registration_url(int(appointment_day_id), start_time, course_id)
    flexible_start_choices = []
    for choice in public_offer.get("flexible_start_choices", []) if isinstance(public_offer.get("flexible_start_choices"), list) else []:
        if not isinstance(choice, dict):
            continue
        choice_day_id = normalize_space(choice.get("appointmentDayId") or appointment_day_id)
        choice_start_time = appointment_display_time({
            "appointment_display_start": choice.get("appointment_display_start"),
            "start_time": choice.get("start_time"),
        })
        if not choice_day_id or not choice_start_time:
            continue
        flexible_start_choices.append({
            **choice,
            "appointment_registration_url": build_registration_url(int(choice_day_id), choice_start_time, course_id),
        })
    start_datetime = normalize_space(public_offer.get("appointment_display_start") or public_offer.get("start_datetime"))
    end_datetime = normalize_space(public_offer.get("appointment_display_end") or public_offer.get("end_datetime"))
    if not start_datetime:
        return None
    return {
        "hub_slug": hub_slug,
        "tab_ids": sorted(APPOINTMENT_COURSE_TAB_IDS.get(course_key, set())),
        "course_id": course_id,
        "course_key": course_key,
        "course_title": normalize_space(public_offer.get("course_title") or catalog.get("official_title")),
        "course_family": course_family,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "scheduler_consumption_start": normalize_space(public_offer.get("scheduler_consumption_start")),
        "scheduler_consumption_end": normalize_space(public_offer.get("scheduler_consumption_end")),
        "location_name": clean_location(public_offer.get("offer_location") or public_offer.get("location")),
        "instructor_display_name": normalize_space(public_offer.get("instructor_display_name")),
        "appointmentDayId": int(appointment_day_id),
        "appointment_registration_url": url,
        "source_offer_id": source_offer_id,
        "presentation_mode": normalize_space(public_offer.get("presentation_mode")),
        "public_render_decision": normalize_space(public_offer.get("public_render_decision")),
        "flexible_start_button_text": normalize_space(public_offer.get("flexible_start_button_text")),
        "flexible_start_choices": flexible_start_choices,
        "nearest_anchor_class": public_offer.get("nearest_anchor_class") if isinstance(public_offer.get("nearest_anchor_class"), dict) else None,
        "suppressed_adjacent_offer_ids": public_offer.get("suppressed_adjacent_offer_ids") if isinstance(public_offer.get("suppressed_adjacent_offer_ids"), list) else [],
        "public_display_item_type": "appointment_seed_offer",
        "display_item_type": "appointment_seed_offer",
        "seed_publication_mode": "appointment_seed_offer",
        "approval_status": "auto_approved_by_rules",
        "public_ready": True,
        "standalone_class_lander_allowed": False,
        "class_lander_created": False,
        "public_schedule_row_created": False,
        "render_source": normalize_space(public_offer.get("render_source")) or "public_sellable_offers_preview",
    }


def is_renderable_appointment_seed_offer(offer: dict[str, Any]) -> bool:
    return (
        offer.get("public_display_item_type") == "appointment_seed_offer"
        and offer.get("display_item_type") == "appointment_seed_offer"
        and offer.get("seed_publication_mode") == "appointment_seed_offer"
        and offer.get("approval_status") == "auto_approved_by_rules"
        and offer.get("public_ready") is True
        and is_valid_appointment_seed_registration_url(offer.get("appointment_registration_url"))
        and offer.get("standalone_class_lander_allowed") is False
        and offer.get("class_lander_created") is False
        and offer.get("public_schedule_row_created") is False
        and offer.get("render_source") == "auto_public_appointment_seed"
    )


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def clean_location(value: str | None) -> str:
    text = unescape(str(value or "").strip())
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if "::" in text:
        text = text.rsplit("::", 1)[-1].strip()
    if text.startswith("::"):
        text = text[2:].strip()
    return text or "Location TBA"


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def load_course_visibility_policy() -> dict[str, Any]:
    if not COURSE_VISIBILITY_POLICY_PATH.exists():
        return {}
    try:
        payload = json.loads(COURSE_VISIBILITY_POLICY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def course_visibility_record(course_id: str | None, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy if isinstance(policy, dict) else load_course_visibility_policy()
    courses = policy.get("courses", {}) if isinstance(policy, dict) else {}
    record = courses.get(normalize_space(course_id), {}) if isinstance(courses, dict) else {}
    return record if isinstance(record, dict) else {}


def course_visibility_state(course_id: str | None, policy: dict[str, Any] | None = None) -> str:
    record = course_visibility_record(course_id, policy)
    state = normalize_space(record.get("state"))
    if state:
        return state
    policy = policy if isinstance(policy, dict) else load_course_visibility_policy()
    return normalize_space(policy.get("default_state")) or "active_public"


def course_allows_public_inventory(course_id: str | None, policy: dict[str, Any] | None = None) -> bool:
    state = course_visibility_state(course_id, policy)
    return state not in {"menu_only_suppressed", "hidden"}


def course_is_hidden(course_id: str | None, policy: dict[str, Any] | None = None) -> bool:
    return course_visibility_state(course_id, policy) == "hidden"


def suppressed_course_copy(course_id: str | None, policy: dict[str, Any] | None = None) -> str:
    policy = policy if isinstance(policy, dict) else load_course_visibility_policy()
    record = course_visibility_record(course_id, policy)
    states = policy.get("states", {}) if isinstance(policy, dict) else {}
    menu_state = states.get("menu_only_suppressed", {}) if isinstance(states, dict) else {}
    return normalize_space(record.get("suppressed_public_copy") or menu_state.get("suppressed_public_copy")) or (
        "Public dates are not currently listed for this option. This course may be available by request or for group training."
    )


def load_course_code_lookup() -> dict[str, str]:
    if not COURSE_MAP_PATH.exists():
        return {}
    try:
        payload = json.loads(COURSE_MAP_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    courses = payload.get("courses_by_id") or payload.get("courses") or {} if isinstance(payload, dict) else {}
    lookup: dict[str, str] = {}
    if not isinstance(courses, dict):
        return lookup
    for course_id, course in courses.items():
        if not isinstance(course, dict):
            continue
        values = [
            course_id,
            course.get("course_id"),
            course.get("course_number"),
            course.get("course_code"),
            course.get("course_key"),
            course.get("clean_title"),
            course.get("official_title"),
        ]
        values.extend(course.get("aliases", []) if isinstance(course.get("aliases"), list) else [])
        for value in values:
            key = normalize_match_text(value)
            if key:
                lookup[key] = str(course_id)
    return lookup


def tab_course_ids(tab: dict[str, Any]) -> set[str]:
    lookup = load_course_code_lookup()
    ids: set[str] = set()
    for value in tab.get("course_codes", []) if isinstance(tab.get("course_codes"), list) else []:
        text = normalize_space(value)
        if not text:
            continue
        if re.fullmatch(r"\d+", text):
            ids.add(text)
        mapped = lookup.get(normalize_match_text(text))
        if mapped:
            ids.add(mapped)
    return ids


def tab_visibility_state(tab: dict[str, Any], policy: dict[str, Any] | None = None) -> str:
    ids = tab_course_ids(tab)
    if not ids:
        return "active_public"
    states = {course_visibility_state(course_id, policy) for course_id in ids}
    if "active_public" in states:
        return "active_public"
    if "menu_only_suppressed" in states:
        return "menu_only_suppressed"
    if "hidden" in states:
        return "hidden"
    return "active_public"


def public_internal_href_exists(href: str | None) -> bool:
    value = normalize_space(href)
    if not value or not value.startswith("/") or value.startswith("//"):
        return True
    path_part = value.split("#", 1)[0].split("?", 1)[0].strip("/")
    if not path_part:
        return True
    candidate = OUTPUT_DIR / path_part
    if value.endswith("/") or candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate.exists()


def safe_public_href(href: str | None, fallback: str) -> str:
    value = normalize_space(href)
    if not value:
        return fallback
    return value if public_internal_href_exists(value) else fallback


def load_free_time_scheduler_config() -> dict[str, Any]:
    if not FREE_TIME_SCHEDULER_CONFIG_PATH.exists():
        return {}
    try:
        payload = json.loads(FREE_TIME_SCHEDULER_CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def b64url_json(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def offer_link_signing_secret(config: dict[str, Any]) -> str:
    target = config.get("offer_click_target", {}) if isinstance(config, dict) else {}
    env_name = normalize_space(target.get("signing_secret_env")) or "OFFER_LINK_SIGNING_SECRET"
    return os.environ.get(env_name, "")


def build_offer_token(offer: dict[str, Any], *, hub_slug: str, config: dict[str, Any]) -> tuple[str, bool]:
    payload = {
        "v": 1,
        "offer_id": normalize_space(offer.get("offer_id") or offer.get("page_slug")),
        "course_key": normalize_space(offer.get("course_key")),
        "course_display_name": normalize_space(offer.get("course_display_name") or offer.get("course_title")),
        "requested_start": normalize_space(offer.get("start_time")),
        "requested_end": normalize_space(offer.get("end_time")),
        "location_name": normalize_space(offer.get("location_name") or offer.get("location_address")),
        "hub_slug": hub_slug,
        "source_page": hub_slug,
        "offer_source": "customer_facing_offers",
    }
    body = b64url_json(payload)
    target = config.get("offer_click_target", {}) if isinstance(config, dict) else {}
    if not target.get("sign_links", True):
        return body, False
    secret = offer_link_signing_secret(config)
    if not secret:
        raise RuntimeError(
            "offer_click_target.sign_links is true but the signing secret is missing. "
            "Set the configured signing secret env var or disable Worker link generation."
        )
    signature = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    return f"{body}.{base64.urlsafe_b64encode(signature).decode('ascii').rstrip('=')}", True


def requestable_offer_click_target(offer: dict[str, Any], *, hub_slug: str) -> dict[str, Any]:
    config = load_free_time_scheduler_config()
    target = config.get("offer_click_target", {}) if isinstance(config, dict) else {}
    enabled = bool(target.get("enabled")) and normalize_space(target.get("mode")) == "worker"
    base_url = normalize_space(target.get("base_url"))
    offer_slug = normalize_space(offer.get("offer_slug") or offer.get("page_slug"))
    fallback = {
        "href": "#request-this-time",
        "mode": "local_static",
        "token": "",
        "signed": False,
        "offer_slug": offer_slug,
        "enabled": False,
    }
    if not enabled or not base_url or not offer_slug:
        return fallback
    base = base_url.split("/check-time", 1)[0].rstrip("/")
    return {
        "href": f"{base}/o/{quote(offer_slug)}",
        "mode": "worker",
        "token": "",
        "signed": False,
        "offer_slug": offer_slug,
        "enabled": True,
    }


def has_public_raw_location(session: dict[str, Any]) -> bool:
    location_raw = normalize_space(session.get("location_display") or session.get("location_name"))
    return location_raw.startswith("::")


def strip_review_text(value: str | None) -> str:
    text = unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_space(text)


def load_google_review_stats() -> dict[str, Any]:
    fallback = {"label": "450+ 5-star reviews on Google", "themes": review_theme_summaries()}
    if not REVIEWS_FILE.exists():
        return fallback

    try:
        payload = json.loads(REVIEWS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback

    reviews = payload.get("reviews", payload) if isinstance(payload, dict) else payload
    if not isinstance(reviews, list):
        return fallback

    five_star = [
        review
        for review in reviews
        if review.get("rating") == 5 or str(review.get("starRating", "")).upper() == "FIVE"
    ]
    label = f"{len(five_star)} 5-star reviews on Google" if five_star else fallback["label"]
    return {"label": label, "themes": review_theme_summaries()}


def review_theme_summaries() -> list[str]:
    return [
        "Students often mention knowledgeable instructors who keep CPR, BLS, ACLS, and PALS requirements clear.",
        "Renewing providers regularly describe the classes as organized, direct, and respectful of their time.",
        "Reviewers commonly point to clear explanations, hands-on practice, and a class experience that feels manageable.",
    ]


def render_google_trust_block() -> str:
    stats = load_google_review_stats()
    themes = "".join(
        f"""
          <article class="review-snippet">
            <p>{escape(theme)}</p>
          </article>
""".rstrip()
        for theme in stats["themes"]
    )
    themes_html = f'<div class="review-snippets" aria-label="Common student review themes"><div class="review-theme-label">What students mention</div>{themes}</div>' if themes else ""
    return f"""
  <section class="top-trust below-inventory-trust" aria-label="910CPR trust and reviews">
    <div class="top-trust-copy">
      <div class="home-status-label">Serving North And South Carolina</div>
      <p>From the mountains to the coast, 910CPR helps healthcare teams, dental offices, schools, workplaces, and students meet real certification requirements with clear, organized classes.</p>
    </div>
    <a class="google-review-card" href="{GOOGLE_REVIEWS_URL}" target="_blank" rel="noopener noreferrer" aria-label="Open 910CPR Google reviews in a new tab">
      <span class="review-stars review-stars-large" aria-hidden="true">★★★★★</span>
      <strong>Trusted by {escape(stats['label'])}</strong>
      <em>As of May 5, 2026</em>
      <span>Read 910CPR reviews on Google</span>
    </a>
    {themes_html}
  </section>
""".rstrip()


def normalize_match_text(value: str | None) -> str:
    text = normalize_space(value).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def hub_asset_url(value: str | None, fallback: str = "") -> str:
    """Return a URL that works for generated hub pages served from docs/."""
    text = normalize_space(value) or fallback
    if text.startswith(("/images/", "/assets/", "/css/")):
        return text.lstrip("/")
    return text


def hub_script_url(path: str) -> str:
    return hub_asset_url(path)


def approved_locations_for_page(page: dict[str, Any]) -> set[str]:
    return {
        clean_location(location)
        for location in page.get("approved_public_locations", [])
        if clean_location(location)
    }


def location_matches_approved(location: str, approved_locations: set[str]) -> bool:
    location_key = normalize_match_text(location)
    if not approved_locations:
        return False
    for approved in approved_locations:
        approved_key = normalize_match_text(approved)
        if not approved_key:
            continue
        if location_key == approved_key or approved_key in location_key or location_key in approved_key:
            return True
        approved_tokens = set(approved_key.split())
        location_tokens = set(location_key.split())
        if approved_tokens and approved_tokens.issubset(location_tokens):
            return True
    return False


def public_inventory_decision(session: dict[str, Any], page: dict[str, Any]) -> tuple[bool, str]:
    location_raw = normalize_space(session.get("location_display") or session.get("location_name"))
    course_name = normalize_space(session.get("course_name"))
    course_subtitle = normalize_space(session.get("course_subtitle"))
    haystack = normalize_match_text(f"{course_name} {course_subtitle} {location_raw}")
    location_clean = clean_location(location_raw)
    course_token = normalize_space(session.get("course_id") or session.get("course_number"))
    if not course_allows_public_inventory(course_token):
        return False, f"excluded:course_visibility_{course_visibility_state(course_token)}"

    approved_locations = approved_locations_for_page(page)
    approved_location_match = location_matches_approved(location_clean, approved_locations)
    if approved_locations and not approved_location_match:
        return False, "excluded:unapproved_location"
    if not has_public_raw_location(session) and not approved_location_match:
        return False, "excluded:raw_location_not_public"

    if any(term in haystack for term in PRIVATE_HINTS):
        return False, "excluded:private_or_custom_signal"

    return True, "included:public_inventory"


def classify_heartsaver_session(session: dict[str, Any]) -> tuple[dict[str, str] | None, str]:
    course_name = normalize_space(session.get("course_name"))
    course_subtitle = normalize_space(session.get("course_subtitle"))
    course_code = normalize_space(session.get("course_code")).upper()
    haystack = normalize_match_text(f"{course_name} {course_subtitle}")
    upper_name = course_name.upper()

    if "HEARTSAVER" not in upper_name:
        return None, "excluded:not_heartsaver"
    if "USCG" in upper_name:
        return None, "excluded:uscg_routed_elsewhere"

    is_blended = bool(
        course_code in {"AHA_HS_FA_CPR_BL", "AHA_HS_PED_FA_CPR_BL"}
        or "blended" in haystack
        or "skills session" in haystack
        or "online" in haystack
    )
    format_badge = "Online + Skills" if is_blended else "In-Person"
    format_icon = "/images/tab_blended.png" if is_blended else "/images/tab_classroom.png"

    if "pediatric" in haystack:
        return (
            {
                "tab_id": "hs-pediatric-bl" if is_blended else "hs-pediatric-ip",
                "format_badge": "Online + Skills" if is_blended else "In-Person",
                "format_icon": format_icon,
                "family_badge": "Childcare",
            },
            "matched:heartsaver_pediatric",
        )

    if "first aid" in haystack and "cpr aed" in haystack:
        return (
            {
                "tab_id": "hs-fa-cpr-aed-bl" if is_blended else "hs-fa-cpr-aed-ip",
                "format_badge": format_badge,
                "format_icon": format_icon,
                "family_badge": "",
            },
            "matched:heartsaver_first_aid_cpr_aed",
        )

    if "cpr aed" in haystack and "first aid" not in haystack:
        return (
            {
                "tab_id": "hs-cpr-aed-bl" if is_blended else "hs-cpr-aed-ip",
                "format_badge": format_badge,
                "format_icon": format_icon,
                "family_badge": "CPR Focus",
            },
            "matched:heartsaver_cpr_aed_only",
        )

    return None, "excluded:no_heartsaver_tab_match"


def classify_acls_tab(session: dict[str, Any]) -> tuple[str | None, str]:
    course_name = normalize_space(session.get("course_name"))
    course_subtitle = normalize_space(session.get("course_subtitle"))
    course_code = normalize_space(session.get("course_code")).upper()
    haystack = normalize_match_text(f"{course_name} {course_subtitle}")

    if "ACLS" not in course_name.upper() and "ACLS" not in course_code:
        return None, "excluded:not_acls"

    if course_code == "AHA_ACLS_HEARTCODE":
        return "acls-heartcode", "course_code:AHA_ACLS_HEARTCODE"
    if course_code == "AHA_ACLS_PROVIDER_RENEWAL":
        return "acls-renewal", "course_code:AHA_ACLS_PROVIDER_RENEWAL"
    if course_code == "AHA_ACLS_PROVIDER_INITIAL":
        return "acls-provider", "course_code:AHA_ACLS_PROVIDER_INITIAL"

    if "heartcode" in haystack or "skills session" in haystack:
        return "acls-heartcode", "normalized_title:heartcode_or_skills_session"
    if "renewal" in haystack or "provider update" in haystack:
        return "acls-renewal", "normalized_title:renewal_or_update"
    if "acls provider initial" in haystack:
        return "acls-provider", "normalized_title:acls_provider_initial"
    if "acls provider in person initial" in haystack:
        return "acls-provider", "normalized_title:acls_provider_in_person_initial"
    if "aha acls provider" in haystack and "renewal" not in haystack and "update" not in haystack:
        return "acls-provider", "normalized_title:default_provider"

    return None, "excluded:no_acls_tab_match"


def matches_tab(session: dict[str, Any], tab: dict[str, Any], *, page_slug: str | None = None) -> bool:
    if page_slug == "acls":
        matched_tab, _ = classify_acls_tab(session)
        return matched_tab == tab.get("id")

    course_name = normalize_space(session.get("course_name"))
    course_subtitle = normalize_space(session.get("course_subtitle"))
    course_code = normalize_space(session.get("course_code"))
    metadata_parts = [
        course_name,
        course_subtitle,
        course_code,
        normalize_space(session.get("course_key")),
        normalize_space(session.get("official_course_name")),
        normalize_space(session.get("raw_course_name")),
        normalize_space(session.get("certifying_body")),
        normalize_space(session.get("mapped_certifying_body")),
        normalize_space(session.get("mapped_family")),
        normalize_space(session.get("mapped_subtype")),
        normalize_space(session.get("mapped_clean_title")),
    ]
    haystack_raw = " ".join(part for part in metadata_parts if part)
    haystack = haystack_raw.lower()
    normalized_haystack = normalize_match_text(haystack_raw)

    if page_slug == "bls" and tab.get("id") == "bls-heartcode" and "bls" not in normalized_haystack:
        return False

    certifying_bodies = {normalize_space(body).upper() for body in tab.get("certifying_bodies", []) if normalize_space(body)}
    if certifying_bodies:
        session_bodies = {
            normalize_space(session.get("certifying_body")).upper(),
            normalize_space(session.get("mapped_certifying_body")).upper(),
        }
        if not certifying_bodies.intersection(session_bodies):
            return False

    codes = {normalize_space(code) for code in tab.get("course_codes", []) if normalize_space(code)}
    needles = [str(item).lower() for item in tab.get("name_contains", []) if str(item).strip()]
    normalized_needles = [normalize_match_text(item) for item in tab.get("name_contains", []) if str(item).strip()]
    if codes:
        matched = course_code in codes or any(needle in haystack for needle in needles)
        if not matched and normalized_needles:
            matched = any(needle and needle in normalized_haystack for needle in normalized_needles)
    else:
        matched = not needles or any(needle in haystack for needle in needles)
        if not matched and normalized_needles:
            matched = any(needle and needle in normalized_haystack for needle in normalized_needles)

    if not matched:
        return False

    excludes = [str(item).lower() for item in tab.get("exclude_name_contains", []) if str(item).strip()]
    normalized_excludes = [normalize_match_text(item) for item in tab.get("exclude_name_contains", []) if str(item).strip()]
    def has_exclusion(needle: str, normalized_needle: str) -> bool:
        if normalized_needle == "instructor":
            return bool(
                re.search(
                    r"\binstructor\s+(course|renewal|update|candidate|training)\b|\bbecome an? .*?\binstructor\b",
                    normalized_haystack,
                )
            )
        return (needle and needle in haystack) or (normalized_needle and normalized_needle in normalized_haystack)

    return not any(has_exclusion(raw, normalized) for raw, normalized in zip(excludes, normalized_excludes))


def canonical_session_category(session: dict[str, Any]) -> dict[str, str]:
    metadata_parts = [
        normalize_space(session.get("course_name")),
        normalize_space(session.get("official_course_name")),
        normalize_space(session.get("raw_course_name")),
        normalize_space(session.get("course_key")),
        normalize_space(session.get("course_code")),
        normalize_space(session.get("mapped_clean_title")),
        normalize_space(session.get("mapped_family")),
        normalize_space(session.get("mapped_subtype")),
        normalize_space(session.get("mapped_certifying_body")),
    ]
    haystack = normalize_match_text(" ".join(part for part in metadata_parts if part))
    body = certifying_body_key(session)
    family = normalize_space(session.get("mapped_family"))
    subtype = normalize_space(session.get("mapped_subtype"))
    delivery = normalize_space(session.get("mapped_delivery_mode") or session.get("delivery_mode"))

    if not family:
        if "acls" in haystack:
            family = "ACLS"
        elif "pals" in haystack:
            family = "PALS"
        elif "heartsaver" in haystack:
            family = "Heartsaver"
        elif "bls" in haystack or "basic life support" in haystack:
            family = "BLS"
        elif body == "hsi":
            family = "HSI"
        elif body == "arc":
            family = "ARC"

    if not subtype:
        if "heartcode" in haystack or "online skills" in haystack or "blended" in haystack:
            subtype = "HeartCode" if family in {"BLS", "ACLS", "PALS"} else "Blended"
        elif "renewal" in haystack or "update" in haystack:
            subtype = "Renewal"
        elif "provider" in haystack:
            subtype = "Provider"

    return {
        "family": family,
        "subtype": subtype,
        "certifying_body": body,
        "delivery_mode": delivery,
        "haystack": haystack,
    }


def session_is_page_candidate(session: dict[str, Any], page_slug: str) -> bool:
    category = canonical_session_category(session)
    family = category["family"].lower()
    body = category["certifying_body"]
    haystack = category["haystack"]
    if page_slug == "bls":
        return family == "bls" or ("bls" in haystack and "instructor" not in haystack)
    if page_slug == "acls":
        return family == "acls" or "acls" in haystack
    if page_slug == "pals":
        return family == "pals" or "pals" in haystack
    if page_slug == "heartsaver":
        return family == "heartsaver" or "heartsaver" in haystack
    if page_slug == "hsi":
        return family == "hsi" or body == "hsi" or "hsi" in haystack
    if page_slug == "arc":
        return family == "arc" or body == "arc" or "red cross" in haystack or "arc" in haystack
    return False


def build_hub_debug_records(page: dict[str, Any], sessions: list[dict[str, Any]], *, now: datetime) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    page_slug = str(page.get("slug") or "")
    for session in sort_sessions(sessions):
        if not is_future_session(session, now=now):
            continue
        if not session_is_page_candidate(session, page_slug):
            continue

        matched_tabs: list[str] = []
        exclusion_reasons: list[str] = []
        for tab in page.get("tabs", []):
            enriched = enrich_session_for_page(session, page, tab, now=now)
            if enriched:
                matched_tabs.append(str(tab.get("id") or ""))
            elif page_slug == "heartsaver":
                is_public, public_reason = public_inventory_decision(session, page)
                classification, class_reason = classify_heartsaver_session(session)
                exclusion_reasons.append(public_reason if not is_public else class_reason)
            elif page_slug == "acls":
                _, reason = classify_acls_tab(session)
                exclusion_reasons.append(reason)
            else:
                exclusion_reasons.append("excluded:no_tab_match")

        category = canonical_session_category(session)
        included = bool(matched_tabs)
        records.append(
            {
                "page_slug": page_slug,
                "session_id": session.get("session_id"),
                "course_id": session.get("course_id") or session.get("course_number"),
                "course_name": session.get("course_name"),
                "official_course_name": session.get("official_course_name"),
                "course_key": session.get("course_key"),
                "course_code": session.get("course_code"),
                "start_at": session.get("start_at"),
                "included": included,
                "matched_tabs": matched_tabs,
                "matched_classification": {
                    "family": category["family"],
                    "subtype": category["subtype"],
                    "certifying_body": category["certifying_body"],
                    "delivery_mode": category["delivery_mode"],
                },
                "reason_excluded": None if included else sorted(set(exclusion_reasons)),
            }
        )
    return records


def rendered_real_session_count(page: dict[str, Any], sessions: list[dict[str, Any]], *, now: datetime) -> int:
    rendered_ids: set[str] = set()
    rendered_without_id = 0
    for tab in page.get("tabs", []):
        for session in sessions:
            enriched = enrich_session_for_page(session, page, tab, now=now)
            if not enriched:
                continue
            session_id = normalize_space(enriched.get("session_id"))
            if session_id:
                rendered_ids.add(session_id)
            else:
                rendered_without_id += 1
    return len(rendered_ids) + rendered_without_id


def hub_group_schedule_summary(
    page: dict[str, Any],
    sessions: list[dict[str, Any]],
    requestable_offers: list[dict[str, Any]],
    *,
    now: datetime,
) -> dict[str, dict[str, Any]]:
    if str(page.get("slug") or "") != "bls":
        return {}

    offers_by_course_key: dict[str, list[dict[str, Any]]] = {}
    for offer in requestable_offers:
        offers_by_course_key.setdefault(normalize_space(offer.get("course_key")), []).append(offer)

    summary: dict[str, dict[str, Any]] = {}
    for tab in page.get("tabs", []):
        tab_id = str(tab.get("id") or "")
        real_ids: set[str] = set()
        real_without_id = 0
        for session in sessions:
            enriched = enrich_session_for_page(session, page, tab, now=now)
            if not enriched:
                continue
            session_id = normalize_space(enriched.get("session_id"))
            if session_id:
                real_ids.add(session_id)
            else:
                real_without_id += 1

        course_key = BLS_TAB_REQUESTABLE_COURSE_KEYS.get(tab_id, "")
        requestable_count = len(offers_by_course_key.get(course_key, []))
        real_count = len(real_ids) + real_without_id
        combined_rows = sorted(
            [
                *[enrich_session_for_page(session, page, tab, now=now) for session in sessions],
                *requestable_offers_for_tab(page, tab, requestable_offers),
            ],
            key=lambda row: schedule_row_start(row or {}),
        )
        combined_rows = [row for row in combined_rows if row]
        _, default_strategy = prioritize_bls_default_rows(combined_rows, load_free_time_scheduler_config())
        summary[tab_id] = {
            "label": tab.get("label"),
            "requestable_course_key": course_key,
            "real_canonical_sessions_shown_count": real_count,
            "requestable_offers_shown_count": requestable_count,
            "combined_schedule_rows_count": real_count + requestable_count,
            **default_strategy,
        }
    return summary


def write_hub_runtime_debug(
    page: dict[str, Any],
    sessions: list[dict[str, Any]],
    *,
    now: datetime,
    source_path: Path,
    requestable_offers: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    records = build_hub_debug_records(page, sessions, now=now)
    page_requestable_offers = requestable_offers or []
    requestable_summary = summarize_requestable_offers(page_requestable_offers)
    group_summary = hub_group_schedule_summary(page, sessions, page_requestable_offers, now=now)
    output_path = RUNTIME_DIR / f"{page.get('slug')}_hub_debug.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "generated_at": now.isoformat(),
                "source_schedule_path": schedule_source_label(source_path),
                "page_slug": page.get("slug"),
                "real_canonical_sessions_shown_count": rendered_real_session_count(page, sessions, now=now),
                **requestable_summary,
                "schedule_rows_by_course_group": group_summary,
                "records": records,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return records


def build_acls_debug_records(page: dict[str, Any], sessions: list[dict[str, Any]], *, now: datetime) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for session in sort_sessions(sessions):
        if not is_future_session(session, now=now):
            continue
        course_name = normalize_space(session.get("course_name"))
        course_code = normalize_space(session.get("course_code")).upper()
        if "ACLS" not in course_name.upper() and "ACLS" not in course_code:
            continue
        normalized_tab, reason = classify_acls_tab(session)
        records.append(
            {
                "session_id": session.get("session_id"),
                "raw_title": session.get("course_name"),
                "start_datetime": session.get("start_at"),
                "normalized_hub": page.get("slug"),
                "normalized_tab": normalized_tab,
                "included": normalized_tab is not None,
                "reason": reason if normalized_tab is None else None,
                "match_reason": reason if normalized_tab is not None else None,
            }
        )
    return records


def session_current_to_future_shape(session: dict[str, Any]) -> dict[str, Any]:
    course = session.get("course", {}) or {}
    timing = session.get("timing", {}) or {}
    location = session.get("location", {}) or {}
    commerce = session.get("commerce", {}) or {}
    return {
        "session_id": session.get("session_id"),
        "course_number": course.get("course_number"),
        "course_name": course.get("course_name_primary_clean"),
        "course_name_raw": course.get("course_name_primary_raw") or course.get("course_name_primary_clean"),
        "course_subtitle": course.get("course_subtitle_text"),
        "course_code": course.get("course_code_hint"),
        "start_at": timing.get("start_at"),
        "location_display": location.get("location_display") or location.get("location_name"),
        "registration_url": commerce.get("registration_url"),
    }


def write_acls_runtime_debug(page: dict[str, Any], future_sessions: list[dict[str, Any]], *, now: datetime, source_path: Path) -> None:
    current_payload = json.loads(SESSIONS_CURRENT_PATH.read_text(encoding="utf-8")) if SESSIONS_CURRENT_PATH.exists() else {}
    current_sessions = current_payload.get("sessions", []) if isinstance(current_payload.get("sessions"), list) else []
    future_by_id = {
        str(session.get("session_id")): session
        for session in future_sessions
        if session.get("session_id") is not None
    }

    records: list[dict[str, Any]] = []
    for raw_session in current_sessions:
        current_shape = session_current_to_future_shape(raw_session)
        start_dt = parse_dt(current_shape.get("start_at"))
        if start_dt is None or start_dt <= now:
            continue

        raw_course_name = normalize_space(current_shape.get("course_name_raw") or current_shape.get("course_name"))
        if "ACLS" not in raw_course_name.upper():
            continue

        session_id = str(current_shape.get("session_id") or "")
        included_in_schedule_future = session_id in future_by_id
        normalized_tab = None
        match_reason = None
        exclusion_reason = None
        normalized_hub = "acls"
        included_in_acls_hub = False

        if included_in_schedule_future:
            normalized_tab, match_reason = classify_acls_tab(future_by_id[session_id])
            included_in_acls_hub = normalized_tab is not None
            if not included_in_acls_hub:
                exclusion_reason = match_reason
        else:
            normalized_tab, match_reason = classify_acls_tab(current_shape)
            exclusion_reason = "excluded_from_schedule_future"

        records.append(
            {
                "session_id": current_shape.get("session_id"),
                "course_number": current_shape.get("course_number"),
                "raw_course_name": raw_course_name,
                "start_datetime": current_shape.get("start_at"),
                "location": clean_location(current_shape.get("location_display")),
                "register_url": current_shape.get("registration_url"),
                "included_in_schedule_future": included_in_schedule_future,
                "normalized_hub": normalized_hub,
                "normalized_tab": normalized_tab,
                "included_in_acls_hub": included_in_acls_hub,
                "exclusion_reason": exclusion_reason,
                "match_reason": match_reason,
            }
        )

    payload = {
        "generated_at": now.isoformat(),
        "source_sessions_current_path": str(SESSIONS_CURRENT_PATH),
        "source_schedule_path": schedule_source_label(source_path),
        "page_slug": page.get("slug"),
        "records": records,
    }
    output_path = RUNTIME_DIR / "acls_hub_debug.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_heartsaver_runtime_debug(page: dict[str, Any], future_sessions: list[dict[str, Any]], *, now: datetime, source_path: Path) -> None:
    records: list[dict[str, Any]] = []
    for session in sort_sessions(future_sessions):
        if not is_future_session(session, now=now):
            continue
        raw_course_name = normalize_space(session.get("course_name"))
        if "HEARTSAVER" not in raw_course_name.upper():
            continue

        is_public, public_reason = public_inventory_decision(session, page)
        classification, class_reason = classify_heartsaver_session(session)
        included = bool(is_public and classification is not None)
        records.append(
            {
                "session_id": session.get("session_id"),
                "raw_course_name": session.get("course_name"),
                "start_datetime": session.get("start_at"),
                "location": clean_location(session.get("location_display") or session.get("location_name")),
                "public_private_decision": "public" if is_public else "private_or_hidden",
                "normalized_tab": classification.get("tab_id") if classification else None,
                "normalized_format": classification.get("format_badge") if classification else None,
                "icon_selected": classification.get("format_icon") if classification else None,
                "included": included,
                "exclusion_reason": None if included else (public_reason if not is_public else class_reason),
            }
        )

    payload = {
        "generated_at": now.isoformat(),
        "source_schedule_path": schedule_source_label(source_path),
        "page_slug": page.get("slug"),
        "records": records,
    }
    output_path = RUNTIME_DIR / "heartsaver_hub_debug.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sort_sessions(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(session: dict[str, Any]) -> tuple[int, str]:
        dt = parse_dt(session.get("start_at"))
        if dt is None:
            return (1, "9999-12-31T23:59:59")
        return (0, dt.isoformat())

    return sorted(sessions, key=sort_key)


def is_future_session(session: dict[str, Any], *, now: datetime) -> bool:
    start_dt = parse_dt(session.get("start_at"))
    return bool(start_dt and start_dt > now)


def enrich_session_for_page(session: dict[str, Any], page: dict[str, Any], tab: dict[str, Any], *, now: datetime) -> dict[str, Any] | None:
    if not is_future_session(session, now=now):
        return None

    page_slug = str(page.get("slug") or "")
    enriched = dict(session)

    if page_slug == "acls":
        matched_tab, _ = classify_acls_tab(session)
        if matched_tab != tab.get("id"):
            return None
        return enriched

    if page_slug == "heartsaver":
        is_public, _ = public_inventory_decision(session, page)
        if not is_public:
            return None
        classification, _ = classify_heartsaver_session(session)
        if not classification or classification.get("tab_id") != tab.get("id"):
            return None
        enriched["_format_badge"] = classification.get("format_badge", "")
        enriched["_format_icon"] = classification.get("format_icon", "")
        enriched["_family_badge"] = classification.get("family_badge", "")
        return enriched

    if matches_tab(session, tab, page_slug=page_slug):
        return enriched
    return None


def heartsaver_tab_display(tab: dict[str, Any], sessions: list[dict[str, Any]]) -> dict[str, str]:
    return {
        "tab_icon": tab.get("tab_icon") or "images/tab_classroom.png",
        "tab_badge": tab.get("tab_badge") or "",
    }


def format_month(dt: datetime | None) -> str:
    return dt.strftime("%b").upper() if dt else "TBD"


def format_day(dt: datetime | None) -> str:
    return dt.strftime("%d").lstrip("0") if dt else "--"


def format_weekday(dt: datetime | None) -> str:
    return dt.strftime("%a") if dt else ""


def format_date_line(dt: datetime | None) -> str:
    return dt.strftime("%A, %B %d").replace(" 0", " ") if dt else "Date TBA"


def format_time_line(dt: datetime | None) -> str:
    return dt.strftime("%I:%M %p").lstrip("0") if dt else "Time TBA"


def debug_source_times_enabled() -> bool:
    return normalize_space(os.environ.get(DEBUG_SOURCE_TIMES_ENV)).lower() in {"1", "true", "yes", "on"}


def appointment_day_id_from_url(url: str | None) -> str:
    parsed = urlparse(normalize_space(url))
    if not parsed.query:
        return ""
    return normalize_space((parse_qs(parsed.query).get("appointmentDayId") or [""])[0])


def is_valid_appointment_seed_registration_url(url: str | None) -> bool:
    parsed = urlparse(normalize_space(url))
    if parsed.netloc != "coastalcprtraining.enrollware.com" or not parsed.path.startswith("/enroll"):
        return False
    query = parse_qs(parsed.query)
    return all(normalize_space((query.get(key) or [""])[0]) for key in ("appointmentDayId", "startTime", "courseId"))


def debug_source_profile(row: dict[str, Any], *, kind_hint: str = "") -> dict[str, Any]:
    row_type = normalize_space(kind_hint)
    render_source = normalize_space(row.get("render_source"))
    display_type = normalize_space(row.get("display_item_type") or row.get("public_display_item_type"))
    source = normalize_space(row.get("source"))

    if row_type == "appointment_seed" or display_type == "appointment_seed_offer" or row.get("_appointment_seed_offer"):
        source_type = "seed"
        badge = "SEED"
        offset_minutes = 1
        source_file = "data/audit/seed_appointment_url_preview.json"
    elif row_type in {"requestable", "universal_request"} or row.get("_requestable_offer") or row.get("_universal_request_offer"):
        source_type = "dynamic"
        badge = "DYNAMIC"
        offset_minutes = 1
        source_file = "data/audit/universal_offer_inventory.json" if row.get("_universal_request_offer") else "docs/data/customer_facing_offers.json"
    elif source == "enrollware_ical" or (row_type == "real_session" and (row.get("session_id") or row.get("registration_url"))):
        source_type = "ical"
        badge = "ICAL"
        offset_minutes = 0
        source_file = "docs/data/schedule_future.json"
    else:
        source_type = "unknown"
        badge = "UNKNOWN"
        offset_minutes = 2
        source_file = render_source or normalize_space(row.get("source_file")) or "unknown"

    class_id = normalize_space(row.get("session_id") or row.get("class_id") or row.get("courseSchedId"))
    appointment_day_id = normalize_space(row.get("appointmentDayId") or row.get("appointment_day_id"))
    if not appointment_day_id:
        appointment_day_id = appointment_day_id_from_url(row.get("appointment_registration_url") or row.get("registration_url"))

    return {
        "source_type": source_type,
        "badge": badge,
        "offset_minutes": offset_minutes,
        "source_file": source_file,
        "course_id": normalize_space(row.get("course_id") or row.get("course_number")),
        "class_id": class_id,
        "appointment_day_id": appointment_day_id,
    }


def debug_display_dt(dt: datetime | None, row: dict[str, Any], *, kind_hint: str = "") -> datetime | None:
    if not debug_source_times_enabled() or dt is None:
        return dt
    profile = debug_source_profile(row, kind_hint=kind_hint)
    return dt + timedelta(minutes=int(profile["offset_minutes"]))


def debug_source_badge_html(row: dict[str, Any], *, kind_hint: str = "") -> str:
    if not debug_source_times_enabled():
        return ""
    profile = debug_source_profile(row, kind_hint=kind_hint)
    return f'<span class="slug-pill-chip slug-debug-source-badge">DEBUG {escape(profile["badge"])}</span>'


def debug_source_data_attrs(row: dict[str, Any], *, kind_hint: str = "") -> str:
    if not debug_source_times_enabled():
        return ""
    profile = debug_source_profile(row, kind_hint=kind_hint)
    attrs = {
        "data-source-type": profile["source_type"],
        "data-source-file": profile["source_file"],
        "data-course-id": profile["course_id"],
        "data-class-id": profile["class_id"],
        "data-appointment-day-id": profile["appointment_day_id"],
    }
    return "".join(
        f' {name}="{escape(str(value), quote=True)}"'
        for name, value in attrs.items()
        if value not in (None, "")
    )


def certifying_body_key(session: dict[str, Any]) -> str:
    body = normalize_space(session.get("mapped_certifying_body") or session.get("certifying_body")).upper()
    haystack = normalize_space(
        " ".join(
            str(session.get(key) or "")
            for key in ("course_name", "course_name_raw", "course_subtitle", "course_code")
        )
    ).upper()
    text = f"{body} {haystack}"
    if "AMERICAN RED CROSS" in text or re.search(r"\bARC\b", text):
        return "arc"
    if "HEALTH & SAFETY INSTITUTE" in text or "HEALTH AND SAFETY INSTITUTE" in text or re.search(r"\bHSI\b", text):
        return "hsi"
    if "AMERICAN HEART ASSOCIATION" in text or re.search(r"\bAHA\b", text):
        return "aha"
    return ""


def certifying_logo_src(session: dict[str, Any]) -> str:
    return hub_asset_url({
        "aha": "/images/0aha.png",
        "arc": "/images/0arc.png",
        "hsi": "/images/0hsi.png",
    }.get(certifying_body_key(session), ""))


def render_emergency_mailto(session: dict[str, Any], *, page_slug: str) -> str:
    start_dt = parse_dt(session.get("start_at"))
    location = clean_location(session.get("location_display") or session.get("location_name"))
    title = normalize_space(session.get("course_name")) or "910CPR Class"
    date_text = format_date_line(start_dt)
    time_text = format_time_line(start_dt)
    date_time = normalize_space(f"{date_text} {time_text}")
    session_id = str(session.get("session_id") or "")
    page_url = f"https://www.910cpr.com/{page_slug}"
    subject = f"910CPR Registration Help - {title} - {date_time}"
    body = "\n".join(
        [
            "Hi 910CPR,",
            "",
            "I would like help registering for this class:",
            "",
            f"Class: {title}",
            f"Date/Time: {date_time}",
            f"Location: {location}",
            f"Session ID: {session_id}",
            f"Page: {page_url}",
            "",
            "My name:",
            "My phone number:",
            "",
            "Thank you.",
        ]
    )
    return f"mailto:{EMERGENCY_REGISTRATION_EMAIL}?subject={quote(subject)}&body={quote(body)}"


def render_session_card(session: dict[str, Any], *, group_mode: bool, page_slug: str) -> str:
    start_dt = parse_dt(session.get("start_at"))
    end_dt = parse_dt(session.get("end_at"))
    display_start_dt = debug_display_dt(start_dt, session, kind_hint="real_session")
    display_end_dt = debug_display_dt(end_dt, session, kind_hint="real_session")
    location = clean_location(session.get("location_display") or session.get("location_name"))
    title = normalize_space(session.get("course_name"))
    register_url = escape(session.get("registration_url") or "#", quote=True)
    session_start = escape(start_dt.isoformat() if start_dt else "", quote=True)
    session_end = escape(end_dt.isoformat() if end_dt else "", quote=True)
    session_id = escape(str(session.get("session_id") or ""), quote=True)
    format_badge = normalize_space(session.get("_format_badge"))
    family_badge = normalize_space(session.get("_family_badge"))
    enrolled_count = session_enrolled_count(session)
    cert_body = certifying_body_key(session)
    cert_logo = certifying_logo_src(session)
    cert_attrs = ""
    if cert_body and cert_logo:
        cert_attrs = (
            f' data-certifying-body="{escape(cert_body, quote=True)}"'
            f' data-certifying-logo="{escape(cert_logo, quote=True)}"'
        )

    action_label = "See Public Class" if group_mode else "Book This Class"
    action_url = escape(f"/classes/{str(session.get('session_id') or '').strip()}.html#ForwardToEnrollware", quote=True) if str(session.get("session_id") or "").strip() else register_url
    action_hint = ""
    badge_html = ""
    if format_badge:
        badge_html += f'<span class="slug-pill-chip slug-pill-chip-format">{escape(format_badge)}</span>'
    if family_badge:
        badge_html += f'<span class="slug-pill-chip slug-pill-chip-family">{escape(family_badge)}</span>'
    badge_html += debug_source_badge_html(session, kind_hint="real_session")
    if enrolled_count >= 1 and not group_mode:
        badge_html += '<span class="slug-pill-chip slug-pill-chip-momentum">Already Enrolled</span>'
        badge_html += f'<span class="slug-pill-chip slug-pill-chip-momentum">{escape(momentum_label(enrolled_count))}</span>'
        badge_html += (
            '<span class="slug-pill-chip slug-pill-chip-momentum">'
            + ("Filling" if enrolled_count >= 2 else "Popular Time")
            + "</span>"
        )
    badge_line = f"      {badge_html}" if badge_html else ""
    action_hint_html = f'    <div class="slug-pill-hint">{escape(action_hint)}</div>' if action_hint else ""

    return f"""
<article class="slug-pill js-session-item" data-session-id="{session_id}" data-start="{session_start}" data-end="{session_end}" data-session-start="{session_start}" data-row-href="{action_url}"{cert_attrs}{debug_source_data_attrs(session, kind_hint="real_session")}>
  <div class="slug-pill-date">
    <div class="slug-pill-month">{format_month(display_start_dt)}</div>
    <div class="slug-pill-day">{format_day(display_start_dt)}</div>
    <div class="slug-pill-weekday">{format_weekday(display_start_dt)}</div>
  </div>
  <div class="slug-pill-main">
    <div class="slug-pill-title">{escape(format_date_line(display_start_dt))}</div>
    <div class="slug-pill-meta-row">
      <span class="slug-pill-chip">{escape(format_time_line(display_start_dt))}</span>
      <span class="slug-pill-chip slug-pill-chip-location">{escape(location)}</span>
{badge_line}
    </div>
    <div class="slug-pill-subtitle">{escape(title)}</div>
  </div>
  <div class="slug-pill-actions">
{action_hint_html}
    <a class="button small primary" href="{action_url}" data-original-href="{register_url}">{action_label}</a>
  </div>
</article>
""".strip()


def session_key(session: dict[str, Any]) -> str:
    return str(session.get("session_id") or session.get("registration_url") or "")


def session_action(session: dict[str, Any], *, page_slug: str) -> tuple[str, str, str]:
    register_url = escape(session.get("registration_url") or "#", quote=True)
    action_label = "Book This Class"
    session_id = str(session.get("session_id") or "").strip()
    action_url = escape(f"/classes/{session_id}.html#ForwardToEnrollware", quote=True) if session_id else register_url
    return action_label, action_url, register_url


def seats_copy(enrolled_count: int) -> str:
    if enrolled_count >= 3:
        return "Popular class"
    if enrolled_count >= 1:
        return "Students already enrolled"
    return "Open registration"


def offer_benefit_copy(tab: dict[str, Any], session: dict[str, Any]) -> str:
    format_badge = normalize_space(session.get("_format_badge") or tab.get("tab_badge"))
    if "heartcode" in format_badge.lower() or "skills" in format_badge.lower():
        return "Finish the online portion, then complete your in-person skills check."
    if "renewal" in normalize_space(tab.get("label")).lower():
        return "A focused renewal path for currently certified providers."
    if format_badge:
        return f"{format_badge} option with a clear class time and registration path."
    return "Hand-picked upcoming option with a clear seat reservation path."


def curated_offer_sessions(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for session in sort_by_momentum([item for item in sessions if session_enrolled_count(item) >= 1]):
        key = session_key(session)
        if key:
            by_key[key] = session
        if len(by_key) >= CURATED_OFFER_LIMIT:
            return list(by_key.values())

    for session in sort_by_start(sessions):
        key = session_key(session)
        if key and key not in by_key:
            by_key[key] = session
        if len(by_key) >= CURATED_OFFER_LIMIT:
            break

    return list(by_key.values())


def render_curated_offer_item(
    session: dict[str, Any],
    tab: dict[str, Any],
    *,
    page: dict[str, Any],
    index: int,
) -> str:
    page_slug = str(page.get("slug") or "")
    start_dt = parse_dt(session.get("start_at"))
    end_dt = parse_dt(session.get("end_at"))
    title = normalize_space(session.get("course_name")) or normalize_space(tab.get("label")) or "910CPR Class"
    location = clean_location(session.get("location_display") or session.get("location_name"))
    image_src = escape(hub_asset_url(tab.get("tab_icon") or page.get("hero_image"), "images/logo.png"), quote=True)
    image_alt = escape(tab.get("label") or page.get("hero_title") or "910CPR class")
    session_id = escape(str(session.get("session_id") or ""), quote=True)
    session_start = escape(start_dt.isoformat() if start_dt else "", quote=True)
    action_label, action_url, register_url = session_action(session, page_slug=page_slug)
    expanded = index == 0
    body_id = f"{tab.get('id')}-curated-offer-{index + 1}"
    enrolled_count = session_enrolled_count(session)
    benefit = offer_benefit_copy(tab, session)
    time_range = format_time_line(start_dt)
    detail_parts = [
        f"Class runs {time_range}.",
        f"Location: {location}.",
        "Use the registration button to reserve this specific session.",
    ]
    if enrolled_count >= 1:
        detail_parts.insert(1, momentum_label(enrolled_count).capitalize() + ".")

    return f"""
<article class="curated-offer-card{' is-open' if expanded else ''} js-session-item" data-session-id="{session_id}" data-session-start="{session_start}" data-start="{session_start}">
  <button class="curated-offer-header" type="button" aria-expanded="{'true' if expanded else 'false'}" aria-controls="{escape(body_id, quote=True)}" data-curated-offer-toggle>
    <span class="curated-offer-media">
      <img src="{image_src}" alt="{image_alt}" loading="lazy" onerror="this.style.display='none'">
    </span>
    <span class="curated-offer-main">
      <span class="curated-offer-title">{escape(title)}</span>
      <span class="curated-offer-meta">
        <span>{escape(format_date_line(start_dt))}</span>
        <span>{escape(format_time_line(start_dt))}</span>
        <span>{escape(location)}</span>
      </span>
      <span class="curated-offer-benefit">{escape(benefit)}</span>
    </span>
    <span class="curated-offer-status">{escape(seats_copy(enrolled_count))}</span>
    <span class="curated-offer-icon" aria-hidden="true"></span>
  </button>
  <div class="curated-offer-body" id="{escape(body_id, quote=True)}" {'data-open="true"' if expanded else 'hidden'} data-curated-offer-body>
    <div class="curated-offer-body-inner">
      <p>{escape(' '.join(detail_parts))}</p>
      <div class="curated-offer-actions">
        <a class="button small primary" href="{action_url}" data-original-href="{register_url}" data-session-id="{session_id}">{escape(action_label)}</a>
        <a class="button small secondary" href="{escape(tab['full_schedule_url'], quote=True)}">More dates</a>
      </div>
    </div>
  </div>
</article>
""".strip()


def render_curated_offers_section(page: dict[str, Any], tab: dict[str, Any], sessions: list[dict[str, Any]]) -> str:
    return ""


def group_request_href(program: str | None = None) -> str:
    if program:
        return f"/request_group_session.html?program={quote(program)}"
    return "/request_group_session.html"


def render_empty_state(page: dict[str, Any], tab: dict[str, Any], *, group_mode: bool) -> str:
    if tab.get("_visibility_state") == "menu_only_suppressed":
        copy = normalize_space(tab.get("_suppressed_public_copy")) or "Public dates are not currently listed for this option. This course may be available by request or for group training."
        help_href = "/courses/"
        group_href = group_request_href(tab.get("program") or page.get("hero_title"))
        return (
            "<div class='slug-empty slug-suppressed-option'>"
            f"<strong>{escape(tab.get('label') or 'Course option')}</strong>"
            f"<p>{escape(copy)}</p>"
            "<div class='slug-empty-actions'>"
            f"<a class='button primary' href='{escape(help_href, quote=True)}'>Help Me Choose</a>"
            f"<a class='button secondary' href='{escape(group_href, quote=True)}'>Group Training Request</a>"
            f"<a class='button secondary' href='tel:9103955193'>Call 910-395-5193</a>"
            "</div>"
            "</div>"
        )
    onsite_href = group_request_href(tab.get("program") or page.get("hero_title"))
    if str(page.get("slug") or "") == "heartsaver":
        return (
            "<div class='slug-empty slug-heartsaver-empty'>"
            "<strong>Public dates are not listed for this delivery option right now.</strong>"
            "<p>910CPR regularly teaches Heartsaver CPR, AED, First Aid, Pediatric, and workplace/public courses. More appointment times may be available as instructor availability opens, and group or workplace sessions can often be arranged around your schedule.</p>"
            "<div class='slug-empty-actions'>"
            f"<a class='button primary' href='{escape(onsite_href, quote=True)}'>Ask About Dates</a>"
            f"<a class='button secondary' href='tel:9103955193'>Call 910-395-5193</a>"
            "</div>"
            "</div>"
        )
    return (
        "<div class='slug-empty'>"
        f"<strong>{EMPTY_FALLBACK_TITLE}</strong>"
        f"<p>{EMPTY_FALLBACK_BODY}</p>"
        "<div class='slug-empty-actions'>"
        f"<a class='button primary' href='{escape(onsite_href, quote=True)}'>Ask About Dates</a>"
        f"<a class='button secondary' href='tel:9103955193'>Call 910-395-5193</a>"
        "</div>"
        "</div>"
    )


def momentum_label(enrolled_count: int) -> str:
    if enrolled_count <= 0:
        return ""
    if enrolled_count == 1:
        return "1 enrolled"
    return f"{enrolled_count} enrolled"


def render_inventory_section(
    title: str,
    body: str,
    sessions: list[dict[str, Any]],
    *,
    group_mode: bool,
    limit: int | None = None,
    empty_copy: str | None = None,
    section_class: str = "",
    page_slug: str = "",
    tab_label: str = "",
    initial_visible: int | None = None,
) -> str:
    selected = sessions[:limit] if limit is not None else sessions
    cards = "\n".join(render_schedule_row_card(session, group_mode=group_mode, page_slug=page_slug) for session in selected)
    if not cards and empty_copy:
        cards = f"<div class=\"slug-section-empty\"><p>{escape(empty_copy)}</p></div>"
    reveal_attrs = ""
    if not group_mode and sessions:
        reveal_label = tab_label or title
        visible_count = initial_visible if initial_visible is not None else HUB_INITIAL_VISIBLE_LIMIT
        reveal_attrs = (
            f' data-initial-visible="{visible_count}"'
            f' data-reveal-increment="{HUB_REVEAL_INCREMENT}"'
            f' data-reveal-label="{escape(reveal_label, quote=True)}"'
        )
    return f"""
<section class="slug-inventory-section {escape(section_class, quote=True)}">
  <div class="slug-inventory-head">
    <h3>{escape(title)}</h3>
    <p>{escape(body)}</p>
  </div>
  <div class="slug-pill-list"{reveal_attrs}>
    {cards}
  </div>
</section>
""".strip()


def render_schedule_row_card(row: dict[str, Any], *, group_mode: bool, page_slug: str) -> str:
    if row.get("_appointment_seed_offer"):
        return render_appointment_seed_offer_card(row)
    if row.get("_universal_request_offer"):
        return render_universal_request_offer_card(row)
    if row.get("_requestable_offer"):
        return render_requestable_offer_card(row, hub_slug=page_slug)
    return render_session_card(row, group_mode=group_mode, page_slug=page_slug)


def requestable_offers_for_page(page: dict[str, Any], grouped_offers: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    if str(page.get("slug") or "") != "bls":
        return []

    offers: list[dict[str, Any]] = []
    for course_key in sorted(BLS_REQUESTABLE_COURSE_KEYS):
        offers.extend(grouped_offers.get(course_key, []))
    return sorted(offers, key=lambda offer: parse_dt(offer.get("start_time")) or datetime.max.replace(tzinfo=TZ))


def requestable_offers_for_tab(page: dict[str, Any], tab: dict[str, Any], requestable_offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if str(page.get("slug") or "") != "bls":
        return []
    course_key = BLS_TAB_REQUESTABLE_COURSE_KEYS.get(str(tab.get("id") or ""))
    if not course_key:
        return []
    selected = []
    for offer in requestable_offers:
        if normalize_space(offer.get("course_key")) == course_key:
            row = dict(offer)
            row["_requestable_offer"] = True
            selected.append(row)
    return sorted(selected, key=lambda offer: parse_dt(offer.get("start_time")) or datetime.max.replace(tzinfo=TZ))


def schedule_row_start(row: dict[str, Any]) -> datetime:
    if row.get("_appointment_seed_offer"):
        value = row.get("start_datetime")
    elif row.get("_universal_request_offer"):
        value = row.get("start_datetime")
    elif row.get("_requestable_offer"):
        value = row.get("start_time")
    else:
        value = row.get("start_at")
    return parse_dt(value) or datetime.max.replace(tzinfo=TZ)


def schedule_row_kind(row: dict[str, Any]) -> str:
    if row.get("_appointment_seed_offer"):
        return "appointment_seed"
    if row.get("_universal_request_offer"):
        return "request_only"
    if row.get("_requestable_offer"):
        return "requestable"
    return "real_seated" if session_enrolled_count(row) >= 1 else "real_empty"


def real_gap_days(rows: list[dict[str, Any]]) -> int:
    real_starts = sorted(schedule_row_start(row) for row in rows if not row.get("_requestable_offer"))
    if len(real_starts) < 2:
        return 999
    gaps = [(after.date() - before.date()).days for before, after in zip(real_starts, real_starts[1:])]
    return max(gaps) if gaps else 0


def prioritize_bls_default_rows(rows: list[dict[str, Any]], config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    strategy = config.get("hub_display_strategy", {}) if isinstance(config, dict) else {}
    if not strategy.get("prefer_seated_real_classes", True):
        return rows, {"default_visible_count": min(len(rows), HUB_INITIAL_VISIBLE_LIMIT), "hidden_requestable_count": 0}

    minimum_real = int(strategy.get("minimum_real_rows_before_requestable", 3) or 3)
    requestable_cap = int(strategy.get("max_requestable_rows_in_default_view_per_course", 3) or 3)
    gap_threshold = int(strategy.get("show_requestable_when_real_gap_days_exceeds", 10) or 10)

    seated = [row for row in rows if schedule_row_kind(row) == "real_seated"]
    empty = [row for row in rows if schedule_row_kind(row) == "real_empty"]
    requestable = [row for row in rows if schedule_row_kind(row) == "requestable"]
    real_rows = [*seated, *empty]
    largest_gap = real_gap_days(rows)
    allow_requestable_default = (
        len(real_rows) < minimum_real
        or largest_gap > gap_threshold
        or not real_rows
    )
    default_rows = [*seated, *empty]
    if allow_requestable_default:
        default_rows.extend(requestable[:requestable_cap])

    seen = {id(row) for row in default_rows}
    remainder = [row for row in sorted(rows, key=schedule_row_start) if id(row) not in seen]
    ordered = [*default_rows, *remainder] if strategy.get("keep_full_interwoven_view_behind_show_more", True) else sorted(default_rows, key=schedule_row_start)
    default_visible_count = len(default_rows)
    hidden_requestable_count = max(0, len(requestable) - sum(1 for row in default_rows if row.get("_requestable_offer")))
    return ordered, {
        "default_visible_count": default_visible_count,
        "real_seated_default_visible": len(seated),
        "real_empty_default_visible": len(empty),
        "requestable_default_visible": sum(1 for row in default_rows if row.get("_requestable_offer")),
        "requestable_hidden_from_default": hidden_requestable_count,
        "largest_real_gap_days": largest_gap,
        "requestable_allowed_in_default": allow_requestable_default,
    }


def requestable_offer_month(offer: dict[str, Any]) -> str:
    start_dt = parse_dt(offer.get("start_time"))
    return start_dt.strftime("%Y-%m") if start_dt else "unknown"


def summarize_requestable_offers(offers: list[dict[str, Any]]) -> dict[str, Any]:
    by_course_key: dict[str, int] = {}
    by_month: dict[str, int] = {}
    for offer in offers:
        course_key = normalize_space(offer.get("course_key")) or "unknown"
        by_course_key[course_key] = by_course_key.get(course_key, 0) + 1
        month_key = requestable_offer_month(offer)
        by_month[month_key] = by_month.get(month_key, 0) + 1
    return {
        "requestable_offers_shown_count": len(offers),
        "requestable_offers_by_course_key": dict(sorted(by_course_key.items())),
        "requestable_offers_by_month": dict(sorted(by_month.items())),
        "requestable_offers_did_not_create_docs_classes_landers": True,
    }


def render_requestable_offer_card(offer: dict[str, Any], *, hub_slug: str = "bls") -> str:
    start_dt = parse_dt(offer.get("start_time"))
    end_dt = parse_dt(offer.get("end_time"))
    display_start_dt = debug_display_dt(start_dt, offer, kind_hint="requestable")
    display_end_dt = debug_display_dt(end_dt, offer, kind_hint="requestable")
    course_key = normalize_space(offer.get("course_key"))
    title = normalize_space(offer.get("course_display_name") or offer.get("course_title")) or "BLS requestable time"
    location = clean_location(offer.get("location_name") or offer.get("location_address"))
    label = normalize_space(offer.get("customer_label")) or "Request This Time"
    requested_start = escape(start_dt.isoformat() if start_dt else normalize_space(offer.get("start_time")), quote=True)
    requested_end = escape(end_dt.isoformat() if end_dt else normalize_space(offer.get("end_time")), quote=True)
    course_key_attr = escape(course_key, quote=True)
    click_target = requestable_offer_click_target(offer, hub_slug=hub_slug or "bls")
    button_href = escape(click_target["href"], quote=True)
    click_mode = escape(click_target["mode"], quote=True)
    offer_token = escape(click_target["token"], quote=True)
    offer_slug = escape(click_target.get("offer_slug") or normalize_space(offer.get("offer_slug") or offer.get("page_slug")), quote=True)
    token_signed = "true" if click_target["signed"] else "false"
    data_attrs = (
        'data-offer-source="customer_facing_offers" '
        'data-real-enrollware-session="false" '
        f'data-course-key="{course_key_attr}" '
        f'data-requested-start="{requested_start}" '
        f'data-start="{requested_start}" '
        f'data-session-start="{requested_start}" '
        f'data-offer-click-target="{click_mode}" '
        f'data-offer-slug="{offer_slug}" '
        f'data-offer-token="{offer_token}" '
        f'data-offer-token-signed="{token_signed}" '
        f'data-location-name="{escape(location, quote=True)}"'
    )
    time_range = format_time_line(display_start_dt)
    notice_minutes = offer.get("minimum_customer_notice_minutes_used")
    notice_copy = ""
    if notice_minutes not in (None, ""):
        notice_copy = f'<span class="slug-pill-chip">Notice window: {escape(str(notice_minutes))} min</span>'
    debug_badge = debug_source_badge_html(offer, kind_hint="requestable")

    return f"""
<article class="slug-pill slug-requestable-offer" {data_attrs} data-requested-end="{requested_end}"{debug_source_data_attrs(offer, kind_hint="requestable")}>
  <div class="slug-pill-date">
    <div class="slug-pill-month">{format_month(display_start_dt)}</div>
    <div class="slug-pill-day">{format_day(display_start_dt)}</div>
    <div class="slug-pill-weekday">{format_weekday(display_start_dt)}</div>
  </div>
  <div class="slug-pill-main">
    <div class="slug-pill-title">{escape(format_date_line(display_start_dt))}</div>
    <div class="slug-pill-meta-row">
      <span class="slug-pill-chip">{escape(time_range)}</span>
      <span class="slug-pill-chip slug-pill-chip-location">{escape(location)}</span>
      {notice_copy}
      {debug_badge}
    </div>
    <div class="slug-pill-subtitle">{escape(title)}</div>
  </div>
  <div class="slug-pill-actions">
    <a class="button small secondary" href="{button_href}" {data_attrs}>{escape(label)}</a>
  </div>
</article>
""".strip()


def render_requestable_offers_section(page: dict[str, Any], offers: list[dict[str, Any]]) -> str:
    if str(page.get("slug") or "") != "bls" or not offers:
        return ""

    cards = "\n".join(render_requestable_offer_card(offer, hub_slug=str(page.get("slug") or "bls")) for offer in offers)
    return f"""
<section class="slug-inventory-section slug-requestable-offers-section" id="request-this-time" aria-label="Requestable BLS times">
  <div class="slug-inventory-head">
    <h3>Need another BLS time?</h3>
    <p>These times are based on current instructor availability and must be confirmed before booking.</p>
  </div>
  <div class="slug-pill-list slug-requestable-offer-list">
    {cards}
  </div>
  <p class="slug-flexible-note">Requestable times are confirmed before a booking link is created.</p>
</section>
""".strip()


def appointment_offers_for_tab(tab: dict[str, Any], appointment_offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tab_id = normalize_space(tab.get("id"))
    selected: list[dict[str, Any]] = []
    for offer in appointment_offers:
        course_key = normalize_space(offer.get("course_key"))
        tab_ids = set(offer.get("tab_ids", [])) if isinstance(offer.get("tab_ids"), list) else set()
        if tab_id in tab_ids or tab_id in APPOINTMENT_COURSE_TAB_IDS.get(course_key, set()):
            row = dict(offer)
            row["_appointment_seed_offer"] = True
            selected.append(row)
    return sorted(selected, key=lambda item: parse_dt(item.get("start_datetime")) or datetime.max.replace(tzinfo=TZ))


def request_only_offers_for_tab(tab: dict[str, Any], universal_offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tab_id = normalize_space(tab.get("id"))
    selected: list[dict[str, Any]] = []
    for offer in universal_offers:
        if offer.get("display_item_type") != "request_only_availability_offer":
            continue
        tab_ids = set(offer.get("tab_ids", [])) if isinstance(offer.get("tab_ids"), list) else set()
        if tab_id and tab_id in tab_ids:
            row = dict(offer)
            row["_universal_request_offer"] = True
            selected.append(row)
    return sorted(selected, key=lambda item: parse_dt(item.get("start_datetime")) or datetime.max.replace(tzinfo=TZ))


def future_request_blocks_for_tab(tab: dict[str, Any], universal_offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tab_id = normalize_space(tab.get("id"))
    selected: list[dict[str, Any]] = []
    for offer in universal_offers:
        if offer.get("display_item_type") != "future_request_block":
            continue
        tab_ids = set(offer.get("tab_ids", [])) if isinstance(offer.get("tab_ids"), list) else set()
        if tab_id and tab_id in tab_ids:
            row = dict(offer)
            row["_future_request_block"] = True
            selected.append(row)
    return sorted(selected, key=lambda item: parse_dt(item.get("start_datetime")) or datetime.max.replace(tzinfo=TZ))


def render_appointment_seed_offer_card(offer: dict[str, Any]) -> str:
    start_dt = parse_dt(offer.get("start_datetime"))
    end_dt = parse_dt(offer.get("end_datetime"))
    display_start_dt = debug_display_dt(start_dt, offer, kind_hint="appointment_seed")
    display_end_dt = debug_display_dt(end_dt, offer, kind_hint="appointment_seed")
    title = normalize_space(offer.get("course_title")) or "Available class time"
    instructor = normalize_space(offer.get("instructor_display_name") or offer.get("instructor_key")).title()
    location = clean_location(offer.get("location_name") or offer.get("offer_location") or offer.get("location_key"))
    if not is_valid_appointment_seed_registration_url(offer.get("appointment_registration_url")):
        return ""
    url = escape(offer.get("appointment_registration_url") or "#", quote=True)
    presentation_mode = normalize_space(offer.get("presentation_mode"))
    source_offer_id = normalize_space(offer.get("source_offer_id"))
    render_source = normalize_space(offer.get("render_source"))
    start_attr = escape(start_dt.isoformat() if start_dt else normalize_space(offer.get("start_datetime")), quote=True)
    end_attr = escape(end_dt.isoformat() if end_dt else normalize_space(offer.get("end_datetime")), quote=True)
    time_range = format_time_line(display_start_dt)
    if display_start_dt and display_end_dt:
        time_range = f"{format_time_line(display_start_dt)} - {format_time_line(display_end_dt)}"
    data_attrs = (
        f'data-start="{start_attr}" '
        f'data-end="{end_attr}" '
        f'data-source-offer-id="{escape(source_offer_id, quote=True)}" '
        f'data-render-source="{escape(render_source, quote=True)}" '
        f'data-presentation-mode="{escape(presentation_mode, quote=True)}"'
    )
    flexible_choices = offer.get("flexible_start_choices") if isinstance(offer.get("flexible_start_choices"), list) else []
    flexible_html = ""
    action_html = f'<a class="button small primary" href="{url}">Book This Class</a>'
    if presentation_mode == "flexible_start_window" and flexible_choices:
        time_range = "Start times available"
        label = "Choose your start time:"
        choice_links = []
        valid_choice_records = []
        seen_start_times: set[str] = set()
        sorted_choices = sorted(
            [choice for choice in flexible_choices if isinstance(choice, dict)],
            key=lambda choice: parse_dt(choice.get("appointment_display_start")) or datetime.max.replace(tzinfo=TZ),
        )
        for choice in sorted_choices:
            if not isinstance(choice, dict):
                continue
            if not is_valid_appointment_seed_registration_url(choice.get("appointment_registration_url")):
                continue
            choice_url = escape(choice.get("appointment_registration_url") or "#", quote=True)
            choice_start_dt = parse_dt(choice.get("appointment_display_start"))
            choice_label = normalize_space(choice.get("start_time"))
            if choice_start_dt:
                choice_label = format_time_line(choice_start_dt)
            if not choice_label or choice_label in seen_start_times:
                continue
            seen_start_times.add(choice_label)
            choice_offer_id = escape(normalize_space(choice.get("offer_id")), quote=True)
            valid_choice_records.append((choice, choice_label, choice_offer_id, choice_url))
            choice_links.append(
                f'<a class="slug-flexible-start-time-link" href="{choice_url}" data-source-offer-id="{choice_offer_id}">{escape(choice_label)}</a>'
            )
        if choice_links:
            if len(choice_links) == 1:
                _single_choice, single_label, single_offer_id, single_url = valid_choice_records[0]
                action_html = f'<a class="button small primary" href="{single_url}" data-source-offer-id="{single_offer_id}">Register for {escape(single_label)}</a>'
                flexible_html = ""
            else:
                flexible_html = f"""
  <div class="slug-flexible-start-choices" aria-label="Choose your start time">
    <div class="slug-flexible-start-label">{escape(label)}</div>
    <div class="slug-flexible-start-choice-list">
      {'<span class="slug-flexible-start-separator">·</span>'.join(choice_links)}
    </div>
  </div>"""
                action_html = '<span class="slug-pill-action-note">Select a start time below</span>'
    return f"""
<article class="slug-pill slug-appointment-option" {data_attrs}{debug_source_data_attrs(offer, kind_hint="appointment_seed")}>
  <div class="slug-pill-date">
    <div class="slug-pill-month">{format_month(display_start_dt)}</div>
    <div class="slug-pill-day">{format_day(display_start_dt)}</div>
    <div class="slug-pill-weekday">{format_weekday(display_start_dt)}</div>
  </div>
  <div class="slug-pill-main">
    <div class="slug-pill-title">{escape(format_date_line(display_start_dt))}</div>
    <div class="slug-pill-meta-row">
      <span class="slug-pill-chip">{escape(time_range)}</span>
      <span class="slug-pill-chip slug-pill-chip-location">{escape(location)}</span>
      <span class="slug-pill-chip">Available class option</span>
      {debug_source_badge_html(offer, kind_hint="appointment_seed")}
      {f'<span class="slug-pill-chip">Instructor: {escape(instructor)}</span>' if instructor else ''}
    </div>
    <div class="slug-pill-subtitle">{escape(title)}</div>
  </div>
  <div class="slug-pill-actions">
    {action_html}
  </div>
  {flexible_html}
</article>
""".strip()


def render_universal_request_offer_card(offer: dict[str, Any]) -> str:
    start_dt = parse_dt(offer.get("start_datetime"))
    end_dt = parse_dt(offer.get("end_datetime"))
    lock_end_dt = parse_dt(offer.get("scheduler_consumption_end"))
    display_start_dt = debug_display_dt(start_dt, offer, kind_hint="universal_request")
    display_end_dt = debug_display_dt(end_dt, offer, kind_hint="universal_request")
    display_lock_end_dt = debug_display_dt(lock_end_dt, offer, kind_hint="universal_request")
    title = normalize_space(offer.get("course_title")) or "Available training time"
    location = clean_location(offer.get("location_name"))
    url = escape(offer.get("request_url") or group_request_href(title), quote=True)
    label = normalize_space(offer.get("cta_label")) or "Ask about this time"
    time_range = format_time_line(display_start_dt)
    if display_start_dt and display_end_dt:
        time_range = f"{format_time_line(display_start_dt)} - {format_time_line(display_end_dt)}"
    note = normalize_space(offer.get("display_note")) or "This time is based on instructor availability and must be confirmed before a booking link is created."
    lock_note = ""
    if start_dt and lock_end_dt and lock_end_dt > (end_dt or start_dt):
        lock_note = f'<span class="slug-pill-chip">Time held through {escape(format_time_line(display_lock_end_dt))}</span>'
    return f"""
<article class="slug-pill slug-request-time-option"{debug_source_data_attrs(offer, kind_hint="universal_request")}>
  <div class="slug-pill-date">
    <div class="slug-pill-month">{format_month(display_start_dt)}</div>
    <div class="slug-pill-day">{format_day(display_start_dt)}</div>
    <div class="slug-pill-weekday">{format_weekday(display_start_dt)}</div>
  </div>
  <div class="slug-pill-main">
    <div class="slug-pill-title">{escape(format_date_line(display_start_dt))}</div>
    <div class="slug-pill-meta-row">
      <span class="slug-pill-chip">{escape(time_range)}</span>
      <span class="slug-pill-chip slug-pill-chip-location">{escape(location)}</span>
      <span class="slug-pill-chip">Confirm before booking</span>
      {debug_source_badge_html(offer, kind_hint="universal_request")}
      {lock_note}
    </div>
    <div class="slug-pill-subtitle">{escape(title)}</div>
    <p class="slug-flexible-note">{escape(note)}</p>
  </div>
  <div class="slug-pill-actions">
    <a class="button small secondary" href="{url}">{escape(label)}</a>
  </div>
</article>
""".strip()


def render_future_request_block_panel(offer: dict[str, Any]) -> str:
    title = normalize_space(offer.get("course_title")) or "this course"
    location = clean_location(offer.get("location_name"))
    url = escape(offer.get("request_url") or group_request_href(title), quote=True)
    label = normalize_space(offer.get("cta_label")) or "Request a future block"
    preferred_month = normalize_space(offer.get("preferred_month"))
    month_copy = ""
    if preferred_month:
        try:
            month_dt = datetime.strptime(preferred_month, "%Y-%m")
            month_copy = f'<span class="slug-pill-chip">Planning window: {escape(month_dt.strftime("%B %Y"))}</span>'
        except ValueError:
            month_copy = f'<span class="slug-pill-chip">Planning window: {escape(preferred_month)}</span>'
    location_copy = f'<span class="slug-pill-chip slug-pill-chip-location">{escape(location)}</span>' if location else ""
    return f"""
<section class="slug-inventory-section slug-future-request-section" aria-label="Request a future training block">
  <div class="slug-pill-list">
    <article class="slug-pill slug-future-request-block">
      <div class="slug-pill-main">
        <div class="slug-pill-title">Need a later date?</div>
        <div class="slug-pill-meta-row">
          {month_copy}
          {location_copy}
        </div>
        <div class="slug-pill-subtitle">We can often arrange {escape(title)} beyond the currently listed schedule.</div>
        <p class="slug-flexible-note">Future requests are checked against instructor availability, course duration, setup time, cleanup time, and location constraints before confirmation.</p>
      </div>
      <div class="slug-pill-actions">
        <a class="button small secondary" href="{url}">{escape(label)}</a>
      </div>
    </article>
  </div>
</section>
""".strip()


def render_appointment_seed_offers_section(offers: list[dict[str, Any]]) -> str:
    if not offers:
        return ""
    cards = "\n".join(render_appointment_seed_offer_card(offer) for offer in offers)
    return f"""
<section class="slug-inventory-section slug-appointment-options-section" aria-label="Available class options">
  <div class="slug-inventory-head">
    <h3>Available class option</h3>
    <p>These available options can be booked through the normal 910CPR registration path.</p>
  </div>
  <div class="slug-pill-list slug-appointment-options-list">
    {cards}
  </div>
</section>
""".strip()


def build_flexible_lookup(page: dict[str, Any], tab: dict[str, Any], sessions: list[dict[str, Any]]) -> dict[str, Any] | None:
    location_id = str(tab.get("flexible_location_id") or page.get("flexible_location_id") or "").strip()
    course_id = str(tab.get("flexible_course_id") or "").strip() or extract_schedule_course_id(tab.get("full_schedule_url"))
    if not location_id or not course_id:
        return None

    appointment_page_url = build_appointment_page_url(location_id, course_id)
    seed_dates = tab.get("flexible_seed_dates") or seed_dates_from_sessions(sessions)
    return {
        "endpoint": APPOINTMENT_ENDPOINT,
        "appointment_page_url": appointment_page_url,
        "location_id": location_id,
        "course_id": course_id,
        "cache_seconds": int(tab.get("flexible_cache_seconds") or page.get("flexible_cache_seconds") or 180),
        "seed_dates": seed_dates,
        "label": tab.get("label"),
    }


def render_flexible_section(page: dict[str, Any], tab: dict[str, Any], sessions: list[dict[str, Any]]) -> str:
    lookup = build_flexible_lookup(page, tab, sessions)
    if not lookup:
        return ""

    payload = {
        "endpoint": lookup["endpoint"],
        "locationId": lookup["location_id"],
        "courseId": lookup["course_id"],
        "appointmentPageUrl": lookup["appointment_page_url"],
        "cacheSeconds": lookup["cache_seconds"],
        "seedDates": lookup["seed_dates"],
        "label": lookup["label"],
    }
    attrs = escape(json.dumps(payload), quote=True)
    return f"""
<section class="slug-inventory-section slug-flexible-section" data-flexible-availability="{attrs}">
  <div class="slug-inventory-head">
    <h3>Flexible Available Times</h3>
    <p>Need a different time? Check flexible availability and view all available open seats for this class path.</p>
  </div>
  <div class="slug-flexible-shell">
    <div class="slug-flexible-copy">
      <strong>Don’t see a scheduled time that works?</strong>
      <p>Open the live flexible-time view for this course, or load the latest available open seats here when supported.</p>
    </div>
    <div class="slug-flexible-actions">
      <button class="button secondary" type="button" data-flexible-load>Check flexible availability</button>
      <a class="button secondary" href="{escape(lookup['appointment_page_url'], quote=True)}">View all available open seats</a>
    </div>
    <div class="slug-flexible-results" data-flexible-results hidden></div>
    <p class="slug-flexible-note" data-flexible-note>Flexible times are loaded live and may change quickly.</p>
  </div>
</section>
""".strip()


def render_tab_button(tab: dict[str, Any], *, active: bool) -> str:
    active_class = " active" if active else ""
    icon = escape(hub_asset_url(tab.get("tab_icon"), "images/tab_classroom.png"), quote=True)
    badge = escape(tab.get("tab_badge") or "", quote=False)
    label = escape(tab["label"])
    program = escape(tab["program"], quote=True)
    target = escape(tab["id"], quote=True)
    badge_html = f'<span class="hub-tab-tag">{badge}</span>' if badge else ""

    return (
        f"<button class='tab-btn{active_class}' data-program='{program}' data-tab-target='#{target}' type='button'>"
        f"<img class=\"hub-tab-icon\" src=\"{icon}\" alt=\"\" loading=\"lazy\" onerror=\"this.style.display='none'\">"
        f"<span class=\"hub-tab-copy\"><span class=\"hub-tab-label\">{label}</span>{badge_html}</span>"
        "</button>"
    )


def render_panel_description(tab: dict[str, Any]) -> str:
    short_text = escape(tab.get("description_short") or tab.get("description") or "")
    more_text = escape(tab.get("description_more") or "")
    if not more_text:
        return f'<p class="slug-panel-copy">{short_text}</p>'
    return (
        "<div class=\"slug-panel-description\">"
        f"<p class=\"slug-panel-copy\">{short_text}</p>"
        f"<p class=\"slug-panel-copy slug-panel-copy-extra\">{more_text}</p>"
        "</div>"
    )


def full_schedule_short_label(page: dict[str, Any]) -> str:
    labels = {
        "bls": "BLS",
        "acls": "ACLS",
        "pals": "PALS",
        "heartsaver": "Heartsaver",
        "uscg-elementary-first-aid-cpr": "USCG",
    }
    return labels.get(str(page.get("slug") or ""), "Class")


def render_tab_panel(
    page: dict[str, Any],
    tab: dict[str, Any],
    sessions: list[dict[str, Any]],
    *,
    active: bool,
    group_mode: bool,
    requestable_offers: list[dict[str, Any]] | None = None,
    appointment_seed_offers: list[dict[str, Any]] | None = None,
    universal_offers: list[dict[str, Any]] | None = None,
) -> str:
    panel_class = "tab-panel active" if active else "tab-panel"
    keep_empty_tab_ids = {
        "heartsaver": {
            "hs-fa-cpr-aed-ip",
            "hs-fa-cpr-aed-bl",
            "hs-cpr-aed-ip",
            "hs-cpr-aed-bl",
            "hs-pediatric-ip",
            "hs-pediatric-bl",
        },
        "pals": {"pals-heartcode"},
    }
    keep_empty_attr = (
        ' data-keep-empty-tab="true"'
        if tab.get("id") in keep_empty_tab_ids.get(str(page.get("slug") or ""), set())
        else ""
    )
    if group_mode:
        request_href = group_request_href(tab["program"])
        full_schedule_data = escape(
            json.dumps(
                {
                    "url": tab["full_schedule_url"],
                    "label": tab["full_schedule_label"],
                }
            ),
            quote=True,
        )
        return f"""
<section class="{panel_class}" id="{escape(tab['id'], quote=True)}" data-banner="{full_schedule_data}"{keep_empty_attr}>
  <div class="slug-panel-card">
    <div class="slug-panel-head">
      <div>
        <h2>{escape(tab['label'])}</h2>
        {render_panel_description(tab)}
      </div>
    </div>
    <section class="slug-inventory-section slug-scheduled-section">
      <div class="slug-pill-list">
        <article class="slug-pill slug-group-request-pill">
          <div class="slug-pill-main">
            <div class="slug-pill-title">{escape(tab['label'])}</div>
            <div class="slug-pill-subtitle">Private request-based training at your location. Share your preferred date, location, and group size and we’ll confirm availability.</div>
          </div>
          <div class="slug-pill-actions">
            <a class="button small primary" href="{escape(request_href, quote=True)}">Request This Training</a>
          </div>
        </article>
      </div>
    </section>
  </div>
</section>
""".strip()

    tab_appointment_seed_offers = appointment_offers_for_tab(tab, appointment_seed_offers or [])
    tab_request_only_offers = request_only_offers_for_tab(tab, universal_offers or [])
    tab_future_request_blocks = future_request_blocks_for_tab(tab, universal_offers or [])
    tab_requestable_offers = requestable_offers_for_tab(page, tab, requestable_offers or [])
    upcoming_sessions = sorted([*sort_by_start(sessions), *tab_requestable_offers, *tab_appointment_seed_offers, *tab_request_only_offers], key=schedule_row_start)
    default_visible_count: int | None = None
    if str(page.get("slug") or "") == "bls" and not tab_appointment_seed_offers:
        upcoming_sessions, default_strategy = prioritize_bls_default_rows(upcoming_sessions, load_free_time_scheduler_config())
        default_visible_count = int(default_strategy.get("default_visible_count") or len(upcoming_sessions))
    elif tab_appointment_seed_offers:
        default_visible_count = len(upcoming_sessions)

    section_html: list[str] = []
    curated_html = render_curated_offers_section(page, tab, sessions)
    if curated_html:
        section_html.append(curated_html)

    if upcoming_sessions:
        inventory_title = "Upcoming dates"
        inventory_body = (
            "Browse upcoming class times here. Some times are requestable and confirmed before a booking link is created."
            if tab_requestable_offers or tab_request_only_offers
            else "Browse upcoming class times here, then use Book This Class for the exact session you want."
        )
        if str(page.get("slug") or "") == "heartsaver":
            inventory_title = "Next scheduled class" if len(upcoming_sessions) == 1 else "Upcoming dates"
            inventory_body = (
                "Don't see a time that works? Request a private or group class."
            )
        section_html.append(
            render_inventory_section(
                inventory_title,
                inventory_body,
                upcoming_sessions,
                group_mode=group_mode,
                limit=None,
                section_class="slug-scheduled-section",
                page_slug=str(page.get("slug") or ""),
                tab_label=str(tab.get("label") or page.get("hero_title") or "class"),
                initial_visible=default_visible_count,
            )
        )
    else:
        section_html.append(render_empty_state(page, tab, group_mode=group_mode))

    if tab_future_request_blocks:
        section_html.append(render_future_request_block_panel(tab_future_request_blocks[0]))

    flexible_html = ""
    full_schedule_data = escape(
        json.dumps(
            {
                "url": tab["full_schedule_url"],
                "label": tab["full_schedule_label"],
            }
        ),
        quote=True,
    )
    inventory_label = "Start here, more dates available"
    schedule_short_label = full_schedule_short_label(page)
    escape_hatch_html = ""
    panel_sections = "\n    ".join(part for part in [" ".join(section_html), flexible_html, escape_hatch_html] if part)

    return f"""
<section class="{panel_class}" id="{escape(tab['id'], quote=True)}" data-banner="{full_schedule_data}"{keep_empty_attr}>
  <div class="slug-panel-card">
    <div class="slug-panel-head">
      <div>
        <div class="slug-panel-kicker">{escape(inventory_label)}</div>
        <h2>{escape(tab['label'])}</h2>
        {render_panel_description(tab)}
      </div>
    </div>
    {panel_sections}
  </div>
</section>
""".strip()


def render_hero_image(page: dict[str, Any]) -> str:
    hero_image = hub_asset_url(page.get("hero_image"))
    if not hero_image:
        return ""
    hero_alt = escape(page.get("hero_image_alt") or page["hero_title"])
    return (
        "<div class=\"slug-hero-image-wrap\">"
        f"<img class=\"slug-hero-image\" src=\"{escape(hero_image, quote=True)}\" alt=\"{hero_alt}\" loading=\"lazy\" onerror=\"this.parentElement.hidden=true\">"
        "</div>"
    )


def render_hero_actions(page: dict[str, Any], first_tab: dict[str, Any], *, group_mode: bool) -> str:
    if group_mode:
        primary_href = f"/request_group_session.html?program={quote(first_tab['program'])}"
        primary_label = first_tab["primary_cta_label"]
        return (
            "<div class=\"slug-hero-actions\">"
            f"<a class=\"button primary\" href=\"{escape(primary_href, quote=True)}\">{escape(primary_label)}</a>"
            "</div>"
        )

    return ""


def render_group_training_push(page: dict[str, Any], first_tab: dict[str, Any], *, group_mode: bool) -> str:
    if group_mode:
        return ""
    onsite_href = group_request_href(first_tab.get("program") or page.get("hero_title"))
    classes_href = "#ecosystem-categories" if page.get("ecosystem_hub") else f"#slug-tabs-{escape(page['slug'], quote=True)}"
    if str(page.get("slug") or "") == "heartsaver":
        classes_href = "/courses/heartsaver-first-aid-cpr-aed.html"
    return f"""
  <section class="group-training-push" aria-label="On-site group training">
    <div class="group-training-copy">
      <div class="home-status-label">Group Training</div>
      <h2>Training for your team? We come to you.</h2>
      <p>No travel. No scheduling headaches. Your team already knows where to go.</p>
    </div>
    <div class="group-training-actions">
      <a class="button primary group-training-primary" href="{escape(onsite_href, quote=True)}">Schedule On-Site Training</a>
      <div class="group-training-individual">
        <p>Just need a seat for yourself? Scroll down. We’ve got you covered.</p>
        <a class="button secondary" href="{classes_href}">View Upcoming Classes</a>
      </div>
    </div>
  </section>
""".rstrip()


def resolve_guidance_banners(page: dict[str, Any], banner_library: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    seen: set[str] = set()
    for banner_id in page.get("guidance_banner_ids", []):
        key = str(banner_id).strip()
        if not key or key in seen:
            continue
        banner = banner_library.get(key)
        if not banner or not banner.get("enabled", True):
            continue
        seen.add(key)
        resolved.append({"id": key, **banner})
    return resolved


def render_guidance_banners(page: dict[str, Any], banner_library: dict[str, dict[str, Any]]) -> str:
    banners = resolve_guidance_banners(page, banner_library)
    if not banners:
        return ""

    rendered: list[str] = []
    for banner in banners:
        eyebrow = escape(banner.get("eyebrow") or "Guidance")
        title = escape(banner.get("title") or "")
        body = escape(banner.get("body") or "")
        actions: list[str] = []
        for action in banner.get("actions", []):
            href = str(action.get("href") or "").strip()
            label = str(action.get("label") or "").strip()
            if not href or not label:
                continue
            variant = "secondary" if action.get("variant") == "secondary" else "primary"
            actions.append(
                f"<a class=\"button {variant}\" href=\"{escape(href, quote=True)}\">{escape(label)}</a>"
            )

        rendered.append(
            f"""
  <section class=\"slug-guidance-banner\" data-guidance-banner=\"{escape(banner['id'], quote=True)}\">
    <div class=\"slug-guidance-copy\">
      <div class=\"slug-guidance-eyebrow\">{eyebrow}</div>
      <h2>{title}</h2>
      <p>{body}</p>
    </div>
    {f'<div class=\"slug-guidance-actions\">{"".join(actions)}</div>' if actions else ''}
  </section>
""".strip()
        )

    return f"<div class=\"slug-guidance-stack\">{''.join(rendered)}</div>"


def render_emergency_alert() -> str:
    return ""


def render_banner(page: dict[str, Any], first_tab: dict[str, Any]) -> str:
    return f"""
  <section class="slug-banner">
    <div class="slug-banner-copy">
      <div class="slug-banner-eyebrow">Full Schedule</div>
      <h2>{escape(page['full_schedule_banner'])}</h2>
    </div>
    <div class="slug-banner-actions">
      <a class="button primary" data-full-schedule-link href="{escape(first_tab['full_schedule_url'], quote=True)}">{escape(first_tab['full_schedule_label'])}</a>
    </div>
  </section>
""".strip()


def render_other_training_options(page: dict[str, Any]) -> str:
    cards = page.get("other_training_options", [])
    if not cards:
        return ""
    rendered = []
    for card in cards:
        rendered.append(
            f"""
<article class="training-option-card">
  <h3>{escape(card['label'])}</h3>
  <p>{escape(card['description'])}</p>
  <a class="text-link strong-link" href="{escape(card['href'], quote=True)}">{escape(card['cta'])}</a>
</article>
""".strip()
        )
    return f"""
  <section class="slug-training-options">
    <div class="slug-banner-copy">
      <div class="slug-banner-eyebrow">Other Training Options</div>
      <h2>Need a different certifying body or delivery path?</h2>
    </div>
    <div class="training-option-grid">
      {''.join(rendered)}
    </div>
  </section>
""".strip()


def render_heartsaver_course_jumps(page: dict[str, Any]) -> str:
    if page.get("slug") != "heartsaver":
        return ""
    cards = [
        {
            "href": "/courses/heartsaver-first-aid-cpr-aed.html",
            "image": "images/HS-FA-CPR-AED.jpeg",
            "title": "Heartsaver First Aid CPR AED",
            "copy": "For workplace and community responders who need practical first aid, CPR, and AED training. Topics include choking, naloxone awareness, FAST stroke recognition, seizures, asthma, burns, heat illness, and common injury response.",
            "featured": True,
        },
        {
            "href": "/courses/heartsaver-cpr-aed.html",
            "image": "images/HS-CPR-AED.jpeg",
            "title": "Heartsaver CPR AED",
            "copy": "A focused CPR/AED path for people who do not need the first aid module. It reinforces adult and child choking response and why breaths may matter in opioid-related respiratory arrest.",
        },
        {
            "href": "/courses/heartsaver-first-aid.html",
            "image": "images/HS-FA.jpeg",
            "title": "Heartsaver First Aid",
            "copy": "First aid only, without CPR or AED. This course focuses on recognizing and responding to common injuries and illnesses such as bleeding, burns, allergic reactions, fainting, seizures, heat illness, and other everyday emergencies.",
        },
        {
            "href": "/courses/heartsaver-pediatric-first-aid-cpr-aed.html",
            "image": "images/HS-PEDI-FA-CPR-AED.jpeg",
            "title": "Pediatric First Aid CPR AED",
            "copy": "For childcare, school, camp, and caregiver teams that need infant and child CPR, AED, choking, seizure, asthma, allergic reaction, heat illness, burn, and injury response practice.",
        },
        {
            "href": "/courses/bloodborne-pathogens.html",
            "image": "images/HS-BBP.jpeg",
            "title": "Bloodborne Pathogens",
            "copy": "Heartsaver Bloodborne Pathogens online course teaches employees how to protect themselves and others from being exposed to blood or blood-containing materials. This course is designed to meet OSHA requirements for bloodborne pathogens training when paired with site-specific instruction.",
        },
    ]
    rendered = []
    for card in cards:
        card_class = "course-jump-card heartsaver-jump-card"
        if card.get("featured"):
            card_class += " heartsaver-featured-card"
        rendered.append(
            f"""
        <a class="{card_class}" href="{escape(card['href'], quote=True)}">
          <img src="{escape(card['image'], quote=True)}" alt="" loading="lazy">
          <strong>{escape(card['title'])}</strong>
          <span>{escape(card['copy'])}</span>
          <b>View course options</b>
        </a>
""".rstrip()
        )
    return f"""
  <section class="home-course-jumps heartsaver-course-jumps" aria-label="Heartsaver course options">
    <div class="section-heading heartsaver-course-heading">
      <div>
        <div class="eyebrow">General Public Courses</div>
        <h2>Jump to Heartsaver options</h2>
      </div>
      <p class="section-copy">Workforce, construction, childcare, health and fitness, hospitality, and general public CPR, AED, and first aid paths.</p>
    </div>
    <div class="heartsaver-course-grid">
      {''.join(rendered)}
    </div>
  </section>
""".rstrip()


def heartsaver_delivery_label(tab: dict[str, Any]) -> str:
    badge = normalize_space(tab.get("tab_badge"))
    if "online" in badge.lower() or "skills" in badge.lower() or "blended" in badge.lower():
        return "Blended / Online + Skills"
    return "In-person"


def render_heartsaver_delivery_choice(tab: dict[str, Any], *, active: bool = False) -> str:
    icon = escape(hub_asset_url(tab.get("tab_icon"), "images/tab_classroom.png"), quote=True)
    if icon and not icon.startswith("/"):
        icon = f"/{icon}"
    label = normalize_space(tab.get("label")) or heartsaver_delivery_label(tab)
    badge = normalize_space(tab.get("tab_badge")) or heartsaver_delivery_label(tab)
    active_class = " active" if active else ""
    tab_id = escape(tab["id"], quote=True)
    program = escape(tab.get("program") or "", quote=True)
    badge_html = f'<span class="hub-tab-tag">{escape(badge)}</span>' if badge else ""
    return f"""
        <button class="tab-btn heartsaver-delivery-tab{active_class}" data-tab-target="#{tab_id}" data-program="{program}" type="button">
          <img class="hub-tab-icon" src="{icon}" alt="" loading="lazy" onerror="this.style.display='none'">
          <span class="hub-tab-copy">
            <span class="hub-tab-label">{escape(label)}</span>
            {badge_html}
            <span class="hub-tab-tag hub-tab-count" data-count-target>Checking dates</span>
          </span>
        </button>
""".rstrip()


def render_heartsaver_request_only_section(section: dict[str, str]) -> str:
    actions = "".join(
        f"<a class=\"button {escape(action['variant'], quote=True)}\" href=\"{escape(action['href'], quote=True)}\">{escape(action['label'])}</a>"
        for action in section["actions"]
    )
    return f"""
  <section class="section-box heartsaver-course-flow" id="{escape(section['id'], quote=True)}">
    <div class="section-heading heartsaver-course-heading">
      <div>
        <div class="eyebrow">Course selected</div>
        <h2>{escape(section['title'])}</h2>
      </div>
      <p class="section-copy">{escape(section['copy'])}</p>
    </div>
    <div class="slug-empty">
      <strong>{escape(section['status_title'])}</strong>
      <p>{escape(section['status_copy'])}</p>
      <div class="slug-empty-actions">{actions}</div>
    </div>
  </section>
""".rstrip()


def render_heartsaver_course_flow(
    page: dict[str, Any],
    visible_tabs: list[tuple[dict[str, Any], list[dict[str, Any]]]],
    *,
    group_mode: bool,
    requestable_offers: list[dict[str, Any]] | None = None,
    appointment_seed_offers: list[dict[str, Any]] | None = None,
    universal_offers: list[dict[str, Any]] | None = None,
    only_group_ids: set[str] | None = None,
) -> str:
    if page.get("slug") != "heartsaver":
        return ""

    tab_lookup = {tab.get("id"): (tab, matched) for tab, matched in visible_tabs}
    groups = [
        {
            "id": "heartsaver-first-aid-cpr-aed",
            "title": "Heartsaver First Aid CPR AED",
            "copy": "Choose this when your requirement includes first aid, CPR, and AED.",
            "tab_ids": ["hs-fa-cpr-aed-ip", "hs-fa-cpr-aed-bl"],
        },
        {
            "id": "heartsaver-cpr-aed",
            "title": "Heartsaver CPR AED",
            "copy": "Choose this when your requirement is CPR and AED only, without first aid.",
            "tab_ids": ["hs-cpr-aed-ip", "hs-cpr-aed-bl"],
        },
        {
            "id": "heartsaver-first-aid",
            "title": "Heartsaver First Aid",
            "copy": "First Aid only, no CPR or AED.",
            "request_only": True,
            "status_title": "First Aid-only is usually arranged by request.",
            "status_copy": "Heartsaver First Aid-only training is usually arranged for workplaces, groups, or special requests. If you need First Aid as an individual, contact us and we will help you find the best option.",
            "actions": [
                {"label": "Ask about First Aid options", "href": "/request_group_session.html?program=Heartsaver%20First%20Aid", "variant": "primary"},
                {"label": "Call 910-395-5193", "href": "tel:9103955193", "variant": "secondary"},
            ],
        },
        {
            "id": "heartsaver-pediatric-first-aid-cpr-aed",
            "title": "Pediatric First Aid CPR AED",
            "copy": "Choose this for childcare, school, camp, and caregiver requirements.",
            "tab_ids": ["hs-pediatric-ip", "hs-pediatric-bl"],
        },
        {
            "id": "heartsaver-bloodborne-pathogens",
            "title": "Bloodborne Pathogens",
            "copy": "Bloodborne pathogens training is usually coordinated for workplace or site-specific needs.",
            "request_only": True,
            "status_title": "Bloodborne Pathogens is handled by request.",
            "status_copy": "Tell us what your workplace or compliance requirement says and we will help route the right Heartsaver Bloodborne Pathogens option.",
            "actions": [
                {"label": "Request Bloodborne Pathogens training", "href": "/request_group_session.html?program=Bloodborne%20Pathogens", "variant": "primary"},
                {"label": "Call 910-395-5193", "href": "tel:9103955193", "variant": "secondary"},
            ],
        },
    ]

    rendered: list[str] = []
    for group in groups:
        if only_group_ids and str(group["id"]) not in only_group_ids:
            continue
        if group.get("request_only"):
            rendered.append(render_heartsaver_request_only_section(group))
            continue

        choices: list[str] = []
        panels: list[str] = []
        for tab_index, tab_id in enumerate(group.get("tab_ids", [])):
            tab_match = tab_lookup.get(tab_id)
            if not tab_match:
                continue
            tab, matched = tab_match
            choices.append(render_heartsaver_delivery_choice(tab, active=tab_index == 0))
            panels.append(
                render_tab_panel(
                    page,
                    tab,
                    matched,
                    active=tab_index == 0,
                    group_mode=group_mode,
                    requestable_offers=requestable_offers or [],
                    appointment_seed_offers=appointment_seed_offers or [],
                    universal_offers=universal_offers or [],
                )
            )

        if not choices and not panels:
            continue

        rendered.append(
            f"""
  <section class="section-box heartsaver-course-flow" id="{escape(group['id'], quote=True)}" data-tabs>
    <div class="section-heading heartsaver-course-heading">
      <div>
        <div class="eyebrow">Course selected</div>
        <h2>{escape(group['title'])}</h2>
      </div>
      <p class="section-copy">{escape(group['copy'])}</p>
    </div>
    <div class="tabs hub-tabs heartsaver-delivery-tabs" aria-label="{escape(group['title'], quote=True)} delivery choices">
      {''.join(choices)}
    </div>
    <div class="heartsaver-delivery-panels">
      {''.join(panels)}
    </div>
  </section>
""".rstrip()
        )

    return "\n".join(rendered)


def render_heartsaver_split_course_page(
    page: dict[str, Any],
    visible_tabs: list[tuple[dict[str, Any], list[dict[str, Any]]]],
    *,
    group_id: str,
    title: str,
    description: str,
    appointment_seed_offers: list[dict[str, Any]],
    requestable_offers: list[dict[str, Any]],
    universal_offers: list[dict[str, Any]],
) -> str:
    flow = render_heartsaver_course_flow(
        page,
        visible_tabs,
        group_mode=False,
        requestable_offers=requestable_offers,
        appointment_seed_offers=appointment_seed_offers,
        universal_offers=universal_offers,
        only_group_ids={group_id},
    )
    body = f"""
<div class="card slug-hub-shell heartsaver-course-page">
  <header class="site-brand-bar">
    <a class="site-brand-link" href="/index.html" aria-label="910CPR home">
      <img class="site-brand-logo" src="/images/logo.png" alt="910CPR logo" loading="eager" onerror="this.src='/images/910CPR_wave.jpg';this.onerror=null;">
      <span class="site-brand-wordmark">910CPR</span>
    </a>
  </header>
  <section class="hero slug-hero">
    <div class="hero-main">
      <div class="eyebrow">Heartsaver Course Hub</div>
      <h1>{escape(title)}</h1>
      <p class="subhead">{escape(description)}</p>
      <div class="slug-hero-actions">
        <a class="button secondary" href="/heartsaver.html">Back to all Heartsaver options</a>
      </div>
    </div>
  </section>
  <div class="heartsaver-course-flow-stack">
    {flow}
  </div>
  {render_other_training_options(page)}
</div>
"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} | 910CPR</title>
<meta name="description" content="{escape(description)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://www.910cpr.com/courses/{escape(group_id)}.html">
<link rel="icon" type="image/png" href="/images/logo.png">
<link rel="shortcut icon" href="/images/logo.png">
<link rel="apple-touch-icon" href="/images/logo.png">
<link rel="stylesheet" href="/css/lander.css">
</head>
<body>
<div class="wrap">
  <div class="page-shell">
    {body}
  </div>
</div>
<script src="/assets/hub-ui.js?v=20260511-hash-tabs"></script>
<script src="/assets/live-sessions.js"></script>
<script src="/assets/session-expiry.js"></script>
<script src="/assets/hybrid-inventory.js"></script>
</body>
</html>"""


def render_heartsaver_alias_page(*, title: str, target_path: str, canonical_path: str, description: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} | 910CPR</title>
<meta name="description" content="{escape(description)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://www.910cpr.com{escape(canonical_path)}">
<meta http-equiv="refresh" content="0; url={escape(target_path)}">
<link rel="stylesheet" href="/css/lander.css">
</head>
<body>
<div class="wrap">
  <div class="page-shell">
    <div class="card slug-hub-shell">
      <header class="site-brand-bar">
        <a class="site-brand-link" href="/index.html" aria-label="910CPR home">
          <img class="site-brand-logo" src="/images/logo.png" alt="910CPR logo" loading="eager">
          <span class="site-brand-wordmark">910CPR</span>
        </a>
      </header>
      <section class="hero slug-hero">
        <div class="hero-main">
          <div class="eyebrow">Heartsaver Course Hub</div>
          <h1>{escape(title)}</h1>
          <p class="subhead">{escape(description)}</p>
          <div class="slug-hero-actions">
            <a class="button primary" href="{escape(target_path)}">Open current course page</a>
            <a class="button secondary" href="/heartsaver.html">Back to Heartsaver options</a>
          </div>
        </div>
      </section>
    </div>
  </div>
</div>
</body>
</html>"""


def write_heartsaver_split_course_pages(
    page: dict[str, Any],
    sessions: list[dict[str, Any]],
    *,
    requestable_offers: list[dict[str, Any]],
    appointment_seed_offers: list[dict[str, Any]],
    universal_offers: list[dict[str, Any]],
    build_meta: dict[str, str],
) -> list[Path]:
    now = datetime.now(TZ)
    universal_tab_ids = {
        normalize_space(tab_id)
        for offer in universal_offers
        for tab_id in (offer.get("tab_ids", []) if isinstance(offer.get("tab_ids"), list) else [])
        if normalize_space(tab_id)
    }
    visible_tabs = visible_tabs_for_page(page, sessions, now=now, force_visible_tab_ids=universal_tab_ids)
    pages = [
        {
            "group_id": "heartsaver-first-aid-cpr-aed",
            "title": "Heartsaver First Aid CPR AED",
            "description": "The most common Heartsaver path for workplace and community responders who need First Aid, CPR, and AED training.",
        },
        {
            "group_id": "heartsaver-cpr-aed",
            "title": "Heartsaver CPR AED",
            "description": "CPR and AED training for people who do not need the First Aid module.",
        },
        {
            "group_id": "heartsaver-first-aid",
            "title": "Heartsaver First Aid",
            "description": "First Aid-only training for workplaces, groups, special requests, and individuals who need help choosing the best path.",
        },
        {
            "group_id": "heartsaver-pediatric-first-aid-cpr-aed",
            "title": "Pediatric First Aid CPR AED",
            "description": "Pediatric first aid, CPR, and AED training for childcare, school, camp, and caregiver requirements.",
        },
        {
            "group_id": "bloodborne-pathogens",
            "title": "Bloodborne Pathogens",
            "description": "Bloodborne pathogens training for workplace or site-specific exposure-control requirements.",
        },
    ]
    COURSES_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for spec in pages:
        html = render_heartsaver_split_course_page(
            page,
            visible_tabs,
            group_id=spec["group_id"],
            title=spec["title"],
            description=spec["description"],
            appointment_seed_offers=appointment_seed_offers,
            requestable_offers=requestable_offers,
            universal_offers=universal_offers,
        )
        html = apply_build_metadata(html, build_meta)
        html = clean_generated_html(html)
        output_path = COURSES_OUTPUT_DIR / f"{spec['group_id']}.html"
        output_path.write_text(html, encoding="utf-8")
        written.append(output_path)
    alias_path = COURSES_OUTPUT_DIR / "aha-heartsaver-cpr-aed.html"
    alias_html = render_heartsaver_alias_page(
        title="AHA Heartsaver CPR AED",
        target_path="/courses/heartsaver-cpr-aed.html",
        canonical_path="/courses/heartsaver-cpr-aed.html",
        description="Use the current Heartsaver CPR AED course hub for in-person and blended CPR/AED options.",
    )
    alias_html = apply_build_metadata(alias_html, build_meta)
    alias_html = clean_generated_html(alias_html)
    alias_path.write_text(alias_html, encoding="utf-8")
    written.append(alias_path)
    return written


def render_brand_bar() -> str:
    return """
<header class="site-brand-bar">
  <a class="site-brand-link" href="index.html" aria-label="910CPR home">
    <img class="site-brand-logo" src="images/logo.png" alt="910CPR logo" loading="eager" onerror="this.src='images/910CPR_wave.jpg';this.onerror=null;">
    <span class="site-brand-wordmark">910CPR</span>
  </a>
</header>
""".strip()


def sync_uscg_old_url_to_selector() -> Path | None:
    """Keep the old USCG public URL backed by the live selector page when available."""
    if not USCG_SELECTOR_PAGE.exists():
        return None
    USCG_OLD_PUBLIC_PAGE.write_text(USCG_SELECTOR_PAGE.read_text(encoding="utf-8"), encoding="utf-8")
    return USCG_OLD_PUBLIC_PAGE


def render_ecosystem_session_preview(sessions: list[dict[str, Any]], *, page_slug: str, empty_copy: str) -> str:
    if not sessions:
        return f"""
        <div class="finder-empty ecosystem-empty">
          <strong>{escape(empty_copy)}</strong>
          <p>For help choosing a class path, call or text 910-395-5193.</p>
        </div>
""".rstrip()
    selected = sorted(sessions, key=schedule_row_start)[:3]
    return "\n".join(render_schedule_row_card(session, group_mode=False, page_slug=page_slug) for session in selected)


def render_ecosystem_category_card(
    page: dict[str, Any],
    tab: dict[str, Any],
    sessions: list[dict[str, Any]],
    *,
    appointment_seed_offers: list[dict[str, Any]] | None = None,
    universal_offers: list[dict[str, Any]] | None = None,
) -> str:
    card_image = escape(hub_asset_url(tab.get("card_image") or page.get("hero_image"), "images/logo.png"), quote=True)
    card_alt = escape(tab.get("card_image_alt") or tab.get("label") or page.get("hero_title") or "", quote=True)
    href = escape(safe_public_href(tab.get("full_schedule_url"), f"#{tab.get('id')}"), quote=True)
    request_href = escape(group_request_href(tab.get("program") or tab.get("label")), quote=True)
    empty_copy = tab.get("empty_copy") or page.get("empty_copy") or "Upcoming dates are being added. Call/text 910-395-5193 for scheduling assistance."
    chips = []
    if tab.get("tab_badge"):
        chips.append(f"<span class=\"finder-pill-tag\">{escape(tab['tab_badge'])}</span>")
    for chip in tab.get("category_chips", []):
        chips.append(f"<span class=\"finder-pill-tag finder-pill-tag-format\">{escape(chip)}</span>")
    chips_html = f"<div class=\"finder-pill-tags\">{''.join(chips)}</div>" if chips else ""
    points_html = "".join(f"<li>{escape(point)}</li>" for point in tab.get("ecosystem_points", []))
    points_block = f"<ul class=\"ecosystem-points\">{points_html}</ul>" if points_html else ""
    request_only_offers = request_only_offers_for_tab(tab, universal_offers or [])
    combined_sessions = sorted([*sessions, *(appointment_seed_offers or []), *request_only_offers], key=schedule_row_start)
    session_count = len(combined_sessions)
    session_label = f"{session_count} upcoming date{'s' if session_count != 1 else ''}" if session_count else "Scheduling assistance available"

    return f"""
      <section class="finder-card ecosystem-card" id="{escape(tab['id'], quote=True)}">
        <div class="finder-card-head ecosystem-card-head">
          <div>
            <div class="home-status-label">{escape(session_label)}</div>
            <h3>{escape(tab['label'])}</h3>
            <p class="finder-card-copy">{escape(tab.get('description') or '')}</p>
            {chips_html}
          </div>
          <img class="class-card-course-image ecosystem-card-logo" src="{card_image}" alt="{card_alt}" loading="lazy" onerror="this.style.display='none'">
        </div>
        {points_block}
        <div class="finder-pills ecosystem-session-list">
          {render_ecosystem_session_preview(combined_sessions, page_slug=str(page.get('slug') or ''), empty_copy=empty_copy)}
        </div>
        <div class="finder-card-actions ecosystem-card-actions">
          <a class="button primary" href="{href}">{escape(tab.get('primary_cta_label') or 'View Details')}</a>
          <a class="button secondary" href="{request_href}">{escape(tab.get('secondary_cta_label') or 'Ask About Dates')}</a>
        </div>
      </section>
""".rstrip()


def render_ecosystem_page(
    page: dict[str, Any],
    sessions: list[dict[str, Any]],
    banner_library: dict[str, dict[str, Any]],
    *,
    appointment_seed_offers: list[dict[str, Any]] | None = None,
    universal_offers: list[dict[str, Any]] | None = None,
) -> str:
    now = datetime.now(TZ)
    tabs = page.get("tabs", [])
    category_cards: list[str] = []
    jump_links: list[str] = []
    for tab in tabs:
        matched = []
        for session in sessions:
            enriched = enrich_session_for_page(session, page, tab, now=now)
            if enriched:
                matched.append(enriched)
        matched = sort_sessions(matched)
        tab_seed_offers = []
        if page.get("suppress_dynamic_appointment_offers") is not True:
            tab_seed_offers = appointment_offers_for_tab(tab, appointment_seed_offers or [])
        jump_links.append(f"<a class=\"jump-chip\" href=\"#{escape(tab['id'], quote=True)}\">{escape(tab['label'])}</a>")
        category_cards.append(render_ecosystem_category_card(page, tab, matched, appointment_seed_offers=tab_seed_offers, universal_offers=universal_offers or []))

    future_cards = []
    for card in page.get("future_categories", []):
        future_cards.append(
            f"""
<article class="training-option-card">
  <h3>{escape(card['label'])}</h3>
  <p>{escape(card['description'])}</p>
  <a class="text-link strong-link" href="{escape(card.get('href') or group_request_href(card['label']), quote=True)}">{escape(card.get('cta') or 'Ask about this option')}</a>
</article>
""".strip()
        )
    future_block = (
        f"""
  <section class="slug-training-options ecosystem-future-options">
    <div class="slug-banner-copy">
      <div class="slug-banner-eyebrow">Additional Paths</div>
      <h2>{escape(page.get('future_categories_title') or 'More options can be coordinated')}</h2>
    </div>
    <div class="training-option-grid">
      {''.join(future_cards)}
    </div>
  </section>
""".rstrip()
        if future_cards
        else ""
    )

    first_tab = tabs[0]
    body = f"""
<div class="card slug-hub-shell ecosystem-hub ecosystem-{escape(page['slug'], quote=True)}">
  {render_brand_bar()}
  <section class="hero slug-hero home-hero ecosystem-hero">
    <div class="hero-main">
      <div class="eyebrow">{escape(page['eyebrow'])}</div>
      <h1>{escape(page['hero_title'])}</h1>
      <p class="subhead">{escape(page['hero_copy'])}</p>
      <div class="hero-actions">
        <a class="button primary" href="#ecosystem-categories">{escape(page.get('primary_cta_label') or 'Compare course options')}</a>
        <a class="button secondary" href="{escape(group_request_href(page.get('hero_title')), quote=True)}">{escape(page.get('secondary_cta_label') or 'Request group training')}</a>
      </div>
    </div>
    <div class="hero-side">
      {render_hero_image(page)}
      <div class="trust-badge ecosystem-trust-badge">
        <strong>{escape(page.get('trust_title') or 'Permanent training hub')}</strong>
        <span>{escape(page.get('trust_copy') or 'Use this page for class routing, renewals, QR codes, and future scheduling updates.')}</span>
      </div>
    </div>
  </section>
  {render_guidance_banners(page, banner_library)}
  <section class="home-jumps ecosystem-jumps" aria-label="{escape(page['hero_title'], quote=True)} quick links">
    {''.join(jump_links)}
  </section>
  <section class="home-finder ecosystem-categories" id="ecosystem-categories">
    <div class="section-heading">
      <div>
        <div class="eyebrow">{escape(page.get('category_eyebrow') or 'Course Categories')}</div>
        <h2>{escape(page.get('category_title') or 'Choose your training path')}</h2>
      </div>
      <p class="section-copy">{escape(page.get('category_copy') or 'Each category stays available even while new dates are being added.')}</p>
    </div>
    <div class="finder-grid">
      {''.join(category_cards)}
    </div>
  </section>
  {future_block}
  {render_google_trust_block()}
  {render_group_training_push(page, first_tab, group_mode=False)}
  {render_other_training_options(page)}
</div>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(page['title'])}</title>
<meta name="description" content="{escape(page['description'])}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://www.910cpr.com/{escape(page['slug'])}.html">
<link rel="icon" type="image/png" href="images/logo.png">
<link rel="shortcut icon" href="images/logo.png">
<link rel="apple-touch-icon" href="images/logo.png">
<link rel="stylesheet" href="css/lander.css">
</head>
<body>
<div class="wrap">
  <div class="page-shell">
    {body}
  </div>
</div>
<script src="assets/hub-ui.js?v=20260511-hash-tabs"></script>
<script src="assets/live-sessions.js"></script>
<script src="assets/session-expiry.js"></script>
<script src="assets/hybrid-inventory.js"></script>
</body>
</html>"""


def visible_tabs_for_page(
    page: dict[str, Any],
    sessions: list[dict[str, Any]],
    *,
    now: datetime,
    force_visible_tab_ids: set[str] | None = None,
) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    page_slug = str(page.get("slug") or "")
    visible_tabs: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    visibility_policy = load_course_visibility_policy()
    for tab in page.get("tabs", []):
        visibility_state = tab_visibility_state(tab, visibility_policy)
        if visibility_state == "hidden":
            continue
        tab_course_id = next(iter(sorted(tab_course_ids(tab))), "")
        tab = {
            **tab,
            "_visibility_state": visibility_state,
            "_suppressed_public_copy": suppressed_course_copy(tab_course_id, visibility_policy) if visibility_state == "menu_only_suppressed" else "",
        }
        matched = []
        if visibility_state != "menu_only_suppressed":
            for session in sessions:
                enriched = enrich_session_for_page(session, page, tab, now=now)
                if enriched:
                    matched.append(enriched)
        matched = sort_sessions(matched)
        keep_empty_tab_ids = {
            "heartsaver": {
                "hs-fa-cpr-aed-ip",
                "hs-fa-cpr-aed-bl",
                "hs-cpr-aed-ip",
                "hs-cpr-aed-bl",
                "hs-pediatric-ip",
                "hs-pediatric-bl",
            },
            "pals": {"pals-heartcode"},
        }
        keep_empty_tab = (
            bool(page.get("keep_empty_tabs"))
            or tab.get("id") in keep_empty_tab_ids.get(page_slug, set())
            or tab.get("id") in (force_visible_tab_ids or set())
        )
        if matched or keep_empty_tab:
            if page_slug == "heartsaver":
                display = heartsaver_tab_display(tab, matched)
                tab = {**tab, **display}
            visible_tabs.append((tab, matched))
    return visible_tabs


def render_page(
    page: dict[str, Any],
    sessions: list[dict[str, Any]],
    banner_library: dict[str, dict[str, Any]],
    *,
    requestable_offers: list[dict[str, Any]] | None = None,
    appointment_seed_offers: list[dict[str, Any]] | None = None,
    universal_offers: list[dict[str, Any]] | None = None,
) -> str:
    if page.get("ecosystem_hub"):
        return render_ecosystem_page(page, sessions, banner_library, appointment_seed_offers=appointment_seed_offers or [], universal_offers=universal_offers or [])

    group_mode = bool(page.get("group_mode"))
    page_slug = str(page.get("slug") or "")
    now = datetime.now(TZ)
    tabs = page.get("tabs", [])
    first_tab = tabs[0]
    universal_tab_ids = {
        normalize_space(tab_id)
        for offer in (universal_offers or [])
        for tab_id in (offer.get("tab_ids", []) if isinstance(offer.get("tab_ids"), list) else [])
        if normalize_space(tab_id)
    }
    visible_tabs = visible_tabs_for_page(page, sessions, now=now, force_visible_tab_ids=universal_tab_ids)

    buttons: list[str] = []
    panels: list[str] = []

    for index, (tab, matched) in enumerate(visible_tabs):
        buttons.append(render_tab_button(tab, active=index == 0))
        panels.append(
            render_tab_panel(
                page,
                tab,
                matched,
                active=index == 0,
                group_mode=group_mode,
                requestable_offers=requestable_offers or [],
                appointment_seed_offers=appointment_seed_offers or [],
                universal_offers=universal_offers or [],
            )
        )

    if page_slug == "heartsaver":
        tabs_html = ""
    else:
        tabs_html = (
            f"""
  <section class="section-box slug-tabs-block" id="slug-tabs-{escape(page['slug'], quote=True)}" data-tabs>
    <div class="tabs hub-tabs">
      {''.join(buttons)}
    </div>
    {''.join(panels)}
  </section>
"""
            if visible_tabs
            else f"""
  <section class="section-box slug-tabs-block" id="slug-tabs-{escape(page['slug'], quote=True)}" data-tabs>
    <div class="slug-empty hub-empty-state">
      <strong>{escape(EMPTY_FALLBACK_TITLE)}</strong>
      <p>{escape(EMPTY_FALLBACK_BODY)}</p>
    </div>
  </section>
"""
        )

    body = f"""
<div class="card slug-hub-shell">
  {render_brand_bar()}
  <section class="hero slug-hero">
    <div class="hero-main">
      <div class="eyebrow">{escape(page['eyebrow'])}</div>
      <h1>{escape(page['hero_title'])}</h1>
      <p class="subhead">{escape(page['hero_copy'])}</p>
      {render_hero_actions(page, first_tab, group_mode=group_mode)}
    </div>
    <div class="hero-side">
      {render_hero_image(page)}
    </div>
  </section>
  {render_emergency_alert()}
  {render_guidance_banners(page, banner_library)}
  {render_heartsaver_course_jumps(page)}
  {tabs_html}
  {render_google_trust_block()}
  {render_group_training_push(page, first_tab, group_mode=group_mode)}
  {render_other_training_options(page)}
</div>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(page['title'])}</title>
<meta name="description" content="{escape(page['description'])}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://www.910cpr.com/{escape(page['slug'])}.html">
<link rel="icon" type="image/png" href="images/logo.png">
<link rel="shortcut icon" href="images/logo.png">
<link rel="apple-touch-icon" href="images/logo.png">
<link rel="stylesheet" href="css/lander.css">
</head>
<body>
<div class="wrap">
  <div class="page-shell">
    {body}
  </div>
</div>
<script src="assets/hub-ui.js?v=20260511-hash-tabs"></script>
<script src="assets/live-sessions.js"></script>
<script src="assets/session-expiry.js"></script>
<script src="assets/hybrid-inventory.js"></script>
</body>
</html>"""


def clean_generated_html(html: str) -> str:
    return "\n".join(line.rstrip() for line in html.splitlines()).rstrip() + "\n"


def build() -> None:
    reporter = BuildStatusReporter("build_slug_hubs")
    schedule_source_path = authoritative_schedule_path()
    reporter.set_context(inputs=[MANIFEST_PATH, schedule_source_path], outputs=[OUTPUT_DIR])
    reporter.waiting(total=0)
    manifest_payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if isinstance(manifest_payload, dict):
        manifest = manifest_payload.get("pages", [])
        banner_library = manifest_payload.get("guidance_banners", {})
    else:
        manifest = manifest_payload
        banner_library = {}

    sessions, schedule_source_path = load_authoritative_schedule()
    grouped_customer_offers = load_customer_facing_offers()
    universal_offers_by_page = load_universal_offer_inventory()
    universal_appointment_seed_offers_by_page = {
        hub_slug: [
            offer for offer in offers
            if offer.get("display_item_type") == "appointment_seed_offer"
        ]
        for hub_slug, offers in universal_offers_by_page.items()
    }
    appointment_seed_offers_by_page = merge_appointment_seed_offers(
        universal_appointment_seed_offers_by_page,
        load_hub_appointment_seed_offers(),
        load_public_sellable_appointment_seed_offers(),
    )
    now = datetime.now(TZ)
    build_meta = current_build_metadata("scripts/build_slug_hubs.py", f"slug hub rebuild from {schedule_source_label(schedule_source_path)}")

    reporter.start(total=len(manifest))
    last_output: Path | None = None
    all_hub_debug_records: list[dict[str, Any]] = []
    requestable_offer_summary_by_page: dict[str, dict[str, Any]] = {}
    schedule_rows_by_page: dict[str, dict[str, Any]] = {}
    try:
        for index, page in enumerate(manifest, start=1):
            page_requestable_offers = requestable_offers_for_page(page, grouped_customer_offers)
            page_slug = str(page.get("slug") or "")
            page_appointment_seed_offers = appointment_seed_offers_by_page.get(page_slug, [])
            page_universal_offers = universal_offers_by_page.get(page_slug, [])
            requestable_offer_summary_by_page[page_slug] = summarize_requestable_offers(page_requestable_offers)
            schedule_rows_by_page[page_slug] = hub_group_schedule_summary(page, sessions, page_requestable_offers, now=now)
            html = render_page(
                page,
                sessions,
                banner_library,
                requestable_offers=page_requestable_offers,
                appointment_seed_offers=page_appointment_seed_offers,
                universal_offers=page_universal_offers,
            )
            html = apply_build_metadata(html, build_meta)
            html = clean_generated_html(html)
            last_output = OUTPUT_DIR / f"{page['slug']}.html"
            last_output.write_text(html, encoding="utf-8")
            all_hub_debug_records.extend(
                write_hub_runtime_debug(
                    page,
                    sessions,
                    now=now,
                    source_path=schedule_source_path,
                    requestable_offers=page_requestable_offers,
                )
            )
            if page.get("slug") == "acls":
                write_acls_runtime_debug(page, sessions, now=now, source_path=schedule_source_path)
            if page.get("slug") == "heartsaver":
                write_heartsaver_runtime_debug(page, sessions, now=now, source_path=schedule_source_path)
                for course_output in write_heartsaver_split_course_pages(
                    page,
                    sessions,
                    requestable_offers=page_requestable_offers,
                    appointment_seed_offers=page_appointment_seed_offers,
                    universal_offers=page_universal_offers,
                    build_meta=build_meta,
                ):
                    print(f"Wrote {course_output}")
            reporter.update(current=index, total=len(manifest), last_output_file=last_output)
            print(f"Wrote {last_output}")
        uscg_alias_output = sync_uscg_old_url_to_selector()
        if uscg_alias_output:
            print(f"Wrote {uscg_alias_output}")
        consolidated_debug_path = ROOT / "debug" / "hub_session_classification.json"
        consolidated_debug_path.parent.mkdir(parents=True, exist_ok=True)
        consolidated_debug_path.write_text(
            json.dumps(
                {
                    "generated_at": now.isoformat(),
                    "source_schedule_path": schedule_source_label(schedule_source_path),
                    "customer_facing_offers_path": schedule_source_label(CUSTOMER_FACING_OFFERS_PATH),
                    "requestable_offer_summary_by_page": requestable_offer_summary_by_page,
                    "schedule_rows_by_page": schedule_rows_by_page,
                    "records": all_hub_debug_records,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        reporter.done(
            current=len(manifest),
            total=len(manifest),
            last_output_file=last_output,
            pages_generated=len(manifest),
            counts={
                "sessions_loaded": len(sessions),
                "slug_hub_pages": len(manifest),
                "schedule_source": schedule_source_label(schedule_source_path),
            },
        )
        write_status_snapshot()
    except Exception:
        reporter.error(last_output_file=last_output)
        raise


if __name__ == "__main__":
    build()
