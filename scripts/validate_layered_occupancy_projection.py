"""In-process, restricted V2 occupancy gate. Never serialize source evidence."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from scripts.fetch_canonical_scheduling_demand import stable_hash

SCHEMA = "layered-publication.v2"
REQUIRED_PAGES = frozenset({
    "bls", "heartsaver", "acls", "pals", "arc", "hsi",
    "uscg_first_aid_cpr_aed", "family_cpr",
})
ACTIVE = {"scheduled", "active"}


def instant(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("Explicit occupied instant required")
    return value.astimezone(timezone.utc)


def span(start, end):
    try:
        a, b = instant(start), instant(end)
        if a < b:
            return a, b
    except (ValueError, TypeError, OverflowError):
        pass
    return None


def positive(row):
    count = row.get("active_registration_count")
    # Older valid source responses imply count available when not explicit.
    return row.get("operational_has_active_seat") is True or (
        type(count) is int and count > 0 and row.get("count_available") is not False
    )


def expected_occupancy(endpoint):
    """Derive independently from the full scoped endpoint, including carry-in."""
    expected = {}
    for row in endpoint["sessions"]:
        if row.get("session_status") not in ACTIVE:
            continue
        tag = "positive" if positive(row) else (
            "stale" if row.get("operational_has_stale_commitment") is True else None)
        if tag is None:
            continue
        key = str(row.get("canonical_session_id") or "").strip()
        times = span(row.get("consumption_start_at") or row.get("start_at"),
                     row.get("consumption_end_at") or row.get("end_at"))
        # Disallow conflicting or missing occupancy semantics. The runner may
        # still display its private diagnostics, but V2 may not publish.
        if not key or times is None:
            raise ValueError("V2 canonical source has unproved occupied bounds or identity")
        value = (tag, times)
        if key in expected and expected[key] != value:
            raise ValueError("V2 canonical source has conflicting occupied identity")
        expected[key] = value
    return expected


def observed_occupancy(projected):
    actual = {}
    assignments = {}
    for row in projected:
        if (row.get("source_file") != "canonical_class_sessions"
                or row.get("session_status") not in ACTIVE):
            continue
        tag = "positive" if positive(row) else ("stale" if row.get("stale_commitment") is True else None)
        if tag is None:
            continue
        key = str(row.get("source_event_id") or "").strip()
        times = span(row.get("start"), row.get("end"))
        if (not key or times is None or row.get("normalization_issue")
                or row.get("duration_resolution") or (tag == "stale" and row.get("kind") != "hold")):
            raise ValueError("V2 selector has unproved canonical occupied bounds or lifecycle")
        value = (tag, times)
        if key in actual and actual[key] != value:
            raise ValueError("V2 selector has conflicting occupied identity")
        assignment = tuple(row.get(field) for field in
                           ("instructor", "instructor_unassigned", "resource", "location",
                            "availability_location_mode", "stored_instructor_identity_state"))
        if key in assignments and assignments[key] != assignment:
            raise ValueError("V2 selector has conflicting canonical occupancy assignments")
        assignments[key] = assignment
        actual[key] = value
    return actual


def expected_public_windows(snapshot, *, now, windows, eligible, interval, source_id,
                            resource, horizon_days=90):
    """Enumerate independently from raw calendar rows, before adapter/cache filtering.

    The caller supplies the inspected snapshot's source selection policy and
    bound parser. It must not use selected_windows, a report, or a cache result.
    """
    if not isinstance(snapshot, dict) or not isinstance(resource, str) or not resource:
        raise ValueError("V2 calendar window inputs are missing")
    zone = ZoneInfo("America/New_York")
    local_day = instant(now).astimezone(zone).replace(hour=0, minute=0, second=0, microsecond=0)
    lower, upper = instant(local_day), instant(local_day + timedelta(days=horizon_days))
    result = {}
    for index, row in enumerate(windows(snapshot), start=1):
        if not eligible(row):
            continue
        try:
            start, end = map(instant, interval(row))
        except (ValueError, TypeError, AttributeError, KeyError, OverflowError):
            raise ValueError("V2 eligible calendar window has unresolved bounds") from None
        if end <= start:
            raise ValueError("V2 eligible calendar window has unresolved bounds")
        if end <= lower or start >= upper:
            continue
        ident = source_id(row, index)
        person = str(row.get("person_id") or "").strip()
        label = str(row.get("instructor_name") or "").strip()
        if not ident or ident in result or not label or not person:
            raise ValueError("V2 calendar window has missing or duplicate source identity")
        result[ident] = [person, label, resource,
                         max(start, lower).isoformat(), min(end, upper).isoformat()]
    return result


def validate_window_dispositions(expected, reports, closed, offers):
    """A real engine intersection or an explicit fail-closed receipt, exactly once."""
    if not isinstance(expected, dict) or not isinstance(closed, dict) or not isinstance(reports, list):
        raise ValueError("V2 calendar window coverage evidence is missing")
    observed = {}
    for report in reports:
        if not isinstance(report, dict):
            raise ValueError("V2 invalid calendar window evidence")
        ident = report.get("availability_window")
        intersections = report.get("layered_windows")
        if (not isinstance(ident, str) or ident not in expected or ident in observed
                or not isinstance(intersections, list) or len(intersections) != 1
                or not isinstance(intersections[0], dict)):
            raise ValueError("V2 engine has missing, unexpected or duplicate calendar window")
        intersection = intersections[0]
        times = span(intersection.get("start"), intersection.get("end"))
        expected_profile = expected[ident]
        if (intersection.get("instructor_source_id") != ident
                or intersection.get("room_source_id") != "room-" + ident
                or intersection.get("person_token") != stable_hash({"person": expected_profile[0]})
                or times is None
                or [intersection.get("instructor"), intersection.get("location"),
                    *(time.isoformat() for time in times)] != expected_profile[1:]):
            raise ValueError("V2 engine calendar window person, resource or bounds differ")
        observed[ident] = True
    for ident, profile in closed.items():
        if ident not in expected or ident in observed or profile != expected[ident]:
            raise ValueError("V2 closed calendar window lacks matching source evidence")
        observed[ident] = False
    if set(observed) != set(expected):
        raise ValueError("V2 calendar window was neither evaluated nor closed")
    for row in offers:
        if row.get("offerType") != "dynamic_appointment":
            continue
        if any(isinstance(row.get(key), str) and row[key] in closed
               for key in ("availabilityBlockId", "availabilityWindow")):
            raise ValueError("V2 closed calendar window produced a public offer")


def dynamic_offer_key(offer):
    """Restricted lookup for a stable offer DTO across finalizer deep copies."""
    return stable_hash({"offer": offer})


def accepted_candidate_shape(row):
    try:
        local = instant(row["start"]).astimezone(ZoneInfo("America/New_York"))
        return (row["course"], local.date().isoformat(), local.strftime("%H:%M"),
                instant(row["end"]), row["instructor"], row["location"],
                "barnacle" if row["mode"] == "barnacle" else "open_day",
                row["duration_minutes"],
                int((instant(row["instruction_end"]) - instant(row["start"])).total_seconds() / 60))
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        raise ValueError("V2 engine candidate has invalid accepted geometry") from None


def validate_dynamic_provenance(payload, reports):
    """Compare final top-level AND renderer input offers to accepted engine rows."""
    lineage = payload.get("_dynamicOfferLineage")
    offers = payload.get("offers", [])
    visible = []
    for row in offers:
        if row.get("offerType") == "seated_class":
            continue
        if row.get("offerType") != "dynamic_appointment":
            raise ValueError("V2 final offer has no recognized source type")
        visible.append(row)
    nested = []
    for day in payload.get("dates", []):
        for slot in day.get("startTimes", []):
            for row in slot.get("courses", []):
                if row.get("offerType") == "seated_class":
                    continue
                if row.get("offerType") != "dynamic_appointment":
                    raise ValueError("V2 final renderer offer has no recognized source type")
                if (row.get("date"), row.get("startTime")) != (day.get("date"), slot.get("startTime")):
                    raise ValueError("V2 dynamic renderer coordinates differ from accepted offer")
                nested.append(row)
    keys = [dynamic_offer_key(row) for row in visible]
    if Counter(keys) != Counter(dynamic_offer_key(row) for row in nested):
        raise ValueError("V2 dynamic offers differ from renderer input")
    if not keys:
        return
    if not isinstance(lineage, dict):
        raise ValueError("V2 dynamic offer lineage is missing")
    accepted = {rep["availability_window"]: {accepted_candidate_shape(row) for row in rep["accepted"]}
                for rep in reports if rep.get("accepted") is not None}
    for row, key in zip(visible, keys):
        window = lineage.get(key)
        if not isinstance(window, str) or window not in accepted:
            raise ValueError("V2 dynamic offer lacks an evaluated calendar window")
        if row.get("dynamicBookingMode") == "request":
            if any(row.get(f) for f in ("availabilityBlockId", "availabilityWindow",
                                       "matchedContainerId", "appointmentDayId", "appointmentUrl",
                                       "registrationUrl", "sourceAvailabilityBlock",
                                       "sourceSessionIds", "edgeIds")):
                raise ValueError("V2 request-only offer contains booking or private source data")
        elif (row.get("availabilityBlockId") != window or row.get("availabilityWindow") != window):
            raise ValueError("V2 dynamic booking window differs from restricted lineage")
        try:
            end = instant(row["occupiedUntil"])
            if end.astimezone(ZoneInfo("America/New_York")).strftime("%H:%M") != row["schedulerConsumptionEnd"]:
                raise ValueError("inconsistent visible end")
            shape = (row["courseId"], row["date"], row["startTime"], end,
                     row["instructor"], row["resource"], row["scheduleRole"],
                     row["schedulerConsumptionMinutes"], row["durationMinutes"])
        except (ValueError, TypeError, AttributeError, KeyError, OverflowError):
            raise ValueError("V2 dynamic offer has invalid consumption geometry") from None
        if shape not in accepted[window]:
            raise ValueError("V2 dynamic offer does not match an accepted engine candidate")


def validate_seated_provenance(payload, endpoint):
    """Independently attest final seated rows against the fresh canonical source."""
    by_alias = defaultdict(list)
    for row in endpoint["sessions"]:
        for alias in {str(row.get(key) or "").strip() for key in
                      ("canonical_session_id", "external_class_id")} - {""}:
            by_alias[alias].append(row)

    def attest(offer):
        block = offer.get("sourceAvailabilityBlock")
        if not isinstance(block, dict):
            raise ValueError("V2 seated offer lacks source identity")
        sid = str(block.get("sessionId") or "").strip()
        if (not sid or any(str(offer[key]).strip() != sid for key in
                           ("session_id", "sourceSessionId") if offer.get(key) is not None)
                or offer.get("availabilityBlockId") != "seated:" + sid):
            raise ValueError("V2 seated offer has conflicting source identity")
        matches = by_alias[sid]
        if len(matches) != 1:
            raise ValueError("V2 seated offer lacks unique canonical source")
        row = matches[0]
        count = row.get("active_registration_count")
        lead = row.get("lead_instructor_identity")
        course_ids = {str(row[key]) for key in ("catalog_course_id", "external_course_id")
                      if row.get(key) is not None and str(row[key]).strip()}
        times = span(row.get("start_at"), row.get("end_at"))
        if (row.get("session_status") not in ACTIVE or row.get("visibility") != "public"
                or row.get("registration_status") != "open"
                or row.get("demand_status") != "current"
                or row.get("demand_basis") != "canonical_active_registrations"
                or row.get("count_available") is not True or type(count) is not int or count < 1
                or not isinstance(lead, dict) or lead.get("status") != "verified"
                or not offer.get("instructor")
                or str(offer["instructor"]).strip().casefold()
                   != str(row.get("lead_instructor_name") or "").strip().casefold()
                or course_ids != {str(offer.get("courseId"))} or times is None):
            raise ValueError("V2 seated offer has no current public joinable canonical source")
        local = times[0].astimezone(ZoneInfo("America/New_York"))
        if (offer.get("date"), offer.get("startTime")) != (local.date().isoformat(), local.strftime("%H:%M")):
            raise ValueError("V2 seated offer differs from its canonical occurrence")
        canonical_id = str(row.get("canonical_session_id") or "").strip()
        if not canonical_id:
            raise ValueError("V2 seated offer lacks a durable canonical source identity")
        return canonical_id, dynamic_offer_key(offer)

    top = [attest(offer) for offer in payload.get("offers", [])
           if offer.get("offerType") == "seated_class"]
    nested = []
    for day in payload.get("dates", []):
        for slot in day.get("startTimes", []):
            for offer in slot.get("courses", []):
                if offer.get("offerType") != "seated_class":
                    continue
                if (offer.get("date"), offer.get("startTime")) != (day.get("date"), slot.get("startTime")):
                    raise ValueError("V2 seated renderer coordinates differ from its occurrence")
                nested.append(attest(offer))
    if Counter(top) != Counter(nested) or len({ident for ident, _ in top}) != len(top):
        raise ValueError("V2 seated offers differ from renderer input")


def validate_engine_coverage(reports):
    """Prove submitted source IDs survived actual engine normalization.

    This is not an independent room/instructor oracle: source rows filtered
    out *before* submission can still need protection. Window completeness
    is checked separately against the frozen calendar source inventory.
    """
    if not isinstance(reports, list):
        raise ValueError("V2 engine report evidence is missing")
    for report in reports:
        expected = report.get("canonical_window_input")
        blocks = report.get("normalized_occupancy")
        if not isinstance(expected, list) or not isinstance(blocks, list):
            raise ValueError("V2 engine occupied-source evidence is missing")
        actual = []
        for block in blocks:
            ids = block.get("canonical_source_ids", [])
            if not isinstance(ids, list) or any(not isinstance(key, str) or not key for key in ids):
                raise ValueError("V2 engine occupied-source evidence is invalid")
            if not ids:
                continue
            times = span(block.get("start"), block.get("raw_end"))
            location = block.get("location")
            if times is None or not isinstance(location, str) or not location:
                raise ValueError("V2 engine occupied-source bounds or room are invalid")
            if location.startswith("instructor-only:"):
                location = "instructor-only:"
            actual.extend([key, *(value.isoformat() for value in times), location] for key in ids)
        if (any(not isinstance(row, list) or len(row) != 4 or
                any(not isinstance(value, str) or not value for value in row) for row in expected)
                or sorted(expected) != sorted(actual) or len({row[0] for row in actual}) != len(actual)):
            raise ValueError("V2 engine occupied canonical identities, bounds or rooms differ from window input")


class OccupancyGate:
    def __init__(self, endpoint, *, active):
        self.active = active
        self.fingerprint = (endpoint.get("generated_at"), stable_hash(endpoint)) if active else None
        self.expected = expected_occupancy(endpoint) if active else {}
        self.endpoint = endpoint if active else None
        self.seen = set()
        self.calendar_snapshot_hash = None
        self.calendar_window_inventory = None

    def observe(self, key, payload):
        v2 = payload.get("schedulingModel") == SCHEMA
        if v2 != self.active:
            raise ValueError("Public refresh selector and occupancy gate mode differ")
        if not v2:
            return
        if payload.get("pageKey") != key or key in self.seen:
            raise ValueError("V2 selector page evidence is missing or duplicated")
        proof = payload.get("_canonicalDemandFingerprint")
        if proof != self.fingerprint:
            raise ValueError("V2 selector used a different canonical source snapshot")
        rows = (payload.get("layeredDiagnostics") or {}).get("projected_sources")
        if not isinstance(rows, list):
            raise ValueError("V2 selector canonical projection evidence is missing")
        actual = observed_occupancy(rows)
        reports = payload["layeredDiagnostics"].get("reports")
        evidence = payload.get("_windowCoverageEvidence")
        if not isinstance(evidence, dict) or not evidence.get("calendar_hash"):
            raise ValueError("V2 calendar snapshot evidence is missing")
        snapshot_hash = evidence["calendar_hash"]
        if self.calendar_snapshot_hash is not None and snapshot_hash != self.calendar_snapshot_hash:
            raise ValueError("V2 calendar snapshot changed between page calculations")
        inventory = evidence.get("expected")
        validate_window_dispositions(inventory, reports, evidence.get("closed"),
                                     payload.get("offers", []))
        inventory_hash = stable_hash({"windows": inventory})
        if self.calendar_window_inventory is not None and inventory_hash != self.calendar_window_inventory:
            raise ValueError("V2 expected calendar window scope differs between families")
        validate_engine_coverage(reports)
        validate_dynamic_provenance(payload, reports)
        validate_seated_provenance(payload, self.endpoint)
        self.calendar_snapshot_hash = snapshot_hash
        self.calendar_window_inventory = inventory_hash
        if actual != self.expected:
            # No raw IDs, dates, or customer data in public CI logs.
            raise ValueError("V2 canonical occupied identity/bounds projection mismatch")
        self.seen.add(key)

    def finish(self, current):
        if not self.active:
            return
        if not REQUIRED_PAGES.issubset(self.seen):
            raise ValueError("V2 canonical occupancy proof missing required families")
        if self.fingerprint != (current.get("generated_at"), stable_hash(current)):
            raise ValueError("V2 canonical snapshot changed during public refresh")

    def summary(self):
        return {"positive_count": sum(tag == "positive" for tag, _ in self.expected.values()),
                "stale_hold_count": sum(tag == "stale" for tag, _ in self.expected.values()),
                "verified_page_count": len(self.seen)}
