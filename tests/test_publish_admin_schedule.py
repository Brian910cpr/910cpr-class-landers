from __future__ import annotations

import json
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import publish_admin_schedule
from scripts.publish_admin_schedule import build_admin_schedule, find_schedule_conflicts


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

    def test_blocks_august_5_shared_room_overlap_even_when_instructor_is_missing(self) -> None:
        rows = [
            {
                "session_id": "13869457",
                "course_name": "AHA HeartCode BLS",
                "start_at": "2026-08-05T12:30:00-04:00",
                "end_at": "2026-08-05T13:15:00-04:00",
                "lead_instructor_name": "Brian Ennis",
                "location_name": "NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office",
            },
            {
                "session_id": "13818252",
                "course_name": "AHA HeartCode BLS",
                "start_at": "2026-08-05T13:00:00-04:00",
                "end_at": "2026-08-05T14:00:00-04:00",
                "lead_instructor_name": None,
                "location_name": "NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office",
            },
        ]

        normalized = [row for row in (build_admin_schedule({"sessions": rows}, now=datetime.fromisoformat("2026-08-01T08:00:00-04:00"))["sessions"])]
        conflicts = find_schedule_conflicts(normalized)

        self.assertEqual(1, len(conflicts))
        self.assertEqual("shared_resource_overlap", conflicts[0]["type"])
        self.assertEqual(["13869457", "13818252"], conflicts[0]["session_ids"])
        self.assertTrue(any(resource.startswith("location:") for resource in conflicts[0]["shared_resources"]))

    def test_reports_invalid_or_missing_end_time(self) -> None:
        conflicts = find_schedule_conflicts([
            {
                "session_id": "bad-end",
                "start_at": "2026-08-05T13:00:00-04:00",
                "end_at": "2026-08-05T12:30:00-04:00",
                "blocking_resources": ["location:room b"],
            }
        ])

        self.assertEqual("invalid_time_range", conflicts[0]["type"])

    def test_main_preserves_last_known_good_output_when_conflicted(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            sessions_path = temp / "sessions.json"
            output_path = temp / "admin_schedule.json"
            snapshot_path = temp / "missing_snapshot.json"
            sessions_path.write_text(json.dumps({"sessions": [
                {
                    "session_id": "first",
                    "start_at": "2099-08-05T12:30:00-04:00",
                    "end_at": "2099-08-05T13:15:00-04:00",
                    "location_name": "Room B",
                },
                {
                    "session_id": "second",
                    "start_at": "2099-08-05T13:00:00-04:00",
                    "end_at": "2099-08-05T14:00:00-04:00",
                    "location_name": "Room B",
                },
            ]}), encoding="utf-8")
            output_path.write_text("last-known-good\n", encoding="utf-8")

            with (
                patch.object(publish_admin_schedule, "SESSIONS_CURRENT", sessions_path),
                patch.object(publish_admin_schedule, "OUTPUT", output_path),
                patch.object(publish_admin_schedule, "STUDENT_SNAPSHOT", snapshot_path),
            ):
                result = publish_admin_schedule.main()

            self.assertEqual(1, result)
            self.assertEqual("last-known-good\n", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
