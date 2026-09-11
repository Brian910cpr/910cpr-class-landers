import tempfile
import unittest
from pathlib import Path

from scripts.cloudflare_pages_preflight import validate_tree


class CloudflarePagesPreflightTests(unittest.TestCase):
    def test_valid_tree_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("ok", encoding="utf-8")
            errors, count = validate_tree(root, max_files=2, max_file_size=10)
            self.assertEqual(errors, [])
            self.assertEqual(count, 1)

    def test_oversized_asset_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "large.bin").write_bytes(b"12345")
            errors, _ = validate_tree(root, max_files=2, max_file_size=4)
            self.assertIn("asset exceeds 4 bytes: large.bin (5 bytes)", errors)

    def test_file_count_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one").write_text("", encoding="utf-8")
            (root / "two").write_text("", encoding="utf-8")
            errors, count = validate_tree(root, max_files=1, max_file_size=10)
            self.assertEqual(count, 2)
            self.assertIn("tree has 2 files; limit is 1", errors)

    def test_redirect_limits_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "_redirects").write_text("\n".join(f"/old-{n} /new-{n}" for n in range(3)), encoding="utf-8")
            errors, _ = validate_tree(root, max_files=2, max_file_size=10_000)
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
