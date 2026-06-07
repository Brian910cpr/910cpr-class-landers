#!/usr/bin/env python3
"""Audit current Lander public offers against current Enrollware source data."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_instructor_availability_report import DEBUG_DIR, TZ, parse_dt


CUSTOMER_FACING_OFFERS_PATH = ROOT / "docs" / "data" / "customer_facing_offers.json"
PUBLIC_SCHEDULE_PATH = ROOT / "public_schedule.json"
LIVE_SCHEDULE_FUTURE_PATH = ROOT / "live-schedule_future.json"
ENROLLWARE_SOURCE_PATH = ROOT / "data" / "sessions_current.json"
REPORT_JSON_PATH = DEBUG_DIR / "lander_offer_enrollware_presence_audit.json"
REPORT_MD_PATH = DEBUG_DIR / "lander_offer_enrollware_presence_audit.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_dt(value: Any) -> datetime | None:
    return parse_dt(value)


def date_key(value: Any) -> str | None:
    dt = normalize_dt(value)
    return dt.date().isoformat() if dt else None


def time_key(value: Any) -> str | None:
    dt = normalize_dt(value)
    return dt.strftime("%H:%M") if dt else None


def normalize_text(value: Any) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or "")).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_enrollware_id(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        text = str(value)
        match = re.search(r"(?:enroll\?id=|[?&]id=)(\d+)", text)
        if match:
            return match.group(1)
        if re.fullmatch(r"\d{6,}", text):
            return text
    return None


def load_enrollware_index() -> dict[str, Any]:
    if not ENROLLWARE_SOURCE_PATH.exists():
        return {
            "available": False,
            "source_path": str(ENROLLWARE_SOURCE_PATH),
            "session_count": 0,
            "by_session_id": {},
            "by_fallback_key": {},
        }
    data = load_json(ENROLLWARE_SOURCE_PATH)
    by_session_id: dict[str, dict[str, Any]] = {}
    by_fallback_key: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for session in data.get("sessions", []):
        if not isinstance(session, dict):
            continue
        course = session.get("course", {}) if isinstance(session.get("course"), dict) else {}
        location = session.get("location", {}) if isinstance(session.get("location"), dict) else {}
        start = session.get("start_datetime") or session.get("start")
        session_id = str(session.get("session_id") or "")
        course_id = str(course.get("course_id") or course.get("course_number") or "")
        key = (
            course_id,
            str(date_key(start) or ""),
            str(time_key(start) or ""),
            normalize_text(location.get("name") or location.get("display_name") or session.get("location_name") or ""),
        )
        normalized = {
            "session_id": session_id,
            "course_id": course_id,
            "course_name": course.get("course_name_raw") or course.get("mapped_clean_title") or session.get("mapped_clean_title"),
            "start_datetime": start,
            "date": date_key(start),
            "start_time": time_key(start),
            "location": location.get("name") or location.get("display_name") or session.get("location_name"),
        }
        if session_id:
            by_session_id[session_id] = normalized
        if course_id and key[1] and key[2]:
            by_fallback_key.setdefault(key, []).append(normalized)
    build = data.get("build") if isinstance(data.get("build"), dict) else {}
    return {
        "available": True,
        "source_path": str(ENROLLWARE_SOURCE_PATH),
        "generated_at": build.get("generated_at"),
        "session_count": len(by_session_id),
        "by_session_id": by_session_id,
        "by_fallback_key": by_fallback_key,
    }


def customer_facing_offer_records() -> list[dict[str, Any]]:
    if not CUSTOMER_FACING_OFFERS_PATH.exists():
        return []
    data = load_json(CUSTOMER_FACING_OFFERS_PATH)
    records: list[dict[str, Any]] = []
    for course in data.get("courses", []):
        if not isinstance(course, dict):
            continue
        for offer in course.get("offered_options", []):
            if not isinstance(offer, dict):
                continue
            records.append(
                {
                    "source_file": str(CUSTOMER_FACING_OFFERS_PATH),
                    "source_type": "customer_facing_offer",
                    "offer_key": offer.get("offer_slug") or offer.get("page_slug"),
                    "session_id": extract_enrollware_id(offer.get("enrollware_class_id"), offer.get("enrollware_enroll_url")),
                    "course_id": None,
                    "course_key": offer.get("course_key") or course.get("course_key"),
                    "course_title": offer.get("course_title") or course.get("course_title"),
                    "start_datetime": offer.get("start_time"),
                    "date": date_key(offer.get("start_time")) or offer.get("date"),
                    "start_time": time_key(offer.get("start_time")),
                    "location": offer.get("location_name") or offer.get("location_address"),
                    "instructor": offer.get("instructor_key") or offer.get("instructor"),
                    "registration_url": offer.get("enrollware_enroll_url"),
                    "raw_status": offer.get("session_status"),
                }
            )
    return records


def public_schedule_records() -> list[dict[str, Any]]:
    if not PUBLIC_SCHEDULE_PATH.exists():
        return []
    data = load_json(PUBLIC_SCHEDULE_PATH)
    records: list[dict[str, Any]] = []
    for session in data.get("sessions", []):
        if not isinstance(session, dict):
            continue
        start = session.get("start")
        records.append(
            {
                "source_file": str(PUBLIC_SCHEDULE_PATH),
                "source_type": "public_schedule_session",
                "offer_key": session.get("session_id"),
                "session_id": extract_enrollware_id(session.get("register_url")),
                "course_id": None,
                "course_key": None,
                "course_title": session.get("course"),
                "start_datetime": start,
                "date": date_key(start),
                "start_time": time_key(start),
                "location": session.get("location"),
                "instructor": session.get("instructor"),
                "registration_url": session.get("register_url"),
                "raw_status": None,
            }
        )
    return records


def source_files_inspected() -> list[dict[str, Any]]:
    files = [CUSTOMER_FACING_OFFERS_PATH, PUBLIC_SCHEDULE_PATH, LIVE_SCHEDULE_FUTURE_PATH, ENROLLWARE_SOURCE_PATH]
    inspected = []
    for path in files:
        info = {"path": str(path), "exists": path.exists(), "used": False, "note": ""}
        if path == LIVE_SCHEDULE_FUTURE_PATH and path.exists():
            try:
                load_json(path)
                info["note"] = "Valid JSON, but not used by this first audit pass."
            except Exception:
                info["note"] = "Not valid JSON; skipped."
        inspected.append(info)
    return inspected


def classify_offer(offer: dict[str, Any], enrollware: dict[str, Any]) -> dict[str, Any]:
    if not enrollware.get("available"):
        return {
            "enrollware_presence_status": "source_unavailable",
            "reason": "Enrollware source data is unavailable.",
            "matched_enrollware_key": None,
            "recommended_action": "needs_review",
        }
    session_id = offer.get("session_id")
    if session_id:
        match = enrollware["by_session_id"].get(str(session_id))
        if match:
            return {
                "enrollware_presence_status": "present_in_enrollware",
                "reason": "Matched Enrollware session ID from public registration URL/class ID.",
                "matched_enrollware_key": str(session_id),
                "recommended_action": "keep",
                "matched_enrollware_session": match,
            }
        return {
            "enrollware_presence_status": "missing_from_enrollware",
            "reason": "Public offer references an Enrollware session ID that is not present in current source data.",
            "matched_enrollware_key": str(session_id),
            "recommended_action": "remove_from_public_output",
        }
    if offer.get("course_id") and offer.get("date") and offer.get("start_time"):
        key = (
            str(offer.get("course_id")),
            str(offer.get("date")),
            str(offer.get("start_time")),
            normalize_text(offer.get("location")),
        )
        matches = enrollware["by_fallback_key"].get(key, [])
        if len(matches) == 1:
            return {
                "enrollware_presence_status": "present_in_enrollware",
                "reason": "Matched by course ID, date, start time, and location.",
                "matched_enrollware_key": matches[0].get("session_id"),
                "recommended_action": "keep",
                "matched_enrollware_session": matches[0],
            }
        if len(matches) > 1:
            return {
                "enrollware_presence_status": "ambiguous_match",
                "reason": "Multiple Enrollware sessions match fallback keys.",
                "matched_enrollware_key": ",".join(str(match.get("session_id")) for match in matches),
                "recommended_action": "needs_review",
            }
    return {
        "enrollware_presence_status": "missing_from_enrollware",
        "reason": "No Enrollware session ID is present and no exact fallback match could be made.",
        "matched_enrollware_key": None,
        "recommended_action": "remove_from_public_output",
    }


def build_report() -> dict[str, Any]:
    enrollware = load_enrollware_index()
    offers = customer_facing_offer_records() + public_schedule_records()
    audited = []
    for offer in offers:
        result = classify_offer(offer, enrollware)
        audited.append({**offer, **result})
    status_counts = Counter(item["enrollware_presence_status"] for item in audited)
    action_counts = Counter(item["recommended_action"] for item in audited)
    inspected = source_files_inspected()
    for item in inspected:
        if item["path"] in {str(CUSTOMER_FACING_OFFERS_PATH), str(PUBLIC_SCHEDULE_PATH), str(ENROLLWARE_SOURCE_PATH)}:
            item["used"] = item["exists"]
    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "source_files_inspected": inspected,
        "enrollware_source": {
            "path": enrollware.get("source_path"),
            "available": enrollware.get("available"),
            "generated_at": enrollware.get("generated_at"),
            "session_count": enrollware.get("session_count", 0),
        },
        "summary": {
            "total_lander_offers_checked": len(audited),
            "present": status_counts.get("present_in_enrollware", 0),
            "missing": status_counts.get("missing_from_enrollware", 0),
            "ambiguous": status_counts.get("ambiguous_match", 0),
            "source_unavailable": status_counts.get("source_unavailable", 0),
            "not_checked": status_counts.get("not_checked", 0),
            "recommended_removals": action_counts.get("remove_from_public_output", 0),
            "needs_review": action_counts.get("needs_review", 0),
            "keep": action_counts.get("keep", 0),
        },
        "offers": audited,
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    missing_examples = [
        offer
        for offer in report["offers"]
        if offer["enrollware_presence_status"] == "missing_from_enrollware"
    ][:20]
    lines = [
        "# Lander Offer Enrollware Presence Audit",
        "",
        "> REPORT ONLY - no public pages, links, CTAs, or schedule files were modified.",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Enrollware source: {report['enrollware_source']['path']}",
        f"- Enrollware source available: {report['enrollware_source']['available']}",
        f"- Enrollware session count: {report['enrollware_source']['session_count']}",
        f"- Total Lander offers checked: {report['summary']['total_lander_offers_checked']}",
        f"- Present: {report['summary']['present']}",
        f"- Missing: {report['summary']['missing']}",
        f"- Ambiguous: {report['summary']['ambiguous']}",
        f"- Source unavailable: {report['summary']['source_unavailable']}",
        f"- Not checked: {report['summary']['not_checked']}",
        f"- Recommended removals: {report['summary']['recommended_removals']}",
        f"- Needs review: {report['summary']['needs_review']}",
        "",
        "## Source Files Inspected",
        "",
    ]
    for source in report["source_files_inspected"]:
        lines.append(f"- {source['path']} - exists={source['exists']} used={source['used']} {source['note']}".rstrip())
    lines.extend(["", "## Missing/Stale Examples", ""])
    if not missing_examples:
        lines.append("No missing/stale offers found.")
    for offer in missing_examples:
        lines.append(
            f"- {offer['source_type']} {offer.get('offer_key')} - {offer.get('date')} {offer.get('start_time')} - {offer.get('course_title')}"
        )
        lines.append(f"  - Reason: {offer['reason']}")
        lines.append(f"  - Recommended action: {offer['recommended_action']}")
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    report = build_report()
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
