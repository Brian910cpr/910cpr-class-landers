import copy
import unittest
from scripts.layered_resource_readiness import audit, timestamp


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.now = timestamp("2026-10-05T03:00:00Z")
        row = dict(start="2026-10-10T00:00:00-04:00", end="2026-10-11T00:00:00-04:00",
                   observed_at="2026-10-05T02:59:00Z", freshness_minutes=60,
                   source="explicit_test_evidence", status="known_complete")
        self.snapshot = dict(resources=[dict(id="office", active=True, location="shipyard")],
            room_availability=[dict(row, id="room", resource_id="office", location="shipyard", simultaneous_classes=1)],
            instructor_availability=[dict(row, id="instructor", instructor_id="brian", locations=["shipyard"])],
            commitment_coverage=[dict(row, id="commitments", instructor_id="brian", location="shipyard")])

    def codes(self, snapshot):
        return {i["code"] for i in audit(snapshot, self.now)["issues"]}

    def test_explicit_overnight_coverage_intersects_without_business_hours(self):
        report = audit(self.snapshot, self.now)
        self.assertEqual(report["state"], "RESOURCE_INPUTS_READY")
        self.assertEqual(report["intersections"][0]["start"], "2026-10-10T04:00:00+00:00")

    def test_container_or_location_does_not_supply_room_availability(self):
        self.assertIn("missing_room_availability", self.codes(dict(resources=self.snapshot["resources"])))

    def test_fresh_feed_does_not_refresh_commitment_proof(self):
        self.snapshot["commitment_coverage"][0]["observed_at"] = "2026-09-27T00:00:00Z"
        self.assertIn("stale_or_future_commitment", self.codes(self.snapshot))
        self.assertFalse(audit(self.snapshot, self.now)["intersections"])

    def test_unknown_capacity_is_not_single_room(self):
        del self.snapshot["room_availability"][0]["simultaneous_classes"]
        self.assertIn("unsupported_or_unknown_room_concurrency", self.codes(self.snapshot))

    def test_missing_resource_and_incomplete_coverage_fail_closed(self):
        self.snapshot["resources"] = []
        self.assertIn("unresolved_room_resource", self.codes(self.snapshot))
        self.snapshot["resources"] = [dict(id="office", active=True, location="shipyard")]
        self.snapshot["commitment_coverage"] = []
        self.assertIn("missing_complete_commitment_coverage", self.codes(self.snapshot))

    def test_naive_timestamps_and_future_observation_rejected(self):
        self.snapshot["room_availability"][0]["start"] = "2026-10-10T00:00:00"
        self.assertIn("invalid_room_coverage", self.codes(self.snapshot))
        self.snapshot["instructor_availability"][0]["observed_at"] = "2026-10-05T03:01:00Z"
        self.assertIn("stale_or_future_instructor", self.codes(self.snapshot))

    def test_input_is_not_mutated(self):
        original = copy.deepcopy(self.snapshot)
        audit(self.snapshot, self.now)
        self.assertEqual(original, self.snapshot)


if __name__ == "__main__":
    unittest.main()
