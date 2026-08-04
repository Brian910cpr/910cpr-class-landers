import json
import re
import unittest
from pathlib import Path

from scripts.dockmaster import dockmaster_comment

ROOT = Path(__file__).resolve().parents[1]
SELECTORS = ("bls", "acls", "pals", "heartsaver", "arc", "hsi")
ANCHOR_IDS = ("13833211", "13818252", "13787687")


class AnchorCalendarAndLanderTests(unittest.TestCase):
    def test_selector_source_has_48_segment_timeline_and_no_availability_dot(self):
        source = (ROOT / "scripts/build_bls_block_schedule_pilot.py").read_text(encoding="utf-8")
        self.assertIn("length: 48", source)
        self.assertIn("grid-template-columns: repeat(48", source)
        self.assertNotIn("availability-dot", source)

    def test_deployed_selectors_have_anchor_visual_states(self):
        for page in SELECTORS:
            html = (ROOT / "docs" / f"{page}.html").read_text(encoding="utf-8")
            self.assertIn("day-timeline-segment", html, page)
            self.assertIn("is-anchor", html, page)
            self.assertIn("is-barnacle", html, page)
            self.assertIn("is-available", html, page)
            self.assertIn("register-panel", html, page)
            self.assertIn("★", html, page)
            self.assertNotIn("availability-dot", html, page)

    def test_bls_feed_has_three_anchors_and_at_most_one_position_per_direction(self):
        payload = json.loads((ROOT / "docs/data/block-selector-availability/bls.json").read_text(encoding="utf-8"))
        courses = [course for day in payload["dates"] for slot in day["startTimes"] for course in slot["courses"]]
        anchors = [course for course in courses if course.get("schedule_role") == "anchor"]
        self.assertEqual(len(anchors), 3)
        positions = {}
        for course in courses:
            if course.get("schedule_role") != "barnacle":
                continue
            key = (course["attached_to_session_id"], course["barnacle_direction"])
            positions.setdefault(key, set()).add((course["date"], course["startTime"]))
        self.assertTrue(positions)
        self.assertTrue(all(len(starts) == 1 for starts in positions.values()))

    def test_anchor_landers_are_branded_stable_and_direct(self):
        for session_id in ANCHOR_IDS:
            path = ROOT / "docs/classes" / f"{session_id}.html"
            html = path.read_text(encoding="utf-8")
            self.assertIn("⭐ Anchor Class", html)
            self.assertIn("Join us and train with others!", html)
            self.assertIn(f"https://coastalcprtraining.enrollware.com/enroll?id={session_id}", html)
            self.assertIn(f'https://www.910cpr.com/classes/{session_id}.html', html)
            self.assertRegex(html, r"Dockmaster’s Journal\s+Entry \d{4}")
            self.assertNotRegex(html, r"MedNorth|Cardio Partners|Breakthrough Autism")

    def test_dockmaster_comment_is_deterministic_valid_and_contains_no_pii(self):
        first = dockmaster_comment("session-123")
        self.assertEqual(first, dockmaster_comment("session-123"))
        self.assertTrue(first.startswith("<!--") and first.endswith("-->"))
        self.assertNotIn("--", first[4:-3])
        self.assertIsNone(re.search(r"[\w.+-]+@[\w.-]+|\b\d{3}-\d{3}-\d{4}\b|enroll\?id=", first, re.I))

    def test_selector_booking_urls_are_unmodified_enrollware_urls_and_locations_are_public(self):
        payload = json.loads((ROOT / "docs/data/block-selector-availability/bls.json").read_text(encoding="utf-8"))
        courses = [course for day in payload["dates"] for slot in day["startTimes"] for course in slot["courses"]]
        self.assertTrue(courses)
        for course in courses:
            url = course.get("appointmentUrl", "")
            self.assertRegex(url, r"^https://coastalcprtraining\.enrollware\.com/enroll\?(?:appointmentDayId=\d+&startTime=[^&]+&courseId=\d+|id=\d+)$")
            self.assertNotRegex(str(course.get("location", "")), r"MedNorth|Cardio Partners|Breakthrough Autism")


if __name__ == "__main__":
    unittest.main()
