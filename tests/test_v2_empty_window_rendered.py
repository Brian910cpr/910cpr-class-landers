"""Offline rendered proof of the saved baseline and corrected free-window receipts."""
import json
import unittest
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

class EmptyWindowRenderedTests(unittest.TestCase):
    def test_before_after_desktop_mobile_bookable_windows(self):
        receipt=json.loads((ROOT/'data/audit/v2_empty_window_before_after.json').read_text(encoding='utf-8'))
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True)
            try:
                for width in (1440,390):
                    for state in ('before','after'):
                        with self.subTest(width=width,state=state):
                            page=browser.new_page(viewport={'width':width,'height':1000},timezone_id='America/New_York')
                            page.add_init_script("const NativeDate=Date;const fixtureNow=NativeDate.parse('2026-10-05T16:00:00Z');window.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[fixtureNow]));}static now(){return fixtureNow;}};")
                            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                            def local(route):
                                path=urlparse(route.request.url).path
                                if path=='/heartsaver.html':route.fulfill(status=200,content_type='text/html',path=str(ROOT/f'data/audit/v2_empty_window_{state}.html'))
                                elif path.startswith('/data/block-selector-availability/'):
                                    route.fulfill(status=200,content_type='application/json',body=json.dumps(receipt[state]['feed']))
                                elif path.startswith('/assets/') and (ROOT/'docs'/path.lstrip('/')).is_file():
                                    route.fulfill(status=200,path=str(ROOT/'docs'/path.lstrip('/')))
                                else:route.fulfill(status=204,body='')
                            page.route('**/*',local)
                            page.goto('https://fixture.test/heartsaver.html',wait_until='domcontentloaded')
                            page.wait_for_function("typeof availabilityReady==='function' && availabilityReady()")
                            button=page.locator('[data-course-id="209809"]')
                            if not button.is_visible():page.locator('#show-all-toggle').check()
                            button.click()
                            starts=page.evaluate('filteredDates().flatMap(d=>d.startTimes.map(t=>t.startTime))')
                            self.assertEqual(starts,[] if state=='before' else ['10:00','11:00','12:00'])
                            if state=='after':
                                page.locator('#start-list button').filter(has_text='12:00').click()
                                href=page.locator('#course-list a').first.get_attribute('href')
                                self.assertIn('courseId=209809',href);self.assertIn('startTime=12:00',href)
                            self.assertFalse(errors)
                            page.close()
            finally:browser.close()

if __name__=='__main__':unittest.main()
