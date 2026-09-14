"""Stable crawlable class links derived from canonical public Anchor sessions."""

from __future__ import annotations

import html
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from scripts.public_class_eligibility import session_has_public_class_location


MIN_DAYS_AHEAD = 14
MAX_DAYS_AHEAD = 21
DEFAULT_LIMIT = 6


def parse_datetime(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.astimezone()


def verified_enrollware_url(value: Any) -> bool:
    try:
        parsed = urlparse(str(value or "").strip())
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (host == "enrollware.com" or host.endswith(".enrollware.com"))


def is_public_anchor(session: dict[str, Any]) -> bool:
    status = str(session.get("session_status") or "active").strip().lower()
    registration_status = str(session.get("registration_status") or "open").strip().lower()
    return (
        str(session.get("schedule_role") or "").strip().lower() == "anchor"
        and session.get("external_publication_eligible") is True
        and session.get("public_direct_booking") is not False
        and status not in {"cancelled", "canceled", "deleted", "draft", "tentative", "proposed"}
        and registration_status not in {"closed", "full", "cancelled", "canceled", "deleted"}
        and session.get("is_full") is not True
        and session_has_public_class_location(session)
        and verified_enrollware_url(session.get("registration_url"))
    )


def select_stable_sessions(
    sessions: list[dict[str, Any]],
    course_ids: list[str],
    *,
    now: datetime,
    limit: int = DEFAULT_LIMIT,
) -> list[dict[str, Any]]:
    allowed = {str(value).strip() for value in course_ids if str(value).strip()}
    start_date = (now + timedelta(days=MIN_DAYS_AHEAD)).date()
    end_date = (now + timedelta(days=MAX_DAYS_AHEAD)).date()
    grouped: dict[str, list[dict[str, Any]]] = {course_id: [] for course_id in allowed}

    for session in sessions:
        course_id = str(session.get("course_id") or session.get("course_number") or "").strip()
        start = parse_datetime(session.get("start_at"))
        session_id = str(session.get("session_id") or "").strip()
        if course_id not in allowed or not session_id or not start:
            continue
        if start.date() < start_date or start.date() > end_date or not is_public_anchor(session):
            continue
        copy = dict(session)
        copy["_projection_start"] = start
        grouped[course_id].append(copy)

    for rows in grouped.values():
        rows.sort(key=lambda row: row["_projection_start"])

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    active = [grouped[course_id] for course_id in course_ids if grouped.get(str(course_id))]
    while active and len(selected) < limit:
        remaining: list[list[dict[str, Any]]] = []
        for rows in active:
            while rows and str(rows[0].get("session_id")) in seen:
                rows.pop(0)
            if not rows:
                continue
            row = rows.pop(0)
            seen.add(str(row.get("session_id")))
            selected.append(row)
            if rows:
                remaining.append(rows)
            if len(selected) >= limit:
                break
        active = remaining
    return sorted(selected, key=lambda row: row["_projection_start"])


def render_projection(sessions: list[dict[str, Any]], *, family: str) -> str:
    if not sessions:
        return ""
    items: list[str] = []
    for session in sessions:
        start = session.get("_projection_start") or parse_datetime(session.get("start_at"))
        if not start:
            continue
        session_id = html.escape(str(session.get("session_id") or ""), quote=True)
        course_name = html.escape(str(session.get("mapped_clean_title") or session.get("course_name") or family))
        location = str(session.get("location_display") or session.get("location_name") or "Wilmington, NC")
        location = html.escape(location.replace("::", "").strip(" ;"))
        when = html.escape(start.strftime("%A, %B %d at %I:%M %p").replace(" 0", " "))
        items.append(
            '<li class="stable-class-item">'
            f'<a href="/classes/{session_id}.html"><strong>{course_name}</strong><span>{when} · {location}</span></a>'
            '</li>'
        )
    if not items:
        return ""
    return f"""
    <section class="stable-class-projection" aria-labelledby="stable-class-title">
      <div><p class="stable-class-kicker">Planning two to three weeks ahead</p>
      <h2 id="stable-class-title">Confirmed upcoming {html.escape(family)} classes</h2>
      <p class="muted">These confirmed public classes sit in a steadier planning window. For today and the next two weeks, use the current calendar above.</p></div>
      <ul class="stable-class-list">{''.join(items)}</ul>
    </section>
""".rstrip()


def render_from_schedule(
    schedule_path: Path,
    *,
    course_ids: list[str],
    family: str,
    now: datetime,
) -> str:
    try:
        payload = json.loads(schedule_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return ""
    sessions = payload.get("sessions", []) if isinstance(payload, dict) else []
    if not isinstance(sessions, list):
        return ""
    return render_projection(select_stable_sessions(sessions, course_ids, now=now), family=family)
