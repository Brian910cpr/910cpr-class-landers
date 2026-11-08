"""Regression guards for shared dark surfaces and WCAG color pairs.

These are source/palette checks, not a substitute for rendered browser QA.
"""
import re
import unittest
from pathlib import Path
from scripts.inject_global_theme_assets import THEME_VERSION, inject_html

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "docs/assets/site-theme.css").read_text(encoding="utf-8")
JS = (ROOT / "docs/assets/site-theme.js").read_text(encoding="utf-8")

def luminance(color):
    channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    linear = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in channels]
    return sum(x * weight for x, weight in zip(linear, (.2126, .7152, .0722)))

def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + .05) / (lo + .05)

class SiteThemeContrastTests(unittest.TestCase):
    def test_unclassed_surfaces_share_the_card_palette(self):
        selector, declarations = next((s, d) for s, d in re.findall(r"([^{}]+)\{([^{}]+)\}", CSS) if "section:not([class])" in s)
        self.assertIn('html[data-theme="dark"]', selector)
        for surface in ('article:not([class])', 'fieldset', '.card'):
            self.assertIn(surface, selector)
        self.assertIn('background: #111a27 !important', declarations)
        self.assertIn('color: #e8eef6 !important', declarations)

    def test_dark_text_pairs_meet_wcag_aa(self):
        for fg, bg in [('#e8eef6','#111a27'),('#f5f8fc','#111a27'),('#b9c6d5','#111a27'),('#83cbfa','#111a27'),('#eef5fc','#172334'),('#b9c6d5','#172334'),('#9ce1c2','#111a27'),('#ffb4b8','#111a27')]:
            with self.subTest(foreground=fg, background=bg):
                self.assertIn(fg, CSS)
                self.assertGreaterEqual(contrast(fg,bg), 4.5)

    def test_focus_indicator_contrasts_with_dark_controls(self):
        self.assertGreaterEqual(contrast('#ffd166', '#172334'), 3)
        self.assertIn('outline: 3px solid #ffd166 !important', CSS)

    def test_runtime_and_generator_versions_match(self):
        self.assertIn('const themeVersion = "' + THEME_VERSION + '"', JS)
        self.assertIn('url.origin === location.origin', JS)
        self.assertIn('url.pathname === "/assets/site-theme.css"', JS)

    def test_old_generated_page_gets_current_version(self):
        original = '<head><link rel="stylesheet" href="/assets/site-theme.css?v=20260818.5"><script src="/assets/site-theme.js"></script></head>'
        updated, changed = inject_html(original)
        self.assertTrue(changed)
        self.assertIn('site-theme.css?v=' + THEME_VERSION, updated)
        self.assertFalse(inject_html(updated)[1])

if __name__ == "__main__":
    unittest.main()
