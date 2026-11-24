"""Explicitly activated V2 publication bridge; no external writes or new scheduler.

Coverage is evidence, not inferred from room hours or an inverse availability row.
Malformed occupancy closes only intersecting declared resource/instructor windows;
missing bounds close the affected resource horizon. Existing records are immutable.
"""
from copy import deepcopy
from collections import Counter
from datetime import timedelta, timezone
from urllib.parse import urlsplit
from scripts.layered_selector_adapter import aware, build_shadow
from scripts.layered_scheduling_engine import encode as encode_value, attested_checkout_hold, stamp
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
            if row.get("start") and (not row.get("end") or aware(row["end"]) <= aware(row["start"])):
                meta = course_metadata.get(cid, {})
                minutes = row.get("duration_minutes") or meta.get("scheduler_consumption_minutes") or meta.get("duration_minutes")
                if isinstance(minutes, (int, float)) and minutes > 0:
                    row["end"] = (aware(row["start"]) + timedelta(minutes=minutes)).isoformat()
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


def calculate(windows, occupancy, courses, policy, resources, now, interval,
              qualified, coverage, travel_minutes=None):
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
    metadata = {str(c["course_id"]): c for c in courses}
    projected = project_sources(occupancy, metadata)
    projected.sort(key=lambda row: row.get("source_file") != "canonical_class_sessions")
    known_rooms = {r["resource_name"] for location in resources.get("locations", [])
                   for r in location.get("internal_resources", [])}
    reports, issues = [], []
    for index, window in enumerate(windows):
        try:
            ws, we = map(aware, interval(window))
            if we <= ws:
                raise ValueError("invalid_resource_window")
        except (ValueError, TypeError, KeyError) as error:
            issues.append(dict(reason=str(error), instructor=window.get("instructor_name"),
                resource=policy["primary_resource"], window_id=window.get("source_availability_window")))
            continue
        name = str(window.get("instructor_name") or "").casefold().strip()
        room = policy["primary_resource"]
        relevant, invalid = [], []
        for source in projected:
            person = str(source.get("instructor") or "").casefold().strip()
            same_person = person == name or person in {"brian", "brian ennis"} and "brian" in name
            resource = source.get("resource") or room
            # Match build_shadow's conservative venue-only primary-room fallback
            # before filtering other instructors' occupied intervals.
            if resource not in known_rooms or resource == "Shipyard Office":
                resource = room
            same_room = resource == room and source.get("location_resolution") == "location_resource_map"
            if source.get("availability_location_mode") == "instructor_time_only":
                same_room = False
            if not same_person and not same_room and not source.get("instructor_unassigned"):
                continue
            try:
                start, end = aware(source["start"]), aware(source["end"])
                if end <= start:
                    raise ValueError("unresolved duration")
                # Keep enough boundary context for the +/-24h full-course
                # repeat gap and travel/cleanup. Distant commitments still
                # exist in projected_sources and in their own dated windows,
                # but must not demand a route for this unrelated window.
                # Unknown routes near either boundary still fail closed.
                travel_values = [v for v in (travel_minutes or {}).values()
                                 if type(v) in (int, float) and v >= 0]
                travel_envelope = max(travel_values, default=0)
                horizon = timedelta(minutes=max(48 * 60, 24 * 60 + travel_envelope))
                if end < ws - horizon or start > we + horizon:
                    continue
                relevant.append(source)
            except (KeyError, TypeError, ValueError):
                scope = source.get("uncertainty_scope", {})
                bounded = scope.get("start") and scope.get("end")
                if bounded:
                    try:
                        bounded = aware(scope["end"]) > aware(scope["start"])
                    except (ValueError, TypeError):
                        bounded = False
                if bounded and (aware(scope["end"]) <= ws or aware(scope["start"]) >= we):
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
                from scripts.layered_scheduling_engine import stamp
                if proof.get("status") != "known_complete":
                    continue
                for field in ("start", "end", "observed_at", "valid_until"):
                    stamp(proof[field])  # Proof bounds must explicitly carry timezone.
                observed = aware(proof["observed_at"]).astimezone(timezone.utc)
                freshness = timedelta(minutes=proof.get("freshness_minutes", 60))
                lease = min(aware(proof["valid_until"]).astimezone(timezone.utc), observed+freshness)
                if observed > now or freshness.total_seconds() <= 0 or lease <= now:
                    continue
                fresh.append(dict(proof,valid_until=lease.isoformat()))
            except (KeyError, ValueError, TypeError):
                continue  # Invalid evidence cannot open a window.
        if invalid:
            issues.extend(invalid)
            continue
        try:
            report = build_shadow([window], relevant, courses, policy, resources, now,
                interval, qualified, lead_minutes=policy.get("lead_minutes", 1440),
                travel_minutes=travel_minutes, commitment_coverage=fresh,
                shared_room_edges=True)
            report["adapter_mode"] = "active_local_v2"
            report["availability_window"] = window.get("source_availability_window", str(index))
            # Coverage lease must survive both publication and browser rendering.
            matched = [p for p in fresh if p.get("instructor") == window["instructor_name"]
                and p.get("location") == room and aware(p["start"]) <= ws and we <= aware(p["end"])]
            report["valid_until"] = min((aware(p["valid_until"]).astimezone(timezone.utc) for p in matched), default=now)
            # A publication generated under a provisional checkout lease must
            # not outlive that lease, even when calendar proof lasts longer.
            for source in relevant:
                if attested_checkout_hold(source, now, metadata):
                    expiry = stamp(source['hold_expires_at'])
                    if expiry > now:
                        report['valid_until'] = min(report['valid_until'], expiry)
            reports.append(report)
        except ValueError as error:
            issues.append(dict(reason=str(error), instructor=window.get("instructor_name"),
                resource=room, start=ws.isoformat(), end=we.isoformat()))
    return dict(schema=SCHEMA, reports=reports, issues=issues, projected_sources=projected,
        counts=dict(input_sources=len(occupancy), normalized_sources=len(projected),
                    input_windows=len(windows), evaluated_windows=len(reports),
                    failed_windows=len(windows)-len(reports), uncertainty_issues=len(issues)))


