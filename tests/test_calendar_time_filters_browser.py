"""Browser regressions against real repository availability; no generated session fixtures.

Run: python -B -m unittest tests.test_calendar_time_filters_browser
Requires the existing local Playwright installation and Chromium.
CALENDAR_SCREENSHOT_DIR optionally saves desktop/mobile review images.
"""
from datetime import date, datetime, timedelta, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from threading import Thread
import unittest
from urllib.parse import parse_qsl, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BUCKETS = [("early-am", 0, 360), ("am", 360, 720), ("afternoon", 720, 1020), ("evening", 1020, 1260), ("late-pm", 1260, 1440)]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class CalendarTimeFilterBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT / "docs")))
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def load(self, family, width=1280):
        page = self.browser.new_page(viewport={"width": width, "height": 900}, timezone_id="Pacific/Honolulu")
        self.addCleanup(page.close)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        # Third-party analytics/chat are irrelevant to local calendar verification.
        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(self.base) else route.abort())
        data = json.loads((ROOT / "docs/data/block-selector-availability" / f"{family}.json").read_text(encoding="utf-8"))
        self.assertTrue(data["dates"], f"{family}: real inventory required for this test")
        # Freeze before the first real inventory day so the test survives feed rotation.
        today = date.fromisoformat(min(day["date"] for day in data["dates"])) - timedelta(days=1)
        page.clock.set_fixed_time(datetime.combine(today, datetime.min.time(), timezone.utc) + timedelta(hours=16))
        page.goto(f"{self.base}/{family}.html", wait_until="domcontentloaded")
        page.wait_for_function("availabilityState === 'ready'")
        self.assertEqual(errors, [])
        return page, data, today, errors

    def result(self, page):
        return page.evaluate("filteredDates().flatMap(day => day.startTimes.map(slot => ({date: day.date, time: slot.startTime, ids: slot.courses.map(course => String(course.courseId)), urls: slot.courses.map(course => course.appointmentUrl)})))")

    def expected(self, data, ids, predicate=lambda day, minutes: True):
        result = []
        for day in data["dates"]:
            for slot in day["startTimes"]:
                try:
                    value = datetime.strptime(slot["startTime"], "%H:%M")
                except ValueError:
                    value = datetime.strptime(slot["startTime"], "%I:%M %p")
                minute = value.hour * 60 + value.minute
                courses = [course for course in slot["courses"] if str(course["courseId"]) in ids]
                if courses and predicate(date.fromisoformat(day["date"]), minute):
                    result.append({"date": day["date"], "time": slot["startTime"], "ids": [str(course["courseId"]) for course in courses], "urls": [course["appointmentUrl"] for course in courses]})
        return result

    def smart(self, page, text):
        page.get_by_role("textbox", name="Smart filter", exact=True).fill(text)
        page.get_by_role("textbox", name="Smart filter", exact=True).press("Enter")

    def assert_rendered(self, page, expected):
        if expected:
            self.assertGreater(page.locator(".day-button:not(:disabled)").count(), 0)
            self.assertGreater(page.locator("#start-list button:not(:disabled)").count(), 0)
            links = page.locator("#course-list a.register-link").evaluate_all("links => links.map(link => link.href)")
            def enrollment_target(url):
                parsed = urlsplit(url)
                # Existing attribution adds UTM fields and normalizes percent-encoding.
                return (parsed.scheme, parsed.netloc, parsed.path, tuple(sorted((key, value) for key, value in parse_qsl(parsed.query) if not key.startswith("utm_"))))
            allowed = {enrollment_target(url) for item in expected for url in item["urls"]}
            self.assertTrue(links)
            self.assertTrue({enrollment_target(url) for url in links} <= allowed)
        else:
            self.assertEqual(page.locator(".day-button:not(:disabled)").count(), 0)
            self.assertEqual(page.locator("#start-list button:not(:disabled)").count(), 0)
            self.assertEqual(page.locator("#course-list a.register-link").count(), 0)
            self.assertIn("No matching times", page.locator("#date-list").inner_text())

    def exercise_family(self, family):
        page, data, today, errors = self.load(family)
        ids = page.evaluate("[...activeCourseIds()]")
        baseline = self.expected(data, ids)
        self.assertTrue(baseline)
        self.assertEqual(self.result(page), baseline)
        self.assertEqual(page.locator(".calendar-time-bullet").all_text_contents(), ["•"] * 4)
        self.assertEqual(page.get_by_role("heading", name="When are YOU available?", exact=True).count(), 1)
        self.assertEqual(page.locator(".calendar-timing-pill .calendar-availability-heading").count(), 1)
        self.assertEqual(page.locator(".calendar-filter-pill").count(), 1)
        self.assertEqual(page.locator(".calendar-timing-pill .calendar-time-smart").count(), 1)
        self.assertEqual(page.locator(".calendar-billing-pill").count(), 0)
        self.assertEqual(page.locator(".calendar-billing-code").count(), 0)
        self.assertEqual(page.get_by_role("combobox", name="Billing Code", exact=True).count(), 0)
        for bucket, lower, upper in BUCKETS:
            with self.subTest(family=family, bucket=bucket):
                page.locator(f'#calendar-time-filters input[value="{bucket}"]').check()
                expected = self.expected(data, ids, lambda day, minute: lower <= minute < upper)
                self.assertEqual(self.result(page), expected)
                self.assert_rendered(page, expected)
                page.get_by_role("button", name="Clear timing filters").click()
                self.assertEqual(self.result(page), baseline)
        for bucket in ["am", "evening"]:
            page.locator(f'#calendar-time-filters input[value="{bucket}"]').check()
        expected = self.expected(data, ids, lambda day, minute: 360 <= minute < 720 or 1020 <= minute < 1260)
        self.assertEqual(self.result(page), expected)
        self.smart(page, "after 6pm")
        self.assertEqual(self.result(page), self.expected(data, ids, lambda day, minute: 1080 < minute < 1260))
        page.get_by_role("button", name="Clear timing filters").click()
        next_monday = today + timedelta(days=7 - today.weekday())
        phrases = [
            ("after 6pm", lambda day, minute: minute > 1080),
            ("Tuesday or Wednesday evening", lambda day, minute: day.weekday() in [1, 2] and 1020 <= minute < 1260),
            ("before noon", lambda day, minute: minute < 720),
            ("Saturday morning", lambda day, minute: day.weekday() == 5 and 360 <= minute < 720),
            ("after work next week", lambda day, minute: next_monday <= day <= next_monday + timedelta(days=6) and minute > 1020),
            ("anything after 7pm", lambda day, minute: minute > 1140),
            ("weekdays before 10am", lambda day, minute: day.weekday() < 5 and minute < 600),
            ("can't Tuesday evening", lambda day, minute: not (day.weekday() == 1 and 1020 <= minute < 1260)),
        ]
        for phrase, predicate in phrases:
            with self.subTest(family=family, phrase=phrase):
                self.smart(page, phrase)
                self.assertEqual(page.get_by_role("textbox", name="Smart filter").get_attribute("aria-invalid"), "false")
                expected = self.expected(data, ids, predicate)
                self.assertEqual(self.result(page), expected)
                self.assert_rendered(page, expected)
        # Valid but impossible in the loaded source: empty, with no alternative-course suggestion.
        self.smart(page, "2099-01-01 after 7pm")
        self.assertEqual(self.result(page), [])
        self.assert_rendered(page, [])
        self.smart(page, "after 7pm except my work shift")
        self.assertEqual(self.result(page), [])
        self.assertEqual(page.get_by_role("textbox", name="Smart filter").get_attribute("aria-invalid"), "true")
        self.assertIn("Try", page.locator(".calendar-time-status").inner_text())
        page.get_by_role("button", name="Clear timing filters").click()
        self.assertEqual(self.result(page), baseline)
        self.assertEqual(page.evaluate("[...activeCourseIds()]"), ids)
        self.assertEqual(page.locator('#calendar-time-filters input[type="checkbox"]:checked').count(), 0)
        # Existing comparison and deep-linked course context remain authoritative after reset.
        page.locator("#compare-toggle").check()
        compare_ids = page.evaluate("[...activeCourseIds()]")
        self.smart(page, "before noon")
        self.assertEqual(self.result(page), self.expected(data, compare_ids, lambda day, minute: minute < 720))
        page.get_by_role("button", name="Clear timing filters").click()
        self.assertEqual(self.result(page), self.expected(data, compare_ids))
        page.locator("#compare-toggle").uncheck()
        alternative = page.evaluate("courseOptions.find(course => course.courseId !== selectedCourseId).courseId")
        page.evaluate("id => { window.location.hash = id; }", alternative)
        page.wait_for_function("id => selectedCourseId === id", arg=alternative)
        self.smart(page, "before noon")
        self.assertEqual(self.result(page), self.expected(data, [alternative], lambda day, minute: minute < 720))
        page.get_by_role("button", name="Clear timing filters").click()
        self.assertEqual(page.evaluate("selectedCourseId"), alternative)
        self.assertEqual(self.result(page), self.expected(data, [alternative]))
        self.assertEqual(errors, [])

    def test_bls_real_inventory_and_controls(self):
        self.exercise_family("bls")

    def test_acls_real_inventory_and_controls(self):
        self.exercise_family("acls")

    def test_compact_desktop_and_mobile_wrapping(self):
        for family in ["bls", "acls"]:
            for width in [1280, 390, 320]:
                with self.subTest(family=family, width=width):
                    page, _, _, errors = self.load(family, width)
                    panel = page.locator("#calendar-time-filters")
                    dimensions = panel.bounding_box()
                    self.assertLess(dimensions["height"], 285 if width < 600 else 165)
                    self.assertGreaterEqual(dimensions["x"], 0)
                    self.assertLessEqual(dimensions["x"] + dimensions["width"], width)
                    timing_pill = page.locator(".calendar-timing-pill").bounding_box()
                    self.assertIsNotNone(timing_pill)
                    for selector in [".calendar-time-item", ".calendar-time-smart input", ".calendar-time-smart button"]:
                        for item in page.locator(selector).all():
                            box = item.bounding_box()
                            self.assertGreaterEqual(box["x"], dimensions["x"])
                            self.assertLessEqual(box["x"] + box["width"], dimensions["x"] + dimensions["width"] + 1)
                    calendar = page.locator("#date-list").bounding_box()
                    self.assertGreaterEqual(calendar["y"], dimensions["y"] + dimensions["height"])
                    self.assertGreater(calendar["height"], dimensions["height"])
                    screenshots = os.environ.get("CALENDAR_SCREENSHOT_DIR")
                    if screenshots:
                        output = Path(screenshots)
                        output.mkdir(parents=True, exist_ok=True)
                        panel.evaluate("element => window.scrollTo(0, element.getBoundingClientRect().top + window.scrollY - 20)")
                        page.screenshot(path=str(output / f"calendar-{family}-{width}.png"))
                    self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
