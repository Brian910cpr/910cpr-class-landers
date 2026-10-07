from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from scripts.anchor_state import ANCHOR_SYMBOL, in_repeat_bubble, promote_seated_sessions, repeat_scope_key, same_course_anchor
from scripts.canonical_scheduling_demand import resolve_canonical_demand, exclude_non_session_sources, reconciliation_issues, load_publication_demand
from scripts.fetch_canonical_scheduling_demand import validate_payload

ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
ADMIN_SCHEDULE_PATH = ROOT / "docs" / "data" / "admin_schedule.json"
SELECTOR_DIR = ROOT / "docs" / "data" / "block-selector-availability"
ANCHOR_FEED_PATH = ROOT / "docs" / "data" / "anchor_state.json"
POLICY_PATH = ROOT / "data" / "config" / "anchor_schedule_policy.json"
CANONICAL_DEMAND_PATH = ROOT / "data" / "runtime" / "canonical_scheduling_demand.json"
DEMAND_MATCH_AUDIT_PATH = ROOT / "data" / "audit" / "canonical_scheduling_demand_matches.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def apply_demand_projection(sessions: list[dict[str, Any]], payload: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = payload.get("sessions", []) if isinstance(payload, dict) else []
    sessions, _excluded = exclude_non_session_sources(sessions, payload)
    return resolve_canonical_demand(sessions, rows if isinstance(rows, list) else [])


