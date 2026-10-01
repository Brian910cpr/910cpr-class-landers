from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
import subprocess
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from scripts.block_start_time_selector import build_block_schedule_page, load_block_schedule_page_configs
from scripts.build_bls_block_schedule_pilot import apply_final_live_availability_guard
from scripts.canonical_scheduling_demand import load_publication_demand, resolve_canonical_demand

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
        parsed = datetime.fromisoformat(clean(value).replace("Z", "+00:00"))
        return parsed.astimezone(ZoneInfo("America/New_York")) if parsed.tzinfo else parsed.replace(tzinfo=ZoneInfo("America/New_York"))
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
        "attachedToSessionId": item.get("attached_to_session_id"),
        "scheduleRole": item.get("schedule_role"),
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



def daily_truth(schedule: dict[str, Any], availability: dict[str, Any], demand: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Readable facts above the matrix. Public output contains no participants."""
    days: dict[str, dict[str, Any]] = {}
    def day_for(start: datetime) -> dict[str, Any]:
        return days.setdefault(start.date().isoformat(), {"hardBlocks": [], "classes": []})
    resolved, _ = resolve_canonical_demand(schedule.get("sessions", []), demand.get("sessions", []))
    seen = set()
    for row in resolved:
        start, end = parse_dt(row.get("start_at")), parse_dt(row.get("consumption_end_at") or row.get("end_at"))
        if not start or not end:
            continue
        sid = clean(row.get("session_id"))
        seen.add(sid)
        day_for(start)["classes"].append({
            "externalClassId": sid, "canonicalSessionId": row.get("canonical_session_id"),
            "courseName": row.get("course_name"), "start": start.isoformat(), "end": end.isoformat(),
            "registeredCount": row.get("active_registration_count") if row.get("count_available") else None,
            "demandStatus": row.get("demand_status"), "source": "Current Enrollware class",
            "workspaceStatus": row.get("workspace_projection_status"),
        })
    for row in demand.get("sessions", []):
        if clean(row.get("external_class_id")) in seen:
            continue
        start, end = parse_dt(row.get("consumption_start_at") or row.get("start_at")), parse_dt(row.get("consumption_end_at") or row.get("end_at"))
        if not start or not end:
            continue
        day_for(start)["classes"].append({
            "externalClassId": row.get("external_class_id"), "canonicalSessionId": row.get("canonical_session_id"),
            "courseName": row.get("course_name"), "start": start.isoformat(), "end": end.isoformat(),
            "registeredCount": row.get("active_registration_count"),
            "demandStatus": row.get("demand_status"), "source": "Canonical commitment",
            "workspaceStatus": row.get("workspace_projection_status"),
        })
        if row.get("session_status") in ("scheduled", "active"):
            day_for(start)["hardBlocks"].append({
                "label": row.get("course_name") or "Committed class", "start": start.isoformat(),
                "end": end.isoformat(), "location": row.get("location_name"),
                "instructor": row.get("lead_instructor_name"), "source": "Canonical class",
            })
    for event in availability.get("events", []):
        if event.get("instructor_key") != "brian":
            continue
        start, end = parse_dt(event.get("start")), parse_dt(event.get("end"))
        if not start or not end or end <= start:
            continue
        cursor = start.replace(hour=0, minute=0, second=0, microsecond=0)
        while cursor < end:
            if cursor + timedelta(days=1) > start:
                day_for(cursor)["hardBlocks"].append({
                    "label": "Brian unavailable", "start": start.isoformat(), "end": end.isoformat(),
                    "source": event.get("source_key"),
                })
            cursor += timedelta(days=1)
    for day in days.values():
        for key in ("hardBlocks", "classes"):
            day[key].sort(key=lambda item: item["start"])
    return days

def publication_contradictions(cells: list[dict[str, Any]], truth: dict[str, Any]) -> list[dict[str, Any]]:
    """Independent last-mile alarm: the matrix must never conceal invalid offers."""
    issues = []
    for cell in cells:
        if cell.get("result") not in ("seated", "offered", "joinable"):
            continue
        day = clean(cell.get("date"))
        facts = truth.get(day, {})
        classes = facts.get("classes", [])
        known_ids = {clean(row.get("externalClassId") or row.get("canonicalSessionId")) for row in classes}
        if classes and cell.get("result") != "seated" and not (
            cell.get("scheduleRole") == "barnacle" and clean(cell.get("attachedToSessionId")) in known_ids
        ):
            issues.append({"date":day,"code":"ORPHAN_SYNTHETIC_OFFER","blocksSynthesis":True,
                           "reason":f"{cell.get('startTime')} {cell.get('courseName')}: no relationship to a real class"})
        start = parse_dt(f"{day}T{cell.get('startTime')}:00")
        if not start:
            continue
        if start.tzinfo is None:
            start = start.replace(tzinfo=ZoneInfo("America/New_York"))
        end = parse_dt(cell.get("schedulerConsumptionEnd")) or start + timedelta(minutes=float(cell.get("durationMinutes") or 0))
        if end.tzinfo is None:
            end = end.replace(tzinfo=ZoneInfo("America/New_York"))
        instructor = clean(cell.get("instructor")).lower().replace(".", "")
        for block in facts.get("hardBlocks", []):
            # Personal busy blocks concern Brian; canonical offsite commitments
            # also name their instructor. Never infer collisions for other staff.
            same_instructor = (instructor in ("brian", "brian ennis", "b ennis") and block.get("source") == "brian_do_not_schedule") or (
                instructor and instructor == clean(block.get("instructor")).lower().replace(".", ""))
            block_start, block_end = parse_dt(block.get("start")), parse_dt(block.get("end"))
            if same_instructor and block_start and block_end and start < block_end and end > block_start:
                issues.append({"date":day,"code":"HARD_BLOCK_COLLISION","blocksSynthesis":True,
                    "reason":f"{cell.get('startTime')} {cell.get('courseName')} overlaps {block.get('label')} ({block.get('start')} to {block.get('end')})"})
                break
    return issues


def main() -> None:
    configs = load_block_schedule_page_configs()
    today = date.today()
    start = today - timedelta(days=LOOKBACK_DAYS)
    end = today + timedelta(days=LOOKAHEAD_DAYS)

    courses: dict[str, dict[str, Any]] = {}
    cells: list[dict[str, Any]] = []
    generated_at: list[str] = []
    source_pages: dict[str, dict[str, Any]] = {}
    issues: dict[str, dict[str, Any]] = {}
    schedule = read_json(SCHEDULE_FUTURE)
    availability = read_json(ADMIN_AVAILABILITY)

    for page_key, config in configs.items():
        payload = apply_final_live_availability_guard(build_block_schedule_page(config))
        for issue in payload.get("reconciliationIssues", []):
            issues[json.dumps(issue, sort_keys=True)] = issue
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

    truth = daily_truth(schedule, availability, load_publication_demand(ROOT))
    for issue in publication_contradictions(list(deduped.values()), truth):
        issues[json.dumps(issue, sort_keys=True)] = issue
    payload = {
        "schemaVersion": "scheduling-landscape.v1",
        "generatedAt": max(generated_at) if generated_at else None,
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "buildId": subprocess.check_output(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT, text=True).strip(),
        "pageId": "scheduling-landscape",
        "timezone": "America/New_York",
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
        "reconciliationIssues": list(issues.values()),
        "dailyTruth": truth,
        "authority": "block_start_time_selector.build_block_schedule_page",
        "operationalLaneSources": {"enrollware": str(SCHEDULE_FUTURE), "brian": str(ADMIN_AVAILABILITY)},
        "note": "Internal diagnostic only. This feed mirrors selector decisions and does not change customer-facing schedule behavior.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Published {len(payload['courses'])} courses and {len(payload['cells'])} evaluated course/time cells -> {OUTPUT}")


if __name__ == "__main__":
    main()
