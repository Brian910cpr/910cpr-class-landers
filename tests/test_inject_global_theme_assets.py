from __future__ import annotations

import unittest

from scripts.inject_global_theme_assets import THEME_VERSION, inject_html


class GlobalThemeInjectionTests(unittest.TestCase):
    def test_injects_assets_before_head_end(self):
        updated, changed = inject_html("<html><head><title>X</title></head><body></body></html>")
        self.assertTrue(changed)
        self.assertIn('/assets/site-theme.css', updated)
        self.assertIn(f'/assets/site-theme.css?v={THEME_VERSION}', updated)
        self.assertIn('/assets/site-theme.js', updated)
        self.assertLess(updated.index('/assets/site-theme.js'), updated.index('</head>'))

    def test_is_idempotent(self):
        once, _ = inject_html("<html><head></head><body></body></html>")
        twice, changed = inject_html(once)
        self.assertFalse(changed)
        self.assertEqual(once, twice)

    def test_upgrades_unversioned_theme_link(self):
        original = '<html><head><link rel="stylesheet" href="/assets/site-theme.css"><script src="/assets/site-theme.js"></script></head></html>'
        updated, changed = inject_html(original)
        self.assertTrue(changed)
        self.assertIn(f'/assets/site-theme.css?v={THEME_VERSION}', updated)

    def test_skips_fragments_without_head(self):
        original = "<section>Fragment</section>"
        updated, changed = inject_html(original)
        self.assertFalse(changed)
        self.assertEqual(original, updated)


if __name__ == "__main__":
    unittest.main()


def test_inject_html_adds_and_refreshes_build_signature():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from scripts.inject_global_theme_assets import inject_html

    first = datetime(2026, 10, 1, 14, 3, tzinfo=ZoneInfo("America/New_York"))
    second = datetime(2026, 10, 1, 14, 9, tzinfo=ZoneInfo("America/New_York"))
    html = "<html><head></head><body><main>hello</main></body></html>"
    stamped, changed = inject_html(html, now=first)
    assert changed is True
    assert 'class="page-build-signature"' in stamped
    assert "✦ Page build 2026-10-01 14:03 EDT" in stamped
    refreshed, changed_again = inject_html(stamped, now=second)
    assert changed_again is True
    assert refreshed.count('class="page-build-signature"') == 1
    assert "✦ Page build 2026-10-01 14:09 EDT" in refreshed
