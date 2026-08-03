from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.anchor_state import ANCHOR_SYMBOL, in_repeat_bubble, promote_seated_sessions, repeat_scope_key, same_course_anchor

ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
ADMIN_SCHEDULE_PATH = ROOT / "docs" / "data" / "admin_schedule.json"
SELECTOR_DIR = ROOT / "docs" / "data" / "block-selector-availability"
ANCHOR_FEED_PATH = ROOT / "docs" / "data" / "anchor_state.json"
POLICY_PATH = ROOT / "data" / "config" / "anchor_schedule_policy.json"


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
    return text(item.get("registration_url") or item.get("registrationUrl") or item.get("appointmentUrl") or item.get("enrollment_url") or item.get("href"))


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
        formatted = parsed.strftime("%I:%M %p").lstrip("0")
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


def _offer_start(offer: dict[str, Any]) -> datetime | None:
    value = start_value(offer)
    if value:
        return dt(value)
    date = text(offer.get("date"))
    clock = text(offer.get("startTime") or offer.get("start_time"))
    return dt(f"{date}T{clock}:00") if date and clock else None


def _anchor_for_offer(offer: dict[str, Any], anchors: list[dict[str, Any]]) -> dict[str, Any] | None:
    offer_start = _offer_start(offer)
    cid = course_id(offer)
    url = registration_url(offer)
    for anchor in anchors:
        if cid != text(anchor.get("course_id")):
            continue
        if url and url == text(anchor.get("registration_url")):
            return anchor
        anchor_start = dt(anchor.get("start_at"))
        if offer_start and anchor_start:
            comparable_offer = offer_start
            comparable_anchor = anchor_start
            if (comparable_offer.tzinfo is None) != (comparable_anchor.tzinfo is None):
                comparable_offer = comparable_offer.replace(tzinfo=None)
                comparable_anchor = comparable_anchor.replace(tzinfo=None)
            if comparable_offer == comparable_anchor:
                return anchor
    return None


def apply_selector_policy(payload: dict[str, Any], anchors: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    """Resolve roles from hard-legal selector inventory without fabricating starts."""
    offers = [item for day in payload.get("dates", []) for slot in day.get("startTimes", []) for item in slot.get("courses", [])]
    anchor_scopes: dict[str, list[dict[str, Any]]] = {}
    for anchor in anchors:
        scope, delay = repeat_scope_key(text(anchor.get("course_id")), policy)
        anchor_scopes.setdefault(scope, []).append({**anchor, "repeat_delay_minutes": delay})

    by_course: dict[str, list[dict[str, Any]]] = {}
    for offer in offers:
        by_course.setdefault(course_id(offer), []).append(offer)

    retained: list[dict[str, Any]] = []
    suppressed = 0
    barnacle_keys: dict[tuple[str, str], tuple[datetime, str, dict[str, Any]]] = {}
    for cid, course_offers in by_course.items():
        scope, delay = repeat_scope_key(cid, policy)
        scoped_anchors = anchor_scopes.get(scope, [])
        for offer in course_offers:
            seated = _anchor_for_offer(offer, anchors)
            if seated:
                promoted = rewrite_offer_to_anchor(offer, seated)
                promoted["registered_count"] = seated.get("registered_count", 0)
                promoted["end_at"] = seated.get("end_at")
                retained.append(promoted)
                continue
            start = _offer_start(offer)
            if not start or not scoped_anchors or delay <= 0:
                retained.append(offer)
                continue
            containing = [a for a in scoped_anchors if (astart := dt(a.get("start_at"))) and in_repeat_bubble(start, astart, int(a["repeat_delay_minutes"]))]
            if not containing:
                retained.append(offer)
                continue
            suppressed += 1
            for anchor in containing:
                astart = dt(anchor.get("start_at"))
                if not astart or start == astart:
                    continue
                comparable_start = start
                comparable_anchor = astart
                if (comparable_start.tzinfo is None) != (comparable_anchor.tzinfo is None):
                    comparable_start = comparable_start.replace(tzinfo=None)
                    comparable_anchor = comparable_anchor.replace(tzinfo=None)
                direction = "pre" if comparable_start < comparable_anchor else "post"
                distance = abs((comparable_start - comparable_anchor).total_seconds())
                key = (text(anchor.get("session_id")), direction)
                candidate = (distance, start.isoformat(), offer)
                if key not in barnacle_keys or candidate[:2] < barnacle_keys[key][:2]:
                    barnacle_keys[key] = candidate

    seen = {(course_id(item), start_value(item) or f"{item.get('date')}T{item.get('startTime')}", registration_url(item)) for item in retained}
    for (anchor_id, direction), (_distance, chosen_stamp, _chosen_offer) in barnacle_keys.items():
        anchor = next(item for item in anchors if text(item.get("session_id")) == anchor_id)
        anchor_scope, _delay = repeat_scope_key(text(anchor.get("course_id")), policy)
        for offer in offers:
            offer_start = _offer_start(offer)
            offer_scope, _offer_delay = repeat_scope_key(course_id(offer), policy)
            if not offer_start or offer_start.isoformat() != chosen_stamp or offer_scope != anchor_scope:
                continue
            barnacle = {
                **offer,
                "schedule_role": "barnacle",
                "schedule_symbol": "",
                "cluster_id": anchor.get("cluster_id"),
                "attached_to_session_id": anchor_id,
                "barnacle_direction": direction,
                "landing_page_required": False,
                "external_publication_eligible": False,
            }
            key = (course_id(barnacle), start_value(barnacle) or f"{barnacle.get('date')}T{barnacle.get('startTime')}", registration_url(barnacle))
            if key not in seen:
                retained.append(barnacle)
                seen.add(key)

    grouped: dict[str, dict[str, Any]] = {}
    for offer in retained:
        date = text(offer.get("date")) or item_date(offer)
        start_time = text(offer.get("startTime") or offer.get("start_time"))
        if not start_time:
            parsed = _offer_start(offer)
            start_time = parsed.strftime("%H:%M") if parsed else ""
        day = grouped.setdefault(date, {"date": date, "displayDate": offer.get("displayDate") or date, "startTimes": {}})
        slot = day["startTimes"].setdefault(start_time, {"startTime": start_time, "displayStartTime": offer.get("displayStartTime") or start_time, "courses": []})
        slot["courses"].append(offer)
    payload["dates"] = []
    for day in sorted(grouped.values(), key=lambda item: item["date"]):
        slots = list(day["startTimes"].values())
        slots.sort(key=lambda item: item["startTime"])
        payload["dates"].append({**day, "startTimes": slots})
    payload.setdefault("counts", {})["publicSelectableDateCount"] = len(payload["dates"])
    payload["counts"]["publicSelectableStartTimeCount"] = sum(len(day["startTimes"]) for day in payload["dates"])
    payload["anchor_policy"] = {"version": "anchor-repeat-bubble-v2", "suppressed_offerons": suppressed, "barnacle_positions": len(barnacle_keys)}
    return payload


def resolve_selector_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Apply the authoritative anchor policy to a freshly built selector payload."""
    schedule = load(SCHEDULE_PATH)
    anchors = promote_seated_sessions(schedule.get("sessions", []) if isinstance(schedule, dict) else [])
    return apply_selector_policy(deepcopy(payload), anchors, load(POLICY_PATH))


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
            payload = apply_selector_policy(payload, anchors, load(POLICY_PATH))
            payload["anchor_policy"]["anchors_promoted"] = len(anchors)
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
