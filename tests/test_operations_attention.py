from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FUNCTION = (ROOT / "supabase/functions/production-board/index.ts").read_text(encoding="utf-8")
DASHBOARD = (ROOT / "docs/admin/dashboard.html").read_text(encoding="utf-8")
CLIENT = (ROOT / "docs/admin/attention-summary.js").read_text(encoding="utf-8")


class OperationsAttentionTests(unittest.TestCase):
    def test_queue_is_authenticated(self):
        self.assertIn('if(!(await authorized(req)))', FUNCTION)
        self.assertIn("x-maxim-session", CLIENT)

    def test_instructor_expiration_and_unknown_dates_are_actionable(self):
        self.assertIn("expires_at.is.null", FUNCTION)
        self.assertIn("expires_at.lte", FUNCTION)
        self.assertIn("Record ${person.display_name}'s expiration", FUNCTION)

    def test_cross_silo_sources_are_derived(self):
        for source in ("session_card_processing", "transactional_email_outbox", "accessory_attention_queue", "requirement_inquiries", "maxim_registration_requests", "certification_import_files"):
            self.assertIn(source, FUNCTION)

    def test_dashboard_leads_with_where_needed(self):
        self.assertLess(DASHBOARD.index('id="where-needed"'), DASHBOARD.index('id="productionSummary"'))
        self.assertIn("attention-summary.js?v=20260828-1", DASHBOARD)

    def test_status_counts_are_visible(self):
        for status in ("critical", "due", "watch"):
            self.assertIn(status, CLIENT)


if __name__ == "__main__":
    unittest.main()
