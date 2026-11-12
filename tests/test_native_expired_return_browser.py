"""Authorized GitHub CI only: real checkout UI + actual adapter + disposable SQL.

Run: NATIVE_RETURN_TEST_SCOPE=bls python -B -m unittest discover -s tests \
    -p test_native_expired_return_browser.py -v
Default BLS scope never imports adult/Pediatric fixtures. Explicit extended scope
covers all six course variants. No providers, charges, uploads, mail, or sockets.
"""
import hashlib
import html
import json
import mimetypes
import os
from pathlib import Path
import selectors
import subprocess
import tempfile
import unittest
from urllib.parse import parse_qs, urlencode, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('NATIVE_RETURN_SOURCE_ROOT', ROOT)).resolve()
ASSETS = Path(os.environ.get('NATIVE_RETURN_ASSET_ROOT', SOURCE)).resolve()
ORIGIN = 'https://native-expired-return.invalid'
API = 'https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/public-registration/generic/'
SCENARIOS = ('available', 'full', 'after_start', 'finalizer_failure', 'unpaid', 'ambiguous', 'held_ambiguous', 'checkout_open_ambiguous', 'cancelled', 'refunded')
EXPECTED = dict(available='paid', full='payment_review', after_start='payment_review',
                finalizer_failure='processing', unpaid='expired', cancelled='cancelled', refunded='refunded')
ARTIFACTS = Path(os.environ.get('NATIVE_RETURN_BROWSER_ARTIFACTS', ROOT / 'test-results/native-expired-return-browser'))


class SqlBridge:
    """Persistent stdin/stdout messages, not an HTTP server or a fake receipt API."""
    def __init__(self):
        self.stderr = tempfile.TemporaryFile(mode='w+t')
        self.process = subprocess.Popen(
            ['node', str(ROOT / 'tests/helpers/native-expired-return-browser.mjs')],
            cwd=SOURCE, env=os.environ.copy(), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=self.stderr, text=True, bufsize=1)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.ready = self.read()
        if not self.ready.get('ready'):
            raise AssertionError(self.ready)

    def read(self):
        if not self.selector.select(timeout=120):
            raise AssertionError('SQL bridge timed out: ' + self.log())
        line = self.process.stdout.readline()
        if not line:
            raise AssertionError('SQL bridge exited: ' + self.log())
        packet = json.loads(line)
        if packet.get('ok') is not True:
            raise AssertionError(packet)
        return packet

    def call(self, op, **fields):
        self.process.stdin.write(json.dumps(dict(op=op, **fields)) + '\n')
        self.process.stdin.flush()
        return self.read()['result']

    def log(self):
        self.stderr.flush()
        self.stderr.seek(0)
        return self.stderr.read()

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            try:
                self.process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=10)
        self.selector.close()
        self.process.stdout.close()
        self.stderr.close()


class NativeExpiredReturnBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Missing browser access must be an explicit failure, never a silent skip.
        # Do not set this environment variable locally to bypass the launch limit.
        if os.environ.get('GITHUB_ACTIONS') != 'true':
            raise RuntimeError('Browser execution is restricted to authorized GitHub CI. Run only the Node --smoke check locally.')
        cls.bridge = SqlBridge()
        cls.addClassCleanup(cls.bridge.close)
        cls.runtime = sync_playwright().start()
        cls.addClassCleanup(cls.runtime.stop)
        cls.browser = cls.runtime.chromium.launch()
        cls.addClassCleanup(cls.browser.close)
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        cls.evidence = []

    @classmethod
    def tearDownClass(cls):
        hashes = {}
        for relative in ('docs/register/index.html', 'docs/assets/inline-registration.js',
                         'docs/assets/generic-checkout.js',
                         'supabase/functions/public-registration/generic.mjs',
                         'supabase/functions/public-registration/index.ts'):
            base = ASSETS if relative in ('docs/register/index.html', 'docs/assets/inline-registration.js') else SOURCE
            hashes[relative] = hashlib.sha256((base / relative).read_bytes()).hexdigest()
        (ARTIFACTS / 'synthetic-evidence.json').write_text(json.dumps(
            dict(scope=cls.bridge.ready['scope'], sourceHashes=hashes, cases=cls.evidence), indent=2))

    def fixture_page(self):
        # Synthetic calendar only provides the DOM contract. The actual production
        # inline-registration script creates and owns the iframe and Change time UI.
        link = '/register/?' + urlencode(dict(session=self.case['session']))
        return '''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/assets/site-theme.css"><title>Synthetic recovery fixture</title></head>
<body><main style="display:grid;grid-template-columns:1fr;max-width:900px;margin:auto">
<section class="panel"><div id="start-list"><button aria-pressed="true">Synthetic selected class</button></div></section>
<section class="panel"><div id="course-list"><a class="register-link" href="''' + html.escape(link, quote=True) + '''">Resume saved registration</a></div></section>
</main><script src="/assets/inline-registration.js"></script></body></html>'''

    def open(self, course, scenario, width, mode):
        self.case = self.bridge.call('seed', course=course, scenario=scenario)
        self.mode, self.width = mode, width
        self.requests, self.responses, self.forbidden, self.errors = [], [], [], []
        self.console, self.failed, self.route_errors = [], [], []
        self.context = self.browser.new_context(viewport=dict(width=width, height=900), service_workers='block')
        self.context.set_default_timeout(15000)
        self.context.add_cookies([dict(name='lw_analytics_excluded', value='1', url=ORIGIN)])
        if mode == 'saved-frame':
            storage_key = 'native-checkout:' + json.dumps([['session', self.case['session']]], separators=(',', ':'))
            self.context.add_init_script('sessionStorage.setItem(' + json.dumps(storage_key) + ',' + json.dumps(self.case['key']) + ');')
        self.context.add_init_script('''window.__returnPaymentExposures=[];
new MutationObserver(()=>{const p=document.querySelector('#pay');
if(p&&!p.hidden&&p.getClientRects().length)window.__returnPaymentExposures.push({url:location.href,text:p.textContent});
}).observe(document,{childList:true,subtree:true,attributes:true});''')
        cors = {'access-control-allow-origin': ORIGIN, 'access-control-allow-methods': 'GET',
                'access-control-allow-headers': 'idempotency-key', 'cache-control': 'no-store'}
        assets = {'/register/': 'docs/register/index.html',
                  '/assets/site-theme.css': 'docs/assets/site-theme.css',
                  '/assets/site-theme.js': 'docs/assets/site-theme.js',
                  '/assets/inline-registration.js': 'docs/assets/inline-registration.js',
                  '/assets/generic-checkout.js': 'docs/assets/generic-checkout.js',
                  '/assets/checkout-profile.js': 'docs/assets/checkout-profile.js',
                  '/assets/checkout-receipt.js': 'docs/assets/checkout-receipt.js'}

        def serve(route):
            request = route.request
            parsed = urlsplit(request.url)
            packet = dict(method=request.method, url=request.url, key=request.headers.get('idempotency-key'))
            self.requests.append(packet)
            try:
                if request.url.startswith(API):
                    action = parsed.path.removeprefix(urlsplit(API).path)
                    if action not in ('form', 'status') or request.method not in ('OPTIONS', 'GET'):
                        self.forbidden.append(packet)
                        return route.abort()
                    if request.method == 'OPTIONS':
                        return route.fulfill(status=204, headers=cors)
                    result = self.bridge.call('request', **packet)
                    self.responses.append(dict(action=action, request=packet, **result))
                    return route.fulfill(status=result['status'], json=result['body'], headers=cors)
                if parsed.netloc != urlsplit(ORIGIN).netloc or request.method != 'GET':
                    self.forbidden.append(packet)
                    return route.abort()
                if parsed.path == '/synthetic-calendar.html':
                    return route.fulfill(body=self.fixture_page(), content_type='text/html', headers={'cache-control': 'no-store'})
                if parsed.path == '/favicon.ico':
                    return route.fulfill(status=204)
                if parsed.path == '/history-away.html':
                    return route.fulfill(body='<html><head><title>Synthetic away</title></head><body>History boundary</body></html>', content_type='text/html')
                if parsed.path in assets:
                    relative = assets[parsed.path]
                    base = SOURCE if parsed.path in ('/assets/generic-checkout.js', '/assets/checkout-profile.js', '/assets/checkout-receipt.js') else ASSETS
                    target = (base / relative).resolve()
                    if not target.is_relative_to(base) or not target.is_file():
                        raise AssertionError('Missing actual asset: ' + str(target))
                    return route.fulfill(path=str(target), content_type=mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
                self.forbidden.append(packet)
                return route.abort()
            except Exception as error:
                self.route_errors.append(str(error))
                return route.abort()

        self.context.route('**/*', serve)
        self.page = self.context.new_page()
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('console', lambda message: self.console.append(dict(type=message.type, text=message.text)))
        self.page.on('requestfailed', lambda request: self.failed.append(dict(url=request.url, failure=request.failure)))
        if mode == 'saved-frame':
            self.page.goto(ORIGIN + '/synthetic-calendar.html')
            self.page.locator('#course-list .register-link').click()
            view = self.frame()
        else:
            self.page.goto(ORIGIN + '/register/?' + urlencode(dict(recover=self.case['recover'])))
            view = self.page
        self.assert_state(view, scenario)
        return view

    def frame(self):
        locator = self.page.locator('iframe[title="Class registration and checkout"]')
        locator.wait_for(state='visible')
        frame = locator.element_handle().content_frame()
        self.assertIsNotNone(frame)
        return frame

    def assert_state(self, view, scenario):
        texts = dict(available='Your registration is confirmed.', full='needs staff review',
                     after_start='needs staff review', finalizer_failure='registration confirmation is pending',
                     unpaid='Your seat hold expired.', ambiguous='Your payment is not confirmed.',
                     held_ambiguous='Your payment is not confirmed.', checkout_open_ambiguous='Your payment is not confirmed.',
                     cancelled='This registration was canceled.', refunded='This order was refunded;')
        view.wait_for_function("text=>document.querySelector('#app')?.textContent.includes(text)", arg=texts[scenario])
        content = view.locator('#app').inner_text()
        self.assertEqual(view.locator('#checkout-form').count(), 1, 'receipt shell must survive status failure')
        self.assertFalse(view.locator('#pay').is_visible(), content)
        self.assertEqual(view.evaluate('window.__returnPaymentExposures'), [], 'payment was exposed during a return')
        self.assertEqual(view.locator('a[href^="https://checkout.stripe.com"]').count(), 0)
        if scenario == 'available':
            self.assertEqual(view.locator('#result').inner_text(), 'Payment received. Your registration is confirmed.')
            self.assertFalse(view.locator('#checkout-form').is_visible())
        else:
            self.assertTrue(view.locator('#check-status').is_visible())
            self.assertNotIn('Your registration is confirmed.', content)
        if scenario in ('full', 'after_start', 'finalizer_failure'):
            self.assertIn('Payment received', content)
            self.assertIn('Do not pay again.', content)
        if scenario in ('full', 'after_start'):
            self.assertIn('not a confirmed booking', content)
        if scenario in ('unpaid', 'ambiguous', 'held_ambiguous', 'checkout_open_ambiguous'):
            self.assertNotIn('Payment received', content)
            self.assertNotIn('You may continue to secure payment', content)
        if self.mode == 'saved-frame':
            self.assertEqual(urlsplit(self.page.url).path, '/synthetic-calendar.html')
            self.assertEqual(parse_qs(urlsplit(view.url).query).get('embed'), ['1'])
        self.assertEqual(self.route_errors, [])
        self.assertEqual(self.forbidden, [])
        self.assertEqual(self.errors, [])
        self.assertEqual(self.failed, [])
        self.assertEqual(view.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), True,
                         'checkout horizontally overflows at this viewport')

    def assert_durable(self, scenario):
        state = self.bridge.call('inspect')
        count = 1 if scenario == 'available' else 0
        self.assertEqual(state['footprint'], dict(registrations=count, studentLinks=count, confirmations=count))
        self.assertEqual(int(state['orderCount']), 1)
        self.assertEqual(state['orderId'], self.case['orderId'])
        self.assertEqual(state['paymentObserved'], scenario in ('available', 'full', 'after_start', 'finalizer_failure', 'cancelled', 'refunded'))
        self.assertEqual(state['status'], dict(available='paid', full='expired', after_start='expired',
                        finalizer_failure='expired', unpaid='expired', ambiguous='expired', held_ambiguous='held', checkout_open_ambiguous='checkout_open', cancelled='cancelled', refunded='refunded')[scenario])
        provider = [call for call in state['calls'] if call['path'].startswith('/v1/')]
        self.assertTrue(all(call['method'] == 'GET' and call['path'].endswith('/' + state['stripeCheckoutId']) for call in provider))
        # payment_review is the public receipt projection, not an order enum.
        # Keep the persisted expired state and the precise reconciliation reason.
        if scenario in ('full', 'after_start'):
            self.assertEqual(state['reconciliationError'],
                             'paid_seat_unavailable' if scenario == 'full' else 'session_not_open')
        elif scenario not in ('cancelled', 'refunded'):
            self.assertIsNone(state['reconciliationError'])
        records = [call for call in state['calls'] if call['path'].endswith('/native_checkout_record_payment')]
        if self.case['scenario'] == 'finalizer_failure':
            # Each user-requested recovery may retry the idempotent recording RPC
            # before finalization. Durable footprints above must still be 0 or 1.
            self.assertGreaterEqual(len(records), 1)
        else:
            self.assertEqual(len(records), 1 if scenario in ('available', 'full', 'after_start') else 0)
        if scenario in ('cancelled', 'refunded'):
            self.assertEqual(provider, [])
            self.assertFalse(any(call['path'].endswith('/native_checkout_finalize_order') for call in state['calls']))
        statuses = [response for response in self.responses if response['action'] == 'status']
        self.assertTrue(statuses)
        if 'ambiguous' in scenario:
            self.assertTrue(all(response['status'] == 500 and response['body']['error'] == 'payment_evidence_mismatch' for response in statuses))
        else:
            self.assertEqual(statuses[-1]['body']['receipt']['status'], EXPECTED[scenario])
        self.assertEqual(self.forbidden, [])
        return state

    def recheck(self, view):
        with self.page.expect_response(lambda response: response.url == API + 'status') as pending:
            view.locator('#check-status').click()
        pending.value.finished()

    def repeat_and_history(self, view, scenario):
        # Recheck by real UI, not direct API calls. Confirmed receipts intentionally
        # hide the form; reload, rather than clicking a hidden recheck button.
        if scenario != 'available':
            for _ in range(3):
                self.recheck(view)
                self.assert_state(view, scenario)
        for _ in range(2):
            view.goto(view.url)
            self.assert_state(view, scenario)
        if self.mode == 'saved-frame':
            self.page.locator('#selected-time-checkout > button').click()
            self.assertFalse(self.page.locator('#selected-time-checkout').is_visible())
            self.page.locator('#course-list .register-link').click()
            view = self.frame()
            self.assert_state(view, scenario)
            # The iframe owns this history entry; do not treat it as top navigation.
            saved = view.url
            view.goto(ORIGIN + '/history-away.html')
            view.evaluate('history.back()')
            view.wait_for_url(saved)
            self.assert_state(view, scenario)
            view.evaluate('history.forward()')
            view.wait_for_url(ORIGIN + '/history-away.html')
            view.evaluate('history.back()')
            view.wait_for_url(saved)
            self.assert_state(view, scenario)
            self.page.reload()
            self.page.locator('#course-list .register-link').click()
            view = self.frame()
            self.assert_state(view, scenario)
        else:
            # Recovery populated the original order nonce; the canonical saved-order
            # URL must resume it without a recover token or a new checkout.
            self.page.goto(ORIGIN + '/register/?' + urlencode(dict(order=self.case['orderId'])))
            self.assert_state(self.page, scenario)
            self.page.goto(ORIGIN + '/history-away.html')
            self.page.go_back()
            self.assert_state(self.page, scenario)
            self.page.go_forward()
            self.assertEqual(urlsplit(self.page.url).path, '/history-away.html')
            self.page.go_back()
            self.assert_state(self.page, scenario)
            view = self.page
        return view

    def diagnostics(self, label):
        frames = []
        for frame in self.page.frames:
            try:
                state = frame.evaluate("({app:document.querySelector('#app')?.innerText,ready:document.readyState,paymentExposures:window.__returnPaymentExposures})")
            except Exception as error:
                state = dict(inspectionError=str(error))
            frames.append(dict(url=frame.url, **state))
        try:
            durable = self.bridge.call('inspect')
        except Exception as error:
            durable = dict(inspectionError=str(error))
        packet = dict(case=self.case, width=self.width, mode=self.mode, page=self.page.url, frames=frames,
                      durable=durable, requests=self.requests, responses=self.responses, forbidden=self.forbidden,
                      errors=self.errors, console=self.console, failedRequests=self.failed,
                      routeErrors=self.route_errors, bridgeLog=self.bridge.log())
        (ARTIFACTS / (label + '.json')).write_text(json.dumps(packet, indent=2))
        try:
            self.page.screenshot(path=str(ARTIFACTS / (label + '.png')), full_page=True)
        except Exception as error:
            packet['screenshotError'] = str(error)
        print('NATIVE_EXPIRED_RETURN_SYNTHETIC_DIAGNOSTICS ' + json.dumps(packet), flush=True)

    def run_case(self, course, scenario, width, mode):
        self.context = None
        self.page = None
        label = f'{course}-{scenario}-{width}-{mode}'
        try:
            view = self.open(course, scenario, width, mode)
            self.assert_durable(scenario)
            view = self.repeat_and_history(view, scenario)
            state = self.assert_durable(scenario)
            if scenario == 'finalizer_failure':
                self.bridge.call('provider_outage')
                self.recheck(view)
                self.assert_state(view, scenario)
                self.assert_durable(scenario)
                self.bridge.call('repair')
                self.recheck(view)
                self.assert_state(view, 'available')
                repaired = self.assert_durable('available')
                mutation_paths = ('/native_checkout_record_payment', '/native_checkout_finalize_order')
                settled_calls = [call for call in repaired['calls'] if call['path'].endswith(mutation_paths)]
                view.goto(view.url)
                self.assert_state(view, 'available')
                state = self.assert_durable('available')
                self.assertEqual([call for call in state['calls'] if call['path'].endswith(mutation_paths)],
                                 settled_calls, 'paid replay must not record or finalize payment again')
            if scenario.endswith('_ambiguous'):
                self.bridge.call('verify_unpaid')
                self.recheck(view)
                view.wait_for_function("document.querySelector('#pay')?.hidden === false")
                self.assertTrue(view.locator('#pay').is_visible())
                self.assertIn('You may continue to secure payment', view.locator('#status').inner_text())
                self.assertNotIn('Payment received', view.locator('#app').inner_text())
                state = self.bridge.call('inspect')
                self.assertEqual(state['status'], scenario.removesuffix('_ambiguous'))
                self.assertFalse(state['paymentObserved'])
                self.assertEqual(state['footprint'], dict(registrations=0, studentLinks=0, confirmations=0))
                self.assertEqual(int(state['orderCount']), 1)
                self.assertEqual(self.responses[-1]['status'], 200)
                self.assertEqual(self.responses[-1]['body']['receipt']['status'], state['status'])
                self.assertEqual(self.forbidden, [])
                self.assertEqual(self.errors, [])
            self.evidence.append(dict(course=course, scenario=scenario, width=width, mode=mode,
                                      footprint=state['footprint'], status=state['status'], orderCount=state['orderCount']))
        except Exception:
            if self.page is not None:
                self.diagnostics(label)
            raise
        finally:
            if self.context is not None:
                self.context.close()

    def test_expired_saved_iframe_matrix_mobile_desktop(self):
        for course in self.bridge.ready['courses']:
            for scenario in SCENARIOS:
                for width in (390, 1280):
                    with self.subTest(course=course, scenario=scenario, width=width):
                        self.run_case(course, scenario, width, 'saved-frame')

    def test_recovery_url_and_saved_order_history_mobile_desktop(self):
        for scenario in SCENARIOS:
            for width in (390, 1280):
                with self.subTest(scenario=scenario, width=width):
                    self.run_case('209806', scenario, width, 'recovery-page')


if __name__ == '__main__':
    unittest.main()
