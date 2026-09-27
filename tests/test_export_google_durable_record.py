import json
import tempfile
import unittest
from pathlib import Path

from scripts import export_google_durable_record as exporter


MIRRORED_AT = "2026-09-11T22:00:00Z"


class GoogleDurableRecordExporterTests(unittest.TestCase):
    def fixture(self):
        return {
            "landerware_sessions": [{
                "id": "session-2", "course_id": "bls", "course_name": "BLS",
                "starts_at": "2026-09-12T13:00:00Z", "provenance": "test",
                "requirements_manifest": {}, "created_at": "2026-09-01T12:00:00Z",
                "updated_at": "2026-09-02T12:00:00Z", "secret_field": "must-not-export",
            }, {
                "id": "session-1", "course_id": "acls", "course_name": "ACLS",
                "starts_at": "2026-09-13T13:00:00Z", "provenance": "test",
                "requirements_manifest": {}, "created_at": "2026-09-01T12:00:00Z",
                "updated_at": "2026-09-02T12:00:00Z",
            }],
            "landerware_registrations": [{
                "id": "registration-1", "person_id": "person-1", "session_id": "session-1",
                "status": "active", "source": "test", "created_at": "2026-09-01T12:00:00Z",
                "updated_at": "2026-09-02T12:00:00Z",
            }],
            "landerware_people": [{
                "id": "person-1", "current_first_name": "Test", "current_last_name": "Person",
                "current_email": "test@example.invalid", "created_at": "2026-09-01T12:00:00Z",
                "updated_at": "2026-09-02T12:00:00Z",
            }],
            "landerware_organizations": [], "landerware_credentials": [], "landerware_retail_orders": [],
        }

    def test_export_is_sorted_allowlisted_and_counted(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = exporter.export(self.fixture(), Path(temp), MIRRORED_AT)
            records = [json.loads(line) for line in (Path(temp) / "session.jsonl").read_text().splitlines()]
            self.assertEqual(["session-1", "session-2"], [row["canonical_id"] for row in records])
            self.assertNotIn("secret_field", records[1]["payload"])
            self.assertEqual(4, manifest["total_records"])
            self.assertEqual(2, manifest["counts"]["session"])
            self.assertRegex(records[0]["content_hash"], r"^sha256:[0-9a-f]{64}$")

    def test_repeat_export_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
            exporter.export(self.fixture(), Path(left), MIRRORED_AT)
            exporter.export(self.fixture(), Path(right), MIRRORED_AT)
            for name in [*(f"{spec.entity_type}.jsonl" for spec in exporter.SPECS), "manifest.json"]:
                self.assertEqual((Path(left) / name).read_bytes(), (Path(right) / name).read_bytes())

    def test_content_hash_ignores_mirror_and_reconciliation_metadata(self):
        spec = exporter.SPECS[0]
        row = self.fixture()["landerware_sessions"][0]
        first = exporter.envelope(spec, row, "2026-09-11T22:00:00Z")
        second = exporter.envelope(spec, row, "2026-09-12T22:00:00Z")
        self.assertEqual(first["content_hash"], second["content_hash"])

    def test_missing_id_and_invalid_table_shape_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "missing id"):
            exporter.envelope(exporter.SPECS[0], {"updated_at": MIRRORED_AT}, MIRRORED_AT)
        payload = self.fixture()
        payload["landerware_people"] = {}
        with tempfile.TemporaryDirectory() as temp, self.assertRaisesRegex(ValueError, "array of objects"):
            exporter.export(payload, Path(temp), MIRRORED_AT)


if __name__ == "__main__":
    unittest.main()
