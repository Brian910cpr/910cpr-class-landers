import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "docs" / "register" / "index.html").read_text(encoding="utf-8")
EDGE = (ROOT / "supabase" / "functions" / "landerware-registration" / "index.ts").read_text(encoding="utf-8")
MIGRATION = (ROOT / "supabase" / "migrations" / "20260903190143_landerware_public_registration_front_door.sql").read_text(encoding="utf-8")


class PublicRegistrationFrontDoorTests(unittest.TestCase):
    def test_page_collects_only_required_identity_fields(self):
        for field in ("firstName", "lastName", "email", "phone"):
            self.assertRegex(PAGE, rf'name="{field}"[^>]*required')
        self.assertIn("Continue Registration", PAGE)
        self.assertIn("Start your registration", PAGE)
        self.assertIn("Continue to secure checkout", PAGE)

    def test_handoff_is_resolved_server_side_and_not_prefilled(self):
        self.assertIn("await publicSession(sessionId)", EDGE)
        self.assertIn('origin!=="https://coastalcprtraining.enrollware.com"', EDGE)
        self.assertIn('prefill:{firstName:false,lastName:false,email:false,phone:false}', EDGE)
        self.assertNotIn("searchParams.set", EDGE)

    def test_database_keeps_one_pending_intent_and_reconciles_in_place(self):
        self.assertIn("landerware_front_door_one_intent_per_person_session", MIGRATION)
        self.assertIn("'awaiting_external_checkout'", MIGRATION)
        self.assertIn("create or replace function public.landerware_reconcile_external_registration", MIGRATION)
        update = re.search(
            r"update public\.landerware_registrations\s+set status = 'confirmed'.*?where id = v_registration\.id",
            MIGRATION,
            re.S,
        )
        self.assertIsNotNone(update)

    def test_database_functions_are_service_role_only(self):
        self.assertIn("from public, anon, authenticated", MIGRATION)
        self.assertIn("to service_role", MIGRATION)


if __name__ == "__main__":
    unittest.main()
