from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AVAILABILITY_PATH = ROOT / "docs" / "data" / "instructor_availability.json"
PROFILES_PATH = ROOT / "docs" / "data" / "instructor_profiles.json"
RANGES_PATH = ROOT / "docs" / "data" / "appointment_range_registry.json"
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
RECOMMENDATIONS_PATH = ROOT / "docs" / "data" / "inventory_recommendations.json"
AUDIT_PATH = ROOT / "debug" / "inventory_resolver_v1_audit.json"

# Resolver V1 estimates only. Keep these obvious and editable.
COURSE_DURATION_ESTIMATES = {
    "HeartCode": 60,
    "BLS": 150,
    "Heartsaver CPR/AED": 90,
    "Heartsaver First Aid CPR/AED": 150,
    "ACLS Renewal": 240,
    "PALS Renewal": 240,
    "ACLS Initial": 300,
    "PALS Initial": 300,
}

BUSINESS_USEFULNESS = {
    "ACLS Initial": 90,
    "PALS Initial": 90,
    "ACLS Renewal": 85,
    "PALS Renewal": 85,
    "BLS": 75,
    "Heartsaver First Aid CPR/AED": 65,
    "Heartsaver CPR/AED": 55,
    "HeartCode": 45,
}

FAMILY_ALIASES = {
    "ACLS": ["ACLS Initial", "ACLS Renewal"],
    "PALS": ["PALS Initial", "PALS Renewal"],
    "BLS": ["BLS"],
    "Heartsaver": ["Heartsaver CPR/AED", "Heartsaver First Aid CPR/AED"],
    "HeartCode": ["HeartCode"],
}


@dataclass(frozen=True)
class Session:
    session_id: str
    instructor: str
    date: str
    location: str
    start_minutes: int
    end_minutes: int
    course_name: str


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def parse_time(value: str | None) -> int | None:
    if not value:
        return None
    parts = str(value).split(":")
    if len(parts) < 2:
        return None
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return None
    return hour * 60 + minute


def format_time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "item"


