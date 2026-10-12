import json
import threading
import unittest
from datetime import datetime, timedelta, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

class StudioBrowserTests(unittest.TestCase):
    """Real Chromium/DOM; synthetic API, never production auth/database proof."""
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'docs')))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.rows, self.receipts, self.writes, self.requests = {}, {}, [], []
        self.fail_next = False
        self.conflict_next = False
        session = {'token': 'lw_s_' + 'a' * 64, 'expiresAt': (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()}
        self.context.add_init_script('localStorage.setItem("landerwareOwnerSession", '+json.dumps(json.dumps(session))+');')
        self.context.route('https://**/*', self.external)

    def tearDown(self):
        self.context.close()

    def external(self, route):
        url = route.request.url
        if '/customer-interactions' not in url:
            route.fulfill(status=200, content_type='application/json', body='{"items":[]}')
            return
        self.requests.append(route.request.url)
        self.assertTrue(route.request.headers.get('x-landerware-owner-session', '').startswith('lw_s_'))
        if route.request.method == 'GET':
            query = parse_qs(urlparse(url).query)
            rows = list(self.rows.values())
            if 'interaction_id' in query:
                rows = [r for r in rows if r['id'] == query['interaction_id'][0]]
            route.fulfill(json={'items': rows, 'next_cursor': None})
            return
        body = route.request.post_data_json
        self.writes.append(body)
        key = body['request_id']
        if self.conflict_next:
            self.conflict_next = False
            row = self.rows[body['input']['id']]
            row['version'] += 1
            row['document'] = {**row['document'], 'callNotes': 'Synthetic other-tab note'}
            route.fulfill(status=409, json={'error': 'Conflict'})
            return
        if key not in self.receipts:
            value = body['input']
            row = {**value, 'version': value['expected_version'] + 1}
            self.rows[value['id']] = row
            self.receipts[key] = {'interaction': row}
        if self.fail_next:
            self.fail_next = False
            route.fulfill(status=503, json={'error': 'Synthetic lost response after commit'})
            return
        route.fulfill(json=self.receipts[key])

    def visit(self, enabled=True):
        if enabled:
            html = (ROOT / 'docs/admin/customer-learning.html').read_text(encoding='utf-8').replace('content="disabled"', 'content="enabled"')
            self.context.route('**/admin/customer-learning.html', lambda route: route.fulfill(content_type='text/html', body=html))
        self.page.goto(f'http://127.0.0.1:{self.server.server_port}/admin/customer-learning.html')
        if enabled:
            self.page.wait_for_function("document.getElementById('storageStatus').textContent.includes('Stored interactions loaded')")

    def saved(self):
        self.page.wait_for_function("document.getElementById('storageStatus').textContent.startsWith('Saved on server')")

    def create(self):
        self.page.click('#newEmail')
        self.page.fill('#customer', 'Synthetic browser customer')
        self.page.fill('#callNotes', 'Synthetic inbound email')
        self.page.click('#saveCheckpoint')
        self.saved()

    def test_disabled_gate_preserves_prototype_without_crm_requests(self):
        self.visit(False)
        self.page.click('#newEmail')
        self.page.fill('#callNotes', 'Synthetic local prototype')
        self.assertIn('Local draft only', self.page.locator('#status').inner_text())
        self.assertEqual(self.requests, [])
        self.assertTrue(self.page.locator('#durableControls').is_hidden())
        self.assertEqual(self.errors, [])

    def test_save_reload_conflict_retry_and_safe_navigation(self):
        self.visit()
        self.create()
        self.assertTrue(self.page.locator('#newCall').is_disabled())
        self.assertTrue(self.page.locator('#finish').is_disabled())
        self.assertIsNone(self.page.evaluate("sessionStorage.getItem('lw-learning-studio-draft-v1')"))
        self.page.reload()
        self.page.wait_for_selector('#queueList button')
        self.page.click('#queueList button')
        self.saved()
        self.assertEqual(self.page.input_value('#callNotes'), 'Synthetic inbound email')
        self.fail_next = True
        self.page.fill('#callNotes', 'Synthetic uncertain save')
        self.page.click('#saveCheckpoint')
        self.page.wait_for_function("document.getElementById('storageStatus').textContent.startsWith('Save not confirmed')")
        self.assertTrue(self.page.locator('#newEmail').is_disabled())
        self.assertTrue(self.page.locator('#reloadStored').is_disabled())
        before = self.page.url
        self.page.click('a[href="/admin/dashboard.html"]')
        self.assertEqual(self.page.url, before)
        self.page.click('#retryCheckpoint')
        self.saved()
        self.assertEqual(self.writes[-1], self.writes[-2])
        self.conflict_next = True
        self.page.fill('#callNotes', 'Synthetic retained conflict draft')
        self.page.click('#saveCheckpoint')
        self.page.wait_for_function("document.getElementById('storageStatus').textContent.startsWith('Conflict')")
        self.page.click('#reviewConflict')
        self.page.wait_for_function("document.getElementById('serverConflict').textContent.includes('other-tab')")
        self.assertEqual(self.page.input_value('#callNotes'), 'Synthetic retained conflict draft')
        self.page.click('#keepConflictDraft')
        self.page.click('#saveCheckpoint')
        self.saved()
        self.assertEqual(self.writes[-1]['input']['expected_version'], 3)
        self.assertEqual(self.errors, [])

    def test_autosave_recovers_after_closing_the_tab(self):
        self.visit()
        self.page.click('#newEmail')
        self.page.fill('#callNotes', 'Synthetic autosaved before closing')
        self.saved()
        self.page.close()
        self.page = self.context.new_page()
        self.visit()
        self.page.click('#queueList button')
        self.saved()
        self.assertEqual(self.page.input_value('#callNotes'), 'Synthetic autosaved before closing')

    def test_module_load_failure_does_not_fall_back_to_tab_local_storage(self):
        self.context.route('**/customer-interaction-studio.mjs*', lambda route: route.abort())
        self.visit_enabled_without_wait()
        self.page.wait_for_function("document.getElementById('storageStatus').textContent.startsWith('Durable capture unavailable')")
        self.assertTrue(self.page.locator('#callNotes').is_disabled())
        self.assertIsNone(self.page.evaluate("sessionStorage.getItem('lw-learning-studio-draft-v1')"))
        self.assertEqual(self.requests, [])

    def visit_enabled_without_wait(self):
        html = (ROOT / 'docs/admin/customer-learning.html').read_text(encoding='utf-8').replace('content="disabled"', 'content="enabled"')
        self.context.route('**/admin/customer-learning.html', lambda route: route.fulfill(content_type='text/html', body=html))
        self.page.goto(f'http://127.0.0.1:{self.server.server_port}/admin/customer-learning.html')

    def test_session_lock_clears_private_fields_and_stops_edits(self):
        self.visit()
        self.create()
        self.page.evaluate("window.dispatchEvent(new CustomEvent('admin-auth-lock'))")
        self.assertEqual(self.page.input_value('#callNotes'), '')
        self.assertEqual(self.page.locator('#queueList button').count(), 0)
        self.assertTrue(self.page.locator('#callNotes').is_disabled())
        self.assertTrue(self.page.locator('#copyCase').is_disabled())
        self.assertEqual(self.errors, [])

if __name__ == '__main__':
    unittest.main()
