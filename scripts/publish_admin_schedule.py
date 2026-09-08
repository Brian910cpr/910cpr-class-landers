from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SESSIONS_CURRENT = ROOT / "data" / "sessions_current.json"
HOT_SYNC_SNAPSHOT = ROOT / "data" / "private" / "runtime" / "hot_sync_snapshot.json"
OUTPUT = ROOT / "docs" / "data" / "admin_schedule.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def value(record: dict[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        current: Any = record
        for key in path:
            if not isinstance(current, dict):
                current = None
                break
            current = current.get(key)
        if current not in (None, ""):
            return current
    return None


def clean_location(raw_location: Any) -> str | None:
    location = html.unescape(re.sub(r"<[^>]+>", " ", str(raw_location or "")))
    return re.sub(r"\s+", " ", location).strip() or None


def blocking_resources(instructor: Any, location: Any) -> list[str]:
    resources: list[str] = []
    instructor_key = str(instructor or "").strip().lower()
    if instructor_key:
        resources.append(f"instructor:{instructor_key.replace(' ', '_')}")
    if location:
        resources.append(f"location:{str(location).strip().lower()}")
    return resources


def normalize_session(session: dict[str, Any]) -> dict[str, Any] | None:
    start = value(session, ("start_at",), ("start",), ("timing", "start_at"), ("timing", "start"))
    if not start:
        return None
    end = value(session, ("end_at",), ("end",), ("timing", "end_at"), ("timing", "end"))
    instructor = value(session, ("lead_instructor_name",), ("instructor",), ("staffing", "lead_instructor_name"))
    location = clean_location(value(session, ("location_name",), ("location_display",), ("location", "location_display"), ("location", "location_name")))
    course = value(
        session,
        ("course_name",),
        ("mapped_clean_title",),
        ("course", "mapped_clean_title"),
        ("course", "course_name_primary_clean"),
    )
    session_id = value(session, ("session_id",), ("class_id",), ("id",))
    return {
        "session_id": session_id,
        "course_name": course or "Class",
        "start_at": start,
        "end_at": end,
        "lead_instructor_name": instructor,
        "location_name": location,
        "participant_count": None,
        "count_available": False,
        "roster_available": False,
        "count_source": "canonical_session_workspace_required",
        "registration_url": value(session, ("registration_url",), ("commerce", "registration_url"), ("source_keys", "enrollware_ical_url")),
        "source": value(session, ("source",)) or "enrollware_ical",
        "blocking_resources": blocking_resources(instructor, location),
    }


def normalize_hot_sync(record: dict[str, Any]) -> dict[str, Any] | None:
    status = str(record.get("status") or "").strip().lower()
    if status not in {"committed", "scheduled", "active"}:
        return None
    # Legacy manual HOT_SYNC records can be absorbed by Enrollware. Durable
    # class_sessions are already canonical and may not expose this field.
    if status == "committed" and record.get("needs_class_report_absorption") in (False, 0, "0"):
        return None
    start = value(record, ("start",), ("start_time",), ("start_at",))
    if not start:
        return None
    end = value(record, ("end",), ("end_time",), ("end_at",))
    instructor = value(record, ("instructor",), ("lead_instructor_name",))
    location = clean_location(value(record, ("location_name",), ("location",)))
    session_id = value(record, ("id",), ("record_id",), ("session_id",))
    course = value(record, ("course_display_name",), ("course_name",), ("course_key",)) or "Class"
    return {
        "session_id": session_id,
        "course_name": course,
        "start_at": start,
        "end_at": end,
        "lead_instructor_name": instructor,
        "location_name": location,
        "participant_count": None,
        "count_available": False,
        "roster_available": False,
        "count_source": "canonical_session_workspace_required",
        "registration_url": value(record, ("enrollware_enroll_url",), ("registration_url",)),
        "source": value(record, ("source",)) or "hot_sync_manual",
        "blocking_resources": blocking_resources(instructor, location),
        "hot_sync": True,
        "client_name": value(record, ("client_name",)),
        "visibility": value(record, ("visibility",)),
        "external_session_id": value(record, ("enrollware_class_id",), ("external_class_id",), ("external_session_id",)),
        "copied_from_session_id": value(record, ("copied_from_session_id",), ("copied_from_id",), ("source_session_id",)),
    }


def hot_sync_records(snapshot: Any) -> tuple[list[dict[str, Any]], bool, str]:
    if not isinstance(snapshot, dict):
        return [], False, "snapshot_missing_or_invalid"
    available = bool(snapshot.get("available"))
    error = str(snapshot.get("error") or "")
    records = snapshot.get("records", [])
    return ([row for row in records if isinstance(row, dict)] if isinstance(records, list) else []), available, error


