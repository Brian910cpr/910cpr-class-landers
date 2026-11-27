"""Explicitly activated V2 publication bridge; no external writes or new scheduler.

Coverage is evidence, not inferred from room hours or an inverse availability row.
Malformed occupancy closes only intersecting declared resource/instructor windows;
missing bounds close the affected resource horizon. Existing records are immutable.
"""
from copy import deepcopy
from collections import Counter
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo
from scripts.layered_selector_adapter import attested_seat, aware, build_shadow, occupied_location, occupancy_instant
from scripts.layered_instructor_identity import same_proved_instructor, strict_coverage_matches
from scripts.layered_scheduling_engine import encode as encode_value, stamp
import json


def encode(value):
    return json.loads(json.dumps(value, default=encode_value))

SCHEMA = "layered-publication.v2"


def active(policy):
    return policy.get("mode") == "active_local_v2"


def project_sources(rows, course_metadata):
    """Read-only durable projection. Unknown counts stay unknown; zero is explicit.

    Fixtures use the same normalized DTO as durable-demand ingestion. This helper
    does not reconcile source identities, infer headcounts, or write registrations.
    """
    result = []
    for original in rows:
        row = deepcopy(original)
        row["course_id"] = str(row.get("course_id") or row.get("courseId") or "")
        cid = row["course_id"]
        try:
            if row.get("start") and (not row.get("end") or occupancy_instant(row["end"]) <= occupancy_instant(row["start"])):
                meta = course_metadata.get(cid, {})
                minutes = row.get("duration_minutes") or meta.get("scheduler_consumption_minutes") or meta.get("duration_minutes")
                if isinstance(minutes, (int, float)) and minutes > 0:
                    row["end"] = (occupancy_instant(row["start"]) + timedelta(minutes=minutes)).isoformat()
                    row["duration_resolution"] = "source/course metadata"
        except (ValueError, TypeError):
            row["normalization_issue"] = "invalid_source_timestamp"
        count = row.get("active_registration_count")
        if row.get("count_available") is not True or not isinstance(count, int) or isinstance(count, bool) or count < 0:
            row["count_available"] = False
            row["active_registration_count"] = None
        row.setdefault("source_file", "canonical_class_sessions")
        result.append(row)
    return result


