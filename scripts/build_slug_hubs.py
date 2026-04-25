from __future__ import annotations

import json
import re
from datetime import datetime
from html import escape, unescape
from pathlib import Path
from typing import Any
from urllib.parse import quote

from scripts.build_status import BuildStatusReporter
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "config" / "slug_hubs.json"
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
OUTPUT_DIR = ROOT / "docs"
TZ = ZoneInfo("America/New_York")
DATE_LIMIT = 12


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


def matches_tab(session: dict[str, Any], tab: dict[str, Any]) -> bool:
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


def sort_sessions(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(session: dict[str, Any]) -> tuple[int, str]:
        dt = parse_dt(session.get("start_at"))
        if dt is None:
            return (1, "9999-12-31T23:59:59")
        return (0, dt.isoformat())

    return sorted(sessions, key=sort_key)


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
    if group_mode:
        return (
            "<div class='slug-empty'>"
            "<strong>Private scheduling is still available.</strong>"
            "<p>No matching public class dates are listed right now, but you can still request this program for your team.</p>"
            "</div>"
        )
    return (
        "<div class='slug-empty'>"
        "<strong>No upcoming dates are listed right now.</strong>"
        "<p>Please check back soon or request help finding a class.</p>"
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
        f"<span class=\"hub-tab-icon\"><img src=\"{icon}\" alt=\"\" loading=\"lazy\" onerror=\"this.parentElement.hidden=true\"></span>"
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
    tabs = page.get("tabs", [])
    first_tab = tabs[0]

    buttons: list[str] = []
    panels: list[str] = []

    for index, tab in enumerate(tabs):
        matched = sort_sessions([session for session in sessions if matches_tab(session, tab)])
        buttons.append(render_tab_button(tab, active=index == 0))
        panels.append(render_tab_panel(tab, matched, active=index == 0, group_mode=group_mode))

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

  <section class="section-box slug-tabs-block" id="slug-tabs-{escape(page['slug'], quote=True)}" data-tabs>
    <div class="tabs hub-tabs">
      {''.join(buttons)}
    </div>
    {''.join(panels)}
  </section>
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

    reporter.start(total=len(manifest))
    last_output: Path | None = None
    try:
        for index, page in enumerate(manifest, start=1):
            html = render_page(page, sessions)
            last_output = OUTPUT_DIR / f"{page['slug']}.html"
            last_output.write_text(html, encoding="utf-8")
            reporter.update(current=index, total=len(manifest), last_output_file=last_output)
            print(f"Wrote {last_output}")
        reporter.done(current=len(manifest), total=len(manifest), last_output_file=last_output)
    except Exception:
        reporter.error(last_output_file=last_output)
        raise


if __name__ == "__main__":
    build()
