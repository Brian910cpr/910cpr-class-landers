from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


TZ = ZoneInfo("America/New_York")

VALID_STATES = {
    "FUTURE_ACTIVE",
    "PAST_LIVE",
    "CANCELED_DEPRECATED",
    "INVALID_REMOVE",
}

CANCELED_STATUSES = {
    "cancelled",
    "canceled",
    "deleted",
    "inactive",
    "deprecated",
}

MATERIAL_CONFLICT_FIELDS = (
    "course_id",
    "course_name",
    "start_at",
    "end_at",
    "registration_url",
    "session_status",
)


def now_iso() -> str:
    return datetime.now(TZ).isoformat()


def clean_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_datetime(value: Any) -> datetime | None:
    text = clean_string(value)
    if not text:
        return None

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=TZ)
    return parsed.astimezone(TZ)


def normalize_status(value: Any) -> str:
    text = clean_string(value)
    return text.lower() if text else ""


def get_nested(record: dict[str, Any], *keys: str) -> Any:
    value: Any = record
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def source_sessions(schedule: Any) -> list[dict[str, Any]]:
    if isinstance(schedule, dict) and isinstance(schedule.get("sessions"), list):
        return [item for item in schedule["sessions"] if isinstance(item, dict)]
    if isinstance(schedule, list):
        return [item for item in schedule if isinstance(item, dict)]
    return []


