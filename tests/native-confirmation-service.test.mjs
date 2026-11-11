import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeConfirmationService} from '../supabase/functions/_shared/native-confirmation-service.mjs';
import {nativeConfirmationHandler} from '../supabase/functions/native-checkout-confirmations/handler.mjs';
const id='11111111-1111-4111-8111-111111111111',lease='22222222-2222-4222-8222-222222222222';
const job={messageId:id,lease,recipient:'brian@910cpr.com',subject:'Synthetic owner fulfillment',body:'Synthetic local test. No actual request sent.',customerTemplate:false,confirmation:null};
const request=(path='retry',data={},headers={})=>new Request('https://fixture.invalid/native-checkout-confirmations/'+path,{method:path==='status'?'GET':'POST',headers:{'content-type':'application/json',...headers},...(path==='status'?{}:{body:JSON.stringify(data)})});
test('missing server mail configuration never claims or sends',async()=>{
 const svc=nativeConfirmationService({rpc:()=>{throw Error('must not claim');},env:()=>undefined,request:()=>{throw Error('must not send');}});
 assert.equal(svc.configured(),false);assert.equal((await svc.deliver()).configured,false);
});
test('disabled queue never calls transport',async()=>{
 let calls=0;const svc=nativeConfirmationService({rpc:async name=>{assert.equal(name,'native_checkout_claim_confirmation');calls++;return {disabled:true};},env:()=> 'fixture',request:()=>{throw Error('must not send');}});
 assert.equal((await svc.deliver()).disabled,true);assert.equal(calls,1);
});
test('uncertain settlement retries the same receipt once without a second provider call',async()=>{
 let claims=0,settles=0,sends=0;const seen=[];
 const svc=nativeConfirmationService({rpc:async(name,args)=>{if(name==='native_checkout_claim_confirmation'){claims++;return job;}seen.push(args);if(++settles===1)throw Error('lost response');return {replay:true};},env:key=>key==='RESEND_API_KEY'?'fixture':undefined,request:async()=>{sends++;return Response.json({id:'fixture_receipt'});}});
 const r=await svc.deliver();assert.equal(r.accepted,1);assert.equal(r.stopped,null);assert.equal(r.pendingSettlement,undefined);assert.equal(claims,1);assert.equal(sends,1);assert.equal(settles,2);assert.deepEqual(seen[0],seen[1]);
});
test('unresolved settlement preserves a private receipt and exposes no lease in result',async()=>{
 let sends=0;const reports=[];const svc=nativeConfirmationService({rpc:async name=>{if(name==='native_checkout_claim_confirmation')return job;throw Error('unknown');},env:key=>key==='RESEND_API_KEY'?'fixture':undefined,request:async()=>{sends++;return Response.json({id:'fixture_receipt'});},report:r=>reports.push(r)});
 const r=await svc.deliver();assert.equal(r.stopped,'settlement_unknown');assert.equal(r.accepted,0);assert.equal(sends,1);assert.equal(reports[0].p_provider_id,'fixture_receipt');assert.equal(reports[0].p_lease,lease);assert.equal(r.pendingSettlement,undefined);assert.doesNotMatch(JSON.stringify(r),/fixture_receipt|brian@|22222222/);
});
test('HTTP owner authorization precedes all health, queue and transport access',async()=>{
 let called=false;const h=nativeConfirmationHandler({authorized:async()=>false,service:{health:()=>{called=true},deliver:()=>{called=true},configured:()=>{called=true}}});
 for(const p of ['status','retry'])assert.equal((await h(request(p))).status,401);assert.equal(called,false);
});
test('HTTP request cannot pick recipient, body, sender, provider or oversized fields',async()=>{
 let calls=0;const h=nativeConfirmationHandler({authorized:async()=>true,service:{deliver:()=>calls++,health:()=>calls++}});
 for(const data of [{recipient:'other@example.test'},{body:'untrusted'},{from:'other@example.test'},{provider:'other'},{orderId:'invalid'},{orderId:[]},[]])assert.equal((await h(request('retry',data))).status,400);
 assert.equal((await h(request('retry',{body:'a'.repeat(5000)}))).status,413);assert.equal(calls,0);
});
test('HTTP origin rejection and auth failures expose no raw exceptions',async()=>{
 const h=nativeConfirmationHandler({authorized:async()=>{throw Error('secret diagnostic');},service:{}});
 assert.equal((await h(request('retry',{}, {origin:'https://evil.invalid'}))).status,403);
 const r=await h(request());assert.equal(r.status,503);assert.doesNotMatch(await r.text(),/secret diagnostic/);
});
test('owner retry reports unhealthy or disabled explicitly and accepts only an order scope',async()=>{
 let passed;const service={configured:()=>true,deliver:async o=>{passed=o;return {configured:true,disabled:true,accepted:0,actualDeliveryConfirmed:false};},health:async()=>({healthy:false,disabled:true})};
 const h=nativeConfirmationHandler({authorized:async()=>true,service});const r=await h(request('retry',{orderId:id}));assert.equal(r.status,503);assert.equal(passed,id);assert.equal((await r.json()).delivery.actualDeliveryConfirmed,false);
 const status=await h(request('status'));assert.equal(status.status,200);assert.deepEqual(await status.json(),{configured:true,health:{healthy:false,disabled:true}});
});
