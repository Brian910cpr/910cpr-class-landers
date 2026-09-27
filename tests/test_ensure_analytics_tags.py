from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.ensure_analytics_tags import (
    ANALYTICS_EXCLUSION_COOKIE,
    ATTRIBUTION_SCRIPT_SRC,
    GTM_ID,
    audit_html,
    ensure_analytics_tag,
)


class EnsureAnalyticsTagsTests(unittest.TestCase):
    def test_repository_analytics_preference_is_tag_free_and_reversible(self) -> None:
        path = Path(__file__).resolve().parents[1] / "docs" / "internal" / "analytics-preferences.html"
        text = path.read_text(encoding="utf-8")

        self.assertEqual(audit_html(path).status, "internal_clean")
        self.assertIn("${COOKIE}=1", text)
        self.assertIn("Max-Age=0", text)
        self.assertIn("ga-disable-", text)

    def test_inserts_head_and_noscript_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.html"
            path.write_text("<html><head><title>Test</title></head><body><main>Hi</main></body></html>", encoding="utf-8")

            self.assertTrue(ensure_analytics_tag(path))
            first = path.read_text(encoding="utf-8")
            self.assertIn(GTM_ID, first)
            self.assertIn(ANALYTICS_EXCLUSION_COOKIE, first)
            self.assertIn(ATTRIBUTION_SCRIPT_SRC, first)
            self.assertEqual(audit_html(path).status, "ok")

            self.assertFalse(ensure_analytics_tag(path))
            second = path.read_text(encoding="utf-8")
            self.assertEqual(first, second)
            self.assertEqual(first.count("googletagmanager.com/gtm.js"), 1)
            self.assertEqual(first.count("googletagmanager.com/ns.html?id=GTM-PQS8DCBH"), 1)
            self.assertEqual(first.count("/assets/analytics-attribution.js"), 1)

    def test_deduplicates_existing_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.html"
            duplicate = """<html><head>
<!-- Google Tag Manager --><script src="https://www.googletagmanager.com/gtm.js?id=GTM-PQS8DCBH"></script><!-- End Google Tag Manager -->
<!-- Google Tag Manager --><script src="https://www.googletagmanager.com/gtm.js?id=GTM-PQS8DCBH"></script><!-- End Google Tag Manager -->
</head><body>
<!-- Google Tag Manager (noscript) --><noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-PQS8DCBH"></iframe></noscript><!-- End Google Tag Manager (noscript) -->
</body></html>"""
            path.write_text(duplicate, encoding="utf-8")

            self.assertTrue(ensure_analytics_tag(path))
            text = path.read_text(encoding="utf-8")
            self.assertEqual(audit_html(path).status, "ok")
            self.assertEqual(text.count("googletagmanager.com/gtm.js"), 1)
            self.assertEqual(text.count("googletagmanager.com/ns.html?id=GTM-PQS8DCBH"), 1)

    def test_removes_tags_from_internal_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "admin" / "dashboard.html"
            path.parent.mkdir()
            path.write_text(
                "<html><head>" +
                '<!-- Google Tag Manager --><script src="https://www.googletagmanager.com/gtm.js?id=GTM-PQS8DCBH"></script><!-- End Google Tag Manager -->' +
                "</head><body>" +
                '<!-- Google Tag Manager (noscript) --><noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-PQS8DCBH"></iframe></noscript><!-- End Google Tag Manager (noscript) -->' +
                "<main>Admin</main></body></html>",
                encoding="utf-8",
            )

            self.assertEqual(audit_html(path).status, "internal_tagged")
            self.assertTrue(ensure_analytics_tag(path))
            self.assertEqual(audit_html(path).status, "internal_clean")
            self.assertNotIn("googletagmanager", path.read_text(encoding="utf-8"))

    def test_does_not_add_tags_to_untagged_internal_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "control-center" / "index.html"
            path.parent.mkdir()
            original = "<html><head></head><body><main>Internal</main></body></html>"
            path.write_text(original, encoding="utf-8")

            self.assertFalse(ensure_analytics_tag(path))
            self.assertEqual(audit_html(path).status, "internal_clean")
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_preference_page_stays_unmeasured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "analytics-preferences" / "index.html"
            path.parent.mkdir()
            path.write_text("<html><head></head><body>Preference</body></html>", encoding="utf-8")

            self.assertFalse(ensure_analytics_tag(path))
            self.assertEqual(audit_html(path).status, "internal_clean")


if __name__ == "__main__":
    unittest.main()
