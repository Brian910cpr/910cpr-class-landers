from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
FAMILY = DOCS / "family-cpr.html"


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
        self.assertIn("does not include a certification card", family_html())

    def test_actions_are_correct(self) -> None:
        links = parsed_family().links
        self.assertTrue(any(href == "/request_group_session.html?program=Family%20and%20Friends%20CPR&request_type=private-class" and text == "Request Family & Friends CPR" for href, text in links))
        self.assertTrue(any(href == "tel:9103955193" and text == "Call 910CPR" for href, text in links))
        self.assertTrue(any(href == "/heartsaver.html" and text == "View Other CPR Classes" for href, text in links))

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
