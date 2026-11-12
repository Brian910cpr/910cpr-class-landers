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
        self.disabled=False;self.forbidden=[];self.errors=[];self.requests=[];self.api_responses=[];self.console=[];self.failed_requests=[]
        context=self.browser.new_context(viewport={'width':width,'height':900},service_workers='block');self.addCleanup(context.close)
        # Exercise the real markup without emitting analytics from synthetic CI.
        context.add_cookies([{'name':'lw_analytics_excluded','value':'1','url':ORIGIN}])
        def serve(route):
            request=route.request;url=urlsplit(request.url)
            self.requests.append({'method':request.method,'url':request.url})
            if request.method!='GET':self.forbidden.append(request.url);return route.abort()
            if request.url.startswith(API):
                if url.path!=urlsplit(API).path+'form':self.forbidden.append(request.url);return route.abort()
                packet=dict(now=now.isoformat(),session=source,disabled=self.disabled,selection={k:v[0] for k,v in parse_qs(url.query).items()})
                result=subprocess.run(['node','tests/helpers/native-pediatric-browser-model.mjs'],cwd=ROOT,input=json.dumps(packet),capture_output=True,text=True,check=True)
                response=json.loads(result.stdout)
                self.api_responses.append({'selection':packet['selection'],'disabled':self.disabled,**response})
                return route.fulfill(status=response['status'],json=response['body'],headers={'access-control-allow-origin':ORIGIN})
            if url.netloc!=urlsplit(ORIGIN).netloc:self.forbidden.append(request.url);return route.abort()
            if url.path=='/heartsaver.html':return route.fulfill(body=html,content_type='text/html')
            if url.path=='/data/block-selector-availability/heartsaver.json':return route.fulfill(json=self.feed)
            if url.path.startswith(('/assets/','/images/','/register/')):
                target=ROOT/'docs'/url.path.lstrip('/')
                if target.is_dir():target=target/'index.html'
                if target.is_file():return route.fulfill(path=str(target),content_type=mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
            self.forbidden.append(request.url);route.abort()
        context.route('**/*',serve);page=context.new_page();self.active_page=page;page.on('pageerror',lambda e:self.errors.append(str(e)))
        page.on('console',lambda m:self.console.append({'type':m.type,'text':m.text}))
        page.on('requestfailed',lambda request:self.failed_requests.append({'url':request.url,'failure':request.failure}))
        page.clock.install(time=now);page.goto(ORIGIN+'/heartsaver.html');page.wait_for_function("availabilityState === 'ready'")
        return page,now
    def diagnostics(self,page):
        frames=[]
        for frame in page.frames:
            try:
                state=frame.evaluate("({app:document.querySelector('#app')?.textContent,forms:document.querySelectorAll('#checkout-form').length,ready:document.readyState})")
            except Exception as error:state={'inspectionError':str(error)}
            frames.append({'url':frame.url,**state})
        return json.dumps({'pageUrl':page.url,'frames':frames,'errors':self.errors,'console':self.console,
            'forbidden':self.forbidden,'requests':self.requests,'failedRequests':self.failed_requests,
            'apiResponses':self.api_responses},indent=2)

    def test_existing_session_contact_only_form_and_revocation_mobile_desktop(self):
        for width in (390,1280):
            with self.subTest(width=width):
                page=None;self.active_page=None
                try:
                    page,now=self.open(width);page.locator('[data-course-id="351632"]').first.click()
                    link=page.locator('#course-list a.register-link');self.assertIn('course=351632',link.get_attribute('href'))
                    selected_session=parse_qs(urlsplit(link.get_attribute('href')).query)['session'][0]
                    self.assertTrue(selected_session.startswith('lw-'));link.click()
                    # The production reader installs inline-registration.js. Existing
                    # classes open the shared form in a frame, not a new page.
                    iframe=page.locator('iframe[title="Class registration and checkout"]')
                    iframe.wait_for(state='visible')
                    frame=iframe.element_handle().content_frame()
                    self.assertIsNotNone(frame)
                    frame.wait_for_selector('#checkout-form')
                    frame_query=parse_qs(urlsplit(frame.url).query)
                    self.assertEqual(frame_query['session'],[selected_session]);self.assertEqual(frame_query['embed'],['1'])
                    self.assertEqual(urlsplit(page.url).path,'/heartsaver.html')
                    self.assertEqual(self.api_responses[-1]['body']['selection']['course'],'351632')
                    self.assertEqual(self.api_responses[-1]['body']['selection']['session'],selected_session)
                    self.assertEqual(frame.locator('input[type=file]').count(),0)
                    self.assertEqual(frame.locator('input[type=checkbox]').count(),0)
                    self.assertEqual(frame.locator('input[type=email]').count(),1)
                    self.assertEqual(frame.locator('input[type=tel]').count(),1)
                    self.assertIn('$95.00',frame.locator('#total').inner_text())
                    self.disabled=True
                    frame.goto(frame.url)
                    frame.wait_for_function("document.querySelector('#app')?.textContent.includes('Online checkout is not available')")
                    self.assertEqual(frame.locator('#checkout-form').count(),0)
                    page.goto(ORIGIN+'/heartsaver.html');page.wait_for_function("availabilityState === 'ready'")
                    page.clock.set_system_time(now+timedelta(minutes=16));page.reload();page.wait_for_function("availabilityState === 'ready'")
                    self.assertEqual(page.locator('#course-list a.register-link').count(),0)
                    self.assertEqual(self.errors,[]);self.assertEqual(self.forbidden,[])
                except Exception:
                    page=page or self.active_page
                    if page is not None:print('PEDIATRIC_SYNTHETIC_BROWSER_DIAGNOSTICS '+self.diagnostics(page),flush=True)
                    raise
