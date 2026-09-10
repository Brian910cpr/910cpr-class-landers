import unittest
from datetime import date

from scripts.build_long_range_bls_inventory import build_inventory


class LongRangeBlsInventoryTests(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "schema_version": "test.v1",
            "enabled": True,
            "planning_horizon_days": 100,
            "short_term_cutoff_days": 90,
            "course_ids": ["209806", "359474", "210549"],
            "weekly_templates": [
                {"weekday": 0, "start_time": "09:15", "course_id": "209806"},
                {"weekday": 0, "start_time": "12:30", "course_id": "359474"},
                {"weekday": 0, "start_time": "18:15", "course_id": "210549"},
            ],
        }
        self.catalog = {
            course_id: {"course_id": course_id, "official_title": course_id, "family": "BLS"}
            for course_id in self.policy["course_ids"]
        }
        self.ranges = [(date(2026, 1, 1), date(2027, 12, 31))]

    def test_only_long_range_proposals_survive_without_demand(self):
        result = build_inventory(self.policy, self.catalog, self.ranges, today=date(2026, 9, 10))
        self.assertTrue(result["occurrences"])
        self.assertTrue(all((date.fromisoformat(item["date"]) - date(2026, 9, 10)).days > 90 for item in result["occurrences"]))
        self.assertTrue(all(item["is_committed_session"] is False for item in result["occurrences"]))
        self.assertTrue(all(item["reserves_capacity"] is False for item in result["occurrences"]))
        self.assertTrue(all(item["emit_event_structured_data"] is False for item in result["occurrences"]))
        self.assertEqual({"209806", "359474", "210549"}, {item["course_id"] for item in result["occurrences"]})

    def test_demand_preserves_proposal_inside_cutoff(self):
        key = "seo-bls-209806-20260914-0915"
        result = build_inventory(self.policy, self.catalog, self.ranges, today=date(2026, 9, 10), demand_keys={key})
        match = next(item for item in result["occurrences"] if item["inventory_key"] == key)
        self.assertEqual("demand_detected", match["inventory_state"])
        self.assertFalse(match["is_committed_session"])
        self.assertEqual("canonical_session_workflow", match["promotion_target"])

    def test_unknown_course_id_fails_closed(self):
        policy = {**self.policy, "course_ids": [*self.policy["course_ids"], "made-up"]}
        with self.assertRaisesRegex(ValueError, "unknown course IDs"):
            build_inventory(policy, self.catalog, self.ranges, today=date(2026, 9, 10))

    def test_outside_verified_container_range_is_pruned(self):
        ranges = [(date(2026, 1, 1), date(2026, 11, 30))]
        result = build_inventory(self.policy, self.catalog, ranges, today=date(2026, 9, 10))
        self.assertFalse(result["occurrences"])
        self.assertIn("outside_verified_appointment_container_range", {item["reason"] for item in result["pruned"]})


if __name__ == "__main__":
    unittest.main()
