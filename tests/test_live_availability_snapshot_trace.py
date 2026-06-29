import unittest

from scripts import audit_live_availability_snapshot_trace as trace


class LiveAvailabilitySnapshotTraceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = trace.run()
        cls.summary = cls.report["summary"]

    def test_seed_simulation_august_bls_is_lost_before_dynamic_generation(self) -> None:
        self.assertGreater(self.summary["seed_simulation_august_bls_blocks"], 0)
        self.assertEqual(0, self.summary["live_snapshot_august_blocks"])
        self.assertEqual(0, self.summary["dynamic_august_offers"])
        self.assertEqual("data/audit/live_availability_snapshot_preview.json", self.summary["first_divergence_file"])

    def test_live_snapshot_source_is_reported_loudly(self) -> None:
        self.assertEqual("scripts/build_live_availability_snapshot.py", self.summary["live_snapshot_script"])
        self.assertEqual("data/audit/live_availability_snapshot_preview.json", self.summary["active_dynamic_input_path"])
        self.assertEqual("live_availability_snapshot", self.summary["dynamic_generation_availability_source"])
        self.assertGreater(self.summary["live_snapshot_available_blocks"], 0)

    def test_runtime_rrule_gap_is_visible(self) -> None:
        self.assertGreaterEqual(self.summary["runtime_events_with_august_rrule_not_expanded"], 1)
        self.assertEqual(0, self.summary["runtime_august_events"])

    def test_course_master_is_downstream_of_trace(self) -> None:
        self.assertIn("live snapshot", self.summary["zero_reason"])
        self.assertNotIn("Course Master", self.summary["zero_reason"])


if __name__ == "__main__":
    unittest.main()
