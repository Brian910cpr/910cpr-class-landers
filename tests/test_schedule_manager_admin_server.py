from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import free_time_scheduler, generate_dynamic_offers
from scripts import schedule_manager_admin_server as manager


class ScheduleManagerTests(unittest.TestCase):
    def setUp(self):
        self.original_store = manager.STORE
        self.temp = tempfile.TemporaryDirectory()
        manager.STORE = Path(self.temp.name) / "hot_sync_active.json"

    def tearDown(self):
        manager.STORE = self.original_store
        self.temp.cleanup()

    def body(self):
        return {"course_key": "aha_bls_provider_renewal", "date": "2026-08-10", "start_time": "15:00", "instructor": "Brian Ennis", "location_name": ":: Wilmington; Shipyard Blvd - B", "visibility": "public", "capacity": 6, "participants": []}

    def test_create_persists_committed_anchor_with_canonical_duration(self):
        record = manager.new_record(self.body())
        manager.write_records([record])
        reread = manager.read_records()[0]
        self.assertEqual("landerware_manual", reread["provenance"])
        self.assertEqual("anchor", reread["schedule_role"])
        self.assertEqual("2026-08-10T17:00:00-04:00", reread["end_at"])
        self.assertEqual("awaiting_registration_link", reread["public_visibility_status"])
        self.assertFalse(reread["public_direct_booking"])
        json.loads(manager.STORE.read_text(encoding="utf-8"))

    def test_heartcode_skills_session_occupies_45_minutes_and_allows_immediate_follow_on(self):
        first_body = {
            **self.body(),
            "course_key": "aha_heartcode_bls",
            "start_time": "15:00",
        }
        second_body = {**self.body(), "start_time": "15:45"}

        first = manager.new_record(first_body)
        second = manager.new_record(second_body)

        self.assertEqual("2026-08-10T15:45:00-04:00", first["end_at"])
        self.assertEqual(first["end_at"], second["start_at"])
        self.assertFalse(
            generate_dynamic_offers.intervals_overlap(
                manager.datetime.fromisoformat(first["start_at"]),
                manager.datetime.fromisoformat(first["end_at"]),
                manager.datetime.fromisoformat(second["start_at"]),
                manager.datetime.fromisoformat(second["end_at"]),
            )
        )

    def test_all_mapped_skills_only_rules_use_45_minute_default(self):
        skills_only_ids = {
            "209811",  # AHA ACLS HeartCode
            "209812",  # AHA PALS HeartCode
            "210549",  # AHA BLS HeartCode
            "209808",  # AHA Heartsaver CPR AED Online + Skills
            "251545",  # AHA Heartsaver Pediatric Online + Skills
            "329495",  # AHA Heartsaver First Aid CPR AED Blended
            "248287",  # ARC BLS Blended
            "372258",  # ARC Adult CPR/AED Online + Skills
            "445670",  # HSI BLS + Adult First Aid Blended
            "359827",  # USCG Elementary First Aid / CPR Blended
        }
        rules = manager.course_rules()
        for course_id in skills_only_ids:
            with self.subTest(course_id=course_id):
                self.assertEqual(45, rules[course_id]["duration_minutes"])
                self.assertEqual(45, rules[course_id]["minimum_reservation_block_minutes"])

    def test_participants_edit_and_cancel_survive_restart(self):
        record = manager.new_record(self.body())
        record["participants"] = [{"name": "Pat", "email": "pat@example.com"}]
        record["status"] = record["session_status"] = "cancelled"
        manager.write_records([record])
        self.assertEqual("Pat", manager.read_records()[0]["participants"][0]["name"])
        self.assertEqual("cancelled", manager.read_records()[0]["session_status"])

    def test_cancelled_manual_class_no_longer_enters_scheduler_blocking_inventory(self):
        manager.write_records([{**manager.new_record(self.body()), "status": "cancelled", "session_status": "cancelled"}])
        config = {"timezone": "America/New_York", "hot_sync_delta": {"enabled": True, "active_path": str(manager.STORE), "absorbed_archive_path": str(Path(self.temp.name) / "absorbed.jsonl")}}
        result = free_time_scheduler.absorb_hot_sync_delta([], None, config)
        self.assertEqual([], result["active_sessions_for_merge"])
        self.assertEqual("cancelled", manager.read_records()[0]["hot_sync_status"])


if __name__ == "__main__": unittest.main()
