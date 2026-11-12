"""Real generated BLS selector + existing generic checkout, synthetic I/O only.

Run in authorized CI: python -B -m unittest tests.test_native_bls_publication_browser -v
Requires Playwright/Chromium; missing browsers fail, never skip. No submission,
payment, mail, upload, production input, socket server, or external request runs.
"""
import copy
import json
from datetime import timedelta
import mimetypes
from pathlib import Path
import tempfile
import unittest
from urllib.parse import parse_qs, urlencode, urlsplit

from playwright.sync_api import sync_playwright
from tests.native_bls_browser_fixtures import (
    ROOT, fixture, seated_fixture, offers, selection, generic_model,
    public_selector_availability_payload, render_html, runner,
)

ORIGIN = 'https://bls-browser.invalid'
API = 'https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/public-registration/generic/'


class BlsPublicationBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def open(self, case=None, payload=None, width=390, remaining=2, bundle=True, path='/bls.html', saved=False):
        if case is None:
            case, payload = fixture()
        self.case = case
        self.feed = copy.deepcopy(public_selector_availability_payload(payload))
        self.requests, self.errors, self.api_packets, self.forbidden = [], [], [], []
        self.api_keys = []
        temp = tempfile.TemporaryDirectory(prefix='bls-browser-')
        self.addCleanup(temp.cleanup)
        html = Path(temp.name) / 'bls.html'
        html.write_text(render_html(payload), encoding='utf-8')
        context = self.browser.new_context(viewport={'width': width, 'height': 900}, service_workers='block')
        self.addCleanup(context.close)

        def serve(route):
            request = route.request
            parsed = urlsplit(request.url)
            self.requests.append((request.method, request.url))
            # Saved nonce headers require an intercepted CORS preflight. It
            # grants GET only; submission/payment/upload methods remain blocked.
            if saved and request.method == 'OPTIONS' and request.url.startswith(API) and parsed.path in (urlsplit(API).path+'form', urlsplit(API).path+'status'):
                return route.fulfill(status=204, headers={'access-control-allow-origin': ORIGIN,
                    'access-control-allow-methods': 'GET', 'access-control-allow-headers': 'idempotency-key'})
            # Exactly one intercepted read API is allowed. No request goes out.
            if request.method != 'GET':
                self.forbidden.append(request.url)
                return route.abort()
            if request.url.startswith(API):
                action = parsed.path.removeprefix(urlsplit(API).path)
                if action not in (('form', 'status') if saved else ('form',)):
                    self.forbidden.append(request.url)
                    return route.abort()
                self.api_keys.append(request.headers.get('idempotency-key'))
                packet = generic_model(case, self.feed, selection(request.url), remaining=remaining, bundleEnabled=bundle, saved=saved, action=action, key=request.headers.get('idempotency-key'))
                self.api_packets.append(packet)
                return route.fulfill(status=packet['status'], json=packet['body'], headers={'access-control-allow-origin': ORIGIN})
            if parsed.netloc != urlsplit(ORIGIN).netloc:
                return route.abort()
            if parsed.path == '/bls.html':
                return route.fulfill(path=str(html), content_type='text/html')
            if parsed.path == '/data/block-selector-availability/bls.json':
                return route.fulfill(json=self.feed)
            if parsed.path.startswith(('/assets/', '/images/', '/register/')):
                relative = parsed.path.lstrip('/')
                if parsed.path.endswith('/'):
                    relative += 'index.html'
                asset = (ROOT / 'docs' / relative).resolve()
                if asset.is_relative_to((ROOT / 'docs').resolve()) and asset.is_file():
                    return route.fulfill(path=str(asset), content_type=mimetypes.guess_type(str(asset))[0] or 'application/octet-stream')
            return route.abort()

        context.route('**/*', serve)
        if saved:
            # Use the exact legacy storage key read by the existing generic UI.
            chosen = selection(path)
            storage_key = 'skillsCheckout:' + json.dumps([chosen.get(k, '') for k in
                ('course', 'date', 'startTime', 'location', 'instructor', 'skillsContext')], separators=(',', ':'))
            context.add_init_script('sessionStorage.setItem(' + json.dumps(storage_key) + ', "44444444-1111-4111-8111-111111111111")')
        page = context.new_page()
        page.on('pageerror', lambda error: self.errors.append(str(error)))
        page.clock.install(time=case.now)
        page.goto(ORIGIN + path)
        if path == '/bls.html':
            page.wait_for_function("availabilityState === 'ready'")
        return page

    def select(self, page, cid):
        page.locator('[data-course-id="' + cid + '"]').first.click()
        self.assertEqual(page.evaluate('selectedCourseId'), cid)
        row = page.evaluate('filteredDates().find(d=>d.date===selectedDate).startTimes.find(s=>s.startTime===selectedStart).courses[0]')
        link = page.locator('#course-list a.register-link')
        self.assertEqual(link.count(), 1)
        self.assertEqual(link.get_attribute('href'), row['registrationUrl'])
        self.assertEqual(selection(row['registrationUrl']), dict(course=cid, skillsContext='bls-skills', selectionId=row['selectionId']))
        self.assertEqual(row['physicalCourseId'], '509474')
        self.assertEqual(row['capacity'], 2)
        return row

    def check_form(self, page, cid, remaining=2):
        page.locator('#checkout-form').wait_for()
        self.assertEqual(page.locator('form').count(), 1)
        self.assertEqual(page.locator('[data-choice]').count(), 1)
        choice = 'skills_only' if cid == '509474' else 'online_and_skills'
        self.assertTrue(page.locator('[data-choice=""][value="' + choice + '"]').is_checked())
        self.assertEqual(page.locator('#total').inner_text(), 'Estimated total: $55.00' if cid == '509474' else 'Estimated total: $95.00')
        self.assertIn('Class capacity: 2.', page.locator('#app header').inner_text())
        self.assertIn('Seats currently available: ' + str(remaining) + '.', page.locator('#app header').inner_text())
        self.assertEqual(self.api_packets[-1]['body']['selection']['course'], cid)
        self.assertEqual(self.errors, [])
        self.assertEqual(self.forbidden, [])
        self.assertTrue(all(method == 'GET' for method, _ in self.requests))

    def test_distinct_packages_labels_prices_and_exact_links_mobile_desktop(self):
        for width in (390, 1280):
            for cid in ('509474', '210549'):
                with self.subTest(width=width, cid=cid):
                    page = self.open(width=width)
                    buttons = page.locator('[data-course-id="' + cid + '"]').first.inner_text()
                    self.assertIn('$55' if cid == '509474' else '$95', buttons)
                    self.assertIn('Skills' if cid == '509474' else 'HeartCode', buttons)
                    first = self.select(page, '509474')
                    second = self.select(page, '210549')
                    self.assertEqual(first['nativeOfferId'], second['nativeOfferId'])
                    self.assertNotEqual(first['selectionId'], second['selectionId'])
                    self.assertNotEqual(first['registrationUrl'], second['registrationUrl'])
                    row = self.select(page, cid)
                    page.locator('#course-list a.register-link').click()
                    page.wait_for_url('**/register/checkout/**')
                    self.assertEqual(selection(page.url), selection(row['registrationUrl']))
                    self.check_form(page, cid)

    def test_held_aliases_reuse_canonical_seat_and_generic_form_mobile_desktop(self):
        case, payload, sid = seated_fixture()
        for width in (390, 1280):
            for cid in ('509474', '210549'):
                with self.subTest(width=width, cid=cid):
                    page = self.open(case, payload, width, remaining=1)
                    row = self.select(page, cid)
                    self.assertEqual(row['sourceSessionId'], sid)
                    self.assertEqual(row['remainingSeats'], 1)
                    self.assertEqual(row['nativeOfferId'], 'native-skills-seated:' + sid)
                    page.locator('#course-list a.register-link').click()
                    page.wait_for_url('**/register/checkout/**')
                    self.check_form(page, cid, remaining=1)
                    self.assertTrue(page.locator('#add-student').is_disabled())
                    self.assertEqual(page.locator('iframe').count(), 0)

    def test_bundle_unready_keeps_only55_bookable(self):
        case, payload = fixture()
        case.native_policy['_blsSkillsProof']['bundleEnabled'] = False
        payload = runner.project_bls_offers(payload, {'sessions': []}, case.native_policy, case.now)
        page = self.open(case, payload, bundle=False)
        self.assertEqual({row['courseId'] for row in offers(self.feed)}, {'509474'})
        self.select(page, '509474')
        # A configured but unavailable package must not acquire a link.
        button = page.locator('[data-course-id="210549"]')
        if button.count():
            button.first.click()
            self.assertEqual(page.locator('#course-list a.register-link').count(), 0)
        self.select(page, '509474')
        page.locator('#course-list a.register-link').click()
        self.check_form(page, '509474')

    def test_default_off_matches_legacy_generated_display(self):
        from scripts.block_start_time_selector import load_block_schedule_page_configs
        case, payload = fixture()
        base = load_block_schedule_page_configs()['bls']
        payload['offers'] = []
        payload['pageConfig'] = runner.native_page_config(base)
        default_html = render_html(payload)
        baseline = self.open(case, payload, width=1280)
        baseline_text = baseline.locator('#course-option-list').inner_text()
        payload['pageConfig'] = runner.native_page_config(base, bls_skills_enabled=False, bls_bundle_enabled=False)
        self.assertEqual(default_html, render_html(payload))
        page = self.open(case, payload, width=1280)
        self.assertEqual(page.locator('#course-option-list').inner_text(), baseline_text)
        self.assertEqual(page.locator('#course-list a.register-link').count(), 0)
        self.assertNotIn('HeartCode BLS including online access', page.locator('body').inner_text())

    def test_expired_original_offer_cannot_be_selected_after_global_restamp(self):
        case, payload = fixture()
        page = self.open(case, payload)
        self.select(page, '210549')
        self.feed['generatedAt'] = (case.now+timedelta(minutes=16)).isoformat()
        self.feed['validUntil'] = (case.now+timedelta(hours=1)).isoformat()
        page.clock.set_system_time(case.now+timedelta(minutes=16))
        # Click the already-rendered CTA: its listener must reject the stale lease.
        before = page.url
        page.locator('#course-list a.register-link').click()
        page.wait_for_function("availabilityState === 'ready'")
        self.assertEqual(page.url, before)
        self.assertEqual(page.locator('#course-list a.register-link').count(), 0)
        self.assertEqual(page.evaluate('[selectedDate,selectedStart]'), ['', ''])
        self.assertEqual(self.api_packets, [])
        self.assertEqual(self.errors, [])

    def test_legacy_dated55_link_uses_real_generic_model_without_upgrade(self):
        case, payload = fixture()
        row = next(row for row in offers(public_selector_availability_payload(payload)) if row['courseId']=='509474')
        legacy = dict(course='210549', skillsContext='bls-skills', date=row['date'], startTime=row['startTime'], instructor=row['instructor'], location=row['location'])
        for width in (390, 1280):
            page = self.open(case, payload, width, bundle=False, path='/register/skills-session/?'+urlencode(legacy))
            self.check_form(page, '509474')
            self.assertEqual(page.locator('[data-choice][value="online_and_skills"]').count(), 0)

    def test_saved_legacy55_receipt_keeps_original_nonce_and_amount(self):
        case, payload = fixture()
        row = next(row for row in offers(public_selector_availability_payload(payload)) if row['courseId']=='509474')
        legacy = dict(course='210549', skillsContext='bls-skills', date=row['date'], startTime=row['startTime'], instructor=row['instructor'], location=row['location'])
        page = self.open(case, payload, bundle=False, saved=True, path='/register/skills-session/?'+urlencode(legacy))
        page.wait_for_function("document.getElementById('total')?.textContent.startsWith('Saved total: $55.00')")
        page.wait_for_function("document.querySelector('[data-choice]')?.disabled === true")
        self.assertTrue(page.locator('[data-choice][value="skills_only"]').is_checked())
        self.assertEqual(page.locator('form').count(), 1)
        self.assertTrue(self.api_keys)
        self.assertEqual(set(self.api_keys), {'44444444-1111-4111-8111-111111111111'})
        self.assertTrue(all(c['name']=='native_checkout_receipt' for packet in self.api_packets for c in packet['calls']))
        self.assertEqual(self.forbidden, [])
        self.assertEqual(self.errors, [])

    def test_bare_stale_ambiguous_and_final_seat_legacy_links_fail_closed(self):
        case, payload = fixture()
        row = next(row for row in offers(public_selector_availability_payload(payload)) if row['courseId']=='509474')
        legacy = dict(course='210549', skillsContext='bls-skills', date=row['date'], startTime=row['startTime'])
        for mode in ('bare', 'stale', 'ambiguous', 'no-seat'):
            with self.subTest(mode=mode):
                page = self.open(case, payload, remaining=0 if mode=='no-seat' else 2)
                chosen = dict(course='210549', skillsContext='bls-skills') if mode=='bare' else legacy
                if mode == 'stale':
                    for offer in offers(self.feed):
                        offer['validUntil'] = case.now.isoformat()
                if mode == 'ambiguous':
                    for day in self.feed['dates']:
                        for slot in day['startTimes']:
                            slot['courses'] += copy.deepcopy(slot['courses'])
                page.goto(ORIGIN+'/register/skills-session/?'+urlencode(chosen))
                page.get_by_role('link', name='Return to classes').wait_for()
                self.assertEqual(page.locator('#checkout-form').count(), 0)
                self.assertEqual(self.api_packets[-1]['status'], 409)
                self.assertEqual(self.forbidden, [])


if __name__ == '__main__':
    unittest.main()
