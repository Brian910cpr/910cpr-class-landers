import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "migrations" / "20260922220000_universal_scheduling_gateway.sql").read_text(encoding="utf-8")
EDGE = (ROOT / "supabase" / "functions" / "scheduling-gateway" / "index.ts").read_text(encoding="utf-8")
PAGE = (ROOT / "docs" / "schedule" / "index.html").read_text(encoding="utf-8")
NOT_FOUND = (ROOT / "docs" / "404.html").read_text(encoding="utf-8")


class UniversalSchedulingGatewayTests(unittest.TestCase):
    def test_supports_every_required_lifecycle_without_course_specific_routes(self):
        for purpose in (
            "initial_scheduling",
            "direct_registration",
            "reschedule",
            "no_show_recovery",
            "renewal_22_month",
            "renewal_23_month",
            "instructor_invitation",
        ):
            self.assertIn(purpose, MIGRATION)
            self.assertIn(purpose, EDGE)
        self.assertNotIn("heartsaver-skills-only", EDGE.lower())
        self.assertIn("compatible_course_ids", MIGRATION)

    def test_tokens_are_opaque_hashed_expiring_and_revocable(self):
        self.assertIn("token_sha256 text not null unique", MIGRATION)
        self.assertIn("expires_at timestamptz not null", MIGRATION)
        self.assertIn("revoked_at timestamptz", MIGRATION)
        self.assertIn('await sha256(rawToken)', EDGE)
        self.assertRegex(EDGE, r"crypto\.getRandomValues\(new Uint8Array\(32\)\)")
        self.assertNotIn("paid=true", PAGE)

    def test_context_rechecks_current_registration_and_live_schedule(self):
        self.assertIn("currentPaymentPolicy", EDGE)
        self.assertIn("landerware_registrations?id=eq.", EDGE)
        self.assertIn("/data/schedule_future.json", EDGE)
        self.assertIn('session.registration_status !== "open"', EDGE)
        self.assertIn("session.public_direct_booking !== true", EDGE)
        self.assertIn("compatible.has(courseId)", EDGE)

    def test_selection_is_idempotent_audited_and_append_only_for_reschedules(self):
        self.assertIn("idempotency_key text not null unique", MIGRATION)
        self.assertIn("for update", MIGRATION.lower())
        self.assertIn("supersedes_registration_id", MIGRATION)
        self.assertIn("superseded_by_registration_id", MIGRATION)
        self.assertIn("landerware_scheduling_actions", MIGRATION)
        self.assertIn("landerware_activity_events", MIGRATION)
        self.assertNotIn("delete from public.landerware_registrations", MIGRATION.lower())

    def test_privileged_tables_and_mutation_are_not_public(self):
        self.assertIn("enable row level security", MIGRATION)
        self.assertIn("from public, anon, authenticated", MIGRATION)
        self.assertIn("to service_role", MIGRATION)
        self.assertIn("x-hot-sync-admin-key", EDGE)
        self.assertIn("requireAdmin(request)", EDGE)

    def test_page_has_one_contextual_action_and_no_catalog_browser(self):
        self.assertIn("Available dates", PAGE)
        self.assertIn("These options are checked against the live schedule", PAGE)
        self.assertIn("payment.message", PAGE)
        self.assertIn("Confirm this class", PAGE)
        self.assertNotIn("course carousel", PAGE.lower())
        self.assertNotIn("Google Tag Manager", PAGE)

    def test_email_style_path_is_recovered_on_static_host(self):
        self.assertIn("landerwareScheduleToken", NOT_FOUND)
        self.assertIn('location.replace("/schedule/")', NOT_FOUND)
        self.assertIn("sessionStorage.getItem('landerwareScheduleToken')", PAGE)
        self.assertRegex(NOT_FOUND, re.compile(r"schedule.*A-Za-z0-9_", re.DOTALL))


if __name__ == "__main__":
    unittest.main()