def apply_default_owner_occupancy(rows, owner, primary, now, coverage, owner_qualified,
                                  *, owner_person_id=None, strict_identity=False):
    """Project effective ownership only for a proved, genuinely unassigned class.

    This is an in-memory copy, never a roster, a stored assignment, or an
    entitlement to public registration. Any unresolved conflict keeps the
    original physical block and its existing unassigned behavior.
    """
    owner = str(owner or "").strip()
    if not owner or (strict_identity and not owner_person_id):
        return rows

    def key(value):
        name = " ".join(str(value or "").casefold().split())
        return "brian ennis" if name == "brian" else name

    def bounds(row, *, allow_local=True):
        try:
            start, end = (occupancy_instant(row[field], allow_local=allow_local)
                          for field in ("start", "end"))
            if start < end:
                return start, end
        except (KeyError, ValueError, TypeError, AttributeError):
            pass
        return None

    def room_relation(row):
        if row.get("availability_location_mode") == "instructor_time_only":
            return False
        if row.get("location_resolution") == "location_resource_map":
            resource = row.get("resource")
            return resource in {None, "", primary, "Shipyard Office"}
        return None  # Not proof of a separate room.

    owner_key = key(owner)
    instant = stamp(aware(now).isoformat())
    fresh_intervals = []
    for proof in coverage or []:
        if (proof.get("status") != "known_complete" or proof.get("location") != primary
                or not (strict_coverage_matches(proof, {"person_id": owner_person_id})
                        if strict_identity else key(proof.get("instructor")) == owner_key)):
            continue
        span = bounds(proof, allow_local=False)
        try:
            observed = stamp(proof["observed_at"])
            expiry = min(stamp(proof["valid_until"]), observed + timedelta(
                minutes=proof.get("freshness_minutes", 60)))
        except (KeyError, ValueError, TypeError, AttributeError, OverflowError):
            continue
        if span and observed <= instant < expiry:
            fresh_intervals.append(span)

    result = list(rows)
    for index, row in enumerate(rows):
        if (row.get("source_file") != "canonical_class_sessions"
                or row.get("booking_source") != "confirmed_booking_intake"
                or row.get("registration_backend") != "landerware"
                or row.get("session_status") not in {"scheduled", "active"}
                or row.get("visibility") not in {"private", "unlisted", "internal"}
                or row.get("stored_instructor_absent") is not True
                or (strict_identity and row.get("stored_instructor_identity_state") != "unassigned")
                or not row.get("instructor_unassigned")
                or row.get("operational_has_active_seat") is not True
                or room_relation(row) is not True
                or not owner_qualified(str(row.get("course_id") or ""))):
            continue
        span = bounds(row)
        if not span or not any(start <= span[0] < span[1] <= end
                              for start, end in fresh_intervals):
            continue

        conflict = False
        for other_index, other in enumerate(rows):
            if other_index == index:
                continue
            other_person = (other.get("effective_instructor_person_id") if strict_identity
                            else key(other.get("instructor")))
            owner_identity = owner_person_id if strict_identity else owner_key
            other_room = room_relation(other)
            if (strict_identity and other_room is False
                    and other.get("uncertain_calendar_owner_id")
                    and other["uncertain_calendar_owner_id"] != owner_person_id):
                continue
            if (other_room is False and other_person
                    and other_person not in {owner_identity, "unknown", "unassigned"}
                    and not other.get("instructor_unassigned")):
                continue
            other_span = bounds(other)
            if other_span and (other_span[1] <= span[0] or other_span[0] >= span[1]):
                continue
            # A legacy row that explicitly resolves to a different canonical
            # class cannot be ignored as this class's mirror, even if its legacy
            # key and occupied interval agree. Contradictory evidence stays busy.
            linked_canonical = other.get("linked_canonical_session_id")
            if (other_span == span and other_room is True and other_person == owner_identity
                    and other.get("source_file") in {"data/sessions_current.json", "docs/data/schedule_future.json"}
                    and (not linked_canonical or linked_canonical == row.get("source_event_id"))
                    and row.get("external_class_id")
                    and str(row["external_class_id"]) == str(other.get("external_class_id") or "")
                    and str(row.get("course_id") or "") == str(other.get("course_id") or "")):
                continue  # Exact durable mirror, not evidence of another class.
            conflict = True
            break
        if not conflict:
            result[index] = dict(row, instructor=owner, instructor_unassigned=False,
                                 effective_instructor_basis="owner_default_verified_coverage")
            if strict_identity:
                result[index]["effective_instructor_person_id"] = owner_person_id
    return result


def repeat_context_for_window(projected, metadata, window, start, end, *, strict_identity=False,
                              known_rooms=(), primary=None):
    """Confirmed full-course starts only; never use this context as physical occupancy."""
    def instructor_key(value):
        key = " ".join(str(value or "").casefold().split())
        return "brian ennis" if key == "brian" else key

    instructor = instructor_key(window.get("instructor_name"))
    lower = stamp(start.isoformat()) - timedelta(hours=24)
    upper = stamp(end.isoformat()) + timedelta(hours=24)
    claims = {}
    for row in projected:
        matches_person = (same_proved_instructor(row, window) if strict_identity else
                          bool(instructor and instructor_key(row.get("instructor")) == instructor))
        if (not matches_person or not attested_seat(row)
                or (not row.get("kind") and "blocked" in str(row.get("source_file")))
                or row.get("normalization_issue")):
            continue
        cid = row["course_id"]
        if not cid:
            continue
        try:
            occupied_start, occupied_end = stamp(row["start"]), stamp(row["end"])
        except (KeyError, ValueError, TypeError, AttributeError):
            continue
        if occupied_end > occupied_start and lower <= occupied_start <= upper:
            location = occupied_location(row, known_rooms, primary, instructor)
            claims.setdefault((occupied_start.isoformat(), occupied_end.isoformat(), location), set()).add(cid)
    matches = set()
    for (when, _, _), course_ids in claims.items():
        if len(course_ids) != 1:
            continue  # Same instructor/physical interval cannot pick an arbitrary course.
        cid = next(iter(course_ids))
        meta = metadata.get(cid)
        if meta and meta.get("kind") != "skills" and meta.get("blended_classroom_skills") != "blended":
            matches.add((cid, when))
    return [{"course": cid, "start": when} for cid, when in sorted(matches)]


