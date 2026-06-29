from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from scripts import build_live_availability_snapshot as snapshot
from scripts import export_calendar_snapshots as exporter


class LiveAvailabilitySnapshotTest(unittest.TestCase):
    def test_missing_local_snapshot_creates_placeholder_blocked_source(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "amy_availability",
                "owner_instructor_key": "amy",
                "mode": "explicit_availability",
                "default_location_key": "shipyard",
            }]
        }
        people_payload = {
            "people": [{
                "person_id": "amy",
                "display_name": "Amy Arnold",
                "email": "amy@example.com",
            }]
        }

        blocks, blocked, stats = snapshot.build_snapshot(calendar_payload, people_payload, {"courses": []}, {})

        self.assertEqual([], blocks)
        self.assertEqual(1, len(blocked))
        self.assertEqual("local_calendar_snapshot_missing", blocked[0]["reason_code"])
        self.assertEqual(1, stats["configured_calendar_sources_found"])

    def test_normalizes_offerable_event_block(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "amy_availability",
                "owner_instructor_key": "amy",
                "mode": "explicit_availability",
                "default_location_key": "shipyard",
            }]
        }
        people_payload = {
            "people": [{
                "person_id": "amy",
                "display_name": "Amy Arnold",
                "email": "amy@example.com",
                "certifications": [{"certification_code": "AHA_BLS_INSTRUCTOR"}],
            }]
        }
        course_payload = {
            "courses": [{
                "course_id": "209806",
                "family": "BLS",
                "required_instructor_certifications": ["AHA_BLS_INSTRUCTOR"],
            }]
        }
        local_snapshot = {
            "events_by_source": {
                "amy_availability": [{
                    "id": "evt1",
                    "summary": "HARD",
                    "start": "2026-06-22T08:30:00",
                    "end": "2026-06-22T12:00:00",
                }]
            }
        }

        blocks, blocked, _ = snapshot.build_snapshot(calendar_payload, people_payload, course_payload, local_snapshot)

        self.assertEqual([], blocked)
        self.assertEqual(1, len(blocks))
        self.assertEqual("available", blocks[0]["availability_status"])
        self.assertEqual("Amy Arnold", blocks[0]["instructor_name"])
        self.assertEqual(["BLS"], blocks[0]["allowed_course_families"])
        self.assertEqual("2026-06-22T08:30:00", blocks[0]["start_datetime"])
        self.assertEqual("2026-06-22T12:00:00", blocks[0]["end_datetime"])

    def test_snapshot_from_expanded_recurring_event_contains_august_blocks(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "amy_availability",
                "owner_instructor_key": "amy",
                "mode": "explicit_availability",
                "default_location_key": "shipyard",
            }]
        }
        people_payload = {
            "people": [{
                "person_id": "amy",
                "display_name": "Amy Arnold",
                "email": "amy@example.com",
                "certifications": [{"certification_code": "AHA_BLS_INSTRUCTOR"}],
            }]
        }
        course_payload = {
            "courses": [{
                "course_id": "209806",
                "family": "BLS",
                "required_instructor_certifications": ["AHA_BLS_INSTRUCTOR"],
            }]
        }
        ics_text = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:august-recurring
