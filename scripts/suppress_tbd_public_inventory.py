from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.public_class_eligibility import session_has_public_class_location

SESSION_ID_RE = re.compile(r"[?&]id=(\d+)")


def is_public_direct_bookable(session: dict[str, Any]) -> bool:
    return session.get("public_direct_booking") is not False and str(session.get("registration_status") or "open").strip().lower() not in {"closed", "full"}


def raw_location_values(session: dict[str, Any]) -> list[str]:
    location = session.get("location")
    values: list[Any] = [
        session.get("raw_location"),
        session.get("location_raw"),
        session.get("location_display"),
        session.get("location_name"),
        session.get("location"),
    ]
    if isinstance(location, dict):
        values.extend(
            [
                location.get("raw_location"),
                location.get("location_raw"),
                location.get("location_display"),
                location.get("location_name"),
                location.get("name"),
            ]
        )
    return [str(value) for value in values if value not in (None, "")]


def nonpublic_session_ids(sessions_current_path: Path) -> set[str]:
    payload = json.loads(sessions_current_path.read_text(encoding="utf-8"))
    sessions = payload.get("sessions", []) if isinstance(payload, dict) else []
    return {
        str(session.get("session_id") or "").strip()
        for session in sessions
        if isinstance(session, dict)
        and str(session.get("session_id") or "").strip()
        and not session_has_public_class_location(session)
    }


def nonpublic_session_ids_from_schedule_future(schedule_future_path: Path) -> set[str]:
    payload = json.loads(schedule_future_path.read_text(encoding="utf-8"))
    sessions = payload.get("sessions", []) if isinstance(payload, dict) else payload
    if not isinstance(sessions, list):
        return set()
    return {
        str(session.get("session_id") or "").strip()
        for session in sessions
        if isinstance(session, dict)
        and str(session.get("session_id") or "").strip()
        and not session_has_public_class_location(session)
    }


def public_schedule_id(entry: dict[str, Any]) -> str:
    for key in ("class_id", "classSchedId", "sched_id", "id"):
        value = str(entry.get(key) or "").strip()
        if value:
            return value
    for key in ("register_url", "registration_url", "url"):
        match = SESSION_ID_RE.search(str(entry.get(key) or ""))
        if match:
            return match.group(1)
    return str(entry.get("session_id") or "").strip()


def write_public_schedule_from_future(schedule_future_path: Path, output_paths: list[Path], suppressed_ids: set[str]) -> int:
    payload = json.loads(schedule_future_path.read_text(encoding="utf-8"))
    sessions = payload.get("sessions", []) if isinstance(payload, dict) else []
    rows = []
    for session in sessions:
        if not isinstance(session, dict):
            continue
        session_id = str(session.get("session_id") or "").strip()
        if not session_id or session_id in suppressed_ids:
            continue
        if not is_public_direct_bookable(session):
            continue
        if not session_has_public_class_location(session):
            continue
        course_id = session.get("course_id")
        course_name = session.get("course_name") or session.get("raw_course_name") or session.get("official_course_name") or ""
        rows.append(
            {
                "session_id": course_id or session_id,
                "class_id": session_id,
                "course_id": course_id,
                "course": course_name,
                "title": course_name,
                "start": session.get("start_at") or "",
                "location": session.get("location_display") or session.get("location_name") or "",
                "location_name": session.get("location_name") or session.get("raw_location") or "",
                "location_display": session.get("location_display") or "",
                "seats_available": session.get("available_seats"),
                "register_url": session.get("registration_url") or "",
                "schedule_url": f"https://coastalcprtraining.enrollware.com/schedule#ct{course_id}" if course_id else "",
            }
        )
    output = {
        "generated_at": payload.get("build", {}).get("generated_at", ""),
        "count": len(rows),
        "sessions": rows,
    }
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(rows)