def event_identity(row: dict[str, Any]) -> tuple[str, str, str]:
    start = str(row.get("start_at") or "")[:16]
    course = re.sub(r"\W+", "", str(row.get("course_name") or "").lower())
    location = re.sub(r"\W+", "", str(row.get("location_name") or "").lower())
    return start, course, location


def manual_lineage_id(row: dict[str, Any]) -> str:
    """Return the stable HOT_SYNC identity shared by a record and its UI copy."""
    explicit = str(row.get("copied_from_session_id") or "").strip()
    session_id = explicit or str(row.get("session_id") or "").strip()
    while session_id.startswith("manual-copy-"):
        session_id = session_id.removeprefix("manual-copy-")
    return session_id


def merge_hot_sync(enrollware_rows: list[dict[str, Any]], hot_sync_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    enrollware_ids = {str(row.get("session_id")) for row in enrollware_rows if row.get("session_id") is not None}
    identities = {event_identity(row) for row in enrollware_rows}
    merged = list(enrollware_rows)
    added = 0
    seen_manual_lineages: set[str] = set()
    hot_sync_rows = sorted(
        hot_sync_rows,
        key=lambda row: str(row.get("session_id") or "").startswith("manual-copy-"),
    )
    for row in hot_sync_rows:
        lineage_id = manual_lineage_id(row)
        if lineage_id and lineage_id in seen_manual_lineages:
            continue
        external_id = str(row.get("external_session_id") or "").strip()
        if external_id and external_id in enrollware_ids:
            continue
        identity = event_identity(row)
        if identity in identities:
            continue
        merged.append(row)
        if lineage_id:
            seen_manual_lineages.add(lineage_id)
        identities.add(identity)
        added += 1
    return merged, added


def build_admin_schedule(payload: Any, *, now: datetime | None = None, student_snapshot: Any = None, hot_sync_snapshot: Any = None) -> dict[str, Any]:
    rows = payload.get("sessions", []) if isinstance(payload, dict) else []
    normalized = [row for session in rows if isinstance(session, dict) for row in [normalize_session(session)] if row]

    raw_hot_sync, hot_sync_available, hot_sync_error = hot_sync_records(hot_sync_snapshot)
    normalized_hot_sync = [row for record in raw_hot_sync for row in [normalize_hot_sync(record)] if row]
    normalized, hot_sync_added = merge_hot_sync(normalized, normalized_hot_sync)

    reference = now or datetime.now().astimezone()
    today = reference.date()
    normalized = [
        row for row in normalized
        if datetime.fromisoformat(str(row["start_at"]).replace("Z", "+00:00")).date() >= today
    ]
    normalized.sort(key=lambda row: (str(row.get("start_at")), str(row.get("session_id"))))
    brian_rows = [
        row for row in normalized
        if str(row.get("lead_instructor_name") or "").strip().lower() in {"brian", "brian ennis", "b. ennis"}
    ]
    return {
        "schema_version": "1.1",
        "generated_at": reference.isoformat(),
        "purpose": "Sanitized complete LanderWare occupancy for the admin planner; combines Enrollware iCal with committed HOT_SYNC classes.",
        "counts": {
            "sessions": len(normalized),
            "enrollware_sessions": len([row for row in normalized if not row.get("hot_sync")]),
            "hot_sync_records_fetched": len(raw_hot_sync),
            "hot_sync_committed_normalized": len(normalized_hot_sync),
            "hot_sync_sessions_added": hot_sync_added,
            "brian_resource_blocks": len(brian_rows),
            "participant_truth": "canonical_registrations_only",
        },
        "sources": {
            "enrollware_ical": {"available": True},
            "hot_sync": {"available": hot_sync_available, "error": hot_sync_error},
        },
        "sessions": normalized,
    }


def main() -> int:
    hot_sync_snapshot = read_json(HOT_SYNC_SNAPSHOT) if HOT_SYNC_SNAPSHOT.exists() else None
    payload = build_admin_schedule(read_json(SESSIONS_CURRENT), hot_sync_snapshot=hot_sync_snapshot)
    if not payload["sources"]["hot_sync"]["available"]:
        raise RuntimeError(
            "Refusing to publish an incomplete admin schedule without the authoritative "
            f"HOT_SYNC snapshot: {payload['sources']['hot_sync']['error'] or 'unknown error'}"
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Published {payload['counts']['sessions']} admin schedule sessions to {OUTPUT}")
    print(f"Enrollware sessions: {payload['counts']['enrollware_sessions']}")
    print(f"HOT_SYNC sessions added: {payload['counts']['hot_sync_sessions_added']}")
    print(f"Brian resource blocks: {payload['counts']['brian_resource_blocks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
