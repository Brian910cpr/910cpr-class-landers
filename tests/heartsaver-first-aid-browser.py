"""Click the first-aid format links against the exact checked-out public files."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

DOCS = Path(__file__).resolve().parents[1] / "docs"
LANDER = "/courses/heartsaver-first-aid-cpr-aed.html"
FORMATS = (
    ("See in-person options", "first-aid-cpr-aed", "209809"),
    ("See blended options", "first-aid-cpr-aed-blended", "329495"),
)


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def main():
    with ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietStaticHandler, directory=str(DOCS))) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = f"http://127.0.0.1:{server.server_port}"
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                for viewport, mobile in (({"width": 390, "height": 844}, True), ({"width": 1366, "height": 900}, False)):
                    page = browser.new_page(viewport=viewport, is_mobile=mobile, has_touch=mobile)
                    errors = []
                    page.on("pageerror", lambda err: errors.append(str(err)))
                    # No request can reach Stripe, Analytics, Enrollware or a live store.
                    def local_only(route):
                        url = urlsplit(route.request.url)
                        if f"{url.scheme}://{url.netloc}" != origin or route.request.method not in ("GET", "HEAD"):
                            route.abort()
                        else:
                            route.continue_()

                    page.route("**/*", local_only)
                    for label, anchor, course_id in FORMATS:
                        response = page.goto(origin + LANDER, wait_until="domcontentloaded")
                        assert response is not None and response.ok
                        expect(page.locator('a[href*="enrollware"], [data-row-href], [data-original-href]')).to_have_count(0)
                        link = page.get_by_role("link", name=label, exact=True)
                        expect(link).to_be_visible()
                        link.click()
                        page.wait_for_url(f"{origin}/heartsaver.html#{anchor}")
                        selected = page.locator('#course-option-list [aria-pressed="true"][data-course-id]')
                        expect(selected).to_have_count(1)
                        expect(selected).to_have_attribute("data-course-id", course_id)
                        print(f"{viewport['width']}px: {label} selected {course_id}", flush=True)
                    assert not errors, errors
                    page.close()
                browser.close()
        finally:
            server.shutdown()
            thread.join()


if __name__ == "__main__":
    main()
