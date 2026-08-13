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
        resolved_urls = set()
        for artifact in builder.ARTIFACTS.glob("*.json"):
            payload = json.loads(artifact.read_text(encoding="utf-8"))
            for day in payload.get("dates", []):
                for slot in day.get("startTimes", []):
                    for offer in slot.get("courses", []):
                        if offer.get("publicSelectable") and offer.get("appointmentUrl"):
                            resolved_urls.add(str(offer["appointmentUrl"]))
        checked = 0
        for path in self.pages:
            html = path.read_text(encoding="utf-8")
            for url in re.findall(r'href="([^"]*appointmentDayId[^"]+)"', html):
                raw_url = url.replace("&amp;", "&")
                query = parse_qs(urlparse(raw_url).query)
                self.assertTrue(query["appointmentDayId"][0])
                self.assertTrue(query["startTime"][0])
                self.assertTrue(query["courseId"][0])
                self.assertIn(raw_url, resolved_urls)
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

    def test_open_page_hero_routes_to_course_family_without_preselecting(self):
        open_pages = [
            path for path in self.pages
            if "/arc/" in path.as_posix()
            and 'data-page-state="open"' in path.read_text(encoding="utf-8")
        ]
        self.assertTrue(open_pages)
        html = open_pages[0].read_text(encoding="utf-8")
        hero = re.search(r'<section class="hero">(.*?)</section>', html, re.DOTALL).group(1)
        self.assertIn('href="/arc.html"', hero)
        self.assertIn("Choose your course", hero)
        self.assertNotIn("data-registration", hero)
        self.assertNotIn("appointmentDayId", hero)

    def test_generates_exact_course_date_pages_from_route_config(self):
        exact = self.root / "aha-bls-provider" / "wilmington" / "2026-08-12.html"
        self.assertTrue(exact.exists())
        html = exact.read_text(encoding="utf-8")
        self.assertIn("<h1>AHA BLS Provider</h1>", html)
        self.assertNotIn("AHA HeartCode BLS</span>", html)
        self.assertNotIn("AHA BLS Provider Renewal</span>", html)
        self.assertNotIn('id="course-option-filter"', html)

    def test_course_routes_are_backed_by_confirmed_resolved_course_ids(self):
        routes = builder.load_course_routes()
        artifact_ids = set()
        for path in builder.ARTIFACTS.glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            family = str(payload.get("pageKey") or path.stem)
            for day in payload.get("dates", []):
                for slot in day.get("startTimes", []):
                    for offer in slot.get("courses", []):
                        if offer.get("publicSelectable"):
                            artifact_ids.add((family, str(offer.get("courseId") or "")))
        for route in routes:
            self.assertIn((route["family_key"], route["course_id"]), artifact_ids)

    def test_detected_course_delivery_filter_uses_resolved_offers(self):
        filtered_pages = []
        for path in self.pages:
            html = path.read_text(encoding="utf-8")
            if 'id="course-option-filter"' not in html:
                continue
            filtered_pages.append(path)
            self.assertIn('<option value="all">All course options</option>', html)
            option_keys = set(re.findall(r'<option value="(course-[^"]+)"', html))
            card_keys = set(re.findall(r'data-course-option="(course-[^"]+)"', html))
            self.assertEqual(option_keys, card_keys)
            self.assertNotRegex(html, r'>\s*\d{5,}\s*</option>')
            self.assertFalse(any(re.fullmatch(r"course-\d+", key) for key in option_keys))
        self.assertTrue(filtered_pages)

    def test_filter_assets_are_versioned_together(self):
        for path in self.pages:
            html = path.read_text(encoding="utf-8")
            self.assertIn('/css/date-availability.css?v=20260725', html)
            self.assertIn('/assets/date-availability.js?v=20260725', html)

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

    def test_prior_date_pages_are_rerendered_as_expired(self):
        original_manifest = builder.MANIFEST
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                manifest = root / "manifest.json"
                manifest.write_text(json.dumps({
                    "pages": [{
                        "path": "/bls/wilmington/2026-07-23.html",
                        "state": "full",
                        "page_key": "bls",
                        "family_key": "bls",
                        "page_type": "family_date",
                        "city": "Wilmington",
                        "date": "2026-07-23",
                    }]
                }), encoding="utf-8")
                builder.MANIFEST = manifest
                builder.build(root, date(2026, 7, 24))
                html = (root / "bls" / "wilmington" / "2026-07-23.html").read_text(encoding="utf-8")
                self.assertIn('data-page-state="expired"', html)
                self.assertIn("have concluded", html)
        finally:
            builder.MANIFEST = original_manifest


if __name__ == "__main__":
    unittest.main()
