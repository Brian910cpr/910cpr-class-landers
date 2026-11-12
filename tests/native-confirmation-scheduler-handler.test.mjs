import test from 'node:test';import assert from 'node:assert/strict';
import {nativeScheduledHandler,tokenHash} from '../supabase/functions/native-checkout-confirmations/scheduled.mjs';
const id='11111111-1111-4111-8111-111111111111',token='a'.repeat(64);
const req=(body={},opts={})=>new Request('https://fixture.invalid/functions/v1/native-checkout-confirmations/scheduled'+(opts.query||''),{method:opts.method||'POST',headers:{'content-type':'application/json',authorization:'Bearer '+token,'x-native-scheduler-run':id,...opts.headers},...(opts.method==='GET'?{}:{body:JSON.stringify(body)})});
const good={configured:true,claimed:0,accepted:0,rejected:0,ambiguous:0,stopped:null,empty:true};
function setup({admission={authorized:true,started:true},result=good,finish,deliver}={}){let calls=[],sends=0;const h=nativeScheduledHandler({rpc:async(name,args)=>{calls.push({name,args});if(name.endsWith('_begin'))return admission;return finish?finish(args):{settled:true};},service:{deliver:async(order,options)=>{assert.equal(order,null);assert.deepEqual(options,{limit:1});sends++;return deliver?deliver():result;}}});return {h,calls,get sends(){return sends;}};}
test('strict callback rejects selectors, origin, query, media, malformed credentials before RPC',async()=>{const f=setup();for(const b of [{orderId:id},{recipient:'x'},[],null,{constructor:'x'}])assert.equal((await f.h(req(b))).status,400);assert.equal((await f.h(req({}, {query:'?orderId=x'}))).status,400);assert.equal((await f.h(req({}, {headers:{origin:'https://www.910cpr.com'}}))).status,403);assert.equal((await f.h(req({}, {headers:{'content-type':'text/plain'}}))).status,400);for(const headers of [{authorization:'bad'},{authorization:'Bearer bad'},{authorization:'bearer '+token},{authorization:'Bearer '+token+' extra'},{'x-native-scheduler-token':token},{'x-native-scheduler-run':'bad'}])assert.equal((await f.h(req({}, {headers}))).status,401);assert.equal(f.calls.length,0);});
test('GET and wrong path have no side effect',async()=>{const f=setup();assert.equal((await f.h(req({}, {method:'GET'}))).status,404);assert.equal((await f.h(new Request('https://x/evil/scheduled',{method:'POST'}))).status,404);assert.equal(f.calls.length,0);});
test('hash-only service RPC and bounded null-order service, response excludes all receipts',async()=>{const f=setup();const r=await f.h(req());assert.equal(r.status,200);assert.equal(f.sends,1);assert.deepEqual(f.calls[0],{name:'native_checkout_scheduler_begin',args:{p_run_id:id,p_token_hash:await tokenHash(token)}});assert.notEqual(f.calls[0].args.p_token_hash,token);assert.deepEqual(await r.json(),{state:'completed',actualDeliveryConfirmed:false});});
test('disabled, duplicate and unauthorized run never deliver',async()=>{for(const admission of [{authorized:false},{authorized:true,disabled:true},{authorized:true,started:false}]){const f=setup({admission});assert.ok((await f.h(req())).status>=400);assert.equal(f.sends,0);assert.equal(f.calls.length,1);}});
test('customer lane disabled produces transport evidence with zero sends from service',async()=>{const f=setup({result:{...good,disabled:true}});assert.equal((await f.h(req())).status,200);assert.equal(f.calls[1].args.p_result.outcome,'disabled');});
test('unknown and ambiguous results retain a durable latch classification',async()=>{for(const result of [{...good,claimed:1,ambiguous:1},{...good,stopped:'settlement_unknown'},{...good,stopped:'claim_unknown'},{...good,claimed:11},{...good,claimed:1},{...good,configured:false}]){const f=setup({result});assert.equal((await f.h(req())).status,503);assert.ok(['uncertain','fault'].includes(f.calls[1].args.p_result.outcome));assert.equal(f.sends,1);}});
test('known provider rejection remains completed for SQL backoff but is not claimed delivered',async()=>{const f=setup({result:{...good,claimed:1,rejected:1}});assert.equal((await f.h(req())).status,200);assert.equal(f.calls[1].args.p_result.rejected,1);});
test('completion retries only same sanitized receipt, never provider',async()=>{let n=0;const f=setup({finish:()=>{if(++n===1)throw Error('lost');return {replay:true}}});assert.equal((await f.h(req())).status,200);assert.equal(f.sends,1);assert.deepEqual(f.calls[1],f.calls[2]);});
test('unresolved finish and thrown delivery return no raw exceptions or private receipt',async()=>{const f=setup({finish:()=>{throw Error('private')},deliver:()=>{throw Error('private')}});const r=await f.h(req());assert.equal(r.status,503);assert.equal(f.sends,1);assert.equal(f.calls.length,3);assert.doesNotMatch(await r.text(),/private|11111111|aaaa/);assert.equal(f.calls[1].args.p_result.code,'delivery_unknown');});
test('large stream body is bounded before RPC',async()=>{const f=setup();assert.equal((await f.h(req({x:'a'.repeat(100)}))).status,400);assert.equal(f.calls.length,0);});

const {nativeConfirmationHandler}=await import('../supabase/functions/native-checkout-confirmations/handler.mjs');
test('existing owner status exposes separate sanitized scheduler evidence only after owner auth',async()=>{
 let calls=0;const scheduler={enabled:false,lastCompletedAt:null,observerFresh:false,callbackFresh:false,healthy:false,actualDeliveryConfirmed:false};
 const svc={configured:()=>true,health:async()=>({healthy:true,lastPollAt:'fresh-postcommit'})};
 const statusReq=()=>new Request('https://fixture.invalid/native-checkout-confirmations/status');
 const denied=nativeConfirmationHandler({authorized:async()=>false,service:svc,schedulerStatus:async()=>{calls++;return scheduler;}});
 assert.equal((await denied(statusReq())).status,401);assert.equal(calls,0);
 const allowed=nativeConfirmationHandler({authorized:async()=>true,service:svc,schedulerStatus:async()=>{calls++;return scheduler;}});
 const r=await allowed(statusReq());assert.equal(r.status,200);assert.deepEqual(await r.json(),{configured:true,health:{healthy:true,lastPollAt:'fresh-postcommit'},scheduler});assert.equal(calls,1);
});
test('scheduler status failure is not silently converted to healthy queue-only status',async()=>{
 const h=nativeConfirmationHandler({authorized:async()=>true,service:{configured:()=>true,health:async()=>({healthy:true})},schedulerStatus:async()=>{throw Error('private');}});
 const r=await h(new Request('https://fixture.invalid/native-checkout-confirmations/status'));assert.equal(r.status,503);assert.doesNotMatch(await r.text(),/private/);
});

test('blocked code preparation completes without acceptance or rejection and remains sanitized',async()=>{
 const f=setup({result:{...good,claimed:1,blocked:1}});assert.equal((await f.h(req())).status,200);
 assert.deepEqual(f.calls[1].args.p_result,{outcome:'completed',code:null,claimed:1,accepted:0,rejected:0,ambiguous:0,blocked:1});
 for(const blocked of [-1,1.5,11,'1']){const bad=setup({result:{...good,claimed:1,blocked}});assert.equal((await bad.h(req())).status,503);}
});
