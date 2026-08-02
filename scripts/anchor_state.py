from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
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
    for key in ("registered_count", "enrolled_count", "seated_count", "participant_count"):
        value = session.get(key)
        if value is None:
            continue
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            continue
    # A session imported from Enrollware is a real seated class even when the
    # public feed omits counts. The caller may explicitly set confirmed_seated.
    return 1 if session.get("confirmed_seated") is True else 0


def _course_id(session: dict[str, Any]) -> str:
    return _text(session.get("course_id") or session.get("course_number"))


def _session_id(session: dict[str, Any]) -> str:
    return _text(session.get("session_id") or session.get("id"))


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
    schedule_role: str = "anchor"
    schedule_symbol: str = ANCHOR_SYMBOL
    promotion_reason: str = "first_confirmed_seat"
    landing_page_required: bool = True
    external_publication_eligible: bool = True


def promote_seated_sessions(sessions: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return explicit anchor records for every real session with a seat.

    This intentionally does not consult speculative ``anchor_eligible`` rules.
    Those rules may decide whether an empty availability block can originate an
    offer. They must never prevent a real seated class from becoming an anchor.
    """
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
