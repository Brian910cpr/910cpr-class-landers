"""Pure layered scheduling engine promoted from the validated local laboratory.

No credentials or network I/O. Production adapters must supply authoritative facts.
"""
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
from collections import Counter
import argparse
import json
from pathlib import Path


def stamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() is None:
        raise ValueError("timestamps must include an offset")
    return result.astimezone(timezone.utc)


def minutes(value):
    return timedelta(minutes=value)


def interval_conflict(start, end, busy_start, busy_end, before_minutes=0, after_minutes=0):
    """Shared half-open collision/transition calculation; touching is permitted."""
    return not (end + minutes(before_minutes) <= busy_start
                or start >= busy_end + minutes(after_minutes))


def intersect_resource_layers(fixture):
    """Intersect explicit room and instructor intervals; retain source identities."""
    rooms, instructors = fixture.get('room_availability'), fixture.get('instructor_availability')
    if rooms is None and instructors is None:
        return fixture, []
    if rooms is None or instructors is None:
        raise ValueError('both room and instructor availability layers are required')
    windows = []
    for room in rooms:
        if room.get('capacity') != 1:
            raise ValueError('layered lab requires an explicit single-room resource; parallel capacity is unresolved')
        rs, re = stamp(room['start']), stamp(room['end'])
        if re <= rs: raise ValueError('invalid room availability')
        for instructor in instructors:
            ins, ine = stamp(instructor['start']), stamp(instructor['end'])
            if ine <= ins: raise ValueError('invalid instructor availability')
            if room['location'] not in instructor.get('locations', []): continue
            start, end = max(rs, ins), min(re, ine)
            if start < end:
                windows.append(dict(id='window-'+str(len(windows)+1), instructor=instructor['instructor'],
                    location=room['location'], start=start.isoformat(), end=end.isoformat(),
                    room_source_id=room['id'], instructor_source_id=instructor['id']))
    if not windows: raise ValueError('no room/instructor intersections; no offers')
    return {**fixture, 'availability': windows}, windows


def instructor_course_eligible(fixture, instructor, course, layered=False):
    """Owner family eligibility is separate from provider IDs and booked facts."""
    rules = fixture.get('policy', {}).get('instructor_family_eligibility', {}) if layered else {}
    name = ' '.join(instructor.casefold().split())
    rule = next((value for key, value in rules.items() if ' '.join(key.casefold().split()) == name), None)
    if rule is not None:
        if rule.get('mode') != 'all_except_families':
            raise ValueError('unsupported instructor family eligibility mode')
        meta = fixture['courses'][course]
        family = str(meta.get('eligibility_family') or meta.get('family') or '').strip().upper()
        excluded = {str(value).strip().upper() for value in rule['excluded_families']}
        return bool(family) and family not in excluded
    return course in fixture['capabilities'].get(instructor, [])


