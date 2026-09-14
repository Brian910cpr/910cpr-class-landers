from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import retire_expired_public_pages as maintenance


class RetireExpiredPublicPagesTests(unittest.TestCase):
    def test_prunes_only_links_to_noindex_class_pages(self):
        with TemporaryDirectory() as temp:
            output = Path(temp)
            (output / "1.html").write_text('<meta name="robots" content="noindex,follow">', encoding="utf-8")
            (output / "2.html").write_text('<meta name="robots" content="index,follow">', encoding="utf-8")
            page = output / "3.html"
            page.write_text(
                '<aside class="current-courses-sidebar"><ul>'
                '<li><a href="/classes/1.html"><strong>Past</strong></a></li>'
                '<li><a href="/classes/2.html"><strong>Future</strong></a></li>'
                '</ul></aside>',
                encoding="utf-8",
            )
            with patch.object(maintenance, "OUTPUT_DIR", output):
                retired = maintenance.retired_class_ids()
                changed = maintenance.prune_retired_sidebar_links(retired)
            self.assertEqual({"1"}, retired)
            self.assertEqual(1, changed)
            rendered = page.read_text(encoding="utf-8")
            self.assertNotIn('/classes/1.html', rendered)
            self.assertIn('/classes/2.html', rendered)

    def test_removes_empty_sidebar(self):
        with TemporaryDirectory() as temp:
            output = Path(temp)
            page = output / "3.html"
            page.write_text(
                '<main>Keep</main><aside class="current-courses-sidebar"><ul>'
                '<li><a href="/classes/1.html"><strong>Past</strong></a></li>'
                '</ul></aside>',
                encoding="utf-8",
            )
            with patch.object(maintenance, "OUTPUT_DIR", output):
                changed = maintenance.prune_retired_sidebar_links({"1"})
            self.assertEqual(1, changed)
            self.assertEqual('<main>Keep</main>', page.read_text(encoding="utf-8"))

    def test_prunes_only_retired_class_urls_from_existing_sitemap(self):
        with TemporaryDirectory() as temp:
            sitemap = Path(temp) / "sitemap.xml"
            sitemap.write_text(
                '<urlset>\n'
                '<url><loc>https://www.910cpr.com/</loc></url>\n'
                '<url><loc>https://www.910cpr.com/classes/1.html</loc></url>\n'
                '<url><loc>https://www.910cpr.com/classes/2.html</loc></url>\n'
                '</urlset>\n',
                encoding="utf-8",
            )
            with patch.object(maintenance, "SITEMAP_PATH", sitemap):
                removed = maintenance.prune_retired_sitemap_urls({"1"})
            rendered = sitemap.read_text(encoding="utf-8")
            self.assertEqual(1, removed)
            self.assertIn('https://www.910cpr.com/', rendered)
            self.assertNotIn('/classes/1.html', rendered)
            self.assertIn('/classes/2.html', rendered)


if __name__ == "__main__":
    unittest.main()
