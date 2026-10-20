import {createRequire} from 'node:module';
const {chromium}=createRequire(import.meta.url)('playwright');
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
const root=new URL('../docs/',import.meta.url);
const server=createServer(async(req,res)=>{try{const path=new URL(req.url,'http://test').pathname;res.setHeader('content-type',path.endsWith('.js')?'text/javascript':path.endsWith('.css')?'text/css':'text/html');res.end(await readFile(new URL('.'+(path.endsWith('/')?path+'index.html':path),root)));}catch{res.writeHead(404).end();}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({headless:true,...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE?{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE}:{})});
try{
 const page=await browser.newPage({viewport:{width:390,height:844}});let confirms=0,help=0;
 const option={id:'11111111-1111-4111-8111-111111111111',course:'AHA BLS Provider',startsAt:'2026-11-03T17:00:00Z',location:'910CPR',address:'4018 Shipyard Blvd, Room B'};
 await page.route('**/functions/v1/registration-reschedule/**',route=>{const action=route.request().url().split('/').at(-1);let response={status:'pending',firstName:'Test',course:option.course,currentStartsAt:'2026-10-24T16:00:00Z',options:[option]};if(action==='confirm'){confirms++;response={...option,confirmationStatus:'sent'};}if(action==='help'){help++;response={ok:true};}return route.fulfill({contentType:'application/json',body:JSON.stringify(response)});});
 await page.goto(`http://127.0.0.1:${server.address().port}/reschedule/#lw_r_${'a'.repeat(64)}`);
 await page.getByRole('button',{name:'Tuesday, November 3, 2026, available times'}).click();
 await page.getByRole('button',{name:'12:00 PM'}).click();
 assert.equal(confirms,0,'Selecting a time must not move the student');
 assert.ok(await page.locator('.no-payment').isVisible());
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'mobile layout overflow');

 await page.getByRole('button',{name:'Confirm this change'}).click();
 await page.locator('#success h2').waitFor();
 assert.equal(confirms,1);assert.ok(await page.getByText('A confirmation email has been sent.').isVisible());
 // Test no token / empty calendar / stale selection with the actual UI code.
 await page.goto(`http://127.0.0.1:${server.address().port}/reschedule/`);await page.reload();
 assert.ok(await page.getByText('Open the private rescheduling link in your email to choose a new time.').isVisible());
 await page.unroute('**/functions/v1/registration-reschedule/**');
 await page.route('**/functions/v1/registration-reschedule/**',route=>route.fulfill({contentType:'application/json',body:JSON.stringify({status:'pending',firstName:'Test',course:option.course,currentStartsAt:option.startsAt,options:[]})}));
 await page.goto(`http://127.0.0.1:${server.address().port}/reschedule/#lw_r_${'b'.repeat(64)}`);await page.reload();
 await page.getByText(/There are no available replacement dates/).waitFor();
 assert.equal(await page.locator('#confirm').isVisible(),false);
 console.log('PASS: mobile date/time/review/confirm, no premature move, success, missing token, empty calendar');
}finally{await browser.close();server.close();}
