"""Focused, read-only checks for the CBPT community landing page."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Tags(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class CBPTLandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / 'docs/cbpt.html').read_text()
        cls.tags = Tags(cls.html).tags

    def test_event_metadata_matches_page(self):
        schema = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', self.html, re.S)[1])
        self.assertEqual(schema['startDate'], '2026-12-06T13:00:00-05:00')
        self.assertEqual(schema['endDate'], '2026-12-06T15:00:00-05:00')
        self.assertEqual(schema['url'], 'https://www.910cpr.com/cbpt')
        self.assertEqual(schema['location']['name'], 'Carolina Beach Physical Therapy')
        self.assertEqual(schema['location']['address']['postalCode'], '28428')
        self.assertNotIn('offers', schema)  # No unconfirmed inventory claim.

    def test_no_pool_registration_or_capacity_promise(self):
        for stale in ('2027', 'Earl Jackson', 'nseaswim', '/pool', '30 people', 'public-event-registration'):
            self.assertNotIn(stale.lower(), self.html.lower())
        self.assertFalse(any(tag == 'form' for tag, _ in self.tags))
        self.assertIn('Online seat reservations are not yet available', self.html)
        self.assertIn('No certification card is issued', self.html)

    def test_partner_images_are_decodable_formats(self):
        images = [a['src'] for tag, a in self.tags if tag == 'img']
        self.assertEqual(len(images), 6)  # Header, four partners, AHA.
        for src in images:
            data = (ROOT / 'docs' / src.lstrip('/')).read_bytes()
            self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n') or (data[:4] == b'RIFF' and data[8:12] == b'WEBP'), src)
        self.assertIn('/images/0aha.png', images)

    def test_partner_links_and_share_targets(self):
        links = [a for tag, a in self.tags if tag == 'a']
        for label in ('Carolina Beach Physical Therapy Facebook', 'The Mobile Mermaid Facebook', 'NC Mobile IV Medics Facebook'):
            self.assertTrue(any(a.get('aria-label') == label and a['href'].startswith('https://www.facebook.com/') for a in links))
        self.assertIn('Facebook link awaiting verification', self.html)
        for a in links:
            if a['href'].startswith(('sms:', 'mailto:?subject=', 'https://www.facebook.com/sharer')):
                self.assertIn('%2Fcbpt', a['href'])
        self.assertIn('href="tel:+19103955193"', self.html)

    def test_old_route_preserved(self):
        old = (ROOT / 'docs/carolinabeachpt.html').read_text()
        self.assertIn('location.replace("/cbpt" + location.search + location.hash)', old)
        redirects = (ROOT / 'docs/_redirects').read_text()
        self.assertIn('/cbpt /cbpt.html 200', redirects)
        self.assertIn('/carolinabeachpt /cbpt 301', redirects)


if __name__ == '__main__':
    unittest.main()