def scoped_sources(rows, start, end, travel_minutes, known_rooms, primary):
    """Shared direct/cache context: physical day edges plus conservative offsite scope.

    Retain malformed bounds and transitively connected physical occupancy. A
    nearby unresolved offsite direction must not disappear merely because the
    cached day has no configured route duration. Distant offsite sources remain
    in the full projected source audit, not the unrelated window calculation.
    """
    travel = max([0] + [int(v) for v in (travel_minutes or {}).values()
                         if type(v) in (int, float) and v >= 0])
    zone = ZoneInfo("America/New_York")
    lower = (start.astimezone(zone).replace(hour=0, minute=0, second=0, microsecond=0)
             .astimezone(timezone.utc) - timedelta(minutes=travel))
    end_day = (end.astimezone(timezone.utc) - timedelta(microseconds=1)).astimezone(zone)
    upper = (end_day.replace(hour=0, minute=0, second=0, microsecond=0)
             + timedelta(days=1)).astimezone(timezone.utc) + timedelta(minutes=travel)
    horizon = timedelta(minutes=max(48 * 60, 24 * 60 + travel))
    route_lower = start.astimezone(timezone.utc) - horizon
    route_upper = end.astimezone(timezone.utc) + horizon
    chosen = {}
    changed = True
    while changed:
        changed = False
        for index, row in enumerate(rows):
            if index in chosen:
                continue
            try:
                a, b = (occupancy_instant(row[field]) for field in ("start", "end"))
                if b <= a:
                    raise ValueError("unresolved")
            except (KeyError, ValueError, TypeError, AttributeError):
                chosen[index] = row
                continue
            if a <= upper and b >= lower:
                chosen[index] = row
                new_lower, new_upper = min(lower, a-timedelta(minutes=travel)), max(upper, b+timedelta(minutes=travel))
                if (new_lower, new_upper) != (lower, upper):
                    lower, upper = new_lower, new_upper
                    changed = True
    # Do not extend the physical connected component using a merely nearby
    # offsite route-check source. Match the shadow adapter's venue resolution.
    for index, row in enumerate(rows):
        if index in chosen or row.get("availability_location_mode") == "instructor_time_only":
            continue
        room = row.get("resource")
        room = room if room in known_rooms and room != "Shipyard Office" else primary
        same_venue = row.get("location_resolution") == "location_resource_map" or room != primary
        if same_venue:
            continue
        try:
            a, b = (occupancy_instant(row[field]) for field in ("start", "end"))
        except (KeyError, ValueError, TypeError, AttributeError):
            chosen[index] = row
            continue
        if a <= route_upper and b >= route_lower:
            chosen[index] = row
    return [chosen[i] for i in sorted(chosen)]


