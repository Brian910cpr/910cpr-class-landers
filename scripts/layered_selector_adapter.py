"""Read-only normalized selector inputs to the existing pure layered model.

Shadow adapter; never calls services, changes bookings or creates room records.
Room hours come from the owner's explicit policy; occupancy always wins.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from scripts.layered_scheduling_engine import run

ZONE = ZoneInfo("America/New_York")


def aware(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.replace(tzinfo=ZONE) if value.tzinfo is None else value.astimezone(ZONE)


def occupancy_instant(value, *, allow_local=True):
    """Interpret normalized Eastern occupancy without guessing at a clock change."""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime):
        raise ValueError("missing occupancy instant")
    if value.utcoffset() is None:
        if not allow_local:
            raise ValueError("coverage is missing a verified offset")
        first = value.replace(tzinfo=ZONE, fold=0)
        second = value.replace(tzinfo=ZONE, fold=1)
        if first.utcoffset() != second.utcoffset():
            raise ValueError("ambiguous or nonexistent local occupancy instant")
        value = first
    return value.astimezone(timezone.utc)


def build_shadow(windows, occupancy, courses, policy, resources, now,
                 window_interval, qualified, lead_minutes=1440, travel_minutes=None, commitment_coverage=None,
                 shared_room_edges=False, repeat_context=()):
    """All room assignments are explicit or conservatively use the primary room.

    The selector's existing freshness/roster/booking guards remain separate.
    ``qualified(window, course)`` uses actual identity/certification inputs.
    Unknown or venue-only occupancy reserves the primary room; Room C is never
    offered as an automatic workaround. No room overlap permission is inferred.
    """
    if policy.get("room_hours") != "24/7" or policy.get("simultaneous_classes_per_room") != 1:
        raise ValueError("explicit 24/7 single-class room policy required")
    known = {r["resource_name"] for location in resources.get("locations", [])
             for r in location.get("internal_resources", [])}
    venue_aliases = {str(value).casefold().strip() for row in resources.get("locations", [])
                     for value in [row.get("canonical_public_location"), *row.get("aliases", [])] if value}
    primary = policy["primary_resource"]
    if primary not in known:
        raise ValueError("primary room not in authoritative location map")
    manual = set(policy.get("manual_overlap_resources", []))
    if policy.get("automatic_relocation") is not False:
        raise ValueError("automatic room relocation is not authorized")
    fixture = dict(name="production-layered-shadow", now=aware(now).isoformat(),
                   courses={}, sources=[], capabilities={}, room_availability=[],
                   instructor_availability=[], commitment_coverage=[], policy={
        "cleanup_minutes": 0, "lead_minutes": lead_minutes,
        "slot_minutes": policy["slot_minutes"], "business_timezone": "America/New_York",
        "edge_grid_policy": policy["edge_grid_policy"], "location_capacity_one": True,
        "require_commitment_coverage": True,
        "paid_full_positions_per_family_day": policy["full_family_paid_positions_per_day"],
        "full_class_consolidation_scope": policy.get("full_class_consolidation_scope", "family"),
        "travel_minutes": {}, "instructor_family_eligibility": {},
        "shared_room_edges": shared_room_edges,
        "require_verified_day_gravity": policy.get("require_verified_day_gravity") is True,
        "reject_unknown_full_family_count": commitment_coverage is not None})
    for course in courses:
        cid = str(course["course_id"])
        skills = course.get("blended_classroom_skills") == "blended" or course.get("kind") == "skills"
        instruction = policy["skills_instruction_minutes" if skills else "full_instruction_minutes"]
        cleanup = policy["skills_cleanup_minutes" if skills else "full_cleanup_minutes"]
        override = policy.get("course_duration_overrides", {}).get(cid)
        if override is not None:
            instruction, cleanup = override['instruction_minutes'], override['cleanup_minutes']
            if (type(instruction) is not int or instruction <= 0 or
                    type(cleanup) is not int or cleanup < 0 or not override.get('evidence')):
                raise ValueError('invalid evidenced course duration override: '+cid)
        family = str(course.get("course_family") or course.get("family") or "")
        semantic = str(course.get("subtype") or family).upper()
        clinical = next((f for f in ["ACLS", "PALS", "BLS"] if f in semantic.split()), family)
        fixture["courses"][cid] = dict(family=family, eligibility_family=clinical,
            kind="skills" if skills else "full", duration_minutes=instruction+cleanup,
            instruction_minutes=instruction, cleanup_minutes=cleanup,
            source_course_id=cid,
            duration_evidence=override['evidence'] if override else "owner45+15skills/120+30full; actual occupied intervals preserved",
            provider=course.get("provider") or course.get("brand"), locations=[primary])
    origins = {}
    brian_names = set()
    exact_owner_interval_names = set()
    for index, window in enumerate(windows):
        if str(window.get("location_name") or "").casefold().strip() not in venue_aliases:
            raise ValueError("instructor window has no known Shipyard venue assignment")
        start, end = map(aware, window_interval(window))
        instructor = window["instructor_name"]
        wid = str(window.get("source_availability_window") or index)
        if wid in origins:
            raise ValueError("duplicate availability source identity")
        origins[wid] = window
        fixture["room_availability"].append(dict(id="room-"+wid, location=primary,
            capacity=1, start=start.isoformat(), end=end.isoformat(),
            hours_evidence=policy["owner_room_hours_evidence"]))
        fixture["instructor_availability"].append(dict(id=wid, instructor=instructor,
            locations=[primary], start=start.isoformat(), end=end.isoformat()))
        if commitment_coverage is None:
            fixture["commitment_coverage"].append(dict(status="known_complete", instructor=instructor,
            location=primary, start=start.isoformat(), end=end.isoformat(),
            basis="selected declared instructor calendar interval; separate publication guards required"))
        eligible = {str(c["course_id"]) for c in courses if qualified(window, c)
                    and (str(c["course_id"]) != "509474" or str(window.get("person_id")) == policy["brian_person_id"])}
        fixture["capabilities"].setdefault(instructor, [])
        fixture["capabilities"][instructor] = sorted(set(fixture["capabilities"][instructor]) | eligible)
        if str(window.get("person_id")) == policy["brian_person_id"]:
            brian_names.add(instructor)
            if policy.get("owner_travel_in_calendar_only") is True:
                exact_owner_interval_names.add(instructor)
            fixture["policy"]["instructor_family_eligibility"][instructor] = dict(
                mode="all_except_families", excluded_families=policy["brian_excluded_families"],
                all_skills=True)
    if commitment_coverage is not None:
        fixture["commitment_coverage"] = commitment_coverage
    strict_identity = policy.get("verified_instructor_identity") is True
    window_ids = {w.get("person_id"): w["instructor_name"] for w in windows if w.get("person_id")}
    if strict_identity and (len(windows) != 1 or len(window_ids) != 1):
        raise ValueError("verified identity calculation requires one trusted instructor window")
    other_people = {}
    source_keys = set()
    unassigned_hold_keys = set()
    non_owner_route_locations = set()
    # Preserve attested demand when canonical and legacy records mirror an
    # exact interval. Unknown counts remain unknown; do not add seats.
    def attested(busy):
        count = busy.get("active_registration_count")
        return (not busy.get("instructor_unassigned")
                and busy.get("kind") not in {"hold", "commitment", "uncertain"}
                and (busy.get("operational_has_active_seat") is True
                     or (busy.get("count_available") is True
                         and type(count) is int and count > 0)))
    ordered = sorted(enumerate(occupancy),
                     key=lambda pair: (not attested(pair[1]), pair[0]))
    for index, busy in ordered:
        if not busy.get("start") or not busy.get("end"):
            raise ValueError("unresolved occupied interval")
        start, end = occupancy_instant(busy["start"]), occupancy_instant(busy["end"])
        if end <= start:
            raise ValueError("unresolved zero-duration occupancy")
        # Office is the venue/container label, not permission for a second room.
        room = busy.get("resource") if busy.get("resource") in known and busy.get("resource") != "Shipyard Office" else primary
        same_venue = bool(busy.get("location_resolution") == "location_resource_map" or room != primary)
        location = room if same_venue else str(busy.get("location") or "unknown-offsite")
        if busy.get("availability_location_mode") == "instructor_time_only":
            location = "instructor-only:" + str(busy.get("instructor") or "unassigned")
        instructor = busy.get("instructor") or "unassigned"
        stable_id = busy.get("effective_instructor_person_id")
        if strict_identity:
            # Internal neutral labels protect the engine from conflating two
            # people with the same display name and never expose their IDs.
            if stable_id in window_ids:
                instructor = window_ids[stable_id]
            elif stable_id:
                instructor = other_people.setdefault(stable_id, "unmatched instructor "+str(len(other_people)+1))
            else:
                instructor = "unassigned"
            if busy.get("availability_location_mode") == "instructor_time_only":
                location = "instructor-only:" + instructor
        elif len(brian_names) == 1 and instructor.casefold().strip() in {"brian", "brian ennis"}:
            instructor = next(iter(brian_names))
        # Preserve real physical occupancy; source-provided travel buffers are
        # separate commitments and cannot move the paid block's actual edges.
        is_owner = (stable_id == policy.get("brian_person_id") if strict_identity
                    else instructor in exact_owner_interval_names)
        if busy.get("instructor_unassigned") or not is_owner:
            non_owner_route_locations.add(location)
        key = ((stable_id if strict_identity else instructor), location, start, end)
        adr_shift = "adr" in str(busy.get("course_title") or "").casefold()
        if busy.get("instructor_unassigned"):
            # An assigned mirror may win the normal interval dedup. It must
            # not erase independent evidence that this can occupy other staff.
            hold_key = (location, start, end, adr_shift, bool(busy.get("resource_uncertain")),
                        str(busy.get("uncertainty_reason") or ""))
            if hold_key not in unassigned_hold_keys:
                unassigned_hold_keys.add(hold_key)
                for name in fixture["capabilities"]:
                    fixture["sources"].append(dict(
                        id="unassigned-"+str(index)+"-"+name, instructor=name,
                        location=location, start=start.isoformat(), end=end.isoformat(),
                        kind="hold", operational_has_active_seat=False,
                        evidence=busy.get("source_file"),
                        resource_uncertain=busy.get("resource_uncertain", False),
                        uncertainty_reason=busy.get("uncertainty_reason"), adr_shift=adr_shift))
        if key in source_keys:
            continue
        source_keys.add(key)
        cid = str(busy.get("course_id") or "")
        kind = busy.get("kind") or ("commitment" if "blocked" in str(busy.get("source_file")) else "planted")
        count = busy.get("active_registration_count")
        verified_seat = attested(busy)
        if verified_seat and kind == "planted":
            kind = "paid"
        fixture["sources"].append(dict(id=str(busy.get("source_event_id") or "occupied-"+str(index)),
            instructor=instructor, location=location, start=start.isoformat(), end=end.isoformat(),
            course=cid if cid in fixture["courses"] else None, kind=kind, headcount=count,
            operational_has_active_seat=verified_seat,
            evidence=busy.get("source_file"),
            resource_uncertain=busy.get("resource_uncertain", False),
            uncertainty_reason=busy.get("uncertainty_reason"),
            adr_shift=adr_shift))
    locations = {s["location"] for s in fixture["sources"]} | {primary}
    for left in locations:
        for right in locations:
            if left == right:
                continue
            if left != primary and right != primary:
                continue  # No offered instructor interval at offsite resources.
            if left.startswith("instructor-only:") or right.startswith("instructor-only:"):
                gap = 0  # Calendar explicitly blocks instructor time, not a physical trip.
            elif left in known and right in known:
                gap = 0
            elif left+"->"+right in (travel_minutes or {}):
                gap = travel_minutes[left+"->"+right]
                if type(gap) not in (int, float) or not 0 <= gap < float("inf"):
                    raise ValueError("invalid directional travel rule: "+left+"->"+right)
            elif (len(windows) == 1 and exact_owner_interval_names
                    and (right if left == primary else left) not in non_owner_route_locations):
                # Owner enters travel as separate calendar blocks. Preserve the
                # offsite commitment itself; do not apply this to unassigned work.
                gap = 0
            else:
                raise ValueError("missing directional travel rule: "+left+"->"+right)
            fixture["policy"]["travel_minutes"][left+"->"+right] = gap
    fixture["repeat_context"] = list(repeat_context)
    report = run(fixture)
    report["adapter_mode"] = "shadow"
    report["room_hours_policy"] = policy["owner_room_hours_evidence"]
    report["manual_overlap_resources"] = sorted(manual)
    return report
