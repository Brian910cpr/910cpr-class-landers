import unittest

from scripts.check_case_insensitive_paths import ALLOWED_COLLISIONS, collision_groups


class CaseInsensitivePathTests(unittest.TestCase):
    def test_detects_case_only_collision(self):
        self.assertEqual(
            collision_groups(["docs/BLS.html", "docs/bls.html", "docs/index.html"]),
            {frozenset(("docs/BLS.html", "docs/bls.html"))},
        )

    def test_allowlist_documents_five_legacy_groups(self):
        self.assertEqual(len(ALLOWED_COLLISIONS), 5)


if __name__ == "__main__":
    unittest.main()
