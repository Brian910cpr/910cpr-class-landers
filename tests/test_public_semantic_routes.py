from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SLUG_HUBS = ROOT / "data" / "config" / "slug_hubs.json"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[dict[str, str], str]] = []
        self._attrs: dict[str, str] | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._attrs = {key: value or "" for key, value in attrs}
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._attrs is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._attrs is not None:
            self.links.append((self._attrs, re.sub(r"\s+", " ", " ".join(self._text)).strip()))
            self._attrs = None
            self._text = []


def slug_hub_pages() -> dict[str, dict]:
    payload = json.loads(SLUG_HUBS.read_text(encoding="utf-8"))
    return {page["slug"]: page for page in payload["pages"]}


def local_path_from_href(href: str) -> str | None:
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc:
        return None
    path = parsed.path
    if not path or path.startswith("#"):
        return None
    if path.startswith("/"):
        path = path[1:]
    if path.endswith("/"):
        path += "index.html"
    if "." not in Path(path).name:
        path += ".html"
    return path


class PublicSemanticRouteTests(unittest.TestCase):
    def test_group_tab_routes_stay_in_group_flow_and_do_not_self_loop(self) -> None:
        group = slug_hub_pages()["group-training"]
        for tab in group["tabs"]:
            with self.subTest(tab=tab["id"]):
                href = tab["full_schedule_url"]
                self.assertTrue(href.startswith("/request_group_session.html?"), href)
                self.assertIn("request_type=group", href)
                self.assertNotEqual("/group-training.html", href)
                self.assertNotIn("/bls.html", href)
                self.assertNotIn("/acls.html", href)
                self.assertNotIn("/pals.html", href)
                self.assertNotIn("/heartsaver.html", href)

    def test_group_request_page_preserves_group_context(self) -> None:
        html = (DOCS / "request_group_session.html").read_text(encoding="utf-8")
        self.assertIn("id='request_type'", html)
        self.assertIn('new URLSearchParams(window.location.search)', html)
        self.assertIn('params.get("program")', html)
        self.assertIn('params.get("request_type")', html)
        self.assertIn("programInput.value = program", html)
        self.assertNotIn("bls-schedule.html", html)
        self.assertNotIn("acls-schedule.html", html)
        self.assertNotIn("pals-schedule.html", html)

    def test_course_family_schedule_routes_match_family(self) -> None:
        pages = slug_hub_pages()
        for tab in pages["bls"]["tabs"]:
            self.assertEqual("/bls-schedule.html", tab["full_schedule_url"])
        for tab in pages["acls"]["tabs"]:
            self.assertEqual("/acls-schedule.html", tab["full_schedule_url"])
        for tab in pages["pals"]["tabs"]:
            self.assertEqual("/pals-schedule.html", tab["full_schedule_url"])
        for tab in pages["heartsaver"]["tabs"]:
            self.assertEqual("/heartsaver-schedule.html", tab["full_schedule_url"])
        for tab in pages["uscg-elementary-first-aid-cpr"]["tabs"]:
            self.assertEqual("/courses/uscg-first-aid-cpr-aed.html", tab["full_schedule_url"])

    def test_hsi_routes_do_not_leave_hsi_family(self) -> None:
        page = slug_hub_pages()["hsi"]
        for tab in page["tabs"]:
            href = tab["full_schedule_url"]
            self.assertNotIn("/bls", href)
            self.assertTrue(href.startswith("/hsi") or "/courses/hsi-" in href, href)

    def test_selectors_retained_only_for_multi_option_families_here(self) -> None:
        pages = slug_hub_pages()
        self.assertGreater(len(pages["bls"]["tabs"]), 1)
        self.assertGreater(len(pages["acls"]["tabs"]), 1)
        self.assertGreater(len(pages["pals"]["tabs"]), 1)
        self.assertGreater(len(pages["heartsaver"]["tabs"]), 1)
        self.assertEqual("/courses/uscg-first-aid-cpr-aed.html", pages["uscg-elementary-first-aid-cpr"]["tabs"][0]["full_schedule_url"])

    def test_generated_primary_routes_exist_and_avoid_error_page(self) -> None:
        for rel in [
            "bls.html",
            "acls.html",
            "pals.html",
            "heartsaver.html",
            "hsi.html",
            "arc.html",
            "uscg-elementary-first-aid-cpr.html",
            "group-training.html",
        ]:
            parser = LinkParser()
            parser.feed((DOCS / rel).read_text(encoding="utf-8"))
            for attrs, text in parser.links:
                href = attrs.get("href", "")
                if not re.search(r"schedule|date|book|register|request|group|details|option", text + " " + href, re.I):
                    continue
                path = local_path_from_href(href)
                if path is None:
                    continue
                with self.subTest(source=rel, text=text, href=href):
                    self.assertNotIn("error", path.lower())
                    self.assertTrue((DOCS / path).exists(), path)

    def test_public_class_landers_match_direct_bookable_public_schedule(self) -> None:
        payload = json.loads((DOCS / "public_schedule.json").read_text(encoding="utf-8"))
        public_ids = {str(row["class_id"]) for row in payload["sessions"]}
        class_ids = {
            path.stem
            for path in (DOCS / "classes").glob("*.html")
            if path.stem.isdigit()
        }
        self.assertFalse(public_ids - class_ids)
        self.assertFalse(class_ids - public_ids)
        self.assertNotIn("12774086", class_ids)
        self.assertNotIn("12774096", class_ids)


if __name__ == "__main__":
    unittest.main()
