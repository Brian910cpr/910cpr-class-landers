from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
CALENDAR_SOURCES_PATH = ROOT / "data" / "config" / "calendar_sources.json"
PEOPLE_CATALOG_PATH = ROOT / "data" / "config" / "people_catalog.json"
COURSE_CATALOG_PATH = ROOT / "data" / "config" / "course_catalog.json"
RECHECK_REQUIREMENTS_PATH = AUDIT_DIR / "live_availability_recheck_requirements.json"
SNAPSHOT_PATH = AUDIT_DIR / "live_availability_snapshot_preview.json"
REPORT_PATH = AUDIT_DIR / "live_availability_snapshot_report.md"
RUNTIME_CALENDAR_SNAPSHOT_DIR = ROOT / "data" / "runtime" / "calendar_snapshots"

LOCAL_SNAPSHOT_CANDIDATES = [
    ROOT / "data" / "calendar" / "live_calendar_events_snapshot.json",
    AUDIT_DIR / "live_calendar_events_snapshot.json",
    ROOT / "data" / "inventory" / "live_calendar_events_snapshot.json",
]

UNKNOWN = "UNKNOWN"
LOCAL_TZ = ZoneInfo("America/New_York")
DEFAULT_LOCATION_BY_KEY = {
    "shipyard": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
}

MODE_TO_SOURCE_TYPE = {
    "explicit_availability": "google_calendar",
    "inverse_blocking": "inverse_google_calendar",
    "blocking": "blocking_calendar",
    "occupancy": "occupancy_calendar",
}


def read_json(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid_json: {exc}"
    except OSError as exc:
        return None, f"read_error: {exc}"


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean_text(value).lower()).strip("_")


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = clean_text(value)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed
    return parsed.astimezone(LOCAL_TZ).replace(tzinfo=None)


def has_explicit_time(value: Any) -> bool:
    text = clean_text(value)
    if not text:
        return False
    return "T" in text or bool(re.search(r"\b\d{1,2}:\d{2}\b", text))


def raw_value_has_time(value: Any) -> bool:
    text = clean_text(value)
    if not text:
        return False
    if re.fullmatch(r"\d{8}", text):
        return False
    return "T" in text or bool(re.search(r"\b\d{1,2}:?\d{2}\b", text))


def is_all_day_event(event: dict[str, Any]) -> bool:
    if event.get("all_day") is True:
        return True
    raw_start = event.get("start_raw")
    raw_end = event.get("end_raw")
    if raw_start or raw_end:
        return not raw_value_has_time(raw_start) and not raw_value_has_time(raw_end)
    raw_properties = event.get("raw_properties")
    if isinstance(raw_properties, dict):
        dt_start = raw_properties.get("DTSTART")
        dt_end = raw_properties.get("DTEND")
        if dt_start or dt_end:
            return not raw_value_has_time(dt_start) and not raw_value_has_time(dt_end)
    return False


def is_standard_time_increment(value: datetime) -> bool:
    return value.minute % 15 == 0


def event_policy_reason_codes(source: dict[str, Any], event: dict[str, Any], start: datetime | None, end: datetime | None) -> list[str]:
    if not start or not end:
        return ["event_missing_parseable_start_or_end"]

    raw_start = event.get("start") or event.get("start_at") or event.get("start_datetime")
    raw_end = event.get("end") or event.get("end_at") or event.get("end_datetime")
    explicit_time = has_explicit_time(raw_start) and has_explicit_time(raw_end) and not is_all_day_event(event)
    all_day_allowed = bool(source.get("all_day_means_available"))
    reasons: list[str] = []

    if not explicit_time and not all_day_allowed:
        reasons.append("all_day_without_time")
    if end <= start:
        reasons.append("invalid_time_range")
    if (
        explicit_time
        and not bool(source.get("allow_non_standard_time_increment"))
        and (not is_standard_time_increment(start) or not is_standard_time_increment(end))
    ):
        reasons.append("non_standard_time_increment")
    return reasons


def event_time_validation(source: dict[str, Any], event: dict[str, Any]) -> tuple[datetime | None, datetime | None, str | None, list[str]]:
    raw_start = event.get("start") or event.get("start_at") or event.get("start_datetime")
    raw_end = event.get("end") or event.get("end_at") or event.get("end_datetime")
    start = parse_dt(raw_start)
    end = parse_dt(raw_end)
    reasons = event_policy_reason_codes(source, event, start, end)
    return start, end, reasons[0] if reasons else None, reasons


def calendar_sources(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("calendar_sources"), list):
        return []
    return [source for source in payload["calendar_sources"] if isinstance(source, dict)]


