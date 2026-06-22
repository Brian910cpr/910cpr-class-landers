from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import build_index
from scripts.stale_class_link_fallbacks import infer_current_public_destination, safe_class_detail_href


class StaleClassLinkFallbackTest(unittest.TestCase):
    def test_infers_current_hub_destinations(self) -> None:
        self.assertEqual("/bls.html", infer_current_public_destination("AHA BLS Provider"))
        self.assertEqual("/acls.html", infer_current_public_destination("ACLS Renewal"))
        self.assertEqual("/pals.html", infer_current_public_destination("PALS Provider"))
        self.assertEqual("/heartsaver.html", infer_current_public_destination("Heartsaver First Aid CPR AED"))
        self.assertEqual("/arc.html", infer_current_public_destination("Red Cross BLS"))
        self.assertEqual("/hsi.html", infer_current_public_destination("ASHI CPR AED"))
        self.assertEqual("/uscg-elementary-first-aid-cpr.html", infer_current_public_destination("USCG Elementary First Aid"))
        self.assertEqual("/group-training.html", infer_current_public_destination("onsite workplace group training"))
        self.assertEqual("/classes/", infer_current_public_destination("misc archive item"))

    def test_existing_numeric_class_page_is_kept(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir)
            classes_dir = docs_dir / "classes"
            classes_dir.mkdir()
            (classes_dir / "12345.html").write_text("<html></html>", encoding="utf-8")

            self.assertEqual(
                "/classes/12345.html",
                safe_class_detail_href("12345", docs_dir, "AHA BLS Provider"),
            )

    def test_missing_numeric_class_page_falls_back_to_hub(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir)
            (docs_dir / "classes").mkdir()

            self.assertEqual(
                "/bls.html",
                safe_class_detail_href("99999", docs_dir, "AHA BLS Provider"),
            )
            self.assertEqual(
                "/classes/",
                safe_class_detail_href("99999", docs_dir, "Class Location TBA"),
            )

    def test_build_index_format_session_line_does_not_emit_missing_numeric_class_link(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            original_docs_dir = build_index.DOCS_DIR
            try:
                docs_dir = Path(temp_dir)
                (docs_dir / "classes").mkdir()
                build_index.DOCS_DIR = docs_dir

                line = build_index.format_session_line({
                    "session_id": "99999",
                    "course_name": "AHA BLS Provider",
                    "start_at": "2026-07-01T09:00:00-04:00",
                    "location_name": "Wilmington",
                })

                self.assertIn('href="/bls.html"', line)
                self.assertNotIn("/classes/99999.html", line)
            finally:
                build_index.DOCS_DIR = original_docs_dir


if __name__ == "__main__":
    unittest.main()
