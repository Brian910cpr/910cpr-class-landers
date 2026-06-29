import unittest

from scripts import audit_august_offer_explosion as audit


class AugustOfferExplosionAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = audit.run()
        cls.summary = cls.report["summary"]

    def test_august_dynamic_offers_are_compressed_before_seed_selection(self) -> None:
        self.assertGreater(self.summary["live_august_availability_blocks"], 0)
        self.assertEqual(20901, self.summary["dynamic_august_offers"])
        self.assertGreater(self.summary["dynamic_august_bls_offers"], 0)
        self.assertLess(self.summary["public_sellable_august_offers"], self.summary["dynamic_august_offers"])
        self.assertEqual(60, self.summary["public_sellable_august_offers"])
        self.assertEqual(4, self.summary["selected_august_seeds"])

    def test_selected_august_seeds_are_url_backed_but_not_rendered_by_audit(self) -> None:
        self.assertEqual(4, self.summary["august_appointment_url_previews"])
        self.assertEqual(0, self.summary["august_rendered_seed_rows"])
        self.assertTrue(self.summary["safety_checks"]["rrule_expansion_creates_candidates_not_public_rows"])

    def test_large_generated_files_are_tracked_review_artifacts(self) -> None:
        files = {item["path"]: item for item in self.summary["large_files"]}
        self.assertTrue(files["data/audit/dynamic_offers_preview.json"]["tracked"])
        self.assertTrue(files["data/audit/public_sellable_offers_preview.json"]["tracked"])
        self.assertGreater(files["data/audit/dynamic_offers_preview.json"]["size_mb"], 50)


if __name__ == "__main__":
    unittest.main()
