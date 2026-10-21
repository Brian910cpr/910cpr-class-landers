import functools, http.server, json, os, threading, unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

class CalendarBrowserTest(unittest.TestCase):
 def test_calendar_themes_and_booking_boundary(self):
  handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(Path(__file__).resolve().parents[1]/'docs'))
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
  threading.Thread(target=server.serve_forever,daemon=True).start()
  option={'id':'synthetic-session','course':'AHA BLS Provider','startsAt':'2026-10-23T14:30:00Z','location':'Test classroom','address':'Test address'}
  options=[option,{**option,'id':'synthetic-november','startsAt':'2026-11-03T17:00:00Z'}]
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_EXECUTABLE'),args=['--no-sandbox','--disable-dev-shm-usage'])
    for theme in ['light','dark']:
     for width in [390,1440]:
      with self.subTest(theme=theme,width=width):
       page=browser.new_page(viewport={'width':width,'height':900},color_scheme=theme)
       page.set_default_timeout(5000)
       errors=[]
       page.on('pageerror',lambda e:errors.append(str(e)))
       confirmations=[]
       def route(request):
        action=request.request.url.rsplit('/',1)[-1]
        if action=='confirm':
         confirmations.append(request.request.post_data_json)
         payload={**option,'confirmationStatus':'sent'}
        else: payload={'status':'pending','firstName':'Test','course':option['course'],'currentStartsAt':'2026-10-20T14:30:00Z','options':options}
        request.fulfill(content_type='application/json',body=json.dumps(payload))
       page.route('**/functions/v1/registration-reschedule/**',route)
       page.route('**/www.googletagmanager.com/**',lambda r:r.abort())
       page.goto(f'http://127.0.0.1:{server.server_port}/reschedule/#lw_r_'+('a'*64))
       page.locator('#calendar-month').wait_for()
       self.assertEqual(page.locator('#calendar-month').inner_text(),'October 2026')
       self.assertEqual(page.locator('.weekday').count(),7)
       self.assertEqual(page.locator('.calendar-grid button').count(),31)
       self.assertTrue(page.get_by_role('button',name='Thu, Oct 22, 2026',exact=True).is_disabled())
       page.get_by_role('button',name='Next month',exact=True).click()
       self.assertEqual(page.locator('#calendar-month').inner_text(),'November 2026')
       self.assertTrue(page.get_by_role('button',name='Next month',exact=True).is_disabled())
       page.get_by_role('button',name='Previous month',exact=True).click()
       page.get_by_role('button',name='Fri, Oct 23, 2026',exact=True).click()
       page.get_by_role('button',name='10:30 AM',exact=True).click()
       self.assertTrue(page.locator('#review').is_visible())
       self.assertEqual(confirmations,[],'Selection must never mutate a booking')
       page.get_by_role('checkbox',name='Evening,',exact=False).check()
       self.assertIn('No times match',page.locator('#dates').inner_text())
       self.assertFalse(page.locator('#review').is_visible(),'Filtering must clear stale selections')
       self.assertEqual(page.locator('#times button').count(),0)
       self.assertEqual(confirmations,[])
       page.get_by_role('button',name='Clear timing filters',exact=True).click()
       self.assertEqual(page.locator('#calendar-month').inner_text(),'October 2026')
       page.locator('#availability-filters-smart').fill('after 6pm')
       page.locator('#availability-filters-smart').press('Enter')
       self.assertIn('No times match',page.locator('#dates').inner_text())
       page.get_by_role('button',name='Clear timing filters',exact=True).click()
       page.locator('#availability-filters input[value=am]').check()
       page.get_by_role('button',name='Fri, Oct 23, 2026',exact=True).click()
       page.get_by_role('button',name='10:30 AM',exact=True).click()

       self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
       contrast=page.evaluate("""()=>{const rgb=s=>s.match(/[0-9.]+/g).slice(0,3).map(Number);const lum=c=>c.map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4}).reduce((v,x,i)=>v+x*[.2126,.7152,.0722][i],0);let bg=lum(rgb(getComputedStyle(document.querySelector('main')).backgroundColor));return ['h1','#intro','footer p'].map(s=>{let fg=lum(rgb(getComputedStyle(document.querySelector(s)).color));return (Math.max(bg,fg)+.05)/(Math.min(bg,fg)+.05)})}""")
       self.assertTrue(all(c>=4.5 for c in contrast),str(contrast))
       page.get_by_role('button',name='Confirm this change',exact=True).click()
       page.locator('#success').wait_for(state='visible')
       self.assertEqual(confirmations,[{'sessionId':'synthetic-session'}])
       self.assertEqual(errors,[])
       page.close()
    browser.close()
  finally:server.shutdown();server.server_close()

if __name__=='__main__':unittest.main()
