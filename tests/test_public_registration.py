import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "docs" / "register" / "index.html").read_text(encoding="utf-8")
BLS_PAGE = (ROOT / "docs" / "bls.html").read_text(encoding="utf-8")
EDGE = (ROOT / "supabase" / "functions" / "public-registration" / "index.ts").read_text(encoding="utf-8")
SQL = (ROOT / "supabase" / "migrations" / "20260908233000_public_registration_intents.sql").read_text(encoding="utf-8")
QUEUE_SQL = (ROOT / "supabase" / "migrations" / "20260908233800_public_registration_intent_queue.sql").read_text(encoding="utf-8")
NATIVE_SQL = (ROOT / "supabase" / "migrations" / "20260909220000_native_public_checkout.sql").read_text(encoding="utf-8")
BLS_ADDONS_SQL = (ROOT / "supabase" / "migrations" / "20260930030000_bls_public_registration_addons.sql").read_text(encoding="utf-8")
PER_STUDENT_BILLING_SQL = (ROOT / "supabase" / "migrations" / "20260930050000_per_student_public_billing_codes.sql").read_text(encoding="utf-8")


class PublicRegistrationTests(unittest.TestCase):
    def test_collects_multiple_students_and_uses_idempotency(self):
        for name in ("firstName", "lastName", "email", "phone"):
            self.assertIn(f'data-field="{name}"', PAGE)
        self.assertIn("Add another student", PAGE)
        self.assertIn("students:order", PAGE)
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
        self.assertIn("greatest(v_registered,coalesce(v_inventory.externally_registered,0))", NATIVE_SQL)

    def test_catalog_is_seeded_from_verified_enrollware_snapshots(self):
        for course_id, cents in (("209806", "7500"), ("359474", "7500"), ("210549", "5500")):
            self.assertIn(f"('{course_id}','enrollware'", NATIVE_SQL)
            self.assertIn(cents, NATIVE_SQL)
        self.assertIn("raw/course_archive_v4.json", NATIVE_SQL)

    def test_stripe_checkout_is_current_and_idempotent(self):
        self.assertIn('"2026-07-29.dahlia"', EDGE)
        self.assertIn('"idempotency-key":idempotencyKey', EDGE)
        self.assertIn('p.set("integration_identifier"', EDGE)
        self.assertNotIn("payment_method_types", EDGE)
        self.assertLess(EDGE.index("stripeKey();const result"), EDGE.index('rpc("landerware_create_public_order"'))

    def test_gmail_queue_is_preserved_and_page_does_not_restart_in_enrollware(self):
        self.assertIn('delivery_provider:"gmail"', EDGE)
        self.assertIn("landerware_messages", EDGE)
        self.assertNotIn("fallbackRegistrationUrl", PAGE)
        self.assertIn("Your information is still on this page", PAGE)

    def test_bls_initial_addons_and_company_picker_are_present(self):
        self.assertIn("BLS Provider Manual eBook", BLS_ADDONS_SQL)
        self.assertIn("1749", BLS_ADDONS_SQL)
        self.assertIn("AHA Heartsaver First Aid in person", BLS_ADDONS_SQL)
        self.assertIn("AHA Heartsaver First Aid online", BLS_ADDONS_SQL)
        self.assertIn("5000", BLS_ADDONS_SQL)
        self.assertIn("6000", BLS_ADDONS_SQL)
        self.assertIn("payer_mode','corporate_invoice", BLS_ADDONS_SQL)
        self.assertIn("query.length<3", PAGE)
        self.assertIn("COMPANY_BILLING_CODES", PAGE)
        self.assertIn("order-total", PAGE)
        self.assertIn("data-billing-code", PAGE)
        self.assertIn("billingCode:card.querySelector", PAGE)
        self.assertIn("data-same-for-all", PAGE)
        self.assertIn("copyFirstToAll", PAGE)
        self.assertIn("data-manual-choice", PAGE)
        self.assertIn("data-first-aid-choice", PAGE)
        self.assertIn("data-product-image", PAGE)
        self.assertIn('target="_blank"', PAGE)
        self.assertIn("Buy Direct from AHA", PAGE)
        self.assertIn("manualChoice", PAGE)
        self.assertIn("firstAidChoice", PAGE)
        self.assertIn("add column if not exists billing_code", PER_STUDENT_BILLING_SQL)
        self.assertIn("selected_options jsonb", PER_STUDENT_BILLING_SQL)
        self.assertIn("v_student->>'billingCode'", PER_STUDENT_BILLING_SQL)
        self.assertIn("v_discount:=v_discount+v_student_discount", PER_STUDENT_BILLING_SQL)
        self.assertIn("landerware_corporate_invoice_lines", PER_STUDENT_BILLING_SQL)
        self.assertIn("This confirmation records that we provided the official purchase link", EDGE)

    def test_privileged_rpc_is_not_publicly_executable(self):
        self.assertIn("from public, anon, authenticated", SQL)
        self.assertIn("to service_role", SQL)
        self.assertIn("from public, anon, authenticated", QUEUE_SQL)

    def test_only_real_bls_initial_sessions_route_to_native_registration(self):
        self.assertIn("String(course.courseId) === '209806'", BLS_PAGE)
        self.assertIn("course.offerType === 'seated_class'", BLS_PAGE)
        self.assertIn("/register/?session=${encodeURIComponent(nativeSessionId)}", BLS_PAGE)
        self.assertIn(": course.appointmentUrl", BLS_PAGE)


if __name__ == "__main__":
    unittest.main()