def calculate(windows, occupancy, courses, policy, resources, now, interval,
              qualified, coverage, travel_minutes=None, *, scoped_repeat_context=None):
    """Partition normalization errors by window, retaining all relevant occupancy.

    A bad source cannot be removed to manufacture free space. Unknown offsite
    travel for the selected instructor closes that window; other instructors can
    remain eligible if they do not share the uncertain resource.
    """
    if not active(policy):
        raise ValueError("V2 requires explicit active_local_v2 configuration")
    # Leases measure elapsed time, not Eastern wall time. During the fall-back
    # hour, ZoneInfo comparisons ignore fold when both operands share a zone.
    now = aware(now).astimezone(timezone.utc)
    strict_identity = policy.get("verified_instructor_identity") is True
    metadata = {str(c["course_id"]): c for c in courses}
    projected = project_sources(occupancy, metadata)
    projected.sort(key=lambda row: row.get("source_file") != "canonical_class_sessions")
    known_rooms = {r["resource_name"] for location in resources.get("locations", [])
                   for r in location.get("internal_resources", [])}
    if scoped_repeat_context is not None and len(windows) != 1:
        raise ValueError("scoped repeat context requires exactly one window")
    reports, issues = [], []
    for index, window in enumerate(windows):
        try:
            ws, we = map(occupancy_instant, interval(window))
            if we <= ws:
                raise ValueError("invalid_resource_window")
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            issues.append(dict(reason=str(error), instructor=window.get("instructor_name"),
                resource=policy["primary_resource"], window_id=window.get("source_availability_window")))
            continue
        name = str(window.get("instructor_name") or "").casefold().strip()
        room = policy["primary_resource"]
        relevant, invalid = [], []
        for source in scoped_sources(projected, ws, we, travel_minutes, known_rooms, room):
            person = str(source.get("instructor") or "").casefold().strip()
            same_person = (same_proved_instructor(source, window) if strict_identity else
                           person == name or person in {"brian", "brian ennis"} and "brian" in name)
            resource = source.get("resource") or room
            # Match build_shadow's conservative venue-only primary-room fallback
            # before filtering other instructors' occupied intervals.
            if resource not in known_rooms or resource == "Shipyard Office":
                resource = room
            same_room = resource == room and source.get("location_resolution") == "location_resource_map"
            if source.get("availability_location_mode") == "instructor_time_only":
                same_room = False
            if (strict_identity and not same_room and source.get("uncertain_calendar_owner_id")
                    and source["uncertain_calendar_owner_id"] != window.get("person_id")):
                continue
            if not same_person and not same_room and not source.get("instructor_unassigned"):
                continue
            try:
                start, end = occupancy_instant(source["start"]), occupancy_instant(source["end"])
                if end <= start:
                    raise ValueError("unresolved duration")
                # Keep known intervals outside the window: travel and block edges
                # may affect the boundary even without literal overlap.
                relevant.append(source)
            except (KeyError, TypeError, ValueError):
                scope = source.get("uncertainty_scope", {})
                try:
                    scope_start, scope_end = (occupancy_instant(scope[key]) for key in ("start", "end"))
                    bounded = scope_start < scope_end
                except (KeyError, ValueError, TypeError, AttributeError):
                    bounded = False
                if bounded and (scope_end <= ws or scope_start >= we):
                    continue
                if bounded:
                    uncertain = dict(source, start=scope["start"], end=scope["end"],
                        kind="uncertain", resource_uncertain=same_room,
                        uncertainty_reason="unresolved_occupied_bounds")
                    relevant.append(uncertain)
                    issues.append(dict(source_id=source.get("source_event_id"),
                        reason="unresolved_occupied_bounds", start=scope["start"], end=scope["end"],
                        instructor=source.get("instructor"), resource=resource))
                    continue
                invalid.append(dict(source_id=source.get("source_event_id"),
                    reason="unresolved_occupied_bounds", resource=resource,
                    instructor=window.get("instructor_name"), start=ws.isoformat(), end=we.isoformat()))
        fresh = []
        for proof in coverage or []:
            try:
                if (proof.get("status") != "known_complete"
                        or (strict_identity and not strict_coverage_matches(proof, window))):
                    continue
                for field in ("start", "end", "observed_at", "valid_until"):
                    stamp(proof[field])  # Proof bounds must explicitly carry timezone.
                observed = aware(proof["observed_at"]).astimezone(timezone.utc)
                freshness = timedelta(minutes=proof.get("freshness_minutes", 60))
                lease = min(aware(proof["valid_until"]).astimezone(timezone.utc), observed+freshness)
                if observed > now or freshness.total_seconds() <= 0 or lease <= now:
                    continue
                normalized_proof = dict(proof, valid_until=lease.isoformat())
                if strict_identity:
                    normalized_proof["instructor"] = window["instructor_name"]
                    normalized_proof.pop("instructor_person_id", None)
                fresh.append(normalized_proof)
            except (KeyError, ValueError, TypeError):
                continue  # Invalid evidence cannot open a window.
        if invalid:
            issues.extend(invalid)
            continue
        try:
            repeats = []
            if policy.get("require_verified_day_gravity") is True:
                repeats = (scoped_repeat_context if scoped_repeat_context is not None else
                           repeat_context_for_window(projected, metadata, window, ws, we, strict_identity=strict_identity,
                                                     known_rooms=known_rooms, primary=room))
            report = build_shadow([window], relevant, courses, policy, resources, now,
                interval, qualified, lead_minutes=policy.get("lead_minutes", 1440),
                travel_minutes=travel_minutes, commitment_coverage=fresh,
                shared_room_edges=True, repeat_context=repeats)
            report["adapter_mode"] = "active_local_v2"
            report["availability_window"] = window.get("source_availability_window", str(index))
            # Coverage lease must survive both publication and browser rendering.
            matched = [p for p in fresh if p.get("instructor") == window["instructor_name"]
                and p.get("location") == room and stamp(p["start"]) <= ws and we <= stamp(p["end"])]
            report["valid_until"] = min((aware(p["valid_until"]).astimezone(timezone.utc) for p in matched), default=now)
            reports.append(report)
        except ValueError as error:
            issues.append(dict(reason=str(error), instructor=window.get("instructor_name"),
                resource=room, start=ws.isoformat(), end=we.isoformat()))
    return dict(schema=SCHEMA, reports=reports, issues=issues, projected_sources=projected,
        counts=dict(input_sources=len(occupancy), normalized_sources=len(projected),
                    input_windows=len(windows), evaluated_windows=len(reports),
                    failed_windows=len(windows)-len(reports), uncertainty_issues=len(issues)))


