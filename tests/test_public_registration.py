import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "docs" / "register" / "index.html").read_text(encoding="utf-8")
EDGE = (ROOT / "supabase" / "functions" / "public-registration" / "index.ts").read_text(encoding="utf-8")
SQL = (ROOT / "supabase" / "migrations" / "20260908233000_public_registration_intents.sql").read_text(encoding="utf-8")
QUEUE_SQL = (ROOT / "supabase" / "migrations" / "20260908233800_public_registration_intent_queue.sql").read_text(encoding="utf-8")
NATIVE_SQL = (ROOT / "supabase" / "migrations" / "20260909220000_native_public_checkout.sql").read_text(encoding="utf-8")


class PublicRegistrationTests(unittest.TestCase):
    def test_collects_multiple_students_and_uses_idempotency(self):
        for name in ("firstName", "lastName", "email", "phone"):
            self.assertIn(f'data-field="{name}"', PAGE)
        self.assertIn("Add another student", PAGE)
        self.assertIn("students:entries", PAGE)
        self.assertIn("idempotency-key", PAGE)

    def test_only_accepts_open_public_sessions_and_native_catalog(self):
        self.assertIn('x.public_direct_booking===true', EDGE)
        self.assertIn('x.registration_status==="open"', EDGE)
        self.assertIn("landerware_registration_catalog", EDGE)
        self.assertNotIn('provider: "enrollware"', EDGE)

    def test_hold_is_not_an_active_registration_until_paid(self):
        self.assertIn("default 'held'", NATIVE_SQL)
        self.assertIn("landerware_finalize_public_order", NATIVE_SQL)
        self.assertIn("'active','landerware_native_checkout'", NATIVE_SQL)

    def test_checkout_rules_are_durable(self):
        self.assertIn("interval '30 minutes'", NATIVE_SQL)
        self.assertIn("selected_addons", NATIVE_SQL)
        self.assertIn("billing_codes", NATIVE_SQL)
        self.assertIn("insufficient_seats", NATIVE_SQL)
        self.assertIn("Do not auto-release codes or materials", EDGE)

    def test_privileged_rpc_is_not_publicly_executable(self):
        self.assertIn("from public, anon, authenticated", SQL)
        self.assertIn("to service_role", SQL)
        self.assertIn("from public, anon, authenticated", QUEUE_SQL)


if __name__ == "__main__":
    unittest.main()
