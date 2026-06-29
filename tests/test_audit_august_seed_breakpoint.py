import unittest

from scripts import audit_august_seed_breakpoint as audit


class AugustSeedBreakpointAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = audit.run()

    def test_august_breakpoint_is_before_public_filtering(self) -> None:
        summary = self.report["summary"]
        self.assertEqual("data/audit/dynamic_offers_preview.json", summary["first_breakpoint"])
        self.assertEqual(0, summary["dynamic_offers_generated_august_total"])
        self.assertEqual(0, summary["selected_august_seeds_total"])
        self.assertEqual(0, summary["appointment_url_previews_august_total"])
        self.assertGreater(summary["august_bls_seed_simulation_selected_proposals"], 0)

    def test_july_four_seed_source_is_understood(self) -> None:
        previews = audit.read_json(audit.AUDIT_DIR / "seed_appointment_url_preview.json")["previews"]
        july_four = [row for row in previews if row["date"] == "2026-07-04"]
        self.assertTrue(july_four)
        self.assertTrue(all(row["confidence"] == "high" for row in july_four))
        self.assertTrue(all(row["appointmentDayId"] for row in july_four))
        self.assertTrue(all(row["appointment_url_preview"] for row in july_four))
        self.assertGreaterEqual(self.report["summary"]["url_preview_stats"]["urls_previewed"], len(july_four))

    def test_existing_enrollware_rows_still_exist_and_unknown_seed_rows_do_not_render(self) -> None:
        schedule = audit.read_json(audit.ROOT / "docs" / "data" / "schedule_future.json")
        sessions = schedule["sessions"]
        self.assertTrue(sessions)
        self.assertTrue(any(row.get("session_id") and row.get("course_id") for row in sessions))
        self.assertFalse(any(row.get("course_key") == "UNKNOWN" and row.get("seed_id") for row in sessions))

    def test_valid_reviewed_appointment_seeds_can_render_from_current_artifacts(self) -> None:
        previews = audit.read_json(audit.AUDIT_DIR / "seed_appointment_url_preview.json")["previews"]
        valid = [row for row in previews if row.get("confidence") == "high" and row.get("appointment_url_preview")]
        self.assertTrue(valid)
        for row in valid:
            self.assertTrue(row["appointmentDayId"])
            self.assertTrue(row["course_id"])

    def test_course_master_gate_csv_keeps_unreviewed_or_unknown_blockers_visible(self) -> None:
        gate_rows = self.report["course_master_gate_rows"]
        self.assertTrue(gate_rows)
        self.assertTrue(any("appointment_seed_allowed_false" in row["blockers"] for row in gate_rows))
        self.assertTrue(any("dynamic_offer_allowed_false" in row["blockers"] for row in gate_rows))


if __name__ == "__main__":
    unittest.main()
