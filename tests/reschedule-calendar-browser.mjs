import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import {createServer} from 'node:http';
const {chromium}=createRequire(import.meta.url)('playwright');
const server=createServer(async(req,res)=>{try{const path=new URL(req.url,'http://test').pathname;res.setHeader('content-type',path.endsWith('.js')?'text/javascript':path.endsWith('.css')?'text/css':'text/html');res.end(await readFile(new URL('../docs'+(path.endsWith('/')?path+'index.html':path),import.meta.url)));}catch{res.writeHead(404).end();}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const origin=`http://127.0.0.1:${server.address().port}`;
const browser=await chromium.launch({headless:true,...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE?{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE}:{})});
const errors=[],outbound=[];let confirms=0;
try{
 const page=await browser.newPage({viewport:{width:1100,height:900}});page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().endsWith('/confirm'))confirms++;});
 const fixture={id:'synthetic-initial',course:'Synthetic BLS',startsAt:'2026-11-18T18:00:00Z',location:'Synthetic room'};
 await page.route('**/functions/v1/registration-reschedule/**',route=>route.fulfill({json:route.request().url().endsWith('/confirm')?{...fixture,confirmationStatus:'sent'}:{status:'pending',firstName:'Synthetic',course:fixture.course,currentStartsAt:'2026-10-24T18:00:00Z',options:[fixture,{...fixture,id:'next',startsAt:'2026-12-10T18:00:00Z'}]}}));
 await page.goto(origin+'/reschedule/#lw_r_'+'a'.repeat(64));await page.locator('#dates button:not(:disabled)').first().waitFor();
 for(const width of [1100,768,390,320]){
  await page.setViewportSize({width,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`Overflow ${width}`);
  const targets=await page.locator('#dates button:not(:disabled),.calendar-navigation button').evaluateAll(xs=>xs.map(x=>({w:x.getBoundingClientRect().width,h:x.getBoundingClientRect().height})));
  assert.ok(targets.every(x=>x.w>=44&&x.h>=44),JSON.stringify({width,targets}));
 }
 await page.setViewportSize({width:390,height:844});
 const first=page.locator('#dates button:not(:disabled)').first();await first.focus();await page.keyboard.press('Enter');assert.equal(await page.locator('#time-heading').isVisible(),true);assert.equal(await page.locator('#review').isVisible(),false);
 await page.locator('#times button').first().click();assert.equal(await page.locator('#review').isVisible(),true);assert.equal(confirms,0);
 await page.locator('#next-month').click();assert.equal(await page.locator('#review').isVisible(),false);assert.equal(await page.locator('#time-heading').isVisible(),false);
 await page.locator('#dates button:not(:disabled)').first().focus();await page.keyboard.press('End');assert.equal(await page.evaluate(()=>document.activeElement.dataset.day),await page.locator('#dates button:not(:disabled)').last().getAttribute('data-day'));
 await page.keyboard.press('Home');await page.keyboard.press('Enter');await page.locator('#times button').first().click();await page.locator('#back').click();assert.equal(await page.evaluate(()=>document.activeElement.getAttribute('aria-pressed')),'true');
 await page.locator('#times button').first().click();await page.setViewportSize({width:1100,height:900});
 await page.locator('#confirm').click();await page.locator('#success').waitFor({state:'visible'});assert.equal(confirms,1);assert.ok(await page.getByText('A confirmation email has been sent.',{exact:true}).isVisible());
 await page.unroute('**/functions/v1/registration-reschedule/**');
 // Sparse synthetic feeds exercise all three courses, empty months and exact IDs.
 for(const course of ['209806','359474','209809']){
  const options=[{id:course+'-late',course,startsAt:'2027-02-05T18:00:00Z',location:'Synthetic room'},{id:course+'-early',course,startsAt:'2026-12-02T00:30:00Z',location:'Synthetic room'}];
  await page.route('**/functions/v1/registration-reschedule/context',route=>route.fulfill({json:{status:'pending',firstName:'Synthetic',course,currentStartsAt:'2026-10-21T18:00:00Z',options}}));
  await page.reload();await page.locator('#dates button:not(:disabled)').first().waitFor();assert.equal(await page.locator('#calendar-month').textContent(),'December 2026');assert.equal(await page.locator('#dates button:not(:disabled)').count(),1);assert.equal(await page.locator('#dates button:not(:disabled)').getAttribute('data-day'),'2026-12-01');
  await page.locator('#next-month').click();assert.equal(await page.locator('#calendar-month').textContent(),'January 2027');assert.equal(await page.locator('#dates button:not(:disabled)').count(),0);assert.match(await page.locator('#calendar-status').textContent(),/No available dates/);
  await page.locator('#next-month').click();assert.equal(await page.locator('#next-month').isDisabled(),true);await page.locator('#dates button:not(:disabled)').click();await page.locator('#times button').click();
  let sent;await page.route('**/functions/v1/registration-reschedule/confirm',route=>{sent=route.request().postDataJSON();return route.fulfill({status:409,json:{error:'session_not_available'}});});
  await page.locator('#confirm').click();await page.locator('#status').filter({hasText:'no longer available'}).waitFor();assert.deepEqual(sent,{sessionId:course+'-late'});assert.equal(await page.locator('#review').isVisible(),false);
  await page.unroute('**/functions/v1/registration-reschedule/context');await page.unroute('**/functions/v1/registration-reschedule/confirm');
 }
 assert.deepEqual(errors,[]);assert.deepEqual(outbound,[]);const receipt={status:'passed',viewportWidths:[1100,768,390,320],courseTypes:3,mockedConfirmations:1,productionTransfers:0,outboundRequests:0,pageErrors:0,checks:['44px targets','no overflow','keyboard selection','month bounds','empty month','Eastern day grouping','exact offer ID','failed confirm refresh']};console.log(JSON.stringify(receipt));
}finally{await browser.close();server.close();}