def remove_suppressed_public_schedule_entries(path: Path, suppressed_ids: set[str]) -> int:
    if not path.exists():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        sessions = payload.get("sessions")
        if not isinstance(sessions, list):
            return 0
        kept = [
            entry for entry in sessions
            if not isinstance(entry, dict)
            or (
                public_schedule_id(entry) not in suppressed_ids
                and session_has_public_class_location(entry)
            )
        ]
        removed = len(sessions) - len(kept)
        if removed:
            payload["sessions"] = kept
            payload["count"] = len(kept)
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return removed
    if isinstance(payload, list):
        kept = [
            entry for entry in payload
            if not isinstance(entry, dict)
            or (
                public_schedule_id(entry) not in suppressed_ids
                and session_has_public_class_location(entry)
            )
        ]
        removed = len(payload) - len(kept)
        if removed:
            path.write_text(json.dumps(kept, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return removed
    return 0


def remove_html_session_rows(text: str, suppressed_ids: set[str]) -> tuple[str, int]:
    changed = 0
    for session_id in sorted(suppressed_ids, key=len, reverse=True):
        escaped = re.escape(session_id)
        patterns = [
            rf"\n?\s*<div class=\"slug-time-row\b(?=[^>]*\bdata-session-id=\"{escaped}\")[\s\S]*?<div class=\"slug-time-actions\">[\s\S]*?</div>\s*</div>",
            rf"\n?\s*<article class=\"curated-offer-card\b(?=[^>]*\bdata-session-id=\"{escaped}\")[\s\S]*?</article>",
            rf"\n?\s*<article class=\"slug-pill\b(?=[^>]*\bdata-session-id=\"{escaped}\")[\s\S]*?</article>",
            rf"\n?\s*<div class=\"upcoming-card\b(?=[^>]*\bdata-session-id=\"{escaped}\")[\s\S]*?<div class=\"upcoming-actions\">[\s\S]*?</div>\s*</div>",
            rf"\n?\s*<li class=\"js-session-item\"(?=[^>]*\bdata-session-id=\"{escaped}\")[\s\S]*?</li>",
            rf"\n?\s*<article class=\"course-session-row\b(?=[^>]*\bdata-session-id=\"{escaped}\")[\s\S]*?</article>",
        ]
        for pattern in patterns:
            text, count = re.subn(pattern, "", text)
            changed += count
    return text, changed


def scrub_html_references(docs_dir: Path, suppressed_ids: set[str]) -> tuple[int, int]:
    if not suppressed_ids:
        return 0, 0
    files_changed = 0
    rows_removed = 0
    id_pattern = re.compile("|".join(re.escape(session_id) for session_id in sorted(suppressed_ids, key=len, reverse=True)))
    for path in docs_dir.rglob("*.html"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        present_ids = set(id_pattern.findall(text))
        if not present_ids:
            continue
        updated, removed = remove_html_session_rows(text, present_ids)
        if removed and updated != text:
            path.write_text(updated, encoding="utf-8")
            files_changed += 1
            rows_removed += removed
    return files_changed, rows_removed


def delete_class_pages(classes_dir: Path, suppressed_ids: set[str]) -> int:
    deleted = 0
    for session_id in suppressed_ids:
        path = classes_dir / f"{session_id}.html"
        if path.exists():
            path.unlink()
            deleted += 1
    return deleted


def main() -> int:
    schedule_future_path = ROOT / "docs" / "data" / "schedule_future.json"
    suppressed_ids = nonpublic_session_ids_from_schedule_future(schedule_future_path)
    deleted_pages = delete_class_pages(ROOT / "docs" / "classes", suppressed_ids)
    public_rows = write_public_schedule_from_future(
        schedule_future_path,
        [ROOT / "docs" / "public_schedule.json", ROOT / "docs" / "data" / "public_schedule.json"],
        suppressed_ids,
    )
    removed_legacy_rows = 0
    for path in (ROOT / "docs" / "public_schedule.json", ROOT / "docs" / "data" / "public_schedule.json"):
        removed_legacy_rows += remove_suppressed_public_schedule_entries(path, suppressed_ids)
    files_changed, rows_removed = scrub_html_references(ROOT / "docs", suppressed_ids)

    print(f"Suppressed non-public session IDs: {len(suppressed_ids)}")
    print(f"Deleted class pages: {deleted_pages}")
    print(f"Public schedule rows written: {public_rows}")
    print(f"Removed legacy public schedule rows: {removed_legacy_rows}")
    print(f"HTML files changed: {files_changed}")
    print(f"HTML session rows removed: {rows_removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
