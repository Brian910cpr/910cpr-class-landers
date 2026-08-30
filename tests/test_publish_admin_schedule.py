from __future__ import annotations

import unittest
from datetime import datetime

from scripts.publish_admin_schedule import build_admin_schedule


class PublishAdminScheduleTest(unittest.TestCase):
    def test_durable_little_leaps_is_projected_with_canonical_count(self) -> None:
        durable = {"available": True, "sessions": [{
            "id": "7d569e4f-a56c-4a60-9081-e66fe45ad4c2",
            "external_session_id": "little-leaps-2026-09-19",
            "course_name": "AHA Heartsaver Pediatric First Aid CPR AED",
            "start_at": "2026-09-19T11:00:00-04:00",
            "end_at": "2026-09-19T14:00:00-04:00",
            "location_name": "5226 S College Rd, Wilmington",
            "registered_count": 5,
            "provenance": "gmail_confirmed",
        }]}
        result = build_admin_schedule({"sessions": []}, now=datetime.fromisoformat("2026-08-30T08:00:00-04:00"), durable_snapshot=durable)
        row = result["sessions"][0]
        self.assertEqual("2026-09-19T11:00:00-04:00", row["start_at"])
        self.assertEqual(5, row["registered_count"])
        self.assertTrue(row["durable_session"])
        self.assertEqual(1, result["counts"]["durable_sessions_projected"])

    def test_duplicate_external_session_enriches_durable_record_once(self) -> None:
        payload = {"sessions": [{"session_id": "ew-123", "start_at": "2026-09-19T11:00:00-04:00", "course_name": "AHA Heartsaver Pediatric First Aid CPR AED", "location_name": "5226 S College Rd, Wilmington", "registration_url": "https://example.test/register"}]}
        durable = {"available": True, "sessions": [{"id": "durable-1", "external_session_id": "ew-123", "start_at": "2026-09-19T11:00:00-04:00", "course_name": "AHA Heartsaver Pediatric First Aid CPR AED", "location_name": "5226 S College Rd, Wilmington", "registered_count": 5}]}
        result = build_admin_schedule(payload, now=datetime.fromisoformat("2026-08-30T08:00:00-04:00"), durable_snapshot=durable)
        self.assertEqual(1, len(result["sessions"]))
        self.assertEqual("https://example.test/register", result["sessions"][0]["registration_url"])
        self.assertEqual(5, result["sessions"][0]["registered_count"])

    def test_missing_enrollware_count_remains_unavailable_not_zero(self) -> None:
        payload = {"sessions": [{"session_id": "ew-unknown", "start_at": "2026-08-03T10:00:00-04:00"}]}
        row = build_admin_schedule(payload, now=datetime.fromisoformat("2026-07-18T08:00:00-04:00"))["sessions"][0]
        self.assertIsNone(row["registered_count"])
        self.assertFalse(row["participant_count_available"])

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
