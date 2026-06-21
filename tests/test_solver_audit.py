from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import solver_audit


class SolverAuditTest(unittest.TestCase):
    def test_instructor_qualification_status_distinguishes_match_unknown_and_missing(self) -> None:
        course = {
            "course_id": "209806",
            "official_title": "AHA BLS Provider",
            "required_instructor_certifications": ["AHA_BLS_INSTRUCTOR"],
        }
        rule = {
            "course_id": "209806",
            "required_instructor_certifications": ["AHA_BLS_INSTRUCTOR"],
        }
        catalog = {
            "instructors": [
                {
                    "instructor_id": "known",
                    "display_name": "Known",
                    "certifications": [{"certification_code": "AHA_BLS_INSTRUCTOR"}],
                },
                {
                    "instructor_id": "unknown",
                    "display_name": "Unknown",
                    "certifications": [{"certification_code": solver_audit.UNKNOWN}],
                },
            ]
        }
        lookup = solver_audit.instructor_lookup(catalog)

        self.assertEqual(
            "matched",
            solver_audit.instructor_qualification_status(course, rule, "Known", lookup)["status"],
        )
        self.assertEqual(
            "unknown",
            solver_audit.instructor_qualification_status(course, rule, "Unknown", lookup)["status"],
        )
        self.assertEqual(
            "missing",
            solver_audit.instructor_qualification_status(course, rule, "Missing", lookup)["status"],
        )

    def test_people_catalog_bridge_matches_availability_instructor_without_scheduler_enablement(self) -> None:
        course = {
            "course_id": "209806",
            "official_title": "AHA BLS Provider",
            "required_instructor_certifications": ["AHA_BLS_INSTRUCTOR"],
        }
        rule = {
            "course_id": "209806",
            "required_instructor_certifications": ["AHA_BLS_INSTRUCTOR"],
        }
        people = {
            "people": [
                {
                    "person_id": "person_brian",
                    "display_name": "Brian Ennis",
                    "assignment_mode": "ON_REQUEST",
                    "dynamic_offer_eligible": False,
                    "certifications": [{"certification_code": "AHA_BLS_INSTRUCTOR"}],
                }
            ]
        }
        status = solver_audit.instructor_qualification_status(
            course,
            rule,
            "Brian",
            {},
            solver_audit.people_lookup(people),
            allow_availability_person_bridge=True,
        )

        self.assertEqual("matched", status["status"])
        self.assertEqual("people_catalog", status["qualification_source"])
        self.assertFalse(status["scheduler_enabled"])
        self.assertTrue(status["availability_bridge_used"])

    def test_people_scheduler_enabled_requires_dynamic_offer_and_primary_or_secondary(self) -> None:
        self.assertTrue(
            solver_audit.person_scheduler_enabled({
                "assignment_mode": "PRIMARY",
                "dynamic_offer_eligible": True,
            })
        )
        self.assertTrue(
            solver_audit.person_scheduler_enabled({
                "assignment_mode": "SECONDARY",
                "dynamic_offer_eligible": True,
            })
        )
        self.assertFalse(
            solver_audit.person_scheduler_enabled({
                "assignment_mode": "SUBCONTRACTOR",
                "dynamic_offer_eligible": True,
            })
        )
        self.assertFalse(
            solver_audit.person_scheduler_enabled({
                "assignment_mode": "PRIMARY",
                "dynamic_offer_eligible": False,
            })
        )

    def test_missing_optional_inputs_do_not_crash_and_outputs_are_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit_dir = root / "data" / "audit"
            missing_dir = root / "missing"

            original_input_paths = solver_audit.INPUT_PATHS
            original_summary = solver_audit.SUMMARY_PATH
            original_candidates = solver_audit.CANDIDATES_PATH
            original_rejections = solver_audit.REJECTIONS_PATH
            original_report = solver_audit.REPORT_PATH
            original_audit_dir = solver_audit.AUDIT_DIR

            try:
                solver_audit.AUDIT_DIR = audit_dir
                solver_audit.SUMMARY_PATH = audit_dir / "solver_audit_summary.json"
                solver_audit.CANDIDATES_PATH = audit_dir / "solver_audit_candidates.json"
                solver_audit.REJECTIONS_PATH = audit_dir / "solver_audit_rejections.json"
                solver_audit.REPORT_PATH = audit_dir / "solver_audit_report.md"
                solver_audit.INPUT_PATHS = {
                    name: missing_dir / f"{name}.json"
                    for name in original_input_paths
                }

                result = solver_audit.run_audit()

                self.assertEqual([], result["files_read"])
                self.assertEqual(0, result["candidate_count"])
                self.assertEqual(0, result["rejection_count"])

                written = sorted(path.relative_to(root).as_posix() for path in audit_dir.glob("solver_audit_*"))
                self.assertEqual(
                    [
                        "data/audit/solver_audit_candidates.json",
                        "data/audit/solver_audit_rejections.json",
                        "data/audit/solver_audit_report.md",
                        "data/audit/solver_audit_summary.json",
                    ],
                    written,
                )
            finally:
                solver_audit.INPUT_PATHS = original_input_paths
                solver_audit.SUMMARY_PATH = original_summary
                solver_audit.CANDIDATES_PATH = original_candidates
                solver_audit.REJECTIONS_PATH = original_rejections
                solver_audit.REPORT_PATH = original_report
                solver_audit.AUDIT_DIR = original_audit_dir


if __name__ == "__main__":
    unittest.main()
