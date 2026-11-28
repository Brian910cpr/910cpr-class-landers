import copy
import unittest
from pathlib import Path

from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload
from scripts.fetch_canonical_scheduling_demand import stable_hash
from scripts.validate_layered_occupancy_projection import OccupancyGate, REQUIRED_PAGES, SCHEMA, expected_public_windows


class OccupancyGateTest(unittest.TestCase):
    def setUp(self):
        self.a = "2026-11-27T23:45:00-05:00"
        self.b = "2026-11-28T00:30:00-05:00"
        self.endpoint = {"generated_at": "2026-11-28T05:01:00Z", "sessions": [
            {"canonical_session_id": "PRIVATE-A", "session_status": "scheduled",
             "operational_has_active_seat": True, "visibility": "private",
             "consumption_start_at": self.a, "consumption_end_at": self.b},
            {"canonical_session_id": "STALE-B", "session_status": "active",
             "operational_has_stale_commitment": True, "start_at": self.a, "end_at": self.b},
            {"canonical_session_id": "CANCELED-C", "session_status": "canceled",
             "operational_has_active_seat": True, "start_at": self.a, "end_at": self.b},
        ]}
        self.rows = [
            {"source_file": "canonical_class_sessions", "source_event_id": "PRIVATE-A",
             "session_status": "scheduled", "operational_has_active_seat": True,
             "start": "2026-11-28T04:45:00Z", "end": "2026-11-28T05:30:00Z"},
            {"source_file": "canonical_class_sessions", "source_event_id": "STALE-B",
             "session_status": "active", "stale_commitment": True, "kind": "hold",
             "start": self.a, "end": self.b},
        ]

    def payload(self, page="bls"):
        return {"pageKey": page, "schedulingModel": SCHEMA,
                "_canonicalDemandFingerprint": (self.endpoint["generated_at"], stable_hash(self.endpoint)),
                "_windowCoverageEvidence": {"expected": {}, "closed": {}, "calendar_hash": "fixture"},
                "layeredDiagnostics": {"projected_sources": copy.deepcopy(self.rows), "reports": []}}

    def gate(self):
        return OccupancyGate(self.endpoint, active=True)

    def test_all_eight_carry_in_and_stale_proven_without_leaks(self):
        gate = self.gate()
        for page in REQUIRED_PAGES:
            payload = self.payload(page)
            gate.observe(page, payload)
            compact = str(public_selector_availability_payload(payload))
            for value in ("PRIVATE-A", "STALE-B", "_canonicalDemandFingerprint", "_windowCoverageEvidence", "layeredDiagnostics"):
                self.assertNotIn(value, compact)
        gate.finish(self.endpoint)
        self.assertEqual(gate.summary(), {"positive_count": 1, "stale_hold_count": 1, "verified_page_count": 8})

    def test_same_count_substitution_is_rejected_without_ids_in_log(self):
        payload = self.payload()
        payload["layeredDiagnostics"]["projected_sources"][0]["source_event_id"] = "WRONG"
        with self.assertRaisesRegex(ValueError, "^V2 canonical occupied identity/bounds projection mismatch$"):
            self.gate().observe("bls", payload)

    def test_changed_bounds_inferred_duration_and_dropped_hold_fail(self):
        for alteration in ({"end": self.a}, {"end": "2026-11-28T05:45:00Z"},
                           {"duration_resolution": "course metadata"}):
            payload = self.payload()
            payload["layeredDiagnostics"]["projected_sources"][0].update(alteration)
            with self.assertRaises(ValueError):
                self.gate().observe("bls", payload)
        payload = self.payload()
        payload["layeredDiagnostics"]["projected_sources"].pop()
        with self.assertRaises(ValueError):
            self.gate().observe("bls", payload)

    def test_noncandidate_resources_do_not_drop_occupied_rows(self):
        payload = self.payload()
        payload["dates"] = []
        payload["layeredDiagnostics"]["reports"] = []
        self.gate().observe("bls", payload)

    def test_missing_family_duplicate_page_stale_snapshot_and_wrong_mode_fail(self):
        gate = self.gate()
        gate.observe("bls", self.payload())
        with self.assertRaisesRegex(ValueError, "missing required families"):
            gate.finish(self.endpoint)
        with self.assertRaisesRegex(ValueError, "duplicated"):
            gate.observe("bls", self.payload())
        for page in REQUIRED_PAGES - {"bls"}:
            gate.observe(page, self.payload(page))
        with self.assertRaisesRegex(ValueError, "changed during"):
            gate.finish(dict(self.endpoint, generated_at="later"))
        altered = self.payload()
        altered["_canonicalDemandFingerprint"] = ("other", "snapshot")
        with self.assertRaisesRegex(ValueError, "different canonical"):
            self.gate().observe("bls", altered)
        with self.assertRaisesRegex(ValueError, "mode differ"):
            self.gate().observe("bls", {"schedulingModel": "v1"})
        v1 = OccupancyGate(None, active=False)
        v1.observe("bls", {})
        v1.finish(None)
        with self.assertRaisesRegex(ValueError, "mode differ"):
            v1.observe("bls", self.payload())

    def seated_payload(self, *, visibility="public"):
        row = self.endpoint["sessions"][0]
        row.update(external_class_id="PUBLIC-ALIAS", catalog_course_id="209806",
                   start_at=self.a, end_at=self.b, visibility=visibility,
                   registration_status="open", external_course_id=None, count_available=True, active_registration_count=1,
                   demand_status="current", demand_basis="canonical_active_registrations",
                   lead_instructor_identity={"status": "verified"}, lead_instructor_name="Fixture Lead")
        offer = {"offerType": "seated_class", "date": "2026-11-27", "startTime": "23:45",
                 "courseId": "209806", "instructor": "Fixture Lead",
                 "availabilityBlockId": "seated:PUBLIC-ALIAS",
                 "sourceAvailabilityBlock": {"sessionId": "PUBLIC-ALIAS"}}
        payload = self.payload()
        payload["offers"] = [copy.deepcopy(offer)]
        payload["dates"] = [{"date": offer["date"], "startTimes": [
            {"startTime": offer["startTime"], "courses": [offer]}]}]
        return payload

    def test_public_exact_seated_source_passes_and_private_injection_fails(self):
        payload = self.seated_payload()
        self.gate().observe("bls", payload)
        for visibility in ("private", "unlisted", "internal", None):
            with self.subTest(visibility=visibility):
                payload = self.seated_payload(visibility=visibility)
                with self.assertRaisesRegex(ValueError, "^V2 seated offer has no current public joinable canonical source$"):
                    self.gate().observe("bls", payload)

    def test_nested_only_or_relocated_seated_offer_fails(self):
        payload = self.seated_payload()
        payload["offers"] = []
        with self.assertRaisesRegex(ValueError, "seated offers differ from renderer input"):
            self.gate().observe("bls", payload)
        payload = self.seated_payload()
        payload["dates"][0]["startTimes"][0]["startTime"] = "23:50"
        with self.assertRaisesRegex(ValueError, "seated renderer coordinates"):
            self.gate().observe("bls", payload)

    def test_stale_zero_or_nonunique_source_cannot_be_rendered(self):
        for patch in ({"demand_status": "stale"}, {"active_registration_count": 0},
                      {"registration_status": "closed"}, {"lead_instructor_identity": {}},
                      {"external_course_id": "different"}):
            payload = self.seated_payload()
            self.endpoint["sessions"][0].update(patch)
            payload["_canonicalDemandFingerprint"] = (self.endpoint["generated_at"], stable_hash(self.endpoint))
            with self.assertRaisesRegex(ValueError, "no current public joinable canonical source"):
                self.gate().observe("bls", payload)
        payload = self.seated_payload()
        self.endpoint["sessions"][1]["external_class_id"] = "PUBLIC-ALIAS"
        payload["_canonicalDemandFingerprint"] = (self.endpoint["generated_at"], stable_hash(self.endpoint))
        with self.assertRaisesRegex(ValueError, "unique canonical source"):
            self.gate().observe("bls", payload)

    def test_engine_rejects_dropped_or_misrouted_source(self):
        payload = self.payload()
        room = "Fixture room"
        start, end = "2026-11-28T04:45:00+00:00", "2026-11-28T05:30:00+00:00"
        occupancy = {"canonical_source_ids": ["PRIVATE-A"], "start": start, "raw_end": end, "location": room}
        report = {"canonical_window_input": [["PRIVATE-A", start, end, room]],
                  "normalized_occupancy": [occupancy]}
        report = {**self.window_receipt("w1"), **report}
        payload["_windowCoverageEvidence"]["expected"] = {"w1": self.window_profile()}
        payload["layeredDiagnostics"]["reports"] = [report]
        self.gate().observe("bls", payload)
        for change in ({"location": "Wrong room"}, {"canonical_source_ids": []},
                       {"raw_end": "2026-11-28T05:40:00+00:00"}):
            report["normalized_occupancy"] = [dict(occupancy, **change)]
            with self.assertRaisesRegex(ValueError, "identities, bounds or rooms differ"):
                self.gate().observe("bls", payload)

    def window_profile(self):
        return ["PERSON-1", "Fixture Lead", "Fixture room",
                "2026-11-28T05:00:00+00:00", "2026-11-28T05:45:00+00:00"]

    def window_receipt(self, ident):
        person, label, room, start, end = self.window_profile()
        return {"availability_window": ident,
                "layered_windows": [{"instructor_source_id": ident, "room_source_id": "room-" + ident,
                                     "person_token": stable_hash({"person": person}),
                                     "instructor": label, "location": room, "start": start, "end": end}],
                "canonical_window_input": [], "normalized_occupancy": []}

    def test_empty_or_omitted_engine_windows_can_no_longer_pass(self):
        payload = self.payload()
        payload["_windowCoverageEvidence"]["expected"] = {
            "w1": self.window_profile(), "w2": self.window_profile()}
        for reports in ([], [self.window_receipt("w1")]):
            payload["layeredDiagnostics"]["reports"] = reports
            with self.assertRaisesRegex(ValueError, "neither evaluated nor closed"):
                self.gate().observe("bls", payload)
        payload["layeredDiagnostics"]["reports"] = [self.window_receipt("w1"), self.window_receipt("w2")]
        self.gate().observe("bls", payload)

    def test_wrong_person_room_or_instant_fails_even_when_occupancy_counts_match(self):
        payload = self.payload()
        payload["_windowCoverageEvidence"]["expected"] = {"w1": self.window_profile()}
        valid = self.window_receipt("w1")
        for field, bad in (("location", "Wrong room"), ("instructor", "Wrong name"), ("person_token", "Wrong stable ID"),
                           ("start", "2026-11-28T05:30:00+00:00")):
            mutated = copy.deepcopy(valid)
            mutated["layered_windows"][0][field] = bad
            payload["layeredDiagnostics"]["reports"] = [mutated]
            with self.assertRaisesRegex(ValueError, "person, resource or bounds differ"):
                self.gate().observe("bls", payload)

    def test_explicit_closed_window_cannot_supply_a_dynamic_offer(self):
        payload = self.payload()
        evidence = payload["_windowCoverageEvidence"]
        evidence["expected"] = {"w1": self.window_profile()}
        evidence["closed"] = copy.deepcopy(evidence["expected"])
        self.gate().observe("bls", payload)
        payload["offers"] = [{"offerType": "dynamic_appointment", "availabilityBlockId": "w1"}]
        with self.assertRaisesRegex(ValueError, "produced a public offer"):
            self.gate().observe("bls", payload)
        payload["offers"] = []
        evidence["closed"]["w1"][2] = "Wrong room"
        with self.assertRaisesRegex(ValueError, "lacks matching source evidence"):
            self.gate().observe("bls", payload)

    def test_raw_window_inventory_clips_carry_in_and_keeps_distinct_folds(self):
        rows = [
            dict(id="carry-in", person_id="ID", instructor_name="Fixture Lead",
                 start="2026-10-31T23:50:00-04:00", end="2026-11-01T01:30:00-05:00"),
            dict(id="ended", person_id="ID", instructor_name="Fixture Lead",
                 start="2026-10-31T23:50:00-04:00", end="2026-11-01T00:00:00-04:00"),
        ]
        inventory = expected_public_windows({"rows": rows}, now="2026-11-01T05:32:00Z",
            windows=lambda s: s["rows"], eligible=lambda w: True, interval=lambda w: (w["start"], w["end"]),
            source_id=lambda w, i: w["id"], resource="Fixture room")
        self.assertEqual(inventory, {"carry-in": ["ID", "Fixture Lead", "Fixture room",
                            "2026-11-01T04:00:00+00:00", "2026-11-01T06:30:00+00:00"]})

    def test_calendar_snapshot_change_fails_between_page_builds(self):
        gate = self.gate()
        gate.observe("bls", self.payload())
        changed = self.payload("pals")
        changed["_windowCoverageEvidence"]["calendar_hash"] = "other"
        with self.assertRaisesRegex(ValueError, "snapshot changed"):
            gate.observe("pals", changed)

    def test_same_source_with_conflicting_assignments_is_rejected(self):
        payload = self.payload()
        projection = payload["layeredDiagnostics"]["projected_sources"]
        projection.append(dict(projection[0], instructor="Different lead", resource="Different room"))
        with self.assertRaisesRegex(ValueError, "conflicting canonical occupancy assignments"):
            self.gate().observe("bls", payload)

    def test_publication_and_probe_wire_the_gate_before_public_serialization(self):
        root = Path(__file__).resolve().parents[1]
        for path, pack in (
            (".github/workflows/refresh-admin-availability.yml",
             "json.dumps(public_selector_availability_payload(payload)"),
            ("scripts/run_layered_release_probe.py", "feed=public_selector_availability_payload(payload)"),
        ):
            source = (root / path).read_text()
            self.assertLess(source.index("gate.observe("), source.index(pack))
            self.assertIn("gate.finish(load_publication_demand(", source)


if __name__ == "__main__":
    unittest.main()
