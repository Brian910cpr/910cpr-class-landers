from __future__ import annotations

import json
import re
from datetime import datetime
from html import escape, unescape
from pathlib import Path
from typing import Any
from urllib.parse import quote

from scripts.build_status import BuildStatusReporter
from supervisor.status_snapshot import write_status_snapshot
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "config" / "slug_hubs.json"
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
OUTPUT_DIR = ROOT / "docs"
STATE_DIR = ROOT / "data" / "state"
RUNTIME_DIR = ROOT / "data" / "runtime"
SESSIONS_CURRENT_PATH = ROOT / "data" / "sessions_current.json"
TZ = ZoneInfo("America/New_York")
DATE_LIMIT = 12
EMPTY_FALLBACK_TITLE = "No upcoming dates are currently listed for this course."
EMPTY_FALLBACK_BODY = "Please contact us and we'll help you find the right class."


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


def normalize_match_text(value: str | None) -> str:
    text = normalize_space(value).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


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
    location = clean_location(session.get("location_display") or session.get("location_name"))
    title = normalize_space(session.get("course_name"))
    register_url = escape(session.get("registration_url") or "#", quote=True)
    session_start = escape(start_dt.isoformat() if start_dt else "", quote=True)

    action_label = "See Public Class" if group_mode else "Register"
    action_hint = "Preview the closest public option" if group_mode else "Secure this class time"

    return f"""
<article class="slug-pill" data-session-start="{session_start}">
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
    </div>
    <div class="slug-pill-subtitle">{escape(title)}</div>
  </div>
  <div class="slug-pill-actions">
    <div class="slug-pill-hint">{escape(action_hint)}</div>
    <a class="button small primary" href="{register_url}">{action_label}</a>
  </div>
</article>
""".strip()


def render_empty_state(*, group_mode: bool) -> str:
    return (
        "<div class='slug-empty'>"
        f"<strong>{EMPTY_FALLBACK_TITLE}</strong>"
        f"<p>{EMPTY_FALLBACK_BODY}</p>"
        "</div>"
    )


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


def render_tab_panel(tab: dict[str, Any], sessions: list[dict[str, Any]], *, active: bool, group_mode: bool) -> str:
    panel_class = "tab-panel active" if active else "tab-panel"
    cards = "\n".join(render_session_card(session, group_mode=group_mode) for session in sessions[:DATE_LIMIT])
    if not cards:
        cards = render_empty_state(group_mode=group_mode)

    full_schedule_url = escape(tab["full_schedule_url"], quote=True)
    full_schedule_data = escape(
        json.dumps(
            {
                "url": tab["full_schedule_url"],
                "label": tab["full_schedule_label"],
            }
        ),
        quote=True,
    )
    inventory_label = f"{len(sessions)} upcoming option" + ("" if len(sessions) == 1 else "s")

    return f"""
<section class="{panel_class}" id="{escape(tab['id'], quote=True)}" data-banner="{full_schedule_data}">
  <div class="slug-panel-card">
    <div class="slug-panel-head">
      <div>
        <div class="slug-panel-kicker">{escape(inventory_label)}</div>
        <h2>{escape(tab['label'])}</h2>
        <p class="slug-panel-copy">{escape(tab['description'])}</p>
      </div>
    </div>
    <div class="slug-pill-list">
      {cards}
    </div>
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

    primary_href = first_tab["full_schedule_url"]
    primary_label = first_tab["primary_cta_label"]
    secondary_href = first_tab["full_schedule_url"]
    secondary_label = first_tab["full_schedule_label"]
    return (
        "<div class=\"slug-hero-actions\">"
        f"<a class=\"button primary\" href=\"{escape(primary_href, quote=True)}\">{escape(primary_label)}</a>"
        f"<a class=\"button secondary\" href=\"{escape(secondary_href, quote=True)}\">{escape(secondary_label)}</a>"
        "</div>"
    )


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


def render_page(page: dict[str, Any], sessions: list[dict[str, Any]]) -> str:
    group_mode = bool(page.get("group_mode"))
    now = datetime.now(TZ)
    tabs = page.get("tabs", [])
    first_tab = tabs[0]

    visible_tabs: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for tab in tabs:
        matched = [
            session
            for session in sessions
            if matches_tab(session, tab, page_slug=str(page.get("slug") or "")) and is_future_session(session, now=now)
        ]
        matched = sort_sessions(matched)
        if matched:
            visible_tabs.append((tab, matched))

    buttons: list[str] = []
    panels: list[str] = []

    for index, (tab, matched) in enumerate(visible_tabs):
        buttons.append(render_tab_button(tab, active=index == 0))
        panels.append(render_tab_panel(tab, matched, active=index == 0, group_mode=group_mode))

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
  {tabs_html}
  {render_banner(page, first_tab)}
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
</body>
</html>"""


def build() -> None:
    reporter = BuildStatusReporter("build_slug_hubs")
    reporter.waiting(total=0)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    schedule = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    sessions = schedule.get("sessions", [])
    now = datetime.now(TZ)

    reporter.start(total=len(manifest))
    last_output: Path | None = None
    try:
        for index, page in enumerate(manifest, start=1):
            html = render_page(page, sessions)
            last_output = OUTPUT_DIR / f"{page['slug']}.html"
            last_output.write_text(html, encoding="utf-8")
            if page.get("slug") == "acls":
                write_acls_runtime_debug(page, sessions, now=now)
            reporter.update(current=index, total=len(manifest), last_output_file=last_output)
            print(f"Wrote {last_output}")
        reporter.done(current=len(manifest), total=len(manifest), last_output_file=last_output)
        write_status_snapshot()
    except Exception:
        reporter.error(last_output_file=last_output)
        raise


if __name__ == "__main__":
    build()
