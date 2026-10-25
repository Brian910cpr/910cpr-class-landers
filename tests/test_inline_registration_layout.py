"""Rendered selector contract using synthetic sessions, never real bookings."""
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class InlineLayout(unittest.TestCase):
    def test_desktop_and_mobile_reselection_preserve_inputs(self):
        script = (ROOT / 'docs/assets/inline-registration.js').read_text(encoding='utf-8')
        shell = '''<style>.selector-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
        @media(max-width:924px){.selector-grid{grid-template-columns:1fr}}[hidden]{display:none!important}</style>
        <div class="selector-grid"><div class="panel" id="dates">Calendar</div>
        <div class="panel"><div id="start-list"><button aria-pressed="true">9:00 AM</button></div></div>
        <div class="panel"><div id="course-list"><article class="course">
        <a class="register-link" href="/register/?session=123456">Register</a></article></div></div></div>'''
        form = '''<h1>BLS Renewal</h1><form><div class="student"><input data-field="firstName">
        <input data-field="email"><input type="radio" name="manual-0" value="own" checked>
        <input type="radio" name="manual-0" value="ebook"></div></form>
        <script>parent.postMessage({type:'landerware:checkout-size',sessionId:new URLSearchParams(location.search).get('session'),height:400},location.origin)</script>'''
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for width in (1440, 390):
                with self.subTest(width=width):
                    page = browser.new_page(viewport={'width': width, 'height': 1000})
                    errors = []
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    page.route('http://inline.test/**', lambda route: route.fulfill(
                        content_type='text/html', body=form if '/register/' in route.request.url else shell))
                    page.goto('http://inline.test/')
                    page.add_script_tag(content=script)
                    page.locator('.register-link').click()
                    frame = page.frame_locator('iframe')
                    frame.locator('[data-field="firstName"]').fill('Synthetic')
                    frame.locator('[data-field="email"]').fill('synthetic@example.test')
                    frame.locator('[value="ebook"]').check()
                    self.assertTrue(page.locator('#dates').is_visible())
                    self.assertFalse(page.locator('#start-list').is_visible())
                    self.assertEqual(page.locator('#selected-time-checkout').evaluate(
                        'e=>getComputedStyle(e).gridColumnStart'), '2' if width == 1440 else '1')
                    page.get_by_role('button', name='9:00 AM — Change time').click()
                    self.assertTrue(page.locator('#start-list').is_visible())
                    page.evaluate('''() => {
                      const link=document.querySelector('.register-link');
                      const next=link.cloneNode(true);next.href='/register/?session=654321';link.replaceWith(next);
                      document.querySelector('#start-list button').textContent='11:00 AM';
                    }''')
                    page.locator('.register-link').click()
                    page.wait_for_function("document.querySelector('iframe').contentDocument.querySelector('[data-field=firstName]')?.value==='Synthetic'")
                    self.assertEqual(frame.locator('[data-field="email"]').input_value(), 'synthetic@example.test')
                    self.assertTrue(frame.locator('[value="ebook"]').is_checked())
                    self.assertIn('session=654321', page.locator('iframe').get_attribute('src'))
                    self.assertEqual(page.locator('iframe').count(), 1)
                    self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                    self.assertEqual(errors, [])
                    page.close()
            browser.close()


if __name__ == '__main__':
    unittest.main()
