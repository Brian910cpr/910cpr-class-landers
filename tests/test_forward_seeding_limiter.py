import unittest

from scripts import audit_forward_seeding_limiter as limiter


class ForwardSeedingLimiterTraceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = limiter.run()
        cls.summary = cls.report["summary"]

    def test_exact_limiter_is_rrule_not_expanded_in_runtime_export(self) -> None:
        self.assertEqual("scripts/export_calendar_snapshots.py", self.summary["limiter"]["file"])
        self.assertEqual("parse_ics_events", self.summary["limiter"]["function"])
        self.assertIn("no future occurrences are materialized", self.summary["limiter"]["specific_behavior"])
        self.assertEqual("data/runtime/calendar_snapshots/brian_do_not_schedule.json", self.summary["first_divergence"]["file"])

    def test_sixty_day_export_reaches_august_but_rows_stop_july_four(self) -> None:
        path_b = self.summary["path_b_live_snapshot"]
        self.assertEqual(60, path_b["runtime_snapshot_declared_days"])
        self.assertIn("2026-08", path_b["runtime_snapshot_declared_end"])
        self.assertEqual("2026-07-04", path_b["runtime_event_date_range"]["end"])
        self.assertEqual(0, path_b["august_rows"])

    def test_seed_simulation_uses_report_only_august_horizon(self) -> None:
        path_a = self.summary["path_a_seed_simulation"]
        self.assertEqual("2026-08-01", path_a["horizon_start_date"])
        self.assertEqual(45, path_a["lookahead_days"])
        self.assertEqual(14, path_a["seed_selection_window_days"])
        self.assertGreater(path_a["august_rows"], 0)


if __name__ == "__main__":
    unittest.main()
