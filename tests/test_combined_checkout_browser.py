"""Isolated browser proof. All API/payment requests are fulfilled in memory.
No hosted registration, payment, file upload or notification is attempted.
"""
import copy
import json
import threading
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

DOCS=Path(__file__).resolve().parents[1]/'docs'
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def profile(key,title,base):
    return {'profileKey':key,'profileVersion':1,'title':title,'description':'Synthetic browser fixture','baseCents':base,'maxStudents':2,'backUrl':'/classes/','driverRules':[{'driver':'native_order'}], 'defaultChoices':['own'],
      'fields':[{'key':key,'wire':wire,'type':typ,'label':label,'required':True,'max_length':100} for key,wire,typ,label in [('first_name','firstName','text','First name'),('last_name','lastName','text','Last name'),('email','email','email','Email'),('phone','phone','tel','Phone')]],
      'optionGroups':[{'key':'materials','label':'Course materials','type':'radio','required':True,'choices':[{'key':'own','label':'I have my own manual','available':True,'amountCents':0,'catalog_keys':[]},{'key':'ebook','label':'Fixture eBook','available':True,'amountCents':2000,'catalog_keys':['fixture-book']}]}], 'uploads':[]}

class CombinedCheckoutBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(DOCS)))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.origin=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def test_shared_form_addition_discount_replay_and_resume_without_external_requests(self):
        self.exercise_flow(False)
    def test_lost_response_reload_resumes_original_basket_without_new_hold(self):
        self.exercise_flow(True)
    def exercise_flow(self,reload):
        primary={'ok':True,'profile':profile('fixture-acls','Fixture ACLS',22500),'selection':{'course':'241108','session':'fixture-A'},'session':{'startsAt':'2030-12-26T19:00:00Z','endsAt':'2030-12-26T23:00:00Z','location':'Fixture location','capacity':2,'durationMinutes':240}}
        added={'ok':True,'profile':profile('fixture-bls','Fixture BLS',7500),'selection':{'course':'209806','session':'fixture-B'},'session':{'startsAt':'2030-12-27T15:00:00Z','endsAt':'2030-12-27T17:00:00Z','location':'Fixture location','capacity':2,'durationMinutes':120}}
        state={'receipt':None,'saved':None,'reserve_attempts':0,'paid':False,'outside':[]}
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            context=browser.new_context(service_workers='block',viewport={'width':390,'height':844})
            page=context.new_page()
            def route_request(route):
                request=route.request;url=request.url
                if '/functions/v1/public-registration/generic/' in url:
                    action=url.split('/generic/')[1].split('?')[0];body=request.post_data_json if request.method=='POST' else None
                    from urllib.parse import urlparse,parse_qs
                    query=parse_qs(urlparse(url).query)
                    if action=='form':
                        if state['saved'] is not None and not query:
                            models=copy.deepcopy([primary,added])
                            for i,m in enumerate(models):m['receipt']=state['receipt']['items'][i]['receipt']
                            result={'ok':True,'basketResume':True,'receipt':state['receipt'],'items':models}
                        else: result=added if query.get('course')==['209806'] else primary
                    elif action=='basket-choices': result={'ok':True,'choices':[{'courseNumber':'209806','family':'BLS','title':'Fixture BLS','sessions':[{'session':'fixture-B','startsAt':'2030-12-27T15:00:00Z','endsAt':'2030-12-27T17:00:00Z','location':'Fixture location'}]}]}
                    elif action=='basket-reserve':
                        state['reserve_attempts']+=1
                        if state['saved'] is None:
                            state['saved']=copy.deepcopy(body)
                            self.assertEqual(len(body['items']),2)
                            self.assertEqual(body['items'][1]['students'][0]['fields']['email'],'updated-synthetic@example.invalid')
                            state['receipt']={'kind':'course_basket','basketId':'fixture-basket','status':'held','amountCents':31250,'currency':'usd','holdExpiresAt':'2030-12-26T14:00:00Z','lines':[], 'items':[{'position':i,'courseNumber':c,'orderId':str(i),'receipt':{'status':'held','students':[{'selectedChoices':body['items'][i]['students'][0]['selectedChoices'],'uploads':{}}]}} for i,c in enumerate(['241108','209806'])]}
                            route.fulfill(status=503,json={'error':'service_unavailable'});return
                        self.assertEqual(state['saved'],body)
                        result={'ok':True,'receipt':state['receipt']}
                    elif action=='basket-status':
                        receipt=copy.deepcopy(state['receipt']);receipt['status']='paid' if state['paid'] else 'held';result={'ok':True,'receipt':receipt}
                    elif action=='basket-checkout': result={'ok':True,'checkoutUrl':'https://checkout.stripe.com/c/pay/synthetic-fixture'}
                    elif action=='basket-form':
                        models=copy.deepcopy([primary,added])
                        for i,m in enumerate(models):m['receipt']=state['receipt']['items'][i]['receipt']
                        result={'ok':True,'receipt':state['receipt'],'items':models}
                    else:
                        self.fail(f'Unexpected API action: {action}')
                    route.fulfill(status=200,json=result);return
                if url.startswith(self.origin+'/'): route.continue_();return
                if url=='https://checkout.stripe.com/c/pay/synthetic-fixture':route.fulfill(status=200,body='Synthetic hosted checkout boundary. No payment.');return
                state['outside'].append(url);route.abort()
            context.route('**/*',route_request)
            page.goto(self.origin+'/register/checkout/?course=241108&session=fixture-A')
            page.locator('#students [data-field=first_name]').fill('Synthetic')
            page.locator('#students [data-field=last_name]').fill('Fixture')
            page.locator('#students [data-field=email]').fill('synthetic@example.invalid')
            page.locator('#students [data-field=phone]').fill('2025550100')
            page.locator('[data-course]').select_option('209806')
            page.locator('[data-time]').select_option('fixture-B')
            page.locator('.extra-participant [data-choice][value=ebook]').check()
            page.locator('#students [data-field=email]').fill('updated-synthetic@example.invalid')
            page.locator('#students [data-field=phone]').click()
            self.assertEqual(page.locator('.extra-participant [data-field=email]').input_value(),'updated-synthetic@example.invalid')
            self.assertIn('Added session discount: $7.50',page.locator('[data-detail]').inner_text())
            self.assertIn('Materials/access: $20.00',page.locator('[data-detail]').inner_text())
            page.locator('#pay').click()
            page.wait_for_function("document.querySelector('#status').textContent.includes('could not complete')")
            key=page.evaluate("sessionStorage.getItem(Object.keys(sessionStorage).find(k=>k.startsWith('native-checkout:')))")
            if reload:
                page.reload()
                page.locator('#total').wait_for()
                self.assertIn('Saved total: $312.50',page.locator('#total').inner_text())
            page.locator('#pay').click()
            page.wait_for_url('https://checkout.stripe.com/c/pay/synthetic-fixture')
            self.assertEqual(state['reserve_attempts'],1 if reload else 2)
            from urllib.parse import urlparse,parse_qs
            # The current nonce was saved before the simulated lost response.
            page.goto(self.origin+'/register/checkout/?basket='+key)
            page.locator('#total').wait_for()
            self.assertIn('Saved total: $312.50',page.locator('#total').inner_text())
            self.assertEqual(page.locator('.extra-participant [data-choice][value=ebook]').is_checked(),True)
            self.assertEqual(page.locator('[data-course]').is_disabled(),True)
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),390)
            state['paid']=True;page.locator('#check-status').click()
            page.wait_for_function("document.querySelector('#result').textContent.includes('registration is confirmed')")
            self.assertEqual(state['outside'],[])
            browser.close()
