"""Synthetic browser CI only. No providers, payments, mail, or external network.

Run explicitly in approved CI: python -m unittest tests.test_native_pediatric_publication_browser -v
Not executed locally where Chromium is denied.
"""
import copy,json,mimetypes,subprocess,unittest
from datetime import timedelta
from urllib.parse import urlsplit,parse_qs
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.test_native_pediatric_publication import fixture,endpoint,p,generator,runner,selector
ROOT=Path(__file__).resolve().parents[1]
ORIGIN='https://pediatric-browser.invalid'
API='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/public-registration/generic/'

class PediatricPublicationBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime=sync_playwright().start();cls.browser=cls.runtime.chromium.launch()
    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.runtime.stop()
    def open(self,width):
        now,policy,row,seats=fixture();source=endpoint(row,seats)
        config=runner.native_page_config(selector.load_block_schedule_page_configs()['heartsaver'],'heartsaver',skills_enabled=False,pediatric_enabled=True)
        payload=p.project(dict(pageKey='heartsaver',pageConfig=config,offers=[],dates=[],counts={},anchor_policy={'finalized':True}),
            dict(generated_at=now.isoformat(),sessions=[source],**{p.PROOF_KEY:policy}),
            dict(schemaVersion='native-publication-scope.v1',enabled=True,pediatricExistingSessionEnabled=True),now)
        self.feed=generator.public_selector_availability_payload(payload);html=generator.render_html(payload)
        self.disabled=False;self.forbidden=[];self.errors=[]
        context=self.browser.new_context(viewport={'width':width,'height':900},service_workers='block');self.addCleanup(context.close)
        def serve(route):
            request=route.request;url=urlsplit(request.url)
            if request.method!='GET':self.forbidden.append(request.url);return route.abort()
            if request.url.startswith(API):
                if url.path!=urlsplit(API).path+'form':self.forbidden.append(request.url);return route.abort()
                packet=dict(now=now.isoformat(),session=source,disabled=self.disabled,selection={k:v[0] for k,v in parse_qs(url.query).items()})
                result=subprocess.run(['node','tests/helpers/native-pediatric-browser-model.mjs'],cwd=ROOT,input=json.dumps(packet),capture_output=True,text=True,check=True)
                response=json.loads(result.stdout)
                return route.fulfill(status=response['status'],json=response['body'],headers={'access-control-allow-origin':ORIGIN})
            if url.netloc!=urlsplit(ORIGIN).netloc:self.forbidden.append(request.url);return route.abort()
            if url.path=='/heartsaver.html':return route.fulfill(body=html,content_type='text/html')
            if url.path=='/data/block-selector-availability/heartsaver.json':return route.fulfill(json=self.feed)
            if url.path.startswith(('/assets/','/images/','/register/')):
                target=ROOT/'docs'/url.path.lstrip('/')
                if target.is_dir():target=target/'index.html'
                if target.is_file():return route.fulfill(path=str(target),content_type=mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
            self.forbidden.append(request.url);route.abort()
        context.route('**/*',serve);page=context.new_page();page.on('pageerror',lambda e:self.errors.append(str(e)))
        page.clock.install(time=now);page.goto(ORIGIN+'/heartsaver.html');page.wait_for_function("availabilityState === 'ready'")
        return page,now
    def test_existing_session_contact_only_form_and_revocation_mobile_desktop(self):
        for width in (390,1280):
            with self.subTest(width=width):
                page,now=self.open(width);page.locator('[data-course-id="351632"]').first.click()
                link=page.locator('#course-list a.register-link');self.assertIn('course=351632',link.get_attribute('href'))
                self.assertIn('session=lw-',link.get_attribute('href'));link.click();page.wait_for_selector('#checkout-form')
                self.assertEqual(page.locator('input[type=file]').count(),0)
                self.assertEqual(page.locator('input[type=checkbox]').count(),0)
                self.assertEqual(page.locator('input[type=email]').count(),1)
                self.assertEqual(page.locator('input[type=tel]').count(),1)
                self.assertIn('$95.00',page.locator('#total').inner_text())
                self.disabled=True;page.reload();page.wait_for_function("document.querySelector('#app').textContent.includes('Online checkout is not available')")
                self.assertEqual(page.locator('#checkout-form').count(),0)
                page.goto(ORIGIN+'/heartsaver.html');page.wait_for_function("availabilityState === 'ready'")
                page.clock.set_system_time(now+timedelta(minutes=16));page.reload();page.wait_for_function("availabilityState === 'ready'")
                self.assertEqual(page.locator('#course-list a.register-link').count(),0)
                self.assertEqual(self.errors,[]);self.assertEqual(self.forbidden,[])
