from __future__ import annotations

import unittest

from scripts.inject_global_theme_assets import inject_html


class GlobalThemeInjectionTests(unittest.TestCase):
    def test_injects_assets_before_head_end(self):
        updated, changed = inject_html("<html><head><title>X</title></head><body></body></html>")
        self.assertTrue(changed)
        self.assertIn('/assets/site-theme.css', updated)
        self.assertIn('/assets/site-theme.js', updated)
        self.assertLess(updated.index('/assets/site-theme.js'), updated.index('</head>'))

    def test_is_idempotent(self):
        once, _ = inject_html("<html><head></head><body></body></html>")
        twice, changed = inject_html(once)
        self.assertFalse(changed)
        self.assertEqual(once, twice)

    def test_skips_fragments_without_head(self):
        original = "<section>Fragment</section>"
        updated, changed = inject_html(original)
        self.assertFalse(changed)
        self.assertEqual(original, updated)


if __name__ == "__main__":
    unittest.main()
