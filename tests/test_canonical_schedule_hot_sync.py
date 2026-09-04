from __future__ import annotations

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from scripts.publish_admin_schedule import build_admin_schedule
from scripts.publish_landerware_ical import build_ical


class CanonicalScheduleHotSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 8, 23, 12, 0, tzinfo=ZoneInfo("America/New_York"))
        self.enrollware = {
            "sessions": [
                {
                    "session_id": "ew-1",
                    "source": "enrollware_ical",
                    "start": "2026-09-08T13:00:00-04:00",
                    "end": "2026-09-08T15:00:00-04:00",
                    "mapped_clean_title": "AHA BLS Provider",
                    "lead_instructor_name": "Brian Ennis",
                    "location_name": "Shipyard Room B",
                }
            ]
        }

    def test_committed_hot_sync_class_is_merged(self) -> None:
        hot_sync = {
            "available": True,
            "records": [
                {
                    "id": "hs_polar",
                    "source": "hot_sync_manual",
                    "status": "committed",
                    "needs_class_report_absorption": True,
                    "course_display_name": "AHA Heartsaver First Aid CPR AED",
                    "start": "2026-09-08T09:30:00-04:00",
                    "end": "2026-09-08T12:00:00-04:00",
                    "client_name": "Polar Ice Wilmington",
                    "location_name": "Polar Ice Wilmington",
                    "instructor": "Brian Ennis",
                }
            ],
        }
        result = build_admin_schedule(self.enrollware, now=self.now, hot_sync_snapshot=hot_sync)
        self.assertEqual(2, result["counts"]["sessions"])
        self.assertEqual(1, result["counts"]["hot_sync_sessions_added"])
        polar = next(row for row in result["sessions"] if row.get("session_id") == "hs_polar")
        self.assertTrue(polar["hot_sync"])
        self.assertEqual("2026-09-08T09:30:00-04:00", polar["start_at"])

    def test_cancelled_hot_sync_class_is_not_merged(self) -> None:
        hot_sync = {
            "available": True,
            "records": [
                {
                    "id": "hs_cancelled",
                    "status": "cancelled",
                    "needs_class_report_absorption": True,
                    "course_display_name": "AHA BLS Provider",
                    "start": "2026-09-08T09:30:00-04:00",
                    "end": "2026-09-08T11:30:00-04:00",
                    "location_name": "Polar Ice Wilmington",
                    "instructor": "Brian Ennis",
                }
            ],
        }
        result = build_admin_schedule(self.enrollware, now=self.now, hot_sync_snapshot=hot_sync)
        self.assertEqual(1, result["counts"]["sessions"])
        self.assertEqual(0, result["counts"]["hot_sync_sessions_added"])

    def test_scheduled_durable_sessions_reserve_september_19(self) -> None:
        hot_sync = {
            "available": True,
            "records": [
                {
                    "id": "6d685cdf-a5b3-4034-9ecd-e459305d30ba",
                    "source": "gmail_confirmed",
                    "status": "scheduled",
                    "course_name": "AHA BLS Provider",
                    "start_at": "2026-09-19T09:00:00-04:00",
                    "end_at": "2026-09-19T11:00:00-04:00",
                    "location_name": "Hendersonville Family Dental",
                    "lead_instructor_name": "Brian Ennis",
                },
                {
                    "id": "094cbbfa-fe0d-44e6-9ead-e7b2f636e332",
                    "source": "gmail_confirmed",
                    "status": "scheduled",
                    "course_name": "AHA Heartsaver Pediatric First Aid CPR AED",
                    "start_at": "2026-09-19T11:00:00-04:00",
                    "end_at": "2026-09-19T14:00:00-04:00",
                    "location_name": "Little Leaps",
                    "lead_instructor_name": "Brian Ennis",
                },
                {
                    "id": "cb6b0f5d-2397-4ffa-87ff-429d2a6da4e9",
                    "source": "gmail_confirmed",
                    "status": "cancelled",
                    "course_name": "AHA BLS Provider",
                    "start_at": "2026-09-19T14:00:00-04:00",
                    "end_at": "2026-09-19T16:00:00-04:00",
                    "location_name": "Hendersonville Family Dental",
                    "lead_instructor_name": "Brian Ennis",
                },
            ],
        }

        result = build_admin_schedule(self.enrollware, now=self.now, hot_sync_snapshot=hot_sync)

        durable = [row for row in result["sessions"] if row.get("hot_sync")]
        self.assertEqual(2, len(durable))
        self.assertEqual(
            {
                "6d685cdf-a5b3-4034-9ecd-e459305d30ba",
                "094cbbfa-fe0d-44e6-9ead-e7b2f636e332",
            },
            {row["session_id"] for row in durable},
        )
        self.assertTrue(
            all("instructor:brian_ennis" in row["blocking_resources"] for row in durable)
        )

    def test_ical_contains_both_sources_with_stable_uids(self) -> None:
        payload = {
            "generated_at": "2026-08-23T12:00:00-04:00",
            "sessions": [
                {
                    "session_id": "ew-1",
                    "source": "enrollware_ical",
                    "course_name": "AHA BLS Provider",
                    "start_at": "2026-09-08T13:00:00-04:00",
                    "end_at": "2026-09-08T15:00:00-04:00",
                    "location_name": "Shipyard Room B",
                },
                {
                    "session_id": "hs_polar",
                    "source": "hot_sync_manual",
                    "hot_sync": True,
                    "course_name": "AHA Heartsaver First Aid CPR AED",
                    "start_at": "2026-09-08T09:30:00-04:00",
                    "end_at": "2026-09-08T12:00:00-04:00",
                    "location_name": "Polar Ice Wilmington",
                },
            ],
        }
        text = build_ical(payload)
        self.assertEqual(2, text.count("BEGIN:VEVENT"))
        self.assertIn("UID:enrollware_ical-ew-1@landerware.910cpr.com", text)
        self.assertIn("UID:hot_sync_manual-hs_polar@landerware.910cpr.com", text)
        self.assertIn("DTSTART:20260908T133000Z", text)
        self.assertIn("LOCATION:Polar Ice Wilmington", text)


if __name__ == "__main__":
    unittest.main()
