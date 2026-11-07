"""Pool page share contracts. Requires local Playwright/Chromium; no outbound traffic."""
import json
from pathlib import Path
import re
import unittest
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class PoolShareBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def open(self, identity, native="absent", clipboard="success", prompt="value", cookie="", event_url=None, path=None):
        path = path or '/' + identity
        context = self.browser.new_context(viewport={"width": 390, "height": 844})
        self.addCleanup(context.close)
        if cookie:
            context.add_cookies([{"name": cookie, "value": "1", "url": "https://www.910cpr.com"}])
        html = (ROOT / f'docs/{identity}.html').read_text(encoding='utf-8')
        if event_url is not None:
            html = re.sub(r'name="community-facebook-event-url" content="[^"]*"',
                          'name="community-facebook-event-url" content="' + event_url + '"', html)
        self.requests = []

        def serve(route):
            self.requests.append(route.request.url)
            target = urlparse(route.request.url).path
            if target == path:
                route.fulfill(content_type='text/html', body=html)
            elif target in ('/assets/community-share.js', '/assets/community-share.css', '/assets/analytics-attribution.js', '/assets/pool-registration.js', '/assets/pool-registration.css'):
                route.fulfill(content_type='text/css' if target.endswith('.css') else 'application/javascript',
                              body=(ROOT / 'docs' / target.lstrip('/')).read_text(encoding='utf-8'))
            else:
                route.fulfill(status=200, body='')

        context.route('**/*', serve)
        options = json.dumps(dict(native=native, clipboard=clipboard, prompt=prompt))
        context.add_init_script("""(() => {
          const options = OPTIONS; window.copies = []; window.prompts = [];
          Object.defineProperty(navigator, 'share', {configurable:true, value: options.native === 'absent' ? undefined : async () => {
            if (options.native !== 'success') throw {name:options.native === 'cancel' ? 'AbortError' : 'NotAllowedError'};
          }});
          Object.defineProperty(navigator, 'clipboard', {configurable:true, value: options.clipboard === 'absent' ? undefined : {writeText:async value => {
            if (options.clipboard === 'error') throw Error('blocked'); window.copies.push(value);
          }}});
          window.prompt = (title,value) => {window.prompts.push(value); if(options.prompt === 'error') throw Error('blocked'); return options.prompt === 'cancel' ? null : value};
          Object.defineProperty(window, 'sessionStorage', {get(){throw Error('blocked')}});
          document.addEventListener('click',event=>{if(event.target.closest('a[data-share]')) window.navigationPrevented=event.defaultPrevented});
        })();""".replace('OPTIONS', options))
        page = context.new_page()
        page.goto('https://www.910cpr.com' + path + '?utm_source=private@example.test&phone=5551234567')
        return page

    def events(self, page, identity, kind='click'):
        return page.evaluate("name => (window.dataLayer || []).filter(e=>e.event===name)", identity + '_share_' + kind)

    def control(self, page, placement, channel):
        return page.locator(f'[data-share-placement="{placement}"] [data-share="{channel}"]')

    def test_both_pages_all_controls_mobile_keyboard_and_registration_preserved(self):
        for identity in ('pool', 'poolbls'):
            page = self.open(identity)
            page.wait_for_function("!document.getElementById('seatLabel').textContent.includes('Checking')")
            before = page.locator('#registration').inner_html()
            request_count = len(self.requests)
            for placement in ('top', 'bottom'):
                self.assertEqual(page.locator(f'[data-share-placement="{placement}"] svg').count(), 5)
                for channel in ('native', 'facebook', 'sms', 'email', 'copy'):
                    control = self.control(page, placement, channel)
                    if channel == 'facebook':
                        expected = {'pool':'https://www.facebook.com/events/3023534924674805/',
                                    'poolbls':'https://www.facebook.com/events/1039252512546187/'}[identity]
                        self.assertEqual(control.get_attribute('href'), expected)
                        with page.expect_popup() as popup:
                            control.locator('svg').click()
                        popup.value.wait_for_url(expected)
                        self.assertEqual(popup.value.url, expected)
                        popup.value.close()
                    else:
                        control.locator('svg').click()
                    event = self.events(page, identity)[-1]
                    self.assertEqual((event['page_id'], event['share_placement'], event['share_channel']),
                                     (identity, placement, 'text' if channel == 'sms' else channel))
                    if channel == 'facebook':
                        self.assertEqual(event['share_target'], 'facebook_event')
                    if channel in ('facebook', 'sms', 'email'):
                        self.assertFalse(page.evaluate('window.navigationPrevented'))
            button = self.control(page, 'bottom', 'copy')
            button.focus(); button.press('Enter'); button.press('Space'); button.click()
            self.assertEqual(len(self.events(page, identity)), 13)
            self.assertEqual(page.locator('#registration').inner_html(), before)
            self.assertFalse(any('public-event-registration' in url for url in self.requests[request_count:]))
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            self.assertTrue(all(value == 'https://www.910cpr.com/' + identity for value in page.evaluate('window.copies')))
            for event in self.events(page, identity) + self.events(page, identity, 'result'):
                self.assertEqual(set(event), {'event','page_id','share_channel','share_placement','share_target','share_method','share_outcome'})
                for private in ('private@example', '5551234567', 'https:'):
                    self.assertNotIn(private, json.dumps(event))

    def test_native_outcomes_and_fallbacks_do_not_double_count(self):
        for identity in ('pool', 'poolbls'):
            for native, clipboard, prompt, outcomes in (
                ('success','success','value',['resolved']), ('cancel','success','value',['cancelled']),
                ('absent','success','value',['succeeded']), ('error','success','value',['failed','succeeded']),
                ('error','error','value',['failed','failed','prompted']),
                ('absent','absent','cancel',['failed','cancelled']), ('absent','error','error',['failed','failed'])):
                with self.subTest(identity=identity,native=native,clipboard=clipboard,prompt=prompt):
                    page=self.open(identity,native=native,clipboard=clipboard,prompt=prompt)
                    self.control(page,'top','native').click()
                    self.assertEqual(len(self.events(page,identity)),1)
                    self.assertEqual([e['share_outcome'] for e in self.events(page,identity,'result')],outcomes)
                    if native=='cancel':
                        self.assertEqual(page.evaluate('window.copies.length+window.prompts.length'),0)

    def test_exclusion_and_analytics_failure_preserve_copy(self):
        for identity in ('pool','poolbls'):
            for cookie in ('analytics_excluded','lw_analytics_excluded'):
                page=self.open(identity,cookie=cookie)
                self.control(page,'top','copy').click()
                self.assertEqual(self.events(page,identity),[])
                self.assertEqual(page.evaluate('window.copies.length'),1)
            page=self.open(identity,path='/internal/'+identity)
            self.control(page,'top','copy').click()
            self.assertEqual(self.events(page,identity),[])
            for failure in ('delete window.dataLayer; delete window.LanderWareAnalytics',
                            "window.dataLayer.push=()=>{throw Error('blocked')}",
                            "Object.defineProperty(document,'cookie',{get(){throw Error('blocked')}})"):
                page=self.open(identity)
                page.evaluate('()=>{'+failure+';}')
                self.control(page,'bottom','copy').click()
                self.assertEqual(page.evaluate('window.copies.length'),1)

    def test_event_configuration_blank_invalid_and_verified_destinations(self):
        for identity in ('pool','poolbls'):
            for event_url in ('','https://example.test/events/123/','https://www.facebook.com/events/123456789/'):
                page=self.open(identity,event_url=event_url)
                expected=event_url if event_url.startswith('https://www.facebook.com/events/') else 'https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Fwww.910cpr.com%2F'+identity
                for placement in ('top','bottom'):
                    control=self.control(page,placement,'facebook')
                    self.assertEqual(control.get_attribute('href'),expected)
                    with page.expect_popup() as popup:
                        control.focus(); control.press('Enter')
                    popup.value.close()
                    self.assertEqual(self.events(page,identity)[-1]['share_target'],'facebook_event' if event_url==expected else 'class_page')


if __name__ == '__main__':
    unittest.main()
