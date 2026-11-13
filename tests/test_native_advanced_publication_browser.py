"""Actual advanced selector HTML, local fixture routes only; no hosted writes."""
import json,mimetypes,unittest
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from playwright.sync_api import sync_playwright
from tests.test_native_advanced_publication import AdvancedPublicationTests
from scripts.build_bls_block_schedule_pilot import render_html,public_selector_availability_payload
from scripts.run_native_publication import native_page_config
ROOT=Path(__file__).resolve().parents[1]
class AdvancedSelectorBrowserTests(unittest.TestCase):
 def test_native_routes_and_original_expiry_on_phone_and_desktop(self):
  fixture=AdvancedPublicationTests();fixture.setUp();payload=fixture.build()
  config=json.loads((ROOT/'data/config/block_schedule_pages.json').read_text())['pages']['acls'];payload['pageConfig']=native_page_config(config,'acls',advanced_enabled=True)
  html=render_html(payload);feed=public_selector_availability_payload(payload);origin='https://advanced-fixture.invalid'
  self.assertNotIn('PRIVATE-contact',html)
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True)
   for width in [390,1280]:
    context=browser.new_context(viewport={'width':width,'height':900},service_workers='block');outside=[];errors=[]
    def serve(route):
     url=urlsplit(route.request.url)
     if url.netloc!=urlsplit(origin).netloc or route.request.method!='GET':outside.append(route.request.url);route.abort();return
     if url.path=='/acls.html':route.fulfill(body=html,content_type='text/html');return
     if url.path=='/data/block-selector-availability/acls.json':route.fulfill(json=feed);return
     if url.path.startswith(('/assets/','/images/')):
      file=(ROOT/'docs'/url.path.lstrip('/')).resolve()
      if file.is_relative_to(ROOT/'docs') and file.is_file():route.fulfill(path=str(file),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream');return
     if url.path=='/register/checkout/':route.fulfill(body='<h1>Synthetic checkout boundary</h1>',content_type='text/html');return
     outside.append(route.request.url);route.abort()
    context.route('**/*',serve);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.clock.install(time=fixture.now)
    page.goto(origin+'/acls.html');page.wait_for_function("availabilityState === 'ready'")
    for cid in ['241108','209818']:
     page.locator('[data-course-id="'+cid+'"]').first.click();link=page.locator('#course-list a.register-link').first;link.wait_for();url=urlsplit(link.get_attribute('href'));self.assertEqual(url.path,'/register/checkout/');self.assertEqual(parse_qs(url.query)['course'],[cid]);self.assertTrue(parse_qs(url.query)['selectionId'][0].startswith('native-full:'))
    self.assertEqual(errors,[]);self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
    # A top-level restamp cannot renew the original course proof.
    feed['validUntil']='2099-01-01T00:00:00Z';page.clock.fast_forward(16*60*1000);page.evaluate('loadResolvedAvailability()');page.wait_for_function("availabilityState === 'ready'");self.assertEqual(page.locator('#course-list a.register-link').count(),0);self.assertEqual(outside,[]);context.close()
   browser.close()
