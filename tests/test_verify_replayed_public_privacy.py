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
            "redacted_uuid_detail_count": 0,
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


    def test_private_uuid_detail_and_sitemap_are_not_public(self):
        # A canonical UUID is a real session identity too. Public finder links
        # are numeric today, but old directly addressable UUID files must not
        # leak private times or remain discoverable via sitemap.
        sid = "22222222-2222-4222-8222-222222222222"
        self.uuid["session_id"] = sid
        (self.details / "index.html").write_text(
            '<a class="class-finder-secondary" href="/classes/111.html">Details</a>',
            encoding="utf-8",
        )
        (self.details / "111.html").write_text("Public detail", encoding="utf-8")
        direct = self.details / (sid + ".html")
        direct.write_text("Private appointment details", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "nonpublic direct detail not redacted"):
            self.run_verify()
        direct.write_text(
            '<meta name="robots" content="noindex,nofollow">'
            '<h1>This class is not publicly listed</h1>', encoding="utf-8",
        )
        (self.root / "docs/sitemap.xml").write_text(
            "<urlset><url><loc>https://www.910cpr.com/classes/" + sid
            + ".html</loc></url></urlset>", encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "nonpublic sitemap discovery"):
            self.run_verify()
        (self.root / "docs/sitemap.xml").write_text("<urlset></urlset>", encoding="utf-8")
        result = self.run_verify()
        self.assertEqual(result["redacted_uuid_detail_count"], 1)
        self.assertEqual(result["redacted_numeric_detail_count"], 0)

    def test_archive_link_to_known_private_class_blocks_publication(self):
        (self.details / "index.html").write_text(
            '<a class="class-finder-secondary" href="/classes/111.html">Details</a>',
            encoding="utf-8",
        )
        (self.details / "111.html").write_text("Verified public detail", encoding="utf-8")
        archive = self.root / "docs/topics/bls.html"
        archive.parent.mkdir(parents=True)
        archive.write_text(
            '<a href="/classes/222.html">An old class listing</a>', encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "archived index links to nonpublic"):
            self.run_verify()
        archive.write_text(
            '<a href="/classes/index.html">Browse current classes</a>', encoding="utf-8"
        )
        self.assertEqual(self.run_verify()["public_detail_count"], 1)

    def test_source_absent_tombstone_cannot_stay_in_sitemap_or_archive(self):
        (self.details / "index.html").write_text(
            '<a class="class-finder-secondary" href="/classes/111.html">Details</a>',
            encoding="utf-8",
        )
        (self.details / "111.html").write_text("Verified public detail", encoding="utf-8")
        # This retired identity is NOT in the current source rows; its noindex
        # tombstone still establishes that this URL must not be advertised.
        (self.details / "333.html").write_text(
            '<meta name="robots" content="noindex,nofollow">'
            '<h1>This class is not publicly listed</h1>', encoding="utf-8"
        )
        sitemap = self.root / "docs/sitemap.xml"
        sitemap.write_text(
            "<urlset><url><loc>https://www.910cpr.com/classes/333.html"
            "</loc></url></urlset>", encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "tombstoned identity in sitemap"):
            self.run_verify()
        sitemap.write_text("<urlset></urlset>", encoding="utf-8")
        archive = self.root / "docs/topics/bls.html"
        archive.parent.mkdir(parents=True)
        archive.write_text(
            "<a href='/classes/333.html'>Old class</a>", encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "archived index links to nonpublic"):
            self.run_verify()
        archive.write_text(
            "<a href='/bls.html'>View current BLS classes</a>", encoding="utf-8"
        )
        self.assertEqual(self.run_verify()["public_detail_count"], 1)

if __name__ == "__main__":
    unittest.main()
