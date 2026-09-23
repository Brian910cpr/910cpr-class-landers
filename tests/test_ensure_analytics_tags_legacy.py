from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.ensure_analytics_tags import audit_html, ensure_analytics_tag


class LegacyAnalyticsTagTests(unittest.TestCase):
    def test_normalizes_unwrapped_legacy_gtm_without_duplication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.html"
            path.write_text(
                """<html><head>
<!-- Google Tag Manager --><script>(function(w,d,s,l,i){var f=d.getElementsByTagName(s)[0],j=d.createElement(s);j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','GTM-PQS8DCBH');</script>
<script src="/assets/analytics-attribution.js?v=20260912-1" defer></script>
</head><body><noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-PQS8DCBH" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript><main>Legacy page</main></body></html>""",
                encoding="utf-8",
            )

            self.assertTrue(ensure_analytics_tag(path))
            text = path.read_text(encoding="utf-8")
            self.assertEqual(audit_html(path).status, "ok")
            self.assertEqual(text.count("googletagmanager.com/gtm.js"), 1)
            self.assertEqual(text.count("googletagmanager.com/ns.html?id=GTM-PQS8DCBH"), 1)

            self.assertFalse(ensure_analytics_tag(path))
            self.assertEqual(audit_html(path).status, "ok")


if __name__ == "__main__":
    unittest.main()
