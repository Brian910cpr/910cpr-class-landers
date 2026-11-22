"""Synthetic negative public-surface replay privacy regression."""
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from scripts import verify_replayed_public_privacy as privacy


class PublicReplayPrivacyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.details = self.root / "docs/classes"
        self.details.mkdir(parents=True)
        (self.root / "docs/sitemap.xml").write_text("<urlset></urlset>", encoding="utf-8")
        self.public = {"session_id": "111", "public": True, "start_at": (datetime.now(privacy.catalog.LOCAL_TZ) + timedelta(days=2)).isoformat()}
        self.private = {"session_id": "222", "public": False}
        self.uuid = {"session_id": "private-uuid", "public": False}

    def run_verify(self):
        rows = [self.public, self.private, self.uuid]
        with patch.object(privacy.catalog, "load_schedule_future_sessions", return_value=rows), \
             patch.object(privacy.catalog, "schedule_future_to_public_session", side_effect=lambda row: row if row["public"] else None):
            return privacy.verify(self.root)

    def test_redacted_private_page_and_independent_public_page_pass(self):
        (self.details / "index.html").write_text(
            '<a class="class-finder-secondary" href="/classes/111.html">Details</a>',
            encoding="utf-8",
        )
        (self.details / "111.html").write_text("Current public class only", encoding="utf-8")
        (self.details / "222.html").write_text(
            '<meta name="robots" content="noindex,nofollow"><h1>This class is not publicly listed</h1>',
            encoding="utf-8",
        )
        self.assertEqual(self.run_verify(), {
            "public_detail_count": 1,
            "rejected_source_identity_count": 2,
            "redacted_numeric_detail_count": 1,
        })

    def test_rejects_private_in_related_card_and_direct_page(self):
        (self.details / "index.html").write_text(
            '<a class="class-finder-secondary" href="/classes/111.html">Details</a>',
            encoding="utf-8",
        )
        (self.details / "111.html").write_text(
            '<div data-session-id="private-uuid">Hidden appointment</div>',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "nonpublic identity leaked"):
            self.run_verify()
        (self.details / "111.html").write_text("Current public class only", encoding="utf-8")
        (self.details / "222.html").write_text("Old private class and enrollment link", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "direct detail not redacted"):
            self.run_verify()
        (self.details / "222.html").write_text(
            '<meta name="robots" content="noindex,nofollow"><h1>This class is not publicly listed</h1>',
            encoding="utf-8",
        )
        (self.root / "docs/sitemap.xml").write_text(
            "<urlset><url><loc>https://www.910cpr.com/classes/222.html</loc></url></urlset>",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "nonpublic sitemap discovery"):
            self.run_verify()


if __name__ == "__main__":
    unittest.main()