def manifest_sessions(manifest: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(manifest, dict):
        return {}
    sessions = manifest.get("sessions")
    if not isinstance(sessions, dict):
        return {}
    return {
        str(session_id): session
        for session_id, session in sessions.items()
        if isinstance(session, dict)
    }


def extract_session_id(record: dict[str, Any]) -> str | None:
    return clean_string(record.get("session_id"))


def extract_source_status(record: dict[str, Any], fallback: dict[str, Any] | None = None) -> str | None:
    value = (
        record.get("session_status")
        or get_nested(record, "status", "session_status")
        or get_nested(record, "status", "source_status")
    )
    if value is None and fallback:
        value = fallback.get("source_status")
    return clean_string(value)


def extract_last_known(record: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
    previous_known = {}
    if previous and isinstance(previous.get("last_known"), dict):
        previous_known = deepcopy(previous["last_known"])

    current = {
        "course_id": record.get("course_id") or get_nested(record, "course", "course_id"),
        "course_name": record.get("course_name") or get_nested(record, "course", "course_name_primary_clean"),
        "course_number": record.get("course_number") or get_nested(record, "course", "course_number"),
        "start_at": record.get("start_at") or get_nested(record, "timing", "start_at"),
        "end_at": record.get("end_at") or get_nested(record, "timing", "end_at"),
        "timezone": record.get("timezone") or get_nested(record, "timing", "timezone"),
        "location_name": record.get("location_name") or get_nested(record, "location", "location_name"),
        "location_display": record.get("location_display") or get_nested(record, "location", "location_display"),
        "registration_url": record.get("registration_url") or get_nested(record, "commerce", "registration_url"),
        "session_status": extract_source_status(record, previous),
    }

    merged = deepcopy(previous_known)
    for key, value in current.items():
        cleaned = clean_string(value)
        if cleaned is not None:
            merged[key] = cleaned
    return merged


def comparable_material(record: dict[str, Any]) -> dict[str, str | None]:
    known = extract_last_known(record)
    return {
        key: clean_string(known.get(key))
        for key in MATERIAL_CONFLICT_FIELDS
    }


def materially_conflict(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_values = comparable_material(left)
    right_values = comparable_material(right)

    for key in MATERIAL_CONFLICT_FIELDS:
        left_value = left_values.get(key)
        right_value = right_values.get(key)
        if left_value and right_value and left_value != right_value:
            return True

    return False


def group_current_records(records: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], set[str], list[dict[str, Any]]]:
    grouped: dict[str, dict[str, Any]] = {}
    conflicts: set[str] = set()
    invalid_records: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        session_id = extract_session_id(record)
        if not session_id:
            invalid_records.append(
                {
                    "session_id": None,
                    "current_state": "INVALID_REMOVE",
                    "previous_state": None,
                    "state_reason": "missing_session_id",
                    "confidence_level": "high",
                    "is_currently_in_source": True,
                    "source_index": index,
                    "data_quality_flags": ["missing_session_id"],
                }
            )
            continue

        if session_id not in grouped:
            grouped[session_id] = record
            continue

        if materially_conflict(grouped[session_id], record):
            conflicts.add(session_id)

    return grouped, conflicts, invalid_records


def source_feed_is_suspect(current_count: int, previous: dict[str, dict[str, Any]]) -> bool:
    previous_seen_count = sum(
        1
        for session in previous.values()
        if session.get("is_currently_in_source") is True
    )

    if previous_seen_count < 5:
        return False

    if current_count == 0:
        return True

    return current_count < max(1, int(previous_seen_count * 0.2))


def invalid_reason(last_known: dict[str, Any], session_id: str | None, is_current: bool) -> tuple[str | None, list[str]]:
    flags: list[str] = []

    if not session_id:
        return "missing_session_id", ["missing_session_id"]

    course_name = clean_string(last_known.get("course_name"))
    start_at = clean_string(last_known.get("start_at"))
    end_at = clean_string(last_known.get("end_at"))

    if not course_name:
        flags.append("missing_required_course")

    if not start_at:
        flags.append("missing_required_timing")
    elif parse_datetime(start_at) is None:
        flags.append("malformed_start_at")

    if end_at and parse_datetime(end_at) is None:
        flags.append("malformed_end_at")

    start_dt = parse_datetime(start_at)
    end_dt = parse_datetime(end_at)
    if start_dt and end_dt and end_dt < start_dt:
        flags.append("end_before_start")

    registration_url = clean_string(last_known.get("registration_url"))
    if is_current and not registration_url:
        flags.append("missing_registration_url")

    if flags:
        return flags[0], flags

    return None, []


def has_cancellation_signal(last_known: dict[str, Any], previous: dict[str, Any] | None = None) -> bool:
    status = normalize_status(last_known.get("session_status"))
    previous_status = normalize_status(previous.get("source_status")) if previous else ""
    previous_reason = normalize_status(previous.get("state_reason")) if previous else ""

    if status in CANCELED_STATUSES:
        return True
    if previous_status in CANCELED_STATUSES:
        return True
    if "canceled" in previous_reason or "cancelled" in previous_reason:
        return True
    return False


def event_time(last_known: dict[str, Any]) -> datetime | None:
    end_dt = parse_datetime(last_known.get("end_at"))
    if end_dt:
        return end_dt
    return parse_datetime(last_known.get("start_at"))


def base_record(
    session_id: str,
    previous: dict[str, Any] | None,
    as_of: str,
) -> dict[str, Any]:
    record = deepcopy(previous) if previous else {}
    record["session_id"] = session_id
    record["previous_state"] = previous.get("current_state") if previous else None
    record.setdefault("first_seen_at", as_of)
    record.setdefault("last_seen_in_source_at", None)
    record.setdefault("last_built_at", None)
    record.setdefault("was_ever_published", False)
    record.setdefault("last_transition_at", None)
    record.setdefault("history", [])
    return record


def set_state(
    record: dict[str, Any],
    state: str,
    reason: str,
    confidence: str,
    as_of: str,
) -> dict[str, Any]:
    previous_state = record.get("previous_state")

    record["current_state"] = state
    record["state_reason"] = reason
    record["confidence_level"] = confidence

    if previous_state != state:
        record["last_transition_at"] = as_of

    return record


def classify_present_session(
    session_id: str,
    source_record: dict[str, Any],
    previous: dict[str, Any] | None,
    conflict_ids: set[str],
    as_of: str,
    as_of_dt: datetime,
) -> dict[str, Any]:
    record = base_record(session_id, previous, as_of)
    last_known = extract_last_known(source_record, previous)
    record["last_known"] = last_known
    record["is_currently_in_source"] = True
    record["last_seen_in_source_at"] = as_of
    record["source_status"] = extract_source_status(source_record, previous)

    if session_id in conflict_ids:
        record["data_quality_flags"] = ["conflicting_duplicate_session_id"]
        return set_state(
            record,
            "INVALID_REMOVE",
            "conflicting_duplicate_session_id",
            "high",
            as_of,
        )

    reason, flags = invalid_reason(last_known, session_id, is_current=True)
    if reason:
        record["data_quality_flags"] = flags
        return set_state(record, "INVALID_REMOVE", reason, "high", as_of)

    record["data_quality_flags"] = []

    if has_cancellation_signal(last_known, previous):
        return set_state(
            record,
            "CANCELED_DEPRECATED",
            "explicit_canceled_status",
            "high",
            as_of,
        )

    dt = event_time(last_known)
    if dt and dt >= as_of_dt:
        return set_state(record, "FUTURE_ACTIVE", "valid_future_session", "high", as_of)

    return set_state(record, "PAST_LIVE", "valid_past_session", "high", as_of)


def classify_missing_session(
    session_id: str,
    previous: dict[str, Any],
    as_of: str,
    as_of_dt: datetime,
    feed_suspect: bool,
) -> dict[str, Any]:
    record = base_record(session_id, previous, as_of)
    last_known = deepcopy(previous.get("last_known")) if isinstance(previous.get("last_known"), dict) else {}
    record["last_known"] = last_known
    record["is_currently_in_source"] = False

    if feed_suspect:
        preserved_state = previous.get("current_state")
        if preserved_state not in VALID_STATES:
            preserved_state = "INVALID_REMOVE"
        return set_state(
            record,
            preserved_state,
            "source_feed_suspect_preserved",
            "low",
            as_of,
        )

    reason, flags = invalid_reason(last_known, session_id, is_current=False)
    if reason:
        record["data_quality_flags"] = flags
        return set_state(record, "INVALID_REMOVE", reason, "medium", as_of)

    record["data_quality_flags"] = []

    if has_cancellation_signal(last_known, previous):
        return set_state(
            record,
            "CANCELED_DEPRECATED",
            "explicit_canceled_status",
            "medium",
            as_of,
        )

    dt = event_time(last_known)
    if dt and dt >= as_of_dt:
        return set_state(
            record,
            "CANCELED_DEPRECATED",
            "future_session_disappeared",
            "medium",
            as_of,
        )

    return set_state(record, "PAST_LIVE", "past_session_disappeared", "medium", as_of)


def summarize_counts(records: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts = {
        "total_sessions": len(records),
        "future_active": 0,
        "past_live": 0,
        "canceled_deprecated": 0,
        "invalid_remove": 0,
        "seen_in_source": 0,
        "missing_from_source": 0,
    }

    for record in records.values():
        state = record.get("current_state")
        if state == "FUTURE_ACTIVE":
            counts["future_active"] += 1
        elif state == "PAST_LIVE":
            counts["past_live"] += 1
        elif state == "CANCELED_DEPRECATED":
            counts["canceled_deprecated"] += 1
        elif state == "INVALID_REMOVE":
            counts["invalid_remove"] += 1

        if record.get("is_currently_in_source") is True:
            counts["seen_in_source"] += 1
        else:
            counts["missing_from_source"] += 1

    return counts


def classify_sessions(
    schedule: Any,
    manifest: Any,
    classification_as_of: str | None = None,
) -> dict[str, Any]:
    as_of = classification_as_of or now_iso()
    as_of_dt = parse_datetime(as_of) or datetime.now(TZ)

    current_records = source_sessions(schedule)
    previous_records = manifest_sessions(manifest)
    grouped_current, conflict_ids, invalid_records = group_current_records(current_records)
    feed_suspect = source_feed_is_suspect(len(current_records), previous_records)

    output_sessions: dict[str, dict[str, Any]] = {}

    for session_id in sorted(grouped_current):
        output_sessions[session_id] = classify_present_session(
            session_id=session_id,
            source_record=grouped_current[session_id],
            previous=previous_records.get(session_id),
            conflict_ids=conflict_ids,
            as_of=as_of,
            as_of_dt=as_of_dt,
        )

    for session_id in sorted(previous_records):
        if session_id in grouped_current:
            continue
        output_sessions[session_id] = classify_missing_session(
            session_id=session_id,
            previous=previous_records[session_id],
            as_of=as_of,
            as_of_dt=as_of_dt,
            feed_suspect=feed_suspect,
        )

    return {
        "classification_as_of": as_of,
        "source_feed_suspect": feed_suspect,
        "duplicate_conflicts": sorted(conflict_ids),
        "invalid_records": invalid_records,
        "counts": summarize_counts(output_sessions),
        "sessions": output_sessions,
    }
