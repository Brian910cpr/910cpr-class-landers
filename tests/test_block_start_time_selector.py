from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scripts import build_bls_block_schedule_pilot
from scripts import block_start_time_selector

ROOT = Path(__file__).resolve().parents[1]
PILOT_REPORT_PATH = ROOT / "data" / "audit" / "bls_block_schedule_pilot.json"


class BlockStartTimeSelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(PILOT_REPORT_PATH.read_text(encoding="utf-8"))

    def test_uses_live_availability_when_present(self):
        self.assertEqual(self.payload["availability_source_used"], "live_availability_snapshot")
        self.assertFalse(self.payload["availability_fallback_used"])

    def test_generates_public_selectable_bls_offers(self):
        self.assertGreater(self.payload["counts"]["publicSelectableOfferCount"], 0)
        course_ids = {offer["courseId"] for offer in self.payload["offers"]}
        self.assertTrue(course_ids)
        self.assertLessEqual(course_ids, set(block_start_time_selector.BLS_PILOT_COURSE_IDS))

    def test_public_starts_are_inside_business_hours(self):
        for offer in self.payload["offers"]:
            hour, minute = [int(part) for part in offer["startTime"].split(":")]
            self.assertGreaterEqual((hour, minute), (8, 0))
            self.assertLessEqual((hour, minute), (19, 0))
            self.assertNotEqual(offer["startTime"], "00:00")

    def test_appointment_urls_include_required_query_params(self):
        for offer in self.payload["offers"][:25]:
            parsed = urlparse(offer["appointmentUrl"])
            query = parse_qs(parsed.query)
            self.assertEqual(parsed.scheme, "https")
            self.assertEqual(parsed.netloc, "coastalcprtraining.enrollware.com")
            self.assertIn("appointmentDayId", query)
            self.assertIn("startTime", query)
            self.assertEqual(query.get("courseId"), [offer["courseId"]])

    def test_whole_block_is_not_presented_as_class(self):
        self.assertFalse(self.payload["whole_block_presented_as_class"])
        self.assertFalse(self.payload["counts"]["wholeBlockPresentedAsClass"])
        visible_labels = set(self.payload["proof"]["visibleStartLabels"])
        for window in self.payload["proof"]["availabilityWindowsThatGeneratedOffers"]:
            self.assertNotIn(window, visible_labels)

    def test_rendered_html_has_register_links_but_not_block_class_label(self):
        html = build_bls_block_schedule_pilot.render_html(self.payload)
        self.assertIn("BLS Schedule Pilot", html)
        self.assertIn("Register", html)
        self.assertIn("appointmentDayId", html)
        self.assertIn("Need BLS ASAP? Show all AHA BLS options", html)
        self.assertIn("const courseOptions =", html)
        self.assertIn("const optionGroups =", html)
        self.assertIn("let compareMode = false", html)
        self.assertIn("function activeCourseIds()", html)
        self.assertNotIn("12:00 AM-6:00 PM", html)
        self.assertNotIn("12:00 AM\u20136:00 PM", html)
        self.assertNotIn("Calendy", html)
        self.assertNotIn("shotgun", html.lower())

    def test_compare_mode_data_model_groups_bls_family_generically(self):
        html = build_bls_block_schedule_pilot.render_html(self.payload)
        self.assertIn('"family": "BLS"', html)
        self.assertIn('"209806"', html)
        self.assertIn('"359474"', html)
        self.assertIn('"210549"', html)
        self.assertIn("optionGroups[selected.family]?.courseIds", html)


if __name__ == "__main__":
    unittest.main()
