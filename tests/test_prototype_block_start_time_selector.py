import json
import unittest
from pathlib import Path

from scripts import prototype_block_start_time_selector as prototype

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_REPORT_PATH = ROOT / "data" / "audit" / "block_start_time_prototype_report.json"


class BlockStartTimePrototypeTests(unittest.TestCase):
    def test_real_course_rules_are_required_and_loaded(self):
        courses = prototype.load_course_rules()

        self.assertGreater(len(courses), 0)
        self.assertTrue(all(course["courseId"] for course in courses))
        self.assertTrue(any(course["appointmentEligible"] for course in courses))

    def test_existing_url_builder_parameter_shape_is_used(self):
        url = prototype.build_registration_url(260671, prototype.time(8, 30), "209806")

        self.assertIn("appointmentDayId=260671", url)
        self.assertIn("startTime=8%3A30%20AM", url)
        self.assertIn("courseId=209806", url)

    def test_prototype_generates_start_rows_without_presenting_block_as_class(self):
        result = json.loads(PROTOTYPE_REPORT_PATH.read_text(encoding="utf-8"))

        self.assertFalse(result["counts"]["wholeBlockPresentedAsClass"])
        self.assertFalse(result["proof"]["wholeBlockPresentedAsClass"])
        self.assertGreater(result["counts"]["startTimesGenerated"], 1)
        self.assertGreater(result["counts"]["fitEligibleCourseStartTimeOffers"], 0)

    def test_next_public_eligible_mode_uses_selected_availability_source(self):
        result = json.loads(PROTOTYPE_REPORT_PATH.read_text(encoding="utf-8"))

        self.assertEqual("live_availability_snapshot", result["availability_source_used"])
        self.assertFalse(result["availability_fallback_used"])
        self.assertGreater(result["counts"]["publicSelectableCourseStartTimeOffers"], 0)


if __name__ == "__main__":
    unittest.main()
