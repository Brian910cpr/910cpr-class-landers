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
    def open(self, page_id='pool', width=390, remaining=30, post=None, query='', saved=None, storage=True):
        context = self.browser.new_context(viewport={'width':width,'height':844})
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
                    route.fulfill(json={'ok':True,'pricing':{'courseUnitCents':2500 if page_id=='poolbls' else 0,'ebookUnitCents':1851},'event':{'remaining':remaining,'handsOnCapacity':30,'start_at':'2027-02-15T16:00:00Z','registration_status':'open'}})
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
            page.locator(f'#guest-{i}-first').fill('Guest'+str(i+1));page.locator(f'#guest-{i}-last').fill('Test')
    def test_free_group_confirmation_mobile_and_desktop(self):
        for width in (390,1280):
            page=self.open(width=width);self.fill(page,3);page.locator('#submit').click()
            page.locator('#confirmation').wait_for(state='visible')
            self.assertEqual(len(self.posts),1);payload=self.posts[0]
            self.assertEqual(payload['guestNames'],['Guest1 Test','Guest2 Test'])
            self.assertEqual(payload['ebookQty'],0);self.assertTrue(payload['requestId'])
            self.assertIn('3 hands-on spots',page.locator('#confirmation').inner_text())
            self.assertTrue(page.locator('#submit').is_hidden());self.assertEqual(self.errors,[])
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            page.evaluate("document.getElementById('registration').dispatchEvent(new Event('submit',{cancelable:true,bubbles:true}))")
            self.assertEqual(len(self.posts),1)
    def test_bls_exact_prices_and_guest_names_survive_choices(self):
        page=self.open('poolbls');self.fill(page,3)
        self.assertEqual(page.locator('#total').inner_text(),'$75.00')
        page.locator('[name=manual][value=ebook]').check()
        self.assertEqual(page.locator('#total').inner_text(),'$130.53')
        self.assertEqual(page.locator('#guest-1-first').input_value(),'Guest2')
        page.locator('#count').select_option('2');page.locator('#count').select_option('3')
        self.assertEqual(page.locator('#guest-1-first').input_value(),'Guest2')
        page.locator('[name=manual][value=none]').check()
        self.assertEqual(page.locator('#total').inner_text(),'$75.00')
        self.assertFalse(page.locator('[name=manual][value=ebook]').is_checked())
    def test_bls_checkout_mock_no_live_payment(self):
        def post(route,body): route.fulfill(json={'ok':True,'paymentPending':True,'checkoutUrl':CHECKOUT})
        page=self.open('poolbls',post=post);self.fill(page,2);page.locator('[name=manual][value=ebook]').check()
        page.locator('#submit').click();page.wait_for_url(CHECKOUT)
        self.assertEqual(self.posts[0]['ebookQty'],2);self.assertEqual(self.posts[0]['attendeeCount'],2)
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
        payload={'attendeeCount':2,'firstName':'Local','lastName':'Test','email':'local@example.invalid','guestNames':['Guest Test'],'ebookQty':2}
        def post(route,body): route.fulfill(json={'ok':True,'paymentPending':True,'checkoutUrl':CHECKOUT})
        page=self.open('poolbls',post=post,query='?checkout_cancelled=1',saved={'requestId':REQUEST_ID,'payload':payload})
        page.locator('#resume-checkout').wait_for(state='visible')
        self.assertEqual(page.locator('#first').input_value(),'Local');self.assertEqual(page.locator('#guest-0-last').input_value(),'Test')
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

if __name__=='__main__':unittest.main()
