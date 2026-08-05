from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.audit_global_page_requirements import audit_page
from scripts.global_page_requirements import Exclusion, enforce_html, process_path


BASE = "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Test</title></head><body>Hi</body></html>"


class GlobalPageRequirementsTests(unittest.TestCase):
    def test_duplicate_doctype_after_build_marker_is_normalized(self):
        source = "<!-- BUILD_CODE: test -->\n<!DOCTYPE html>\n" + BASE
        output = enforce_html(source, Path("docs/classes/test.html"), {})
        self.assertEqual(1, len(re.findall(r"<!doctype\s+html\s*>", output, re.I)))
        self.assertTrue(output.startswith("<!doctype html>"))

    def exclusions(self):
        return {}

    def rendered(self, path: Path, source: str = BASE) -> str:
        return enforce_html(source, path, self.exclusions())

    def test_normal_public_page_passes_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            page = docs / "index.html"
            with patch("scripts.global_page_requirements.DOCS_DIR", docs):
                first = enforce_html(BASE, page, {})
                second = enforce_html(first, page, {})
            self.assertEqual(first, second)
            self.assertEqual(first.count("googletagmanager.com/gtm.js"), 1)
            self.assertEqual(first.count("favicon.svg"), 1)

    def test_duplicate_analytics_is_repaired(self):
        source = BASE.replace("</head>", "<!-- Google Tag Manager --><script src='https://www.googletagmanager.com/gtm.js?id=GTM-PQS8DCBH'></script><!-- End Google Tag Manager --></head>")
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"; docs.mkdir(); page = docs / "x.html"
            with patch("scripts.global_page_requirements.DOCS_DIR", docs):
                result = enforce_html(source, page, {})
            self.assertEqual(result.count("googletagmanager.com/gtm.js"), 1)

    def test_audit_detects_missing_favicon_analytics_wrong_id_and_duplicate_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "bad.html"
            page.write_text("<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Bad</title><link rel='canonical' href='https://github.io/a'><link rel='canonical' href='https://github.io/b'><script>GTM-WRONG</script></head><body></body></html>", encoding="utf-8")
            failures = audit_page(page, {})
            joined = "\n".join(failures)
            self.assertIn("favicon", joined)
            self.assertIn("GTM head loader", joined)
            self.assertIn("GTM-WRONG", joined)
            self.assertIn("expected one canonical", joined)

    def test_documented_redirect_exclusion_passes_canonical_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "redirect.html"
            page.write_text(BASE, encoding="utf-8")
            key = page.resolve().as_posix()
            exclusion = Exclusion(key, "Redirect", frozenset({"canonical"}))
            with patch("scripts.audit_global_page_requirements.canonical_excluded", return_value=True):
                failures = audit_page(page, {key: exclusion})
            self.assertFalse(any("canonical" in item for item in failures))

    def test_processing_twice_does_not_duplicate_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"; docs.mkdir(); page = docs / "generated.html"
            page.write_text(BASE, encoding="utf-8")
            with patch("scripts.global_page_requirements.DOCS_DIR", docs):
                self.assertTrue(process_path(page, {}))
                first = page.read_text(encoding="utf-8")
                self.assertFalse(process_path(page, {}))
            self.assertEqual(first, page.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
