import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "docs" / "register" / "index.html").read_text(encoding="utf-8")
EDGE = (ROOT / "supabase" / "functions" / "public-registration" / "index.ts").read_text(encoding="utf-8")
SQL = (ROOT / "supabase" / "migrations" / "20260908233000_public_registration_intents.sql").read_text(encoding="utf-8")
QUEUE_SQL = (ROOT / "supabase" / "migrations" / "20260908233800_public_registration_intent_queue.sql").read_text(encoding="utf-8")


class PublicRegistrationTests(unittest.TestCase):
    def test_collects_student_identity_and_uses_idempotency(self):
        for name in ("firstName", "lastName", "email", "phone"):
            self.assertIn(f'name="{name}"', PAGE)
        self.assertIn("idempotency-key", PAGE)

    def test_only_accepts_open_public_sessions_and_enrollware_checkout(self):
        self.assertIn('item.public_direct_booking === true', EDGE)
        self.assertIn('item.registration_status === "open"', EDGE)
        self.assertIn('checkout.origin !== "https://coastalcprtraining.enrollware.com"', EDGE)

    def test_pending_intent_is_not_an_active_participant_status(self):
        self.assertIn("'awaiting_external_checkout'", QUEUE_SQL)
        self.assertIn("public_registration_intents", QUEUE_SQL)
        self.assertIn("queue_public_registration_intent", EDGE)

    def test_privileged_rpc_is_not_publicly_executable(self):
        self.assertIn("from public, anon, authenticated", SQL)
        self.assertIn("to service_role", SQL)
        self.assertIn("from public, anon, authenticated", QUEUE_SQL)


if __name__ == "__main__":
    unittest.main()
