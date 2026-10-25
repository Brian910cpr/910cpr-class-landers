import test from 'node:test';
import assert from 'node:assert/strict';
import worker,{dispatch} from '../worker/checkout-confirmation.mjs';
const token='local-test-token-that-is-long-enough-only';
function fixture(t,{send=async()=>({messageId:'provider-test-id'}),settleFails=false}={}){
 const calls=[],jobs=[{messageId:'message-test',lease:'lease-test',recipient:'student@example.test',subject:'Test class',body:'Synthetic confirmation'}];
 t.mock.method(globalThis,'fetch',async(url,opts)=>{
   const args=JSON.parse(opts.body);calls.push({url,args});assert.equal(args.p_token,token);
   if(url.endsWith('/landerware_prepare_checkout_reminders'))return Response.json({scheduled:0,suppressed:0});
   if(url.endsWith('/landerware_claim_checkout_confirmation'))return Response.json(jobs.shift()||{empty:true});
   if(url.endsWith('/landerware_settle_checkout_confirmation')){if(settleFails)return new Response('',{status:503});return Response.json({settled:true})}
   if(url.endsWith('/landerware_checkout_confirmation_health'))return Response.json({healthy:false,observerFresh:false});
   throw Error('unexpected endpoint');
 });
 return{calls,jobs,env:{SUPABASE_URL:'https://database.example.test',SUPABASE_PUBLISHABLE_KEY:'public-test',CHECKOUT_DELIVERY_TOKEN:token,FROM_EMAIL:'sender@example.test',EMAIL:{send}}};
}
test('customer delivery renders canonical HTML and text instead of the legacy body or internal IDs',async t=>{
 const sent=[];const h=fixture(t,{send:async m=>{sent.push(m);return {messageId:'provider-test-id'}}});
 h.jobs[0].body='Order: internal-private-id';h.jobs[0].customerTemplate=true;
 h.jobs[0].confirmation={firstName:'Synthetic',course:'BLS Renewal',courseId:'359474',startsAt:'2026-10-24T14:00:00Z',endsAt:'2026-10-24T16:00:00Z',venue:'Recorded venue',address:'Recorded address',selectedOptions:[]};
 await dispatch(h.env);assert.match(sent[0].html,/Get directions/);assert.match(sent[0].text,/10:00 AM/);assert.doesNotMatch(sent[0].text+sent[0].html,/internal-private-id/);
});
test('missing authoritative customer data fails closed without sending the legacy template',async t=>{
 let sends=0;const h=fixture(t,{send:async()=>{sends++;return {messageId:'test'}}});h.jobs[0].customerTemplate=true;
 await assert.rejects(dispatch(h.env),/confirmation_class_data_missing/);assert.equal(sends,0);
});
test('records provider acceptance and one send for the claimed message',async t=>{
 const sent=[];const h=fixture(t,{send:async m=>{sent.push(m);return{messageId:'provider-test-id'}}});
 assert.deepEqual(await dispatch(h.env),{sent:1,failed:0});assert.equal(sent.length,1);
 assert.equal(h.calls[2].args.p_outcome,'sent');assert.equal(h.calls[2].args.p_provider_id,'provider-test-id');
});
test('explicit provider rejection is recorded without inventing acceptance',async t=>{
 const h=fixture(t,{send:async()=>{throw Object.assign(Error('rejected'),{code:'E_SENDER_NOT_VERIFIED'})}});
 assert.deepEqual(await dispatch(h.env),{sent:0,failed:1});assert.equal(h.calls[2].args.p_outcome,'rejected');
});
test('timeout or unknown send result is ambiguous and cannot be blindly retried',async t=>{
 const h=fixture(t,{send:async()=>{throw Error('timeout')}});await dispatch(h.env);
 assert.equal(h.calls[2].args.p_outcome,'ambiguous');assert.equal(h.calls[2].args.p_error,'provider_result_unknown');
});
test('missing receipt never marks a message sent',async t=>{
 const h=fixture(t,{send:async()=>({})});await dispatch(h.env);assert.equal(h.calls[2].args.p_outcome,'ambiguous');
});
test('acceptance record failure does not run another send or record a rejection',async t=>{
 let sends=0;const h=fixture(t,{send:async()=>{sends++;return{messageId:'provider-id'}},settleFails:true});
 await assert.rejects(dispatch(h.env),/delivery_database_503/);assert.equal(sends,1);assert.equal(h.calls.length,3);
});
test('public health exposes no queue details; protected endpoints reject strangers',async t=>{
 const h=fixture(t);const health=await worker.fetch(new Request('https://worker.example/health'),h.env);
 assert.deepEqual(Object.keys(await health.json()),['build']);
 const denied=await worker.fetch(new Request('https://worker.example/run',{method:'POST'}),h.env);assert.equal(denied.status,401);assert.equal(h.calls.length,0);
});
test('authenticated observer reads canonical queue health',async t=>{
 const h=fixture(t);const r=await worker.fetch(new Request('https://worker.example/status',{headers:{authorization:'Bearer '+token}}),h.env);
 assert.equal(r.status,200);assert.equal((await r.json()).healthy,false);
});

test('delivery events are acknowledged only after durable recording; failures retry',async t=>{
 const calls=[];t.mock.method(globalThis,'fetch',async(url,opts)=>{calls.push({url,args:JSON.parse(opts.body)});return calls.length===1?Response.json({recorded:true}):new Response('',{status:503})});
 let ack=0,retry=0;const env={SUPABASE_URL:'https://database.example.test',SUPABASE_PUBLISHABLE_KEY:'test',CHECKOUT_DELIVERY_TOKEN:token};
 await worker.queue({messages:[1,2].map(n=>({body:{synthetic:n},ack(){ack++},retry(){retry++}}))},env);
 assert.equal(ack,1);assert.equal(retry,1);assert.ok(calls.every(c=>c.url.endsWith('/landerware_record_email_delivery_event')));
 assert.equal(calls[0].args.p_token,token);
});
