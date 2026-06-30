import unittest

from scripts import audit_august_seed_breakpoint as audit


class AugustSeedBreakpointAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = audit.run()

    def test_august_reaches_active_generation_after_rrule_expansion(self) -> None:
        summary = self.report["summary"]
        self.assertEqual("resolved_at_dynamic_offers_preview", summary["first_breakpoint"])
        self.assertTrue(summary["upstream_source_mismatch_resolved"])
        self.assertGreater(summary["dynamic_offers_generated_august_total"], 0)
        self.assertGreater(summary["selected_august_seeds_total"], 0)
        self.assertGreater(summary["appointment_url_previews_august_total"], 0)
        self.assertGreater(summary["august_bls_seed_simulation_selected_proposals"], 0)

    def test_selected_seed_urls_are_appointment_backed(self) -> None:
        previews = audit.read_json(audit.AUDIT_DIR / "seed_appointment_url_preview.json")["previews"]
        self.assertTrue(previews)
        self.assertTrue(all(row["confidence"] == "high" for row in previews))
        self.assertTrue(all(row["appointmentDayId"] for row in previews))
        self.assertTrue(all(row["appointment_url_preview"] for row in previews))
        self.assertGreaterEqual(self.report["summary"]["url_preview_stats"]["urls_previewed"], len(previews))

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
