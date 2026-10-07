"""Explicitly activated V2 publication bridge; no external writes or new scheduler.

Coverage is evidence, not inferred from room hours or an inverse availability row.
Malformed occupancy closes only intersecting declared resource/instructor windows;
missing bounds close the affected resource horizon. Existing records are immutable.
"""
from copy import deepcopy
from collections import Counter
from datetime import timedelta
from scripts.layered_selector_adapter import aware, build_shadow
from scripts.layered_scheduling_engine import encode as encode_value
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
    now = aware(now)
    metadata = {str(c["course_id"]): c for c in courses}
    projected = project_sources(occupancy, metadata)
    projected.sort(key=lambda row: row.get("source_file") != "canonical_class_sessions")
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
            same_room = resource == room and source.get("location_resolution") == "location_resource_map"
            if source.get("availability_location_mode") == "instructor_time_only":
                same_room = False
            if not same_person and not same_room and not source.get("instructor_unassigned"):
                continue
            try:
                start, end = aware(source["start"]), aware(source["end"])
                if end <= start:
                    raise ValueError("unresolved duration")
                # Keep known intervals outside the window: travel and block edges
                # may affect the boundary even without literal overlap.
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
                observed = aware(proof["observed_at"])
                freshness = timedelta(minutes=proof.get("freshness_minutes", 60))
                lease = min(aware(proof["valid_until"]), observed+freshness)
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
            report["valid_until"] = min((aware(p["valid_until"]) for p in matched), default=now)
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
    now = aware(now)
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
    for source in calculation["projected_sources"]:
        for identity in [source.get("source_event_id"), source.get("external_class_id")]:
            if identity is not None and str(identity) not in counts:
                counts[str(identity)] = source
    for original in seated_offers:
        source = counts.get(str(original.get("session_id") or original.get("sourceSessionId") or original.get("sourceAvailabilityBlock", {}).get("sessionId")))
        if source and source.get("count_available") is True and source.get("active_registration_count") == 0:
            rejected.append(dict(original, reasons=["confirmed_zero_existing_booking_choice_retired"]))
        else:
            accepted.append(deepcopy(original))
    # Every retained existing class is that exact course's day anchor,
    # including when its roster count is unknown. Consolidate across separate
    # Google availability gaps without suppressing different course formats.
    day_anchors = {(o['date'], str(o['courseId'])) for o in accepted
                   if o.get('offerType') == 'seated_class'}
    def instructor_key(name):
        key = str(name or '').strip().casefold()
        return 'brian ennis' if key == 'brian' else key
    # Class occupancy comes from every program, not just the page's selected
    # courses. A second calendar gap does not reset an instructor's anchored day.
    anchored_days = set()
    for source in calculation['projected_sources']:
        if (source.get('course_id') and source.get('start') and source.get('end') and
                not source.get('normalization_issue') and aware(source['end']) > aware(source['start'])):
            anchored_days.add((aware(source['start']).date().isoformat(),
                               instructor_key(source.get('instructor'))))
    for offer in accepted:
        if offer.get('offerType') == 'seated_class':
            anchored_days.add((offer['date'], instructor_key(offer.get('instructor'))))
    retained = []
    for offer in accepted:
        if offer.get('offerType') != 'seated_class' and (offer['date'], str(offer['courseId'])) in day_anchors:
            rejected.append(dict(offer, reasons=['existing_course_day_anchor']))
        elif offer.get('scheduleRole') == 'open_day' and (
                (offer['date'], instructor_key(offer.get('instructor'))) in anchored_days or
                (offer['date'], '') in anchored_days):
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


def finalize(payload, now=None):
    """Shared V2 finalizer: enforce leases without reapplying V1 date suppression."""
    from scripts.apply_anchor_policy import _rebuild_dates
    from datetime import datetime, timezone
    now=aware(now or datetime.now(timezone.utc))
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
    return _rebuild_dates(result,kept)
