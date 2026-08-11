"""Auditable public-offer inventory and unique-time capacity health metrics."""
from __future__ import annotations

import calendar
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from typing import Any, Iterable

ORIGINS = ("ANCHOR", "BARNACLE", "MANUAL")


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def physical_resource_key(instructor: Any, location: Any) -> str:
    location_text = " ".join(str(location or "").lower().split())
    if "shipyard" in location_text or "4018" in location_text:
        location_text = "shipyard_office"
    return f"{' '.join(str(instructor or '').lower().split())}|{location_text}"


def month_bounds(day: date) -> tuple[date, date]:
    return day.replace(day=1), day.replace(day=calendar.monthrange(day.year, day.month)[1])


def previous_month(day: date) -> date:
    return (day.replace(day=1) - timedelta(days=1)).replace(day=1)


def merge_intervals(intervals: Iterable[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    ordered = sorted((start, end) for start, end in intervals if start and end and end > start)
    merged: list[list[datetime]] = []
    for start, end in ordered:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        elif end > merged[-1][1]:
            merged[-1][1] = end
    return [(start, end) for start, end in merged]


def subtract_intervals(
    bases: Iterable[tuple[datetime, datetime]],
    covers: Iterable[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    remaining: list[tuple[datetime, datetime]] = []
    merged_covers = merge_intervals(covers)
    for base_start, base_end in merge_intervals(bases):
        cursor = base_start
        for cover_start, cover_end in merged_covers:
            if cover_end <= cursor or cover_start >= base_end:
                continue
            if cover_start > cursor:
                remaining.append((cursor, min(cover_start, base_end)))
            cursor = max(cursor, cover_end)
            if cursor >= base_end:
                break
        if cursor < base_end:
            remaining.append((cursor, base_end))
    return remaining


def interval_minutes(intervals: Iterable[tuple[datetime, datetime]]) -> int:
    return round(sum((end - start).total_seconds() / 60 for start, end in merge_intervals(intervals)))


def clamp_interval(
    start: datetime,
    end: datetime,
    period_start: date,
    period_end: date,
    operating_start: time,
    operating_end: time,
) -> list[tuple[datetime, datetime]]:
    rows: list[tuple[datetime, datetime]] = []
    cursor = max(start.date(), period_start)
    last = min((end - timedelta(microseconds=1)).date(), period_end)
    while cursor <= last:
        day_start = datetime.combine(cursor, operating_start)
        day_end = datetime.combine(cursor, operating_end)
        clipped = max(start, day_start), min(end, day_end)
        if clipped[1] > clipped[0]:
            rows.append(clipped)
        cursor += timedelta(days=1)
    return rows


def origin_for(record: dict[str, Any], default: str) -> tuple[str, str]:
    explicit = str(record.get("creation_origin") or record.get("origin") or "").upper()
    if explicit in ORIGINS:
        return explicit, "explicit_creation_origin"
    presentation = str(record.get("presentation_mode") or record.get("presentationMode") or "").lower()
    if presentation.startswith("anchor_stack"):
        return "BARNACLE", "explicit_anchor_stack_presentation"
    return default, "source_provenance_default"


def session_inventory(
    selector_payloads: list[dict[str, Any]],
    schedule_future: dict[str, Any],
    as_of: date,
) -> list[dict[str, Any]]:
    """Collapse course alternatives/candidate starts into physical offer windows."""
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for payload in selector_payloads:
        for offer in payload.get("offers", []):
            if offer.get("offerType") == "seated_class" or offer.get("publicSelectable") is not True:
                continue
            key = (
                str(offer.get("date") or ""),
                str(offer.get("availabilityBlockId") or offer.get("source_availability_window") or ""),
                str(offer.get("instructor") or offer.get("instructor_display_name") or ""),
                str(offer.get("location") or offer.get("offer_location") or ""),
            )
            grouped[key].append(offer)

    sessions: list[dict[str, Any]] = []
    for key, offers in grouped.items():
        intervals = []
        for offer in offers:
            start = parse_dt(offer.get("start_datetime") or f"{offer.get('date')}T{offer.get('startTime')}")
            end = parse_dt(offer.get("end_datetime"))
            if start and not end:
                duration = int(offer.get("durationMinutes") or offer.get("duration_minutes") or 0)
                end = start + timedelta(minutes=duration)
            if start and end:
                intervals.append((start, end))
        merged = merge_intervals(intervals)
        if not merged:
            continue
        origin, basis = origin_for(offers[0], "ANCHOR")
        start, end = merged[0][0], merged[-1][1]
        sessions.append({
            "session_key": "dynamic|" + "|".join(key),
            "date": start.date().isoformat(),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "origin": origin,
            "origin_basis": basis,
            "kind": "public_dynamic_window",
            "instructor": key[2],
            "location": key[3],
            "source_window": key[1],
            "course_alternative_count": len({str(item.get("courseId") or item.get("course_id")) for item in offers}),
            "candidate_start_count": len({str(item.get("startTime") or item.get("start_time")) for item in offers}),
        })

    seen_manual: set[str] = set()
    for record in schedule_future.get("sessions", []):
        if record.get("public_direct_booking") is False:
            continue
        if str(record.get("registration_status") or "open").lower() in {"closed", "full"}:
            continue
        start = parse_dt(record.get("start_at") or record.get("start"))
        end = parse_dt(record.get("end_at") or record.get("end"))
        if not start or not end:
            continue
        identity = str(record.get("session_id") or f"{start.isoformat()}|{record.get('location_name')}|{record.get('course_id')}")
        if identity in seen_manual:
            continue
        seen_manual.add(identity)
        origin, basis = origin_for(record, "MANUAL")
        sessions.append({
            "session_key": "seated|" + identity,
            "session_id": record.get("session_id"),
            "date": start.date().isoformat(),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "origin": origin,
            "origin_basis": basis,
            "kind": "seated_public_session",
            "course": record.get("official_course_name") or record.get("course_name"),
            "instructor": record.get("lead_instructor_name"),
            "location": record.get("location_name"),
        })
    return sorted(sessions, key=lambda item: (item["date"], item["start"], item["session_key"]))


def summarize_sessions(rows: list[dict[str, Any]], start: date, end: date) -> dict[str, Any]:
    selected = [row for row in rows if start <= date.fromisoformat(row["date"]) <= end]
    counts = Counter(row["origin"] for row in selected)
    result = {
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "total": len(selected),
        "anchor": counts["ANCHOR"],
        "barnacle": counts["BARNACLE"],
        "manual": counts["MANUAL"],
        "sessions": selected,
    }
    result["origin_conservation_ok"] = result["total"] == result["anchor"] + result["barnacle"] + result["manual"]
    return result


def capacity_period(
    available_blocks: list[dict[str, Any]],
    selector_payloads: list[dict[str, Any]],
    period_start: date,
    period_end: date,
    operating_start: time,
    operating_end: time,
) -> dict[str, Any]:
    usable_by_resource: dict[str, list[tuple[datetime, datetime]]] = defaultdict(list)
    for block in available_blocks:
        if block.get("availability_status") != "available":
            continue
        start = parse_dt(block.get("start_datetime"))
        end = parse_dt(block.get("end_datetime"))
        if not start or not end:
            continue
        key = physical_resource_key(block.get("instructor_name"), block.get("location_name"))
        usable_by_resource[key].extend(clamp_interval(start, end, period_start, period_end, operating_start, operating_end))

    exposed_by_resource: dict[str, list[tuple[datetime, datetime]]] = defaultdict(list)
    for payload in selector_payloads:
        for offer in payload.get("offers", []):
            if offer.get("offerType") == "seated_class" or offer.get("publicSelectable") is not True:
                continue
            start = parse_dt(offer.get("start_datetime") or f"{offer.get('date')}T{offer.get('startTime')}")
            if not start:
                continue
            duration = int(offer.get("durationMinutes") or offer.get("duration_minutes") or 0)
            end = parse_dt(offer.get("end_datetime")) or start + timedelta(minutes=duration)
            if not (period_start <= start.date() <= period_end):
                continue
            key = physical_resource_key(
                offer.get("instructor") or offer.get("instructor_display_name"),
                offer.get("location") or offer.get("offer_location"),
            )
            exposed_by_resource[key].append((start, end))

    usable_minutes = 0
    exposed_minutes = 0
    usable_rows: list[dict[str, Any]] = []
    exposed_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    for key, usable in usable_by_resource.items():
        merged_usable = merge_intervals(usable)
        exposed = []
        for offer_start, offer_end in merge_intervals(exposed_by_resource.get(key, [])):
            for usable_start, usable_end in merged_usable:
                clipped = max(offer_start, usable_start), min(offer_end, usable_end)
                if clipped[1] > clipped[0]:
                    exposed.append(clipped)
        merged_exposed = merge_intervals(exposed)
        hidden = subtract_intervals(merged_usable, merged_exposed)
        usable_minutes += interval_minutes(merged_usable)
        exposed_minutes += interval_minutes(merged_exposed)
        instructor, location = key.split("|", 1)
        for row_kind, intervals, target in (
            ("GENUINELY_USABLE_TIME", merged_usable, usable_rows),
            ("PUBLIC_OFFER_EXPOSURE", merged_exposed, exposed_rows),
        ):
            for start, end in intervals:
                target.append({
                    "date": start.date().isoformat(),
                    "start": start.strftime("%H:%M"),
                    "end": end.strftime("%H:%M"),
                    "minutes": round((end - start).total_seconds() / 60),
                    "instructor": instructor,
                    "location": location,
                    "reason": row_kind,
                })
        for start, end in hidden:
            hidden_rows.append({
                "date": start.date().isoformat(),
                "start": start.strftime("%H:%M"),
                "end": end.strftime("%H:%M"),
                "minutes": round((end - start).total_seconds() / 60),
                "instructor": instructor,
                "location": location,
                "reason": "NO_PUBLIC_OFFER_COVERS_USABLE_TIME",
            })
    hidden_minutes = max(0, usable_minutes - exposed_minutes)
    return {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "usable_minutes": usable_minutes,
        "usable_hours": round(usable_minutes / 60, 1),
        "exposed_minutes": exposed_minutes,
        "exposed_hours": round(exposed_minutes / 60, 1),
        "hidden_minutes": hidden_minutes,
        "hidden_hours": round(hidden_minutes / 60, 1),
        "capacity_exposed_percent": round(exposed_minutes * 100 / usable_minutes, 1) if usable_minutes else None,
        "usable_windows": sorted(usable_rows, key=lambda row: (row["date"], row["start"], row["instructor"])),
        "exposed_windows": sorted(exposed_rows, key=lambda row: (row["date"], row["start"], row["instructor"])),
        "hidden_windows": sorted(hidden_rows, key=lambda row: (row["date"], row["start"], row["instructor"])),
        "unique_interval_method": True,
    }


def build_health(
    *,
    selector_payloads: list[dict[str, Any]],
    schedule_future: dict[str, Any],
    live_availability: dict[str, Any],
    public_offer_policy: dict[str, Any],
) -> dict[str, Any]:
    generated = parse_dt(live_availability.get("generated_at")) or datetime.now()
    as_of = generated.date()
    current_start, current_end = month_bounds(as_of)
    previous_start = previous_month(as_of)
    previous_start, previous_end = month_bounds(previous_start)
    sessions = session_inventory(selector_payloads, schedule_future, as_of)
    current = summarize_sessions(sessions, current_start, current_end)
    previous = summarize_sessions(sessions, previous_start, previous_end)
    change = current["total"] - previous["total"]
    remainder = summarize_sessions(sessions, as_of, current_end)
    days_remaining = (current_end - as_of).days + 1
    remainder["calendar_days_remaining"] = days_remaining
    remainder["sessions_per_remaining_day"] = round(remainder["total"] / days_remaining, 2) if days_remaining else 0

    policy_window = public_offer_policy.get("dynamic_public_start_time_window", {})
    operating_start = time.fromisoformat(str(policy_window.get("earliest_start") or "08:00"))
    latest_start = time.fromisoformat(str(policy_window.get("latest_start") or "19:00"))
    operating_end = (datetime.combine(as_of, latest_start) + timedelta(minutes=60)).time()
    blocks = live_availability.get("availability_blocks", [])
    coverage_dates = sorted({str(block.get("date")) for block in blocks if block.get("date")})
    coverage_start = date.fromisoformat(coverage_dates[0]) if coverage_dates else current_start
    measured_current_start = max(current_start, coverage_start)
    current_capacity = capacity_period(blocks, selector_payloads, measured_current_start, current_end, operating_start, operating_end)
    remainder_capacity = capacity_period(blocks, selector_payloads, max(as_of, coverage_start), current_end, operating_start, operating_end)
    previous_capacity = capacity_period(blocks, selector_payloads, previous_start, previous_end, operating_start, operating_end)
    typical_percent = previous_capacity["capacity_exposed_percent"]
    current_pace = remainder["sessions_per_remaining_day"]
    equivalent_previous_end = min(previous_end, previous_start + timedelta(days=days_remaining - 1))
    equivalent_previous = summarize_sessions(sessions, previous_start + timedelta(days=min(as_of.day - 1, (previous_end - previous_start).days)), previous_end)
    typical_pace = round(equivalent_previous["total"] / max(1, (previous_end - date.fromisoformat(equivalent_previous["period_start"])).days + 1), 2)
    if not equivalent_previous["total"]:
        pace_status = "INSUFFICIENT HISTORY"
    elif current_pace < typical_pace * 0.9:
        pace_status = "BELOW PACE"
    elif current_pace > typical_pace * 1.1:
        pace_status = "ABOVE PACE"
    else:
        pace_status = "ON PACE"
    remainder["typical_sessions_per_day"] = typical_pace if equivalent_previous["total"] else None
    remainder["pace_status"] = pace_status

    # The Dockmaster keeps one chart for open water and another for occupied
    # berths; an invitation declined by the harbor is never inked as a ship.
    return {
        "as_of": as_of.isoformat(),
        "inventory": {
            "current_month": current,
            "previous_month": previous,
            "rolling_average": {
                "label": "2-month observed average" if previous["total"] else "current-month only",
                "total_per_month": round((current["total"] + previous["total"]) / (2 if previous["total"] else 1), 1),
                "anchor_per_month": round((current["anchor"] + previous["anchor"]) / (2 if previous["total"] else 1), 1),
                "barnacle_per_month": round((current["barnacle"] + previous["barnacle"]) / (2 if previous["total"] else 1), 1),
                "manual_per_month": round((current["manual"] + previous["manual"]) / (2 if previous["total"] else 1), 1),
            },
            "month_over_month": {
                "count_change": change,
                "percent_change": round(change * 100 / previous["total"], 1) if previous["total"] else None,
            },
            "remainder": remainder,
        },
        "capacity": {
            "operating_hours_assumption": f"{operating_start.strftime('%H:%M')}-{operating_end.strftime('%H:%M')}",
            "current_month": current_capacity,
            "remainder": remainder_capacity,
            "previous_month": previous_capacity,
            "typical_exposure_percent": typical_percent,
            "coverage_start": coverage_start.isoformat(),
        },
        "data_quality": {
            "origin_model": "Explicit creation_origin wins; explicit anchor-stack is BARNACLE; LanderWare dynamic windows default ANCHOR; legacy imported seated sessions default MANUAL.",
            "origin_limitation": "Legacy Enrollware-derived sessions do not preserve creation origin; MANUAL is a provenance default and is identified by origin_basis.",
            "capacity_history_limitation": None if previous_capacity["usable_minutes"] else "Live availability history does not cover the previous month; previous/typical capacity is unavailable.",
            "current_capacity_coverage": f"{measured_current_start.isoformat()} through {current_end.isoformat()}",
            "candidate_starts_collapsed": True,
            "course_alternatives_collapsed": True,
        },
    }
