from __future__ import annotations

import unittest
from datetime import datetime

from scripts.import_enrollware_student_report import apply_snapshot_to_sessions, build_snapshot


class ImportEnrollwareStudentReportTests(unittest.TestCase):
    def test_build_snapshot_groups_students_without_pii(self):
        rows = [
            {"First Name": "One", "Email": "one@example.com", "Class ID": 51222, "Course Date": datetime(2026, 7, 18, 14, 30), "Course": "AHA BLS Provider (Initial)", "Instructor": "Brian Ennis", "Course Location": "Shipyard", "Status": "Pending"},
            {"First Name": "Two", "Email": "two@example.com", "Class ID": 51222, "Course Date": datetime(2026, 7, 18, 14, 30), "Course": "AHA BLS Provider (Initial)", "Instructor": "Brian Ennis", "Course Location": "Shipyard", "Status": "Pending"},
        ]
        payload = build_snapshot(rows, source_name="report.xlsx", source_modified_at="2026-07-18T08:40:17-04:00")
        self.assertEqual(2, payload["counts"]["student_rows"])
        self.assertEqual(1, payload["counts"]["classes_with_students"])
        self.assertEqual(2, payload["classes"][0]["seated_count"])
        self.assertNotIn("One", str(payload))
        self.assertNotIn("example.com", str(payload))

    def test_apply_snapshot_distinguishes_seated_empty_and_outside_coverage(self):
        snapshot = {
            "source_modified_at": "2026-07-18T08:40:17-04:00",
            "class_date_coverage": {"start": "2026-07-18", "end": "2026-07-29"},
            "classes": [{"start_at": "2026-07-18T14:30:00-04:00", "course_key": "aha_bls_provider_initial", "class_id": "51222", "seated_count": 3, "status_counts": {"Pending": 3}}],
        }
        sessions = [
            {"start": "2026-07-18T14:30:00-04:00", "course": {"mapped_clean_title": "AHA BLS Provider"}, "capacity": {}},
            {"start": "2026-07-20T09:15:00-04:00", "course": {"mapped_clean_title": "AHA BLS Provider Renewal"}, "capacity": {}},
            {"start": "2026-08-03T10:00:00-04:00", "course": {"mapped_clean_title": "AHA HeartCode BLS"}, "capacity": {}},
        ]
        counts = apply_snapshot_to_sessions(sessions, snapshot)
        self.assertEqual(3, sessions[0]["registered_count"])
        self.assertEqual("student_rows_present", sessions[0]["enrollment_evidence"]["status"])
        self.assertEqual(0, sessions[1]["registered_count"])
        self.assertEqual("no_student_row_in_snapshot", sessions[1]["enrollment_evidence"]["status"])
        self.assertNotIn("registered_count", sessions[2])
        self.assertEqual(1, counts["covered_classes_without_students"])


if __name__ == "__main__":
    unittest.main()
