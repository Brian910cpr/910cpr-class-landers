"""Read-only V2 replay must fingerprint all real selector source inputs."""
import tempfile
import unittest
from pathlib import Path

from scripts import run_layered_release_probe as probe


class FrozenSourceReplayTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for index, relative in enumerate(probe.SOURCE_PATHS):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{"fixture": ' + str(index) + '}', encoding="utf-8")

    def test_same_snapshot_has_stable_digest(self):
        first = probe.source_fingerprint(self.root)
        self.assertEqual(first, probe.source_fingerprint(self.root))
        self.assertEqual(len(first), 64)

    def test_any_selected_source_change_invalidates_replay(self):
        baseline = probe.source_fingerprint(self.root)
        for relative in probe.SOURCE_PATHS:
            path = self.root / relative
            original = path.read_bytes()
            path.write_bytes(original + b" changed")
            self.assertNotEqual(baseline, probe.source_fingerprint(self.root), relative)
            path.write_bytes(original)
            self.assertEqual(baseline, probe.source_fingerprint(self.root))

    def test_missing_source_fails_closed(self):
        (self.root / probe.SOURCE_PATHS[0]).unlink()
        with self.assertRaises(FileNotFoundError):
            probe.source_fingerprint(self.root)


if __name__ == "__main__":
    unittest.main()