def publish(calculation, page_config, courses, windows, now, url_for, public_reasons,
            seated_offers=(), *, require_verified_day_gravity=False, strict_instructor_identity=False,
            request_course_ids=(), request_qualification=None):
    """Translate accepted calculations to the existing URL/feed/renderer contract."""
    from scripts.apply_anchor_policy import _rebuild_dates
    now = aware(now).astimezone(timezone.utc)
    catalog = {str(c["course_id"]): c for c in courses}
    origins = {str(w.get("source_availability_window", i)): w for i, w in enumerate(windows)}
    request_courses = set(request_course_ids) if isinstance(request_course_ids, (tuple, list)) and all(
        isinstance(cid, str) and cid.isdecimal() for cid in request_course_ids) else set()
    accepted, rejected = [], []
    offer_people = {}  # never serialized
    def diagnostic(candidate):
        row = encode(candidate)
        start = aware(candidate["start"])
        course = catalog.get(candidate["course"], {})
        row.update(date=start.date().isoformat(), startTime=start.strftime("%H:%M"),
            courseId=candidate["course"], courseFamily=course.get("course_family") or course.get("family"),
            courseName=course.get("clean_course_name") or course.get("short_title") or candidate["course"])
        return row
    for report in calculation["reports"]:
        rejected.extend(diagnostic(candidate) for candidate in report["rejected"])
        for candidate in report["accepted"]:
            course = catalog[candidate["course"]]
            start, end = aware(candidate["start"]), aware(candidate["end"])
            window = origins[report["availability_window"]]
            # Current public appointment URLs encode local date/HH:MM, not an offset.
            # Neither occurrence of a repeated wall time can be booked unambiguously.
            if start.replace(fold=0).utcoffset() != start.replace(fold=1).utcoffset():
                rejected.append(dict(diagnostic(candidate), reasons=["ambiguous_public_start_time"]))
                continue
            day_id, container_id, url, blocker = url_for(window, start, candidate["course"])
            reasons = list(public_reasons(start, course))
            allowed_families = set(window.get("allowed_course_families", []))
            if allowed_families and (course.get("course_family") or course.get("family")) not in allowed_families:
                reasons.append("course_family_not_allowed_by_availability")
            if window.get("public_location_allowed") is False:
                reasons.append("location_not_allowed_by_public_policy")
            if report["valid_until"] <= now:
                reasons.append("expired_coverage_proof")
            # Upgrade only explicit public classroom inquiries, never an ambiguous
            # checkout, policy failure, or skills reservation. Coverage and geometry
            # have already passed calculate(); booking proof remains independent.
            request_only = (
                not reasons and url is None
                and blocker in {"no_matching_appointment_container", "unverified_appointment_container_owner"}
                and strict_instructor_identity and bool(window.get("person_id"))
                and window.get("public_location_allowed") is True
                and str(window.get("visibility") or "").casefold().strip() == "public"
                and window.get("public_selectable") is True
                and candidate["course"] in request_courses
                and candidate["course"] != "509474"
                and course.get("kind") in (None, "full")
                and (course.get("blended_classroom_skills") or course.get("delivery_type")) == "classroom"
                and not course.get("schedule_page_option", {}).get("native_registration_path")
                and request_qualification is not None
                and request_qualification(window, course, end) is True
            )
            if not request_only:
                if blocker:
                    reasons.append(blocker)
                if not url:
                    reasons.append("missing_owned_appointment_url")
            if reasons:
                rejected.append(dict(diagnostic(candidate), reasons=reasons))
                continue
            instruction = int((candidate["instruction_end"]-candidate["start"]).total_seconds()/60)
            accepted.append(dict(courseId=candidate["course"], courseName=course.get("schedule_page_option", {}).get("display_label") or course.get("clean_course_name") or course.get("short_title") or candidate["course"],
                courseFamily=course.get("course_family") or course.get("family"),
                deliveryMode=course.get("blended_classroom_skills") or course.get("delivery_type") or "classroom",
                date=start.date().isoformat(), startTime=start.strftime("%H:%M"),
                displayDate=start.strftime("%A, %B %d, %Y"), displayStartTime=start.strftime("%I:%M %p").lstrip("0"),
                durationMinutes=instruction, schedulerConsumptionMinutes=candidate["duration_minutes"],
                schedulerConsumptionEnd=end.strftime("%H:%M"), occupiedUntil=end.isoformat(),
                setupBufferMinutes=0, cleanupBufferMinutes=candidate["duration_minutes"]-instruction,
                instructor=candidate["instructor"], location=window.get("location_name"),
                resource=candidate["location"], appointmentDayId=None if request_only else day_id,
                matchedContainerId=None if request_only else container_id,
                appointmentUrl=url, registrationUrl=url,
                availabilityBlockId=None if request_only else report["availability_window"],
                availabilityWindow=None if request_only else report["availability_window"],
                sourceAvailabilityBlock={} if request_only else window.get("source_live_availability_block", {}),
                **({"dynamicBookingMode": "request"} if request_only else {}),
                offerType="dynamic_appointment", scheduleRole="barnacle" if candidate["mode"]=="barnacle" else "open_day",
                sourceSessionIds=[] if request_only else candidate["source_ids"],
                edgeIds=[] if request_only else candidate["edge_ids"],
                validUntil=report["valid_until"].isoformat(), publicSelectable=True))
            if strict_instructor_identity:
                offer_people[id(accepted[-1])] = window.get("person_id")
    # Never retire a source record. Confirmed-zero booking choices are retired
    # only from this projection; their occupied interval remains in calculation.
    counts = {}
    nonpublic_identities = set()
    def has_verified_demand(source):
        if not source or not source.get("instructor") or source.get("instructor_unassigned"):
            return False
        if source.get("kind") in {"hold", "commitment", "uncertain"}:
            return False
        count = source.get("active_registration_count")
        return (source.get("operational_has_active_seat") is True
                or (source.get("count_available") is True and type(count) is int and count > 0))
    for source in calculation["projected_sources"]:
        # Multiple canonical/legacy representations can share an external
        # container ID. First-match lookup is useful for seat evidence, but
        # must never let a public-looking mirror hide a later private source.
        identities = [source.get("source_event_id"), source.get("external_class_id")]
        restricted = str(source.get("visibility") or "").strip().casefold() in {
            "private", "unlisted", "internal"}
        for identity in identities:
            if identity is not None:
                key = str(identity)
                if key not in counts or (require_verified_day_gravity
                        and has_verified_demand(source) and not has_verified_demand(counts[key])):
                    counts[key] = source
                if restricted:
                    nonpublic_identities.add(key)
    def instructor_key(name):
        key = str(name or '').strip().casefold()
        return 'brian ennis' if key == 'brian' else key

    def seated_identities(offer):
        block = offer.get("sourceAvailabilityBlock")
        return (offer.get("session_id"), offer.get("sourceSessionId"),
                block.get("sessionId") if isinstance(block, dict) else None)

    for original in seated_offers:
        original = dict(original)
        verified_seated_person = original.pop("_verified_instructor_person_id", None)
        identities = seated_identities(original)
        identity = next((value for value in identities if value), None)
        source = counts.get(str(identity))
        # An explicitly nonpublic canonical session can occupy an instructor
        # without ever becoming a joinable public legacy booking choice.
        # The most restrictive visibility wins across every identity match,
        # not merely the first source DTO selected for seat lookup.
        visibility = {str(v).strip().casefold() for v in (
            original.get("visibility"), (source or {}).get("visibility"))}
        if (visibility.intersection({"private", "unlisted", "internal"})
                or any(str(value) in nonpublic_identities for value in identities if value is not None)):
            rejected.append(dict(original, reasons=["nonpublic_occupied_not_joinable"]))
        elif source and source.get("count_available") is True and source.get("active_registration_count") == 0:
            rejected.append(dict(original, reasons=["confirmed_zero_existing_booking_choice_retired"]))
        elif strict_instructor_identity and not (source and source.get("stored_instructor_person_id")
                and verified_seated_person == source["stored_instructor_person_id"]):
            rejected.append(dict(original, reasons=["seated_instructor_identity_unverified"]))
        elif (not strict_instructor_identity and require_verified_day_gravity and has_verified_demand(source)
                and instructor_key(original.get('instructor')) != instructor_key(source.get('instructor'))):
            rejected.append(dict(original, reasons=["seated_instructor_mismatch"]))
        else:
            accepted.append(deepcopy(original))
            if strict_instructor_identity:
                offer_people[id(accepted[-1])] = verified_seated_person
    def matched_source(offer):
        identity = next((value for value in seated_identities(offer) if value), None)
        return counts.get(str(identity))
    def has_matching_verified_demand(offer):
        source = matched_source(offer)
        if strict_instructor_identity:
            return (has_verified_demand(source) and bool(offer_people.get(id(offer)))
                    and offer_people[id(offer)] == source.get("stored_instructor_person_id"))
        return (has_verified_demand(source) and bool(instructor_key(offer.get('instructor')))
                and instructor_key(offer.get('instructor')) == instructor_key(source.get('instructor')))
    def offer_instructor(offer):
        return (offer_people.get(id(offer)) if strict_instructor_identity
                else instructor_key(offer.get("instructor")))
    def anchor_key(offer):
        return (offer['date'], str(offer['courseId']),
                offer_instructor(offer) if require_verified_day_gravity else '')
    day_anchors = {anchor_key(o) for o in accepted
                   if o.get('offerType') == 'seated_class' and
                   (not require_verified_day_gravity or
                    has_matching_verified_demand(o))}
    # Assigned demand establishes day gravity, even when it is not joinable
    # or has no public course ID. Hard resource occupancy stays independent.
    anchored_days = set()
    for source in calculation['projected_sources']:
        if require_verified_day_gravity:
            if not has_verified_demand(source):
                continue
        elif not source.get('course_id'):
            continue
        if (source.get('start') and source.get('end') and
                not source.get('normalization_issue') and
                aware(source['end']).astimezone(timezone.utc) > aware(source['start']).astimezone(timezone.utc)):
            start, end = aware(source['start']), aware(source['end'])
            # Match active V2 engine business-day gravity regardless of source offset.
            zone = ZoneInfo('America/New_York') if require_verified_day_gravity else None
            day = (start.astimezone(zone) if zone else start).date()
            last = (end.astimezone(timezone.utc) -
                    timedelta(microseconds=1)).astimezone(zone or end.tzinfo).date()
            while day <= last:
                instructor = (source.get("effective_instructor_person_id") if strict_instructor_identity
                              else instructor_key(source.get('instructor')))
                if not strict_instructor_identity or instructor:
                    anchored_days.add((day.isoformat(), instructor))
                if not require_verified_day_gravity:
                    break
                day += timedelta(days=1)
    for offer in accepted:
        if offer.get('offerType') == 'seated_class' and (not require_verified_day_gravity or
                has_matching_verified_demand(offer)):
            anchored_days.add((offer['date'], offer_instructor(offer)))
    retained = []
    for offer in accepted:
        course = catalog.get(str(offer['courseId']), {})
        skills_edge = offer.get('scheduleRole') == 'barnacle' and (
            course.get('kind') == 'skills' or course.get('blended_classroom_skills') == 'blended')
        # A retained skills seat occupies its actual interval; it does not consume
        # the whole day's eligible skills edges. Calculation already checks each
        # candidate's 45-minute instruction plus 15-minute cleanup and conflicts.
        if offer.get('offerType') != 'seated_class' and anchor_key(offer) in day_anchors and not skills_edge:
            rejected.append(dict(offer, reasons=['existing_course_day_anchor']))
        elif offer.get('scheduleRole') == 'open_day' and (
                (offer['date'], offer_instructor(offer)) in anchored_days or
                (not require_verified_day_gravity and (offer['date'], '') in anchored_days)):
            rejected.append(dict(offer, reasons=['anchored_day_requires_attached_offer']))
        else:
            retained.append(offer)
    accepted = retained
    seen = set(); unique=[]
    def rendered_key(offer):
        return (offer["date"],offer["startTime"],offer["courseId"],offer.get("instructor"),offer.get("offerType"))
    rendered_people = {}
    if strict_instructor_identity:
        for offer in accepted:
            rendered_people.setdefault(rendered_key(offer), set()).add(offer_instructor(offer))
    for offer in accepted:
        key = rendered_key(offer)
        if strict_instructor_identity and len(rendered_people[key]) > 1:
            rejected.append(dict(offer, reasons=["ambiguous_rendered_instructor_identity"]))
            continue
        if key not in seen: unique.append(offer);seen.add(key)
    payload=dict(generatedAt=now.isoformat(), pageKey=page_config["page_key"], pageConfig=page_config,
        publicPage=page_config.get("output_path", ""), pilot="block_start_time_selector", readOnlyDataBuild=True,
        schedulingModel=SCHEMA, offers=unique, dates=[], counts={}, inputFiles={},
        whole_block_presented_as_class=False, availability_source_used="explicit_layered_coverage",
        availability_fallback_used=False, horizonDays=0, minimumLeadHours=0,
        rejectedCourseStartTimes=rejected, rejectionReasonCounts=dict(Counter(reason for row in rejected for reason in row.get("reasons",[]))),
        reconciliationIssues=calculation["issues"],
        layeredDiagnostics=encode(redact_internal_identity(calculation) if strict_instructor_identity else calculation),
        proof=dict(whole_block_presented_as_class=False, availability_windows_are_not_rendered_as_class_times=True))
    _rebuild_dates(payload,unique)
    payload["counts"].update(calculation["counts"])
    return finalize(payload, now)


