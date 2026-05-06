from __future__ import annotations

import json
import re
from datetime import datetime
from html import escape, unescape
from pathlib import Path
from typing import Any
from urllib.parse import quote

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


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "config" / "slug_hubs.json"
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
REVIEWS_FILE = ROOT / "data" / "raw" / "reviews" / "reviews.json"
OUTPUT_DIR = ROOT / "docs"
STATE_DIR = ROOT / "data" / "state"
RUNTIME_DIR = ROOT / "data" / "runtime"
SESSIONS_CURRENT_PATH = ROOT / "data" / "sessions_current.json"
TZ = ZoneInfo("America/New_York")
DATE_LIMIT = 6
POPULAR_LIMIT = 4
EMPTY_FALLBACK_TITLE = "No selected times showing here, but you still have options."
EMPTY_FALLBACK_BODY = "View the full schedule for additional dates, request a class time, or ask about on-site training for your team."
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


def approved_locations_for_page(page: dict[str, Any]) -> set[str]:
    return {
        clean_location(location)
        for location in page.get("approved_public_locations", [])
        if clean_location(location)
    }


def public_inventory_decision(session: dict[str, Any], page: dict[str, Any]) -> tuple[bool, str]:
    location_raw = normalize_space(session.get("location_display") or session.get("location_name"))
    course_name = normalize_space(session.get("course_name"))
    course_subtitle = normalize_space(session.get("course_subtitle"))
    haystack = normalize_match_text(f"{course_name} {course_subtitle} {location_raw}")
    location_clean = clean_location(location_raw)

    approved_locations = approved_locations_for_page(page)
    if approved_locations and location_clean not in approved_locations:
        return False, "excluded:unapproved_location"

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
    haystack = f"{course_name} {course_subtitle}".lower()
    course_name_lower = course_name.lower()

    codes = {normalize_space(code) for code in tab.get("course_codes", []) if normalize_space(code)}
    if codes:
        if course_code:
            matched = course_code in codes
        else:
            needles = [str(item).lower() for item in tab.get("name_contains", []) if str(item).strip()]
            matched = not needles or any(needle in haystack for needle in needles)
    else:
        needles = [str(item).lower() for item in tab.get("name_contains", []) if str(item).strip()]
        matched = not needles or any(needle in haystack for needle in needles)

    if not matched:
        return False

    excludes = [str(item).lower() for item in tab.get("exclude_name_contains", []) if str(item).strip()]
    return not any(needle in course_name_lower for needle in excludes)


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


def write_acls_runtime_debug(page: dict[str, Any], future_sessions: list[dict[str, Any]], *, now: datetime) -> None:
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
        "source_schedule_future_path": str(SCHEDULE_PATH),
        "page_slug": page.get("slug"),
        "records": records,
    }
    output_path = RUNTIME_DIR / "acls_hub_debug.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_heartsaver_runtime_debug(page: dict[str, Any], future_sessions: list[dict[str, Any]], *, now: datetime) -> None:
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
        "source_schedule_future_path": str(SCHEDULE_PATH),
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
        "tab_icon": tab.get("tab_icon") or "/images/tab_classroom.png",
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


def render_session_card(session: dict[str, Any], *, group_mode: bool) -> str:
    start_dt = parse_dt(session.get("start_at"))
    end_dt = parse_dt(session.get("end_at"))
    location = clean_location(session.get("location_display") or session.get("location_name"))
    title = normalize_space(session.get("course_name"))
    register_url = escape(session.get("registration_url") or "#", quote=True)
    session_start = escape(start_dt.isoformat() if start_dt else "", quote=True)
    session_end = escape(end_dt.isoformat() if end_dt else "", quote=True)
    session_id = escape(str(session.get("session_id") or ""), quote=True)
    format_badge = normalize_space(session.get("_format_badge"))
    family_badge = normalize_space(session.get("_family_badge"))
    enrolled_count = session_enrolled_count(session)

    action_label = "See Public Class" if group_mode else "Book Seat"
    action_hint = ""
    badge_html = ""
    if format_badge:
        badge_html += f'<span class="slug-pill-chip slug-pill-chip-format">{escape(format_badge)}</span>'
    if family_badge:
        badge_html += f'<span class="slug-pill-chip slug-pill-chip-family">{escape(family_badge)}</span>'
    if enrolled_count >= 1 and not group_mode:
        badge_html += '<span class="slug-pill-chip slug-pill-chip-momentum">Already Enrolled</span>'
        badge_html += f'<span class="slug-pill-chip slug-pill-chip-momentum">{escape(momentum_label(enrolled_count))}</span>'
        badge_html += (
            '<span class="slug-pill-chip slug-pill-chip-momentum">'
            + ("Filling" if enrolled_count >= 2 else "Popular Time")
            + "</span>"
        )

    return f"""
<article class="slug-pill js-session-item" data-session-id="{session_id}" data-start="{session_start}" data-end="{session_end}" data-session-start="{session_start}">
  <div class="slug-pill-date">
    <div class="slug-pill-month">{format_month(start_dt)}</div>
    <div class="slug-pill-day">{format_day(start_dt)}</div>
    <div class="slug-pill-weekday">{format_weekday(start_dt)}</div>
  </div>
  <div class="slug-pill-main">
    <div class="slug-pill-title">{escape(format_date_line(start_dt))}</div>
    <div class="slug-pill-meta-row">
      <span class="slug-pill-chip">{escape(format_time_line(start_dt))}</span>
      <span class="slug-pill-chip slug-pill-chip-location">{escape(location)}</span>
      {badge_html}
    </div>
    <div class="slug-pill-subtitle">{escape(title)}</div>
  </div>
  <div class="slug-pill-actions">
    {f'<div class="slug-pill-hint">{escape(action_hint)}</div>' if action_hint else ''}
    <a class="button small primary" href="{register_url}" data-original-href="{register_url}">{action_label}</a>
  </div>
</article>
""".strip()


