import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {publishedOffers,localStart,validToken,familyPath} from '../supabase/functions/registration-reschedule/policy.mjs';
const now=Date.parse('2026-10-19T18:00:00Z');
function publication(extra={}){return {generatedAt:new Date(now-60000).toISOString(),validUntil:new Date(now+60000).toISOString(),dates:[{date:'2026-10-25',startTimes:[{startTime:'10:00',courses:[{courseId:'209806',offerType:'seated_class',registrationUrl:'https://coastalcprtraining.enrollware.com/enroll?id=123456'}]}]}],...extra};}
test('private tokens cannot be a registration ID or guessed email',()=>{assert.ok(validToken('lw_r_'+'a'.repeat(64)));assert.ok(!validToken('person@example.com'));assert.ok(!validToken('123456'));assert.ok(!validToken('lw_r_'+'a'.repeat(63)));});
test('only exact same-course trusted registration URLs are candidates',()=>{assert.equal(publishedOffers(publication(),'359474',now).length,0);assert.equal(publishedOffers(publication(),'209806',now)[0].externalId,'123456');const p=publication();p.dates[0].startTimes[0].courses[0].registrationUrl='https://evil.example/enroll?id=123456';assert.deepEqual(publishedOffers(p,'209806',now),[]);});
test('stale or missing calendar fails closed; expired synthetic offers suppressed',()=>{assert.throws(()=>publishedOffers(publication({generatedAt:new Date(now-31*60000).toISOString()}),'209806',now),/calendar_refresh_required/);assert.throws(()=>publishedOffers(publication({generatedAt:undefined}),'209806',now));const p=publication({validUntil:new Date(now-1000).toISOString()});assert.equal(publishedOffers(p,'209806',now).length,1);p.dates[0].startTimes[0].courses[0].offerType='barnacle';assert.equal(publishedOffers(p,'209806',now).length,0);});
test('Eastern time matches publication across daylight saving changes',()=>{assert.equal(localStart('2026-10-25T14:00:00Z'),'2026-10-25T10:00');assert.equal(localStart('2026-11-03T17:00:00Z'),'2026-11-03T12:00');assert.equal(familyPath('AHA Heartsaver First Aid CPR AED'),'heartsaver');});
globalThis.Deno={env:{get:()=>undefined}};
const {handler}=await import('../supabase/functions/registration-reschedule/index.ts');
test('untrusted origins and missing capability cannot access registration data',async()=>{assert.equal((await handler(new Request('https://test/context',{method:'POST',headers:{origin:'https://evil.example'},body:'{}'}))).status,403);assert.equal((await handler(new Request('https://test/context',{method:'POST',body:'{}'}))).status,401);assert.equal((await handler(new Request('https://test/issue',{method:'POST',body:'{}'}))).status,401);});
test('GET requests cannot move a registration',async()=>{assert.equal((await handler(new Request('https://test/confirm'))).status,405);});
test('confirmation uses server publication and survives an email provider failure',async()=>{
 const originalFetch=globalThis.fetch;const calls=[];const now=Date.now();
 const selected={id:'11111111-1111-4111-8111-111111111111',course:'AHA BLS Provider',startsAt:'2026-10-25T14:00:00Z'};
 Deno.env.get=name=>({SUPABASE_URL:'https://database.test',SUPABASE_SERVICE_ROLE_KEY:'test-only',RESEND_API_KEY:'test-only'}[name]);
 globalThis.fetch=async(url,init={})=>{calls.push({url:String(url),body:init.body&&JSON.parse(init.body)});const path=String(url);
  let result=[];
  if(path.endsWith('/rpc/registration_reschedule_context'))result={status:'pending',course:selected.course,courseNumber:'209806',options:[selected]};
  else if(path.includes('block-selector-availability'))result=publication({generatedAt:new Date(now).toISOString(),validUntil:new Date(now+60000).toISOString()});
  else if(path.includes('/class_sessions?'))result=[{id:selected.id,external_class_id:'123456'}];
  else if(path.endsWith('/rpc/confirm_registration_reschedule'))result={...selected,registrationId:'22222222-2222-4222-8222-222222222222'};
  else if(path.endsWith('/rpc/claim_reschedule_confirmations'))result=[{id:'33333333-3333-4333-8333-333333333333',recipient:'test@example.invalid',subject:'Test',body:'Test'}];
  else if(path==='https://api.resend.com/emails')return new Response('{}',{status:503});
  return new Response(JSON.stringify(result),{status:200,headers:{'content-type':'application/json'}});
 };
 try{
  const response=await handler(new Request('https://test/confirm',{method:'POST',headers:{'x-reschedule-token':'lw_r_'+'a'.repeat(64),'content-type':'application/json'},body:JSON.stringify({sessionId:selected.id,publishedIds:['attacker-controlled']})}));
  assert.equal(response.status,200);assert.equal((await response.json()).confirmationStatus,'pending');
  const move=calls.find(c=>c.url.endsWith('/rpc/confirm_registration_reschedule'));
  assert.deepEqual(move.body.p_published_ids,['123456']);
  assert.ok(calls.some(c=>c.url.includes('registration_reschedule_deliveries?')&&c.body?.status==='failed'));
 }finally{globalThis.fetch=originalFetch;Deno.env.get=()=>undefined;}
});

