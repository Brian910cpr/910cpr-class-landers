from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import free_time_scheduler
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
