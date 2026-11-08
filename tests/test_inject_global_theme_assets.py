from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.inject_global_theme_assets import THEME_VERSION, inject_html


class GlobalThemeInjectionTests(unittest.TestCase):
    def test_every_family_render_keeps_shared_theme_after_rebuild(self):
        from scripts.block_start_time_selector import load_block_schedule_page_configs
        from scripts.build_bls_block_schedule_pilot import render_html

        for key, config in load_block_schedule_page_configs().items():
            with self.subTest(family=key), patch(
                "scripts.build_bls_block_schedule_pilot.load_course_descriptions", return_value={}
            ), patch(
                "scripts.build_bls_block_schedule_pilot.asset_url", side_effect=lambda path: path
            ), patch(
                "scripts.build_bls_block_schedule_pilot.hero_markup", return_value=""
            ), patch(
                "scripts.build_bls_block_schedule_pilot.render_from_schedule", return_value=""
            ):
                rendered = render_html({"pageKey": key, "pageConfig": config, "dates": [], "counts": {}})
                self.assertEqual(rendered.count('/assets/site-theme.js'), 1)
                self.assertEqual(rendered.count(f'/assets/site-theme.css?v={THEME_VERSION}'), 1)
                self.assertLess(rendered.index('/assets/site-theme.js'), rendered.index('</head>'))
                self.assertLess(rendered.index('</style>'), rendered.index('/assets/site-theme.css'))

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
