import json,subprocess,unittest
from datetime import date as calendar_date
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
from scripts.refresh_selector_registration_actions import plan_refresh
class SelectorActions(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.plans=plan_refresh();cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(channel='chrome',headless=True)
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop()
 def open(self,family,width=390,theme='light',fresh_synthetic=False):
  ctx=self.browser.new_context(viewport={'width':width,'height':900},color_scheme=theme);self.addCleanup(ctx.close)
  ctx.add_init_script("{const RealDate=Date;globalThis.Date=class extends RealDate{constructor(...a){super(...(a.length?a:['2026-11-19T12:00:00Z']))}static now(){return RealDate.parse('2026-11-19T12:00:00Z')}}}")
  def serve(r):
   path=urlparse(r.request.url).path
   if r.request.method!='GET':r.abort();return
   if path.startswith('/data/block-selector-availability/'):
    name='docs'+path
    try:
     data=subprocess.check_output(['git','show','HEAD:'+name])
     if fresh_synthetic:
      fixture=json.loads(data);fixture['generatedAt']='2026-11-19T12:00:00Z';fixture['validUntil']='2026-11-20T12:00:00Z'
      for day in fixture['dates']:
       for slot in day['startTimes']:
        for course in slot['courses']:course['validUntil']='2026-11-20T12:00:00Z'
      data=json.dumps(fixture).encode()
     r.fulfill(body=data,content_type='application/json')
    except subprocess.CalledProcessError:r.fulfill(status=503,body='{}')
    return
   name='docs'+path
   if name in self.plans:r.fulfill(body=self.plans[name],content_type='text/html');return
   f=ROOT/name
   if f.is_file():r.fulfill(path=str(f));return
   r.fulfill(body='')
  ctx.route('**/*',serve);page=ctx.new_page();page.set_default_timeout(6000);page.goto('https://www.910cpr.com/'+family+'.html',wait_until='networkidle');return page
 def choose(self,p,cid,date):
  p.locator('[data-course-id="'+cid+'"]').first.click()
  label=calendar_date.fromisoformat(date).strftime('%A, %B %d, %Y').replace(' 0',' ')
  p.locator('button.day-button[aria-label^="'+label+'"]').first.click()
  slot=p.locator('#start-list button');
  if slot.count():slot.first.click()
  p.locator('#course-list .register-link').first.wait_for(state='visible')
 def test_advanced_courses_request_exact_selected_date_time_and_course(self):
  for family,cid in [('acls','241108'),('pals','209805')]:
   for width,theme in [(390,'dark'),(1440,'light')]:
    with self.subTest(family=family,width=width,theme=theme):
     p=self.open(family,width,theme);self.choose(p,cid,'2026-11-24')
     link=p.locator('#course-list .register-link').first;self.assertEqual(link.inner_text(),'Request this class');href=link.get_attribute('href');self.assertTrue(href.startswith('mailto:'))
     body=parse_qs(urlparse(href).query)['body'][0]
     for value in [cid,'2026-11-24','14:00','not a confirmed reservation']:self.assertIn(value,body)
     self.assertNotIn('enrollware',href);self.assertNotIn('pages.dev',href);self.assertIn('No seat is reserved',p.locator('#course-list').inner_text());self.assertTrue(p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
 def test_verified_friday_uses_own_production_checkout(self):
  p=self.open('bls');self.choose(p,'209806','2026-11-20');links=p.locator('#course-list .register-link');self.assertEqual(links.first.inner_text(),'Register');self.assertEqual(links.first.get_attribute('href'),'https://www.910cpr.com/register/?session=15026275')
 def test_heartsaver_skills_preserves_each_explicit_variant(self):
  for variant in ['cpr-aed','first-aid-cpr-aed']:
   for width,theme in [(390,'dark'),(1440,'light')]:
    with self.subTest(variant=variant,width=width,theme=theme):
     p=self.open('heartsaver',width,theme,fresh_synthetic=True)
     p.locator('[data-course-id="509474"][data-skills-context="'+variant+'"]').click()
     p.locator('button.day-button[aria-label^="Friday, November 20, 2026"]').click()
     p.locator('#start-list button').first.click()
     link=p.locator('#course-list .register-link').first
     self.assertEqual(link.inner_text(),'Schedule skills session')
     u=urlparse(link.get_attribute('href'));q=parse_qs(u.query)
     self.assertEqual(u.netloc,'www.910cpr.com');self.assertEqual(u.path,'/register/skills-session/')
     for key,value in [('course','509474'),('date','2026-11-20'),('startTime','10:00'),('skillsContext',variant),('context','heartsaver'),('location','Wilmington; Shipyard Blvd')]:self.assertEqual(q[key],[value])
     self.assertIn('does not collect payment',p.locator('#course-list').inner_text())
 def test_plan_preserves_all_inventory_price_and_option_bytes_including_aliases(self):
  self.assertEqual(len(self.plans),13)
  for name,new in self.plans.items():
   old=subprocess.check_output(['git','show','HEAD:'+name]).decode('utf8')
   for marker in ['    const embeddedScheduleDates = ','    const courseOptions = ']:
    before=[l for l in old.splitlines() if l.startswith(marker)];after=[l for l in new.splitlines() if l.startswith(marker)];self.assertEqual(before,after,(name,marker))
   self.assertIn('registrationAction(course,',new);self.assertNotIn("link.href = '/register/skills-session/?'",new)
if __name__=='__main__':unittest.main()
