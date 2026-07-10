from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import generate_dynamic_offers


class DynamicOffersTest(unittest.TestCase):
    def base_loaded(self) -> dict:
        return {
            "course_catalog": {
                "courses": [{
                    "course_id": "209806",
                    "official_title": "AHA BLS Provider",
                    "family": "BLS",
                    "duration_minutes": 60,
                    "setup_buffer_minutes": 0,
                    "cleanup_buffer_minutes": 0,
                    "default_capacity": 6,
                    "appointment_allowed": True,
                    "required_instructor_certifications": ["AHA_BLS_INSTRUCTOR"],
                }]
            },
            "people_catalog": {
                "people": [{
                    "person_id": "person_brian",
                    "display_name": "Brian Ennis",
                    "assignment_mode": "PRIMARY",
                    "dynamic_offer_eligible": True,
                    "certifications": [{"certification_code": "AHA_BLS_INSTRUCTOR"}],
                }]
            },
            "instructor_availability": {
                "availability_blocks": [{
                    "instructor_name": "Brian",
                    "date": "2026-06-22",
                    "start_time": "08:00",
                    "end_time": "09:00",
                    "availability_status": "available",
                    "location_name": "Legacy Shipyard",
                    "allowed_course_families": ["BLS"],
                }]
            },
            "sessions_current": {"sessions": []},
            "schedule_future": {"sessions": []},
        }

    def brian_shipyard_container(self) -> dict:
        return {
            "containers": [{
                "container_id": "shipyard_brian_test",
                "instructor_name": "Brian",
                "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                "room_or_resource_name": "Shipyard Office",
                "first_valid_date": "2026-06-21",
                "first_valid_appointmentDayId": 260670,
                "last_valid_date": "2027-04-30",
                "last_valid_appointmentDayId": 260983,
                "first_invalid_appointmentDayId": 260984,
                "status": "active",
            }]
        }

    def test_normalize_occupancy_reads_nested_ical_session_fields(self) -> None:
        payload = {
            "sessions": [{
                "start": "2026-07-13T15:30:00-04:00",
                "end": "2026-07-13T17:30:00-04:00",
                "course": {"course_name_raw": "AHA Heartsaver CPR AED Online"},
                "location": {"location_name": "NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office"},
                "staffing": {"lead_instructor_name": "Brian Ennis"},
            }]
        }

        rows = generate_dynamic_offers.normalize_occupancy(payload, "data/sessions_current.json")

        self.assertEqual(1, len(rows))
        self.assertEqual("AHA Heartsaver CPR AED Online", rows[0]["course_title"])
        self.assertEqual("Brian Ennis", rows[0]["instructor"])
        self.assertEqual("NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office", rows[0]["location"])

    def test_generates_offer_for_scheduler_enabled_qualified_person(self) -> None:
        loaded = {
            "course_catalog": {
                "courses": [{
                    "course_id": "209806",
                    "official_title": "AHA BLS Provider",
                    "family": "BLS",
                    "duration_minutes": 60,
                    "setup_buffer_minutes": 0,
                    "cleanup_buffer_minutes": 0,
                    "default_capacity": 6,
                    "appointment_allowed": True,
                    "required_instructor_certifications": ["AHA_BLS_INSTRUCTOR"],
                }]
            },
            "people_catalog": {
                "people": [{
                    "person_id": "person_brian",
                    "display_name": "Brian Ennis",
                    "assignment_mode": "PRIMARY",
                    "dynamic_offer_eligible": True,
                    "certifications": [{"certification_code": "AHA_BLS_INSTRUCTOR"}],
                }]
            },
            "instructor_availability": {
                "availability_blocks": [{
                    "instructor_name": "Brian",
                    "date": "2026-06-22",
                    "start_time": "08:00",
                    "end_time": "09:00",
                    "availability_status": "available",
                    "location_name": "Shipyard",
                    "allowed_course_families": ["BLS"],
                }]
            },
            "sessions_current": {"sessions": []},
            "schedule_future": {"sessions": []},
        }

        offers, rejections, stats = generate_dynamic_offers.generate_offers(loaded)

        self.assertEqual(1, len(offers))
        self.assertEqual("high", offers[0]["confidence"])
        self.assertEqual("person_brian", offers[0]["instructor_person_id"])
        self.assertEqual(1, stats["offers_generated"])
        self.assertEqual([], rejections)

    def test_rejects_unqualified_scheduler_enabled_person(self) -> None:
        loaded = {
            "course_catalog": {
                "courses": [{
                    "course_id": "209811",
                    "official_title": "AHA ACLS HeartCode",
                    "family": "ACLS",
                    "duration_minutes": 60,
                    "setup_buffer_minutes": 0,
                    "cleanup_buffer_minutes": 0,
                    "default_capacity": 1,
                    "appointment_allowed": True,
                    "required_instructor_certifications": ["AHA_ACLS_INSTRUCTOR"],
                }]
            },
            "people_catalog": {
                "people": [{
                    "person_id": "person_brian",
                    "display_name": "Brian Ennis",
                    "assignment_mode": "PRIMARY",
                    "dynamic_offer_eligible": True,
                    "certifications": [{"certification_code": "AHA_BLS_INSTRUCTOR"}],
                }]
            },
            "instructor_availability": {
                "availability_blocks": [{
                    "instructor_name": "Brian",
                    "date": "2026-06-22",
                    "start_time": "08:00",
                    "end_time": "09:00",
                    "availability_status": "available",
                    "location_name": "Shipyard",
                    "allowed_course_families": ["ACLS"],
                }]
            },
            "sessions_current": {"sessions": []},
            "schedule_future": {"sessions": []},
        }

        offers, rejections, _ = generate_dynamic_offers.generate_offers(loaded)

        self.assertEqual([], offers)
        self.assertEqual("instructor_lacks_required_certification", rejections[0]["reason_code"])

    def test_valid_live_snapshot_is_preferred_over_legacy_availability(self) -> None:
        loaded = self.base_loaded()
        loaded["live_availability_snapshot"] = {
            "availability_blocks": [{
                "instructor_name": "Brian Ennis",
                "person_id": "person_brian",
                "start_datetime": "2026-06-23T10:00:00",
                "end_datetime": "2026-06-23T11:00:00",
                "date": "2026-06-23",
                "start_time": "10:00",
                "end_time": "11:00",
                "availability_status": "available",
                "location_name": "Live Shipyard",
                "allowed_course_families": ["BLS"],
                "source_event_id": "live-evt-1",
            }]
        }

        offers, _rejections, stats = generate_dynamic_offers.generate_offers(loaded)

        self.assertEqual("live_availability_snapshot", stats["availability_source_used"])
        self.assertFalse(stats["availability_fallback_used"])
        self.assertEqual(1, stats["available_blocks_read"])
        self.assertEqual(1, len(offers))
        self.assertEqual("2026-06-23", offers[0]["date"])
        self.assertEqual("2026-06-23T10:00:00", offers[0]["start_datetime"])
        self.assertEqual("2026-06-23T11:00:00", offers[0]["end_datetime"])
        self.assertEqual("Live Shipyard", offers[0]["location"])
        self.assertIn("live_calendar_availability_window", offers[0]["reasons"])

    def test_live_snapshot_full_datetimes_preserve_cross_midnight_end_date(self) -> None:
        loaded = self.base_loaded()
        loaded["live_availability_snapshot"] = {
            "availability_blocks": [{
                "instructor_name": "Brian Ennis",
                "person_id": "person_brian",
                "start_datetime": "2026-06-23T23:00:00",
                "end_datetime": "2026-06-24T00:30:00",
                "date": "2026-06-23",
                "end_date": "2026-06-24",
                "start_time": "23:00",
                "end_time": "00:30",
                "availability_status": "available",
                "location_name": "Live Shipyard",
                "allowed_course_families": ["BLS"],
                "source_event_id": "live-overnight-allowed",
            }]
        }

        offers, _rejections, stats = generate_dynamic_offers.generate_offers(loaded)

        self.assertEqual("live_availability_snapshot", stats["availability_source_used"])
        self.assertGreaterEqual(len(offers), 1)
        self.assertEqual("2026-06-23T23:00:00", offers[0]["start_datetime"])
        self.assertEqual("2026-06-24T00:00:00", offers[0]["end_datetime"])

    def test_live_snapshot_invalid_time_range_does_not_fallback_to_legacy(self) -> None:
        loaded = self.base_loaded()
        loaded["live_availability_snapshot"] = {
            "availability_blocks": [{
                "instructor_name": "Brian Ennis",
                "person_id": "person_brian",
                "start_datetime": "2026-06-23T11:00:00",
                "end_datetime": "2026-06-23T10:00:00",
                "date": "2026-06-23",
                "start_time": "11:00",
                "end_time": "10:00",
                "availability_status": "available",
                "location_name": "Live Shipyard",
                "allowed_course_families": ["BLS"],
                "source_event_id": "live-invalid",
            }]
        }

        offers, rejections, stats = generate_dynamic_offers.generate_offers(loaded)

        self.assertEqual([], offers)
        self.assertEqual("live_availability_snapshot", stats["availability_source_used"])
        self.assertFalse(stats["availability_fallback_used"])
        self.assertEqual("invalid_time_range", rejections[0]["reason_code"])

    def test_instructor_time_only_window_targets_confirmed_container_location(self) -> None:
        loaded = self.base_loaded()
        loaded["appointment_containers"] = self.brian_shipyard_container()
        loaded["live_availability_snapshot"] = {
            "availability_blocks": [{
                "instructor_name": "Brian Ennis",
                "person_id": "person_brian",
                "start_datetime": "2026-07-04T08:00:00",
                "end_datetime": "2026-07-04T13:00:00",
                "date": "2026-07-04",
                "end_date": "2026-07-04",
                "start_time": "08:00",
                "end_time": "13:00",
                "availability_status": "available",
                "availability_location_mode": "instructor_time_only",
                "source_location": "4018 Shipyard Blvd, Wilmington, NC 28403, USA",
                "location_name": "4018 Shipyard Blvd, Wilmington, NC 28403, USA",
                "allowed_course_families": ["BLS"],
                "source_event_id": "brian-test-shipyard",
            }]
        }

        offers, _rejections, stats = generate_dynamic_offers.generate_offers(loaded)

        self.assertGreaterEqual(len(offers), 1)
        self.assertEqual("live_availability_snapshot", stats["availability_source_used"])
        self.assertEqual("shipyard_brian_test", offers[0]["matched_container_id"])
        self.assertEqual("NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office", offers[0]["offer_location"])
        self.assertEqual("4018 Shipyard Blvd, Wilmington, NC 28403, USA", offers[0]["source_location"])
        self.assertIn("instructor_time_only_confirmed_container_target", offers[0]["reasons"])

    def test_august_live_snapshot_block_generates_august_bls_offer(self) -> None:
        loaded = self.base_loaded()
        loaded["appointment_containers"] = self.brian_shipyard_container()
        loaded["live_availability_snapshot"] = {
            "availability_blocks": [{
                "instructor_name": "Brian Ennis",
                "person_id": "person_brian",
                "start_datetime": "2026-08-04T13:00:00",
                "end_datetime": "2026-08-04T16:00:00",
                "date": "2026-08-04",
                "end_date": "2026-08-04",
                "start_time": "13:00",
                "end_time": "16:00",
                "availability_status": "available",
                "availability_location_mode": "instructor_time_only",
                "source_location": "report_only_august_alignment_fixture",
                "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                "allowed_course_families": ["BLS"],
                "source_event_id": "august-brian-bls-live-fixture",
            }]
        }

        offers, _rejections, stats = generate_dynamic_offers.generate_offers(loaded)

        august_offers = [offer for offer in offers if offer["date"].startswith("2026-08")]
        self.assertEqual("live_availability_snapshot", stats["availability_source_used"])
        self.assertGreaterEqual(len(august_offers), 1)
        self.assertEqual("2026-08-04", august_offers[0]["date"])
        self.assertEqual("209806", august_offers[0]["course_id"])

    def test_bls_provider_consumption_window_includes_default_buffers(self) -> None:
        loaded = self.base_loaded()
        loaded["course_catalog"]["courses"][0].pop("setup_buffer_minutes")
        loaded["course_catalog"]["courses"][0].pop("cleanup_buffer_minutes")
        loaded["course_catalog"]["courses"][0]["duration_minutes"] = 120
        loaded["instructor_availability"]["availability_blocks"][0].update({
            "date": "2026-06-22",
            "start_time": "17:00",
            "end_time": "22:00",
        })

        offers, _rejections, _stats = generate_dynamic_offers.generate_offers(loaded)
        first = offers[0]

        self.assertEqual("2026-06-22T17:00:00", first["appointment_display_start"])
        self.assertEqual("2026-06-22T19:00:00", first["appointment_display_end"])
        self.assertEqual(15, first["setup_buffer_minutes"])
        self.assertEqual(30, first["cleanup_buffer_minutes"])
        self.assertEqual(165, first["scheduler_consumption_minutes"])
        self.assertEqual("2026-06-22T19:45:00", first["scheduler_consumption_end"])

    def test_zero_live_block_snapshot_falls_back_to_legacy_availability(self) -> None:
        loaded = self.base_loaded()
        loaded["live_availability_snapshot"] = {
            "availability_blocks": [{
                "instructor_name": "Brian Ennis",
                "person_id": "person_brian",
                "date": "2026-06-23",
                "start_time": "10:00",
                "end_time": "11:00",
                "availability_status": "blocked",
                "location_name": "Live Shipyard",
                "allowed_course_families": ["BLS"],
            }]
        }

        offers, _rejections, stats = generate_dynamic_offers.generate_offers(loaded)

        self.assertEqual("legacy_instructor_availability_fallback", stats["availability_source_used"])
        self.assertTrue(stats["availability_fallback_used"])
        self.assertEqual("live_snapshot_zero_available_blocks", stats["availability_source_reason"])
        self.assertEqual(1, len(offers))
        self.assertEqual("2026-06-22", offers[0]["date"])

    def test_invalid_or_missing_live_snapshot_falls_back_safely(self) -> None:
        loaded = self.base_loaded()
        loaded["live_availability_snapshot"] = []

        offers, _rejections, stats = generate_dynamic_offers.generate_offers(loaded)

        self.assertEqual("legacy_instructor_availability_fallback", stats["availability_source_used"])
        self.assertTrue(stats["availability_fallback_used"])
        self.assertEqual("invalid_live_snapshot_shape", stats["availability_source_reason"])
        self.assertEqual(1, len(offers))

    def test_run_outputs_are_scoped_to_audit_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit_dir = root / "data" / "audit"
            config_dir = root / "data" / "config"
            inventory_dir = root / "data" / "inventory"
            docs_data_dir = root / "docs" / "data"
            data_dir = root / "data"
            config_dir.mkdir(parents=True)
            inventory_dir.mkdir(parents=True)
            docs_data_dir.mkdir(parents=True)
            audit_dir.mkdir(parents=True)
            data_dir.mkdir(exist_ok=True)

            (config_dir / "course_catalog.json").write_text(json.dumps(self.base_loaded()["course_catalog"]), encoding="utf-8")
            (config_dir / "people_catalog.json").write_text(json.dumps(self.base_loaded()["people_catalog"]), encoding="utf-8")
            (audit_dir / "live_availability_snapshot_preview.json").write_text(json.dumps({
                "availability_blocks": [{
                    "instructor_name": "Brian Ennis",
                    "person_id": "person_brian",
                    "date": "2026-06-23",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "availability_status": "available",
                    "location_name": "Live Shipyard",
                    "allowed_course_families": ["BLS"],
                }]
            }), encoding="utf-8")
            (inventory_dir / "instructor_availability.json").write_text(json.dumps(self.base_loaded()["instructor_availability"]), encoding="utf-8")
            (data_dir / "sessions_current.json").write_text(json.dumps({"sessions": []}), encoding="utf-8")
            (docs_data_dir / "schedule_future.json").write_text(json.dumps({"sessions": []}), encoding="utf-8")

            original_input_paths = generate_dynamic_offers.INPUT_PATHS
            original_audit_dir = generate_dynamic_offers.AUDIT_DIR
            original_offers = generate_dynamic_offers.OFFERS_PATH
            original_offers_summary_json = generate_dynamic_offers.OFFERS_SUMMARY_JSON_PATH
            original_offers_summary_md = generate_dynamic_offers.OFFERS_SUMMARY_MD_PATH
            original_report = generate_dynamic_offers.REPORT_PATH
            original_consumption_summary = generate_dynamic_offers.CONSUMPTION_SUMMARY_PATH
            original_consumption_report = generate_dynamic_offers.CONSUMPTION_REPORT_PATH
            try:
                generate_dynamic_offers.AUDIT_DIR = audit_dir
                generate_dynamic_offers.OFFERS_PATH = root / "data" / "runtime" / "audit_previews" / "dynamic_offers_preview.json"
                generate_dynamic_offers.OFFERS_SUMMARY_JSON_PATH = audit_dir / "dynamic_offers_preview_summary.json"
                generate_dynamic_offers.OFFERS_SUMMARY_MD_PATH = audit_dir / "dynamic_offers_preview_summary.md"
                generate_dynamic_offers.REPORT_PATH = audit_dir / "dynamic_offers_report.md"
                generate_dynamic_offers.CONSUMPTION_SUMMARY_PATH = audit_dir / "scheduler_consumption_window_summary.json"
                generate_dynamic_offers.CONSUMPTION_REPORT_PATH = audit_dir / "scheduler_consumption_window_report.md"
                generate_dynamic_offers.INPUT_PATHS = {
                    "course_catalog": config_dir / "course_catalog.json",
                    "people_catalog": config_dir / "people_catalog.json",
                    "live_availability_snapshot": audit_dir / "live_availability_snapshot_preview.json",
                    "instructor_availability": inventory_dir / "instructor_availability.json",
                    "sessions_current": data_dir / "sessions_current.json",
                    "schedule_future": docs_data_dir / "schedule_future.json",
                }
                result = generate_dynamic_offers.run()

                self.assertEqual("live_availability_snapshot", result["availability_source_used"])
                self.assertEqual(1, result["available_blocks_read"])
                self.assertEqual(1, result["offers_generated"])
                report = (audit_dir / "dynamic_offers_report.md").read_text(encoding="utf-8")
                self.assertIn("Availability source used: live_availability_snapshot", report)
                written = sorted(path.relative_to(root).as_posix() for path in audit_dir.glob("dynamic_offers_*"))
                self.assertEqual(
                    [
                        "data/audit/dynamic_offers_preview_summary.json",
                        "data/audit/dynamic_offers_preview_summary.md",
                        "data/audit/dynamic_offers_report.md",
                    ],
                    written,
                )
                self.assertTrue((root / "data" / "runtime" / "audit_previews" / "dynamic_offers_preview.json").exists())
            finally:
                generate_dynamic_offers.INPUT_PATHS = original_input_paths
                generate_dynamic_offers.AUDIT_DIR = original_audit_dir
                generate_dynamic_offers.OFFERS_PATH = original_offers
                generate_dynamic_offers.OFFERS_SUMMARY_JSON_PATH = original_offers_summary_json
                generate_dynamic_offers.OFFERS_SUMMARY_MD_PATH = original_offers_summary_md
                generate_dynamic_offers.REPORT_PATH = original_report
                generate_dynamic_offers.CONSUMPTION_SUMMARY_PATH = original_consumption_summary
                generate_dynamic_offers.CONSUMPTION_REPORT_PATH = original_consumption_report


if __name__ == "__main__":
    unittest.main()
