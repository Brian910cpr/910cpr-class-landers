import unittest
from scripts.audit_public_sitemap import inspect_sitemap


def xml(urls):
    return ('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>' + u + '</loc></url>' for u in urls) + '</urlset>').encode()


class SitemapEvidenceTests(unittest.TestCase):
    def test_duplicates_private_and_foreign_are_counted_without_emitting_urls(self):
        report, _ = inspect_sitemap(xml(['https://www.910cpr.com/admin/secret.html'] * 2 + ['http://example.org/x']))
        self.assertEqual(report['duplicate_count'], 1)
        self.assertEqual(report['categories']['private_path'], 2)
        self.assertEqual(report['categories']['foreign_or_insecure'], 1)
        self.assertNotIn('secret', str(report))

    def test_unknown_dates_remain_absent(self):
        report, _ = inspect_sitemap(xml(['https://www.910cpr.com/bls.html']))
        self.assertEqual(report['lastmod_count'], 0)
        self.assertEqual(report['unique_url_count'], 1)

    def test_wrong_document_rejected(self):
        with self.assertRaises(ValueError):
            inspect_sitemap(b'<html/>')
