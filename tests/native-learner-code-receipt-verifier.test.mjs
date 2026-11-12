import test from 'node:test';import assert from 'node:assert/strict';
import {nativeLearnerCodeReceiptVerifier} from '../supabase/functions/_shared/native-learner-code-receipt-verifier.mjs';
import {sendNativeLearnerCode} from '../supabase/functions/_shared/native-resend-adapter.mjs';
const id='11111111-1111-4111-8111-111111111111',lease='22222222-2222-4222-8222-222222222222';
const prepared={deliveryId:id,lease,provider:'resend',providerId:'bound_receipt',recipient:'fixture@example.invalid',product:'aha-25-3553-heartcode-bls-online',code:'SYNTHETIC-PRIVATE-CODE',preparedAt:'2026-11-12T10:00:00Z'};
const text=`Your purchased online course access code is ready.\n\nProduct: ${prepared.product}\nCode: ${prepared.code}\n\nKeep this code private. Complete the online course before your skills session. For help, reply to this email or call 910-395-5193.`;
const response=()=>({object:'email',id:prepared.providerId,to:[prepared.recipient],from:'910CPR <fixture@example.invalid>',created_at:'2026-11-12 10:00:01.123+00',subject:'Your purchased online course access',text,html:null,cc:[],bcc:[],last_event:'delivered'});
function fixture({context=prepared,email=response(),fetcher,settler}={}){
 const requests=[],calls=[];let settlements=0;
 const verify=nativeLearnerCodeReceiptVerifier({env:()=> 'SYNTHETIC-KEY',now:()=>Date.parse('2026-11-12T10:01:00Z'),
  request:async(u,o)=>{requests.push({u,o});return fetcher?fetcher(u,o):Response.json(email);},
  rpc:async(n,a)=>{calls.push({n,a});if(n==='native_learner_code_receipt_context')return context;settlements++;return settler?settler(a,settlements):{verified:true,status:email.last_event,actualDeliveryConfirmed:email.last_event==='delivered'};}});
 return {verify,requests,calls,get settlements(){return settlements;}};
}
test('known receipt is GET-only and exact fixed sender content matches current adapter; result contains no private data',async()=>{
 const f=fixture();assert.deepEqual(await f.verify(id,lease),{verified:true,status:'delivered',actualDeliveryConfirmed:true});
 assert.equal(f.requests.length,1);assert.equal(f.requests[0].u,'https://api.resend.com/emails/bound_receipt');assert.equal(f.requests[0].o.method,'GET');assert.equal(f.requests[0].o.redirect,'error');assert.equal(f.requests[0].o.body,undefined);
 const args=f.calls.at(-1).a;assert.match(args.p_code_sha256,/^[a-f0-9]{64}$/);assert.equal(args.p_recipient,prepared.recipient);assert.equal(args.p_lease,lease);assert.equal(args.p_provider_created_at,'2026-11-12 10:00:01.123+00');
 let payload;await sendNativeLearnerCode(prepared,{apiKey:'SYNTHETIC',from:'fixture@example.invalid',request:async(_u,o)=>{payload=JSON.parse(o.body);return Response.json({id:'synthetic'});}});assert.equal(payload.text,text);assert.equal(payload.subject,response().subject);
 assert.doesNotMatch(JSON.stringify(await f.verify(id,lease)),/PRIVATE|fixture@|bound_receipt|11111111|SYNTHETIC/);
});
test('unknown receipt, wrong lease/provider or malformed context cannot reach provider',async()=>{
 for(const context of [{blocked:true,reason:'PRIVATE'}, {...prepared,providerId:null},{...prepared,lease:id},{...prepared,provider:'cloudflare'},{...prepared,recipient:'Fixture@example.invalid'},{...prepared,code:'bad\ncode'}]){
 const f=fixture({context});assert.equal((await f.verify(id,lease)).verified,false);assert.equal(f.requests.length,0);assert.equal(f.settlements,0);}
 const f=fixture();assert.equal((await f.verify(id,null)).reason,'invalid_request');assert.equal(f.calls.length,0);
});
test('same-recipient different receipt/body/code, extra recipients or copies cannot reconcile',async()=>{
 for(const patch of [{id:'other_receipt'},{text:text.replace('PRIVATE','OTHER')},{subject:'Other'},{to:['other@example.invalid']},{to:[prepared.recipient,prepared.recipient]},{cc:['copy@example.invalid']},{bcc:['copy@example.invalid']},{object:'received_email'},{text:null}]){
 const f=fixture({email:{...response(),...patch}});assert.equal((await f.verify(id,lease)).reason,'receipt_mismatch');assert.equal(f.settlements,0);}
});
test('time and undocumented status fail closed; opened/clicked never imply delivered locally',async()=>{
 for(const created_at of ['invalid','2026-11-12T09:59:59Z','2026-11-12T11:00:00Z']){const f=fixture({email:{...response(),created_at}});assert.equal((await f.verify(id,lease)).reason,'receipt_time_invalid');assert.equal(f.settlements,0);}
 const bad=fixture({email:{...response(),last_event:'accepted'}});assert.equal((await bad.verify(id,lease)).reason,'provider_status_unverified');
 for(const last_event of ['sent','opened','clicked','bounced','failed','complained','suppressed','delivery_delayed']){const f=fixture({email:{...response(),last_event}});assert.deepEqual(await f.verify(id,lease),{verified:true,status:last_event,actualDeliveryConfirmed:false});}
});
test('provider errors and oversized/malformed JSON are sanitized and never recorded',async()=>{
 for(const [fetcher,reason] of [[()=>new Response('PRIVATE',{status:403}),'provider_access_denied'],[()=>new Response('PRIVATE',{status:404}),'receipt_not_found'],[()=>{throw Error('PRIVATE')},'provider_unavailable'],[()=>new Response('x'.repeat(65537)),'provider_response_invalid'],[()=>new Response('{'),'provider_response_invalid']]){
 const f=fixture({fetcher});assert.deepEqual(await f.verify(id,lease),{verified:false,reason});assert.equal(f.settlements,0);assert.equal(f.requests.length,1);}
});
test('uncertain persistence retries only identical evidence; assignment drift does not retry or expose data',async()=>{
 const f=fixture({settler:(_a,n)=>{if(n===1)throw Error('PRIVATE');return {verified:true,status:'delivered',actualDeliveryConfirmed:true};}});assert.equal((await f.verify(id,lease)).verified,true);assert.equal(f.requests.length,1);assert.deepEqual(f.calls.at(-1).a,f.calls.at(-2).a);
 const drift=fixture({settler:()=>({blocked:true})});assert.deepEqual(await drift.verify(id,lease),{verified:false,reason:'assignment_changed'});assert.equal(drift.settlements,1);
 const broken=fixture({settler:()=>{throw Error('PRIVATE')}});assert.deepEqual(await broken.verify(id,lease),{verified:false,reason:'reconciliation_unknown'});assert.equal(broken.settlements,2);assert.equal(broken.requests.length,1);
});
