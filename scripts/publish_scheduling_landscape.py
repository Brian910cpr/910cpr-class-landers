from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from scripts.block_start_time_selector import build_block_schedule_page, load_block_schedule_page_configs
from scripts.build_bls_block_schedule_pilot import apply_final_live_availability_guard

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "data" / "admin" / "scheduling_landscape.json"
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
        "timeGrid": {"startTime": "08:00", "endTime": "19:00", "stepMinutes": 15},
        "courses": sorted(courses.values(), key=lambda item: (clean(item.get("courseFamily")), clean(item.get("courseName")))),
        "cells": sorted(deduped.values(), key=lambda item: (clean(item.get("date")), clean(item.get("startTime")), clean(item.get("courseFamily")), clean(item.get("courseName")))),
        "sourcePages": source_pages,
        "authority": "block_start_time_selector.build_block_schedule_page",
        "note": "Internal diagnostic only. This feed mirrors selector decisions and does not change customer-facing schedule behavior.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Published {len(payload['courses'])} courses and {len(payload['cells'])} evaluated course/time cells -> {OUTPUT}")


if __name__ == "__main__":
    main()
