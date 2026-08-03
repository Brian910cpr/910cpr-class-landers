from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import re
from typing import Any, Iterable


ANCHOR_SYMBOL = "⚓"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(_text(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _count(session: dict[str, Any]) -> int:
    for key in (
        "registered_count",
        "registration_count",
        "enrolled_count",
        "seated_count",
        "participant_count",
        "students_registered",
        "students_enrolled",
        "seats_taken",
    ):
        value = session.get(key)
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            return len(value)
        match = re.match(r"\s*(\d+)\s*(?:/|of\b)?", str(value), re.I)
        if match:
            return max(0, int(match.group(1)))
    for key in ("participants", "students", "registrations"):
        value = session.get(key)
        if isinstance(value, list):
            return len(value)
    if session.get("confirmed_seated") is True or session.get("has_students") is True:
        return 1
    return 0


def _course_id(session: dict[str, Any]) -> str:
    return _text(session.get("course_id") or session.get("course_number"))


def _session_id(session: dict[str, Any]) -> str:
    return _text(session.get("session_id") or session.get("id") or session.get("class_id"))


def _location(session: dict[str, Any]) -> str:
    return _text(session.get("location_name") or session.get("location_display") or session.get("location"))


def _instructor(session: dict[str, Any]) -> str:
    return _text(session.get("lead_instructor_name") or session.get("instructor"))


def cluster_id(session: dict[str, Any]) -> str:
    start = _dt(session.get("start_at") or session.get("start"))
    date_part = start.strftime("%Y-%m-%d") if start else "unknown-date"
    time_part = start.strftime("%H%M") if start else "unknown-time"
    location = "-".join(_location(session).lower().split()) or "unknown-location"
    instructor = "-".join(_instructor(session).lower().split()) or "unassigned"
    return f"{date_part}-{location}-{instructor}-{time_part}"


@dataclass(frozen=True)
class Anchor:
    session_id: str
    course_id: str
    start_at: str
    end_at: str
    location: str
    instructor: str
    registered_count: int
    cluster_id: str
    registration_url: str = ""
    schedule_role: str = "anchor"
    schedule_symbol: str = ANCHOR_SYMBOL
    promotion_reason: str = "first_confirmed_seat"
    landing_page_required: bool = True
    external_publication_eligible: bool = True


def promote_seated_sessions(sessions: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return explicit anchor records for every real session with a seat."""
    anchors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for session in sessions:
        session_id = _session_id(session)
        start = _dt(session.get("start_at") or session.get("start"))
        end = _dt(session.get("end_at") or session.get("end"))
        count = _count(session)
        if not session_id or not start or not end or count < 1:
            continue
        if session_id in seen:
            continue
        seen.add(session_id)
        anchors.append(asdict(Anchor(
            session_id=session_id,
            course_id=_course_id(session),
            start_at=start.isoformat(),
            end_at=end.isoformat(),
            location=_location(session),
            instructor=_instructor(session),
            registered_count=count,
            cluster_id=cluster_id(session),
            registration_url=_text(session.get("registration_url") or session.get("enrollment_url")),
        )))
    anchors.sort(key=lambda item: (item["start_at"], item["session_id"]))
    return anchors


def same_course_anchor(
    *,
    course_id: str,
    date: str,
    location: str,
    anchors: Iterable[dict[str, Any]],
) -> dict[str, Any] | None:
    """Select the earliest compatible seated class before creating a new time."""
    matches = []
    for anchor in anchors:
        start = _dt(anchor.get("start_at"))
        if not start or start.date().isoformat() != date:
            continue
        if _text(anchor.get("course_id")) != _text(course_id):
            continue
        if _text(anchor.get("location")) != _text(location):
            continue
        matches.append(anchor)
    return min(matches, key=lambda item: item["start_at"]) if matches else None


def annotate_offer(
    offer: dict[str, Any],
    *,
    attached_to: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Add stable scheduling-role metadata consumed by renderers and publishers."""
    result = dict(offer)
    if attached_to:
        result.update({
            "schedule_role": "barnacle",
            "schedule_symbol": "",
            "cluster_id": attached_to.get("cluster_id"),
            "attached_to_session_id": attached_to.get("session_id"),
            "landing_page_required": False,
            "external_publication_eligible": False,
        })
    else:
        result.setdefault("schedule_role", "standalone_offer")
        result.setdefault("schedule_symbol", "")
        result.setdefault("landing_page_required", False)
        result.setdefault("external_publication_eligible", False)
    return result


def repeat_scope_key(course_id: str, policy: dict[str, Any]) -> tuple[str, int]:
    """Return the configured repeat scope and start-to-start delay for a course."""
    cid = _text(course_id)
    exact = policy.get("exact_courses", {}).get(cid, {})
    if exact:
        return f"course:{cid}", max(0, int(exact.get("repeat_delay_minutes") or 0))
    for family_id, family in policy.get("families", {}).items():
        if cid in {_text(item) for item in family.get("course_ids", [])}:
            return f"family:{family_id}", max(0, int(family.get("repeat_delay_minutes") or 0))
    default = max(0, int(policy.get("default_repeat_delay_minutes") or 0))
    return f"course:{cid}", default


def in_repeat_bubble(start: datetime, anchor_start: datetime, delay_minutes: int) -> bool:
    """Repeat delays are inclusive, bidirectional, and measured start-to-start."""
    if (start.tzinfo is None) != (anchor_start.tzinfo is None):
        start = start.replace(tzinfo=None)
        anchor_start = anchor_start.replace(tzinfo=None)
    return anchor_start - timedelta(minutes=delay_minutes) <= start <= anchor_start + timedelta(minutes=delay_minutes)
