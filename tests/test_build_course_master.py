from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_course_master


class BuildCourseMasterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build_course_master.run()
        cls.master = json.loads(build_course_master.COURSE_MASTER_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(build_course_master.COURSE_MASTER_SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.report = json.loads(build_course_master.REPORT_JSON_PATH.read_text(encoding="utf-8"))

    def test_every_course_has_exact_schema_field_set(self) -> None:
        expected = set(build_course_master.COURSE_FIELDS)
        for course in self.master["courses"]:
            self.assertEqual(expected, set(course.keys()), course.get("enrollware_course_id"))

    def test_no_course_has_silent_missing_keys(self) -> None:
        for course in self.master["courses"]:
            self.assertIn("missing_required_fields", course)
            self.assertIsInstance(course["missing_required_fields"], list)
            self.assertIn(course["data_quality_status"], {"complete", "needs_review", "incomplete", "inactive"})

    def test_public_sellable_offer_courses_resolve_to_course_master(self) -> None:
        public_payload = json.loads(build_course_master.PUBLIC_SELLABLE_PATH.read_text(encoding="utf-8"))
        public_course_ids = {
            str(offer.get("course_id"))
            for offer in public_payload.get("offers", [])
            if isinstance(offer, dict)
        }
        master_ids = {course["enrollware_course_id"] for course in self.master["courses"]}
        self.assertTrue(public_course_ids)
        self.assertTrue(public_course_ids.issubset(master_ids))
        self.assertTrue(self.report["audit_answers"]["every_public_sellable_dynamic_offer_resolves_to_course_master"])

    def test_dynamic_eligible_course_missing_scheduler_data_is_blocked_for_review(self) -> None:
        for course in self.master["courses"]:
            missing_scheduler = any(
                course[field] is None
                for field in [
                    "classroom_duration_minutes",
                    "setup_buffer_minutes",
                    "cleanup_buffer_minutes",
                    "scheduler_consumption_minutes",
                ]
            )
            if missing_scheduler:
                self.assertFalse(course["dynamic_offer_allowed"], course["enrollware_course_id"])
                self.assertIn(course["data_quality_status"], {"needs_review", "incomplete", "inactive"})

    def test_renderable_public_course_has_mapping_or_is_not_public_complete(self) -> None:
        for course in self.master["courses"]:
            mapped = bool(course["slug_page"] != "unknown" and course["hub_tab"])
            if course["public_visibility"] == "active_public" and course["data_quality_status"] == "complete":
                self.assertTrue(mapped, course["enrollware_course_id"])

    def test_recommendation_keeps_course_catalog_as_preferred_seed_not_competing_truth(self) -> None:
        recommendation = self.report["recommendation"]
        self.assertFalse(recommendation["course_catalog_should_be_promoted_or_renamed"])
        self.assertTrue(recommendation["course_master_should_be_generated_from_course_catalog_plus_enrollware_export"])
        self.assertFalse(recommendation["course_catalog_should_remain_legacy_source_input_only"])


if __name__ == "__main__":
    unittest.main()
