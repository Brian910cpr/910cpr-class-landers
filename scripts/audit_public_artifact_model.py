#!/usr/bin/env python3
"""Audit public artifact types against the Class Lander vs Hub Offer model."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_instructor_availability_report import DEBUG_DIR, TZ, parse_dt


CLASSES_DIR = ROOT / "docs" / "classes"
CUSTOMER_FACING_OFFERS_PATH = ROOT / "docs" / "data" / "customer_facing_offers.json"
PUBLIC_SCHEDULE_PATH = ROOT / "public_schedule.json"
LIVE_SCHEDULE_FUTURE_PATH = ROOT / "live-schedule_future.json"
ENROLLWARE_SOURCE_PATH = ROOT / "data" / "sessions_current.json"
REPORT_JSON_PATH = DEBUG_DIR / "public_artifact_model_audit.json"
REPORT_MD_PATH = DEBUG_DIR / "public_artifact_model_audit.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_text(value: Any) -> str:
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


def date_part(value: Any) -> str | None:
    dt = parse_dt(value)
    return dt.date().isoformat() if dt else None


def time_part(value: Any) -> str | None:
    dt = parse_dt(value)
    return dt.strftime("%H:%M") if dt else None


def load_enrollware_sessions() -> dict[str, Any]:
    if not ENROLLWARE_SOURCE_PATH.exists():
        return {"available": False, "sessions": {}, "source_path": str(ENROLLWARE_SOURCE_PATH)}
    data = load_json(ENROLLWARE_SOURCE_PATH)
    sessions: dict[str, dict[str, Any]] = {}
    for session in data.get("sessions", []):
        if not isinstance(session, dict):
            continue
        session_id = str(session.get("session_id") or "")
        if not session_id:
            continue
        course = session.get("course", {}) if isinstance(session.get("course"), dict) else {}
        location = session.get("location", {}) if isinstance(session.get("location"), dict) else {}
        start = session.get("start_datetime") or session.get("start")
        sessions[session_id] = {
            "session_id": session_id,
            "course_id": str(course.get("course_id") or course.get("course_number") or ""),
            "course_title": course.get("mapped_clean_title") or course.get("course_name_raw") or session.get("mapped_clean_title"),
            "start_datetime": start,
            "end_datetime": session.get("end_datetime") or session.get("end"),
            "date": date_part(start),
            "start_time": time_part(start),
            "location": location.get("name") or location.get("display_name") or session.get("location_name"),
            "instructor": (session.get("staffing") or {}).get("instructor") if isinstance(session.get("staffing"), dict) else None,
        }
    build = data.get("build") if isinstance(data.get("build"), dict) else {}
    return {
        "available": True,
        "sessions": sessions,
        "source_path": str(ENROLLWARE_SOURCE_PATH),
        "generated_at": build.get("generated_at"),
    }


def class_lander_artifacts() -> list[dict[str, Any]]:
    if not CLASSES_DIR.exists():
        return []
    artifacts = []
    for path in sorted(CLASSES_DIR.glob("*.html")):
        session_id = path.stem
        artifacts.append(
            {
                "artifact_key": f"class:{session_id}",
                "public_artifact_type": "class_lander",
                "path": str(path),
                "session_id": session_id,
                "course_key": None,
                "course_title": None,
                "date": None,
                "start_time": None,
                "location": None,
                "instructor": None,
            }
        )
    return artifacts


def hub_offer_artifacts() -> list[dict[str, Any]]:
    if not CUSTOMER_FACING_OFFERS_PATH.exists():
        return []
    data = load_json(CUSTOMER_FACING_OFFERS_PATH)
    artifacts = []
    for course in data.get("courses", []):
        if not isinstance(course, dict):
            continue
        for offer in course.get("offered_options", []):
            if not isinstance(offer, dict):
                continue
            start = offer.get("start_time")
            key = offer.get("offer_slug") or offer.get("page_slug") or f"{offer.get('course_key')}:{start}"
            artifacts.append(
                {
                    "artifact_key": f"hub_offer:{key}",
                    "public_artifact_type": "hub_offer",
                    "path": str(CUSTOMER_FACING_OFFERS_PATH),
                    "session_id": extract_enrollware_id(offer.get("enrollware_class_id"), offer.get("enrollware_enroll_url")),
                    "course_key": offer.get("course_key") or course.get("course_key"),
                    "course_title": offer.get("course_title") or course.get("course_title"),
                    "date": date_part(start) or offer.get("date"),
                    "start_time": time_part(start),
                    "location": offer.get("location_name") or offer.get("location_address"),
                    "instructor": offer.get("instructor_key") or offer.get("instructor"),
                    "offer_status": offer.get("session_status"),
                    "offer_type": offer.get("offer_type"),
                }
            )
    return artifacts


def schedule_offer_artifacts() -> list[dict[str, Any]]:
    if not PUBLIC_SCHEDULE_PATH.exists():
        return []
    data = load_json(PUBLIC_SCHEDULE_PATH)
    artifacts = []
    for session in data.get("sessions", []):
        if not isinstance(session, dict):
            continue
        start = session.get("start")
        enrollware_id = extract_enrollware_id(session.get("register_url"))
        key = enrollware_id or session.get("session_id") or f"{session.get('course')}:{start}"
        artifacts.append(
            {
                "artifact_key": f"schedule:{key}",
                "public_artifact_type": "schedule_offer",
                "path": str(PUBLIC_SCHEDULE_PATH),
                "session_id": enrollware_id,
                "course_key": None,
                "course_title": session.get("course"),
                "date": date_part(start),
                "start_time": time_part(start),
                "location": session.get("location"),
                "instructor": session.get("instructor"),
                "registration_url": session.get("register_url"),
            }
        )
    return artifacts


def classify_artifact(artifact: dict[str, Any], enrollware: dict[str, Any]) -> dict[str, Any]:
    sessions = enrollware.get("sessions", {})
    session_id = artifact.get("session_id")
    matched = sessions.get(str(session_id)) if session_id else None

    if artifact["public_artifact_type"] == "class_lander":
        if not enrollware.get("available"):
            return {
                **artifact,
                "enrollware_backing_status": "unknown",
                "recommended_public_action": "needs_review",
                "model_flags": ["not_public_ready"],
                "matched_enrollware_key": None,
            }
        if matched:
            return {
                **artifact,
                **{k: artifact.get(k) or matched.get(k) for k in ["course_title", "date", "start_time", "location", "instructor"]},
                "enrollware_backing_status": "backed_by_current_enrollware",
                "recommended_public_action": "keep_class_lander",
                "model_flags": [],
                "matched_enrollware_key": session_id,
            }
        return {
            **artifact,
            "enrollware_backing_status": "missing_from_current_enrollware",
            "recommended_public_action": "remove_or_redirect_class_lander",
            "model_flags": ["stale_class_lander", "remove_or_redirect_required", "not_public_ready"],
            "matched_enrollware_key": None,
        }

    if artifact["public_artifact_type"] == "hub_offer":
        if session_id and matched:
            status = "backed_by_current_enrollware"
        elif artifact.get("offer_status") == "proposed" or not session_id:
            status = "generated_seed_candidate"
        else:
            status = "missing_from_current_enrollware"
        return {
            **artifact,
            "enrollware_backing_status": status,
            "recommended_public_action": "show_as_hub_offer_only" if status != "missing_from_current_enrollware" else "suppress_until_enrollware_backed",
            "model_flags": ["hub_offer_only"],
            "matched_enrollware_key": session_id if matched else None,
        }

    if artifact["public_artifact_type"] == "schedule_offer":
        if matched:
            status = "backed_by_current_enrollware"
            action = "show_as_hub_offer_only"
        else:
            status = "missing_from_current_enrollware"
            action = "suppress_until_enrollware_backed"
        return {
            **artifact,
            "enrollware_backing_status": status,
            "recommended_public_action": action,
            "model_flags": [],
            "matched_enrollware_key": session_id if matched else None,
        }

    return {
        **artifact,
        "enrollware_backing_status": "unknown",
        "recommended_public_action": "needs_review",
        "model_flags": [],
        "matched_enrollware_key": None,
    }


def sister_group_key(artifact: dict[str, Any]) -> str:
    return "|".join(
        [
            str(artifact.get("date") or ""),
            str(artifact.get("start_time") or ""),
            clean_text(artifact.get("location")),
            clean_text(artifact.get("instructor")),
        ]
    )


def detect_sister_groups(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for artifact in artifacts:
        key = sister_group_key(artifact)
        if key.strip("|"):
            grouped[key].append(artifact)
    sister_sets = []
    for key, items in grouped.items():
        artifact_types = sorted({str(item.get("public_artifact_type")) for item in items})
        session_ids = sorted({str(item.get("matched_enrollware_key") or item.get("session_id") or "") for item in items if item.get("matched_enrollware_key") or item.get("session_id")})
        if len(items) > 1 and (len(artifact_types) > 1 or len(session_ids) <= 1):
            statuses = Counter(str(item.get("enrollware_backing_status")) for item in items)
            sister_sets.append(
                {
                    "group_key": key,
                    "artifact_count": len(items),
                    "artifact_types": artifact_types,
                    "session_ids": session_ids,
                    "backing_status_counts": dict(sorted(statuses.items())),
                    "recommended_group_action": "age_together_if_source_missing"
                    if statuses.get("missing_from_current_enrollware")
                    else "review_before_creating_sister_class_landers",
                    "examples": [
                        {
                            "artifact_key": item.get("artifact_key"),
                            "public_artifact_type": item.get("public_artifact_type"),
                            "enrollware_backing_status": item.get("enrollware_backing_status"),
                            "recommended_public_action": item.get("recommended_public_action"),
                        }
                        for item in items[:10]
                    ],
                }
            )
    return sorted(sister_sets, key=lambda item: item["artifact_count"], reverse=True)


def source_files_inspected() -> list[dict[str, Any]]:
    files = [CUSTOMER_FACING_OFFERS_PATH, PUBLIC_SCHEDULE_PATH, LIVE_SCHEDULE_FUTURE_PATH, CLASSES_DIR, ENROLLWARE_SOURCE_PATH]
    inspected = []
    for path in files:
        info = {"path": str(path), "exists": path.exists(), "used": False, "note": ""}
        if path == LIVE_SCHEDULE_FUTURE_PATH and path.exists():
            try:
                load_json(path)
                info["note"] = "Valid JSON, but not used in this first model audit."
            except Exception:
                info["note"] = "Not valid JSON; skipped."
        inspected.append(info)
    for info in inspected:
        if info["path"] in {str(CUSTOMER_FACING_OFFERS_PATH), str(PUBLIC_SCHEDULE_PATH), str(CLASSES_DIR), str(ENROLLWARE_SOURCE_PATH)}:
            info["used"] = info["exists"]
    return inspected


def build_report() -> dict[str, Any]:
    enrollware = load_enrollware_sessions()
    raw = class_lander_artifacts() + hub_offer_artifacts() + schedule_offer_artifacts()
    artifacts = [classify_artifact(artifact, enrollware) for artifact in raw]
    type_counts = Counter(str(item.get("public_artifact_type")) for item in artifacts)
    backing_counts = Counter(str(item.get("enrollware_backing_status")) for item in artifacts)
    action_counts = Counter(str(item.get("recommended_public_action")) for item in artifacts)
    sister_sets = detect_sister_groups(artifacts)
    class_landers = [item for item in artifacts if item["public_artifact_type"] == "class_lander"]
    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "source_files_inspected": source_files_inspected(),
        "enrollware_source": {
            "path": enrollware.get("source_path"),
            "available": enrollware.get("available"),
            "generated_at": enrollware.get("generated_at"),
            "session_count": len(enrollware.get("sessions", {})),
        },
        "summary": {
            "total_artifacts": len(artifacts),
            "artifact_type_counts": dict(sorted(type_counts.items())),
            "enrollware_backing_status_counts": dict(sorted(backing_counts.items())),
            "recommended_public_action_counts": dict(sorted(action_counts.items())),
            "class_landers_enrollware_backed": sum(1 for item in class_landers if item["enrollware_backing_status"] == "backed_by_current_enrollware"),
            "class_landers_stale_missing": sum(1 for item in class_landers if item["enrollware_backing_status"] == "missing_from_current_enrollware"),
            "hub_only_offers": action_counts.get("show_as_hub_offer_only", 0),
            "recommended_removals_or_redirects": action_counts.get("remove_or_redirect_class_lander", 0),
            "recommended_suppress_until_backed": action_counts.get("suppress_until_enrollware_backed", 0),
            "sister_conflict_groups_detected": len(sister_sets),
        },
        "artifacts": artifacts,
        "sister_conflict_groups": sister_sets,
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    stale_class = [
        item for item in report["artifacts"]
        if item["public_artifact_type"] == "class_lander" and item["enrollware_backing_status"] == "missing_from_current_enrollware"
    ][:20]
    hub_only = [
        item for item in report["artifacts"]
        if item["recommended_public_action"] == "show_as_hub_offer_only"
    ][:20]
    lines = [
        "# Public Artifact Model Audit",
        "",
        "> REPORT ONLY - no public pages, class landers, links, CTAs, or schedule files were modified.",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Enrollware source: {report['enrollware_source']['path']}",
        f"- Enrollware source available: {report['enrollware_source']['available']}",
        f"- Enrollware session count: {report['enrollware_source']['session_count']}",
        f"- Total artifacts: {report['summary']['total_artifacts']}",
        f"- Artifact types: {json.dumps(report['summary']['artifact_type_counts'], sort_keys=True)}",
        f"- Enrollware backing: {json.dumps(report['summary']['enrollware_backing_status_counts'], sort_keys=True)}",
        f"- Recommended actions: {json.dumps(report['summary']['recommended_public_action_counts'], sort_keys=True)}",
        f"- Class landers Enrollware-backed: {report['summary']['class_landers_enrollware_backed']}",
        f"- Class landers stale/missing: {report['summary']['class_landers_stale_missing']}",
        f"- Hub-only offers: {report['summary']['hub_only_offers']}",
        f"- Sister/conflict groups detected: {report['summary']['sister_conflict_groups_detected']}",
        "",
        "## Source Files Inspected",
        "",
    ]
    for source in report["source_files_inspected"]:
        lines.append(f"- {source['path']} - exists={source['exists']} used={source['used']} {source['note']}".rstrip())
    lines.extend(["", "## Stale Class Lander Examples", ""])
    if not stale_class:
        lines.append("No stale class lander examples found.")
    for item in stale_class:
        lines.append(f"- {item['path']} - session {item['session_id']}")
        lines.append(f"  - Action: {item['recommended_public_action']}")
        lines.append(f"  - Flags: {', '.join(item['model_flags'])}")
    lines.extend(["", "## Hub-Only Offer Examples", ""])
    if not hub_only:
        lines.append("No hub-only offer examples found.")
    for item in hub_only:
        lines.append(f"- {item['artifact_key']} - {item.get('date')} {item.get('start_time')} - {item.get('course_title')}")
        lines.append(f"  - Artifact type: {item['public_artifact_type']}")
        lines.append(f"  - Backing: {item['enrollware_backing_status']}")
    lines.extend(["", "## Sister / Conflict Examples", ""])
    if not report["sister_conflict_groups"]:
        lines.append("No sister/conflict groups detected.")
    for group in report["sister_conflict_groups"][:20]:
        lines.append(f"- {group['group_key']} - {group['artifact_count']} artifacts")
        lines.append(f"  - Types: {', '.join(group['artifact_types'])}")
        lines.append(f"  - Action: {group['recommended_group_action']}")
        lines.append(f"  - Backing: {json.dumps(group['backing_status_counts'], sort_keys=True)}")
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
