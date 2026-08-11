from __future__ import annotations

import unittest
from datetime import date, datetime, time

from scripts.public_offer_capacity_health import (
    build_health,
    capacity_period,
    merge_intervals,
    session_inventory,
    summarize_sessions,
)


class PublicOfferCapacityHealthTests(unittest.TestCase):
    def test_overlapping_course_alternatives_count_unique_physical_time(self):
        availability = [{
            "availability_status": "available",
            "start_datetime": "2026-08-13T08:00:00",
            "end_datetime": "2026-08-13T10:00:00",
            "instructor_name": "Brian Ennis",
            "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
        }]
        offers = [{
            "offers": [
                {
                    "date": "2026-08-13", "startTime": "08:00", "durationMinutes": 120,
                    "courseId": course_id, "publicSelectable": True,
                    "instructor": "Brian Ennis", "location": ":: Wilmington; Shipyard Blvd",
                }
                for course_id in ("209806", "210549", "359474")
            ]
        }]
        result = capacity_period(availability, offers, date(2026, 8, 13), date(2026, 8, 13), time(8), time(20))
        self.assertEqual(120, result["usable_minutes"])
        self.assertEqual(120, result["exposed_minutes"])
        self.assertEqual(100.0, result["capacity_exposed_percent"])
        self.assertEqual(1, len(result["usable_windows"]))
        self.assertEqual(1, len(result["exposed_windows"]))

    def test_candidate_starts_collapse_to_one_inventory_window(self):
        payload = {"offers": [
            {
                "date": "2026-08-13", "startTime": start, "durationMinutes": 60,
                "courseId": course_id, "publicSelectable": True,
                "availabilityBlockId": "gap-1", "instructor": "Brian", "location": "Shipyard",
            }
            for start in ("08:00", "08:30", "09:00")
            for course_id in ("210549", "359474")
        ]}
        sessions = session_inventory([payload], {"sessions": []}, date(2026, 8, 13))
        self.assertEqual(1, len(sessions))
        self.assertEqual(3, sessions[0]["candidate_start_count"])
        self.assertEqual(2, sessions[0]["course_alternative_count"])

    def test_origin_counts_conserve_total(self):
        rows = [
            {"date": "2026-08-13", "origin": origin, "session_key": str(index), "start": "", "end": ""}
            for index, origin in enumerate(("ANCHOR", "ANCHOR", "BARNACLE", "MANUAL"))
        ]
        summary = summarize_sessions(rows, date(2026, 8, 1), date(2026, 8, 31))
        self.assertEqual(4, summary["total"])
        self.assertEqual(summary["total"], summary["anchor"] + summary["barnacle"] + summary["manual"])
        self.assertTrue(summary["origin_conservation_ok"])

    def test_interval_merge_handles_touching_and_overlapping_ranges(self):
        intervals = [
            (datetime(2026, 8, 13, 8), datetime(2026, 8, 13, 9)),
            (datetime(2026, 8, 13, 8, 30), datetime(2026, 8, 13, 10)),
            (datetime(2026, 8, 13, 10), datetime(2026, 8, 13, 11)),
        ]
        self.assertEqual([(datetime(2026, 8, 13, 8), datetime(2026, 8, 13, 11))], merge_intervals(intervals))

    def test_remainder_of_august_includes_as_of_day_through_month_end(self):
        health = build_health(
            selector_payloads=[],
            schedule_future={"sessions": []},
            live_availability={"generated_at": "2026-08-11T13:00:00-04:00", "availability_blocks": []},
            public_offer_policy={"dynamic_public_start_time_window": {"earliest_start": "08:00", "latest_start": "19:00"}},
        )
        remainder = health["inventory"]["remainder"]
        self.assertEqual("2026-08-11", remainder["period_start"])
        self.assertEqual("2026-08-31", remainder["period_end"])
        self.assertEqual(21, remainder["calendar_days_remaining"])

    def test_uncovered_usable_time_is_auditable_hidden_capacity(self):
        availability = [{
            "availability_status": "available",
            "start_datetime": "2026-08-13T08:00:00",
            "end_datetime": "2026-08-13T10:00:00",
            "instructor_name": "Brian Ennis",
            "location_name": "Shipyard",
        }]
        offers = [{"offers": [{
            "date": "2026-08-13", "startTime": "08:00", "durationMinutes": 60,
            "courseId": "210549", "publicSelectable": True,
            "instructor": "Brian Ennis", "location": "Shipyard",
        }]}]
        result = capacity_period(availability, offers, date(2026, 8, 13), date(2026, 8, 13), time(8), time(20))
        self.assertEqual(60, result["hidden_minutes"])
        self.assertEqual("09:00", result["hidden_windows"][0]["start"])
        self.assertEqual("10:00", result["hidden_windows"][0]["end"])


if __name__ == "__main__":
    unittest.main()
