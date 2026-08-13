from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.audit_public_discovery import scan_public_language


class PublicDiscoveryAuditTests(unittest.TestCase):
    def test_customer_copy_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            docs = Path(temp)
            (docs / "classes").mkdir()
            (docs / "classes" / "1.html").write_text(
                "<h1>AHA BLS Provider — August 18 at 9:15 AM</h1>", encoding="utf-8"
            )
            self.assertEqual([], scan_public_language(docs))

    def test_internal_terms_and_build_diagnostics_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            docs = Path(temp)
            (docs / "index.html").write_text(
                '<!-- Dockmaster --><body data-build-id="x">Production Board</body>', encoding="utf-8"
            )
            terms = {row["term"] for row in scan_public_language(docs)}
            self.assertIn("Production Board", terms)
            self.assertIn("Harbor Master / Dockmaster", terms)
            self.assertIn("browser build diagnostics", terms)

    def test_admin_only_content_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            docs = Path(temp)
            (docs / "admin").mkdir()
            (docs / "admin" / "board.html").write_text("Production Board", encoding="utf-8")
            self.assertEqual([], scan_public_language(docs))


if __name__ == "__main__":
    unittest.main()
