"""Intercepted error CTA regression; no registration, payment or SMS launch."""
import unittest
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from tests.test_checkout_three_step_ux_browser import ROOT,SESSION

class UnavailableFallbackTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(channel='chrome',headless=True)
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop()
 def open(self,query,available=False,theme='light',width=390):
  context=self.browser.new_context(viewport={'width':width,'height':900},color_scheme=theme)
  self.addCleanup(context.close);calls=[]
  def serve(route):
   request=route.request;calls.append((request.method,request.url));path=urlparse(request.url).path
   if request.method!='GET':route.abort();return
   if '/functions/v1/public-registration/' in path:
    route.fulfill(status=200 if available else 404,json={'ok':True,'session':SESSION} if available else {'ok':False,'error':'session_not_available'});return
   file=ROOT/'docs'/('register/index.html' if path=='/register/' else path.lstrip('/'))
   route.fulfill(path=str(file)) if file.is_file() else route.fulfill(body='')
  context.route('**/*',serve);page=context.new_page()
  page.goto('https://www.910cpr.com/register/?'+query,wait_until='networkidle')
  return page,calls
 def test_unavailable_and_missing_session_have_text_action_in_all_viewports_themes(self):
  for query in ('session=15026275',''):
   for theme in ('light','dark'):
    for width in (390,1440):
     with self.subTest(query=query,theme=theme,width=width):
      page,calls=self.open(query,theme=theme,width=width)
      self.assertIn('Registration unavailable',page.locator('.errorbox').inner_text())
      link=page.get_by_role('link',name='Text 910CPR for class options: 910-395-5193')
      self.assertEqual(link.get_attribute('href'),'sms:+19103955193');self.assertTrue(link.is_visible())
      link.focus();self.assertTrue(link.evaluate('e=>document.activeElement===e'))
      self.assertEqual(page.locator('a[href="/classes/"]').count(),0)
      self.assertTrue(all(method=='GET' and not url.startswith('sms:') for method,url in calls))
 def test_order_and_recover_keep_status_warning_without_alternate_action(self):
  for query in ('order=11111111-1111-4111-8111-111111111111','recover=synthetic-token'):
   page,calls=self.open(query)
   self.assertIn('Registration status not yet verified',page.locator('.errorbox').inner_text())
   self.assertIn('Do not submit another registration',page.locator('.errorbox').inner_text())
   self.assertEqual(page.locator('.errorbox a').count(),0)
   self.assertTrue(all(method=='GET' for method,_ in calls))
 def test_available_session_keeps_existing_checkout(self):
  page,calls=self.open('session=15026275',available=True)
  self.assertIn('AHA BLS Provider (Initial)',page.locator('.session').inner_text())
  self.assertTrue(page.locator('#continue').is_visible())
  self.assertIn('$75.00',page.locator('#continue').inner_text())
  self.assertEqual(page.locator('.errorbox').count(),0)
  self.assertEqual(page.locator('a[href^="sms:"]').count(),0)
  self.assertTrue(all(method=='GET' for method,_ in calls))

if __name__=='__main__':unittest.main()
