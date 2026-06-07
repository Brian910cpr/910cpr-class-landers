#!/usr/bin/env python3
"""Build a report-only instructor availability summary.

This first pass is intentionally non-destructive. It reads the committed
calendar/instructor config shells and an optional local fixture file, then
writes normalized debug reports. It does not seed public classes or change
public page output.
"""

from __future__ import annotations

import json
import os
import urllib.request
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "data" / "config"
FIXTURE_PATH = ROOT / "data" / "fixtures" / "instructor_calendar_events.json"
DEBUG_DIR = ROOT / "debug"
REPORT_JSON_PATH = DEBUG_DIR / "instructor_availability_report.json"
REPORT_MD_PATH = DEBUG_DIR / "instructor_availability_report.md"
TZ = ZoneInfo("America/New_York")
EXPLICIT_VOCABULARY = {"HARD", "SOFT", "UNAVAILABLE"}
SOURCE_MODES = {"fixture", "live", "auto"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=TZ)
    return parsed.astimezone(TZ)


def normalize_title(value: Any) -> str:
    return " ".join(str(value or "").strip().upper().split())


def event_label(value: Any) -> str:
    title = normalize_title(value)
    first = title.split(" ", 1)[0] if title else ""
    return first if first in EXPLICIT_VOCABULARY else title


def iso(dt: datetime) -> str:
    return dt.isoformat()


def load_fixture_events() -> tuple[list[dict[str, Any]], list[str]]:
    if not FIXTURE_PATH.exists():
        return [], [f"Fixture file not found: {FIXTURE_PATH.relative_to(ROOT)}"]
    payload = load_json(FIXTURE_PATH)
    if isinstance(payload.get("events"), list):
        return [item for item in payload["events"] if isinstance(item, dict)], []
    rows: list[dict[str, Any]] = []
    for key in ("calendar_sources", "instructors"):
        container = payload.get(key)
        if not isinstance(container, dict):
            continue
        for owner_key, events in container.items():
            if not isinstance(events, list):
                continue
            for event in events:
                if isinstance(event, dict):
                    row = dict(event)
                    row.setdefault("calendar_source_key", owner_key)
                    row.setdefault("instructor_key", owner_key)
                    rows.append(row)
    return rows, []


def unfold_ics_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw.startswith((" ", "\t")) and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def parse_ics_datetime(value: str, params: dict[str, str]) -> datetime | None:
    try:
        if "T" not in value:
            parsed = datetime.strptime(value, "%Y%m%d").replace(tzinfo=TZ)
        elif value.endswith("Z"):
            parsed = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=ZoneInfo("UTC"))
        else:
            parsed = datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=ZoneInfo(params.get("TZID", TZ.key)))
    except ValueError:
        return None
    return parsed.astimezone(TZ)


def parse_property(line: str) -> tuple[str, dict[str, str], str]:
    head, _, value = line.partition(":")
    parts = head.split(";")
    params: dict[str, str] = {}
    for param in parts[1:]:
        key, _, param_value = param.partition("=")
        params[key.upper()] = param_value.strip('"')
    return parts[0].upper(), params, value


def live_ics_url(source: dict[str, Any]) -> tuple[str, str]:
    env_var = str(source.get("url_env_var") or "").strip()
    ics_url = os.environ.get(env_var, "").strip() if env_var else ""
    return ics_url, env_var


