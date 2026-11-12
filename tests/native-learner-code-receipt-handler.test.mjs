import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nativeConfirmationHandler} from '../supabase/functions/native-checkout-confirmations/handler.mjs';
const id='11111111-1111-4111-8111-111111111111';
const url='https://fixture.invalid/functions/v1/native-checkout-confirmations/verify-receipt';
const req=(data={deliveryId:id},options={})=>new Request(options.url||url,{method:options.method||'POST',headers:{'content-type':'application/json',...options.headers},...(!['GET','HEAD'].includes(options.method)?{body:typeof data==='string'?data:JSON.stringify(data)}:{})});
function fixture({authorized=true,result={verified:true,status:'delivered',actualDeliveryConfirmed:true}}={}){
 const calls=[];
 const handler=nativeConfirmationHandler({authorized:async()=>{calls.push('auth');return authorized;},
  service:{deliver:()=>{throw Error('must_not_send');},health:()=>{throw Error('must_not_read_queue');}},
  proof:()=>{throw Error('must_not_prove');},schedulerStatus:()=>{throw Error('must_not_read_schedule');},
  verifyReceipt:async deliveryId=>{calls.push(deliveryId);return result;}});
 return {handler,calls};
}
test('owner authorization precedes verification and rejects unauthorized without a provider/DB path',async()=>{
 const f=fixture({authorized:false});const r=await f.handler(req());assert.equal(r.status,401);assert.deepEqual(f.calls,['auth']);
});
test('only exact POST route and allowed origin invoke verification',async()=>{
 for(const options of [{method:'GET'},{method:'PUT'},{url:'https://fixture.invalid/other/verify-receipt'},{headers:{origin:'https://other.invalid'}}]){
  const f=fixture();const r=await f.handler(req(undefined,options));assert.ok([403,404].includes(r.status));assert.equal(f.calls.length,0);
 }
});
test('bounded JSON accepts one delivery UUID only; no status/provider/code/lease hints',async()=>{
 const values=[{},[],null,{deliveryId:null},{deliveryId:3},{deliveryId:'wrong'},{deliveryId:[id]},...['lease','recipient','body','code','provider','providerId','status','proof','configured'].map(key=>({deliveryId:id,[key]:'untrusted'}))];
 for(const data of values){const f=fixture();assert.equal((await f.handler(req(data))).status,400);assert.deepEqual(f.calls,['auth']);}
 for(const [data,options,status] of [['{',{},400],[{deliveryId:id},{headers:{'content-type':'text/plain'}},415],[{deliveryId:id},{url:url+'?status=delivered'},400],['a'.repeat(4097),{},413]]){
  const f=fixture();assert.equal((await f.handler(req(data,options))).status,status);assert.deepEqual(f.calls,['auth']);
 }
});
test('successful verification is sanitized and cannot invoke send/proof/queue/configuration paths',async()=>{
 const f=fixture({result:{verified:true,status:'delivered',actualDeliveryConfirmed:true,recipient:'private@example.invalid',code:'PRIVATE',lease:id,providerId:'private-id',body:'SECRET'}});
 const r=await f.handler(req());assert.equal(r.status,200);assert.deepEqual(await r.json(),{receiptVerification:{verified:true,status:'delivered',actualDeliveryConfirmed:true}});assert.deepEqual(f.calls,['auth',id]);
});
test('failure/malformed results and exceptions never expose private details',async()=>{
 for(const value of [{verified:false,reason:'provider_access_denied',code:'PRIVATE'},{verified:false,reason:'PRIVATE'},{verified:true,status:'unknown',actualDeliveryConfirmed:true}]){
  const f=fixture({result:value});const r=await f.handler(req());assert.equal(r.status,409);const text=await r.text();assert.doesNotMatch(text,/PRIVATE|private@|lease/);
 }
 const h=nativeConfirmationHandler({authorized:async()=>true,verifyReceipt:async()=>{throw Error('PRIVATE');}});const r=await h(req());assert.equal(r.status,503);assert.doesNotMatch(await r.text(),/PRIVATE/);
});
test('optional action absent is explicit and index obtains bound lease server-side with bounded RPC only',async()=>{
 const h=nativeConfirmationHandler({authorized:async()=>true});assert.equal((await h(req())).status,503);
 const s=readFileSync(new URL('../supabase/functions/native-checkout-confirmations/index.ts',import.meta.url),'utf8');
 const block=s.slice(s.indexOf('const verifyBoundReceipt='),s.indexOf('const ownerHandler='));
 assert.match(block,/native_learner_code_receipt_target/);assert.match(block,/JSON.stringify\(\{p_delivery_id:deliveryId\}\)/);assert.match(block,/verifyBoundReceipt\(deliveryId,target.lease\)/);assert.match(block,/AbortSignal.timeout\(7000\)/);
 assert.doesNotMatch(block,/\.send\(|\.deliver\(|console\.|proven\s*=|configured\s*=/);
});