def people_lookup(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("people"), list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    first_names: dict[str, list[dict[str, Any]]] = {}
    for person in payload["people"]:
        if not isinstance(person, dict):
            continue
        display = clean_text(person.get("display_name"))
        email = clean_text(person.get("email"))
        keys = {
            normalize_key(person.get("person_id")),
            normalize_key(display),
            normalize_key(email),
            normalize_key(email.split("@", 1)[0] if "@" in email else ""),
        }
        first = normalize_key(display.split(" ")[0]) if display else ""
        if first:
            first_names.setdefault(first, []).append(person)
        for key in keys:
            if key:
                out[key] = person
    for first, matches in first_names.items():
        if len(matches) == 1 and first not in out:
            out[first] = matches[0]
    return out


def allowed_families_for_person(person: dict[str, Any] | None, course_catalog: Any) -> list[str]:
    if not isinstance(person, dict) or not isinstance(course_catalog, dict):
        return []
    codes = {
        str(cert.get("certification_code"))
        for cert in person.get("certifications", [])
        if isinstance(cert, dict) and cert.get("certification_code")
    }
    families = set()
    for course in course_catalog.get("courses", []):
        if not isinstance(course, dict):
            continue
        reqs = {str(item) for item in course.get("required_instructor_certifications", [])}
        if codes & reqs and course.get("family"):
            families.add(str(course["family"]))
    return sorted(families)


def load_runtime_snapshots() -> tuple[Path | None, Any | None, dict[str, str]]:
    missing = {}
    if not RUNTIME_CALENDAR_SNAPSHOT_DIR.exists():
        missing[str(RUNTIME_CALENDAR_SNAPSHOT_DIR)] = "missing"
        return None, None, missing
    snapshot_files = sorted(RUNTIME_CALENDAR_SNAPSHOT_DIR.glob("*.json"))
    if not snapshot_files:
        missing[str(RUNTIME_CALENDAR_SNAPSHOT_DIR)] = "no_snapshot_files"
        return None, None, missing

    events_by_source: dict[str, list[dict[str, Any]]] = {}
    loaded_files = []
    for path in snapshot_files:
        payload, error = read_json(path)
        if error:
            missing[str(path)] = error
            continue
        if not isinstance(payload, dict):
            missing[str(path)] = "invalid_snapshot_shape"
            continue
        source_key = str(payload.get("calendar_source_id") or path.stem)
        raw_events = payload.get("events", [])
        events_by_source[source_key] = [event for event in raw_events if isinstance(event, dict)] if isinstance(raw_events, list) else []
        loaded_files.append(str(path))

    if not loaded_files:
        return None, None, missing
    return RUNTIME_CALENDAR_SNAPSHOT_DIR, {
        "snapshot_source": "runtime_calendar_snapshots",
        "snapshot_files": loaded_files,
        "events_by_source": events_by_source,
    }, missing


def find_local_snapshot() -> tuple[Path | None, Any | None, dict[str, str]]:
    missing = {}
    runtime_path, runtime_payload, runtime_missing = load_runtime_snapshots()
    missing.update(runtime_missing)
    if runtime_payload is not None:
        return runtime_path, runtime_payload, missing

    for path in LOCAL_SNAPSHOT_CANDIDATES:
        payload, error = read_json(path)
        if error:
            missing[str(path)] = error
            continue
        return path, payload, missing
    return None, None, missing


def source_type(source: dict[str, Any]) -> str:
    mode = str(source.get("calendar_mode") or source.get("mode") or "").strip()
    return MODE_TO_SOURCE_TYPE.get(mode, mode or UNKNOWN)


def event_text(event: dict[str, Any]) -> str:
    return " ".join(clean_text(event.get(key)) for key in ("summary", "title", "description", "notes")).lower()


def is_blocking_event(event: dict[str, Any]) -> bool:
    text = event_text(event)
    return any(marker in text for marker in ("dns", "do not schedule", "adr", "employment", "personal", "unavailable"))


def events_for_source(snapshot_payload: Any, source_key: str) -> list[dict[str, Any]]:
    if not isinstance(snapshot_payload, dict):
        return []
    raw = snapshot_payload.get("events_by_source", {}).get(source_key)
    if raw is None:
        raw = snapshot_payload.get(source_key)
    if raw is None and isinstance(snapshot_payload.get("events"), list):
        raw = [event for event in snapshot_payload["events"] if isinstance(event, dict) and event.get("calendar_source_key") == source_key]
    return [event for event in raw if isinstance(event, dict)] if isinstance(raw, list) else []


def normalize_event_block(source: dict[str, Any], event: dict[str, Any], person: dict[str, Any] | None, course_catalog: Any) -> dict[str, Any] | None:
    start, end, invalid_reason, _reason_codes = event_time_validation(source, event)
    if invalid_reason or not start or not end:
        return None
    stype = source_type(source)
    blocking = is_blocking_event(event) or stype in {"blocking_calendar", "occupancy_calendar"}
    status = "blocked" if blocking else "available"
    location_key = source.get("default_location_key")
    source_location = clean_text(event.get("location"))
    location_name = source_location or DEFAULT_LOCATION_BY_KEY.get(str(location_key), UNKNOWN)
    location_mode = clean_text(source.get("availability_location_mode") or "location_specific") or "location_specific"
    return {
        "instructor_name": person.get("display_name") if person else clean_text(source.get("owner_instructor_key") or source.get("instructor_key") or UNKNOWN).title(),
        "person_id": person.get("person_id", UNKNOWN) if person else UNKNOWN,
        "start_datetime": start.isoformat(),
        "end_datetime": end.isoformat(),
        "date": start.date().isoformat(),
        "end_date": end.date().isoformat(),
        "start_time": start.strftime("%H:%M"),
        "end_time": end.strftime("%H:%M"),
        "availability_status": status,
        "availability_location_mode": location_mode,
        "source_location": source_location or UNKNOWN,
        "location_name": location_name,
        "allowed_course_families": [] if blocking else allowed_families_for_person(person, course_catalog),
        "source_calendar_id": source.get("calendar_source_key", UNKNOWN),
        "source_event_id": event.get("id") or event.get("event_id") or UNKNOWN,
        "source_type": stype,
        "reasons": [
            "read_only_preview",
            "local_calendar_snapshot",
            "blocking_marker_detected" if blocking else "offerable_calendar_window",
        ],
    }


def build_snapshot(calendar_payload: Any, people_payload: Any, course_payload: Any, local_snapshot_payload: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    sources = calendar_sources(calendar_payload)
    people = people_lookup(people_payload)
    blocks: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    dns_markers = 0
    instructors_mapped = []
    for source in sources:
        source_key = str(source.get("calendar_source_key") or UNKNOWN)
        instructor_key = source.get("owner_instructor_key") or source.get("instructor_key")
        person = people.get(normalize_key(instructor_key))
        if person:
            instructors_mapped.append({
                "calendar_source_key": source_key,
                "person_id": person.get("person_id", UNKNOWN),
                "display_name": person.get("display_name", UNKNOWN),
            })
        events = events_for_source(local_snapshot_payload, source_key)
        if not events:
            blocked.append({
                "calendar_source_key": source_key,
                "source_type": source_type(source),
                "reason_code": "local_calendar_snapshot_missing",
                "message": "No local/mock calendar event snapshot found for this source; no availability blocks generated.",
            })
            continue
        for event in events:
            _start, _end, invalid_reason, reason_codes = event_time_validation(source, event)
            block = normalize_event_block(source, event, person, course_payload)
            if not block:
                reason_code = invalid_reason or "event_missing_parseable_start_or_end"
                messages = {
                    "event_missing_parseable_start_or_end": "Calendar event did not include parseable start/end datetimes.",
                    "invalid_time_range": "Calendar event end is not after start; no offerable availability was generated.",
                    "all_day_without_time": "Calendar event has no explicit start/end time and all_day_means_available is false; no offerable availability was generated.",
                    "non_standard_time_increment": "Calendar event start/end is not on a standard 15-minute increment and allow_non_standard_time_increment is false; no offerable availability was generated.",
                }
                blocked.append({
                    "calendar_source_key": source_key,
                    "source_event_id": event.get("id") or event.get("event_id") or UNKNOWN,
                    "source_type": source_type(source),
                    "reason_code": reason_code,
                    "all_reason_codes": reason_codes or [reason_code],
                    "message": messages.get(reason_code, "Calendar event was not usable as an availability block."),
                })
                continue
            if "dns" in event_text(event) or "do not schedule" in event_text(event):
                dns_markers += 1
            blocks.append(block)
    stats = {
        "configured_calendar_sources_found": len(sources),
        "instructors_mapped": instructors_mapped,
        "blocks_generated": len(blocks),
        "blocks_blocked": len(blocked),
        "dns_markers_found": dns_markers,
        "blocked_reason_counts": dict(Counter(item["reason_code"] for item in blocked)),
        "blocked_all_reason_counts": dict(Counter(reason for item in blocked for reason in item.get("all_reason_codes", [item["reason_code"]]))),
        "source_type_counts": dict(Counter(source_type(source) for source in sources)),
        "availability_status_counts": dict(Counter(block["availability_status"] for block in blocks)),
    }
    return blocks, blocked, stats


def render_report(stats: dict[str, Any], blocked: list[dict[str, Any]], local_snapshot_path: Path | None, missing: dict[str, str]) -> str:
    lines = [
        "# Live Availability Snapshot Preview Report",
        "",
        "This is a read-only scaffold. It did not call Google Calendar, call Enrollware, create appointments, modify public pages, write docs output, or enable Worker creation.",
        "",
        "## Summary",
        "",
        f"- Configured calendar sources found: {stats['configured_calendar_sources_found']}",
        f"- Local snapshot found: {local_snapshot_path if local_snapshot_path else 'None'}",
        f"- Instructors mapped: {len(stats['instructors_mapped'])}",
        f"- Blocks generated: {stats['blocks_generated']}",
        f"- Blocks blocked/placeheld: {stats['blocks_blocked']}",
        f"- DNS markers found: {stats['dns_markers_found']}",
        "",
        "## Blocked Reason Counts",
        "",
    ]
    if stats.get("blocked_reason_counts"):
        lines.extend(f"- `{reason}`: {count}" for reason, count in stats["blocked_reason_counts"].items())
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Missing Calendar Source Config / Snapshots",
        "",
    ])
    if missing:
        lines.extend(f"- `{path}`: {reason}" for path, reason in sorted(missing.items()))
    else:
        lines.append("- None")
    lines.extend(["", "## Calendar Sources Blocked Or Placeholdered", ""])
    if blocked:
        lines.extend(["| Source | Type | Reason | Message |", "| --- | --- | --- | --- |"])
        for item in blocked:
            lines.append(f"| {item.get('calendar_source_key', UNKNOWN)} | {item.get('source_type', UNKNOWN)} | `{item.get('reason_code', UNKNOWN)}` | {item.get('message', '')} |")
    else:
        lines.append("- None")
    lines.extend(["", "## Instructors Mapped", ""])
    if stats["instructors_mapped"]:
        lines.extend(["| Calendar Source | Person | Person ID |", "| --- | --- | --- |"])
        for item in stats["instructors_mapped"]:
            lines.append(f"| {item['calendar_source_key']} | {item['display_name']} | `{item['person_id']}` |")
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Next Safest Step",
        "",
        "- Add a local/mock calendar event snapshot fixture and verify normalization before any live Google Calendar integration.",
        "",
    ])
    return "\n".join(lines)