def normalize(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def names_match(block_instructor: str, session_instructor: str, profiles: dict[str, Any]) -> bool:
    block_norm = normalize(block_instructor)
    session_norm = normalize(session_instructor)
    if not block_norm or not session_norm:
        return False
    if block_norm in session_norm or session_norm in block_norm:
        return True
    for profile in profiles.get("instructors", []):
        names = [profile.get("display_name", ""), profile.get("short_name", "")]
        normalized_names = [normalize(name) for name in names if name]
        if block_norm in normalized_names and any(name and name in session_norm for name in normalized_names):
            return True
    return False


def locations_match(block_location: str, session_location: str) -> bool:
    block_norm = normalize(block_location)
    session_norm = normalize(session_location)
    if not block_norm or not session_norm:
        return False
    return block_norm in session_norm or session_norm in block_norm or "wilmingtonshipyard" in block_norm + session_norm


def profile_for(instructor: str, profiles: dict[str, Any]) -> dict[str, Any]:
    instructor_norm = normalize(instructor)
    for profile in profiles.get("instructors", []):
        if instructor_norm in {normalize(profile.get("display_name")), normalize(profile.get("short_name"))}:
            return profile
    return {}


def load_sessions(warnings: list[str]) -> list[Session]:
    schedule = load_json(SCHEDULE_PATH, {"sessions": []})
    sessions: list[Session] = []
    for raw in schedule.get("sessions", []):
        start = parse_iso_datetime(raw.get("start_at"))
        end = parse_iso_datetime(raw.get("end_at"))
        if not start or not end:
            continue
        instructor = raw.get("lead_instructor_name") or raw.get("instructor") or ""
        if not instructor:
            continue
        sessions.append(
            Session(
                session_id=str(raw.get("session_id") or ""),
                instructor=instructor,
                date=start.date().isoformat(),
                location=raw.get("location_display") or raw.get("location_name") or "",
                start_minutes=start.hour * 60 + start.minute,
                end_minutes=end.hour * 60 + end.minute,
                course_name=raw.get("course_name") or raw.get("official_course_name") or "",
            )
        )
    if not sessions:
        warnings.append("No existing sessions with instructor detail were loaded from docs/data/schedule_future.json.")
    return sessions


def occupied_segments(block: dict[str, Any], sessions: list[Session], profiles: dict[str, Any]) -> list[Session]:
    return [
        session
        for session in sessions
        if session.date == block.get("date")
        and names_match(str(block.get("instructor", "")), session.instructor, profiles)
        and locations_match(str(block.get("location", "")), session.location)
    ]


def subtract_occupied(start: int, end: int, occupied: list[Session]) -> list[tuple[int, int]]:
    clipped = sorted(
        (max(start, session.start_minutes), min(end, session.end_minutes))
        for session in occupied
        if session.end_minutes > start and session.start_minutes < end
    )
    gaps: list[tuple[int, int]] = []
    cursor = start
    for segment_start, segment_end in clipped:
        if segment_start > cursor:
            gaps.append((cursor, segment_start))
        cursor = max(cursor, segment_end)
    if cursor < end:
        gaps.append((cursor, end))
    return [(gap_start, gap_end) for gap_start, gap_end in gaps if gap_end > gap_start]


def candidate_courses(allowed_families: list[str], preferred_families: list[str], flexibility: str) -> list[tuple[str, int]]:
    allowed = set(allowed_families)
    preferred = set(preferred_families)
    if "flexible" in allowed:
        allowed = set(FAMILY_ALIASES)
    if "flexible" in preferred:
        preferred = allowed
    families = preferred if flexibility == "strict_preferred_only" else allowed
    candidates: list[tuple[str, int]] = []
    for family in families:
        for course_family in FAMILY_ALIASES.get(family, [family]):
            duration = COURSE_DURATION_ESTIMATES.get(course_family)
            if duration:
                candidates.append((course_family, duration))
    return sorted(set(candidates), key=lambda item: item[0])


def fit_reason(course_family: str, duration: int, gap_minutes: int, block: dict[str, Any], gap_start: int) -> str:
    preferred = set(block.get("preferred_course_families") or [])
    if course_family.startswith(("ACLS", "PALS")) and any(family in preferred for family in ("ACLS", "PALS")):
        return f"Preferred advanced family fits available {gap_minutes}-minute gap."
    anchor = parse_time(block.get("preferred_anchor_start"))
    if anchor is not None and gap_start < anchor:
        return f"Fits available {gap_minutes}-minute gap before preferred anchor."
    return f"Fits available {gap_minutes}-minute gap using V1 {duration}-minute estimate."


def suggested_fits(block: dict[str, Any], gap_start: int, gap_end: int, profile: dict[str, Any]) -> list[dict[str, Any]]:
    gap_minutes = gap_end - gap_start
    allowed = block.get("allowed_course_families") or profile.get("allowed_families") or []
    preferred = block.get("preferred_course_families") or profile.get("preferred_families") or []
    flexibility = block.get("flexibility") or profile.get("default_flexibility") or "use_unused_time_if_useful"
    fits = []
    for course_family, duration in candidate_courses(allowed, preferred, flexibility):
        if duration <= gap_minutes:
            preferred_bonus = 100 if any(course_family.startswith(family) for family in preferred if family != "flexible") else 0
            fits.append(
                {
                    "course_family": course_family,
                    "estimated_minutes": duration,
                    "_score": preferred_bonus + BUSINESS_USEFULNESS.get(course_family, 0),
                    "reason": fit_reason(course_family, duration, gap_minutes, block, gap_start),
                }
            )
    fits.sort(key=lambda item: (-item["_score"], item["estimated_minutes"], item["course_family"]))
    for index, fit in enumerate(fits, start=1):
        fit["rank"] = index
        fit.pop("_score", None)
    return fits


def resolve() -> tuple[dict[str, Any], dict[str, Any]]:
    warnings: list[str] = []
    skipped: list[dict[str, str]] = []
    availability = load_json(AVAILABILITY_PATH, {"availability_blocks": []})
    profiles = load_json(PROFILES_PATH, {"instructors": []})
    load_json(RANGES_PATH, {"ranges": []})  # Loaded to keep V1 aware of the registry file; not used for link generation.
    sessions = load_sessions(warnings)
    recommendations: list[dict[str, Any]] = []
    gaps_found = 0

    blocks = availability.get("availability_blocks") or []
    for block in blocks:
        start = parse_time(block.get("available_start"))
        end = parse_time(block.get("available_end"))
        if start is None or end is None or start >= end:
            skipped.append({"block_id": str(block.get("block_id", "")), "reason": "invalid_availability_window"})
            continue
        if not block.get("date") or not block.get("instructor") or not block.get("location"):
            skipped.append({"block_id": str(block.get("block_id", "")), "reason": "missing_required_block_fields"})
            continue
        profile = profile_for(str(block.get("instructor", "")), profiles)
        occupied = occupied_segments(block, sessions, profiles)
        gaps = subtract_occupied(start, end, occupied)
        gaps_found += len(gaps)
        for gap_start, gap_end in gaps:
            fits = suggested_fits(block, gap_start, gap_end, profile)
            if not fits:
                continue
            recommendation_id = f"{slug(str(block.get('instructor')))}_{block.get('date')}_{format_time(gap_start).replace(':', '')}_{format_time(gap_end).replace(':', '')}"
            recommendations.append(
                {
                    "recommendation_id": recommendation_id,
                    "instructor": block.get("instructor"),
                    "date": block.get("date"),
                    "location": block.get("location"),
                    "availability_block_id": block.get("block_id", ""),
                    "gap_start": format_time(gap_start),
                    "gap_end": format_time(gap_end),
                    "gap_minutes": gap_end - gap_start,
                    "existing_sessions_considered": [
                        {
                            "session_id": session.session_id,
                            "course_name": session.course_name,
                            "start": format_time(session.start_minutes),
                            "end": format_time(session.end_minutes),
                            "instructor": session.instructor,
                            "location": session.location,
                        }
                        for session in occupied
                    ],
                    "suggested_fits": fits,
                    "status": "recommendation_only",
                }
            )

    generated_at = datetime.now(timezone.utc).isoformat()
    output = {
        "schema_version": "0.1",
        "generated_at": generated_at,
        "recommendations": recommendations,
    }
    audit = {
        "schema_version": "0.1",
        "generated_at": generated_at,
        "availability_blocks_read": len(blocks),
        "existing_sessions_read": len(sessions),
        "gaps_found": gaps_found,
        "recommendations_created": len(recommendations),
        "warnings": warnings,
        "skipped_blocks": skipped,
        "hard_stop": "V1 only: availability - existing sessions = usable gaps + simple fit recommendations. No public booking links generated.",
    }
    return output, audit


def main() -> int:
    output, audit = resolve()
    write_json(RECOMMENDATIONS_PATH, output)
    write_json(AUDIT_PATH, audit)
    print(json.dumps({"recommendations": len(output["recommendations"]), "warnings": len(audit["warnings"]), "skipped": len(audit["skipped_blocks"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