def sessions_with_canonical_demand(sessions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not CANONICAL_DEMAND_PATH.exists():
        raise ValueError("Fresh canonical scheduling demand is required before publishing Anchor policy")
    return apply_demand_projection(sessions, validate_payload(load(CANONICAL_DEMAND_PATH)))


def text(value: Any) -> str:
    return str(value or "").strip()


def dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(text(value).replace("Z", "+00:00"))
        return parsed.astimezone(ZoneInfo("America/New_York")) if parsed.tzinfo else parsed
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
            if session.get("promotion_reason") in {"committed_public_session", "manual_override"}:
                session.setdefault("anchor_basis", session["promotion_reason"])
            apply_anchor_to_session(session, anchor)
            changed += 1
        elif session.get("schedule_role") == "anchor":
            for key in ("schedule_role", "schedule_symbol", "cluster_id", "promotion_reason", "landing_page_required", "external_publication_eligible"):
                session.pop(key, None)
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
        # Selector sorting and AM/PM grouping consume a 24-hour machine clock.
        # Keep presentation labels separate when an offer reuses an Anchor.
        if "startTime" in result:
            result["startTime"] = parsed.strftime("%H:%M")
        for key in ("start_time", "displayStartTime", "display_time", "timeLabel", "startTimeLabel"):
            if key in result:
                result[key] = formatted
    url = text(anchor.get("registration_url"))
    if url:
        for key in ("registration_url", "registrationUrl", "appointmentUrl", "enrollment_url", "href"):
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
        anchor_start = dt(anchor.get("start_at"))
        if offer_start and anchor_start:
            comparable_offer = offer_start
            comparable_anchor = anchor_start
            if (comparable_offer.tzinfo is None) != (comparable_anchor.tzinfo is None):
                comparable_offer = comparable_offer.replace(tzinfo=None)
                comparable_anchor = comparable_anchor.replace(tzinfo=None)
            same_identity = bool(url and url == text(anchor.get("registration_url")))
            same_resource = location(offer) == text(anchor.get("location")) and bool(location(offer))
            if comparable_offer == comparable_anchor and (same_identity or same_resource):
                return anchor
    return None


def _offer_end(offer: dict[str, Any], start: datetime) -> datetime:
    explicit = text(offer.get("end_at") or offer.get("end") or offer.get("endsAt"))
    if explicit and (parsed := dt(explicit)):
        return parsed.replace(tzinfo=None) if start.tzinfo is None and parsed.tzinfo else parsed
    clock = text(offer.get("schedulerConsumptionEnd") or offer.get("endTime") or offer.get("end_time"))
    if clock and len(clock) >= 4:
        parsed = dt(f"{item_date(offer)}T{clock[:5]}:00")
        if parsed:
            if parsed <= start:
                parsed += timedelta(days=1)
            return parsed
    minutes = int(offer.get("schedulerConsumptionMinutes") or offer.get("durationMinutes") or 0)
    return start + timedelta(minutes=max(0, minutes))


def _refresh_selector_counts(payload: dict[str, Any]) -> None:
    dates = payload.get("dates", [])
    counts = payload.setdefault("counts", {})
    counts["publicSelectableDateCount"] = len(dates)
    counts["publicSelectableStartTimeCount"] = sum(len(day.get("startTimes", [])) for day in dates)
    counts["publicSelectableOfferCount"] = sum(
        len(slot.get("courses", []))
        for day in dates
        for slot in day.get("startTimes", [])
    )


def _rebuild_dates(payload: dict[str, Any], offers: list[dict[str, Any]]) -> dict[str, Any]:
    # The diagnostic publisher and renderer must see exactly the same decisions.
    if "offers" in payload:
        payload["offers"] = offers
    grouped: dict[str, dict[str, Any]] = {}
    for offer in offers:
        date = text(offer.get("date")) or item_date(offer)
        parsed = _offer_start(offer)
        start_time = text(offer.get("startTime") or offer.get("start_time")) or (parsed.strftime("%H:%M") if parsed else "")
        day = grouped.setdefault(date, {"date": date, "displayDate": offer.get("displayDate") or date, "startTimes": {}})
        slot = day["startTimes"].setdefault(start_time, {"startTime": start_time, "displayStartTime": offer.get("displayStartTime") or start_time, "courses": []})
        slot["courses"].append(offer)
    payload["dates"] = []
    for day in sorted(grouped.values(), key=lambda item: item["date"]):
        slots = sorted(day["startTimes"].values(), key=lambda item: item["startTime"])
        payload["dates"].append({**day, "startTimes": slots})
    _refresh_selector_counts(payload)
    return payload


def apply_daily_anchor_stack(payload: dict[str, Any], anchors: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    """Offer all legal starts on open days, then compact paid days around their anchors."""
    offers = [item for day in payload.get("dates", []) for slot in day.get("startTimes", []) for item in slot.get("courses", [])]
    excluded = {text(value).upper() for value in policy.get("open_day_excluded_families", [])}
    anchors_by_date: dict[str, list[dict[str, Any]]] = {}
    for anchor in anchors:
        if parsed := dt(anchor.get("start_at")):
            anchors_by_date.setdefault(parsed.date().isoformat(), []).append(anchor)

    retained: list[dict[str, Any]] = []
    suppressed = 0
    barnacle_count = 0
    for date in sorted({item_date(offer) for offer in offers}):
        day_offers = [offer for offer in offers if item_date(offer) == date]
        day_anchors = anchors_by_date.get(date, [])
        if not day_anchors:
            for offer in day_offers:
                family = text(offer.get("courseFamily")).upper()
                is_real = text(offer.get("offerType")) == "seated_class" or bool(_anchor_for_offer(offer, anchors))
                if family in excluded and not is_real:
                    suppressed += 1
                else:
                    retained.append(offer)
            continue

        if policy.get("compact_paid_days", True) is False:
            # A seated Enrollware class is hard occupancy, not a reason to hide
            # otherwise legal starts elsewhere in the day. Conflict, duration,
            # travel, lead-time, and calendar rules have already run upstream.
            for offer in day_offers:
                if seated := _anchor_for_offer(offer, day_anchors):
                    retained.append(rewrite_offer_to_anchor(offer, seated))
                    continue
                family = text(offer.get("courseFamily")).upper()
                is_real = text(offer.get("offerType")) == "seated_class"
                if family in excluded and not is_real:
                    suppressed += 1
                    continue
                retained.append(offer)
            continue

        anchored_courses = {text(anchor.get("course_id")) for anchor in day_anchors}
        for offer in day_offers:
            if seated := _anchor_for_offer(offer, day_anchors):
                retained.append(rewrite_offer_to_anchor(offer, seated))
            elif offer.get("offerType") == "seated_class":
                # A real occurrence remains real even when its roster needs
                # reconciliation. Do not relabel it as an invented barnacle.
                retained.append(offer)

        for cid in sorted({course_id(offer) for offer in day_offers} - anchored_courses):
            candidates = [offer for offer in day_offers if course_id(offer) == cid and offer.get("offerType") != "seated_class" and not _anchor_for_offer(offer, day_anchors)]
            chosen: dict[tuple[str, str], tuple[float, str, dict[str, Any]]] = {}
            candidate_scope, _candidate_delay = repeat_scope_key(cid, policy)
            for anchor in day_anchors:
                anchor_scope, _anchor_delay = repeat_scope_key(text(anchor.get("course_id")), policy)
                if (candidate_scope == anchor_scope
                    and [text(anchor.get("course_id")), cid] not in policy.get("barnacle_course_pairs", [])):
                    # Initial/Renewal variants in the same classroom family are
                    # alternatives the customer chooses explicitly, not barnacles
                    # to place before or after one another.
                    continue
                astart = dt(anchor.get("start_at"))
                aend = dt(anchor.get("end_at"))
                if not astart or not aend:
                    continue
                astart = astart.replace(tzinfo=None)
                aend = aend.replace(tzinfo=None)
                for offer in candidates:
                    if not barnacle_compatible(offer, anchor, policy):
                        continue
                    start = _offer_start(offer)
                    if not start:
                        continue
                    start = start.replace(tzinfo=None)
                    end = _offer_end(offer, start).replace(tzinfo=None)
                    direction = "pre" if end <= astart else ("post" if start >= aend else "")
                    if not direction:
                        continue
                    gap = (astart - end).total_seconds() if direction == "pre" else (start - aend).total_seconds()
                    key = (text(anchor.get("session_id")), direction)
                    candidate = (gap, start.isoformat(), offer)
                    if key not in chosen or candidate[:2] < chosen[key][:2]:
                        chosen[key] = candidate
            seen_ids: set[int] = set()
            for (anchor_id, direction), (_gap, _stamp, offer) in chosen.items():
                if id(offer) in seen_ids:
                    continue
                seen_ids.add(id(offer))
                anchor = next(item for item in day_anchors if text(item.get("session_id")) == anchor_id)
                retained.append({**offer, "schedule_role": "barnacle", "schedule_symbol": "", "cluster_id": anchor.get("cluster_id"), "attached_to_session_id": anchor_id, "barnacle_direction": direction, "landing_page_required": False, "external_publication_eligible": False})
                barnacle_count += 1
            suppressed += max(0, len(candidates) - len(seen_ids))

        suppressed += sum(1 for offer in day_offers if course_id(offer) in anchored_courses and not _anchor_for_offer(offer, day_anchors))

    _rebuild_dates(payload, retained)
    payload["anchor_policy"] = {"version": "daily-anchor-stack-v1", "suppressed_offers": suppressed, "barnacle_positions": barnacle_count, "one_course_type_per_calendar_day": True}
    return payload


def barnacle_compatible(offer: dict[str, Any], anchor: dict[str, Any], policy: dict[str, Any]) -> bool:
    """Compatibility must be explicit; proximity alone is not permission."""
    allowed = policy.get("barnacle_course_pairs")
    if allowed is None:
        # Retain the legacy policy contract for older callers. Production
        # declares this field and therefore always uses the strict gate.
        return True
    if [text(anchor.get("course_id")), course_id(offer)] not in allowed:
        return False
    normalize = lambda value: " ".join(text(value).lower().split())
    if not location(offer) or normalize(location(offer)) != normalize(anchor.get("location")):
        return False
    if not offer.get("instructor") or normalize(offer.get("instructor")) != normalize(anchor.get("instructor")):
        return False
    start, astart, aend = _offer_start(offer), dt(anchor.get("start_at")), dt(anchor.get("end_at"))
    if not all((start, astart, aend)):
        return False
    start, astart, aend = (value.replace(tzinfo=None) for value in (start, astart, aend))
    end = _offer_end(offer, start).replace(tzinfo=None)
    # Existing sequential stack semantics: attach directly to an occupied
    # boundary. Overlap remains subject to the existing hard conflict engine.
    return end == astart or start == aend


def apply_selector_policy(payload: dict[str, Any], anchors: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    """Resolve roles from hard-legal selector inventory without fabricating starts."""
    if policy.get("mode") == "daily_anchor_stack_v1":
        return apply_daily_anchor_stack(payload, anchors, policy)
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
    _refresh_selector_counts(payload)
    payload["anchor_policy"] = {"version": "anchor-repeat-bubble-v2", "suppressed_offers": suppressed, "barnacle_positions": len(barnacle_keys)}
    return payload


def production_anchor_policy() -> dict[str, Any]:
    policy = load(POLICY_PATH)
    rules = load(ROOT / "data/inventory/course_consumption_rules.json")["rules"]
    # Reuse the reviewed course-consumption compatibility map; do not invent a
    # second course catalog or treat physical proximity as compatibility.
    derived_pairs = [
        [text(anchor["course_id"]), text(candidate["course_id"])]
        for anchor in rules for candidate in rules
        if candidate.get("can_ride_existing_momentum") is True
        and anchor.get("occupancy_pool") in candidate.get("compatible_with", [])
        and candidate.get("occupancy_pool") in anchor.get("compatible_with", [])
    ]
    configured_pairs = [
        [text(pair[0]), text(pair[1])]
        for pair in policy.get("barnacle_course_pairs", [])
        if isinstance(pair, list) and len(pair) == 2
    ]
    seen = set()
    policy["barnacle_course_pairs"] = []
    for pair in [*configured_pairs, *derived_pairs]:
        key = tuple(pair)
        if key in seen:
            continue
        seen.add(key)
        policy["barnacle_course_pairs"].append(pair)
    return policy


def finalize_selector_payload(payload: dict[str, Any], sessions: list[dict[str, Any]],
                              demand: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """One final decision path for public selectors and the diagnostic feed."""
    if payload.get("schedulingModel") == "layered-publication.v2":
        from scripts.layered_publication_adapter import finalize
        return finalize(payload)
    sessions, _ = exclude_non_session_sources(sessions, demand)
    rows = demand.get("sessions", [])
    issues = [*payload.get("reconciliationIssues", []), *reconciliation_issues(sessions, rows)]
    resolved, _ = resolve_canonical_demand(sessions, rows)
    anchors = promote_seated_sessions(resolved)
    original = [item for day in payload.get("dates", []) for slot in day.get("startTimes", []) for item in slot.get("courses", [])]
    payload = apply_selector_policy(deepcopy(payload), anchors, policy)
    blocked_dates = {item["date"] for item in issues if item["blocksSynthesis"]}
    occupied_dates = {item_date(a) for a in anchors}
    occupied_dates.update(item_date(row) for row in rows
        if row.get("session_status") in ("scheduled", "active")
        and (row.get("active_registration_count", 0) or 0) > 0)
    occupied_dates.update(item_date(row) for row in rows
        if row.get("session_status") in ("scheduled", "active")
        and (not row.get("external_class_id") or row.get("source") == "landerware_event"))
    retained = []
    for day in payload.get("dates", []):
        for slot in day.get("startTimes", []):
            for item in slot.get("courses", []):
                real = item.get("offerType") == "seated_class"
                date = item_date(item)
                if not real and (date in blocked_dates
                    or (date in occupied_dates and item.get("schedule_role") != "barnacle")):
                    continue
                retained.append(item)
    key = lambda item: (item_date(item), text(item.get("startTime")), course_id(item), registration_url(item))
    retained_keys = {key(item) for item in retained}
    rejected = payload.setdefault("rejectedCourseStartTimes", [])
    for item in original:
        if key(item) not in retained_keys:
            reason = "RECONCILIATION_REQUIRED" if item_date(item) in blocked_dates else "ORPHAN_SYNTHETIC_OFFER"
            rejected.append({**item, "reasons": [reason]})
    payload["reconciliationIssues"] = issues
    # Cover one missed 30-minute publication plus build/deploy and queue time.
    # Source-specific freshness caps below remain independent and enforced.
    valid_until = datetime.now(timezone.utc) + timedelta(minutes=90)
    for item in retained:
        expiry = valid_until
        if item.get("offerType") != "seated_class":
            for row in rows:
                if item_date(row) == item_date(item) and row.get("count_available") and row.get("freshness_minutes"):
                    observed = dt(row.get("source_observed_at"))
                    if observed and observed.tzinfo:
                        expiry = min(expiry, observed + timedelta(minutes=row["freshness_minutes"]))
        item["validUntil"] = expiry.isoformat()
    payload["validUntil"] = valid_until.isoformat()
    payload["synthesisBlockedDates"] = sorted(blocked_dates)
    payload["occupiedDates"] = sorted(occupied_dates)
    payload["anchor_policy"]["finalized"] = True
    payload["anchor_policy"]["anchors_promoted"] = len(anchors)
    payload["anchor_policy"]["suppressed_offers"] = len(original) - len(retained)
    payload["rejectionReasonCounts"] = {}
    for item in rejected:
        for reason in item.get("reasons", []):
            payload["rejectionReasonCounts"][reason] = payload["rejectionReasonCounts"].get(reason, 0) + 1
    _rebuild_dates(payload, retained)
    payload["counts"]["rejectedOfferCount"] = len(rejected)
    return payload


def resolve_selector_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Apply the authoritative anchor policy to a freshly built selector payload."""
    schedule = load(SCHEDULE_PATH)
    sessions = schedule.get("sessions", []) if isinstance(schedule, dict) else []
    return finalize_selector_payload(payload, sessions, load_publication_demand(ROOT), production_anchor_policy())


def run() -> dict[str, int]:
    schedule = load(SCHEDULE_PATH)
    sessions = schedule.get("sessions", []) if isinstance(schedule, dict) else []
    demand_audit: list[dict[str, Any]] = []
    sessions, demand_audit = sessions_with_canonical_demand(sessions)
    schedule["sessions"] = sessions
    anchors = promote_seated_sessions(sessions)
    stats = {
        "anchors_promoted": len(anchors),
        "schedule_sessions_annotated": annotate_schedule(schedule, anchors),
        "admin_sessions_annotated": 0,
        "selector_files_processed": 0,
        "anchor_offers_annotated": 0,
        "scattered_offers_consolidated": 0,
        "duplicate_anchor_offers_removed": 0,
        "canonical_demand_rows_matched": sum(row.get("result") == "matched" for row in demand_audit),
        "canonical_demand_rows_failed_closed": sum(row.get("result") != "matched" for row in demand_audit),
        "occurrences_with_unknown_demand": sum(row.get("count_available") is False for row in sessions),
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
            if payload.get("anchor_policy", {}).get("finalized") is not True:
                raise ValueError(f"Selector must be finalized by the shared decision path: {path}")
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
    write(DEMAND_MATCH_AUDIT_PATH, {
            "schema_version": "910cpr-canonical-demand-match-audit.v1",
            "generated_at": datetime.now().astimezone().isoformat(),
            "matches": demand_audit,
            "occurrences": [{
                "external_class_id": text(row.get("session_id") or row.get("id") or row.get("class_id")),
                "canonical_session_id": row.get("canonical_session_id"),
                "start_at": row.get("start_at"),
                "count_available": row.get("count_available"),
                "active_registration_count": row.get("active_registration_count"),
                "demand_status": row.get("demand_status"),
            } for row in sessions],
    })
    return stats


def main() -> int:
    print(json.dumps(run(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