def group_request_href(program: str | None = None) -> str:
    if program:
        return f"/request_group_session.html?program={quote(program)}"
    return "/request_group_session.html"


def render_empty_state(page: dict[str, Any], tab: dict[str, Any], *, group_mode: bool) -> str:
    full_schedule_url = str(tab.get("full_schedule_url") or page.get("full_schedule_url") or "#")
    onsite_href = group_request_href(tab.get("program") or page.get("hero_title"))
    return (
        "<div class='slug-empty'>"
        f"<strong>{EMPTY_FALLBACK_TITLE}</strong>"
        f"<p>{EMPTY_FALLBACK_BODY}</p>"
        "<div class='slug-empty-actions'>"
        f"<a class='button primary' href='{escape(full_schedule_url, quote=True)}'>View Full Schedule</a>"
        f"<a class='button secondary' href='{escape(onsite_href, quote=True)}'>Request On-Site Training</a>"
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
) -> str:
    selected = sessions[:limit] if limit is not None else sessions
    cards = "\n".join(render_session_card(session, group_mode=group_mode) for session in selected)
    if not cards and empty_copy:
        cards = f"<div class=\"slug-section-empty\"><p>{escape(empty_copy)}</p></div>"
    return f"""
<section class="slug-inventory-section {escape(section_class, quote=True)}">
  <div class="slug-inventory-head">
    <h3>{escape(title)}</h3>
    <p>{escape(body)}</p>
  </div>
  <div class="slug-pill-list">
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
    icon = escape(tab.get("tab_icon") or "/images/tab_classroom.png", quote=True)
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
        "<button class=\"slug-more-toggle\" type=\"button\" data-more-toggle>More</button>"
        f"<div class=\"slug-more-copy\" data-more-copy hidden><p>{more_text}</p></div>"
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


def render_tab_panel(page: dict[str, Any], tab: dict[str, Any], sessions: list[dict[str, Any]], *, active: bool, group_mode: bool) -> str:
    panel_class = "tab-panel active" if active else "tab-panel"
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
<section class="{panel_class}" id="{escape(tab['id'], quote=True)}" data-banner="{full_schedule_data}">
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

    popular_sessions = sort_by_momentum([session for session in sessions if session_enrolled_count(session) >= 1])[:POPULAR_LIMIT]
    highlighted_keys = {
        str(session.get("session_id") or session.get("registration_url") or "")
        for session in popular_sessions
    }
    remaining_sessions = [
        session
        for session in sort_by_start(sessions)
        if str(session.get("session_id") or session.get("registration_url") or "") not in highlighted_keys
    ]

    section_html: list[str] = []
    if popular_sessions:
        section_html.append(
            render_inventory_section(
                "Popular upcoming classes",
                "Selected upcoming class times with active registrations.",
                popular_sessions,
                group_mode=group_mode,
                limit=POPULAR_LIMIT,
                section_class="slug-popular-section",
            )
        )

    if remaining_sessions:
        section_html.append(
            render_inventory_section(
                "Next available classes",
                "More selected class times to help you compare dates.",
                remaining_sessions,
                group_mode=group_mode,
                limit=DATE_LIMIT,
                section_class="slug-scheduled-section",
            )
        )
    elif not popular_sessions:
        section_html.append(render_empty_state(page, tab, group_mode=group_mode))

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
    escape_hatch_html = (
        f"""
<section class="slug-escape-hatch">
  <div class="slug-escape-copy">
    <strong>Need a different date or time?</strong>
    <span>These are selected upcoming classes. We have more dates, times, and locations available on the full schedule.</span>
  </div>
  <a class="button primary slug-full-schedule-button" href="{escape(tab['full_schedule_url'], quote=True)}">See all {escape(tab['label'])} dates</a>
