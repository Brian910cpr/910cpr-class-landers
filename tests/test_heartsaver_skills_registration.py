import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase/migrations/20260827220000_landerware_unified_registration.sql").read_text(encoding="utf-8")
EDGE = (ROOT / "supabase/functions/landerware-registration/index.ts").read_text(encoding="utf-8")
MAXIM = (ROOT / "supabase/functions/maxim-portal/index.ts").read_text(encoding="utf-8")
PAGE = (ROOT / "docs/register/heartsaver-skills/index.html").read_text(encoding="utf-8")

class RegistrationProfileTests(unittest.TestCase):
    def test_profile_expresses_full_registration_policy(self):
        for field in ("registration_mode", "session_policy", "allowed_entry_contexts", "required_fields", "requirements", "addons", "payer_policy", "pricing_behavior", "corporate_context", "confirmation_template_key", "completion_prerequisites"):
            self.assertIn(field, SQL)

    def test_requirement_timing_and_satisfaction_are_generic(self):
        for field in ("required_before_registration", "required_before_attendance", "required_before_completion", "upload_now", "submit_later", "staff_may_satisfy", "requirement_type"):
            self.assertIn(field, SQL)
        self.assertIn("reqRow.requirement_type", EDGE)
        self.assertNotIn("AHA_ONLINE_COMPLETION_CERTIFICATE", EDGE)

    def test_generic_handler_is_profile_driven(self):
        self.assertIn("landerware_registration_profiles?profile_key", EDGE)
        self.assertIn('parts[0]===\"register\"&&parts[1]', EDGE)
        self.assertNotIn("const COURSE_ID", EDGE)
        self.assertIn("register/aha-heartsaver-skills-public", PAGE)

    def test_person_and_registration_operations_remain_shared(self):
        self.assertIn("landerware_create_or_find_person", SQL)
        self.assertIn("landerware_register", SQL)
        self.assertIn('rest("rpc/landerware_register"', EDGE)
        self.assertIn('rest("rpc/landerware_register"', MAXIM)
        self.assertIn('rest("rpc/landerware_create_or_find_person"', MAXIM)

    def test_entry_contexts_and_payer_states_are_data(self):
        for value in ("public_anonymous", "secure_known_person", "staff_admin", "maxim_staff", "employee_self_service", "customer_pays", "corporate_client_pays", "invoice_later", "prepaid", "free", "special_price"):
            self.assertIn(value, SQL)
        for field in ("payer_mode", "payment_state", "billing_state"):
            self.assertIn(field, SQL)

    def test_arbitrary_course_needs_configuration_not_handler(self):
        self.assertEqual(1, EDGE.count('parts[0]===\"register\"'))
        self.assertIn("p_profile_key", SQL)
        self.assertIn("registration_profile_snapshot", SQL)

    def test_documents_bind_to_generic_requirement_instance(self):
        self.assertIn("registration_requirement_id", SQL)
        self.assertIn("registrationRequirementId:reqRow.id", EDGE)
        self.assertIn("requirement-submit", EDGE)
        for marker in ("missing_file", "unsupported_file_type", "file_too_large", "invalid_or_expired_token"):
            self.assertIn(marker, EDGE)

    def test_third_course_is_configuration_only(self):
        self.assertIn("nhcso-foundations-instructor-led-v1", SQL)
        self.assertIn("landerware-foundations", SQL)
        self.assertNotIn("nhcso-foundations", EDGE.lower())
        self.assertIn('"mode":"invoice_later"', SQL)

    def test_generic_lifecycle_operations_preserve_linkage(self):
        for operation in ("landerware_satisfy_registration_requirement", "landerware_record_completion", "landerware_issue_credential"):
            self.assertIn(operation, SQL)
        for field in ("registration_id", "person_id", "course_id", "session_id"):
            self.assertIn(field, SQL)
        for event in ("requirement_satisfied", "registration_completed", "credential_issued"):
            self.assertIn(event, SQL)

    def test_required_session_and_upload_are_forwarded_and_enforced(self):
        for field in ("externalSessionId", "startsAt", "locationName"):
            self.assertIn(field, EDGE)
        self.assertIn("required_requirement_missing", EDGE)

    def test_http_replay_does_not_recreate_side_effects(self):
        self.assertIn("existingMessage", EDGE)
        self.assertIn("existing.length", EDGE)
        self.assertIn("registration-confirmation:${result.registrationId}", EDGE)

if __name__ == "__main__": unittest.main()
