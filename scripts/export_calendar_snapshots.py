from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from dateutil.rrule import rrulestr
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
CALENDAR_SOURCES_PATH = ROOT / "data" / "config" / "calendar_sources.json"
PEOPLE_CATALOG_PATH = ROOT / "data" / "config" / "people_catalog.json"
PRIVATE_CALENDAR_SECRETS_PATH = ROOT / "data" / "private" / "calendar_secrets.local.json"
RUNTIME_SNAPSHOT_DIR = ROOT / "data" / "runtime" / "calendar_snapshots"
AUDIT_DIR = ROOT / "data" / "audit"
SUMMARY_PATH = AUDIT_DIR / "calendar_snapshot_export_summary.json"
REPORT_PATH = AUDIT_DIR / "calendar_snapshot_export_report.md"

EXPORT_DAYS = 60
UNKNOWN = "UNKNOWN"
LOCAL_TZ = ZoneInfo("America/New_York")

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


def calendar_sources(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("calendar_sources"), list):
        return []
    return [source for source in payload["calendar_sources"] if isinstance(source, dict) and source.get("active", True)]


def source_key(source: dict[str, Any]) -> str:
    return clean_text(source.get("calendar_source_key") or source.get("source_id") or UNKNOWN)


def source_type(source: dict[str, Any]) -> str:
    mode = clean_text(source.get("calendar_mode") or source.get("mode"))
    return MODE_TO_SOURCE_TYPE.get(mode, mode or UNKNOWN)


def calendar_id_from_source(source: dict[str, Any]) -> str:
    calendar_id = clean_text(source.get("calendar_id"))
    if calendar_id:
        return calendar_id
    source_url = clean_text(source.get("source_url"))
    parsed = urllib.parse.urlparse(source_url)
    query = urllib.parse.parse_qs(parsed.query)
    cid = query.get("cid", [""])[0]
    return urllib.parse.unquote(cid) if cid else source_url


def redacted_url(value: str | None) -> str:
    if not value:
        return UNKNOWN
    text = str(value)
    if len(text) <= 32:
        return text
    parsed = urllib.parse.urlparse(text)
    if parsed.scheme and parsed.netloc:
        safe_prefix = f"{parsed.scheme}://{parsed.netloc}"
        suffix = text[-18:]
        return f"{safe_prefix}/...{suffix}"
    return f"{text[:12]}...{text[-12:]}"


def get_dotted_value(payload: Any, dotted_key: str) -> Any:
    if not isinstance(payload, dict) or not dotted_key:
        return None
    if dotted_key in payload:
        return payload[dotted_key]
    current: Any = payload
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def secret_ics_url_for_source(source: dict[str, Any], secrets: Any) -> tuple[str | None, str | None]:
    env_var = clean_text(source.get("url_env_var"))
    if env_var and os.environ.get(env_var):
        return os.environ[env_var], f"env:{env_var}"

    local_secret_key = clean_text(source.get("local_secret_key"))
    for key in (local_secret_key, env_var, source_key(source)):
        secret_value = clean_text(get_dotted_value(secrets, key))
        if secret_value:
            return secret_value, f"local_secret:{key}"
    return None, None


def ics_url_for_source(source: dict[str, Any], secrets: Any | None = None) -> tuple[str | None, str | None]:
    secret_url, secret_source = secret_ics_url_for_source(source, secrets or {})
    if secret_url:
        return secret_url, secret_source

    calendar_id = clean_text(source.get("calendar_id"))
    if calendar_id:
        encoded_calendar_id = urllib.parse.quote(calendar_id, safe="")
        return f"https://calendar.google.com/calendar/ical/{encoded_calendar_id}/public/basic.ics", "derived_public_ics_from_calendar_id"

    source_url = clean_text(source.get("source_url"))
    if not source_url:
        return None, "missing_source_url"
    lowered = source_url.lower()
    if lowered.endswith(".ics") or "/ical/" in lowered:
        return source_url, "source_url"

    parsed = urllib.parse.urlparse(source_url)
    query = urllib.parse.parse_qs(parsed.query)
    cid = query.get("cid", [""])[0]
    if not cid:
        return None, "missing_calendar_cid"
    encoded_cid = urllib.parse.quote(urllib.parse.unquote(cid), safe="")
    return f"https://calendar.google.com/calendar/ical/{encoded_cid}/public/basic.ics", "derived_public_ics"


