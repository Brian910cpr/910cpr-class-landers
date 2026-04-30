from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


TZ = ZoneInfo("America/New_York")
ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com"
APPOINTMENT_ENDPOINT = f"{ENROLLWARE_BASE}/reg/appointment.aspx/GetAvailableAppointmentTimes"


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def session_enrolled_count(session: dict[str, Any]) -> int:
    raw = session.get("enrolled_count", session.get("registered_count", 0))
    try:
        return max(0, int(raw or 0))
    except (TypeError, ValueError):
        return 0


def session_registration_url(session: dict[str, Any]) -> str:
    return str(session.get("registration_url") or session.get("register_url") or "").strip()


def is_real_scheduled_inventory(session: dict[str, Any]) -> bool:
    return "enroll?id=" in session_registration_url(session)


def extract_schedule_course_id(url: str | None) -> str | None:
    text = str(url or "").strip()
    match = re.search(r"#ct(\d+)", text)
    if match:
        return match.group(1)
    return None


def build_appointment_page_url(location_id: str, course_id: str) -> str:
    return f"{ENROLLWARE_BASE}/reg/appointment.aspx?locationId={location_id}&courseId={course_id}"


def seed_dates_from_sessions(sessions: list[dict[str, Any]], *, limit: int = 5) -> list[str]:
    seen: set[str] = set()
    seeds: list[str] = []
    for session in sessions:
        dt = parse_dt(str(session.get("start_at") or ""))
        if not dt:
            continue
        token = dt.strftime("%m%d%y")
        if token in seen:
            continue
        seen.add(token)
        seeds.append(token)
        if len(seeds) >= limit:
            break
    return seeds


def sort_by_momentum(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(session: dict[str, Any]) -> tuple[int, str, str]:
        dt = parse_dt(str(session.get("start_at") or ""))
        return (
            -session_enrolled_count(session),
            dt.isoformat() if dt else "9999-12-31T23:59:59-05:00",
            str(session.get("session_id") or ""),
        )

    return sorted(sessions, key=key)


def sort_by_start(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(session: dict[str, Any]) -> tuple[str, str]:
        dt = parse_dt(str(session.get("start_at") or ""))
        return (
            dt.isoformat() if dt else "9999-12-31T23:59:59-05:00",
            str(session.get("session_id") or ""),
        )

    return sorted(sessions, key=key)

