"""Synthetic local browser proof. All requests intercepted; no external I/O.

Run: python -B -m unittest tests.test_native_heartsaver_publication_browser -v
Requires Playwright and Chromium; unavailable browsers fail rather than skip.
"""
import copy
from datetime import timedelta
import json
import mimetypes
from pathlib import Path
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright
from tests.test_native_heartsaver_publication import (
    fixture, emit, seat_fixture, offers, generator, runner, selector, scope,
)

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://heartsaver-browser.invalid'


class HeartsaverPublicationBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def open(self, case=None, payload=None, width=390, feed=None):
        case = case or fixture(True)
        payload = payload or emit(case)
        self.feed = copy.deepcopy(feed if feed is not None else generator.public_selector_availability_payload(payload))
        self.requests = []
        self.errors = []
        self.blocked = []
        temp = tempfile.TemporaryDirectory(prefix='heartsaver-browser-')
        self.addCleanup(temp.cleanup)
        html = Path(temp.name) / 'heartsaver.html'
        html.write_text(generator.render_html(payload), encoding='utf-8')
        context = self.browser.new_context(viewport={'width': width, 'height': 900}, service_workers='block')
        self.addCleanup(context.close)

        def serve(route):
            request = route.request
            parsed = urlsplit(request.url)
            self.requests.append((request.method, request.url))
            if parsed.netloc != urlsplit(ORIGIN).netloc or request.method != 'GET':
                self.blocked.append(request.url)
                return route.abort()
            if parsed.path == '/heartsaver.html':
                return route.fulfill(path=str(html), content_type='text/html')
            if parsed.path == '/data/block-selector-availability/heartsaver.json':
                return route.fulfill(json=self.feed)
            if parsed.path.startswith(('/assets/', '/images/')):
                asset = (ROOT / 'docs' / parsed.path.lstrip('/')).resolve()
                if asset.is_relative_to(ROOT / 'docs') and asset.is_file():
                    return route.fulfill(path=str(asset), content_type=mimetypes.guess_type(str(asset))[0] or 'application/octet-stream')
            if parsed.path in ('/register/skills-session/', '/register/'):
                return route.fulfill(body='<h1>Local route assertion only</h1>', content_type='text/html')
            self.blocked.append(request.url)
            route.abort()

        context.route('**/*', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: self.errors.append(str(error)))
        page.clock.install(time=case.now)
        page.goto(ORIGIN + '/heartsaver.html')
        page.wait_for_function("availabilityState === 'ready'")
        self.assertEqual(self.errors, [])
        return page

    def select(self, page, cid):
        page.locator('[data-course-id="' + cid + '"]').first.click()
        self.assertEqual(page.evaluate('selectedCourseId'), cid)

    def route_for_selection(self, page, cid):
        row = page.evaluate("filteredDates().find(d => d.date === selectedDate).startTimes.find(s => s.startTime === selectedStart).courses[0]")
        self.assertEqual(row['courseId'], cid)
        url = page.locator('#course-list a.register-link').get_attribute('href')
        parsed = urlsplit(url)
        self.assertIn(parsed.netloc, ('', urlsplit(ORIGIN).netloc))
        self.assertEqual(parsed.path, '/register/skills-session/')
        query = parse_qs(parsed.query)
        self.assertEqual(query['course'], [cid])
        if cid in scope.HEARTSAVER:
            self.assertEqual(query['selectionId'], [row['selectionId']])
            self.assertEqual(row['coursePolicyKey'], 'heartsaver-full:' + cid + '.v1')
            published = next(o for o in offers(self.feed) if o.get('selectionId') == row['selectionId'])
            self.assertEqual(published['coursePolicyKey'], row['coursePolicyKey'])
        else:
            self.assertNotIn('selectionId', query)
            self.assertEqual(query['skillsContext'], [page.evaluate('selectedSkillsContext')])
            self.assertEqual(query['date'], [row['date']])
            self.assertEqual(query['startTime'], [row['startTime']])
        self.assertEqual(self.errors, [])
        return url

    def test_full_and_independent_skills_routes_mobile_and_desktop(self):
        for width in (390, 1280):
            with self.subTest(width=width):
                page = self.open(width=width)
                for cid in ('209809', '344085'):
                    self.select(page, cid)
                    self.route_for_selection(page, cid)
                skills = page.locator('[data-course-id="509474"]')
                self.assertEqual(skills.count(), 2)
                for index in range(2):
                    skills.nth(index).click()
                    self.assertIn('SKILLS SESSION ONLY', page.locator('#course-list').inner_text())
                    self.route_for_selection(page, '509474')
                self.select(page, '209809')
                url = self.route_for_selection(page, '209809')
                page.locator('#course-list a.register-link').click()
                page.wait_for_url('**/register/skills-session/**')
                self.assertEqual(parse_qs(urlsplit(page.url).query)['selectionId'], parse_qs(urlsplit(url).query)['selectionId'])
                self.assertTrue(all(method == 'GET' for method, _ in self.requests))

    def test_time_filter_and_start_selection_preserve_exact_identity(self):
        page = self.open(width=1280)
        self.select(page, '344085')
        before = self.route_for_selection(page, '344085')
        starts = page.locator('#start-list button:not(:disabled)')
        self.assertGreater(starts.count(), 1)
        starts.nth(1).click()
        after = self.route_for_selection(page, '344085')
        self.assertNotEqual(before, after)
        smart = page.get_by_role('textbox', name='Smart filter', exact=True)
        smart.fill('after 6pm'); smart.press('Enter')
        self.route_for_selection(page, '344085')
        self.assertGreaterEqual(page.evaluate('Number(selectedStart.split(":")[0])'), 18)
        smart.fill('Monday'); smart.press('Enter')
        self.assertEqual(page.locator('#course-list a.register-link').count(), 0)
        self.assertEqual(page.evaluate('[selectedDate,selectedStart]'), ['', ''])
        page.get_by_role('button', name='Clear timing filters', exact=True).click()
        self.route_for_selection(page, '344085')

    def test_held_seat_uses_existing_canonical_session_mobile_and_desktop(self):
        case, choice, source, demand = seat_fixture()
        schedule = runner.retained_projection({'sessions': []}, demand, heartsaver_enabled=True, now=case.now)
        case.sources.append(dict(source_event_id=source['canonical_session_id'], external_class_id=source['external_class_id'], start=source['start_at'], end=source['consumption_end_at'], instructor='Brian Ennis', course_id='344085', resource=case.room, location_resolution='location_resource_map', source_file='canonical_class_sessions', active_registration_count=1, count_available=True))
        seated = selector.seated_class_selector_offers(schedule_future_payload=schedule, selected_courses=case.courses, selected_course_ids=set(scope.HEARTSAVER), course_rules={'344085': {'scheduler_consumption_minutes': 150}})
        payload = runner.annotate_seated_offers(emit(case, seated), schedule)
        for width in (390, 1280):
            with self.subTest(width=width):
                page = self.open(case, payload, width)
                self.select(page, '344085')
                rows = page.evaluate('filteredDates().flatMap(d=>d.startTimes.flatMap(s=>s.courses))')
                self.assertEqual(len(rows), 1)
                self.assertEqual((rows[0]['capacity'], rows[0]['remainingSeats']), (3, 2))
                link = page.locator('#course-list a.register-link')
                parsed = urlsplit(link.get_attribute('href'))
                self.assertEqual(parsed.path, '/register/')
                self.assertEqual(parse_qs(parsed.query)['session'], [source['external_class_id']])
                self.assertNotIn('selectionId', parse_qs(parsed.query))
                link.click(); page.wait_for_url('**/register/?**')

    def test_expiry_removes_cta_even_when_global_feed_is_restamped(self):
        case = fixture()
        page = self.open(case)
        self.select(page, '209809')
        self.route_for_selection(page, '209809')
        self.feed['generatedAt'] = (case.now + timedelta(minutes=16)).isoformat()
        self.feed['validUntil'] = (case.now + timedelta(hours=1)).isoformat()
        page.clock.fast_forward(16 * 60 * 1000)
        page.evaluate('loadResolvedAvailability()')
        page.wait_for_function("availabilityState === 'ready'")
        self.assertEqual(page.locator('#course-list a.register-link').count(), 0)
        self.assertEqual(page.evaluate('[selectedDate,selectedStart]'), ['', ''])
        self.assertEqual(self.errors, [])

    def test_disabled_full_policy_keeps_only_independent_skills(self):
        case = fixture(True)
        for proof in case.native_policy['_heartsaverProof']['courses'].values():
            proof['nativePublicationEnabled'] = False
        page = self.open(case)
        self.assertEqual({o['courseId'] for o in offers(self.feed)}, {'509474'})
        for cid in scope.HEARTSAVER:
            self.select(page, cid)
            self.assertEqual(page.locator('#course-list a.register-link').count(), 0)
        self.select(page, '509474')
        self.route_for_selection(page, '509474')

    def test_empty_refresh_clears_chosen_time_and_registration_link(self):
        page = self.open()
        self.select(page, '344085')
        self.route_for_selection(page, '344085')
        self.feed['dates'] = []
        page.evaluate('loadResolvedAvailability()')
        page.wait_for_function("availabilityState === 'ready'")
        self.assertEqual(page.evaluate('[selectedDate,selectedStart]'), ['', ''])
        self.assertEqual(page.locator('#course-list a.register-link').count(), 0)
        self.assertEqual(page.locator('#start-list button:not(:disabled)').count(), 0)
        self.assertEqual(self.errors, [])


if __name__ == '__main__':
    unittest.main()
