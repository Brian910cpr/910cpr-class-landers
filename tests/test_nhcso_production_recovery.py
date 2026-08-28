import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EDGE = (ROOT / "supabase/functions/nhcso-workspace/index.ts").read_text(encoding="utf-8")
MIGRATION = (ROOT / "supabase/migrations/20260828030000_nhcso_durable_session_recovery.sql").read_text(encoding="utf-8")
WORKSPACE = (ROOT / "docs/corp/nhcso/index.html").read_text(encoding="utf-8")


class NhcsoProductionRecoveryTests(unittest.TestCase):
    def test_cadre_selectors_are_persistent_data_driven(self):
        self.assertIn('action === "list_instructors"', EDGE)
        self.assertIn('.eq("qualification_key", "NHCSO_CADRE")', EDGE)
        self.assertIn("await loadInstructors()", WORKSPACE)
        self.assertNotRegex(WORKSPACE, r'<option>Crystal Jasper</option>')

    def test_one_session_and_original_records_are_linked(self):
        self.assertIn("where external_class_id=p_class_number", MIGRATION)
        self.assertIn("class_session_id uuid references public.class_sessions(id)", MIGRATION)
        self.assertIn("registrations_nhcso_student_unique", MIGRATION)
        self.assertIn("select id into session_id from public.class_sessions where external_class_id=p_class_number", MIGRATION)

    def test_lead_and_assistant_are_relational_and_audited(self):
        self.assertIn("create table if not exists public.class_session_instructors", MIGRATION)
        self.assertIn("'assistant','audited_correction'", MIGRATION)
        self.assertIn("'crystal-assistant-correction'", MIGRATION)

    def test_documents_and_completion_requirements_stay_on_same_session(self):
        self.assertIn("update public.nhcso_documents set class_session_id=session_id", MIGRATION)
        for requirement in ("roster", "skills_testing", "written_exam", "instructor_attestation"):
            self.assertIn(f"'{requirement}','verified'", MIGRATION)

    def test_card_workflow_is_evidence_gated(self):
        self.assertIn("create table if not exists public.session_card_processing", MIGRATION)
        self.assertIn("'ready_for_issue',active_count,0,'[]'::jsonb", MIGRATION)

    def test_notifications_are_post_commit_outbox_items_and_failure_isolated(self):
        self.assertIn("transactional_email_outbox", MIGRATION)
        self.assertIn("submitter_confirmation", MIGRATION)
        self.assertIn("operations_notification", MIGRATION)
        self.assertIn("committed_class_preserved: true", EDGE)
        self.assertIn('status: "failed"', EDGE)

    def test_document_retrieval_is_bound_to_document_and_class(self):
        self.assertIn('action === "get_document_link"', EDGE)
        self.assertRegex(EDGE, re.compile(r'\.eq\("id", documentId\)\.eq\("class_number", classNumber\)'))
        self.assertIn("createSignedUrl(document.storage_path, 300", EDGE)


if __name__ == "__main__":
    unittest.main()
