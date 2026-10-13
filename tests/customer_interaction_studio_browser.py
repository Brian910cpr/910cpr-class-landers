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
        self.events = []
        self.tasks = {}
        self.task_conflict = False
        self.fail_task_read = False
        self.task_pages = False
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
            if query.get('collection') == ['tasks'] and self.fail_task_read:
                route.fulfill(status=503, json={'error': 'Synthetic task read failure'})
                return
            rows = list(self.tasks.values()) if query.get('collection') == ['tasks'] else self.events if query.get('collection') == ['interruptions'] else list(self.rows.values())
            if 'interaction_id' in query:
                rows = [r for r in rows if r.get('interaction_id' if query.get('collection') == ['tasks'] else 'id') == query['interaction_id'][0]]
            if query.get('collection') == ['tasks'] and self.task_pages and 'before' not in query:
                route.fulfill(json={'items': [], 'next_cursor': {'before': '2026-10-13T12:00:00.123456Z', 'before_id': '00000000-0000-4000-8000-000000000001'}})
                return
            route.fulfill(json={'items': rows, 'next_cursor': None})
            return
        body = route.request.post_data_json
        self.writes.append(body)
        key = body['request_id']
        if body.get('operation') == 'save_task':
            if self.task_conflict:
                route.fulfill(status=409, json={'error': 'Synthetic task conflict'})
                return
            if key not in self.receipts:
                value = body['input']
                task = {**value, 'version': value['expected_version'] + 1, 'due_at': value.get('due_at')}
                self.tasks[task['id']] = task
                self.receipts[key] = {'task': task}
            if self.fail_next:
                self.fail_next = False
                route.fulfill(status=503, json={'error': 'Synthetic lost task response after commit'})
                return
            route.fulfill(json=self.receipts[key])
            return
        if self.conflict_next:
            self.conflict_next = False
            row = self.rows[body['input']['id']]
            row['version'] += 1
            row['document'] = {**row['document'], 'callNotes': 'Synthetic other-tab note'}
            route.fulfill(status=409, json={'error': 'Conflict'})
            return
        if body.get('operation') in ('interrupt', 'resume'):
            value = body['input']
            if key not in self.receipts:
                if any(self.rows.get(v['id'], {}).get('version', 0) != v['expected_version'] for v in [value['previous'], value['active']]):
                    route.fulfill(status=409, json={'error': 'Conflict'})
                    return
                result = {name: {**value[name], 'version': value[name]['expected_version'] + 1} for name in ['previous', 'active']}
                result.update(request_id=key, operation=body['operation'])
                for name in ['previous', 'active']:
                    self.rows[result[name]['id']] = result[name]
                self.receipts[key] = {'switch': result}
                self.events.insert(0, {'request_id': key, 'input': {**value, 'operation': body['operation']}, 'result': result})
            if self.fail_next:
                self.fail_next = False
                route.fulfill(status=503, json={'error': 'Synthetic lost switch response after commit'})
                return
            route.fulfill(json=self.receipts[key])
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
        self.assertTrue(self.page.locator('#newCall').is_enabled())
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

    def test_atomic_interrupt_reload_and_resume(self):
        self.visit()
        self.create()
        previous_id = next(iter(self.rows))
        self.page.click('#newCall')
        self.saved()
        self.assertEqual(self.page.input_value('#kind'), 'phone')
        self.assertEqual(self.rows[previous_id]['status'], 'paused')
        self.assertEqual(self.rows[previous_id]['document']['callNotes'], 'Synthetic inbound email')
        self.assertTrue(self.page.locator('#newCall').is_disabled())
        self.page.fill('#callNotes', 'Synthetic unknown caller raw note')
        self.page.click('#saveCheckpoint')
        self.saved()
        self.page.reload()
        self.page.wait_for_selector('#queueList button')
        self.page.locator('#queueList button').filter(has_text='phone').click()
        self.saved()
        self.assertEqual(self.page.input_value('#callNotes'), 'Synthetic unknown caller raw note')
        self.page.click('#resumePrevious')
        self.saved()
        self.assertEqual(self.page.input_value('#kind'), 'email')
        self.assertEqual(self.page.input_value('#callNotes'), 'Synthetic inbound email')
        self.assertEqual(self.rows[previous_id]['status'], 'in_progress')
        phone = next(r for r in self.rows.values() if r['kind'] == 'phone')
        self.assertEqual(phone['status'], 'resolved')
        self.assertIsNone(phone['person_id'])
        self.assertEqual(len(self.events), 2)
        self.assertEqual(self.errors, [])

    def test_uncertain_atomic_switch_freezes_both_drafts_and_retries_identically(self):
        self.visit()
        self.create()
        self.fail_next = True
        self.page.click('#newCall')
        self.page.wait_for_function("document.getElementById('storageStatus').textContent.startsWith('Atomic switch not confirmed')")
        self.assertEqual(self.page.input_value('#kind'), 'email')
        self.assertTrue(self.page.locator('#callNotes').is_disabled())
        self.assertTrue(self.page.locator('#newEmail').is_disabled())
        self.assertTrue(self.page.locator('#resumePrevious').is_disabled())
        self.page.click('#retryCheckpoint')
        self.saved()
        self.assertEqual(self.writes[-1], self.writes[-2])
        self.assertEqual(len(self.events), 1)
        self.assertEqual(len(self.rows), 2)
        self.assertEqual(self.page.input_value('#kind'), 'phone')
        self.fail_next = True
        self.page.click('#resumePrevious')
        self.page.wait_for_function("document.getElementById('storageStatus').textContent.startsWith('Atomic switch not confirmed')")
        self.page.click('#retryCheckpoint')
        self.saved()
        self.assertEqual(self.writes[-1], self.writes[-2])
        self.assertEqual(len(self.events), 2)
        self.assertEqual(self.page.input_value('#kind'), 'email')
        self.assertEqual(self.errors, [])

    def test_atomic_stale_conflict_retains_both_drafts_for_export(self):
        self.visit()
        self.create()
        next(iter(self.rows.values()))['version'] += 1
        self.page.click('#newCall')
        self.page.wait_for_function("document.getElementById('storageStatus').textContent.startsWith('Atomic switch conflict')")
        self.assertTrue(self.page.locator('#retryCheckpoint').is_disabled())
        self.assertTrue(self.page.locator('#callNotes').is_disabled())
        self.assertEqual(self.page.input_value('#callNotes'), 'Synthetic inbound email')
        with self.page.expect_download() as pending:
            self.page.click('#downloadCase')
        data = json.loads(Path(pending.value.path()).read_text())
        self.assertEqual(data['pendingSwitch']['input']['previous']['document']['callNotes'], 'Synthetic inbound email')
        self.assertEqual(data['pendingSwitch']['input']['active']['kind'], 'phone')
        self.assertEqual(len(self.rows), 1)
        self.assertEqual(self.errors, [])

    def follow_up(self):
        self.page.locator('summary').filter(has_text='Capture promised follow-up').click()
        self.page.fill('#followUpTitle', 'Synthetic promised callback')
        self.page.fill('#followUpEvidence', 'Synthetic owner promised a callback')

    def test_follow_up_uncertain_save_reload_and_resume_preserves_obligation(self):
        self.visit()
        self.create()
        self.page.click('#newCall')
        self.saved()
        self.follow_up()
        self.assertTrue(self.page.locator('#resumePrevious').is_disabled())
        before = self.page.url
        self.page.click('a[href="/admin/dashboard.html"]')
        self.assertEqual(self.page.url, before)
        self.fail_next = True
        self.page.click('#saveFollowUp')
        self.page.wait_for_function("document.getElementById('storageStatus').textContent.startsWith('Follow-up not confirmed')")
        self.assertTrue(self.page.locator('#newEmail').is_disabled())
        self.assertTrue(self.page.locator('#callNotes').is_disabled())
        self.page.click('#retryFollowUp')
        self.saved()
        self.assertEqual(self.writes[-1], self.writes[-2])
        self.assertEqual(len(self.tasks), 1)
        self.task_pages = True
        self.page.reload()
        self.page.wait_for_selector('#queueList button')
        self.page.locator('#queueList button').filter(has_text='phone').click()
        self.saved()
        self.assertIn('Synthetic promised callback', self.page.locator('#storedFollowUps').text_content())
        self.page.click('#resumePrevious')
        self.saved()
        phone = next(r for r in self.rows.values() if r['kind'] == 'phone')
        self.assertEqual(phone['status'], 'follow_up_due')
        self.assertEqual(next(iter(self.tasks.values()))['status'], 'pending')
        self.assertEqual(self.errors, [])

    def test_follow_up_conflict_export_and_privacy_lock(self):
        self.visit()
        self.create()
        self.follow_up()
        self.task_conflict = True
        self.page.click('#saveFollowUp')
        self.page.wait_for_function("document.getElementById('storageStatus').textContent.startsWith('Follow-up conflict')")
        self.assertTrue(self.page.locator('#retryFollowUp').is_disabled())
        self.assertTrue(self.page.locator('#reloadStored').is_disabled())
        with self.page.expect_download() as pending:
            self.page.click('#downloadCase')
        data = json.loads(Path(pending.value.path()).read_text())
        self.assertEqual(data['pendingTask']['input']['provenance']['evidence'], 'Synthetic owner promised a callback')
        self.page.evaluate("window.dispatchEvent(new CustomEvent('admin-auth-lock'))")
        self.assertEqual(self.page.input_value('#followUpEvidence'), '')
        self.assertEqual(self.page.locator('#storedFollowUps').inner_text(), '')
        self.assertTrue(self.page.locator('#saveFollowUp').is_disabled())
        self.assertEqual(self.errors, [])

    def test_resume_fails_closed_when_follow_up_read_fails(self):
        self.visit()
        self.create()
        self.page.click('#newCall')
        self.saved()
        self.fail_task_read = True
        count = len(self.writes)
        self.page.click('#resumePrevious')
        self.page.wait_for_function("document.getElementById('storageStatus').textContent.startsWith('Resume unavailable')")
        self.assertEqual(len(self.writes), count)
        self.assertEqual(self.page.input_value('#kind'), 'phone')
        self.fail_task_read = False
        self.page.click('#resumePrevious')
        self.saved()
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