</section>
""".strip()
        if not group_mode
        else ""
    )

    return f"""
<section class="{panel_class}" id="{escape(tab['id'], quote=True)}" data-banner="{full_schedule_data}">
  <div class="slug-panel-card">
    <div class="slug-panel-head">
      <div>
        <div class="slug-panel-kicker">{escape(inventory_label)}</div>
        <h2>{escape(tab['label'])}</h2>
        {render_panel_description(tab)}
      </div>
    </div>
    {' '.join(section_html)}
    {flexible_html}
    {escape_hatch_html}
  </div>
</section>
""".strip()


def render_hero_image(page: dict[str, Any]) -> str:
    hero_image = str(page.get("hero_image") or "").strip()
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
    classes_href = f"#slug-tabs-{escape(page['slug'], quote=True)}"
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
    body = "".join(f"<p>{escape(line)}</p>" for line in EMERGENCY_ALERT_LINES)
    return f"""
  <section class="slug-emergency-alert" role="status" aria-live="polite">
    <h2>{escape(EMERGENCY_ALERT_TITLE)}</h2>
    {body}
  </section>
""".strip()


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


def render_brand_bar() -> str:
    return """
<header class="site-brand-bar">
  <a class="site-brand-link" href="/index.html" aria-label="910CPR home">
    <img class="site-brand-logo" src="/images/logo.png" alt="910CPR logo" loading="eager" onerror="this.src='/images/910CPR_wave.jpg';this.onerror=null;">
    <span class="site-brand-wordmark">910CPR</span>
  </a>
</header>
""".strip()


def render_page(page: dict[str, Any], sessions: list[dict[str, Any]], banner_library: dict[str, dict[str, Any]]) -> str:
    group_mode = bool(page.get("group_mode"))
    now = datetime.now(TZ)
    tabs = page.get("tabs", [])
    first_tab = tabs[0]

    visible_tabs: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for tab in tabs:
        matched = []
        for session in sessions:
            enriched = enrich_session_for_page(session, page, tab, now=now)
            if enriched:
                matched.append(enriched)
        matched = sort_sessions(matched)
        if matched:
            if page.get("slug") == "heartsaver":
                display = heartsaver_tab_display(tab, matched)
                tab = {**tab, **display}
            visible_tabs.append((tab, matched))

    buttons: list[str] = []
    panels: list[str] = []

    for index, (tab, matched) in enumerate(visible_tabs):
        buttons.append(render_tab_button(tab, active=index == 0))
        panels.append(render_tab_panel(page, tab, matched, active=index == 0, group_mode=group_mode))

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
<link rel="canonical" href="https://www.910cpr.com/{escape(page['slug'])}">
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
<script src="/assets/hub-ui.js"></script>
<script src="/assets/live-sessions.js"></script>
<script src="/assets/session-expiry.js"></script>
<script src="/assets/hybrid-inventory.js"></script>
<script>
document.addEventListener("DOMContentLoaded", function () {{
  document.querySelectorAll("[data-more-toggle]").forEach(function (button) {{
    button.addEventListener("click", function () {{
      var wrap = button.closest(".slug-panel-description");
      if (!wrap) return;
      var more = wrap.querySelector("[data-more-copy]");
      if (!more) return;
      var hidden = more.hasAttribute("hidden");
      if (hidden) {{
        more.removeAttribute("hidden");
        button.textContent = "Less";
      }} else {{
        more.setAttribute("hidden", "");
        button.textContent = "More";
      }}
    }});
  }});
}});
</script>
</body>
</html>"""


def build() -> None:
    reporter = BuildStatusReporter("build_slug_hubs")
    reporter.waiting(total=0)
    manifest_payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if isinstance(manifest_payload, dict):
        manifest = manifest_payload.get("pages", [])
        banner_library = manifest_payload.get("guidance_banners", {})
    else:
        manifest = manifest_payload
        banner_library = {}

    schedule = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    sessions = schedule.get("sessions", [])
    now = datetime.now(TZ)

    reporter.start(total=len(manifest))
    last_output: Path | None = None
    try:
        for index, page in enumerate(manifest, start=1):
            html = render_page(page, sessions, banner_library)
            last_output = OUTPUT_DIR / f"{page['slug']}.html"
            last_output.write_text(html, encoding="utf-8")
            if page.get("slug") == "acls":
                write_acls_runtime_debug(page, sessions, now=now)
            if page.get("slug") == "heartsaver":
                write_heartsaver_runtime_debug(page, sessions, now=now)
            reporter.update(current=index, total=len(manifest), last_output_file=last_output)
            print(f"Wrote {last_output}")
        reporter.done(current=len(manifest), total=len(manifest), last_output_file=last_output)
        write_status_snapshot()
    except Exception:
        reporter.error(last_output_file=last_output)
        raise


if __name__ == "__main__":
    build()
