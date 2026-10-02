"""Local Chrome regression: visible expiry notice; synthetic leases stay closed."""
from pathlib import Path
import datetime,json,sys,threading,http.server,functools
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from scripts.build_bls_block_schedule_pilot import render_html
from playwright.sync_api import sync_playwright
from scripts.block_start_time_selector import load_block_schedule_page_configs
payload=json.loads((root/'data/audit/bls_block_schedule_pilot.json').read_text(encoding='utf-8'));payload['pageConfig']=load_block_schedule_page_configs()['bls'];payload['dates']=[]
html=render_html(payload)
review=root/'review/calendar-open-shifts';review.mkdir(parents=True,exist_ok=True);(review/'stale-notice-preview.html').write_text(html,encoding='utf-8')
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root/'docs')));threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
now=datetime.datetime.now(datetime.timezone.utc);expired=(now-datetime.timedelta(hours=1)).isoformat();future=(now+datetime.timedelta(hours=1)).isoformat()
def course(real):return {'courseId':'209806','courseName':'AHA BLS Provider','courseFamily':'BLS','deliveryMode':'in-person','offerType':'seated_class' if real else 'dynamic_appointment','appointmentUrl':'https://example.test/real' if real else 'https://example.test/dynamic','location':':: Wilmington; Shipyard Blvd','durationMinutes':120}
def feed(expiry):return {'schemaVersion':'selector-resolved-availability.v1','validUntil':expiry,'dates':[{'date':'2026-10-05','displayDate':'Monday, October 5, 2026','startTimes':[{'startTime':'11:00','displayStartTime':'11:00 AM','courses':[course(False)]}]},{'date':'2026-10-12','displayDate':'Monday, October 12, 2026','startTimes':[{'startTime':'17:00','displayStartTime':'5:00 PM','courses':[course(True)]}]}]}
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 for state in ['stale','fresh','failed']:
  page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   u=r.request.url
   if not u.startswith(origin):r.abort();return
   if '/bls.html' in u:r.fulfill(content_type='text/html',body=html);return
   if '/data/block-selector-availability/' in u:
    if state=='failed':r.fulfill(status=503,body='unavailable')
    else:r.fulfill(json=feed(expired if state=='stale' else future))
    return
   r.continue_()
  page.route('**/*',route);page.goto(origin+'/bls.html');page.wait_for_timeout(800);assert errors==[],errors
  notice=page.locator('#availability-notice');text=notice.inner_text() if notice.is_visible() else ''
  dynamic=page.locator('#date-list button[aria-label^="Monday, October 5, 2026"]');real=page.locator('#date-list button[aria-label^="Monday, October 12, 2026"]')
  if state=='stale':
   assert notice.is_visible() and 'refreshing' in text;assert not dynamic.count();assert real.count()==1 and real.is_enabled();assert page.locator('#course-list a[href*=real]').count()==1;assert page.locator('a[href*=dynamic]').count()==0;notice.scroll_into_view_if_needed();page.screenshot(path=str(review/'stale-notice-local.png'),full_page=False)
  elif state=='fresh':assert not notice.is_visible();assert dynamic.count()==1 and dynamic.is_enabled();assert real.is_enabled()
  else:assert notice.is_visible() and 'temporarily unavailable' in text;assert not dynamic.count()
  results.append({'state':state,'notice':text,'errors':errors,'dynamic_date_visible':bool(dynamic.count()),'real_date_visible':bool(real.count())});page.close()
 browser.close()
server.shutdown();(review/'stale-notice-browser-results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
