from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
INDEX = DOCS / "index.html"
BOOKING_HOME = DOCS / "assets" / "booking-home.js"


CANONICAL_RUNTIME_CARDS = {
    "AHA BLS": ("/bls.html", "/images/bls_general.png"),
    "AHA ACLS": ("/acls.html", "/images/acls_general.png"),
    "AHA PALS": ("/pals.html", "/images/pals_general.png"),
    "AHA Heartsaver First Aid CPR AED": ("/heartsaver.html#first-aid-cpr-aed", "/images/heartsaver_general.png"),
    "AHA Heartsaver CPR AED": ("/heartsaver.html#cpr-aed", "/images/HS-FA-CPR-AED.jpeg"),
    "ARC Programs": ("/arc.html", "/images/0arc.png"),
    "HSI Programs": ("/hsi.html", "/images/0hsi.png"),
    "USCG / Maritime": ("/courses/uscg-first-aid-cpr-aed.html", "/images/maritime-first-aid.svg"),
    "Family & Friends CPR": ("/family-cpr.html", "/images/FF-CPR-2.jpg"),
}


OBSOLETE_HOMEPAGE_DESTINATIONS = [
    "/courses/aha-family-friends-cpr.html",
    "/courses/heartsaver-first-aid-cpr-aed.html",
    "/courses/heartsaver-cpr-aed.html",
    "/bls-schedule.html",
    "/acls-schedule.html",
    "/pals-schedule.html",
    "/hsi-schedule.html",
    "/heartsaver-schedule.html",
]


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            attr_map = {key: value or "" for key, value in attrs}
            self._href = attr_map.get("href", "")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            text = re.sub(r"\s+", " ", " ".join(self._text)).strip()
            self.links.append((self._href, text))
            self._href = None
            self._text = []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def local_path_for_href(href: str) -> Path | None:
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = parsed.path.lstrip("/")
    if path.endswith("/"):
        path += "index.html"
    if "." not in Path(path).name:
        path += ".html"
    return DOCS / path


