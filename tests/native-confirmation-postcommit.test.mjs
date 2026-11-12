import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeConfirmationService} from '../supabase/functions/_shared/native-confirmation-service.mjs';
import {nativeConfirmationPostcommit} from '../supabase/functions/_shared/native-confirmation-postcommit.mjs';
const id='11111111-1111-4111-8111-111111111111';
test('supported background runtime registers one promise without blocking the committed response',async()=>{
 let finish,done=false;const pending=new Promise(r=>finish=r),registered=[];
 const hook=nativeConfirmationPostcommit({service:{configured:()=>true,deliver:async value=>{assert.equal(value,id);await pending;done=true;return {accepted:1};}},waitUntil:p=>registered.push(p)});
 await hook(id);assert.equal(registered.length,1);assert.equal(done,false);finish();await registered[0];assert.equal(done,true);
});
test('fallback awaits the same work once when background registration fails',async()=>{
 let count=0;const logs=[];const hook=nativeConfirmationPostcommit({service:{configured:()=>true,deliver:async()=>{count++;return {accepted:1};}},waitUntil:()=>{throw Error('runtime unavailable');},report:x=>logs.push(x)});
 await hook(id);assert.equal(count,1);assert.equal(logs[0].event,'native_confirmation_background_unavailable');
});
test('missing mail configuration and malformed order scopes make no provider or queue request',async()=>{
 let count=0;const hook=nativeConfirmationPostcommit({service:{configured:()=>false,deliver:()=>count++}});
 for(const value of [null,undefined,'',{},[id],id])await hook(value);assert.equal(count,0);
});
test('delivery failures are sanitized and never throw into the committed registration',async()=>{
 const logs=[];const hook=nativeConfirmationPostcommit({service:{configured:()=>true,deliver:async()=>{throw Error('PRIVATE secret recipient@example.test');}},report:x=>logs.push(x)});
 await hook(id);assert.deepEqual(logs,[{event:'native_confirmation_postcommit_failed',orderId:id}]);assert.doesNotMatch(JSON.stringify(logs),/PRIVATE|recipient/);
});
test('uncertain delivery is reported without tokens, recipient or raw reason',async()=>{
 const logs=[];const hook=nativeConfirmationPostcommit({service:{configured:()=>true,deliver:async()=>({accepted:0,ambiguous:1,stopped:'secret diagnostic',pendingSettlement:{token:'secret'}})},report:x=>logs.push(x)});
 await hook(id);assert.equal(logs[0].reason,'delivery_failure');assert.equal(logs[0].ambiguous,1);assert.doesNotMatch(JSON.stringify(logs),/secret|token/);
});
test('even broken logging cannot turn committed registration into an error',async()=>{
 const hook=nativeConfirmationPostcommit({service:{configured:()=>true,deliver:async()=>{throw Error('fail');}},report:()=>{throw Error('log failed');}});await hook(id);
});

test('ten-student plus owner notice drains a second bounded batch for the same order',async()=>{
 const scopes=[],logs=[];const hook=nativeConfirmationPostcommit({service:{configured:()=>true,deliver:async scope=>{scopes.push(scope);return scopes.length===1?{claimed:10,accepted:10,limitReached:true}:{claimed:1,accepted:1,empty:true,limitReached:false};}},report:x=>logs.push(x)});
 await hook(id);assert.deepEqual(scopes,[id,id]);assert.equal(logs.length,0);
});
test('two-batch maximum reports remaining work instead of silently leaving it or draining unboundedly',async()=>{
 let calls=0;const logs=[];const hook=nativeConfirmationPostcommit({service:{configured:()=>true,deliver:async()=>{calls++;return {claimed:10,accepted:10,limitReached:true};}},report:x=>logs.push(x)});
 await hook(id);assert.equal(calls,2);assert.equal(logs[0].reason,'batch_limit_reached');
});

test('a recovered settlement continues the same order without resending the accepted message',async()=>{
 let next=0,sends=0,settles=0;const ids=[1,2,3].map(n=>`00000000-0000-4000-8000-${String(n).padStart(12,'0')}`),logs=[];
 const service=nativeConfirmationService({env:k=>k==='RESEND_API_KEY'?'fixture':undefined,request:async()=>{sends++;return Response.json({id:'fixture_receipt_'+sends});},rpc:async(name,args)=>{
  if(name==='native_mail_next_lane')return {lane:'confirmation'};
  if(name==='native_checkout_claim_confirmation'){assert.equal(args.p_order_id,id);return next<ids.length?{messageId:ids[next++],lease:'22222222-2222-4222-8222-222222222222',recipient:'brian@910cpr.com',customerTemplate:false,confirmation:null,subject:'Fixture fulfillment',body:'Synthetic local fixture only.'}:{empty:true};}
  if(name==='native_checkout_settle_confirmation'){if(++settles===1)throw Error('transient unknown settlement');return{settled:true};}
  throw Error('unexpected RPC');
 }});
 await nativeConfirmationPostcommit({service,report:r=>logs.push(r)})(id);
 assert.equal(sends,3);assert.equal(next,3);assert.equal(settles,4);assert.equal(logs.length,0);
});
