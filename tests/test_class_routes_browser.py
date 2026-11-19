import json,re,unittest
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class ClassRoutesBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(channel='chrome',headless=True)
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop()
 def page(self,width):
  context=self.browser.new_context(viewport={'width':width,'height':900})
  self.addCleanup(context.close)
  def serve(route):
   path=urlparse(route.request.url).path
   if route.request.method!='GET':route.abort();return
   if path=='/bls':path='/bls.html'
   if path=='/classes/':path='/classes/index.html'
   file=ROOT/'docs'/path.lstrip('/')
   if file.is_file():route.fulfill(path=str(file))
   else:route.fulfill(status=200,body='')
  context.route('**/*',serve)
  clock=json.loads((ROOT/'docs/data/block-selector-availability/bls.json').read_text(encoding='utf8'))['generatedAt']
  context.add_init_script("const D=Date,T=D.parse("+json.dumps(clock)+");window.Date=class extends D{constructor(...a){super(...(a.length?a:[T]));}static now(){return T;}}")
  return context.new_page()
 def test_listing_and_detail_routes_from_preview_never_target_preview_checkout(self):
  for width in (390,1440):
   with self.subTest(width=width):
    page=self.page(width);page.goto('https://preview.example.pages.dev/classes/',wait_until='networkidle')
    self.assertEqual(page.locator('.class-finder-card').count(),28)
    self.assertEqual(page.locator('.class-finder-primary[href^="https://www.910cpr.com/register/?session="]').count(),6)
    self.assertEqual(page.locator('.class-finder-primary[href^="mailto:"]').count(),22)
    self.assertEqual(page.locator('a[href*="enrollware.com"]').count(),0)
    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
    page.goto('https://preview.example.pages.dev/classes/15026275.html',wait_until='networkidle')
    self.assertEqual(page.locator('.cta-panel a.button.primary').get_attribute('href'),'https://www.910cpr.com/register/?session=15026275')
    page.goto('https://preview.example.pages.dev/classes/14801188.html',wait_until='networkidle')
    self.assertTrue(page.locator('.cta-panel a.button.primary').get_attribute('href').startswith('mailto:'))
    self.assertEqual(page.locator('.cta-panel a.button.primary').inner_text(),'Request this class')
    self.assertIn('No seat is reserved',page.locator('.cta-panel').inner_text())
 def test_actual_bls_friday_register_uses_exact_production_session(self):
  page=self.page(390);page.goto('https://preview.example.pages.dev/bls',wait_until='networkidle')
  page.locator('[data-course-id="209806"]').first.click()
  page.locator('button.day-button[aria-label^="Friday, November 20, 2026"]').click()
  target=page.locator('#course-list a[href="https://www.910cpr.com/register/?session=15026275"]')
  target.wait_for(state='visible')
  self.assertEqual(target.count(),1)
if __name__=='__main__':unittest.main()
