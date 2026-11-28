"""In-process, restricted V2 occupancy gate. Never serialize source evidence."""
from __future__ import annotations

from datetime import datetime, timezone

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
        actual[key] = value
    return actual


class OccupancyGate:
    def __init__(self, endpoint, *, active):
        self.active = active
        self.fingerprint = (endpoint.get("generated_at"), stable_hash(endpoint)) if active else None
        self.expected = expected_occupancy(endpoint) if active else {}
        self.seen = set()

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
