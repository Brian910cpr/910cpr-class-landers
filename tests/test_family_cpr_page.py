from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
FAMILY = DOCS / "family-cpr.html"
FAMILY_ARTIFACT = DOCS / "data" / "block-selector-availability" / "family_cpr.json"
FAMILY_AUDIT = ROOT / "data" / "audit" / "family_cpr_block_schedule.json"


class FamilyLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.images: list[str] = []
        self.canonicals: list[str] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        if tag == "a":
            self._href = attr_map.get("href", "")
            self._text = []
        if tag == "img":
            self.images.append(attr_map.get("src", ""))
        if tag == "link" and attr_map.get("rel") == "canonical":
            self.canonicals.append(attr_map.get("href", ""))

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            text = re.sub(r"\s+", " ", " ".join(self._text)).strip()
            self.links.append((self._href, text))
            self._href = None
            self._text = []


def family_html() -> str:
    return FAMILY.read_text(encoding="utf-8")


def parsed_family() -> FamilyLinkParser:
    parser = FamilyLinkParser()
    parser.feed(family_html())
    return parser


def local_path_for_href(href: str) -> Path | None:
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc or parsed.path == "":
        return None
    path = parsed.path.lstrip("/")
    if not path:
        return DOCS / "index.html"
    if path.endswith("/"):
        path += "index.html"
    if "." not in Path(path).name:
        path += ".html"
    return DOCS / path


