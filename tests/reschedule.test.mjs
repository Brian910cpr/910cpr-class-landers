import test from 'node:test';
import assert from 'node:assert/strict';
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