def fetch_ics(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "LANDERware-scheduler-read-only-snapshot/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def unfold_ics_lines(text: str) -> list[str]:
    unfolded: list[str] = []
    for raw_line in text.splitlines():
        if raw_line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += raw_line[1:]
        else:
            unfolded.append(raw_line.rstrip("\r"))
    return unfolded


def split_ical_property(line: str) -> tuple[str, dict[str, str], str]:
    left, _, value = line.partition(":")
    parts = left.split(";")
    name = parts[0].upper()
    params: dict[str, str] = {}
    for part in parts[1:]:
        key, _, param_value = part.partition("=")
        if key:
            params[key.upper()] = param_value
    return name, params, value


def parse_ics_datetime(value: str, params: dict[str, str] | None = None) -> datetime | None:
    text = clean_text(value)
    if not text:
        return None
    params = params or {}
    formats = [
        ("%Y%m%dT%H%M%SZ", True),
        ("%Y%m%dT%H%M%S", False),
        ("%Y%m%dT%H%MZ", True),
        ("%Y%m%dT%H%M", False),
        ("%Y%m%d", False),
    ]
    for fmt, is_utc in formats:
        try:
            parsed = datetime.strptime(text, fmt)
            if is_utc:
                return parsed.replace(tzinfo=timezone.utc)
            tzid = clean_text(params.get("TZID"))
            if tzid:
                try:
                    return parsed.replace(tzinfo=ZoneInfo(tzid))
                except Exception:
                    return parsed.replace(tzinfo=LOCAL_TZ)
            return parsed
        except ValueError:
            continue
    return None


def ics_datetime_to_iso(value: str, params: dict[str, str] | None = None) -> str | None:
    parsed = parse_ics_datetime(value, params)
    return parsed.isoformat() if parsed else None


def comparable_dt(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def rrule_window_bounds(dtstart: datetime, window_start: datetime, window_end: datetime) -> tuple[datetime, datetime]:
    if dtstart.tzinfo is None:
        return comparable_dt(window_start), comparable_dt(window_end)
    return (
        window_start.astimezone(dtstart.tzinfo) if window_start.tzinfo else window_start.replace(tzinfo=dtstart.tzinfo),
        window_end.astimezone(dtstart.tzinfo) if window_end.tzinfo else window_end.replace(tzinfo=dtstart.tzinfo),
    )


def in_export_window(start: datetime, window_start: datetime, window_end: datetime) -> bool:
    return comparable_dt(window_start) <= comparable_dt(start) <= comparable_dt(window_end)


def recurrence_key(uid: Any, start: datetime | None) -> tuple[str, str]:
    return clean_text(uid), start.isoformat() if start else ""


def parse_recurrence_values(event: dict[str, Any], name: str) -> list[datetime]:
    values: list[datetime] = []
    raw_items = event.get("recurrence", [])
    if not isinstance(raw_items, list):
        return values
    for item in raw_items:
        if not isinstance(item, dict) or name.lower() not in item:
            continue
        raw_value = clean_text(item.get(name.lower()))
        for part in raw_value.split(","):
            parsed = parse_ics_datetime(part)
            if parsed:
                values.append(parsed)
    return values


def recurrence_rules(event: dict[str, Any]) -> list[str]:
    rules: list[str] = []
    for item in event.get("recurrence", []):
        if isinstance(item, dict) and item.get("rrule"):
            rules.append(clean_text(item["rrule"]))
    return [rule for rule in rules if rule]


def normalize_rrule_for_dtstart(rule: str, dtstart: datetime) -> str:
    if dtstart.tzinfo is not None:
        return rule

    def replace_until(match: re.Match[str]) -> str:
        raw_until = match.group(1)
        parsed = parse_ics_datetime(raw_until)
        if not parsed:
            return match.group(0)
        local_until = parsed.astimezone(LOCAL_TZ).replace(tzinfo=None) if parsed.tzinfo else parsed
        return f"UNTIL={local_until.strftime('%Y%m%dT%H%M%S')}"

    return re.sub(r"UNTIL=([0-9]{8}T[0-9]{4,6}Z)", replace_until, rule)


def clone_event_for_occurrence(event: dict[str, Any], occurrence_start: datetime, occurrence_end: datetime, source: str) -> dict[str, Any]:
    cloned = json.loads(json.dumps(event, ensure_ascii=False))
    master_uid = clean_text(event.get("event_id") or event.get("raw_properties", {}).get("UID"))
    cloned["recurrence_source"] = source
    cloned["generated_from_rrule"] = source == "recurring_expanded_instance"
    cloned["recurrence_source_uid"] = master_uid or UNKNOWN
    cloned["original_uid"] = master_uid or UNKNOWN
    cloned["occurrence_start"] = occurrence_start.isoformat()
    cloned["occurrence_end"] = occurrence_end.isoformat()
    cloned["start"] = occurrence_start.isoformat()
    cloned["end"] = occurrence_end.isoformat()
    if source == "recurring_expanded_instance":
        occurrence_suffix = re.sub(r"[^0-9A-Za-z]+", "", occurrence_start.isoformat())
        cloned["event_id"] = f"{master_uid}:{occurrence_suffix}" if master_uid else f"recurring:{occurrence_suffix}"
        cloned["recurring_master_event_id"] = master_uid or UNKNOWN
    return cloned


def expand_recurring_event(
    event: dict[str, Any],
    window_start: datetime,
    window_end: datetime,
    duplicate_keys: set[tuple[str, str]],
    override_keys: set[tuple[str, str]],
) -> tuple[list[dict[str, Any]], Counter]:
    skipped = Counter()
    start_raw = clean_text(event.get("start_raw"))
    end_raw = clean_text(event.get("end_raw"))
    start_params = event.get("start_params") if isinstance(event.get("start_params"), dict) else {}
    end_params = event.get("end_params") if isinstance(event.get("end_params"), dict) else {}
    start_dt = parse_ics_datetime(start_raw, start_params) if start_raw else None
    end_dt = parse_ics_datetime(end_raw, end_params) if end_raw else None
    if not start_dt or not end_dt:
        skipped["recurring_missing_parseable_start_or_end"] += 1
        return [], skipped
    duration = end_dt - start_dt
    if duration.total_seconds() <= 0:
        skipped["recurring_invalid_duration"] += 1
        return [], skipped

    exclusions = {comparable_dt(value) for value in parse_recurrence_values(event, "EXDATE")}
    rdates = parse_recurrence_values(event, "RDATE")
    occurrence_starts: list[datetime] = []
    bounded_start, bounded_end = rrule_window_bounds(start_dt, window_start, window_end)
    for rule in recurrence_rules(event):
        try:
            rule_set = rrulestr(normalize_rrule_for_dtstart(rule, start_dt), dtstart=start_dt)
            occurrence_starts.extend(rule_set.between(bounded_start, bounded_end, inc=True))
        except (ValueError, TypeError) as exc:
            skipped[f"rrule_parse_error:{type(exc).__name__}"] += 1
    occurrence_starts.extend(value for value in rdates if in_export_window(value, window_start, window_end))

    expanded: list[dict[str, Any]] = []
    seen_occurrences: set[str] = set()
    uid = event.get("event_id") or event.get("raw_properties", {}).get("UID")
    for occurrence_start in sorted(occurrence_starts, key=comparable_dt):
        comparable_start = comparable_dt(occurrence_start)
        occurrence_key = comparable_start.isoformat()
        if occurrence_key in seen_occurrences:
            skipped["duplicate_generated_occurrence"] += 1
            continue
        seen_occurrences.add(occurrence_key)
        key = recurrence_key(uid, occurrence_start)
        if comparable_start in exclusions:
            skipped["excluded_by_exdate"] += 1
            continue
        if key in override_keys:
            skipped["suppressed_by_recurrence_override"] += 1
            continue
        if key in duplicate_keys:
            skipped["duplicate_explicit_event_same_uid_start"] += 1
            continue
        occurrence_end = occurrence_start + duration
        expanded.append(clone_event_for_occurrence(event, occurrence_start, occurrence_end, "recurring_expanded_instance"))
    return expanded, skipped


def parse_ics_events(ics_text: str, source: dict[str, Any], window_start: datetime, window_end: datetime) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    lines = unfold_ics_lines(ics_text)
    parsed_events: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    skipped = Counter()
    source_id = source_key(source)
    calendar_id = calendar_id_from_source(source)
    stype = source_type(source)

    for line in lines:
        if line == "BEGIN:VEVENT":
            current = {"raw_properties": {}, "recurrence": []}
            continue
        if line == "END:VEVENT":
            if current is None:
                continue
            start_raw = current.get("start_raw")
            start_dt = parse_ics_datetime(start_raw, current.get("start_params")) if start_raw else None
            if not start_dt:
                skipped["missing_parseable_start"] += 1
            else:
                if in_export_window(start_dt, window_start, window_end) or recurrence_rules(current):
                    parsed_events.append(current)
                else:
                    skipped["outside_export_window"] += 1
            current = None
            continue
        if current is None:
            continue

        name, params, value = split_ical_property(line)
        current["raw_properties"][name] = value
        if name == "UID":
            current["event_id"] = value
        elif name == "SUMMARY":
            current["title"] = value
            current["summary"] = value
        elif name == "DESCRIPTION":
            current["description"] = value
        elif name == "DTSTART":
            current["start_raw"] = value
            current["start_params"] = params
            current["start"] = ics_datetime_to_iso(value, params)
        elif name == "DTEND":
            current["end_raw"] = value
            current["end_params"] = params
            current["end"] = ics_datetime_to_iso(value, params)
        elif name == "RECURRENCE-ID":
            current["recurrence_id_raw"] = value
            current["recurrence_id_params"] = params
            current["recurrence_id"] = ics_datetime_to_iso(value, params)
        elif name == "LOCATION":
            current["location"] = value
        elif name == "STATUS":
            current["status"] = value
        elif name in {"LAST-MODIFIED", "DTSTAMP"}:
            current["updated"] = ics_datetime_to_iso(value) or value
        elif name == "ORGANIZER":
            current["organizer"] = value
        elif name == "CREATED":
            current["created"] = ics_datetime_to_iso(value) or value
        elif name in {"RRULE", "RDATE", "EXDATE"}:
            current.setdefault("recurrence", []).append({name.lower(): value})

        current["calendar_source_id"] = source_id
        current["calendar_id"] = calendar_id
        current["source_type"] = stype
        current["read_only_snapshot"] = True

    duplicate_keys: set[tuple[str, str]] = set()
    override_keys: set[tuple[str, str]] = set()
    for event in parsed_events:
        event_start = parse_ics_datetime(event.get("start_raw", ""), event.get("start_params"))
        uid = event.get("event_id") or event.get("raw_properties", {}).get("UID")
        if event_start and not recurrence_rules(event):
            duplicate_keys.add(recurrence_key(uid, event_start))
        recurrence_id = parse_ics_datetime(event.get("recurrence_id_raw", ""), event.get("recurrence_id_params"))
        if recurrence_id:
            override_keys.add(recurrence_key(uid, recurrence_id))

    normalized_events = []
    for index, event in enumerate(parsed_events, start=1):
        event_start = parse_ics_datetime(event.get("start_raw", ""), event.get("start_params"))
        has_rrule = bool(recurrence_rules(event))
        has_override = bool(event.get("recurrence_id"))
        if not has_rrule and event_start and not in_export_window(event_start, window_start, window_end):
            skipped["outside_export_window"] += 1
            continue
        event["recurrence_source"] = "overridden_instance" if has_override else ("recurring_master" if has_rrule else "explicit_event")
        event["generated_from_rrule"] = False
        event["original_uid"] = event.get("event_id") or event.get("raw_properties", {}).get("UID") or UNKNOWN
        event["recurrence_source_uid"] = event["original_uid"]
        event.setdefault("event_id", f"{source_id}_event_{index}")
        event.setdefault("title", "")
        event.setdefault("summary", event.get("title", ""))
        event.setdefault("description", "")
        event.setdefault("location", "")
        event.setdefault("status", UNKNOWN)
        event.setdefault("updated", UNKNOWN)
        event.setdefault("creator", UNKNOWN)
        event.setdefault("organizer", event.get("organizer", UNKNOWN))
        if has_rrule:
            expanded, recurring_skipped = expand_recurring_event(event, window_start, window_end, duplicate_keys, override_keys)
            skipped.update(recurring_skipped)
            normalized_events.extend(expanded)
        else:
            normalized_events.append(event)

    normalized_events.sort(key=lambda item: (clean_text(item.get("start")), clean_text(item.get("event_id"))))
    return normalized_events, dict(skipped)


def write_source_snapshot(
    source: dict[str, Any],
    events: list[dict[str, Any]],
    window_start: datetime,
    window_end: datetime,
    export_status: str,
    url_source: str | None,
    warnings: list[str],
    skipped: dict[str, Any] | None = None,
) -> Path:
    source_id = source_key(source)
    RUNTIME_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNTIME_SNAPSHOT_DIR / f"{source_id}.json"
    payload = {
        "schema_version": "0.1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only_snapshot": True,
        "calendar_source_id": source_id,
        "calendar_id": calendar_id_from_source(source),
        "source_type": source_type(source),
        "source_display_name": source.get("display_name", UNKNOWN),
        "date_range": {
            "start": window_start.isoformat(),
            "end": window_end.isoformat(),
            "days": EXPORT_DAYS,
        },
        "export_status": export_status,
        "url_source": url_source or UNKNOWN,
        "event_count": len(events),
        "events": events,
        "warnings": warnings,
        "skipped": skipped or {},
        "public_site_affected": False,
        "enrollware_called": False,
        "appointments_created": False,
        "appointment_urls_changed": False,
        "worker_creation_enabled": False,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Calendar Snapshot Export Report",
        "",
        "This is a read-only local export. It did not call Enrollware, create appointments, change appointment URLs, modify public pages, write docs output, or enable Worker creation.",
        "",
        "Private event descriptions are stored only inside the local runtime snapshot JSON files and are not printed in this report.",
        "",
        "## Summary",
        "",
        f"- Calendar sources found: {summary['calendar_sources_found']}",
        f"- Snapshots written: {summary['snapshots_written']}",
        f"- Total events exported: {summary['total_events_exported']}",
        f"- Date range exported: {summary['date_range']['start']} through {summary['date_range']['end']}",
        f"- Private calendar secrets loaded: {summary['private_calendar_secrets_loaded']}",
        "",
        "## Events Exported Per Source",
        "",
        "| Source | Calendar ID Present | ICS URL Attempted | URL Source | Type | Status | Failure Reason | Events | Snapshot | Warning Count |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | --- | ---: |",
    ]
    for item in summary["sources"]:
        lines.append(
            f"| {item['calendar_source_id']} | {item['calendar_id_present']} | {item['attempted_ics_url_redacted']} | "
            f"{item['url_source']} | {item['source_type']} | {item['export_status']} | {item.get('failure_reason') or ''} | {item['events_exported']} | "
            f"`{item['snapshot_path']}` | {len(item.get('warnings', []))} |"
        )
    lines.extend(["", "## Warnings", ""])
    warnings = [warning for item in summary["sources"] for warning in item.get("warnings", [])]
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def export_calendar_snapshots(fetcher: Callable[[str], str] = fetch_ics) -> dict[str, Any]:
    calendar_payload, calendar_error = read_json(CALENDAR_SOURCES_PATH)
    _people_payload, people_error = read_json(PEOPLE_CATALOG_PATH)
    private_secrets_payload, private_secrets_error = read_json(PRIVATE_CALENDAR_SECRETS_PATH)
    window_start = datetime.now().astimezone()
    window_end = window_start + timedelta(days=EXPORT_DAYS)
    sources = calendar_sources(calendar_payload or {})
    source_summaries = []

    for source in sources:
        source_id = source_key(source)
        warnings: list[str] = []
        events: list[dict[str, Any]] = []
        skipped: dict[str, Any] = {}
        export_status = "ok"
        ics_url, url_source = ics_url_for_source(source, private_secrets_payload or {})
        calendar_id = calendar_id_from_source(source)
        failure_reason = None
        if not ics_url:
            export_status = "failed"
            failure_reason = f"no usable Google Calendar ICS URL ({url_source})"
            warnings.append(f"{source_id}: {failure_reason}; likely needs a Secret iCal URL or Google API auth")
        else:
            try:
                ics_text = fetcher(ics_url)
                events, skipped = parse_ics_events(ics_text, source, window_start, window_end)
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                export_status = "failed"
                failure_reason = f"calendar export failed ({type(exc).__name__})"
                warnings.append(f"{source_id}: {failure_reason}; likely needs a Secret iCal URL or Google API auth")
        snapshot_path = write_source_snapshot(source, events, window_start, window_end, export_status, url_source, warnings, skipped)
        source_summaries.append({
            "calendar_source_id": source_id,
            "calendar_id": calendar_id,
            "calendar_id_present": bool(calendar_id and calendar_id != UNKNOWN),
            "source_type": source_type(source),
            "export_status": export_status,
            "failure_reason": failure_reason,
            "url_source": url_source or UNKNOWN,
            "attempted_ics_url_redacted": redacted_url(ics_url),
            "events_exported": len(events),
            "snapshot_path": str(snapshot_path),
            "warnings": warnings,
            "skipped": skipped,
        })

    summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only_snapshot_export": True,
        "calendar_sources_path": str(CALENDAR_SOURCES_PATH),
        "people_catalog_path": str(PEOPLE_CATALOG_PATH),
        "private_calendar_secrets_path": str(PRIVATE_CALENDAR_SECRETS_PATH),
        "private_calendar_secrets_loaded": private_secrets_error is None,
        "calendar_sources_found": len(sources),
        "snapshots_written": len(source_summaries),
        "total_events_exported": sum(item["events_exported"] for item in source_summaries),
        "events_exported_per_source": {item["calendar_source_id"]: item["events_exported"] for item in source_summaries},
        "date_range": {
            "start": window_start.isoformat(),
            "end": window_end.isoformat(),
            "days": EXPORT_DAYS,
        },
        "sources": source_summaries,
        "input_errors": {
            "calendar_sources": calendar_error,
            "people_catalog": people_error,
            "private_calendar_secrets": private_secrets_error,
        },
        "public_site_affected": False,
        "enrollware_called": False,
        "appointments_created": False,
        "appointment_urls_changed": False,
        "worker_creation_enabled": False,
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(summary), encoding="utf-8")
    return summary


def main() -> int:
    summary = export_calendar_snapshots()
    print("Calendar snapshot export complete (READ ONLY).")
    print("No Enrollware, public pages, appointments, appointment URLs, docs output, or Worker settings were changed.")
    print("")
    print(f"Calendar sources found: {summary['calendar_sources_found']}")
    print(f"Snapshots written: {summary['snapshots_written']}")
    print(f"Total events exported: {summary['total_events_exported']}")
    print(f"Date range exported: {summary['date_range']['start']} through {summary['date_range']['end']}")
    print("")
    print("Events exported per source:")
    for source_id, count in summary["events_exported_per_source"].items():
        print(f"- {source_id}: {count}")
    print("")
    print("Output files:")
    print(f"- {SUMMARY_PATH}")
    print(f"- {REPORT_PATH}")
    for item in summary["sources"]:
        print(f"- {item['snapshot_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
