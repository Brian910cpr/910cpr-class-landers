from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.block_start_time_selector import build_block_schedule_page, load_block_schedule_page_configs
from scripts.build_bls_block_schedule_pilot import apply_final_live_availability_guard

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "data" / "admin" / "scheduling_landscape.json"
ADMIN_AVAILABILITY = ROOT / "docs" / "data" / "admin_availability.json"
SCHEDULE_FUTURE = ROOT / "docs" / "data" / "schedule_future.json"
LOOKBACK_DAYS = 3
LOOKAHEAD_DAYS = 35


def clean(value: Any) -> str:
    return str(value or "").strip()


def in_window(value: Any, start: date, end: date) -> bool:
    try:
        parsed = date.fromisoformat(clean(value))
    except ValueError:
        return False
    return start <= parsed <= end


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def parse_dt(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(clean(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def source_label(value: Any) -> tuple[str, str]:
    key = clean(value).lower()
    if "ical" in key:
        return "enrollware-ical", "Enrollware iCal"
    if "class_report" in key or "class report" in key:
        return "class-report", "Class Report"
    return "enrollware-other", clean(value) or "Other Enrollware source"


def quarter_hour_cells(start: datetime, end: datetime) -> list[tuple[str, str]]:
    if end <= start:
        return []
    cursor = start.replace(minute=(start.minute // 15) * 15, second=0, microsecond=0)
    cells: list[tuple[str, str]] = []
    while cursor < end:
        cell_end = cursor + timedelta(minutes=15)
        if cell_end > start and cursor < end:
            cells.append((cursor.date().isoformat(), cursor.strftime("%H:%M")))
        cursor = cell_end
    return cells


def operational_lane_cells(schedule: dict[str, Any], availability: dict[str, Any]) -> list[dict[str, Any]]:
    cells: dict[tuple[str, str, str], dict[str, Any]] = {}
    build = schedule.get("build", {}) if isinstance(schedule.get("build"), dict) else {}
    default_source = build.get("source_mode") or build.get("source_file") or "other"
    for session in schedule.get("sessions", []):
        if not isinstance(session, dict):
            continue
        start = parse_dt(session.get("start_at"))
        end = parse_dt(session.get("end_at"))
        if not start or not end:
            continue
        source_class, label = source_label(session.get("source") or default_source)
        for day, clock in quarter_hour_cells(start, end):
            key = (day, clock, "enrollware")
            cell = cells.setdefault(key, {
                "date": day, "startTime": clock, "laneId": "enrollware",
                "result": source_class, "sourceLabel": label, "items": [],
                "reasons": ["enrollware_schedule_input", source_class],
            })
            cell["items"].append({
                "sessionId": clean(session.get("session_id")),
                "courseName": clean(session.get("course_name") or session.get("official_course_name")),
                "start": start.isoformat(), "end": end.isoformat(),
                "registeredCount": session.get("registered_count"),
            })
    for event in availability.get("events", []):
        if not isinstance(event, dict) or clean(event.get("instructor_key")).lower() != "brian":
            continue
        start = parse_dt(event.get("start"))
        end = parse_dt(event.get("end"))
        if not start or not end:
            continue
        for day, clock in quarter_hour_cells(start, end):
            key = (day, clock, "brian")
            cell = cells.setdefault(key, {
                "date": day, "startTime": clock, "laneId": "brian",
                "result": "unavailable", "sourceLabel": "Google Calendar",
                "items": [], "reasons": ["brian_google_calendar_unavailable"],
            })
            cell["items"].append({
                "title": "Unavailable", "start": start.isoformat(), "end": end.isoformat(),
                "sourceKey": clean(event.get("source_key")),
            })
    return sorted(cells.values(), key=lambda item: (item["date"], item["startTime"], item["laneId"]))


def compact_offer(item: dict[str, Any], page_key: str) -> dict[str, Any]:
    source = item.get("sourceAvailabilityBlock") if isinstance(item.get("sourceAvailabilityBlock"), dict) else {}
    return {
        "date": item.get("date"),
        "startTime": item.get("startTime"),
        "courseId": clean(item.get("courseId")),
        "courseName": item.get("courseName"),
        "courseFamily": item.get("courseFamily"),
        "pageKey": page_key,
        "result": "seated" if item.get("offerType") == "seated_class" else ("joinable" if item.get("offerType") == "joinable" else "offered"),
        "offerType": item.get("offerType"),
        "durationMinutes": item.get("durationMinutes"),
        "schedulerConsumptionEnd": item.get("schedulerConsumptionEnd"),
        "availabilityBlockId": item.get("availabilityBlockId"),
        "availabilityWindow": item.get("availabilityWindow"),
        "instructor": item.get("instructor"),
        "location": item.get("location"),
        "registrationUrl": item.get("registrationUrl"),
        "sessionId": source.get("sessionId"),
        "reasons": ["public_selectable", clean(item.get("offerType")) or "synthetic_offer"],
    }


def compact_rejection(item: dict[str, Any], page_key: str) -> dict[str, Any]:
    reasons = item.get("reasons")
    if not isinstance(reasons, list):
        reason = item.get("reason")
        reasons = [reason] if reason else []
    return {
        "date": item.get("date"),
        "startTime": item.get("startTime"),
        "courseId": clean(item.get("courseId")),
        "courseName": item.get("courseName"),
        "courseFamily": item.get("courseFamily"),
        "pageKey": page_key,
        "result": "suppressed",
        "availabilityBlockId": item.get("availabilityBlockId") or item.get("sourceAvailabilityBlockId"),
        "availabilityWindow": item.get("availabilityWindow"),
        "instructor": item.get("instructor"),
        "location": item.get("location"),
        "reasons": [clean(reason) for reason in reasons if clean(reason)],
    }


def main() -> None:
    configs = load_block_schedule_page_configs()
    today = date.today()
    start = today - timedelta(days=LOOKBACK_DAYS)
    end = today + timedelta(days=LOOKAHEAD_DAYS)

    courses: dict[str, dict[str, Any]] = {}
    cells: list[dict[str, Any]] = []
    generated_at: list[str] = []
    source_pages: dict[str, dict[str, Any]] = {}
    schedule = read_json(SCHEDULE_FUTURE)
    availability = read_json(ADMIN_AVAILABILITY)

    for page_key, config in configs.items():
        payload = apply_final_live_availability_guard(build_block_schedule_page(config))
        if payload.get("generatedAt"):
            generated_at.append(clean(payload.get("generatedAt")))

        for option in config.get("course_options", []):
            course_id = clean(option.get("course_id"))
            if not course_id:
                continue
            courses[course_id] = {
                "courseId": course_id,
                "courseName": option.get("display_label") or option.get("option_label") or course_id,
                "courseFamily": config.get("family") or page_key,
                "pageKey": page_key,
                "variant": option.get("variant"),
                "deliveryMode": option.get("delivery_mode"),
            }

        offers = [item for item in payload.get("offers", []) if isinstance(item, dict) and in_window(item.get("date"), start, end)]
        rejections = [item for item in payload.get("rejectedCourseStartTimes", []) if isinstance(item, dict) and in_window(item.get("date"), start, end)]
        cells.extend(compact_offer(item, page_key) for item in offers)
        cells.extend(compact_rejection(item, page_key) for item in rejections)
        source_pages[page_key] = {
            "generatedAt": payload.get("generatedAt"),
            "counts": payload.get("counts", {}),
            "rejectionReasonCounts": payload.get("rejectionReasonCounts", {}),
        }

    # Prefer an actual offered/seated result if the same course/time is also represented by a rejected candidate.
    rank = {"seated": 4, "joinable": 3, "offered": 2, "suppressed": 1}
    deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for cell in cells:
        key = (clean(cell.get("date")), clean(cell.get("startTime")), clean(cell.get("courseId")))
        if not all(key):
            continue
        previous = deduped.get(key)
        if previous is None or rank.get(clean(cell.get("result")), 0) >= rank.get(clean(previous.get("result")), 0):
            deduped[key] = cell

    payload = {
        "schemaVersion": "scheduling-landscape.v1",
        "generatedAt": max(generated_at) if generated_at else None,
        "window": {"startDate": start.isoformat(), "endDate": end.isoformat()},
        "timeGrid": {"startTime": "00:00", "endTime": "24:00", "stepMinutes": 15},
        "courses": sorted(courses.values(), key=lambda item: (clean(item.get("courseFamily")), clean(item.get("courseName")))),
        "lanes": [
            {"laneId": "enrollware", "label": "Enrollware Inputs", "description": "Classes entering the schedule, colored by authoritative source."},
            {"laneId": "brian", "label": "Brian Unavailable", "description": "DoNotSchedule blocks from Brian's Google Calendar."},
        ],
        "laneCells": operational_lane_cells(schedule, availability),
        "cells": sorted(deduped.values(), key=lambda item: (clean(item.get("date")), clean(item.get("startTime")), clean(item.get("courseFamily")), clean(item.get("courseName")))),
        "sourcePages": source_pages,
        "authority": "block_start_time_selector.build_block_schedule_page",
        "operationalLaneSources": {"enrollware": str(SCHEDULE_FUTURE), "brian": str(ADMIN_AVAILABILITY)},
        "note": "Internal diagnostic only. This feed mirrors selector decisions and does not change customer-facing schedule behavior.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Published {len(payload['courses'])} courses and {len(payload['cells'])} evaluated course/time cells -> {OUTPUT}")


if __name__ == "__main__":
    main()
