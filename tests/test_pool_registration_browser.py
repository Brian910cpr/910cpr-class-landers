"""Local-only checkout regression tests. Every network request is intercepted."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unittest
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REQUEST_ID = "b6f17b40-fbb2-4ff2-a509-41763b6b5366"
CHECKOUT = "https://checkout.stripe.com/c/pay/test_mock_only"

class PoolRegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch()
    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.runtime.stop()
    def open(self, page_id='pool', width=390, remaining=30, post=None, query='', saved=None, storage=True, theme='light'):
        context = self.browser.new_context(viewport={'width':width,'height':844}, color_scheme=theme)
        self.addCleanup(context.close)
        self.posts=[]; self.errors=[]
        event='nseaswim-pool-'+('bls' if page_id=='poolbls' else 'family')+'-2027-02-15'
        if saved:
            context.add_init_script('sessionStorage.setItem('+json.dumps('pool-checkout:'+event)+','+json.dumps(json.dumps(saved))+')')
        if not storage:
            context.add_init_script("Object.defineProperty(window,'sessionStorage',{get(){throw Error('blocked')}})")
        def serve(route):
            url=route.request.url; path=urlparse(url).path
            if 'public-event-registration' in url:
                if route.request.method=='POST':
                    body=route.request.post_data_json; self.posts.append(body)
                    if post: return post(route,body)
                    route.fulfill(json={'ok':True,'confirmed':True,'attendeeCount':body.get('attendeeCount',1)})
                else:
                    if remaining is None:
                        route.fulfill(status=503,json={'ok':False,'error':'Unavailable'});return
                    route.fulfill(json={'ok':True,'pricing':{'courseUnitCents':2500 if page_id=='poolbls' else 0,'ebookUnitCents':2000},'event':{'remaining':remaining,'handsOnCapacity':30,'start_at':'2027-02-15T16:00:00Z','registration_status':'open'}})
            elif url.startswith(CHECKOUT): route.fulfill(body='<h1>Mock checkout only</h1>',content_type='text/html')
            elif path=='/'+page_id: route.fulfill(path=str(ROOT/'docs'/f'{page_id}.html'),content_type='text/html')
            elif path.startswith('/assets/') and (ROOT/'docs'/path.lstrip('/')).is_file():
                route.fulfill(path=str(ROOT/'docs'/path.lstrip('/')),content_type='text/css' if path.endswith('.css') else 'application/javascript')
            else: route.fulfill(body='',status=200)
        context.route('**/*',serve)
        page=context.new_page(); page.on('pageerror',lambda error:self.errors.append(str(error)))
        page.clock.install(time=datetime(2026,11,7,tzinfo=timezone.utc))
        page.goto('https://www.910cpr.com/'+page_id+query)
        page.wait_for_function("!document.getElementById('seatLabel').textContent.includes('Checking')")
        return page
    def fill(self,page,count=1):
        page.locator('#count').select_option(str(count))
        page.locator('#first').fill('Local');page.locator('#last').fill('Test')
        page.locator('#email').fill('local@example.invalid')
        for i in range(count-1):
            page.locator(f'#guest-{i}-first').fill('Guest'+str(i+1));page.locator(f'#guest-{i}-last').fill('Test');page.locator(f'#guest-{i}-email').fill('guest'+str(i+1)+'@example.invalid')
    def test_free_group_confirmation_mobile_and_desktop(self):
        for width in (390,1280):
            page=self.open(width=width);self.fill(page,3);page.locator('#submit').click()
            page.locator('#confirmation').wait_for(state='visible')
            self.assertEqual(len(self.posts),1);payload=self.posts[0]
            self.assertEqual(payload['guestNames'],['Guest1 Test','Guest2 Test']);self.assertEqual(payload['guestEmails'],['guest1@example.invalid','guest2@example.invalid'])
            self.assertEqual(payload['ebookQty'],0);self.assertTrue(payload['requestId'])
            self.assertIn('3 hands-on spots',page.locator('#confirmation').inner_text())
            self.assertTrue(page.locator('#submit').is_hidden());self.assertEqual(self.errors,[])
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            page.evaluate("document.getElementById('registration').dispatchEvent(new Event('submit',{cancelable:true,bubbles:true}))")
            self.assertEqual(len(self.posts),1)
    def test_bls_exact_prices_and_guest_names_survive_choices(self):
        page=self.open('poolbls');self.fill(page,3)
        self.assertEqual(page.locator('#total').inner_text(),'$75')
        page.locator('#withBook').click()
        self.assertEqual(page.locator('#total').inner_text(),'$135')
        self.assertEqual(page.locator('#guest-1-first').input_value(),'Guest2');self.assertEqual(page.locator('#guest-1-email').input_value(),'guest2@example.invalid')
        page.locator('#count').select_option('2');page.locator('#count').select_option('3')
        self.assertEqual(page.locator('#guest-1-first').input_value(),'Guest2');self.assertEqual(page.locator('#guest-1-email').input_value(),'guest2@example.invalid')
        page.locator('#ownBook').click()
        self.assertEqual(page.locator('#total').inner_text(),'$75')
        self.assertEqual(page.locator('#withBook').get_attribute('aria-pressed'),'false')
    def test_bls_checkout_mock_no_live_payment(self):
        def post(route,body): route.fulfill(json={'ok':True,'paymentPending':True,'checkoutUrl':CHECKOUT})
        page=self.open('poolbls',post=post);self.fill(page,2);page.locator('#withBook').click()
        page.locator('#submit').click();page.wait_for_url(CHECKOUT)
        self.assertEqual(self.posts[0]['ebookQty'],2);self.assertEqual(self.posts[0]['attendeeCount'],2);self.assertEqual(self.posts[0]['guestEmails'],['guest1@example.invalid'])
    def test_double_submit_sends_once(self):
        page=self.open();self.fill(page)
        page.evaluate("for(let i=0;i<5;i++)document.getElementById('registration').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))")
        page.locator('#confirmation').wait_for(state='visible');self.assertEqual(len(self.posts),1)
    def test_capacity_full_and_group_limit(self):
        page=self.open(remaining=0);self.assertTrue(page.locator('#submit').is_disabled())
        self.assertIn('full',page.locator('#seatLabel').inner_text())
        page=self.open(remaining=2);self.assertTrue(page.locator('#count option[value="3"]').is_disabled())
    def test_capacity_failure_does_not_claim_available(self):
        page=self.open(remaining=None)
        self.assertFalse(page.locator('#submit').is_enabled());self.assertEqual(self.posts,[])
        self.assertIn('could not check',page.locator('#seatLabel').inner_text())
    def test_untrusted_paid_flag_is_not_confirmation(self):
        page=self.open('poolbls',query='?paid=1')
        self.assertTrue(page.locator('#confirmation').is_hidden());self.assertIn('cannot be confirmed',page.locator('#status').inner_text())
    def test_cancel_return_restores_and_resumes_same_request(self):
        payload={'attendeeCount':2,'firstName':'Local','lastName':'Test','email':'local@example.invalid','guestNames':['Guest Test'],'guestEmails':['guest@example.invalid'],'ebookQty':2}
        def post(route,body): route.fulfill(json={'ok':True,'paymentPending':True,'checkoutUrl':CHECKOUT})
        page=self.open('poolbls',post=post,query='?checkout_cancelled=1',saved={'requestId':REQUEST_ID,'payload':payload})
        page.locator('#resume-checkout').wait_for(state='visible');self.assertEqual(page.locator('#resume-checkout').get_attribute('href'),CHECKOUT)
        self.assertEqual(page.locator('#first').input_value(),'Local');self.assertEqual(page.locator('#guest-0-last').input_value(),'Test');self.assertEqual(page.locator('#guest-0-email').input_value(),'guest@example.invalid')
        self.assertTrue(page.locator('#first').is_disabled());self.assertEqual(self.posts[0]['action'],'status')
        self.assertEqual(self.posts[0]['requestId'],REQUEST_ID)
    def test_verified_return_without_storage(self):
        def post(route,body): route.fulfill(json={'ok':True,'confirmed':True,'attendeeCount':2})
        page=self.open('poolbls',post=post,storage=False,query='?request_id='+REQUEST_ID+'&session_id=cs_test_mock')
        page.locator('#confirmation').wait_for(state='visible')
        self.assertEqual(self.posts[0]['checkoutSessionId'],'cs_test_mock');self.assertIn('Payment confirmed',page.locator('#status').inner_text())
        self.assertNotIn('request_id',page.url);self.assertNotIn('session_id',page.url)
    def test_lost_response_retries_original_key(self):
        attempts=[]
        def post(route,body):
            attempts.append(body)
            if len(attempts)==1: route.abort('failed')
            elif body.get('action')=='status': route.fulfill(status=404,json={'ok':False,'error':'Request not found'})
            else: route.fulfill(json={'ok':True,'confirmed':True,'attendeeCount':1})
        page=self.open(post=post);self.fill(page);page.locator('#submit').click()
        page.wait_for_function("document.getElementById('submit').textContent==='Check registration status'")
        self.assertTrue(page.locator('#first').is_disabled());page.locator('#submit').click()
        page.locator('#confirmation').wait_for(state='visible')
        self.assertEqual(len(attempts),3);self.assertEqual(attempts[0],attempts[2])
    def test_expired_checkout_unlocks_without_automatic_resubmit(self):
        def post(route,body):route.fulfill(json={'ok':True,'expired':True})
        page=self.open('poolbls',post=post,query='?request_id='+REQUEST_ID)
        page.wait_for_function("document.getElementById('status').textContent.includes('expired')")
        self.assertTrue(page.locator('#first').is_enabled());self.assertEqual(len(self.posts),1)
    def test_post_reservation_conflict_keeps_original_key(self):
        def post(route,body):route.fulfill(status=409,json={'ok':False,'error':'Checkout mismatch','code':'checkout_mismatch'})
        page=self.open('poolbls',post=post);self.fill(page);page.locator('#submit').click()
        page.wait_for_function("document.getElementById('submit').textContent==='Check registration status'")
        self.assertTrue(page.locator('#first').is_disabled())
        initial=self.posts[0]['requestId'];page.locator('#submit').click()
        page.wait_for_function("!document.getElementById('submit').disabled")
        self.assertEqual(self.posts[-1]['requestId'],initial)
    def test_rejects_non_stripe_checkout_url(self):
        def post(route,body):route.fulfill(json={'ok':True,'paymentPending':True,'checkoutUrl':'https://example.invalid/unsafe'})
        page=self.open('poolbls',post=post);self.fill(page);page.locator('#submit').click()
        page.wait_for_function("document.getElementById('submit').textContent==='Check registration status'")
        self.assertTrue(page.locator('#resume-checkout').is_hidden());self.assertIn('/poolbls',page.url)

    def test_dark_theme_checkout_text_has_accessible_contrast(self):
        import re
        def lum(color):
            channels=[int(x)/255 for x in re.findall(r"\d+",color)[:3]]
            linear=[v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4 for v in channels]
            return sum(v*w for v,w in zip(linear,[0.2126,0.7152,0.0722]))
        for page_id in ['pool','poolbls']:
            page=self.open(page_id,theme='dark')
            self.assertEqual(page.locator('html').get_attribute('data-theme'),'dark')
            styles=page.locator('.registration h2,.registration label,.price-choice strong,.price-choice .amount,.price-choice small,.price-choice .breakdown,.checkout-capacity,.checkout-switch,.summary,#submit').evaluate_all("""els=>els.filter(el=>el.getClientRects().length).map(el=>{let p=el,bg;while(p){bg=getComputedStyle(p).backgroundColor;if(bg!=='rgba(0, 0, 0, 0)')break;p=p.parentElement;}return [el.textContent.trim(),getComputedStyle(el).color,bg];})""")
            for text,color,bg in styles:
                light,dark=sorted([lum(color),lum(bg)],reverse=True)
                self.assertGreaterEqual((light+0.05)/(dark+0.05),4.5,text)

    def test_earl_jackson_template_structure_and_responsive_order(self):
        for width in [390,1280]:
            page=self.open('poolbls',width=width)
            self.assertEqual(page.locator('#registration > .card').count(),1)
            self.assertEqual(page.locator('.price-choices button.price-choice').count(),2)
            self.assertEqual(page.locator('.row label.field .req').count(),4)
            self.assertEqual(page.locator('#ownBook').get_attribute('aria-pressed'),'true')
            choices=page.locator('.price-choices').bounding_box()['y'];contact=page.locator('#first').bounding_box()['y']
            self.assertLess(choices,contact) if width==390 else self.assertGreater(choices,contact)
            page=self.open('pool',width=width)
            self.assertEqual(page.locator('#registration > .card').count(),1)
            self.assertLess(page.locator('#count').bounding_box()['y'],page.locator('#first').bounding_box()['y'])
            self.assertEqual(page.locator('#registration .survey-body select').count(),4)

    def test_every_attendee_email_required_on_both_forms(self):
        for name in ['pool','poolbls']:
            page=self.open(name);self.fill(page,3)
            self.assertEqual(page.locator('#guests input[type=email][required]').count(),2)
            page.locator('#guest-1-email').fill('');page.locator('#submit').click()
            self.assertEqual(self.posts,[])
            page.locator('#guest-1-email').fill('not-an-email');page.locator('#submit').click()
            self.assertEqual(self.posts,[])
            page.locator('#guest-1-email').fill('guest2@example.invalid');page.locator('#submit').click()
            page.locator('#confirmation').wait_for(state='visible')
            self.assertEqual(self.posts[0]['guestEmails'],['guest1@example.invalid','guest2@example.invalid'])
    def test_simple_book_price_and_optional_default(self):
        page=self.open('poolbls')
        self.assertEqual(page.locator('#withBook .amount').inner_text(),'$45')
        self.assertIn('$25 BLS class + $20 eManual',page.locator('#withBook').inner_text())
        self.assertEqual(page.locator('#ownBook .amount').inner_text(),'$25')
        self.assertEqual(page.locator('#ownBook').get_attribute('aria-pressed'),'true')
        self.assertEqual(page.locator('#total').inner_text(),'$25')
        page.locator('#withBook').click();self.assertEqual(page.locator('#total').inner_text(),'$45')

    def test_hidden_checkout_recovery_has_valid_local_fallback(self):
        for name in ['pool','poolbls']:
            page=self.open(name)
            self.assertEqual(page.locator('#resume-checkout').get_attribute('href'),'#registration')
            self.assertTrue(page.locator('#resume-checkout').is_hidden())
            self.assertEqual(page.locator('#registration').count(),1)

if __name__=='__main__':unittest.main()
