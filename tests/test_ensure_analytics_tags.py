from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.ensure_analytics_tags import GTM_ID, audit_html, ensure_analytics_tag


class EnsureAnalyticsTagsTests(unittest.TestCase):
    def test_inserts_head_and_noscript_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.html"
            path.write_text("<html><head><title>Test</title></head><body><main>Hi</main></body></html>", encoding="utf-8")

            self.assertTrue(ensure_analytics_tag(path))
            first = path.read_text(encoding="utf-8")
            self.assertIn(GTM_ID, first)
            self.assertEqual(audit_html(path).status, "ok")

            self.assertFalse(ensure_analytics_tag(path))
            second = path.read_text(encoding="utf-8")
            self.assertEqual(first, second)
            self.assertEqual(first.count("googletagmanager.com/gtm.js"), 1)
            self.assertEqual(first.count("googletagmanager.com/ns.html?id=GTM-PQS8DCBH"), 1)

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


if __name__ == "__main__":
    unittest.main()
