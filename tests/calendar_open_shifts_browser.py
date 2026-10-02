"""CyberPC local Chrome QA. External requests blocked; auth stub exists only inside test browser.
Requires installed playwright + Chrome. Writes two review screenshots, never calls live APIs.
"""
from pathlib import Path
import json, threading, http.server, functools, datetime
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root/'docs')))
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}'
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
schedule={'generated_at':now,'sessions':[{'session_id':'fixture-noon','course_id':'210549','course_name':'AHA HeartCode BLS','start_at':'2026-10-05T12:00:00-04:00','end_at':'2026-10-05T12:00:00-04:00','lead_instructor_name':'Brian','location_name':':: Wilmington; Shipyard Blvd','registered_count':None}]}
availability={'generated_at':now,'sources':[{'source_key':key,'generated_at':now,'export_status':'ok'} for key in ['brian_do_not_schedule','amy_availability','nick_availability']],'events':[]}
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    context=browser.new_context(timezone_id='America/New_York',viewport={'width':1440,'height':1000})
    page=context.new_page(); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def route(request):
        u=request.request.url
        if not u.startswith(url):request.abort();return
        if '/admin/admin-auth.js' in u:request.fulfill(content_type='text/javascript',body='window.LanderWareAdminAuth={get:()=>null,fetch:(...args)=>fetch(...args),subscribe:()=>{},onLock:()=>{},set:()=>{},clear:()=>{}};');return
        if '/data/admin_schedule.json' in u:request.fulfill(json=schedule);return
        if '/data/admin_availability.json' in u:request.fulfill(json=availability);return
        if '/data/block-selector-availability/' in u:request.fulfill(json={'dates':[]});return
        request.continue_()
    page.route('**/*',route)
    page.goto(url+'/admin/dashboard.html'); page.wait_for_timeout(1200)
    assert errors==[], errors
    assert page.evaluate("window.lastOpenShiftReport.accepted.filter(c=>c.kind==='skills').length")==12
    assert page.evaluate("window.lastOpenShiftReport.accepted.some(c=>c.kind==='full')")
    assert 'open shifts' in page.locator('[data-day="2026-10-05"]').inner_text()
    assert '12:00 PM' in page.locator('.schedule-row.class').inner_text()
    assert '12:45 PM' in page.locator('.schedule-row.class').inner_text()
    assert 'cleanup until 1:00 PM' in page.locator('.schedule-row.class').inner_text()
    print('errors',errors)
    print('detail',page.locator('#dayDetail').inner_text()[:3500])
    print('report',page.evaluate('window.lastOpenShiftReport?({occupied:window.lastOpenShiftReport.occupied.length,blocks:window.lastOpenShiftReport.blocks.length,edges:window.lastOpenShiftReport.edges.length,candidates:window.lastOpenShiftReport.candidates.length,accepted:window.lastOpenShiftReport.accepted.length,rejected:window.lastOpenShiftReport.rejected.length,diagnostics:window.lastOpenShiftReport.diagnostics}):null'))
    output=root/'review/calendar-open-shifts';output.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(output/'local-desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(output/'local-mobile.png'),full_page=True)
    def starts():
        return page.evaluate("window.lastOpenShiftReport.accepted.filter(c=>c.courseId==='210549').map(c=>c.start.toLocaleTimeString('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit'})).sort()")
    assert starts()==['11:00','13:00']
    for source,expected in [
        ({'session_id':'right','course_id':'210549','course_name':'BLS','start_at':'2026-10-05T13:00:00-04:00','end_at':'2026-10-05T14:00:00-04:00','lead_instructor_name':'Brian','location_name':':: Wilmington; Shipyard Blvd'},['11:00','14:00']),
        ({'session_id':'left','course_id':'210549','course_name':'BLS','start_at':'2026-10-05T11:00:00-04:00','end_at':'2026-10-05T12:00:00-04:00','lead_instructor_name':'Brian','location_name':':: Wilmington; Shipyard Blvd'},['10:00','14:00']),
        ({'session_id':'full','course_id':'209806','course_name':'Full class','start_at':'2026-10-05T14:00:00-04:00','end_at':'2026-10-05T17:00:00-04:00','lead_instructor_name':'Brian','location_name':':: Wilmington; Shipyard Blvd'},['10:00','17:00'])]:
        schedule['sessions'].append(source)
        page.locator('#reloadAvailability').click()
        page.wait_for_function("window.lastOpenShiftReport?.blocks[0]?.sourceIds.length === "+str(len(schedule['sessions'])))
        assert starts()==expected,(starts(),expected)
        assert page.evaluate("window.lastOpenShiftReport.freeIntervals.length")==0
    schedule['sessions']=[]
    page.locator('#reloadAvailability').click()
    page.wait_for_function("window.lastOpenShiftReport?.occupied.length===0")
    page.locator('[data-day="2026-10-05"]').click()
    assert len(starts())==24
    assert starts()[0]=='00:00' and starts()[-1]=='23:00'
    assert errors==[],errors
    print('Rendered desktop/mobile, sequential chain growth, and 24-hour free-day checks passed')
    browser.close()
server.shutdown()
