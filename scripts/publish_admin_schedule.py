from __future__ import annotations

import json
import html
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SESSIONS_CURRENT = ROOT / "data" / "sessions_current.json"
OUTPUT = ROOT / "docs" / "data" / "admin_schedule.json"
STUDENT_SNAPSHOT = ROOT / "data" / "enrollware_student_snapshot.json"


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


def normalize_session(session: dict[str, Any]) -> dict[str, Any] | None:
    start = value(session, ("start_at",), ("start",), ("timing", "start_at"), ("timing", "start"))
    if not start:
        return None
    end = value(session, ("end_at",), ("end",), ("timing", "end_at"), ("timing", "end"))
    instructor = value(session, ("lead_instructor_name",), ("instructor",), ("staffing", "lead_instructor_name"))
    raw_location = value(session, ("location_name",), ("location_display",), ("location", "location_display"), ("location", "location_name"))
    location = html.unescape(re.sub(r"<[^>]+>", " ", str(raw_location or "")))
    location = re.sub(r"\s+", " ", location).strip() or None
    course = value(
        session,
        ("course_name",),
        ("mapped_clean_title",),
        ("course", "mapped_clean_title"),
        ("course", "course_name_primary_clean"),
    )
    session_id = value(session, ("session_id",), ("class_id",), ("id",))
    instructor_key = str(instructor or "").strip().lower()
    resources = []
    if instructor_key:
        resources.append(f"instructor:{instructor_key.replace(' ', '_')}")
    if location:
        resources.append(f"location:{str(location).strip().lower()}")
    return {
        "session_id": session_id,
        "course_name": course or "Class",
        "start_at": start,
        "end_at": end,
        "lead_instructor_name": instructor,
        "location_name": location,
        "registered_count": value(session, ("registered_count",), ("capacity", "registered_count"), ("capacity", "students_count_raw")) or 0,
        "registration_url": value(session, ("registration_url",), ("commerce", "registration_url"), ("source_keys", "enrollware_ical_url")),
        "source": value(session, ("source",)) or "enrollware_ical",
        "blocking_resources": resources,
    }


def apply_student_snapshot(rows: list[dict[str, Any]], snapshot: Any) -> dict[str, int]:
    from scripts.import_enrollware_student_report import apply_snapshot_to_sessions
    return apply_snapshot_to_sessions(rows, snapshot)


def parse_timestamp(raw: Any) -> datetime | None:
    if raw in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def find_schedule_conflicts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return deterministic hard conflicts for invalid or shared-resource overlaps."""
    conflicts: list[dict[str, Any]] = []
    parsed: list[tuple[dict[str, Any], datetime, datetime]] = []

    for row in rows:
        start = parse_timestamp(row.get("start_at"))
        end = parse_timestamp(row.get("end_at"))
        if not start or not end or end <= start:
            conflicts.append({
                "type": "invalid_time_range",
                "session_ids": [row.get("session_id")],
                "start_at": row.get("start_at"),
                "end_at": row.get("end_at"),
            })
            continue
        parsed.append((row, start, end))

    parsed.sort(key=lambda item: (item[1], str(item[0].get("session_id"))))
    for index, (first, first_start, first_end) in enumerate(parsed):
        first_resources = set(first.get("blocking_resources") or [])
        for second, second_start, second_end in parsed[index + 1:]:
            if second_start >= first_end:
                break
            shared_resources = sorted(first_resources.intersection(second.get("blocking_resources") or []))
            if second_start < first_end and first_start < second_end and shared_resources:
                conflicts.append({
                    "type": "shared_resource_overlap",
                    "session_ids": [first.get("session_id"), second.get("session_id")],
                    "shared_resources": shared_resources,
                    "overlap_start": max(first_start, second_start).isoformat(),
                    "overlap_end": min(first_end, second_end).isoformat(),
                })

    return conflicts


def build_admin_schedule(payload: Any, *, now: datetime | None = None, student_snapshot: Any = None) -> dict[str, Any]:
    rows = payload.get("sessions", []) if isinstance(payload, dict) else []
    normalized = [row for session in rows if isinstance(session, dict) for row in [normalize_session(session)] if row]
    reference = now or datetime.now().astimezone()
    today = reference.date()
    normalized = [
        row for row in normalized
        if datetime.fromisoformat(str(row["start_at"]).replace("Z", "+00:00")).date() >= today
    ]
    normalized.sort(key=lambda row: (str(row.get("start_at")), str(row.get("session_id"))))
    enrollment_counts = apply_student_snapshot(normalized, student_snapshot)
    conflicts = find_schedule_conflicts(normalized)
    brian_rows = [
        row for row in normalized
        if str(row.get("lead_instructor_name") or "").strip().lower() in {"brian", "brian ennis", "b. ennis"}
    ]
    return {
        "schema_version": "1.0",
        "generated_at": reference.isoformat(),
        "purpose": "Sanitized complete Enrollware occupancy for the admin planner; includes non-public locations.",
        "counts": {
            "sessions": len(normalized),
            "brian_resource_blocks": len(brian_rows),
            "hard_conflicts": len(conflicts),
            **enrollment_counts,
        },
        "integrity": {
            "status": "blocked" if conflicts else "ok",
            "hard_conflicts": conflicts,
        },
        "sessions": normalized,
    }


def main() -> int:
    snapshot = read_json(STUDENT_SNAPSHOT) if STUDENT_SNAPSHOT.exists() else None
    payload = build_admin_schedule(read_json(SESSIONS_CURRENT), student_snapshot=snapshot)
    conflicts = payload["integrity"]["hard_conflicts"]
    if conflicts:
        print(f"BLOCKED: refusing to replace the last known-good admin schedule; found {len(conflicts)} hard conflict(s).")
        for conflict in conflicts:
            print(json.dumps(conflict, sort_keys=True))
        return 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Published {payload['counts']['sessions']} admin schedule sessions to {OUTPUT}")
    print(f"Brian resource blocks: {payload['counts']['brian_resource_blocks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
