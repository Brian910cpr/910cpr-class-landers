from __future__ import annotations

import unittest
from datetime import date

from scripts import build_seed_appointment_url_preview as preview


class SeedAppointmentUrlPreviewTest(unittest.TestCase):
    def container(self) -> dict:
        return {
            "container_id": "shipyard_brian",
            "instructor_name": "Brian",
            "location_name": "Shipyard",
            "first_valid_date": "2026-06-21",
            "first_valid_appointmentDayId": 260670,
            "last_valid_date": "2026-06-30",
            "last_valid_appointmentDayId": 260679,
            "first_invalid_appointmentDayId": 260680,
            "status": "active",
            "priority": 100,
        }

    def test_computes_appointment_day_id_from_first_valid_date(self) -> None:
        self.assertEqual(
            260671,
            preview.compute_appointment_day_id(self.container(), date(2026, 6, 22)),
        )

    def test_builds_preview_url_for_valid_seed(self) -> None:
        seeds = {
            "seeds": [{
                "seed_id": "seed-1",
                "source_offer_id": "offer-1",
                "date": "2026-06-22",
                "start_time": "08:30",
                "course_id": "209806",
                "course_title": "AHA BLS Provider",
                "instructor_display_name": "Brian Ennis",
                "location": "Shipyard",
            }]
        }
        courses = {
            "courses": [{
                "course_id": "209806",
                "appointment_allowed": True,
                "appointment_container_required": True,
            }]
        }
        containers = {"containers": [self.container()]}

        records, stats = preview.build_preview_records(seeds, courses, containers)

        self.assertEqual(1, stats["urls_previewed"])
        self.assertEqual(260671, records[0]["appointmentDayId"])
        self.assertIn("appointmentDayId=260671", records[0]["appointment_url_preview"])
        self.assertIn("startTime=8%3A30%20AM", records[0]["appointment_url_preview"])
        self.assertIn("courseId=209806", records[0]["appointment_url_preview"])

    def test_url_uses_appointment_display_start_not_lock_window(self) -> None:
        seeds = {
            "seeds": [{
                "seed_id": "seed-1",
                "source_offer_id": "offer-1",
                "date": "2026-06-22",
                "start_time": "16:45",
                "appointment_display_start": "2026-06-22T17:00:00",
                "scheduler_consumption_start": "2026-06-22T17:00:00",
                "scheduler_consumption_end": "2026-06-22T19:45:00",
                "course_id": "209806",
                "course_title": "AHA BLS Provider",
                "instructor_display_name": "Brian Ennis",
                "location": "Shipyard",
            }]
        }
        courses = {"courses": [{"course_id": "209806", "appointment_allowed": True, "appointment_container_required": True}]}
        records, _stats = preview.build_preview_records(seeds, courses, {"containers": [self.container()]})

        self.assertIn("startTime=5%3A00%20PM", records[0]["appointment_url_preview"])
        self.assertEqual("2026-06-22T19:45:00", records[0]["scheduler_consumption_end"])

    def test_blocks_out_of_range_seed(self) -> None:
        seeds = {
            "seeds": [{
                "seed_id": "seed-1",
                "source_offer_id": "offer-1",
                "date": "2026-07-01",
                "start_time": "08:30",
                "course_id": "209806",
                "course_title": "AHA BLS Provider",
                "instructor_display_name": "Brian Ennis",
                "location": "Shipyard",
            }]
        }
        courses = {
            "courses": [{
                "course_id": "209806",
                "appointment_allowed": True,
                "appointment_container_required": True,
            }]
        }
        containers = {"containers": [self.container()]}

        records, stats = preview.build_preview_records(seeds, courses, containers)

        self.assertEqual(0, stats["urls_previewed"])
        self.assertEqual(1, stats["seeds_blocked"])
        self.assertEqual("date_after_owned_appointment_range", records[0]["blocking_reason"])


if __name__ == "__main__":
    unittest.main()