class HomepageRoutingTests(unittest.TestCase):
    def test_runtime_course_cards_use_canonical_destinations_and_images(self) -> None:
        js = read(BOOKING_HOME)
        for label, (href, image) in CANONICAL_RUNTIME_CARDS.items():
            with self.subTest(label=label):
                self.assertIn(f'title: "{label}"', js)
                self.assertIn(f'href: "{href}"', js)
                if image is not None:
                    self.assertIn(f'image: "{image}"', js)

    def test_homepage_has_no_obsolete_course_or_schedule_destinations(self) -> None:
        combined = read(INDEX) + "\n" + read(BOOKING_HOME)
        for href in OBSOLETE_HOMEPAGE_DESTINATIONS:
            with self.subTest(href=href):
                self.assertNotIn(href, combined)

    def test_homepage_no_schedule_compatibility_urls(self) -> None:
        combined = read(INDEX) + "\n" + read(BOOKING_HOME)
        self.assertNotRegex(combined, r"/(?:bls|acls|pals|hsi|heartsaver)-schedule\\.html")

    def test_family_and_friends_homepage_tile_uses_public_page_and_image(self) -> None:
        js = read(BOOKING_HOME)
        self.assertIn('title: "Family & Friends CPR"', js)
        self.assertIn('href: "/family-cpr.html"', js)
        self.assertIn('image: "/images/FF-CPR-2.jpg"', js)
        self.assertTrue((DOCS / "family-cpr.html").exists())
        self.assertTrue((DOCS / "images" / "FF-CPR-2.jpg").exists())

    def test_not_sure_cta_uses_guided_chooser_not_raw_mailto(self) -> None:
        js = read(BOOKING_HOME)
        html = read(INDEX)
        self.assertNotIn("mailto:info@910cpr.com?subject=Help%20Choosing%20A%20Class", js)
        self.assertNotIn("mailto:info@910cpr.com?subject=Help%20Choosing%20A%20Class", html)
        self.assertIn("Need help choosing the right class?", js)
        self.assertIn("Help Me Choose the Right Class", js)
        self.assertIn("data-course-chooser-toggle", js)
        self.assertIn('aria-expanded="false"', js)
        self.assertIn('aria-controls="guided-course-chooser"', js)
        self.assertIn('id="guided-course-chooser"', js)
        self.assertIn("chooserToggle?.addEventListener", js)
        self.assertIn("firstLink", js)
        self.assertIn("focus()", js)
        self.assertNotIn('href="/classes/"', html)

    def test_guided_chooser_uses_canonical_course_destinations(self) -> None:
        combined = read(INDEX) + "\n" + read(BOOKING_HOME)
        expected = [
            "/bls.html",
            "/acls.html",
            "/pals.html",
            "/hsi.html#bls",
            "/heartsaver.html#first-aid-cpr-aed",
            "/heartsaver.html#cpr-aed",
            "/heartsaver.html#pediatric-first-aid-cpr-aed",
            "/family-cpr.html",
        ]
        for href in expected:
            with self.subTest(href=href):
                self.assertIn(href, combined)
        self.assertIn('href="tel:9103955193"', combined)

    def test_email_fallback_is_secondary_and_prefilled(self) -> None:
        js = read(BOOKING_HOME)
        self.assertIn("data-context-email-link", js)
        self.assertIn("Email with this context", js)
        self.assertIn("Help Choosing the Right CPR Class", js)
        self.assertIn("I need help choosing the correct class.", js)
        self.assertIn("Requirement from my employer, school, or license:", js)
        self.assertIn("My deadline:", js)

    def test_homepage_uscg_card_uses_maritime_svg_and_valid_route(self) -> None:
        combined = read(INDEX) + "\n" + read(BOOKING_HOME)
        self.assertIn('href: "/courses/uscg-first-aid-cpr-aed.html"', combined)
        self.assertIn('image: "/images/maritime-first-aid.svg"', combined)
        self.assertIn('src="/images/maritime-first-aid.svg"', combined)
        self.assertTrue((DOCS / "images" / "maritime-first-aid.svg").exists())

    def test_homepage_styles_prevent_mobile_horizontal_overflow(self) -> None:
        css = read(DOCS / "css" / "lander.css")
        self.assertIn(".home-course-chooser-grid", css)
        self.assertIn("grid-template-columns: 1fr", css)
        self.assertIn(".home-help-actions .button", css)

    def test_noscript_homepage_links_use_canonical_destinations(self) -> None:
        parser = LinkParser()
        parser.feed(read(INDEX))
        links = {(text, href) for href, text in parser.links}
        self.assertIn(("AHA Heartsaver First Aid CPR AED", "/heartsaver.html#first-aid-cpr-aed"), links)
        self.assertIn(("AHA Heartsaver CPR AED", "/heartsaver.html#cpr-aed"), links)
        self.assertIn(("USCG / Maritime", "/courses/uscg-first-aid-cpr-aed.html"), links)
        self.assertIn(("Family & Friends CPR", "/family-cpr.html"), links)

    def test_all_homepage_internal_destinations_exist_locally(self) -> None:
        parser = LinkParser()
        parser.feed(read(INDEX))
        hrefs = [href for href, _ in parser.links]
        js = read(BOOKING_HOME)
        hrefs.extend(re.findall(r'href: "([^"]+)"', js))
        for href in hrefs:
            with self.subTest(href=href):
                local_path = local_path_for_href(href)
                if local_path is not None:
                    self.assertTrue(local_path.exists(), f"{href} -> {local_path}")

    def test_visible_runtime_cards_are_rendered_as_links(self) -> None:
        js = read(BOOKING_HOME)
        self.assertIn('<a class="home-course-tile"', js)
        self.assertIn('<img src="${escapeAttribute(course.image)}"', js)
        self.assertIn('<strong>${escapeHtml(course.title)}</strong>', js)


if __name__ == "__main__":
    unittest.main()
