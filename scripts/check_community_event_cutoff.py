from pathlib import Path
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parents[1]/'docs'
CUTOFF=datetime(2026,10,4,15,30,tzinfo=timezone.utc)
results=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True)
 for name in ('earl','jackson'):
  for width in (390,1280):
   for offset in (-1000,0,1000):
    context=browser.new_context(viewport={'width':width,'height':900})
    page=context.new_page();errors=[];posts=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    def serve(route):
     url=route.request.url
     if 'public-event-registration' in url:
      if route.request.method=='POST':posts.append(url)
      route.fulfill(json={'ok':route.request.method!='POST','error':'Mock registration response','event':{'remaining':10,'handsOnCapacity':20},'checkoutUrl':'https://example.invalid/checkout'});return
     from urllib.parse import urlparse,unquote
     path=unquote(urlparse(url).path)
     target=ROOT/path.lstrip('/')
     if target.is_dir():target=target/'index.html'
     if target.is_file():route.fulfill(path=str(target));return
     route.abort()
    page.route('**/*',serve)
    from datetime import timedelta
    page.clock.install(time=CUTOFF+timedelta(milliseconds=offset))
    page.goto('https://www.910cpr.com/'+name+'/');page.wait_for_timeout(40)
    assert not errors,(name,errors)
    closed=offset>=0
    assert page.locator('#submit').is_disabled()==closed
    assert page.locator('#event-passed-banner').is_visible()==closed
    logos=page.locator('.logo-tile')
    assert logos.count()==4
    assert all(logos.nth(i).get_attribute('href') for i in range(4))
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(name,width,'horizontal overflow')
    baseline=0
    if not closed:
     page.locator('#first').fill('Local');page.locator('#last').fill('Test');page.locator('#email').fill('local@example.invalid')
     page.evaluate("document.getElementById('form').requestSubmit()")
     page.wait_for_timeout(40)
     assert len(posts)==1,(name,'pre-cutoff handler did not POST to mock')
     baseline=1
     page.clock.run_for(1001)
     assert page.locator('#submit').is_disabled()
     assert page.locator('#event-passed-banner').is_visible()
    page.evaluate("document.getElementById('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))")
    page.evaluate("document.getElementById('form').requestSubmit()")
    page.locator('#first').press('Enter')
    page.evaluate("document.getElementById('submit').disabled=false")
    page.clock.run_for(1001)
    assert page.locator('#submit').is_disabled()
    assert len(posts)==baseline,(name,'POST after cutoff')
    assert all(page.locator('#event-followup a').nth(i).get_attribute('href') for i in range(page.locator('#event-followup a').count()))
    results.append({'page':name,'width':width,'offsetMs':offset,'pass':True,'posts':len(posts)})
    # Screenshots are local review artifacts and are not written into the repository.
    context.close()
 browser.close()
print(json.dumps(results,indent=2))
