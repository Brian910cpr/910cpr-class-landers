import json
import re
import tempfile
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scripts import build_date_availability_pages as builder


class DateAvailabilityPagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.counts = builder.build(cls.root, date(2026, 7, 24))
        cls.pages = sorted(cls.root.rglob("*.html"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_generates_date_pages_not_time_pages(self):
        self.assertGreater(self.counts["date_pages_generated"], 0)
        self.assertTrue(all(re.search(r"/\d{4}-\d{2}-\d{2}\.html$", p.as_posix()) for p in self.pages))

    def test_appointment_links_preserve_resolved_identifiers(self):
        checked = 0
        for path in self.pages:
            html = path.read_text(encoding="utf-8")
            for url in re.findall(r'href="([^"]*appointmentDayId[^"]+)"', html):
                query = parse_qs(urlparse(url.replace("&amp;", "&")).query)
                self.assertTrue(query["appointmentDayId"][0])
                self.assertTrue(query["startTime"][0])
                self.assertTrue(query["courseId"][0])
                checked += 1
        self.assertGreater(checked, 0)

    def test_schema_and_event_boundary(self):
        anchored = 0
        for path in self.pages:
            html = path.read_text(encoding="utf-8")
            schema = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html).group(1))
            types = [node.get("@type") for node in schema["@graph"]]
            self.assertIn("BreadcrumbList", types)
            self.assertIn(["Organization", "LocalBusiness"], types)
            has_seated = 'data-page-state="anchored"' in html or 'data-page-state="full"' in html
            has_event = "Event" in types
            self.assertEqual(has_event, has_seated)
            anchored += int(has_seated)
        self.assertGreater(anchored, 0)

    def test_one_gtm_and_unique_metadata(self):
        titles = set()
        descriptions = set()
        for path in self.pages:
            html = path.read_text(encoding="utf-8")
            self.assertEqual(html.count("googletagmanager.com/gtm.js"), 1)
            self.assertEqual(html.count("googletagmanager.com/ns.html?id=GTM-PQS8DCBH"), 1)
            self.assertEqual(html.count('rel="canonical"'), 1)
            titles.add(re.search(r"<title>(.*?)</title>", html).group(1))
            descriptions.add(re.search(r'<meta name="description" content="([^"]+)"', html).group(1))
        self.assertEqual(len(titles), len(self.pages))
        self.assertEqual(len(descriptions), len(self.pages))

    def test_no_pii_in_analytics_payload(self):
        for path in self.pages:
            html = path.read_text(encoding="utf-8").lower()
            self.assertNotIn('"student_name"', html)
            self.assertNotIn('"student_email"', html)
            self.assertNotIn('"student_phone"', html)

    def test_full_and_expired_state_rendering(self):
        closed = {
            "page_key": "bls", "city": "Wilmington", "date": "2026-08-12",
            "display_date": "Wednesday, August 12, 2026", "offers": [],
            "real_sessions": [{
                "session_id": "123", "course_name": "AHA BLS Provider",
                "start_at": "2026-08-12T12:30:00-04:00", "end_at": "2026-08-12T14:30:00-04:00",
                "location_display": ":: Wilmington; Shipyard Blvd - B",
                "registration_url": "https://coastalcprtraining.enrollware.com/enroll?id=123",
                "registration_status": "closed", "public_direct_booking": False, "registered_count": 6,
            }],
        }
        _, full_html = builder.render(closed, [], date(2026, 8, 1), "test")
        self.assertIn('data-page-state="full"', full_html)
        self.assertIn('"@type":"Event"', full_html)
        _, expired_html = builder.render(closed, [], date(2026, 8, 13), "test")
        self.assertIn('data-page-state="expired"', expired_html)
        self.assertIn("have concluded", expired_html)
        self.assertIn("View upcoming dates", expired_html)


if __name__ == "__main__":
    unittest.main()
