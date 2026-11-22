from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LINK = '<a href="/privacy-terms/">SMS Privacy &amp; Terms</a>'
NOTICE = "Providing a phone number does not opt you in to texts."

class SmsPolicyDiscoverability(unittest.TestCase):
    def test_public_page_has_both_sections_and_only_back_link(self):
        policy = (ROOT / 'docs/privacy-terms/index.html').read_text()
        self.assertIn('id="opt-in-data"', policy)
        self.assertIn('id="sms-program"', policy)
        self.assertEqual(len(re.findall(r'<a\b', policy)), 1)
        self.assertRegex(policy, r'<a[^>]*>Back</a>')

    def test_links_remain_in_home_and_bls_generators_and_pages(self):
        for path in ('docs/index.html', 'docs/contact.html', 'docs/bls.html',
                     'scripts/build_index_and_sitemap.py', 'scripts/build_bls_block_schedule_pilot.py'):
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_text().count(LINK), 1)

    def test_phone_forms_disclose_that_providing_number_is_not_consent(self):
        for path in ('docs/group-training.html', 'docs/register/index.html',
                     'docs/register/skills-session/index.html', 'docs/register/heartsaver-skills/index.html',
                     'docs/assets/generic-checkout.js'):
            with self.subTest(path=path):
                source = (ROOT / path).read_text()
                self.assertEqual(source.count(f'{NOTICE} {LINK}'), 1)

    def test_generic_checkout_uses_updated_script(self):
        self.assertIn('generic-checkout.js?v=20261122-sms-policy',
                      (ROOT / 'docs/register/checkout/index.html').read_text())
