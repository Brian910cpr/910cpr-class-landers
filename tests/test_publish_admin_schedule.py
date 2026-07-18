from __future__ import annotations

import unittest
from datetime import datetime

from scripts.publish_admin_schedule import build_admin_schedule


class PublishAdminScheduleTest(unittest.TestCase):
    def test_includes_shipyard_and_offsite_brian_classes_as_resource_blocks(self) -> None:
        payload = {
            "sessions": [
                {
                    "session_id": "13782393",
                    "timing": {"start_at": "2026-08-03T10:00:00-04:00", "end_at": "2026-08-03T11:00:00-04:00"},
                    "course": {"course_name_primary_clean": "AHA BLS HeartCode"},
                    "location": {"location_display": ":: Wilmington; Shipyard Blvd - B"},
                    "staffing": {"lead_instructor_name": "Brian Ennis"},
                },
                {
                    "session_id": "13613957",
                    "timing": {"start_at": "2026-08-16T14:00:00-04:00", "end_at": "2026-08-16T16:00:00-04:00"},
                    "course": {"course_name_primary_clean": "Family & Friends CPR"},
                    "location": {"location_display": "Freya's Haus"},
                    "staffing": {"lead_instructor_name": "Brian Ennis"},
                },
            ]
        }

        result = build_admin_schedule(payload, now=datetime.fromisoformat("2026-07-18T08:00:00-04:00"))

        self.assertEqual(2, result["counts"]["sessions"])
        self.assertEqual(2, result["counts"]["brian_resource_blocks"])
        self.assertTrue(all("instructor:brian_ennis" in row["blocking_resources"] for row in result["sessions"]))
        self.assertEqual({"13782393", "13613957"}, {row["session_id"] for row in result["sessions"]})


if __name__ == "__main__":
    unittest.main()