def redact_internal_identity(value):
    if isinstance(value, dict):
        return {key: redact_internal_identity(item) for key, item in value.items()
                if key not in {"person_id", "stored_instructor_person_id",
                               "effective_instructor_person_id", "instructor_person_id", "uncertain_calendar_owner_id",
                               "catalog_external_id", "_verified_instructor_person_id"}}
    if isinstance(value, list):
        return [redact_internal_identity(item) for item in value]
    return value


# Customer-facing rejection reports must not retain raw source offers.
# Rejected seated links and expired appointment DTOs can contain private
# registration URLs, rosters, internal source references and customer metadata.
PUBLIC_REJECTION_DIAGNOSTIC_FIELDS = frozenset({
    "date", "startTime", "courseId", "courseFamily", "courseName",
    "offerType", "scheduleRole", "reasons",
})


def public_rejection_diagnostics(rows):
    safe = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if "nonpublic_occupied_not_joinable" in (row.get("reasons") or []):
            safe.append({"reasons": ["nonpublic_occupied_not_joinable"]})
        else:
            safe.append({key: value for key, value in row.items()
                         if key in PUBLIC_REJECTION_DIAGNOSTIC_FIELDS})
    return safe


def finalize(payload, now=None):
    """Shared V2 finalizer: enforce leases without reapplying V1 date suppression."""
    from scripts.apply_anchor_policy import _rebuild_dates
    from datetime import datetime, timezone
    now=aware(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    result=deepcopy(payload)
    original=result.get("offers", [])
    kept=[]
    for offer in original:
        if offer.get("offerType")=="seated_class":
            kept.append(offer)
        elif offer.get("validUntil") and aware(offer["validUntil"]) > now:
            kept.append(offer)
        else:
            result.setdefault("rejectedCourseStartTimes", []).append(dict(offer,reasons=["expired_or_missing_scoped_lease"]))
    result["validUntil"] = max((o["validUntil"] for o in kept if o.get("offerType")!="seated_class"),default=now.isoformat())
    result["anchor_policy"] = dict(mode=SCHEMA,finalized=True)
    from scripts.public_registration_closures import apply_closures
    result = apply_closures(_rebuild_dates(result,kept))[0]
    # Redact after the closure filter, which may add rejected seated rows.
    result["rejectedCourseStartTimes"] = public_rejection_diagnostics(
        result.get("rejectedCourseStartTimes", []))
    return result
