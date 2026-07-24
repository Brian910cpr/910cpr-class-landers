from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SELECTOR_PAGES = (
    "docs/acls.html",
    "docs/arc.html",
    "docs/bls.html",
    "docs/courses/uscg-first-aid-cpr-aed.html",
    "docs/heartsaver.html",
    "docs/hsi.html",
    "docs/pals.html",
    "docs/uscg-elementary-first-aid-cpr.html",
)


class SelectorMobileProgressionTests(unittest.TestCase):
    def test_all_selector_pages_advance_to_the_next_required_action(self):
        for relative_path in SELECTOR_PAGES:
            html = (ROOT / relative_path).read_text(encoding="utf-8")
            with self.subTest(page=relative_path):
                self.assertIn("function scrollToNextStep(targetId)", html)
                self.assertIn("if (!isMobileLayout())", html)
                self.assertIn("prefers-reduced-motion: reduce", html)
                self.assertIn("scrollToNextStep('date-list')", html)
                self.assertIn("scrollToNextStep('start-list')", html)
                self.assertIn("scrollToNextStep('course-list')", html)

    def test_authoritative_builder_contains_the_same_progression(self):
        builder = (ROOT / "scripts/build_bls_block_schedule_pilot.py").read_text(encoding="utf-8")
        self.assertIn("function scrollToNextStep(targetId)", builder)
        self.assertIn("scrollToNextStep('date-list')", builder)
        self.assertIn("scrollToNextStep('start-list')", builder)
        self.assertIn("scrollToNextStep('course-list')", builder)


if __name__ == "__main__":
    unittest.main()
