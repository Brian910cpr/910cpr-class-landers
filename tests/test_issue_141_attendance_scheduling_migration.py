import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase/migrations/20260911190000_attendance_scheduling_state_gate.sql").read_text(encoding="utf-8")
DB_TEST = (ROOT / "supabase/tests/issue_141_attendance_scheduling_state.sql").read_text(encoding="utf-8")


class AttendanceSchedulingMigrationTests(unittest.TestCase):
    def test_attendance_is_a_positive_fact_with_provenance(self):
        for marker in (
            "landerware_attendance_assertions",
            "asserted_by text not null",
            "asserted_at timestamptz not null",
            "attendance_artifact",
            "approved_authoritative_source",
            "attendance_assertion_evidence_required",
            "affirmative_attendance_requires_assertion",
            "attendance_assertion_does_not_match_state",
        ):
            self.assertIn(marker, MIGRATION)
        self.assertNotIn("missing_score", MIGRATION)
        self.assertNotIn("card not issued", MIGRATION.lower())

    def test_unknown_attendance_only_queues_internal_closeout(self):
        self.assertIn("attendance_status = 'unknown'", MIGRATION)
        self.assertIn("instructor_closeout_required", MIGRATION)
        self.assertIn("landerware_closeout_tasks", MIGRATION)
        self.assertNotIn("insert into public.landerware_messages", MIGRATION.lower())
        self.assertIn("'messagesInserted', 0", MIGRATION)
        self.assertIn("unknown attendance created outbound message", DB_TEST)

    def test_required_by_and_source_are_fail_closed(self):
        self.assertIn("required_by_required", MIGRATION)
        self.assertIn("required_by_source_required", MIGRATION)
        self.assertIn("landerware_scheduling_deadline_required", MIGRATION)
        self.assertIn("expected required_by_required", DB_TEST)

    def test_replays_are_idempotent(self):
        self.assertGreaterEqual(MIGRATION.count("idempotentReplay"), 4)
        self.assertIn("idempotency_key text not null unique", MIGRATION)
        self.assertIn("attendance replay duplicated assertion", DB_TEST)
        self.assertIn("request replay was not idempotent", DB_TEST)

    def test_database_test_is_transactional_and_nonpersistent(self):
        normalized = DB_TEST.strip().lower()
        self.assertTrue(normalized.startswith("-- run after"))
        self.assertIn("begin;", normalized)
        self.assertTrue(normalized.endswith("rollback;"))


if __name__ == "__main__":
    unittest.main()
