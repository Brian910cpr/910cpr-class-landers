from pathlib import Path
import tempfile
import unittest
from scripts.audit_growth_inventory import audit


class GrowthInventoryAuditTests(unittest.TestCase):
    def test_counts_families_and_detects_missing_local_targets_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / 'docs'
            (docs / 'topics').mkdir(parents=True)
            (docs / 'topics' / 'cpr.html').write_text('<html>CPR</html>')
            (docs / 'index.html').write_text('<html>Home</html>')
            sitemap = docs / 'sitemap.xml'
            sitemap.write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://www.910cpr.com/topics/cpr.html</loc></url><url><loc>https://www.910cpr.com/missing.html</loc></url><url><loc>https://www.910cpr.com/missing.html</loc></url></urlset>')
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            result = audit(root)
            self.assertEqual(result['families'], {'(root)': 1, 'topics': 1})
            self.assertEqual(result['missing_sitemap_targets'], ['https://www.910cpr.com/missing.html'])
            self.assertEqual(result['sitemaps'][0]['duplicate_entries'], 1)
            self.assertEqual(before, {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