class FamilyCprPageTests(unittest.TestCase):
    def test_canonical_family_page_exists(self) -> None:
        html = family_html()
        self.assertIn("<h1 id=\"family-cpr-title\">Family &amp; Friends CPR</h1>", html)
        self.assertIn("Learn practical CPR skills for adults, children, and infants", html)

    def test_canonical_tag_points_to_family_cpr(self) -> None:
        self.assertEqual(["https://www.910cpr.com/family-cpr.html"], parsed_family().canonicals)

    def test_family_image_path_exists(self) -> None:
        parser = parsed_family()
        self.assertIn("/images/FF-CPR-2.jpg", parser.images)
        self.assertTrue((DOCS / "images" / "FF-CPR-2.jpg").exists())

    def test_forbidden_generated_or_internal_copy_absent(self) -> None:
        html = family_html()
        forbidden = [
            "Live course hub built from Class Report.xlsx",
            "Use this page to jump into actual upcoming sessions",
            "No upcoming public sessions are listed right now",
            "Current CPR and First Aid Focus",
            "Class Report",
            "spreadsheet",
            "Locate an AHA Training Center",
        ]
        for text in forbidden:
            with self.subTest(text=text):
                self.assertNotIn(text, html)

    def test_no_professional_certification_implication(self) -> None:
        html = family_html().lower()
        self.assertNotIn("healthcare provider", html)
        self.assertNotIn("workplace acceptance", html)
        self.assertNotIn("bls", html)
        self.assertNotIn("acls", html)
        self.assertNotIn("pals", html)

    def test_no_certification_card_statement_is_clear(self) -> None:
        html = family_html()
        self.assertIn("No certification. No test. Just learn what to do.", html)
        self.assertIn("does not include a certification card", html)

    def test_compact_highlights_precede_scheduling_and_details_follow_it(self) -> None:
        html = family_html()
        highlights = html.index('class="section-box family-cpr-strip"')
        scheduling = html.index("<h2>Scheduling</h2>")
        details = html.index("<h2>Relaxed, practical CPR practice</h2>")
        self.assertLess(highlights, scheduling)
        self.assertLess(scheduling, details)
        self.assertNotIn("<h2>What the course covers</h2>", html)
        self.assertNotIn("<h2>Good for</h2>", html)

    def test_actions_are_correct(self) -> None:
        links = parsed_family().links
        self.assertTrue(any(href == "/request_group_session.html?program=Family%20and%20Friends%20CPR&request_type=private-class" and text == "Request Family & Friends CPR" for href, text in links))
        self.assertTrue(any(href == "tel:9103955193" and text == "Call 910CPR" for href, text in links))
        self.assertTrue(any(href == "/heartsaver.html" and text == "View Other CPR Classes" for href, text in links))

    def test_live_offer_section_fetches_authoritative_family_artifact(self) -> None:
        html = family_html()
        self.assertIn("/data/block-selector-availability/family_cpr.json", html)
        self.assertIn("fetch(availabilityUrl, { cache: 'no-store' })", html)
        self.assertIn("selector-resolved-availability.v1", html)
        self.assertIn("Checking current class times…", html)

    def test_live_offer_section_uses_shared_selector_structure(self) -> None:
        html = family_html()
        self.assertIn('class="selector-shell"', html)
        self.assertIn('class="selector-grid"', html)
        self.assertIn('id="date-list" class="month-stack"', html)
        self.assertIn('id="start-list" class="button-list"', html)
        self.assertIn('id="course-list" class="course-list"', html)
        self.assertIn("<h3>Calendar</h3>", html)
        self.assertIn("<h3>Start Times</h3>", html)
        self.assertIn("<h3>Register</h3>", html)
        self.assertIn("function renderCalendar()", html)
        self.assertIn("function renderStartTimes()", html)
        self.assertIn("function renderRegistration()", html)
        self.assertIn("course.appointmentUrl", html)

    def test_live_offer_section_has_no_static_appointment_inventory(self) -> None:
        html = family_html()
        self.assertNotIn("coastalcprtraining.enrollware.com/enroll?appointmentDayId", html)
        self.assertNotIn("courseId=252737", html)
        self.assertNotIn("family-cpr-offer\"><", html)
        self.assertNotIn("family-cpr-offer-list", html)
        self.assertNotIn("offers.slice(0, 8)", html)
        self.assertNotIn("flattenOffers", html)
        self.assertNotIn("renderOffers", html)

    def test_fallback_request_cta_remains_available_when_no_public_dates(self) -> None:
        html = family_html()
        self.assertIn("No current public dates are available. Request an individual, family, or group session.", html)
        self.assertIn("Current public Family & Friends CPR times are temporarily unavailable.", html)

    def test_family_artifact_urls_still_use_family_course_id(self) -> None:
        payload = json.loads(FAMILY_ARTIFACT.read_text(encoding="utf-8"))
        urls = []
        for day in payload.get("dates", []):
            for slot in day.get("startTimes", []):
                for course in slot.get("courses", []):
                    if course.get("appointmentUrl"):
                        urls.append(course["appointmentUrl"])
        self.assertTrue(urls)
        for url in urls:
            with self.subTest(url=url):
                self.assertIn("courseId=252737", url)

    def test_public_html_has_no_customer_visible_offer_count_phrases(self) -> None:
        forbidden_patterns = [
            r"\b\d+\s+current public options? available\b",
            r"\b\d+\s+options? available\b",
            r"\b\d+\s+public offers?\b",
            r"\b\d+\s+offers?\b",
            r"\bshowing\s+\d+\s+times\b",
            r"public-selectable offers",
            r"resolved offers",
            r"selector inventory totals",
        ]
        public_pages = [
            DOCS / "index.html",
            DOCS / "family-cpr.html",
            DOCS / "bls.html",
            DOCS / "acls.html",
            DOCS / "pals.html",
            DOCS / "hsi.html",
            DOCS / "heartsaver.html",
            DOCS / "arc.html",
            DOCS / "uscg-elementary-first-aid-cpr.html",
            DOCS / "courses" / "uscg-first-aid-cpr-aed.html",
        ]
        next_page = DOCS / "next.html"
        if next_page.exists():
            public_pages.append(next_page)
        for path in public_pages:
            html = path.read_text(encoding="utf-8")
            for pattern in forbidden_patterns:
                with self.subTest(path=path, pattern=pattern):
                    self.assertIsNone(re.search(pattern, html, flags=re.IGNORECASE))

    def test_internal_json_and_audit_counts_remain_available(self) -> None:
        artifact = json.loads(FAMILY_ARTIFACT.read_text(encoding="utf-8"))
        audit = json.loads(FAMILY_AUDIT.read_text(encoding="utf-8"))
        self.assertIn("dates", artifact)
        self.assertIn("counts", audit)
        self.assertGreater(audit["counts"].get("publicSelectableOfferCount", 0), 0)

    def test_mobile_styles_prevent_page_level_horizontal_overflow(self) -> None:
        html = family_html()
        self.assertIn("overflow-x: hidden", html)
        self.assertIn(".selector-grid > *", html)
        self.assertIn("min-width: 0", html)

    def test_redirect_shims_preserve_query_and_fragment_in_script(self) -> None:
        for rel in ["aha-family-friends-cpr.html", "courses/aha-family-friends-cpr.html", "ffcpr.html"]:
            with self.subTest(rel=rel):
                html = (DOCS / rel).read_text(encoding="utf-8")
                self.assertIn("window.location.search + window.location.hash", html)
                self.assertIn("window.location.replace(target)", html)
                self.assertIn("https://www.910cpr.com/family-cpr.html", html)

    def test_internal_links_use_canonical_family_url(self) -> None:
        scan_paths = [
            DOCS / "index.html",
            DOCS / "courses" / "index.html",
            DOCS / "assets" / "booking-home.js",
        ]
        for path in scan_paths:
            with self.subTest(path=path):
                html = path.read_text(encoding="utf-8")
                self.assertNotIn("/courses/aha-family-friends-cpr.html", html)
                self.assertNotIn("/aha-family-friends-cpr.html", html)
        self.assertIn('href: "/family-cpr.html"', (DOCS / "assets" / "booking-home.js").read_text(encoding="utf-8"))
        self.assertIn('image: "/images/FF-CPR-2.jpg"', (DOCS / "assets" / "booking-home.js").read_text(encoding="utf-8"))

    def test_internal_family_page_links_resolve(self) -> None:
        for href, text in parsed_family().links:
            with self.subTest(text=text, href=href):
                local = local_path_for_href(href)
                if local is not None:
                    self.assertTrue(local.exists(), f"{href} -> {local}")


if __name__ == "__main__":
    unittest.main()