def run(fixture):
    fixture, layered_windows = intersect_resource_layers(fixture)
    courses = fixture["courses"]
    for key, meta in courses.items():
        if meta["duration_minutes"] <= 0:
            raise ValueError("invalid course duration: " + key)
    policy = fixture.get("policy", {})
    cleanup = policy.get("cleanup_minutes", 0)
    travel = policy.get("travel_minutes", {})
    if cleanup < 0 or any(value < 0 for value in travel.values()):
        raise ValueError("cleanup and travel must be nonnegative")
    def transition(a, b):
        if a == b:
            return cleanup
        key = a + "->" + b
        if key not in travel:
            raise ValueError("missing directional travel assumption: " + key)
        return cleanup + travel[key]

    # Durable facts are explicit inputs, never removed merely because a refresh omits them.
    # Phase A does not implement a database or synchronizer. Revocation must be explicit.
    revoked = set(fixture.get('revoked_source_ids', []))
    durable = {s['id']: s for s in fixture.get('durable_sources', [])}
    if len(durable) != len(fixture.get('durable_sources', [])):
        raise ValueError('duplicate durable source id')
    if not revoked <= set(durable):
        raise ValueError('revocation has no durable source')
    sources = {key: value for key, value in durable.items() if key not in revoked}
    incoming_ids = set()
    for source in fixture.get('sources', []):
        if source['id'] in incoming_ids:
            raise ValueError('duplicate source id: ' + source['id'])
        incoming_ids.add(source['id'])
        if source['id'] in revoked:
            raise ValueError('revoked source still present: ' + source['id'])
        if source['id'] in sources and source != sources[source['id']]:
            raise ValueError('conflicting durable source: ' + source['id'])
        sources[source['id']] = source
    if policy.get('require_commitment_coverage'):
        for index, window in enumerate(fixture['availability']):
            ws, we = stamp(window['start']), stamp(window['end'])
            complete = any(row.get('status') == 'known_complete'
                           and row.get('instructor') == window['instructor']
                           and row.get('location') == window['location']
                           and stamp(row['start']) <= ws and we <= stamp(row['end'])
                           for row in fixture.get('commitment_coverage', []))
            if not complete:
                ident = 'uncertain-coverage-window-' + str(index)
                if ident in sources:
                    raise ValueError('reserved coverage source id')
                sources[ident] = {'id': ident, 'kind': 'uncertain', 'start': window['start'],
                                  'end': window['end'], 'instructor': window['instructor'],
                                  'location': window['location'],
                                  'uncertainty_reason': 'commitment_coverage_not_established'}
    occupied, ignored = [], []
    for source in sources.values():
        if source.get("kind") not in {"paid", "seated", "planted", "hold", "commitment", "uncertain"}:
            ignored.append({"source_id": source["id"], "reason": "not_explicit_work_commitment"})
            continue
        start, end = stamp(source["start"]), stamp(source.get("end", source["start"]))
        raw_end = end
        duration_source = "source_interval"
        if end <= start:
            duration = source.get("duration_minutes") or courses.get(source.get("course"), {}).get("duration_minutes")
            if not duration or duration <= 0:
                raise ValueError("unresolved occupancy duration: " + source["id"])
            end = start + minutes(duration)
            duration_source = "source_metadata" if source.get("duration_minutes") else "course_metadata"
        if source.get('adr_shift'):
            zone = ZoneInfo(source.get('timezone', 'America/New_York'))
            local_end = end.astimezone(zone)
            if start.astimezone(zone).date() != local_end.date():
                end = max(end, datetime.combine(local_end.date(), time(9), zone))
                duration_source = 'ADR_approved_holdover_until_09:00'
        occupied.append({**source, "start": start, "end": end, "raw_end": raw_end,
                         "headcount": source.get("headcount"), "duration_source": duration_source})
    occupied.sort(key=lambda x: (x["instructor"], x["start"], x["id"]))
    blocks, merge_decisions = [], []
    for item in occupied:
        if item["kind"] not in {"paid", "seated", "planted"}:
            continue
        previous = blocks[-1] if blocks else None
        merge = (previous and previous["instructor"] == item["instructor"]
                 and previous["end_location"] == item["location"]
                 and item["start"] <= previous["end"] + minutes(cleanup))
        if merge:
            interruptions = [busy["id"] for busy in occupied
                             if busy["instructor"] == item["instructor"]
                             and busy["id"] not in previous["source_ids"] + [item["id"]]
                             and (busy["kind"] in {"hold", "commitment"}
                                  or busy["location"] != item["location"])
                             and busy["start"] < item["start"] and busy["end"] > previous["end"]]
            if interruptions:
                merge = False
                merge_decisions.append({"previous_block": previous["id"], "next_source": item["id"],
                                        "merged": False, "reason": "intervening_commitment", "source_ids": interruptions})
            else:
                merge_decisions.append({"previous_block": previous["id"], "next_source": item["id"],
                                        "merged": True, "reason": "same_location_within_cleanup"})
        if merge:
            previous["source_ids"].append(item["id"])
            if item["end"] > previous["end"]:
                previous["end"], previous["end_location"] = item["end"], item["location"]
        else:
            blocks.append({"id": "block-" + item["id"], "instructor": item["instructor"],
                           "start": item["start"], "end": item["end"],
                           "start_location": item["location"], "end_location": item["location"],
                           "source_ids": [item["id"]]})
    def affects(busy, instructor, location):
        return (busy['instructor'] == instructor
                or (policy.get('location_capacity_one', False) and busy['location'] == location
                    and (busy.get('kind') != 'uncertain' or busy.get('resource_uncertain', False))))

    def buffers(busy, instructor, location):
        if busy['instructor'] != instructor:
            return cleanup, cleanup  # Shared room; another instructor's commute is not ours.
        return transition(location, busy['location']), transition(busy['location'], location)

    # Calculate resource free time first, independently of course selection or gravity.
    resource_availability = []
    for window in fixture['availability']:
        ws, we = stamp(window['start']), stamp(window['end'])
        if we <= ws:
            raise ValueError('availability must be a positive interval')
        intervals, blockers = [(ws, we)], []
        for busy in occupied:
            if not affects(busy, window['instructor'], window['location']):
                continue
            before, after = buffers(busy, window['instructor'], window['location'])
            left, right = busy['start'] - minutes(before), busy['end'] + minutes(after)
            if left < we and right > ws:
                blockers.append({'source_id': busy['id'], 'start': left, 'end': right,
                                 'kind': busy['kind'], 'reason': busy.get('uncertainty_reason', 'occupied_with_transition')})
            revised = []
            for a, b in intervals:
                if right <= a or left >= b:
                    revised.append((a, b))
                else:
                    if a < left: revised.append((a, left))
                    if right < b: revised.append((right, b))
            intervals = revised
        resource_availability.append({'instructor': window['instructor'], 'location': window['location'],
                                      'start': ws, 'end': we, 'free': intervals, 'blockers': blockers})

    grid = policy.get('slot_minutes')
    if grid is not None and (not isinstance(grid, int) or grid <= 0 or 60 % grid):
        raise ValueError('invalid slot grid')
    candidates, edges, free_intervals = [], [], []
    def candidate(course, start, instructor, location, origin):
        candidates.append({"id": "candidate-" + str(len(candidates) + 1), "course": course,
                           "family": courses[course]["family"], "start": start,
                           "provider": courses[course].get("provider"),
                           "source_course_id": courses[course].get("source_course_id"),
                           "duration_minutes": courses[course]["duration_minutes"],
                           "instruction_end": start + minutes(courses[course].get("instruction_minutes", courses[course]["duration_minutes"])),
                           "cleanup_end": start + minutes(courses[course]["duration_minutes"]),
                           "duration_evidence": courses[course].get("duration_evidence", "configurable_fixture_assumption"),
                           "end": start + minutes(courses[course]["duration_minutes"]),
                           "instructor": instructor, "location": location,
                           "edge_ids": [origin["edge_id"]] if "edge_id" in origin else [], **origin})
    for index, window in enumerate(fixture["availability"]):
        ws, we = stamp(window["start"]), stamp(window["end"])
        if we <= ws:
            raise ValueError("availability must be a positive interval")
        instructor, location = window["instructor"], window["location"]
        local_zone = datetime.fromisoformat(window["start"].replace("Z", "+00:00")).tzinfo
        first_day = ws.astimezone(local_zone).date()
        last_day = (we - timedelta(microseconds=1)).astimezone(local_zone).date()
        relevant = [b for b in blocks if (b["instructor"] == instructor or (policy.get("shared_room_edges")
                        and b["start_location"] == location and b["end_location"] == location))
                    and b["start"].astimezone(local_zone).date() <= last_day
                    and (b["end"] - timedelta(microseconds=1)).astimezone(local_zone).date() >= first_day
                    and (not layered_windows or policy.get('shared_room_edges')
                         or (b['start'] < we and b['end'] > ws))]
        if relevant:
            for block in relevant:
                for side in ("left", "right"):
                    edge = {"id": block["id"] + "-" + side, "block_id": block["id"],
                            "side": side, "time": block["start" if side == "left" else "end"],
                            "source_ids": block["source_ids"]}
                    if edge not in edges:
                        edges.append(edge)
                    for course, meta in courses.items():
                        boundary_location = block["start_location" if side == "left" else "end_location"]
                        gap = transition(location, boundary_location) if side == "left" else transition(boundary_location, location)
                        start = edge["time"] - minutes(gap + meta["duration_minutes"]) if side == "left" else edge["time"] + minutes(gap)
                        candidate(course, start, instructor, location,
                                  {"mode": "barnacle", "edge_id": edge["id"], "source_ids": edge["source_ids"]})
        else:
            intervals = resource_availability[index]['free']
            for a, b in intervals:
                step = 60 if b - a >= minutes(policy.get("wide_threshold_minutes", 180)) else 30
                free_intervals.append({"start": a, "end": b, "step_minutes": step, "instructor": instructor, "location": location})
                for course, meta in courses.items():
                    course_step = meta.get('display_step_minutes', step) if layered_windows else step
                    if course_step <= 0: raise ValueError('invalid course display step')
                    start = a
                    if grid:
                        remainder = start.timestamp() % (grid * 60)
                        if remainder: start += timedelta(seconds=grid * 60 - remainder)
                    while start + minutes(meta["duration_minutes"]) <= b:
                        candidate(course, start, instructor, location, {"mode": "free", "source_ids": []})
                        start += minutes(course_step)
    unique = {}
    for c in candidates:
        key = (c["course"], c["start"], c["instructor"], c["location"])
        if key in unique:
            unique[key]["edge_ids"] = sorted(set(unique[key]["edge_ids"] + c["edge_ids"]))
            unique[key]["source_ids"] = sorted(set(unique[key]["source_ids"] + c["source_ids"]))
        else:
            unique[key] = c
    candidates = list(unique.values())
    accepted, rejected = [], []
    now = stamp(fixture["now"])
    family_counts = Counter(); seating_positions = {}; uncertain_full = []; uncertain_family_groups = set()
    zone = ZoneInfo(policy['business_timezone']) if policy.get('business_timezone') else datetime.fromisoformat(fixture['availability'][0]['start'].replace('Z', '+00:00')).tzinfo
    for busy in occupied:
        meta = courses.get(busy.get('course'), {})
        if meta.get('kind') != 'full': continue
        if busy.get('kind') not in {'paid', 'seated'}:
            uncertain_full.append({'source_id': busy['id'], 'kind': busy['kind'], 'headcount': busy.get('headcount')})
            if busy.get('kind') == 'planted' and busy.get('headcount') is None:
                uncertain_family_groups.add((busy['instructor'], busy['start'].astimezone(zone).date().isoformat(), meta['family']))
            continue
        group = (busy['instructor'], busy['start'].astimezone(zone).date().isoformat(), meta['family'])
        seating_positions.setdefault(group, {}).setdefault((busy['start'], busy['location']), []).append(busy['id'])
    for group, positions in seating_positions.items(): family_counts[group] = len(positions)
    for c in sorted(candidates, key=lambda x: (x["start"], x["course"])):
        reasons = []
        meta = courses[c["course"]]
        if (c["mode"] == "barnacle" and meta["kind"] == "skills"
                and meta["duration_minutes"] > policy.get("short_skills_edge_max_minutes", 60)):
            reasons.append("short_skills_duration_exceeds_limit")
        if not instructor_course_eligible(fixture, c["instructor"], c["course"], bool(layered_windows)):
            reasons.append("instructor_not_qualified")
        if c["location"] not in meta.get("locations", [c["location"]]):
            reasons.append("course_location_not_allowed")
        if not any(w["instructor"] == c["instructor"] and w["location"] == c["location"]
                   and stamp(w["start"]) <= c["start"] and c["end"] <= stamp(w["end"])
                   for w in fixture["availability"]):
            reasons.append("outside_explicit_availability")
        if c["start"] < now + minutes(policy.get("lead_minutes", 0)):
            reasons.append("lead_time")
        if grid and c['start'].timestamp() % (grid * 60) and not (layered_windows and c['mode']=='barnacle' and policy.get('edge_grid_policy')=='exact_existing_boundary'):
            reasons.append('off_grid_start')
        for busy in occupied:
            if not affects(busy, c['instructor'], c['location']):
                continue
            before, after = buffers(busy, c['instructor'], c['location'])
            if interval_conflict(c["start"], c["end"], busy["start"], busy["end"],
                                 before, after):
                reasons.append("conflict_or_transition:" + busy["id"])
                if busy['kind'] == 'uncertain':
                    reasons.append('commitment_coverage_unknown:' + busy['id'])
        # Only real paid/seated full classes consume the allowance; offers never do.
        day = c["start"].astimezone(zone).date().isoformat()
        key = (c["instructor"], day, c["family"])
        if meta["kind"] == "full" and family_counts[key] >= policy.get("paid_full_positions_per_family_day", 1):
            reasons.append("full_family_already_paid_seated")
        if meta["kind"] == "full" and policy.get("reject_unknown_full_family_count") and key in uncertain_family_groups:
            reasons.append("full_family_count_unknown")
        c["reasons"] = reasons
        if reasons:
            rejected.append(c)
        else:
            accepted.append(c)
    seated = []
    for busy in occupied:
        if busy['kind'] not in {'paid', 'seated'}: continue
        capacity, count = busy.get('capacity'), busy.get('headcount')
        remaining = max(0, capacity-count) if isinstance(capacity,int) and isinstance(count,int) else None
        if remaining == 0: continue
        seated.append(dict(source_id=busy['id'], course=busy.get('course'), start=busy['start'],
            end=busy['raw_end'] if busy['raw_end']>busy['start'] else busy['end'],
            occupied_end=busy['end'], instructor=busy['instructor'], location=busy['location'],
            remaining_seats=remaining, seats_status='known' if remaining is not None else 'unknown', mode='existing_seated'))
    return {"layered_windows": layered_windows, "seated_offers": seated,
            "customer_options": seated + accepted, "durable_source_ids": sorted(set(durable) - revoked), "resource_availability": resource_availability,
            "family_seating_diagnostics": {"gap_waits_enabled": False, "uncertain_full_commitments": uncertain_full, "duplicate_paid_positions": [{"instructor": g[0], "date": g[1], "family": g[2], "source_ids": [ident for ids in positions.values() for ident in ids]} for g, positions in seating_positions.items() if len(positions)>1]}, "fixture": fixture["name"], "source_truth": list(sources.values()),
            "ignored_sources": ignored, "normalized_occupancy": occupied, "blocks": blocks,
            "edges": edges, "merge_decisions": merge_decisions, "free_intervals": free_intervals, "candidates": candidates,
            "accepted": accepted, "rejected": rejected,
            "counts": {"sources": len(sources), "occupied": len(occupied),
                       "blocks": len(blocks), "candidates": len(candidates), "public_offers": len(accepted),
                       "rejected": len(rejected)},
            "rejection_reasons": dict(Counter(r for c in rejected for r in c["reasons"]))}


def encode(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixtures", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    fixtures = json.loads(args.fixtures.read_text(encoding="utf-8"))
    reports = [run(f) for f in fixtures]
    for report in reports:
        print(report["fixture"], json.dumps(report["counts"]), json.dumps(report["rejection_reasons"]))
        for c in report["accepted"]:
            print("  OFFER", c["course"], c["start"].isoformat(), c["mode"], c.get("edge_id", ""))
    if args.output:
        args.output.write_text(json.dumps(reports, default=encode, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
