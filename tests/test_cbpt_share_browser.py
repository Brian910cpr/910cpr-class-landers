"""Local browser contract tests. All network requests are intercepted; no analytics is sent.

Run with: python -m unittest tests.test_cbpt_share_browser -v
Requires Playwright and its Chromium browser.
"""
import json
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class CBPTShareBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def open_page(self, *, native="absent", clipboard="success", prompt="value",
                  cookie="", path="/cbpt", event_url="", blocked_storage=False):
        context = self.browser.new_context()
        self.addCleanup(context.close)
        if cookie:
            context.add_cookies([{"name": cookie, "value": "1", "url": "https://www.910cpr.com"}])
        html = (ROOT / "docs/cbpt.html").read_text(encoding="utf-8")
        html = html.replace('name="cbpt-facebook-event-url" content=""',
                            'name="cbpt-facebook-event-url" content="' + event_url + '"')

        def serve(route):
            from urllib.parse import urlparse
            request_path = urlparse(route.request.url).path
            if request_path == path:
                route.fulfill(status=200, content_type="text/html", body=html)
            elif request_path in ("/assets/cbpt-share.js", "/assets/analytics-attribution.js"):
                route.fulfill(status=200, content_type="application/javascript",
                              body=(ROOT / "docs" / request_path.lstrip("/")).read_text(encoding="utf-8"))
            else:
                route.fulfill(status=200, body="")

        context.route("**/*", serve)
        context.add_init_script("""(() => {
          const options = OPTIONS;
          window.nativeCalls = 0; window.copies = []; window.prompts = [];
          Object.defineProperty(navigator, 'share', {configurable: true, value:
            options.native === 'absent' ? undefined : async () => {
              window.nativeCalls++;
              if (options.native !== 'success') throw {name: options.native === 'cancel' ? 'AbortError' : 'NotAllowedError'};
            }});
          Object.defineProperty(navigator, 'clipboard', {configurable: true, value:
            options.clipboard === 'absent' ? undefined : {writeText: async value => {
              if (options.clipboard === 'error') throw Error('blocked');
              window.copies.push(value);
            }}});
          window.prompt = (label, value) => {
            window.prompts.push(value);
            if (options.prompt === 'error') throw Error('blocked');
            return options.prompt === 'cancel' ? null : value;
          };
          if (options.blocked_storage) Object.defineProperty(window, 'sessionStorage', {get() {throw Error('blocked');}});
          document.addEventListener('click', event => {
            const link = event.target.closest('a[data-share]');
            if (link) window.lastLinkClick = {prevented: event.defaultPrevented, href: link.href};
          });
        })();""".replace("OPTIONS", json.dumps(dict(native=native, clipboard=clipboard,
                                                    prompt=prompt, blocked_storage=blocked_storage))))
        page = context.new_page()
        page.goto("https://www.910cpr.com" + path + "?utm_source=private-person@example.test&phone=5551234567")
        page.wait_for_load_state("load")
        return page

    def events(self, page, name="cbpt_share_click"):
        # A round trip also lets resolved/rejected share promises finish.
        return page.evaluate("name => (window.dataLayer || []).filter(e => e.event === name)", name)

    def control(self, page, placement, channel):
        return page.locator(f'[data-share-placement="{placement}"] [data-share="{channel}"]')

    def test_both_sections_nested_svg_keyboard_repeated_clicks_and_links(self):
        page = self.open_page()
        for placement in ("top", "bottom"):
            for channel in ("native", "copy", "text", "email", "facebook"):
                control = self.control(page, placement, channel)
                if channel == "facebook":
                    with page.expect_popup() as popup:
                        control.locator("svg").click()
                    popup.value.close()
                else:
                    control.locator("svg").click()
                event = self.events(page)[-1]
                self.assertEqual((event["share_channel"], event["share_placement"]), (channel, placement))
                if channel in ("text", "email", "facebook"):
                    self.assertFalse(page.evaluate("window.lastLinkClick.prevented"))
        self.assertEqual(len(self.events(page)), 10)
        button = self.control(page, "bottom", "copy")
        button.focus()
        button.press("Enter")
        button.press("Space")
        button.click()
        button.click()
        self.assertEqual(len(self.events(page)), 14)
        self.assertEqual(page.locator('[data-share-placement="bottom"] .share-status').inner_text(), "Copied!")
        for event in self.events(page) + self.events(page, "cbpt_share_result"):
            self.assertEqual(set(event), {"event", "page_id", "share_channel", "share_placement", "share_target", "share_method", "share_outcome"})
            self.assertNotIn("private-person", json.dumps(event))
            self.assertNotIn("5551234567", json.dumps(event))
            self.assertNotIn("https:", json.dumps(event))

    def test_native_success_cancel_and_failure_are_distinct(self):
        for mode, outcomes, copies in (
            ("success", [("native", "resolved")], 0),
            ("cancel", [("native", "cancelled")], 0),
            ("error", [("native", "failed"), ("clipboard", "succeeded")], 1),
            ("absent", [("clipboard", "succeeded")], 1),
        ):
            with self.subTest(mode=mode):
                page = self.open_page(native=mode)
                self.control(page, "top", "native").click()
                self.assertEqual(len(self.events(page)), 1)
                self.assertEqual([(e["share_method"], e["share_outcome"]) for e in self.events(page, "cbpt_share_result")], outcomes)
                self.assertEqual(page.evaluate("window.copies.length"), copies)

    def test_copy_fallback_never_claims_prompt_is_success(self):
        for clipboard in ("error", "absent"):
            for prompt, outcome in (("value", "prompted"), ("cancel", "cancelled"), ("error", "failed")):
                with self.subTest(clipboard=clipboard, prompt=prompt):
                    page = self.open_page(native="error", clipboard=clipboard, prompt=prompt)
                    self.control(page, "bottom", "native").click()
                    self.assertEqual(len(self.events(page)), 1)
                    self.assertEqual([e["share_outcome"] for e in self.events(page, "cbpt_share_result")], ["failed", "failed", outcome])
                    self.assertEqual(page.evaluate("window.prompts"), ["https://www.910cpr.com/cbpt"])

    def test_exclusions_initial_and_after_load_do_not_break_copy(self):
        for cookie in ("analytics_excluded", "lw_analytics_excluded"):
            page = self.open_page(cookie=cookie)
            self.control(page, "top", "copy").click()
            self.assertEqual(self.events(page), [])
            self.assertEqual(self.events(page, "cbpt_share_result"), [])
            self.assertEqual(page.evaluate("window.copies.length"), 1)
        for path in ("/admin/cbpt", "/control-center/cbpt", "/internal/cbpt", "/drafts/cbpt", "/analytics-preferences"):
            page = self.open_page(path=path)
            self.control(page, "top", "copy").click()
            self.assertEqual(self.events(page), [])
        page = self.open_page()
        page.evaluate("document.cookie = 'analytics_excluded=1; path=/'")
        self.control(page, "top", "copy").click()
        self.assertEqual(self.events(page), [])

    def test_analytics_failure_and_blocked_storage_do_not_break_behavior(self):
        for failure in ("delete window.dataLayer; delete window.LanderWareAnalytics", "window.dataLayer = {}",
                        "window.dataLayer.push = () => {throw Error('blocked')}",
                        "window.LanderWareAnalytics.isExcluded = () => {throw Error('blocked')}",
                        "Object.defineProperty(document, 'cookie', {get() {throw Error('blocked')}})"):
            page = self.open_page(blocked_storage=True)
            page.evaluate("() => {" + failure + ";}")
            self.control(page, "top", "native").click()
            self.assertEqual(page.evaluate("window.copies"), ["https://www.910cpr.com/cbpt"])
        page = self.open_page(blocked_storage=True)
        self.control(page, "bottom", "copy").click()
        self.assertEqual(len(self.events(page)), 1)
        page.locator("#page-info").click()
        self.assertEqual(len(self.events(page)), 1)  # Diagnostics are not a share activation.

    def test_verified_event_configuration_and_invalid_value_fallback(self):
        for configured, expected in (("", "class_page"), ("https://www.facebook.com/events/123456789/", "facebook_event"),
                                     ("https://example.test/events/123/", "class_page"),
                                     ("https://www.facebook.com/events/123/?name=private", "class_page")):
            page = self.open_page(event_url=configured)
            for placement in ("top", "bottom"):
                control = self.control(page, placement, "facebook")
                self.assertEqual(control.get_attribute("href"), configured if expected == "facebook_event" else
                                 "https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Fwww.910cpr.com%2Fcbpt")
                with page.expect_popup() as popup:
                    control.click()
                popup.value.close()
                self.assertEqual(self.events(page)[-1]["share_target"], expected)


if __name__ == "__main__":
    unittest.main()
