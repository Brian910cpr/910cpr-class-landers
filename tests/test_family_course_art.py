from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import family_course_art as art


class FamilyCourseArtTests(unittest.TestCase):
    def test_numbered_discovery_uses_only_existing_files_and_numeric_order(self):
        for count in (1, 2, 3, 5, 12):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as folder:
                docs = Path(folder)
                characters = docs / "images" / "characters"
                characters.mkdir(parents=True)
                for number in range(1, count + 1):
                    (characters / f"ACLS-{number}.webp").write_bytes(b"approved")
                (characters / "ACLS-1-480.webp").write_bytes(b"small")
                (characters / "BLS-1.webp").write_bytes(b"other family")
                with patch.object(art, "DOCS", docs), patch.object(art, "CHARACTERS", characters):
                    found = art.hero_candidates({"hero_image": {"rotation_prefix": "ACLS"}})
                self.assertEqual(count, len(found))
                self.assertEqual([f"/images/characters/ACLS-{i}.webp" for i in range(1, count + 1)], [item["url"].split("?")[0] for item in found])
                self.assertIn("480w", found[0]["srcset"])
                if count > 1:
                    self.assertNotIn("srcset", found[1])

    def test_missing_number_does_not_create_a_broken_candidate(self):
        with tempfile.TemporaryDirectory() as folder:
            docs = Path(folder)
            for name in ("ACLS-1.webp", "ACLS-5.webp"):
                (docs / name).write_bytes(b"asset")
            with patch.object(art, "DOCS", docs), patch.object(art, "CHARACTERS", docs):
                found = art.hero_candidates({"hero_image": {"rotation_prefix": "ACLS"}})
            self.assertEqual(2, len(found))
            self.assertTrue(found[1]["url"].startswith("/ACLS-5.webp?"))

    def test_unavailable_fallback_is_not_rendered(self):
        self.assertEqual("", art.hero_markup({"hero_image": {"url": "/missing-approved-art.webp"}}))

    def test_real_course_pages_have_one_family_specific_deck_and_no_eager_number_one(self):
        import html
        import re

        pages = json.loads((art.ROOT / "data/config/block_schedule_pages.json").read_text())["pages"]
        for family, expected in {"bls": 3, "acls": 3, "pals": 5}.items():
            with self.subTest(family=family):
                candidates = art.hero_candidates(pages[family])
                self.assertGreaterEqual(len(candidates), expected)
                self.assertTrue(all(row["url"].startswith(f"/images/characters/{family}/")
                                    for row in candidates))
                path = art.ROOT / pages[family]["output_path"]
                text = path.read_text()
                img = re.search(r'<img data-family-hero="[^"]+"[^>]*>', text).group()
                self.assertNotIn(" src=", img)
                self.assertNotIn(" srcset=", img)
                self.assertIn("<noscript><img src=", text)
                self.assertEqual(candidates, json.loads(html.unescape(
                    re.search(r'data-hero-images="([^"]+)"', img).group(1))))
                self.assertIn(art.asset_url("/assets/family-hero.js"), text)
                for alias in pages[family]["alias_output_paths"]:
                    self.assertEqual((art.ROOT / alias).read_text(), text)

    def test_published_character_manifest_preserves_full_size_sources(self):
        manifest = json.loads((art.ROOT / "CUSTOMER_images/approved-course-characters/manifest.json").read_text())
        self.assertTrue({"BLS-1", "ACLS-1", "ACLS-2", "ACLS-3", "PALS-1"}.issubset(manifest))
        for item in manifest.values():
            self.assertGreaterEqual(item["source_dimensions"][0], 960)
            self.assertLess(item["variants"]["480"]["bytes"], 100_000)


if __name__ == "__main__":
    unittest.main()
