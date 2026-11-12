import test from 'node:test';
import assert from 'node:assert/strict';
import {createHandler} from '../supabase/functions/skills-session-reservation/handler.mjs';
import {skillsOffers} from '../supabase/functions/skills-session-reservation/policy.mjs';
const now=Date.parse('2026-11-06T12:00:00Z'),key='44444444-4444-4444-8444-444444444444';
const feed=()=>({schemaVersion:'selector-resolved-availability.v1',pageKey:'bls',generatedAt:new Date(now).toISOString(),validUntil:new Date(now+60000).toISOString(),dates:[{date:'2026-11-10',startTimes:[{startTime:'10:00',courses:[{courseId:'210549',offerType:'dynamic_appointment',publicSelectable:true,durationMinutes:45,schedulerConsumptionMinutes:60,cleanupBufferMinutes:15,occupiedUntil:'2026-11-10T16:00:00Z',instructor:'Fixture Instructor',resource:':: Wilmington; Shipyard Blvd - B',location:':: Wilmington; Shipyard Blvd',availabilityBlockId:'fixture',sourceSessionIds:[],validUntil:new Date(now+60000).toISOString()}]}]}]});
const request=(route,body)=>new Request('https://fixture.invalid/'+route,{method:'POST',headers:{'idempotency-key':key,'content-type':'application/json'},body:JSON.stringify({context:'bls-skills',...body})});
const student={firstName:'Fixture',lastName:'Student',email:'fixture@example.invalid',phone:'2025550100',onlineCompletionAcknowledged:true};
const order={orderId:'order',sessionId:'session',studentId:'student',total:9500,status:'held',holdExpiresAt:new Date(now+1800000).toISOString(),startsAt:'2026-11-10T15:00:00Z',location:':: Wilmington; Shipyard Blvd'};
test('bundle entry point selects a current server offer and keeps physical course 509474 while charging $95 once',async()=>{
 const calls=[],offer=skillsOffers(feed(),'bls-skills',now,'210549')[0];
 const handler=createHandler({enabled:()=>true,now:()=>now,publication:async()=>feed(),rpc:async(name,args)=>{calls.push({name,args});assert.equal(name,'reserve_bls_bundle');return args.p_offer.startsAt?order:{status:'offer_required'};}});
 const response=await handler(request('bundle-reserve',{selectionId:offer.selectionId,student,amountCents:1,startsAt:'forged'}));
 const result=await response.json();assert.equal(response.status,200);assert.equal(result.status,'held');assert.equal(result.registrationId,undefined);
 assert.equal(calls[1].args.p_offer.courseNumber,'509474');assert.equal(calls[1].args.p_offer.context,'bls-skills');assert.equal(calls[1].args.p_offer.startsAt,offer.startsAt);
});
test('unstocked bundle choices fail closed; tampered context and incomplete identity cannot reserve',async()=>{
 const handler=createHandler({enabled:()=>true,now:()=>now,publication:()=>assert.fail('no calendar needed while stock closed'),rpc:async name=>{assert.equal(name,'bls_native_bundle_ready');return false;}});
 const result=await (await handler(request('choices',{publicCourse:'210549'}))).json();assert.equal(result.amountCents,9500);assert.deepEqual(result.offers,[]);
 for(const body of [{context:'hsi-blended',student},{student:{...student,phone:''}},{student:{...student,onlineCompletionAcknowledged:false}}])assert.notEqual((await handler(request('bundle-reserve',{selectionId:'forged',...body}))).status,200);
});
test('saved bundle resumes without a feed, uploads optional evidence privately, and never reports paid from URL data',async()=>{
 let uploaded=0,provider=0;
 const handler=createHandler({enabled:()=>true,now:()=>now,publication:()=>assert.fail('saved order must not need fresh availability'),rpc:async(name)=>name==='reserve_bls_bundle'?order:order,
  uploadBundle:async(receipt,saved,file)=>{assert.equal(receipt,key);assert.equal(saved.orderId,'order');assert.equal(file.extension,'pdf');return {documentId:String(++uploaded)};},
  publicOrder:async(action,receipt,saved)=>{provider++;assert.equal(action,'checkout');assert.equal(receipt,key);assert.equal(saved.total,9500);return {checkoutUrl:'https://checkout.stripe.com/c/pay/fixture'};}});
 assert.equal((await handler(request('bundle-reserve',{selectionId:'saved',student}))).status,200);
 const status=await (await handler(request('bundle-status',{paid:true}))).json();assert.equal(status.paymentStatus,'pending');assert.equal(provider,0);assert.equal(uploaded,0);
 assert.equal((await handler(request('bundle-certificate',{certificate:{type:'application/pdf',base64:btoa('%PDF-fixture')}}))).status,200);
 assert.match((await (await handler(request('bundle-checkout',{}))).json()).checkoutUrl,/^https:\/\/checkout.stripe.com\//);assert.equal(provider,1);
});
test('expired holds cannot open payment and paid canonical receipts remain paid without another checkout',async()=>{
 for(const [status,expiry,expected] of [['held',now-1,409],['paid',now-1,200]]){
  const handler=createHandler({enabled:()=>true,now:()=>now,rpc:async()=>({...order,status,holdExpiresAt:new Date(expiry).toISOString()}),publicOrder:()=>assert.fail('must not create another payment')});
  const response=await handler(request('bundle-checkout',{}));assert.equal(response.status,expected);if(status==='paid')assert.equal((await response.json()).paymentStatus,'paid');
 }
 const review=createHandler({enabled:()=>true,now:()=>now,rpc:async()=>({...order,status:'expired',reconciliationError:'paid_inventory_unavailable'}),publicOrder:()=>assert.fail('must not charge a payment under review')});
 const response=await review(request('bundle-status',{}));assert.equal((await response.json()).error,'payment_reconciliation_required');
});