SUMMARY:HARD
DTSTART:20260727T090000
DTEND:20260727T120000
RRULE:FREQ=WEEKLY;COUNT=3;BYDAY=MO
LOCATION:Shipyard
END:VEVENT
END:VCALENDAR
"""
        events, _skipped = exporter.parse_ics_events(
            ics_text,
            {"calendar_source_key": "amy_availability", "mode": "explicit_availability"},
            snapshot.datetime(2026, 7, 1, 0, 0, 0),
            snapshot.datetime(2026, 8, 31, 0, 0, 0),
        )
        local_snapshot = {"events_by_source": {"amy_availability": events}}

        blocks, blocked, _stats = snapshot.build_snapshot(calendar_payload, people_payload, course_payload, local_snapshot)

        self.assertEqual([], blocked)
        self.assertTrue(any(block["date"].startswith("2026-08") for block in blocks))

    def test_timezone_aware_utc_event_converts_to_local_time(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "amy_availability",
                "owner_instructor_key": "amy",
                "mode": "explicit_availability",
                "default_location_key": "shipyard",
            }]
        }
        people_payload = {
            "people": [{
                "person_id": "amy",
                "display_name": "Amy Arnold",
                "email": "amy@example.com",
            }]
        }
        local_snapshot = {
            "events_by_source": {
                "amy_availability": [{
                    "id": "utc-event",
                    "summary": "HARD",
                    "start": "2026-06-26T18:00:00+00:00",
                    "end": "2026-06-26T22:00:00+00:00",
                }]
            }
        }

        blocks, blocked, _ = snapshot.build_snapshot(calendar_payload, people_payload, {"courses": []}, local_snapshot)

        self.assertEqual([], blocked)
        self.assertEqual(1, len(blocks))
        self.assertEqual("2026-06-26T14:00:00", blocks[0]["start_datetime"])
        self.assertEqual("2026-06-26T18:00:00", blocks[0]["end_datetime"])
        self.assertEqual("14:00", blocks[0]["start_time"])
        self.assertEqual("18:00", blocks[0]["end_time"])

    def test_inverse_blocking_empty_time_becomes_availability_inside_container(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "brian_inverse",
                "owner_instructor_key": "brian",
                "mode": "inverse_blocking",
                "availability_location_mode": "instructor_time_only",
                "default_location_key": "shipyard",
                "inverse_expansion_start_datetime": "2026-07-01T00:00:00",
                "inverse_expansion_horizon_days": 1,
                "inverse_expansion_min_gap_minutes": 90,
                "inverse_expansion_require_active_appointment_container": True,
            }]
        }
        people_payload = {
            "people": [{
                "person_id": "brian",
                "display_name": "Brian Ennis",
                "certifications": [{"certification_code": "AHA_BLS_INSTRUCTOR"}],
            }]
        }
        course_payload = {
            "courses": [{
                "course_id": "209806",
                "family": "BLS",
                "duration_minutes": 120,
                "appointment_allowed": True,
                "required_instructor_certifications": ["AHA_BLS_INSTRUCTOR"],
            }]
        }
        appointment_payload = {
            "containers": [{
                "container_id": "shipyard_brian",
                "instructor_name": "Brian",
                "first_valid_date": "2026-07-01",
                "last_valid_date": "2026-07-01",
                "status": "active",
            }]
        }
        local_snapshot = {"events_by_source": {"brian_inverse": []}}

        blocks, blocked, stats = snapshot.build_snapshot(calendar_payload, people_payload, course_payload, local_snapshot, appointment_payload)

        self.assertEqual([], blocked)
        available = [block for block in blocks if block["availability_status"] == "available"]
        self.assertEqual(1, len(available))
        self.assertTrue(available[0]["inverse_generated"])
        self.assertEqual("2026-07-01T00:00:00", available[0]["start_datetime"])
        self.assertEqual("2026-07-02T00:00:00", available[0]["end_datetime"])
        self.assertEqual("instructor_time_only", available[0]["availability_location_mode"])
        self.assertIn("inverse_blocking_gap_expansion", available[0]["reasons"])
        self.assertEqual(1, stats["inverse_generated_availability_blocks"])

    def test_inverse_blocking_events_subtract_from_default_open_windows(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "brian_inverse",
                "owner_instructor_key": "brian",
                "mode": "inverse_blocking",
                "default_location_key": "shipyard",
                "inverse_expansion_start_datetime": "2026-07-01T00:00:00",
                "inverse_expansion_horizon_days": 1,
                "inverse_expansion_min_gap_minutes": 90,
                "inverse_expansion_require_active_appointment_container": False,
            }]
        }
        local_snapshot = {
            "events_by_source": {
                "brian_inverse": [{
                    "id": "block1",
                    "summary": "ADR F/R Shift",
                    "start": "2026-07-01T10:00:00",
                    "end": "2026-07-01T12:00:00",
                }]
            }
        }

        blocks, blocked, stats = snapshot.build_snapshot(calendar_payload, {}, {"courses": []}, local_snapshot)

        self.assertEqual([], blocked)
        blocked_events = [block for block in blocks if block["availability_status"] == "blocked"]
        available = [block for block in blocks if block["availability_status"] == "available"]
        self.assertEqual(1, len(blocked_events))
        self.assertEqual("block1", blocked_events[0]["source_event_id"])
        self.assertEqual(["2026-07-01T00:00:00", "2026-07-01T12:00:00"], [block["start_datetime"] for block in available])
        self.assertEqual(["2026-07-01T10:00:00", "2026-07-02T00:00:00"], [block["end_datetime"] for block in available])
        self.assertEqual(2, stats["inverse_generated_availability_blocks"])
        self.assertEqual(1, stats["inverse_blocking_event_blocks"])

    def test_inverse_expansion_respects_appointment_container_coverage(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "brian_inverse",
                "owner_instructor_key": "brian",
                "mode": "inverse_blocking",
                "default_location_key": "shipyard",
                "inverse_expansion_start_datetime": "2026-07-01T00:00:00",
                "inverse_expansion_horizon_days": 5,
                "inverse_expansion_min_gap_minutes": 90,
                "inverse_expansion_require_active_appointment_container": True,
            }]
        }
        people_payload = {"people": [{"person_id": "brian", "display_name": "Brian Ennis"}]}
        appointment_payload = {
            "containers": [{
                "container_id": "shipyard_brian",
                "instructor_name": "Brian",
                "first_valid_date": "2026-07-03",
                "last_valid_date": "2026-07-03",
                "status": "active",
            }]
        }
        local_snapshot = {"events_by_source": {"brian_inverse": []}}

        blocks, blocked, _stats = snapshot.build_snapshot(calendar_payload, people_payload, {"courses": []}, local_snapshot, appointment_payload)

        self.assertEqual([], blocked)
        available_dates = sorted({block["date"] for block in blocks if block["availability_status"] == "available"})
        self.assertEqual(["2026-07-03"], available_dates)

    def test_dns_marker_becomes_blocked_block(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "brian_dns",
                "owner_instructor_key": "brian",
                "mode": "inverse_blocking",
                "inverse_expansion_start_datetime": "2026-06-22T00:00:00",
                "inverse_expansion_horizon_days": 1,
                "inverse_expansion_require_active_appointment_container": False,
            }]
        }
        local_snapshot = {
            "events_by_source": {
                "brian_dns": [{
                    "id": "dns1",
                    "summary": "DNS - personal",
                    "start": "2026-06-22T08:30:00",
                    "end": "2026-06-22T09:30:00",
                }]
            }
        }

        blocks, _blocked, stats = snapshot.build_snapshot(calendar_payload, {}, {}, local_snapshot)

        blocked_blocks = [block for block in blocks if block["availability_status"] == "blocked"]
        self.assertEqual(1, len(blocked_blocks))
        self.assertEqual("dns1", blocked_blocks[0]["source_event_id"])
        self.assertEqual(1, stats["dns_markers_found"])

    def test_zero_length_event_is_invalid_time_range_not_offerable(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "brian_inverse",
                "owner_instructor_key": "brian",
                "mode": "inverse_blocking",
                "default_location_key": "shipyard",
                "inverse_expansion_start_datetime": "2026-07-04T00:00:00",
                "inverse_expansion_horizon_days": 1,
                "inverse_expansion_require_active_appointment_container": False,
            }]
        }
        local_snapshot = {
            "events_by_source": {
                "brian_inverse": [{
                    "id": "zero1",
                    "summary": "Available",
                    "start": "2026-07-04T00:00:00",
                    "end": "2026-07-04T00:00:00",
                }]
            }
        }

        _blocks, blocked, stats = snapshot.build_snapshot(calendar_payload, {}, {}, local_snapshot)

        self.assertEqual(1, len(blocked))
        self.assertEqual("invalid_time_range", blocked[0]["reason_code"])
        self.assertEqual(1, stats["blocked_reason_counts"]["invalid_time_range"])

    def test_all_day_event_without_policy_is_blocked_not_offerable(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "brian_inverse",
                "owner_instructor_key": "brian",
                "mode": "inverse_blocking",
                "default_location_key": "shipyard",
                "inverse_expansion_start_datetime": "2026-07-04T00:00:00",
                "inverse_expansion_horizon_days": 1,
                "inverse_expansion_require_active_appointment_container": False,
            }]
        }
        local_snapshot = {
            "events_by_source": {
                "brian_inverse": [{
                    "id": "allday1",
                    "summary": "Available",
                    "start": "2026-07-04",
                    "end": "2026-07-05",
                }]
            }
        }

        _blocks, blocked, stats = snapshot.build_snapshot(calendar_payload, {}, {}, local_snapshot)

        self.assertEqual(1, len(blocked))
        self.assertEqual("all_day_without_time", blocked[0]["reason_code"])
        self.assertEqual(1, stats["blocked_reason_counts"]["all_day_without_time"])

    def test_all_day_event_with_explicit_policy_still_invalid_time_range_guarded(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "brian_inverse",
                "owner_instructor_key": "brian",
                "mode": "inverse_blocking",
                "default_location_key": "shipyard",
                "all_day_means_available": True,
                "inverse_expansion_start_datetime": "2026-07-04T00:00:00",
                "inverse_expansion_horizon_days": 1,
                "inverse_expansion_require_active_appointment_container": False,
            }]
        }
        local_snapshot = {
            "events_by_source": {
                "brian_inverse": [{
                    "id": "allday-zero",
                    "summary": "Available",
                    "start": "2026-07-04",
                    "end": "2026-07-04",
                }]
            }
        }

        _blocks, blocked, _stats = snapshot.build_snapshot(calendar_payload, {}, {}, local_snapshot)

        self.assertEqual("invalid_time_range", blocked[0]["reason_code"])

    def test_cross_midnight_timed_explicit_event_is_ingested(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "amy_availability",
                "owner_instructor_key": "amy",
                "mode": "explicit_availability",
                "default_location_key": "shipyard",
            }]
        }
        local_snapshot = {
            "events_by_source": {
                "amy_availability": [{
                    "id": "overnight1",
                    "summary": "Available",
                    "start": "2026-07-04T16:00:00+00:00",
                    "end": "2026-07-05T04:00:00+00:00",
                }]
            }
        }

        blocks, blocked, stats = snapshot.build_snapshot(calendar_payload, {}, {}, local_snapshot)

        self.assertEqual([], blocked)
        self.assertEqual(1, len(blocks))
        self.assertEqual("2026-07-04", blocks[0]["date"])
        self.assertEqual("2026-07-05", blocks[0]["end_date"])
        self.assertEqual("2026-07-04T12:00:00", blocks[0]["start_datetime"])
        self.assertEqual("2026-07-05T00:00:00", blocks[0]["end_datetime"])
        self.assertNotIn("overnight_not_allowed", stats["blocked_all_reason_counts"])

    def test_cross_midnight_non_standard_increment_is_still_blocked(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "amy_availability",
                "owner_instructor_key": "amy",
                "mode": "explicit_availability",
                "default_location_key": "shipyard",
            }]
        }
        local_snapshot = {
            "events_by_source": {
                "amy_availability": [{
                    "id": "overnight-odd",
                    "summary": "Available",
                    "start": "2026-07-04T16:01:00+00:00",
                    "end": "2026-07-05T03:59:00+00:00",
                }]
            }
        }

        blocks, blocked, stats = snapshot.build_snapshot(calendar_payload, {}, {}, local_snapshot)

        self.assertEqual([], blocks)
        self.assertEqual("non_standard_time_increment", blocked[0]["reason_code"])
        self.assertEqual(["non_standard_time_increment"], blocked[0]["all_reason_codes"])
        self.assertEqual(1, stats["blocked_all_reason_counts"]["non_standard_time_increment"])

    def test_non_standard_time_increment_is_blocked_by_default(self) -> None:
        calendar_payload = {
            "calendar_sources": [{
                "calendar_source_key": "amy_availability",
                "owner_instructor_key": "amy",
                "mode": "explicit_availability",
            }]
        }
        local_snapshot = {
            "events_by_source": {
                "amy_availability": [{
                    "id": "odd1",
                    "summary": "HARD",
                    "start": "2026-07-06T08:01:00",
                    "end": "2026-07-06T09:59:00",
                }]
            }
        }

        blocks, blocked, _stats = snapshot.build_snapshot(calendar_payload, {}, {}, local_snapshot)

        self.assertEqual([], blocks)
        self.assertEqual("non_standard_time_increment", blocked[0]["reason_code"])

    def test_runtime_snapshot_directory_is_preferred_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            original_runtime_dir = snapshot.RUNTIME_CALENDAR_SNAPSHOT_DIR
            try:
                runtime_dir = Path(temp_dir)
                snapshot.RUNTIME_CALENDAR_SNAPSHOT_DIR = runtime_dir
                (runtime_dir / "amy_availability.json").write_text(json.dumps({
                    "calendar_source_id": "amy_availability",
                    "events": [{
                        "event_id": "runtime-event",
                        "summary": "HARD",
                        "start": "2026-06-22T08:30:00",
                        "end": "2026-06-22T12:00:00",
                    }],
                }), encoding="utf-8")

                path, payload, missing = snapshot.find_local_snapshot()

                self.assertEqual(runtime_dir, path)
                self.assertEqual([], [reason for reason in missing.values() if reason != "missing"])
                self.assertEqual("runtime-event", payload["events_by_source"]["amy_availability"][0]["event_id"])
            finally:
                snapshot.RUNTIME_CALENDAR_SNAPSHOT_DIR = original_runtime_dir


if __name__ == "__main__":
    unittest.main()
