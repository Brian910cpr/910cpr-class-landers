from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.build_session_bundle import build_bundle, stable_id


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "fixtures" / "september_19_source_records.json"
EXAMPLE = ROOT / "data" / "fixtures" / "session_bundle_2026-09-19.json"
SCHEMA = ROOT / "data" / "contracts" / "session_bundle.schema.json"


class SessionBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = json.loads(SOURCE.read_text(encoding="utf-8"))
        self.bundle = build_bundle(self.source, generated_at="2026-09-04T00:00:00Z")

    def test_stable_ids_depend_on_kind_and_source_identity(self) -> None:
        first = stable_id("ses", "landerware_class_sessions", "abc")
        self.assertEqual(first, stable_id("ses", "LANDERWARE_CLASS_SESSIONS", "abc"))
        self.assertNotEqual(first, stable_id("ses", "landerware_class_sessions", "def"))
        self.assertNotEqual(first, stable_id("reg", "landerware_class_sessions", "abc"))

    def test_september_19_operational_and_cancelled_occupancy(self) -> None:
        by_time = {row["start_at"]: row for row in self.bundle["sessions"]}
        self.assertTrue(by_time["2026-09-19T09:00:00-04:00"]["occupancy"]["reserves_customer_availability"])
        self.assertTrue(by_time["2026-09-19T11:00:00-04:00"]["occupancy"]["reserves_customer_availability"])
        self.assertFalse(by_time["2026-09-19T14:00:00-04:00"]["occupancy"]["reserves_customer_availability"])
        self.assertEqual([], by_time["2026-09-19T14:00:00-04:00"]["occupancy"]["blocking_resource_ids"])
        self.assertEqual(
            {"Hendersonville Family Dental", "Little Leaps"},
            {row["location"]["display_name"] for row in self.bundle["sessions"] if row["occupancy"]["reserves_customer_availability"]},
        )

    def test_unknown_registrations_are_not_reported_as_zero(self) -> None:
        self.assertEqual([], self.bundle["registrations"])
        self.assertIn("registrations_not_present", {row["code"] for row in self.bundle["missing_dependencies"]})

    def test_checked_in_example_is_reproducible_and_contract_complete(self) -> None:
        self.assertEqual(self.bundle, json.loads(EXAMPLE.read_text(encoding="utf-8")))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), set(self.bundle))
        self.assertTrue(all(row["source_refs"] for row in self.bundle["sessions"]))

    def test_same_source_id_in_two_systems_cannot_cross_link_registration(self) -> None:
        source = {
            "bundle_source_id": "collision-test",
            "scope": {"date": "2026-09-19", "timezone": "America/New_York"},
            "sessions": [
                {"source_system": "system_a", "source_id": "shared-1", "start_at": "2026-09-19T09:00:00-04:00", "end_at": "2026-09-19T10:00:00-04:00", "status": "scheduled"},
                {"source_system": "system_b", "source_id": "shared-1", "start_at": "2026-09-19T11:00:00-04:00", "end_at": "2026-09-19T12:00:00-04:00", "status": "scheduled"},
            ],
            "registrations": [
                {"source_system": "registration_system", "source_id": "reg-a", "session_source_system": "system_a", "session_source_id": "shared-1", "person_id": "per_a", "status": "registered"},
                {"source_system": "registration_system", "source_id": "reg-b", "session_source_system": "system_b", "session_source_id": "shared-1", "person_id": "per_b", "status": "registered"},
            ],
        }
        bundle = build_bundle(source, generated_at="2026-09-04T00:00:00Z")
        by_person = {row["person_id"]: row["session_id"] for row in bundle["registrations"]}
        self.assertEqual(stable_id("ses", "system_a", "shared-1"), by_person["per_a"])
        self.assertEqual(stable_id("ses", "system_b", "shared-1"), by_person["per_b"])
        self.assertNotEqual(by_person["per_a"], by_person["per_b"])


if __name__ == "__main__":
    unittest.main()
