import json
import tempfile
import unittest
from pathlib import Path

from scripts import apply_google_durable_mirror as mirror
from scripts import export_google_durable_record as exporter


MIRRORED_AT = "2026-09-11T22:00:00Z"
RUN_AT = "2026-09-11T23:00:00Z"


def fixture():
    return {
        "landerware_sessions": [{
            "id": "session-1", "course_id": "acls", "course_name": "ACLS",
            "starts_at": "2026-09-13T13:00:00Z", "created_at": "2026-09-01T12:00:00Z",
            "updated_at": "2026-09-02T12:00:00Z",
        }, {
            "id": "session-2", "course_id": "bls", "course_name": "BLS",
            "starts_at": "2026-09-12T13:00:00Z", "created_at": "2026-09-01T12:00:00Z",
            "updated_at": "2026-09-02T12:00:00Z",
        }],
        "landerware_registrations": [{
            "id": "registration-1", "person_id": "person-1", "session_id": "session-1",
            "status": "active", "created_at": "2026-09-01T12:00:00Z",
            "updated_at": "2026-09-02T12:00:00Z",
        }],
        "landerware_people": [{
            "id": "person-1", "current_first_name": "Test", "current_last_name": "Person",
            "current_email": "test@example.invalid", "created_at": "2026-09-01T12:00:00Z",
            "updated_at": "2026-09-02T12:00:00Z",
        }],
        "landerware_organizations": [], "landerware_credentials": [], "landerware_retail_orders": [],
    }


class CorruptingMirror(mirror.LocalJsonMirror):
    def read(self, entity_type, canonical_id):
        row = super().read(entity_type, canonical_id)
        if row:
            row["content_hash"] = "sha256:" + "0" * 64
        return row


class GoogleDurableMirrorTests(unittest.TestCase):
    def make_export(self, root: Path):
        export_dir = root / "export"
        exporter.export(fixture(), export_dir, MIRRORED_AT)
        return export_dir

    def test_repeat_apply_is_idempotent_and_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            export_dir = self.make_export(root)
            first = mirror.apply_export(export_dir, root / "mirror", RUN_AT)
            second = mirror.apply_export(export_dir, root / "mirror", RUN_AT)
            self.assertEqual({"inserted": 4, "updated": 0, "unchanged": 0}, first["operations"])
            self.assertEqual({"inserted": 0, "updated": 0, "unchanged": 4}, second["operations"])
            self.assertEqual("verified", second["health"])
            self.assertEqual(4, second["reconciliation"]["matched"])
            self.assertEqual(2, len((root / "mirror" / "audit_log.jsonl").read_text().splitlines()))

    def test_changed_content_updates_without_duplicate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = fixture()
            export_dir = root / "export"
            exporter.export(payload, export_dir, MIRRORED_AT)
            mirror.apply_export(export_dir, root / "mirror", RUN_AT)
            payload["landerware_people"][0]["current_first_name"] = "Changed"
            exporter.export(payload, export_dir, MIRRORED_AT)
            receipt = mirror.apply_export(export_dir, root / "mirror", RUN_AT)
            people = json.loads((root / "mirror" / "records" / "person.json").read_text())
            self.assertEqual(1, receipt["operations"]["updated"])
            self.assertEqual(["person-1"], list(people))

    def test_extra_destination_record_is_durable_exception(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            export_dir = self.make_export(root)
            destination = mirror.LocalJsonMirror(root / "mirror")
            destination.upsert("person", "extra-person", {"content_hash": "sha256:" + "1" * 64})
            receipt = mirror.apply_export(export_dir, root / "mirror", RUN_AT, destination=destination)
            self.assertEqual("failed", receipt["health"])
            self.assertEqual(1, receipt["reconciliation"]["extra"])
            exception = json.loads((root / "mirror" / "exceptions.jsonl").read_text().splitlines()[0])
            self.assertEqual("extra", exception["status"])

    def test_read_after_write_failure_is_recorded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            export_dir = self.make_export(root)
            destination = CorruptingMirror(root / "mirror")
            receipt = mirror.apply_export(export_dir, root / "mirror", RUN_AT, destination=destination)
            self.assertEqual("failed", receipt["health"])
            self.assertEqual(4, receipt["exception_count"])

    def test_old_source_is_stale_without_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            receipt = mirror.apply_export(
                self.make_export(root), root / "mirror", "2026-09-13T01:00:01Z", stale_after_hours=25
            )
            self.assertEqual("stale", receipt["health"])
            self.assertEqual(0, receipt["exception_count"])

    def test_tampered_export_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            export_dir = self.make_export(root)
            with (export_dir / "person.jsonl").open("a", encoding="utf-8") as handle:
                handle.write("{}\n")
            with self.assertRaisesRegex(ValueError, "export hash mismatch"):
                mirror.apply_export(export_dir, root / "mirror", RUN_AT)

    def test_tampered_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            export_dir = self.make_export(root)
            manifest_path = export_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["counts"]["person"] = 999
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "snapshot hash mismatch"):
                mirror.apply_export(export_dir, root / "mirror", RUN_AT)


if __name__ == "__main__":
    unittest.main()