def run() -> dict[str, Any]:
    calendar_payload, calendar_error = read_json(CALENDAR_SOURCES_PATH)
    people_payload, people_error = read_json(PEOPLE_CATALOG_PATH)
    course_payload, course_error = read_json(COURSE_CATALOG_PATH)
    _requirements, requirements_error = read_json(RECHECK_REQUIREMENTS_PATH)
    local_snapshot_path, local_snapshot_payload, local_snapshot_missing = find_local_snapshot()
    missing = {}
    if calendar_error:
        missing[str(CALENDAR_SOURCES_PATH)] = calendar_error
    if people_error:
        missing[str(PEOPLE_CATALOG_PATH)] = people_error
    if course_error:
        missing[str(COURSE_CATALOG_PATH)] = course_error
    if requirements_error:
        missing[str(RECHECK_REQUIREMENTS_PATH)] = requirements_error
    missing.update(local_snapshot_missing)
    blocks, blocked, stats = build_snapshot(calendar_payload or {}, people_payload or {}, course_payload or {}, local_snapshot_payload or {})
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "public_site_affected": False,
        "google_calendar_called": False,
        "enrollware_called": False,
        "appointments_created": False,
        "appointment_urls_changed": False,
        "worker_creation_enabled": False,
        "local_snapshot_path": str(local_snapshot_path) if local_snapshot_path else None,
        "stats": stats,
        "availability_blocks": blocks,
        "blocked_or_placeholder_sources": blocked,
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(stats, blocked, local_snapshot_path, missing), encoding="utf-8")
    return {"stats": stats, "missing": missing, "output_paths": [SNAPSHOT_PATH, REPORT_PATH]}


def main() -> int:
    result = run()
    print("Live availability snapshot scaffold complete (READ ONLY).")
    print("No Google Calendar, Enrollware, public pages, appointments, appointment URLs, or Worker settings were changed.")
    print("")
    print(f"Configured calendar sources found: {result['stats']['configured_calendar_sources_found']}")
    print(f"Blocks generated: {result['stats']['blocks_generated']}")
    print(f"Blocks blocked/placeheld: {result['stats']['blocks_blocked']}")
    print(f"DNS markers found: {result['stats']['dns_markers_found']}")
    print("")
    print("Output files:")
    for path in result["output_paths"]:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
