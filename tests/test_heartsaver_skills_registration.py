import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase/migrations/20260827220000_landerware_unified_registration.sql").read_text(encoding="utf-8")
EDGE = (ROOT / "supabase/functions/landerware-registration/index.ts").read_text(encoding="utf-8")
MAXIM = (ROOT / "supabase/functions/maxim-portal/index.ts").read_text(encoding="utf-8")
REGISTER_PAGE = (ROOT / "docs/register/heartsaver-skills/index.html").read_text(encoding="utf-8")
SUBMIT_PAGE = (ROOT / "docs/certificate-submit/index.html").read_text(encoding="utf-8")
ADMIN = (ROOT / "docs/admin/dashboard.html").read_text(encoding="utf-8")


class HeartsaverSkillsRegistrationTests(unittest.TestCase):
    def test_unlisted_course_has_no_enrollware_dependency(self):
        self.assertIn("'aha-heartsaver-skills-session'", MIGRATION)
        self.assertIn("'AHA Heartsaver Skills Session'", MIGRATION)
        self.assertIn("'heartsaver-skills', false, null", MIGRATION)
        self.assertIn('name="robots" content="noindex,nofollow"', REGISTER_PAGE)
        self.assertIn("'AHA Heartsaver Skills Session'", ADMIN)

    def test_public_and_maxim_use_same_registration_rpc(self):
        call = 'rest("rpc/landerware_register"'
        self.assertIn(call, EDGE)
        self.assertIn(call, MAXIM)
        self.assertNotIn('rest("rpc/landerware_record_corporate_registration"', MAXIM)

    def test_identity_matching_is_case_insensitive_and_preserves_registrations(self):
        self.assertIn("lower(trim(coalesce(current_email,'')))=v_email", MIGRATION)
        self.assertIn('rest("rpc/landerware_create_or_find_person"', MAXIM)
        self.assertIn("order by created_at asc limit 1 for update", MIGRATION)
        self.assertNotIn("delete from public.landerware_registrations", MIGRATION.lower())
        self.assertIn("p_existing_person_id: durable.personId", MAXIM)

    def test_registration_is_idempotent(self):
        self.assertIn("landerware_registration_idempotency", MIGRATION)
        self.assertIn("idempotentReplay", EDGE)
        self.assertIn("sessionStorage.getItem('heartsaverRegistrationKey')", REGISTER_PAGE)

    def test_certificate_is_registration_bound_and_later_submission_reuses_it(self):
        self.assertIn("registration_id uuid not null references public.landerware_registrations(id)", MIGRATION)
        self.assertIn("requirement_id uuid not null references public.landerware_certification_requirements(id)", MIGRATION)
        self.assertIn("related_record_ids: { personId: token.person_id, registrationId: token.registration_id, requirementId: token.requirement_id }", EDGE)
        self.assertIn("satisfied_at: new Date().toISOString(), status: \"satisfied\"", EDGE)
        self.assertIn("original registration is now up to date", SUBMIT_PAGE)

    def test_upload_validation_and_token_lifecycle(self):
        for marker in ("missing_file", "unsupported_file_type", "file_too_large", "invalid_or_expired_token"):
            self.assertIn(marker, EDGE)
        self.assertIn("submission_count", EDGE)
        self.assertIn("duplicate: true", EDGE)
        self.assertIn("180 * 86400000", EDGE)

    def test_confirmation_copy_handles_both_flows(self):
        self.assertIn("We received your AHA online-course completion certificate", EDGE)
        self.assertIn("Submit Completion Certificate", EDGE)
        self.assertIn("You may also bring the certificate with you to class", EDGE)
        self.assertIn('delivery_provider: "gmail"', EDGE)


if __name__ == "__main__":
    unittest.main()
