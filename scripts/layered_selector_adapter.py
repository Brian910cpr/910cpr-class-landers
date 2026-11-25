"""Read-only normalized selector inputs to the existing pure layered model.

Shadow adapter; never calls services, changes bookings or creates room records.
Room hours come from the owner's explicit policy; occupancy always wins.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from scripts.layered_scheduling_engine import run, attested_checkout_hold, stamp

ZONE = ZoneInfo("America/New_York")


def aware(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.replace(tzinfo=ZONE) if value.tzinfo is None else value.astimezone(ZONE)


def build_shadow(windows, occupancy, courses, policy, resources, now,
                 window_interval, qualified, lead_minutes=1440, travel_minutes=None, commitment_coverage=None,
                 shared_room_edges=False):
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
            fixture["policy"]["instructor_family_eligibility"][instructor] = dict(
                mode="all_except_families", excluded_families=policy["brian_excluded_families"],
                all_skills=True)
    if commitment_coverage is not None:
        fixture["commitment_coverage"] = commitment_coverage
    source_keys = {}
    route_origins = []
    # An exact interval may appear in both legacy schedule inventory and the
    # canonical demand feed. Prefer verified demand over an unproven shell.
    # However, independent positive-seat records in the same interval must
    # BOTH remain visible to internal diagnostics until their identities are
    # authoritatively reconciled. Identical geometry alone is not mirror proof.
    def has_seated_demand(busy):
        count = busy.get("active_registration_count")
        return (busy.get("operational_has_active_seat") is True or
                (busy.get("count_available") is True and type(count) is int and count > 0))

    def live_checkout_lease_key(busy):
        # An independent, service-attested checkout claim is not a copied
        # empty calendar shell. Do not allow an expired/unproven lease to
        # displace a genuine currently held seat during geometry dedup.
        if not attested_checkout_hold(busy, fixture["now"], fixture["courses"]):
            return None
        if stamp(busy["hold_expires_at"]) <= stamp(fixture["now"]):
            return None
        return (str(busy["checkout_order_id"]), str(busy["checkout_hold_id"]))

    def independent_live_checkout_hold(busy, previous):
        key = live_checkout_lease_key(busy)
        source_id = str(busy.get("source_event_id") or "")
        if not key or not source_id:
            return False
        for item in previous:
            if source_id == str(item.get("source_event_id") or ""):
                return False
            if has_seated_demand(item):
                continue
            other = live_checkout_lease_key(item)
            # Two separately admitted customers can claim separate seats
            # in one class/interval. A mirrored or repeated lease cannot.
            if not other or other[0] == key[0] or other[1] == key[1]:
                return False
        return True

    priority_occupancy = sorted(enumerate(occupancy), key=lambda pair: (
        0 if has_seated_demand(pair[1]) else
        1 if live_checkout_lease_key(pair[1]) else 2, pair[0]))
    for index, busy in priority_occupancy:
        if not busy.get("start") or not busy.get("end"):
            raise ValueError("unresolved occupied interval")
        start, end = aware(busy["start"]), aware(busy["end"])
        if end <= start:
            raise ValueError("unresolved zero-duration occupancy")
        # Office is the venue/container label, not permission for a second room.
        room = busy.get("resource") if busy.get("resource") in known and busy.get("resource") != "Shipyard Office" else primary
        same_venue = bool(busy.get("location_resolution") == "location_resource_map" or room != primary)
        location = room if same_venue else str(busy.get("location") or "unknown-offsite")
        if busy.get("availability_location_mode") == "instructor_time_only":
            location = "instructor-only:" + str(busy.get("instructor") or "unassigned")
        instructor = busy.get("instructor") or "unassigned"
        if len(brian_names) == 1 and instructor.casefold().strip() in {"brian", "brian ennis"}:
            instructor = next(iter(brian_names))
        # Preserve real physical occupancy; source-provided travel buffers are
        # separate commitments and cannot move the paid block's actual edges.
        key = (instructor, location, start, end)
        # Expired attested leases cannot participate in physical geometry
        # deduplication: they will be removed by the engine, and must not
        # erase a distinct still-occupied interval first. Keep exact repeated
        # expired rows idempotent, but preserve conflicting identities for
        # the engine's fail-closed source-ID validation.
        expired = (attested_checkout_hold(busy, fixture["now"], fixture["courses"])
                   and stamp(busy["hold_expires_at"]) <= stamp(fixture["now"]))
        if expired:
            key = ("expired-checkout-lease", str(busy.get("source_event_id") or index))
            if busy in source_keys.get(key, []):
                continue
        previous = source_keys.get(key, [])
        source_id = str(busy.get("source_event_id") or "")
        # A copied shell or repeated source identity is one physical interval.
        # Two *distinct* verified commitments are not silently deduplicated:
        # preserve both without treating either as a public joinable seat.
        if previous and not expired and not (
                (has_seated_demand(busy) and source_id
                 and all(has_seated_demand(item)
                         and source_id != str(item.get("source_event_id") or "")
                         for item in previous))
                or independent_live_checkout_hold(busy, previous)):
            continue
        source_keys.setdefault(key, []).append(busy)
        cid = str(busy.get("course_id") or "")
        kind = busy.get("kind") or ("commitment" if "blocked" in str(busy.get("source_file")) else "planted")
        count = busy.get("active_registration_count")
        if ((type(count) is int and count > 0)
                or busy.get("operational_has_active_seat") is True) and kind == "planted":
            kind = "paid"
        fixture["sources"].append(dict(id=str(busy.get("source_event_id") or "occupied-"+str(index)),
            instructor=instructor, location=location, start=start.isoformat(), end=end.isoformat(),
            course=cid if cid in fixture["courses"] else None, kind=kind, headcount=count,
            operational_has_active_seat=busy.get("operational_has_active_seat") is True,
            evidence=busy.get("source_file"), source_file=busy.get("source_file"),
            # These fields must come from a service-attested atomic checkout
            # hold ledger, never an untrusted appointment shell or URL.
            checkout_hold_status=busy.get("checkout_hold_status"),
            hold_admission_attested=busy.get("hold_admission_attested"),
            checkout_hold_capacity_claimed=busy.get("checkout_hold_capacity_claimed"),
            checkout_hold_resource_verified=busy.get("checkout_hold_resource_verified"),
            checkout_hold_id=busy.get("checkout_hold_id"),
            checkout_order_id=busy.get("checkout_order_id"),
            hold_admitted_at=busy.get("hold_admitted_at"),
            hold_expires_at=busy.get("hold_expires_at"),
            instructor_unassigned=bool(busy.get("instructor_unassigned")),
            resource_uncertain=busy.get("resource_uncertain", False),
            uncertainty_reason=busy.get("uncertainty_reason"),
            adr_shift="adr" in str(busy.get("course_title") or "").casefold()))
        route_origins.append((fixture["sources"][-1], busy))
        if busy.get("instructor_unassigned"):
            for name in fixture["capabilities"]:
                fixture["sources"].append(dict(fixture["sources"][-1],
                    id="unassigned-"+str(index)+"-"+name, instructor=name, kind="hold"))
    # Match the engine's attested expiry decision before route validation.
    # Retain the expired source for the engine's ignored-source diagnostics.
    locations = {s["location"] for s in fixture["sources"]
                 if not (attested_checkout_hold(s, fixture["now"], fixture["courses"])
                         and stamp(s["hold_expires_at"]) <= stamp(fixture["now"]))} | {primary}
    # Diagnostic only: classify every origin of a missing primary-room route
    # before the existing fail-closed validation. No source identities or
    # location values are included in these fixed categories.
    missing_locations = {loc for loc in locations if loc != primary
        and not loc.startswith("instructor-only:") and loc not in known
        and any((travel_minutes or {}).get(direction) is None
                for direction in (loc+"->"+primary, primary+"->"+loc))}
    route_categories = set()
    if missing_locations:
        for source, original in route_origins:
            if source["location"] not in missing_locations:
                continue
            if (attested_checkout_hold(source, fixture["now"], fixture["courses"])
                    and stamp(source["hold_expires_at"]) <= stamp(fixture["now"])):
                continue
            origin = str(original.get("source_file") or "")
            if origin == "canonical_class_sessions":
                category = ("canonical_positive" if has_seated_demand(original)
                            else "canonical_other")
            elif origin in {"data/sessions_current.json", "docs/data/schedule_future.json"}:
                category = "legacy_inventory"
            elif origin.startswith("live_availability_snapshot.blocked["):
                category = "calendar_physical_or_unknown"
            else:
                category = "other_source"
            route_categories.add(category)
            route_categories.add("scope_unassigned" if original.get("instructor_unassigned")
                                 else "scope_selected_instructor" if source["instructor"] in fixture["capabilities"]
                                 else "scope_shared_resource")
            overlaps = any(aware(source["start"]) < aware(window["end"])
                           and aware(window["start"]) < aware(source["end"])
                           for window in fixture["instructor_availability"])
            route_categories.add("interval_overlaps_window" if overlaps else "interval_outside_window")
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
            else:
                gap = (travel_minutes or {}).get(left+"->"+right)
                if gap is None:
                    error = ValueError("missing directional travel rule: "+left+"->"+right)
                    error.route_source_categories = sorted(route_categories)
                    raise error
            fixture["policy"]["travel_minutes"][left+"->"+right] = gap
    report = run(fixture)
    report["adapter_mode"] = "shadow"
    report["room_hours_policy"] = policy["owner_room_hours_evidence"]
    report["manual_overlap_resources"] = sorted(manual)
    return report
