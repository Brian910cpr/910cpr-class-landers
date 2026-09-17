from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import re
from typing import Any, Iterable


ACTIVE_REGISTRATION_STATUSES = frozenset({"registered", "confirmed", "completed"})


def _text(value: Any) -> str:
    return str(value or "").strip()


def _identity(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", _text(value).casefold()).strip()


def _instant(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(_text(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _external_class_id(row: dict[str, Any]) -> str:
    return _text(row.get("external_class_id") or row.get("class_id") or row.get("session_id"))


def _course_identities(row: dict[str, Any]) -> set[str]:
    values = (
        row.get("external_course_id"), row.get("course_id"), row.get("course_key"),
        row.get("external_course_key"), row.get("course_number"),
    )
    return {normalized for value in values if (normalized := _identity(value))}


def _location(row: dict[str, Any]) -> str:
    return _identity(row.get("location_name") or row.get("location_display") or row.get("location"))


def _instructor(row: dict[str, Any]) -> str:
    return _identity(
        row.get("lead_instructor_name") or row.get("instructor_name") or row.get("instructor")
    )


def _start(row: dict[str, Any]) -> datetime | None:
    return _instant(row.get("start_at") or row.get("starts_at") or row.get("start"))


def _strict_occurrence_match(demand: dict[str, Any], occurrence: dict[str, Any]) -> bool:
    demand_courses = _course_identities(demand)
    occurrence_courses = _course_identities(occurrence)
    if not demand_courses or not occurrence_courses or demand_courses.isdisjoint(occurrence_courses):
        return False
    if _start(demand) != _start(occurrence):
        return False
    if not _location(demand) or _location(demand) != _location(occurrence):
        return False
    demand_instructor = _instructor(demand)
    return not demand_instructor or demand_instructor == _instructor(occurrence)


def resolve_canonical_demand(
    occurrences: Iterable[dict[str, Any]],
    demand_rows: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Attach PII-free canonical demand to schedule occurrences, failing closed.

    Exact external class identity wins. Fallback identity is deliberately strict and
    is accepted only when exactly one occurrence matches a durable Session.
    """
    resolved = [deepcopy(row) for row in occurrences]
    exact: dict[str, list[int]] = {}
    for index, occurrence in enumerate(resolved):
        if external_id := _external_class_id(occurrence):
            exact.setdefault(external_id, []).append(index)

    audits: list[dict[str, Any]] = []
    claimed: dict[int, str] = {}
    for demand in demand_rows:
        canonical_id = _text(demand.get("canonical_session_id") or demand.get("session_id") or demand.get("id"))
        external_id = _text(demand.get("external_class_id"))
        match_basis = "external_class_id"
        candidates = exact.get(external_id, []) if external_id else []
        if not external_id:
            match_basis = "strict_occurrence_identity"
            candidates = [index for index, row in enumerate(resolved) if _strict_occurrence_match(demand, row)]

        if len(candidates) != 1:
            audits.append({
                "canonical_session_id": canonical_id,
                "external_class_id": external_id or None,
                "result": "ambiguous" if candidates else "unmatched",
                "match_basis": match_basis,
                "candidate_count": len(candidates),
            })
            continue

        index = candidates[0]
        if index in claimed and claimed[index] != canonical_id:
            audits.append({
                "canonical_session_id": canonical_id,
                "external_class_id": external_id or None,
                "result": "ambiguous",
                "match_basis": match_basis,
                "candidate_count": 1,
                "reason": "occurrence_already_claimed_by_another_canonical_session",
            })
            continue

        claimed[index] = canonical_id
        count = max(0, int(demand.get("active_registration_count") or 0))
        resolved[index].update({
            "canonical_session_id": canonical_id,
            "active_registration_count": count,
            "demand_basis": _text(demand.get("demand_basis")) or "canonical_active_registrations",
            "demand_match_basis": match_basis,
        })
        audits.append({
            "canonical_session_id": canonical_id,
            "external_class_id": external_id or None,
            "result": "matched",
            "match_basis": match_basis,
            "candidate_count": 1,
        })
    return resolved, audits
