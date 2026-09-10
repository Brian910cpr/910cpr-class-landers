from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import audit_sitewide_links
from scripts import validate_sitewide_links_strict


class StrictLinkAuditTests(unittest.TestCase):
    def test_missing_internal_target_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            debug = root / "debug"
            docs.mkdir()
            debug.mkdir()
            (docs / "index.html").write_text(
                '<!doctype html><html><body><a href="/missing.html">Missing target</a></body></html>',
                encoding="utf-8",
            )
            csv_path = debug / "sitewide_link_button_audit.csv"
            md_path = debug / "sitewide_link_button_audit.md"

            with (
                patch.object(audit_sitewide_links, "ROOT", root),
                patch.object(audit_sitewide_links, "DOCS_DIR", docs),
                patch.object(audit_sitewide_links, "DEBUG_DIR", debug),
                patch.object(audit_sitewide_links, "CSV_PATH", csv_path),
                patch.object(audit_sitewide_links, "MD_PATH", md_path),
            ):
                rc = validate_sitewide_links_strict.main()

            self.assertEqual(rc, 1)
            self.assertTrue(csv_path.exists())
            self.assertTrue(md_path.exists())

            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))

            broken = [row for row in rows if row.get("status") == "BROKEN"]
            self.assertEqual(len(broken), 1)
            self.assertEqual(broken[0].get("normalized_destination"), "/missing.html")
            self.assertIn("BROKEN", md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
