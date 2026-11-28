import copy
import unittest
from pathlib import Path

from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload
from scripts.fetch_canonical_scheduling_demand import stable_hash
from scripts.validate_layered_occupancy_projection import OccupancyGate, REQUIRED_PAGES, SCHEMA


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
                "layeredDiagnostics": {"projected_sources": copy.deepcopy(self.rows)}}

    def gate(self):
        return OccupancyGate(self.endpoint, active=True)

    def test_all_eight_carry_in_and_stale_proven_without_leaks(self):
        gate = self.gate()
        for page in REQUIRED_PAGES:
            payload = self.payload(page)
            gate.observe(page, payload)
            compact = str(public_selector_availability_payload(payload))
            for value in ("PRIVATE-A", "STALE-B", "_canonicalDemandFingerprint", "layeredDiagnostics"):
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
