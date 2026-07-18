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


def build_admin_schedule(payload: Any, *, now: datetime | None = None) -> dict[str, Any]:
    rows = payload.get("sessions", []) if isinstance(payload, dict) else []
    normalized = [row for session in rows if isinstance(session, dict) for row in [normalize_session(session)] if row]
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
        "schema_version": "1.0",
        "generated_at": reference.isoformat(),
        "purpose": "Sanitized complete Enrollware occupancy for the admin planner; includes non-public locations.",
        "counts": {
            "sessions": len(normalized),
            "brian_resource_blocks": len(brian_rows),
        },
        "sessions": normalized,
    }


def main() -> int:
    payload = build_admin_schedule(read_json(SESSIONS_CURRENT))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Published {payload['counts']['sessions']} admin schedule sessions to {OUTPUT}")
    print(f"Brian resource blocks: {payload['counts']['brian_resource_blocks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
