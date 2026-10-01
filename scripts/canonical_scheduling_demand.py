from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any, Iterable
from zoneinfo import ZoneInfo


ACTIVE_REGISTRATION_STATUSES = frozenset({"registered", "confirmed", "completed"})


def load_publication_demand(root: Path) -> dict[str, Any]:
    from scripts.fetch_canonical_scheduling_demand import validate_payload
    path = root / "data/runtime/canonical_scheduling_demand.json"
    if not path.exists():
        raise ValueError("Fresh canonical scheduling demand is required before publication")
    payload = validate_payload(json.loads(path.read_text(encoding="utf-8")))
    if "non_session_sources" not in payload:
        raise ValueError("Canonical non-session classification is required before publication")
    return payload


def exclude_non_session_sources(occurrences: Iterable[dict[str, Any]], payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Use only reviewed canonical classifications, never infer from zero demand.

    The endpoint checks the complete reviewed source identity. A different start
    in the current projection must stop publication for reconciliation.
    """
    excluded = {str(row["external_class_id"]): row for row in payload.get("non_session_sources", [])}
    kept, removed = [], []
    for row in occurrences:
        external_id = _text(row.get("external_session_id")) or _external_class_id(row)
        decision = excluded.get(external_id)
        if decision is None:
            kept.append(row)
            continue
        start = _start(row) or _start(row.get("timing", {}))
        if start is None or start != _start(decision):
            raise ValueError(f"Non-session source identity changed: {external_id}; reconciliation required")
        removed.append(external_id)
    return kept, removed


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
    if _start(demand) is None or _start(demand) != _start(occurrence):
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
    demand_rows = list(demand_rows)
    source_rows = [deepcopy(row) for row in occurrences]
    for demand in demand_rows:
        external_id = _text(demand.get("external_class_id"))
        native_id = re.fullmatch(r"lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", external_id)
        if not (native_id and demand.get("source") == "landerware_event"
                and demand.get("registration_backend") == "landerware"
                and demand.get("session_status") in ("scheduled", "active")
                and demand.get("visibility") == "public"
                and demand.get("registration_status") == "open"
                and demand.get("workspace_projection_status") == "current"
                and demand.get("count_available") is True):
            continue
        if any(_external_class_id(row) == external_id for row in source_rows):
            continue
        start, end = _start(demand), _instant(demand.get("end_at"))
        if not start or not end or end <= start or not demand.get("external_course_id"):
            raise ValueError("Native public occurrence has invalid timing or course")
        source_rows.append({
            "session_id": external_id, "external_class_id": external_id,
            "course_id": demand["external_course_id"], "course_name": demand.get("course_name"),
            "start_at": demand["start_at"], "end_at": demand["end_at"],
            "location_name": demand.get("location_name"),
            "lead_instructor_name": demand.get("lead_instructor_name"),
            "source": "landerware_event", "session_status": demand["session_status"],
            "registration_status": "open", "public_direct_booking": True,
            "registration_backend": "landerware",
            "registration_url": "https://www.910cpr.com/register/?session=" + external_id,
        })
    resolved = source_rows
    exact: dict[str, list[int]] = {}
    for index, occurrence in enumerate(resolved):
        # Published projections are inputs to later refreshes, never demand truth.
        for key in ("canonical_session_id", "demand_match_basis", "demand_status"):
            occurrence.pop(key, None)
        occurrence.update(active_registration_count=None, count_available=False, demand_basis="unknown", demand_status="missing_canonical_session")
        if external_id := _external_class_id(occurrence):
            exact.setdefault(external_id, []).append(index)

    audits: list[dict[str, Any]] = []
    claimed: dict[int, str] = {}
    conflicted: set[int] = set()
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
        if index in claimed:
            conflicted.add(index)
            resolved[index].update(active_registration_count=None, count_available=False, demand_basis="unknown")
            resolved[index].pop("canonical_session_id", None)
            resolved[index].pop("demand_match_basis", None)
            resolved[index]["demand_status"] = "ambiguous"
            for prior in audits:
                if prior.get("canonical_session_id") == claimed[index]:
                    prior["result"] = "ambiguous"
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
        if demand.get("visibility") == "private" or demand.get("registration_status") == "closed":
            resolved[index]["public_direct_booking"] = False
            resolved[index]["registration_status"] = "closed"
            resolved[index]["registration_status_source"] = "canonical_class_sessions"
        # External identity survives a reschedule; it does not prove that the
        # canonical occurrence still has the current source's start time.
        if _start(demand) != _start(resolved[index]):
            resolved[index].update(
                canonical_session_id=canonical_id, demand_status="stale_anchor",
                canonical_start_at=demand.get("start_at"),
            )
            audits.append({
                "canonical_session_id": canonical_id, "external_class_id": external_id,
                "result": "stale_anchor", "match_basis": match_basis,
                "source_start_at": resolved[index].get("start_at"),
                "canonical_start_at": demand.get("start_at"),
            })
            continue
        count = demand.get("active_registration_count")
        known = isinstance(count, int) and not isinstance(count, bool) and count >= 0 and demand.get("count_available") is not False
        if index in conflicted:
            continue
        resolved[index].update({
            "canonical_session_id": canonical_id,
            "active_registration_count": count if known else None,
            "count_available": known,
            "demand_basis": "canonical_active_registrations" if known else "unknown",
            "demand_status": "current" if known else _text(demand.get("demand_status")) or "unknown",
            "demand_match_basis": match_basis,
            "consumption_start_at": demand.get("consumption_start_at"),
            "consumption_end_at": demand.get("consumption_end_at"),
            "workspace_projection_status": demand.get("workspace_projection_status"),
            "source_observed_at": demand.get("source_observed_at"),
        })
        audits.append({
            "canonical_session_id": canonical_id,
            "external_class_id": external_id or None,
            "result": "matched" if known else "unknown",
            "match_basis": match_basis,
            "candidate_count": 1,
        })
    return resolved, audits


def reconciliation_issues(occurrences: list[dict[str, Any]], demand_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Publish safe diagnostics and close synthesis on BOTH sides of a move."""
    resolved, _ = resolve_canonical_demand(occurrences, demand_rows)
    issues = []
    for row in resolved:
        status = row.get("demand_status")
        if status == "current":
            continue
        code = {"stale_anchor": "STALE_ANCHOR", "missing_canonical_session": "MISSING_CANONICAL_SESSION",
                "external_reconciliation_required": "MISSING_ROSTER",
                "stale_reconciliation": "STALE_ROSTER"}.get(status, "RECONCILIATION_REQUIRED")
        dates = set()
        for value in (row.get("start_at"), row.get("canonical_start_at")):
            if instant := _instant(value):
                dates.add(instant.astimezone(ZoneInfo("America/New_York")).date().isoformat())
        for day in sorted(dates):
            issues.append({"date": day, "code": code, "externalClassId": _external_class_id(row),
                           "sourceStart": row.get("start_at"), "canonicalStart": row.get("canonical_start_at"),
                           "reason": status, "blocksSynthesis": True})
    for row in demand_rows:
        if (row.get("external_class_id") and row.get("count_available") is False
                and row.get("session_status") in ("scheduled", "active")
                and not any(_external_class_id(item) == row["external_class_id"] for item in resolved)):
            start = _start(row)
            if start:
                issues.append({"date": start.astimezone(ZoneInfo("America/New_York")).date().isoformat(),
                               "code": "STALE_ROSTER" if row.get("demand_status") == "stale_reconciliation" else "MISSING_ROSTER",
                               "externalClassId": row["external_class_id"],
                               "canonicalSessionId": row.get("canonical_session_id"),
                               "reason": row.get("demand_status") or "unknown", "blocksSynthesis": True})
        if row.get("workspace_projection_status") not in (None, "current"):
            start = _start(row)
            if start:
                issues.append({"date": start.astimezone(ZoneInfo("America/New_York")).date().isoformat(),
                               "code": "MISSING_SESSION_PROJECTION" if row["workspace_projection_status"] == "missing" else "STALE_SESSION_PROJECTION",
                               "externalClassId": row.get("external_class_id"),
                               "canonicalSessionId": row.get("canonical_session_id"),
                               "reason": row["workspace_projection_status"], "blocksSynthesis": True})
    return issues
