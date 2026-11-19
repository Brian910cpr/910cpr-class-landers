import json,re,unittest
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
SESSION=dict(id='15026275',courseId='209806',course='AHA BLS Provider (Initial)',startsAt='2026-11-20T16:00:00Z',endsAt='2026-11-20T18:00:00Z',location='Shipyard Room B',price=75,currency='usd',addons=[])
class CheckoutUXTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(channel='chrome',headless=True)
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop()
 def open(self,theme='light',width=390,query='session=15026275',response=None,defer=False,order_response=None):
  context=self.browser.new_context(viewport={'width':width,'height':900},color_scheme=theme)
  self.addCleanup(context.close);requests=[];pending=[]
  def serve(route):
   path=urlparse(route.request.url).path
   if '/functions/v1/public-registration/session/' in path:route.fulfill(json={'ok':True,'session':SESSION});return
   if '/functions/v1/public-registration/order/' in path or '/functions/v1/public-registration/recover/' in path:route.fulfill(json=order_response or {'ok':True,'status':'paid'});return
   if path.endswith('/public-registration/start'):
    requests.append({'body':route.request.post_data_json,'key':route.request.headers.get('idempotency-key')})
    if defer:pending.append(route)
    else:route.fulfill(json=response or {'ok':True,'checkoutUrl':'https://www.910cpr.com/register/?order=11111111-1111-4111-8111-111111111111&paid=1'})
    return
   if route.request.method!='GET':route.abort();return
   file=ROOT/'docs'/('register/index.html' if path=='/register/' else path.lstrip('/'))
   route.fulfill(path=str(file)) if file.is_file() else route.fulfill(status=200,body='')
  context.route('**/*',serve)
  page=context.new_page();page.goto('https://www.910cpr.com/register/?'+query,wait_until='networkidle')
  return page,requests,pending
 def fill(self,page):
  card=page.locator('.student').first
  for field,value in [('firstName','Synthetic'),('lastName','Fixture'),('email','synthetic@example.invalid'),('phone','2025550100')]:card.locator('[data-field='+field+']').fill(value)
 def contrast(self,el):
  return el.evaluate('''e=>{const n=s=>s.match(/[\\d.]+/g).map(Number);const l=a=>a.slice(0,3).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4}).reduce((s,x,i)=>s+x*[.2126,.7152,.0722][i],0);let b=e;while(b&&getComputedStyle(b).backgroundColor==='rgba(0, 0, 0, 0)')b=b.parentElement;const a=l(n(getComputedStyle(e).color)),c=l(n(getComputedStyle(b).backgroundColor));return(Math.max(a,c)+.05)/(Math.min(a,c)+.05)}''')
 def test_steps_buttons_options_and_contrast_in_both_themes_and_sizes(self):
  for theme in ('light','dark'):
   for width in (390,1440):
    with self.subTest(theme=theme,width=width):
     page,_,_=self.open(theme,width)
     self.assertIn('1. your selected class',page.locator('.session').inner_text().lower())
     self.assertIn('AHA BLS Provider (Initial)',page.locator('.session').inner_text())
     self.assertIn('Friday, November 20',page.locator('.session').inner_text())
     self.assertIn('2. Students',page.locator('.formwrap h2').first.inner_text())
     self.assertIn('3. Review',page.locator('#checkout-review-title').inner_text())
     self.assertEqual(page.locator('#continue').inner_text(),'Register · $75.00 estimated')
     self.assertEqual(page.locator('#add-student').inner_text(),'Add other students')
     self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
     for selector in ['#continue','#add-student']:
      el=page.locator(selector);self.assertGreaterEqual(el.bounding_box()['height'],44);self.assertGreaterEqual(self.contrast(el),4.5)
      el.hover();self.assertGreaterEqual(self.contrast(el),4.5)
      page.keyboard.press('Tab');el.focus();self.assertNotEqual(el.evaluate('e=>getComputedStyle(e).outlineStyle'),'none')
     for el in page.locator('.product-choice strong,.product-choice small,.billing-help').all():self.assertGreaterEqual(self.contrast(el),4.5)
     field=page.locator('[data-billing-code]')
     color=field.evaluate("e=>getComputedStyle(e,'::placeholder').color")
     field.evaluate("(e,c)=>e.style.setProperty('color',c,'important')",color)
     self.assertGreaterEqual(self.contrast(field),4.5)
     field.evaluate("e=>e.style.removeProperty('color')")
     self.assertEqual(page.locator('.product-image:visible').count(),0)
     self.assertIn('purchased separately',page.locator('.product-group').first.inner_text())
     self.assertEqual(page.locator('.product-choice strong').first.evaluate('e=>getComputedStyle(e).fontSize'),'14px')
 def test_estimates_pending_code_and_student_state_are_preserved(self):
  page,_,_=self.open();self.fill(page)
  page.locator('[data-manual-choice][value=ebook]').first.check()
  self.assertIn('$92.49',page.locator('#continue').inner_text())
  code=page.locator('[data-billing-code]').first;code.fill('MaximBH')
  self.assertEqual(page.locator('#continue').inner_text(),'Register · validate total')
  self.assertNotIn('$75',page.locator('.checkout-review').inner_text());self.assertNotIn('$0',page.locator('.checkout-review').inner_text())
  page.locator('[data-same-for-all]').check();page.locator('#add-student').click()
  self.assertEqual(page.locator('.student').count(),2)
  self.assertEqual(page.locator('[data-billing-code]').nth(1).input_value(),'MaximBH')
  self.assertTrue(page.locator('[data-manual-choice][value=ebook]').nth(1).is_checked())
  self.assertEqual(page.locator('[data-field=email]').first.input_value(),'synthetic@example.invalid')
  page.locator('.remove').click();self.assertEqual(page.locator('.student').count(),1)
  code.fill('');self.assertIn('$92.49',page.locator('#continue').inner_text())
 def test_interrupted_invalid_code_keeps_fields_and_prevents_duplicate_submit(self):
  page,requests,pending=self.open(defer=True);self.fill(page);page.locator('[data-billing-code]').fill('invalid-code')
  page.locator('#continue').click();page.wait_for_timeout(100)
  page.locator('#registration').dispatch_event('submit')
  self.assertEqual(len(requests),1);self.assertTrue(page.locator('[data-field=email]').is_disabled())
  pending[0].fulfill(status=400,json={'ok':False,'error':'invalid_billing_code'})
  page.wait_for_function("!document.getElementById('continue').disabled")
  self.assertEqual(page.locator('[data-field=email]').input_value(),'synthetic@example.invalid')
  self.assertEqual(page.locator('[data-billing-code]').input_value(),'invalid-code')
  self.assertIn('not valid',page.locator('#status').inner_text())
  self.assertEqual(requests[0]['body']['students'][0]['billingCode'],'invalid-code')
  self.assertRegex(requests[0]['key'],r'^[a-f0-9-]{36}$')
 def test_zero_company_order_success_never_claims_payment_or_delivery(self):
  page,requests,_=self.open();self.fill(page);page.locator('[data-billing-code]').fill('MaximBH');page.locator('#continue').click()
  page.wait_for_url('**/register/?order=*&paid=1');page.locator('.loading h2').wait_for()
  text=page.locator('#app').inner_text()
  self.assertIn('Registration confirmed',text)
  self.assertIn('A confirmation of your registration will follow.',text)
  for forbidden in ['payment was received','bill was paid','already paid','email is on the way']:self.assertNotIn(forbidden,text.lower())
  self.assertEqual(requests[0]['body']['students'][0]['billingCode'],'MaximBH')
 def test_recovered_order_uses_same_truthful_confirmation_wording(self):
  page,requests,_=self.open(query='recover=11111111-1111-4111-8111-111111111111')
  self.assertIn('A confirmation of your registration will follow.',page.locator('#app').inner_text())
  self.assertEqual(requests,[])
 def test_unverified_return_does_not_claim_success_or_invite_a_duplicate(self):
  page,requests,_=self.open(query='order=11111111-1111-4111-8111-111111111111&paid=1',order_response={'ok':False,'status':'payment_pending'})
  text=page.locator('#app').inner_text()
  self.assertIn('Registration status not yet verified',text)
  self.assertIn('Do not submit another registration',text)
  self.assertNotIn('Registration confirmed',text)
  self.assertEqual(page.locator('#app a[href="/classes/"]').count(),0)
  self.assertEqual(requests,[])
if __name__=='__main__':unittest.main()
