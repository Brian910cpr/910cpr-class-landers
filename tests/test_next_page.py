from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
NEXT = DOCS / "next.html"


class NextPageLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.ids: set[str] = set()
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        if "id" in attr_map:
            self.ids.add(attr_map["id"])
        if tag == "a":
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


def next_html() -> str:
    return NEXT.read_text(encoding="utf-8")


def parsed_next() -> NextPageLinkParser:
    parser = NextPageLinkParser()
    parser.feed(next_html())
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


class NextPageTests(unittest.TestCase):
    def test_next_page_exists_without_fragment(self) -> None:
        html = next_html()
        self.assertIn("<title>What’s Next? Certification Help & CPR Classes | 910CPR</title>", html)
        self.assertIn("Whether you just completed a class with 910CPR or someone shared this card with you", html)
        self.assertIn('href="/index.html#class-finder">← View All Courses</a>', html)

    def test_required_fragments_exist(self) -> None:
        parser = parsed_next()
        self.assertTrue({"card", "classes", "employer", "group", "review"}.issubset(parser.ids))

    def test_primary_action_cards_target_required_fragments(self) -> None:
        links = parsed_next().links
        expected = {
            "I Just Finished My Class": "#card",
            "I Need Another Certification": "#classes",
            "My Employer Sent Me Here": "#employer",
            "Train My Workplace or Group": "#group",
        }
        for label, href in expected.items():
            with self.subTest(label=label):
                self.assertTrue(
                    any(link_href == href and link_text.startswith(label) for link_href, link_text in links),
                    f"{label} -> {href}",
                )

    def test_class_links_use_canonical_family_pages(self) -> None:
        html = next_html()
        self.assertIn('href="/bls.html"', html)
        self.assertIn('href="/acls.html"', html)
        self.assertIn('href="/pals.html"', html)
        self.assertIn('href="/heartsaver.html#cpr-aed"', html)
        self.assertIn('href="/heartsaver.html#first-aid-cpr-aed"', html)
        self.assertIn('href="/hsi.html"', html)
        self.assertNotIn("-schedule.html", html)

    def test_no_unsupported_delivery_deadline_promise(self) -> None:
        html = next_html().lower()
        self.assertNotIn("same day", html)
        self.assertNotIn("within 24", html)
        self.assertNotIn("within one business day", html)

    def test_review_section_appears_after_card_help(self) -> None:
        html = next_html()
        self.assertGreater(html.index('id="review"'), html.index('id="card"'))

    def test_contact_actions_are_actionable(self) -> None:
        html = next_html()
        self.assertIn("subject=Certification%20Card%20Help", html)
        self.assertIn("subject=Student%20Information%20Correction", html)
        self.assertIn("subject=Employer%20Verification%20Request", html)
        self.assertIn('href="tel:9103955193"', html)
        self.assertIn("/request_group_session.html?program=Workplace%20Group%20Training", html)

    def test_fragment_navigation_sets_accessible_focus_and_header_offset(self) -> None:
        html = next_html()
        self.assertIn("scroll-margin-top: 96px", html)
        self.assertIn("scrollIntoView({ block: 'start'", html)
        self.assertIn("target.focus({ preventScroll: true })", html)

    def test_internal_next_page_links_resolve(self) -> None:
        parser = parsed_next()
        for href, text in parser.links:
            with self.subTest(text=text, href=href):
                if href.startswith("#"):
                    self.assertIn(href[1:], parser.ids)
                    continue
                local = local_path_for_href(href)
                if local is not None:
                    self.assertTrue(local.exists(), f"{href} -> {local}")


if __name__ == "__main__":
    unittest.main()
