from datetime import datetime
import unittest

from scripts.publish_scheduling_landscape import operational_lane_cells, quarter_hour_cells
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SchedulingLandscapeOperationalLanesTest(unittest.TestCase):
    def test_portrait_details_panel_and_delayed_hover_contract(self):
        html = (ROOT / "docs" / "admin" / "scheduling-landscape.html").read_text(encoding="utf-8")
        script = (ROOT / "docs" / "admin" / "scheduling-landscape-lanes.js").read_text(encoding="utf-8")
        self.assertIn(".site-theme-toggle{display:none!important}", html)
        self.assertIn(".drawer{position:static", html)
        self.assertIn("setTimeout(() => cell.click(), 650)", script)
        self.assertIn('matrix.addEventListener("pointerout"', script)
        self.assertIn('document.documentElement.dataset.theme = "light"', script)

    def test_partial_intervals_fill_each_overlapping_quarter_hour(self):
        self.assertEqual(
            [("2026-08-25", "09:00"), ("2026-08-25", "09:15")],
            quarter_hour_cells(datetime.fromisoformat("2026-08-25T09:07:00-04:00"), datetime.fromisoformat("2026-08-25T09:22:00-04:00")),
        )

    def test_builds_enrollware_source_and_brian_unavailability_lanes(self):
        schedule = {"build": {"source_mode": "enrollware_ical_authoritative"}, "sessions": [{
            "session_id": "13946813", "course_name": "BLS Renewal",
            "start_at": "2026-08-25T09:15:00-04:00", "end_at": "2026-08-25T11:15:00-04:00",
        }]}
        availability = {"events": [{
            "instructor_key": "brian", "source_key": "brian_do_not_schedule", "title": "Unavailable",
            "start": "2026-08-25T13:00:00-04:00", "end": "2026-08-25T14:00:00-04:00",
        }]}
        cells = operational_lane_cells(schedule, availability)
        enrollware = [cell for cell in cells if cell["laneId"] == "enrollware"]
        brian = [cell for cell in cells if cell["laneId"] == "brian"]
        self.assertEqual(8, len(enrollware))
        self.assertTrue(all(cell["result"] == "enrollware-ical" for cell in enrollware))
        self.assertEqual(4, len(brian))
        self.assertTrue(all(cell["result"] == "unavailable" for cell in brian))
        self.assertNotIn("location", brian[0]["items"][0])
        self.assertEqual("Unavailable", brian[0]["items"][0]["title"])


if __name__ == "__main__":
    unittest.main()