def publish(calculation, page_config, courses, windows, now, url_for, public_reasons,
            seated_offers=()):
    """Translate accepted calculations to the existing URL/feed/renderer contract."""
    from scripts.apply_anchor_policy import _rebuild_dates
    now = aware(now).astimezone(timezone.utc)
    catalog = {str(c["course_id"]): c for c in courses}
    origins = {str(w.get("source_availability_window", i)): w for i, w in enumerate(windows)}
    accepted, rejected = [], []
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
            day_id, container_id, url, blocker = url_for(window, start, candidate["course"])
            reasons = list(public_reasons(start, course))
            allowed_families = set(window.get("allowed_course_families", []))
            if allowed_families and (course.get("course_family") or course.get("family")) not in allowed_families:
                reasons.append("course_family_not_allowed_by_availability")
            if window.get("public_location_allowed") is False:
                reasons.append("location_not_allowed_by_public_policy")
            if blocker: reasons.append(blocker)
            if not url: reasons.append("missing_owned_appointment_url")
            if report["valid_until"] <= now: reasons.append("expired_coverage_proof")
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
                resource=candidate["location"], appointmentDayId=day_id, matchedContainerId=container_id,
                appointmentUrl=url, registrationUrl=url, availabilityBlockId=report["availability_window"],
                availabilityWindow=report["availability_window"], sourceAvailabilityBlock=window.get("source_live_availability_block", {}),
                offerType="dynamic_appointment", scheduleRole="barnacle" if candidate["mode"]=="barnacle" else "open_day",
                sourceSessionIds=candidate["source_ids"], edgeIds=candidate["edge_ids"],
                validUntil=report["valid_until"].isoformat(), publicSelectable=True))
    # Never retire a source record. Confirmed-zero booking choices are retired
    # only from this projection; their occupied interval remains in calculation.
    counts = {}
    denied_booking_identities = set()
    for source in calculation["projected_sources"]:
        for identity in [source.get("source_event_id"), source.get("external_class_id")]:
            if identity is None:
                continue
            identity = str(identity)
            # A canonical row can be followed by a second legacy mirror with
            # the same external class ID but an explicitly revoked route.
            # First-source wins for counts, but any known denial wins for
            # public joinability. Geometry and positive seats remain intact.
            if identity not in counts:
                counts[identity] = source
            if (str(source.get("visibility") or "").strip().lower() in {"private", "unlisted", "internal"}
                    or source.get("public_direct_booking") is False
                    # An operationally occupied seat may be deliberately closed
                    # to new registrations; a stale public CTA must not revive it.
                    or str(source.get("registration_status") or "").strip().lower() in {"closed", "full", "unverified", "cancelled", "canceled", "deleted"}
                    or str(source.get("session_status") or "").strip().lower() in {"cancelled", "canceled", "deleted"}
                    or source.get("is_full") is True):
                denied_booking_identities.add(identity)
    def matches_authoritative_start(source, offer):
        # An ID match alone is not enough: a rescheduled class can retain its
        # legacy ID while a cached public card still advertises the old date.
        # Compare the actual selected source start in Eastern local time; never
        # reinterpret an unknown start as a joinable public occurrence.
        try:
            actual = aware(source["start"])
            return (offer.get("date") == actual.date().isoformat()
                    and offer.get("startTime") == actual.strftime("%H:%M"))
        except (KeyError, TypeError, ValueError):
            return False

    def matches_authoritative_course(source, offer):
        # A class identifier and start time do not authorize a different
        # course. A source lacking a scheduler course identity is operational
        # occupancy, not proof of the customer's requested registration type.
        expected = str(source.get("course_id") or "").strip()
        requested = str(offer.get("courseId") or "").strip()
        return bool(expected and requested and expected == requested)

    def matches_authoritative_registration_route(source, offer):
        # Matching the class ID, course and occurrence does not authenticate a
        # customer registration URL. Only the selected authoritative source
        # may attest to the exact destination. Never substitute a legacy mirror
        # for missing canonical route proof.
        advertised = str(offer.get("registrationUrl") or offer.get("appointmentUrl") or "").strip()
        if not advertised:
            # Informational fixture rows without a CTA can still carry demand
            # gravity; a customer-selectable card cannot omit route proof.
            return offer.get("publicSelectable") is not True
        recorded = str(source.get("registration_url") or "").strip()
        if not recorded or advertised != recorded:
            return False
        if offer.get("appointmentUrl") and offer["appointmentUrl"] != advertised:
            return False
        try:
            parsed = urlsplit(advertised)
            return (parsed.scheme == "https" and bool(parsed.hostname)
                    and not parsed.username and not parsed.password
                    and not parsed.fragment)
        except ValueError:
            return False

    for original in seated_offers:
        identity = str(original.get("session_id") or original.get("sourceSessionId") or original.get("sourceAvailabilityBlock", {}).get("sessionId"))
        source = counts.get(identity)
        # Defense in depth: never resurrect private or source-revoked seated
        # routes even if an upstream selector mistakenly hands us such an offer.
        # A seated route not backed by any selected authoritative occupancy
        # source is an orphan, not verified bookable inventory. A stale legacy
        # card must never bypass the canonical private/closed source filter.
        if source is None:
            rejected.append(dict(original, reasons=["existing_booking_source_unverified"]))
        elif identity in denied_booking_identities:
            rejected.append(dict(original, reasons=["nonpublic_or_unverified_existing_booking_choice"]))
        elif source and source.get("count_available") is True and source.get("active_registration_count") == 0:
            rejected.append(dict(original, reasons=["confirmed_zero_existing_booking_choice_retired"]))
        elif not matches_authoritative_start(source, original):
            rejected.append(dict(original, reasons=["existing_booking_occurrence_mismatch"]))
        elif not matches_authoritative_course(source, original):
            rejected.append(dict(original, reasons=["existing_booking_course_mismatch"]))
        elif not matches_authoritative_registration_route(source, original):
            rejected.append(dict(original, reasons=["existing_booking_route_unverified"]))
        else:
            accepted.append(deepcopy(original))
    # A published existing-class row is not evidence of registered demand.
    # The source retains its hard occupied interval in calculate()/build_shadow
    # even when no trustworthy headcount is available; this gate controls only
    # whole-day collapse, not instructor/resource occupancy or joinability.
    def has_verified_demand(source):
        if not source:
            return False
        if source.get("operational_has_active_seat") is True:
            return True
        count = source.get("active_registration_count")
        return (source.get("count_available") is True
                and type(count) is int and count > 0)

    def has_provisional_checkout_gravity(source):
        # A real admitted checkout lease shapes offers for its own instructor;
        # it is not paid demand and never makes a private session joinable.
        return (source is not None
                and attested_checkout_hold(source, now, catalog)
                and stamp(source["hold_expires_at"]) > now)

    def matched_source(offer):
        identity = (offer.get("session_id") or offer.get("sourceSessionId")
                    or offer.get("sourceAvailabilityBlock", {}).get("sessionId"))
        return counts.get(str(identity))

    def instructor_key(name):
        key = str(name or '').strip().casefold()
        return 'brian ennis' if key == 'brian' else key

    # A demand Anchor collapses this class for its instructor, not every
    # independently qualified instructor on the same date. Physical room and
    # instructor conflicts are enforced upstream by the scheduling engine.
    day_anchors = {
        (offer['date'], str(offer['courseId']), instructor_key(offer.get('instructor')))
        for offer in accepted
        if offer.get('offerType') == 'seated_class'
        and has_verified_demand(matched_source(offer))
    }

    # Only verified operational demand provides day gravity, including a
    # canonical private/unlisted seat without an external numeric course ID.
    # The actual class remains private and cannot be joined from this flag.
    anchored_days = set()
    for source in calculation['projected_sources']:
        if not (has_verified_demand(source)
                or has_provisional_checkout_gravity(source)):
            continue
        # A confirmed but unassigned private appointment is a real occupied
        # interval, not evidence that *every* qualified instructor is anchored
        # for the rest of the day. The engine still blocks its time for all
        # potentially assigned instructors and any shared physical resource.
        instructor = instructor_key(source.get('instructor'))
        if (instructor and not source.get('instructor_unassigned')
                and source.get('start') and source.get('end')
                and not source.get('normalization_issue')
                and aware(source['end']) > aware(source['start'])):
            anchored_days.add((aware(source['start']).date().isoformat(),
                               instructor))
    for offer in accepted:
        instructor = instructor_key(offer.get('instructor'))
        if (offer.get('offerType') == 'seated_class' and instructor
                and has_verified_demand(matched_source(offer))):
            anchored_days.add((offer['date'], instructor))
    retained = []
    for offer in accepted:
        course = catalog.get(str(offer['courseId']), {})
        skills_edge = offer.get('scheduleRole') == 'barnacle' and (
            course.get('kind') == 'skills' or course.get('blended_classroom_skills') == 'blended')
        # A retained skills seat occupies its actual interval; it does not consume
        # the whole day's eligible skills edges. Calculation already checks each
        # candidate's 45-minute instruction plus 15-minute cleanup and conflicts.
        if (offer.get('offerType') != 'seated_class'
                and (offer['date'], str(offer['courseId']), instructor_key(offer.get('instructor'))) in day_anchors
                and not skills_edge):
            rejected.append(dict(offer, reasons=['existing_course_day_anchor']))
        elif offer.get('scheduleRole') == 'open_day' and (
                (offer['date'], instructor_key(offer.get('instructor'))) in anchored_days):
            rejected.append(dict(offer, reasons=['anchored_day_requires_attached_offer']))
        else:
            retained.append(offer)
    accepted = retained
    seen = set(); unique=[]
    for offer in accepted:
        key = (offer["date"],offer["startTime"],offer["courseId"],offer.get("instructor"),offer.get("offerType"))
        if key not in seen: unique.append(offer);seen.add(key)
    payload=dict(generatedAt=now.isoformat(), pageKey=page_config["page_key"], pageConfig=page_config,
        publicPage=page_config.get("output_path", ""), pilot="block_start_time_selector", readOnlyDataBuild=True,
        schedulingModel=SCHEMA, offers=unique, dates=[], counts={}, inputFiles={},
        whole_block_presented_as_class=False, availability_source_used="explicit_layered_coverage",
        availability_fallback_used=False, horizonDays=0, minimumLeadHours=0,
        rejectedCourseStartTimes=rejected, rejectionReasonCounts=dict(Counter(reason for row in rejected for reason in row.get("reasons",[]))),
        reconciliationIssues=calculation["issues"], layeredDiagnostics=encode(calculation),
        proof=dict(whole_block_presented_as_class=False, availability_windows_are_not_rendered_as_class_times=True))
    _rebuild_dates(payload,unique)
    payload["counts"].update(calculation["counts"])
    return finalize(payload, now)


# Customer-facing rejection reports must not retain raw source offers.
# Rejected seated links and expired appointment DTOs can contain private
# registration URLs, rosters, internal source references and customer metadata.
PUBLIC_REJECTION_DIAGNOSTIC_FIELDS = frozenset({
    "date", "startTime", "courseId", "courseFamily", "courseName",
    "offerType", "scheduleRole", "reasons",
})


def public_rejection_diagnostics(rows):
    result = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("offerType") == "seated_class":
            # The rejected choice may be a private or unlisted appointment.
            # Its exact time/course can identify a confidential commitment;
            # detailed diagnostics stay in the internal calculation only.
            result.append(dict(offerType="seated_class",
                               reasons=["existing_booking_choice_withheld"]))
            continue
        result.append({key: value for key, value in row.items()
                       if key in PUBLIC_REJECTION_DIAGNOSTIC_FIELDS})
    return result


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
