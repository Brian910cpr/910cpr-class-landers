import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.durable_record_recovery import create_archive, restore_archive
from scripts.export_google_durable_record import SPECS, export


class DurableRecordRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        payload = {spec.table: [{"id": f"id-{index}", "created_at": "2026-09-11T20:00:00-04:00"}] for index, spec in enumerate(SPECS)}
        self.export_dir = self.root / "export"
        export(payload, self.export_dir, "2026-09-11T20:01:00-04:00")

    def tearDown(self):
        self.temp.cleanup()

    def test_archive_is_deterministic_and_restores_clean_sample(self):
        first, second = self.root / "first.zip", self.root / "second.zip"
        created = create_archive(self.export_dir, first)
        create_archive(self.export_dir, second)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        receipt = restore_archive(first, self.root / "recovery")
        self.assertEqual(receipt["result"], "verified")
        self.assertEqual(receipt["record_count"], 6)
        self.assertEqual(receipt["reconciliation"]["matched"], 6)
        self.assertEqual(created["archive_sha256"], receipt["archive_sha256"])

    def test_restore_refuses_nonempty_destination(self):
        archive = self.root / "snapshot.zip"
        create_archive(self.export_dir, archive)
        recovery = self.root / "recovery"
        recovery.mkdir()
        (recovery / "keep.txt").write_text("preserve", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "absent or empty"):
            restore_archive(archive, recovery)
        self.assertEqual((recovery / "keep.txt").read_text(encoding="utf-8"), "preserve")

    def test_restore_rejects_tampered_member(self):
        archive, tampered = self.root / "snapshot.zip", self.root / "tampered.zip"
        create_archive(self.export_dir, archive)
        with zipfile.ZipFile(archive) as source, zipfile.ZipFile(tampered, "w") as target:
            for name in source.namelist():
                data = source.read(name)
                target.writestr(name, data + b"x" if name == "person.jsonl" else data)
        with self.assertRaisesRegex(ValueError, "file hash mismatch"):
            restore_archive(tampered, self.root / "bad-recovery")

    def test_restore_rejects_unexpected_member(self):
        archive, unsafe = self.root / "snapshot.zip", self.root / "unsafe.zip"
        create_archive(self.export_dir, archive)
        with zipfile.ZipFile(archive) as source, zipfile.ZipFile(unsafe, "w") as target:
            for name in source.namelist():
                target.writestr(name, source.read(name))
            target.writestr("../escape.txt", "no")
        with self.assertRaisesRegex(ValueError, "unexpected members"):
            restore_archive(unsafe, self.root / "unsafe-recovery")


if __name__ == "__main__":
    unittest.main()
