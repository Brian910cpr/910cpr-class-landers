from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.anchor_state import ANCHOR_SYMBOL, promote_seated_sessions, same_course_anchor

ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
ADMIN_SCHEDULE_PATH = ROOT / "docs" / "data" / "admin_schedule.json"
SELECTOR_DIR = ROOT / "docs" / "data" / "block-selector-availability"
ANCHOR_FEED_PATH = ROOT / "docs" / "data" / "anchor_state.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def text(value: Any) -> str:
    return str(value or "").strip()


def dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(text(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def course_id(item: dict[str, Any]) -> str:
    return text(item.get("course_id") or item.get("courseId") or item.get("course_number"))


def location(item: dict[str, Any]) -> str:
    value = item.get("location_name") or item.get("location_display") or item.get("location") or item.get("locationLabel")
    if isinstance(value, dict):
        value = value.get("location_name") or value.get("name") or value.get("label")
    return text(value)


def start_value(item: dict[str, Any]) -> str:
    return text(item.get("start_at") or item.get("start") or item.get("start_datetime") or item.get("startsAt"))


def item_date(item: dict[str, Any]) -> str:
    parsed = dt(start_value(item))
    return parsed.date().isoformat() if parsed else text(item.get("date"))[:10]


def registration_url(item: dict[str, Any]) -> str:
    return text(item.get("registration_url") or item.get("registrationUrl") or item.get("enrollment_url") or item.get("href"))


def is_offer_like(item: dict[str, Any]) -> bool:
    return bool(course_id(item) and item_date(item) and (start_value(item) or registration_url(item)))


def apply_anchor_to_session(session: dict[str, Any], anchor: dict[str, Any]) -> None:
    session.update({
        "schedule_role": "anchor",
        "schedule_symbol": ANCHOR_SYMBOL,
        "cluster_id": anchor["cluster_id"],
        "promotion_reason": anchor["promotion_reason"],
        "landing_page_required": True,
        "external_publication_eligible": True,
    })


def annotate_schedule(payload: dict[str, Any], anchors: list[dict[str, Any]]) -> int:
    sessions = payload.get("sessions") if isinstance(payload, dict) else None
    if not isinstance(sessions, list):
        return 0
    by_id = {text(anchor.get("session_id")): anchor for anchor in anchors}
    changed = 0
    for session in sessions:
        if not isinstance(session, dict):
            continue
        sid = text(session.get("session_id") or session.get("id") or session.get("class_id"))
        anchor = by_id.get(sid)
        if anchor:
            apply_anchor_to_session(session, anchor)
            changed += 1
    payload["anchor_count"] = len(anchors)
    return changed


def rewrite_offer_to_anchor(item: dict[str, Any], anchor: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(item)
    start = anchor["start_at"]
    end = anchor["end_at"]
    for key in ("start_at", "start", "start_datetime", "startsAt"):
        if key in result:
            result[key] = start
    for key in ("end_at", "end", "end_datetime", "endsAt"):
        if key in result:
            result[key] = end
    if "date" in result:
        result["date"] = start[:10]
    parsed = dt(start)
    if parsed:
        formatted = parsed.strftime("%-I:%M %p")
        for key in ("start_time", "startTime", "display_time", "timeLabel", "startTimeLabel"):
            if key in result:
                result[key] = formatted
    url = text(anchor.get("registration_url"))
    if url:
        for key in ("registration_url", "registrationUrl", "enrollment_url", "href"):
            if key in result:
                result[key] = url
        if not any(key in result for key in ("registration_url", "registrationUrl", "enrollment_url", "href")):
            result["registration_url"] = url
    result.update({
        "session_id": anchor["session_id"],
        "schedule_role": "anchor",
        "schedule_symbol": ANCHOR_SYMBOL,
        "cluster_id": anchor["cluster_id"],
        "promotion_reason": "same_course_anchor_reuse",
        "landing_page_required": True,
        "external_publication_eligible": True,
        "offer_source": "existing_seated_anchor",
    })
    for key in ("label", "display_label", "title"):
        if key in result and not text(result[key]).startswith(ANCHOR_SYMBOL):
            result[key] = f"{ANCHOR_SYMBOL} {text(result[key])}"
    return result


def consolidate_node(node: Any, anchors: list[dict[str, Any]], stats: dict[str, int]) -> Any:
    if isinstance(node, list):
        rewritten = [consolidate_node(item, anchors, stats) for item in node]
        deduped: list[Any] = []
        seen: set[tuple[str, str, str, str]] = set()
        for item in rewritten:
            if isinstance(item, dict) and item.get("schedule_role") == "anchor":
                key = (course_id(item), item_date(item), location(item), text(item.get("session_id")))
                if key in seen:
                    stats["duplicate_anchor_offers_removed"] += 1
                    continue
                seen.add(key)
            deduped.append(item)
        return deduped
    if not isinstance(node, dict):
        return node
    result = {key: consolidate_node(value, anchors, stats) for key, value in node.items()}
    if not is_offer_like(result):
        return result
    anchor = same_course_anchor(
        course_id=course_id(result),
        date=item_date(result),
        location=location(result),
        anchors=anchors,
    )
    if not anchor:
        result.setdefault("schedule_role", "standalone_offer")
        result.setdefault("schedule_symbol", "")
        return result
    original_start = start_value(result)
    rewritten = rewrite_offer_to_anchor(result, anchor)
    if original_start and original_start != anchor["start_at"]:
        stats["scattered_offers_consolidated"] += 1
    else:
        stats["anchor_offers_annotated"] += 1
    return rewritten


def run() -> dict[str, int]:
    schedule = load(SCHEDULE_PATH)
    sessions = schedule.get("sessions", []) if isinstance(schedule, dict) else []
    anchors = promote_seated_sessions(sessions)
    stats = {
        "anchors_promoted": len(anchors),
        "schedule_sessions_annotated": annotate_schedule(schedule, anchors),
        "admin_sessions_annotated": 0,
        "selector_files_processed": 0,
        "anchor_offers_annotated": 0,
        "scattered_offers_consolidated": 0,
        "duplicate_anchor_offers_removed": 0,
    }
    write(SCHEDULE_PATH, schedule)

    if ADMIN_SCHEDULE_PATH.exists():
        admin = load(ADMIN_SCHEDULE_PATH)
        stats["admin_sessions_annotated"] = annotate_schedule(admin, anchors)
        write(ADMIN_SCHEDULE_PATH, admin)

    if SELECTOR_DIR.exists():
        for path in sorted(SELECTOR_DIR.glob("*.json")):
            if not path.read_text(encoding="utf-8").strip():
                continue
            payload = load(path)
            payload = consolidate_node(payload, anchors, stats)
            if isinstance(payload, dict):
                payload["anchor_policy"] = {
                    "version": "seated-anchor-v1",
                    "anchors_promoted": len(anchors),
                }
            write(path, payload)
            stats["selector_files_processed"] += 1

    write(ANCHOR_FEED_PATH, {
        "schema_version": "910cpr-anchor-state.v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "symbol": ANCHOR_SYMBOL,
        "anchors": anchors,
        "counts": stats,
    })
    return stats


def main() -> int:
    print(json.dumps(run(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
