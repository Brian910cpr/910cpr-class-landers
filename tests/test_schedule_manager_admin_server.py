from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import free_time_scheduler
from scripts import schedule_manager_admin_server as manager
from scripts import session_workspace as workspace


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
        self.assertEqual("create", reread["session_workspace"]["lifecycle_state"])
        self.assertEqual(workspace.POLICY_VERSION, reread["requirements_manifest"]["policy_version"])
        self.assertEqual(5, reread["roster"]["blank_walk_in_rows"])
        json.loads(manager.STORE.read_text(encoding="utf-8"))

    def test_workspace_prefills_roster_and_preserves_manifest_snapshot(self):
        body = self.body()
        body["participants"] = [{"name": "Pat Student", "email": "pat@example.com"}]
        record = manager.new_record(body)
        self.assertEqual("Pat Student", record["roster"]["students"][0]["name"])
        manifest_id = record["requirements_manifest"]["manifest_id"]
        captured_at = record["requirements_manifest"]["captured_at"]
        record["course_name"] = "A future renamed course"
        _, changed = workspace.ensure_workspace(record)
        self.assertFalse(changed)
        self.assertEqual(manifest_id, record["requirements_manifest"]["manifest_id"])
        self.assertEqual(captured_at, record["requirements_manifest"]["captured_at"])
        self.assertNotEqual(record["course_name"], record["requirements_manifest"]["course_name"])

    def test_controlled_materials_are_not_claimed_as_provided(self):
        record = manager.new_record(self.body())
        items = record["requirements_manifest"]["items"]
        controlled = [item for item in items if item["classification"] == "external_controlled_material"]
        self.assertGreaterEqual(len(controlled), 2)
        self.assertTrue(all(not item["provided_by_910cpr"] for item in controlled))
        packet = workspace.packet_projection(record)
        self.assertTrue(all(item["classification"] == "landerware_may_provide" for item in packet["provided_requirements"]))
        rendered = workspace.packet_html(packet)
        self.assertIn("Controlled program materials are not included", rendered)
        self.assertIn("Walk-in", rendered)
        self.assertNotIn("testing and answer documentation</h2>", rendered)

    def test_instructor_scope_and_initial_private_roles(self):
        record = manager.new_record(self.body())
        self.assertTrue(workspace.authorized({"role": "Instructor", "actor_name": "Brian Ennis"}, record))
        self.assertFalse(workspace.authorized({"role": "Instructor", "actor_name": "Another Instructor"}, record))
        self.assertFalse(workspace.authorized({"role": "Corporate Client", "actor_name": "Client"}, record))
        self.assertFalse(workspace.authorized({"role": "Employee Self-Service", "actor_name": "Pat"}, record))
        self.assertTrue(workspace.authorized({"role": "Administrator"}, record, administer=True))

    def test_lifecycle_is_ordered_and_actions_are_audited(self):
        record = manager.new_record(self.body())
        actor = {"role": "Instructor", "actor_name": "Brian Ennis", "actor_id": "brian"}
        workspace.transition(record, "prepare", actor)
        self.assertEqual("prepare", record["session_workspace"]["lifecycle_state"])
        event = record["session_workspace"]["action_log"][-1]
        self.assertEqual("lifecycle_transition", event["action"])
        self.assertIsNotNone(event["timestamp"])
        with self.assertRaisesRegex(ValueError, "Invalid lifecycle transition"):
            workspace.transition(record, "archive", actor)

    def test_every_record_level_accepts_future_document_ids(self):
        record = manager.new_record(self.body())
        self.assertEqual([], record["document_ids"])
        self.assertEqual([], record["session_workspace"]["document_ids"])
        self.assertEqual([], record["requirements_manifest"]["document_ids"])
        self.assertEqual([], record["roster"]["document_ids"])
        self.assertEqual([], record["roster"]["students"])

    def test_roster_projection_can_retain_entry_identity_when_schedule_participants_change(self):
        body = self.body(); body["participants"] = [{"name": "Pat", "email": "pat@example.com"}]
        record = manager.new_record(body)
        original_id = record["roster"]["students"][0]["roster_entry_id"]
        existing_ids = {item["email"].casefold(): item["roster_entry_id"] for item in record["roster"]["students"]}
        participant = {"name": "Pat Updated", "email": "pat@example.com"}
        retained = participant.get("roster_entry_id") or existing_ids.get(participant["email"].casefold())
        self.assertEqual(original_id, retained)

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