const selectorFixture=JSON.parse(readFileSync(new URL('./fixtures/reschedule-selector-offers.json',import.meta.url)));
function dynamicPublication(courseNumber='209806',instant=Date.parse(selectorFixture.generatedAt)) {
 const offer=structuredClone(selectorFixture.offers.find(o=>o.courseId===courseNumber)||selectorFixture.offers[0]);
 // Heartsaver uses the same selector contract; its course mapping is verified in canonical courses.
 offer.courseId=courseNumber;
 offer.appointmentUrl=offer.registrationUrl=offer.registrationUrl.replace(/courseId=\d+/,`courseId=${courseNumber}`);
 offer.validUntil=new Date(instant+60000).toISOString();
 return {generatedAt:new Date(instant).toISOString(),validUntil:offer.validUntil,
  dates:[{date:offer.date,startTimes:[{startTime:offer.startTime,courses:[offer]}]}]};
}
test('dynamic choices retain exact identity for Initial, Renewal and Heartsaver without a canonical session',()=>{
 const instant=Date.parse(selectorFixture.generatedAt);
 for(const course of ['209806','359474','209809']) {
  const p=dynamicPublication(course),[o]=publishedOffers(p,course,instant);
  assert.equal(o.kind,'dynamic');assert.equal(o.courseNumber,course);assert.equal(o.startsAt,'2026-10-23T04:00:00.000Z');
  assert.equal(o.consumptionEndsAt,'2026-10-23T06:30:00.000Z');assert.ok(o.selectionId.startsWith('dynamic:'));
  assert.equal(publishedOffers(p,'unrelated',instant).length,0);
 }
 const escaped=dynamicPublication();escaped.dates[0].startTimes[0].courses[0].registrationUrl=escaped.dates[0].startTimes[0].courses[0].registrationUrl.replaceAll('&','&amp;');
 assert.equal(publishedOffers(escaped,'209806',instant).length,1);
});
test('dynamic publication rejects changed URL tuple, room, expired lease, inconsistent bounds and DST ambiguity',()=>{
 const instant=Date.parse(selectorFixture.generatedAt);
 for(const mutate of [o=>o.registrationUrl=o.registrationUrl.replace('12%3A00','1%3A00'),o=>o.appointmentDayId=1,
  o=>o.resource=':: Wilmington; Shipyard Blvd - C',o=>o.occupiedUntil='2026-10-23T02:00:00-04:00',
  o=>o.validUntil=new Date(instant-1).toISOString(),o=>o.registrationUrl=o.registrationUrl.replace('https:','http:')]) {
  const p=dynamicPublication();mutate(p.dates[0].startTimes[0].courses[0]);assert.deepEqual(publishedOffers(p,'209806',instant),[]);
 }
 const p=dynamicPublication();p.dates[0].date='2026-11-01';p.dates[0].startTimes[0].startTime='01:30';
 p.dates[0].startTimes[0].courses[0].registrationUrl=p.dates[0].startTimes[0].courses[0].registrationUrl.replace('12%3A00%20AM','1%3A30%20AM');
 assert.deepEqual(publishedOffers(p,'209806',instant),[]);
});
test('dynamic context only reads; confirm sends the exact freshly revalidated server offer and replay needs no feed',async()=>{
 const originalFetch=globalThis.fetch, calls=[];let confirmed=false;
 const currentTime=Date.now(),publication=dynamicPublication('209806',currentTime);
 const [offer]=publishedOffers(publication,'209806',currentTime);
 Deno.env.get=name=>({SUPABASE_URL:'https://database.test',SUPABASE_SERVICE_ROLE_KEY:'test-only'}[name]);
 const result={sessionId:'11111111-1111-4111-8111-111111111111',selectionId:offer.selectionId,registrationId:'22222222-2222-4222-8222-222222222222'};
 globalThis.fetch=async(url,init={})=>{const path=String(url),body=init.body&&JSON.parse(init.body);calls.push({path,body});let value=[];
  if(path.endsWith('/rpc/registration_reschedule_context'))value=confirmed?{status:'confirmed',result}:{status:'pending',course:'AHA BLS Provider',courseNumber:'209806',options:[]};
  else if(path.includes('block-selector-availability'))value=publication;
  else if(path.endsWith('/rpc/registration_reschedule_dynamic_targets'))value=[{id:offer.selectionId,startsAt:offer.startsAt}];
  else if(path.endsWith('/rpc/confirm_registration_reschedule_dynamic')){confirmed=true;value=result;}
  return new Response(JSON.stringify(value),{status:200,headers:{'content-type':'application/json'}});
 };
 const request=(route,body={})=>new Request(`https://test/${route}`,{method:'POST',headers:{'x-reschedule-token':'lw_r_'+'a'.repeat(64)},body:JSON.stringify(body)});
 try {
  const context=await(await handler(request('context'))).json();assert.equal(context.options.length,1);assert.equal(context.dynamicOffers,undefined);
  assert.ok(!calls.some(c=>/confirm_|create_|materializ/.test(c.path)));
  assert.equal((await handler(request('confirm',{sessionId:offer.selectionId,p_offer:{courseNumber:'attacker'},publishedIds:['attacker']}))).status,200);
  const mutation=calls.find(c=>c.path.endsWith('/rpc/confirm_registration_reschedule_dynamic'));
  assert.deepEqual(mutation.body.p_offer,offer);
  const before=calls.filter(c=>c.path.includes('block-selector-availability')).length;
  const replay=await(await handler(request('confirm',{sessionId:offer.selectionId}))).json();assert.equal(replay.idempotentReplay,true);
  assert.equal(calls.filter(c=>c.path.includes('block-selector-availability')).length,before);
  assert.equal(calls.filter(c=>c.path.endsWith('/rpc/confirm_registration_reschedule_dynamic')).length,1);
  assert.equal((await handler(request('confirm',{sessionId:'another-offer'}))).status,409);
 }finally{globalThis.fetch=originalFetch;Deno.env.get=()=>undefined;}
});
