import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "docs" / "register" / "index.html").read_text(encoding="utf-8")
EDGE = (ROOT / "supabase" / "functions" / "public-registration" / "index.ts").read_text(encoding="utf-8")
SQL = (ROOT / "supabase" / "migrations" / "20260908233000_public_registration_intents.sql").read_text(encoding="utf-8")
QUEUE_SQL = (ROOT / "supabase" / "migrations" / "20260908233800_public_registration_intent_queue.sql").read_text(encoding="utf-8")
RETAIL_SQL = (ROOT / "supabase" / "migrations" / "20260910100000_first_party_retail_checkout.sql").read_text(encoding="utf-8")


class PublicRegistrationTests(unittest.TestCase):
    def test_collects_student_identity_and_uses_idempotency(self):
        for name in ("firstName", "lastName", "email", "phone"):
            self.assertIn(f'name="{name}"', PAGE)
        self.assertIn("idempotency-key", PAGE)

    def test_only_accepts_open_public_sessions_and_enrollware_checkout(self):
        self.assertIn('item.public_direct_booking === true', EDGE)
        self.assertIn('item.registration_status === "open"', EDGE)
        self.assertIn('checkout.origin !== "https://coastalcprtraining.enrollware.com"', EDGE)

    def test_legacy_handoff_intent_remains_migratable_but_is_not_the_live_path(self):
        self.assertIn("'awaiting_external_checkout'", QUEUE_SQL)
        self.assertIn("public_registration_intents", QUEUE_SQL)
        self.assertNotIn('rpc("queue_public_registration_intent"', EDGE)

    def test_first_party_checkout_owns_hold_and_payment_lifecycle(self):
        for marker in ("begin_retail_checkout", 'status text not null default \'held\'', "hold_expires_at", "confirm_retail_payment", "status='active'", "payment_state='paid'"):
            self.assertIn(marker, RETAIL_SQL)
        self.assertIn('stripe("/checkout/sessions"', EDGE)
        self.assertIn('route[0] === "stripe-webhook"', EDGE)
        self.assertIn("validStripeSignature", EDGE)

    def test_retail_prices_are_catalog_snapshots_not_guesses(self):
        for profile, cents in (("retail-209806", "7500"), ("retail-359474", "7500"), ("retail-210549", "5500")):
            self.assertIn(profile, RETAIL_SQL)
            self.assertIn(cents, RETAIL_SQL)
        self.assertIn("raw/course_archive_v4.json", RETAIL_SQL)

    def test_checkout_recovery_and_capacity_are_durable(self):
        self.assertIn("landerware_messages", EDGE)
        self.assertIn("retail-checkout-recovery:", EDGE)
        self.assertIn("p_capacity", EDGE)
        self.assertIn("session_full", RETAIL_SQL)
        self.assertIn("interval '31 minutes'", RETAIL_SQL)
        self.assertIn("status='expired'", RETAIL_SQL)

    def test_webhook_rotation_replay_and_confirmation_are_safe(self):
        self.assertIn('parts.filter(x => x[0] === "v1")', EDGE)
        self.assertIn("if v_order.status='paid'", RETAIL_SQL)
        self.assertIn("retail-paid-confirmation:", RETAIL_SQL)
        self.assertIn("on conflict(idempotency_key) do nothing", RETAIL_SQL)

    def test_privileged_rpc_is_not_publicly_executable(self):
        self.assertIn("from public, anon, authenticated", SQL)
        self.assertIn("to service_role", SQL)
        self.assertIn("from public, anon, authenticated", QUEUE_SQL)


if __name__ == "__main__":
    unittest.main()