def fetch_ics_events(source: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    ics_url, env_var = live_ics_url(source)
    if not ics_url:
        return [], (
            f"No live ICS URL configured in {env_var or 'environment'}. "
            "Public Google Calendar CID web URLs are not fetched directly; provide a public/basic ICS URL or private ICS URL via the configured environment variable."
        )
    try:
        request = urllib.request.Request(ics_url, headers={"User-Agent": "910CPR-Availability-Report/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            text = response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return [], f"Could not fetch {source.get('calendar_source_key')} live calendar: {exc}"

    events: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in unfold_ics_lines(text):
        if line == "BEGIN:VEVENT":
            current = {"calendar_source_key": source.get("calendar_source_key"), "instructor_key": source.get("instructor_key")}
        elif line == "END:VEVENT" and current is not None:
            events.append(current)
            current = None
        elif current is not None:
            name, params, value = parse_property(line)
            if name == "SUMMARY":
                current["title"] = value.replace("\\,", ",")
            elif name in {"DTSTART", "DTEND"}:
                current["start" if name == "DTSTART" else "end"] = parse_ics_datetime(value, params).isoformat() if parse_ics_datetime(value, params) else ""
    return events, None


def fixture_events_for_source(source: dict[str, Any], fixture_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_key = str(source.get("calendar_source_key") or "")
    instructor_key = str(source.get("instructor_key") or source.get("owner_instructor_key") or "")
    return [
        event
        for event in fixture_events
        if str(event.get("calendar_source_key") or "") == source_key
        or str(event.get("source_key") or "") == source_key
        or str(event.get("instructor_key") or "") == instructor_key
    ]


def raw_events_for_source(source: dict[str, Any], fixture_events: list[dict[str, Any]], source_mode: str) -> tuple[list[dict[str, Any]], list[str], str]:
    source_key = str(source.get("calendar_source_key") or "")
    matched = fixture_events_for_source(source, fixture_events)
    if source_mode == "fixture":
        if not matched:
            return [], [f"Fixture mode requested but no fixture events matched {source_key}."], "fixture"
        return matched, [f"Loaded {len(matched)} event(s) from local fixture for {source_key}."], "fixture"
    if source_mode == "live":
        live_events, warning = fetch_ics_events(source)
        warnings = [warning] if warning else []
        if live_events:
            warnings.append(f"Loaded {len(live_events)} event(s) from live ICS for {source_key}.")
        return live_events, warnings, "live"

    ics_url, _ = live_ics_url(source)
    if ics_url:
        live_events, warning = fetch_ics_events(source)
        warnings = [warning] if warning else []
        if live_events:
            warnings.append(f"Loaded {len(live_events)} event(s) from live ICS for {source_key}.")
            return live_events, warnings, "live"
        if matched:
            warnings.append(f"Falling back to {len(matched)} local fixture event(s) for {source_key}.")
            return matched, warnings, "fixture"
        return [], warnings, "live"
    if matched:
        return matched, [f"Loaded {len(matched)} event(s) from local fixture for {source_key}."], "fixture"
    live_events, warning = fetch_ics_events(source)
    warnings = [warning] if warning else []
    if live_events:
        warnings.append(f"Loaded {len(live_events)} event(s) from live ICS for {source_key}.")
    return live_events, warnings, "none"


def normalize_event(raw: dict[str, Any], source: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    start = parse_dt(raw.get("start") or raw.get("start_at") or raw.get("dtstart"))
    end = parse_dt(raw.get("end") or raw.get("end_at") or raw.get("dtend"))
    title = str(raw.get("title") or raw.get("summary") or raw.get("name") or "").strip()
    if not start or not end:
        return None, f"Ignored event with missing/invalid start or end: {title or raw}"
    if end <= start:
        return None, f"Ignored event with non-positive duration: {title or raw}"
    location_key = str(raw.get("location_key") or source.get("default_location_key") or "").strip()
    return {
        "title": title,
        "label": event_label(title),
        "start": iso(start),
        "end": iso(end),
        "location_key": location_key,
        "raw": raw,
    }, None


def overlaps(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return parse_dt(a["start"]) < parse_dt(b["end"]) and parse_dt(b["start"]) < parse_dt(a["end"])


def subtract_blocks(window: dict[str, Any], blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    segments = [(parse_dt(window["start"]), parse_dt(window["end"]))]
    for block in blocks:
        block_start = parse_dt(block["start"])
        block_end = parse_dt(block["end"])
        next_segments = []
        for start, end in segments:
            if block_end <= start or block_start >= end:
                next_segments.append((start, end))
                continue
            if block_start > start:
                next_segments.append((start, min(block_start, end)))
            if block_end < end:
                next_segments.append((max(block_end, start), end))
        segments = [(start, end) for start, end in next_segments if start and end and end > start]
    output = []
    for start, end in segments:
        row = {key: value for key, value in window.items() if key != "raw"}
        row["start"] = iso(start)
        row["end"] = iso(end)
        output.append(row)
    return output


def build_instructor_report(
    instructor: dict[str, Any],
    source: dict[str, Any],
    fixture_events: list[dict[str, Any]],
    fixture_warnings: list[str],
    source_mode: str,
) -> dict[str, Any]:
    source_key = str(source.get("calendar_source_key") or "")
    mode = str(source.get("calendar_mode") or source.get("mode") or instructor.get("calendar_mode") or "")
    raw_events, source_warnings, events_source = raw_events_for_source(source, fixture_events, source_mode)
    warnings = ([] if source_mode == "live" else list(fixture_warnings)) + source_warnings
    ignored_events: list[str] = []
    normalized: list[dict[str, Any]] = []
    for raw in raw_events:
        event, reason = normalize_event(raw, source)
        if reason:
            ignored_events.append(reason)
        elif event:
            normalized.append(event)

    hard = []
    soft = []
    unavailable = []
    blocks = []
    for event in normalized:
        label = event["label"]
        if mode == "explicit_availability":
            if label == "HARD":
                hard.append(event)
            elif label == "SOFT":
                soft.append(event)
            elif label == "UNAVAILABLE":
                unavailable.append(event)
            else:
                ignored_events.append(f"Ignored unsupported explicit availability title: {event['title']}")
        elif mode == "inverse_blocking":
            blocks.append(event)
            unavailable.append(event)

    usable_hard = [segment for window in hard for segment in subtract_blocks(window, unavailable)]
    soft_edges = [segment for window in soft for segment in subtract_blocks(window, unavailable)]
    final_usable = usable_hard if mode == "explicit_availability" else []
    if mode == "inverse_blocking":
        warnings.append(
            "Brian is inverse-blocking only in this report. No availability windows were invented; future offer generation needs a configured candidate-window generator."
        )
    if mode == "explicit_availability" and not hard and not soft:
        warnings.append("No HARD/SOFT events found; explicit-availability instructor has no offerable availability.")

    return {
        "instructor_key": instructor.get("instructor_key"),
        "display_name": instructor.get("display_name"),
        "calendar_source_key": source_key,
        "calendar_source_loaded": bool(source),
        "calendar_mode": mode,
        "events_source": events_source,
        "default_location_key": source.get("default_location_key") or instructor.get("default_location_key"),
        "events_found": len(raw_events),
        "normalized_hard_windows": usable_hard,
        "normalized_soft_windows": soft_edges,
        "unavailable_blocks": unavailable if mode == "explicit_availability" else blocks,
        "blocking_events": blocks,
        "ignored_events": ignored_events,
        "warnings": warnings,
        "final_usable_windows": final_usable,
        "soft_policy_note": "SOFT is flexible edge time only and is not treated as normal availability.",
    }


def build_report(source_mode: str = "auto") -> dict[str, Any]:
    if source_mode not in SOURCE_MODES:
        raise ValueError(f"source_mode must be one of {sorted(SOURCE_MODES)}")
    calendar_config = load_json(CONFIG_DIR / "calendar_sources.json")
    instructor_config = load_json(CONFIG_DIR / "instructors.json")
    load_json(CONFIG_DIR / "locations.json")
    load_json(CONFIG_DIR / "rules.json")

    fixture_events, fixture_warnings = load_fixture_events()
    sources = {
        str(item.get("calendar_source_key") or ""): item
        for item in calendar_config.get("calendar_sources", [])
        if isinstance(item, dict)
    }
    instructors = [item for item in instructor_config.get("instructors", []) if isinstance(item, dict)]
    rows = []
    for instructor in instructors:
        source_key = str(instructor.get("calendar_source_key") or "")
        source = sources.get(source_key, {})
        rows.append(build_instructor_report(instructor, source, fixture_events, fixture_warnings, source_mode))

    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "fixture_path": str(FIXTURE_PATH.relative_to(ROOT)),
        "fixture_loaded": FIXTURE_PATH.exists(),
        "source_mode": source_mode,
        "live_ics_policy": "Live mode uses only the configured *_ICS_URL environment variables. Public Google Calendar CID web URLs are not converted to ICS URLs here; public/basic.ics or private ICS URLs must be supplied explicitly.",
        "calendar_access_optional": True,
        "instructors": rows,
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Instructor Availability Report",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Report only: {report['report_only']}",
        f"- Public behavior changed: {report['public_behavior_changed']}",
        f"- Source mode: {report['source_mode']}",
        f"- Fixture loaded: {report['fixture_loaded']} ({report['fixture_path']})",
        f"- Live ICS policy: {report['live_ics_policy']}",
        "",
    ]
    for item in report["instructors"]:
        lines.extend(
            [
                f"## {item['display_name']} ({item['instructor_key']})",
                f"- Calendar source loaded: {item['calendar_source_loaded']} ({item['calendar_source_key']})",
                f"- Instructor mode: {item['calendar_mode']}",
                f"- Events source: {item['events_source']}",
                f"- Events found: {item['events_found']}",
                f"- HARD windows: {len(item['normalized_hard_windows'])}",
                f"- SOFT edge windows: {len(item['normalized_soft_windows'])}",
                f"- UNAVAILABLE/blocking events: {len(item['unavailable_blocks'])}",
                f"- Final usable windows: {len(item['final_usable_windows'])}",
                f"- Ignored events: {len(item['ignored_events'])}",
                f"- Warnings: {len(item['warnings'])}",
                "",
            ]
        )
        for warning in item["warnings"]:
            lines.append(f"  - Warning: {warning}")
        for ignored in item["ignored_events"]:
            lines.append(f"  - Ignored: {ignored}")
        lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build report-only instructor availability from fixture or live ICS sources.")
    parser.add_argument("--source", choices=sorted(SOURCE_MODES), default="auto", help="Event source mode. live uses only configured ICS URL environment variables.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(source_mode=args.source)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print("Instructor availability report generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
