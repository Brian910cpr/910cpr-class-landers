import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {stripTypeScriptTypes} from 'node:module';
import {readFileSync} from 'node:fs';
import {checkoutAttention,ORDER_STATUS_QUERY,CODE_STATUS_QUERY,SKILLS_PAYMENT_QUERY} from '../supabase/functions/production-board/checkout-attention.mjs';
const now=Date.parse('2030-01-01T12:00:00Z'),id=n=>`12121212-1212-4212-8212-${String(n).padStart(12,'0')}`;
const code=(n,state,extra={})=>({id:id(n),state,attempts:1,claimed_at:'2030-01-01T11:59:00Z',student:{order_id:id(100+n),registration:{class_session_id:id(200+n)}},...extra});
test('read-only adapter distinguishes observed payment/finalization and queued/accepted/unknown/rejected/terminal code outcomes without secrets',async()=>{
 const orders=[{id:id(1),status:'checkout_open',payment_status:'paid',created_at:'2030-01-01T11:55:00Z',class_session_id:id(5),email:'DO-NOT-EXPOSE',reconciliation_error:'DO-NOT-EXPOSE'},
 {id:id(2),status:'expired',payment_status:'unpaid',reconciliation_error:'DO-NOT-EXPOSE'},
 {id:id(3),status:'held',payment_status:'unpaid'}];
 const codes=[code(10,'processing'),code(11,'processing',{prepared_at:'2030-01-01T11:59:01Z'}),code(12,'processing',{claimed_at:'2030-01-01T11:50:00Z'}),code(13,'accepted',{provider_id:'DO-NOT-EXPOSE'}),code(14,'ambiguous'),code(15,'rejected'),code(16,'rejected',{attempts:5}),code(17,'cancelled'),code(18,'cancelled',{prepared_at:'2030-01-01T11:58:00Z'}),code(19,'cancelled',{provider_id:'DO-NOT-EXPOSE'})];
 for(const c of codes)Object.assign(c,{secret_value:'DO-NOT-EXPOSE',recipient:'DO-NOT-EXPOSE'});
 const calls=[],r=await checkoutAttention(async p=>(calls.push(p),p===ORDER_STATUS_QUERY?orders:p===CODE_STATUS_QUERY?codes:[]),now);
 assert.equal(r.items.length,12);assert.equal(r.availability.payments,true);assert.equal(r.availability.codes,true);
 assert.equal(r.items.find(x=>x.key==='native-payment:'+id(1)).title,'Payment received; registration not finalized');
 assert.match(r.items.find(x=>x.key==='native-payment:'+id(2)).detail,/payment not confirmed/);
 assert.equal(r.items.find(x=>x.key==='native-code:'+id(12)).severity,'critical');
 assert.equal(r.items.find(x=>x.key==='native-code:'+id(13)).title,'Code provider accepted; delivery unconfirmed');
 assert.match(r.items.find(x=>x.key==='native-code:'+id(18)).detail,/after private preparation/);
 assert.equal(r.items.find(x=>x.key==='native-code:'+id(16)).severity,'critical');
 assert.equal(JSON.stringify(r).includes('DO-NOT-EXPOSE'),false);
 assert.equal(calls.length,3);for(const p of calls){assert.ok(!/secret_value|recipient|email|payer|token|stripe_checkout/.test(p));assert.match(p,/limit=100/);}
 assert.equal(r.items[0].action_url,'/admin/dashboard.html?session='+id(5));
});
test('unavailable migration/source is visible and cannot masquerade as an empty healthy queue',async()=>{
 const r=await checkoutAttention(async p=>{if(p===CODE_STATUS_QUERY)throw Error('DO-NOT-EXPOSE');return[];},now);
 assert.deepEqual(r.availability,{payments:true,codes:false,legacySkills:true});assert.equal(r.items.length,1);assert.match(r.items[0].detail,/not evidence of an empty queue/);assert.equal(JSON.stringify(r).includes('DO-NOT-EXPOSE'),false);
 assert.deepEqual((await checkoutAttention(async()=>[],now)).items,[]);
});
function adapter(allowed=true,unavailable=false){
 let handler;const calls=[];
 const source=readFileSync(new URL('../supabase/functions/production-board/index.ts',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'');
 const context=vm.createContext({checkoutAttention,authorized:async()=>allowed,Deno:{env:{get:k=>({SUPABASE_URL:'https://fixture.invalid',SUPABASE_SERVICE_ROLE_KEY:'SYNTHETIC-SERVER-KEY'})[k]},serve:h=>handler=h},Request,Response,Headers,URL,Date,Error,JSON,Object,Array,String,Number,Math,Promise,Set,console,
 fetch:async(url,init)=>{calls.push({url,init});assert.equal(init?.method,undefined,'status route must not mutate');if(String(url).includes('native_code_delivery_history?'))return unavailable?Response.json({message:'DO-NOT-EXPOSE'},{status:404}):Response.json([code(20,'ambiguous')]);if(String(url).includes('landerware_public_orders?'))return Response.json([{id:id(4),status:'held',payment_status:'paid',class_session_id:id(9)}]);return Response.json([]);}});
 vm.runInContext(stripTypeScriptTypes(source),context);return{calls,send:(method='GET')=>handler(new Request('https://fixture.invalid/production-board/attention',{method}))};
}
test('actual existing staff endpoint authenticates before any reads and merges native statuses into its established attention response',async()=>{
 const denied=adapter(false);assert.equal((await denied.send()).status,401);assert.equal(denied.calls.length,0);
 const h=adapter(),r=await h.send(),body=await r.json();assert.equal(r.status,200);assert.equal(body.summary.critical,2);assert.equal(body.checkout_status.availability.codes,true);assert.equal(body.items.length,2);assert.equal(JSON.stringify(body).includes('SYNTHETIC-SERVER-KEY'),false);
 const missing=adapter(true,true),partial=await(await missing.send()).json();assert.equal(partial.checkout_status.availability.codes,false);assert.ok(partial.items.some(x=>x.title==='Checkout status unavailable'));assert.equal(JSON.stringify(partial).includes('DO-NOT-EXPOSE'),false);
 const wrongMethod=adapter();assert.equal((await wrongMethod.send('DELETE')).status,404);assert.equal(wrongMethod.calls.length,0);
});

test('recipient-bound provider events are distinct from acceptance, deferment, failure and terminal state',async()=>{
 const rows=[code(30,'accepted',{provider_delivery_status:'delivered',actual_delivery_confirmed:true}),code(31,'accepted',{provider_delivery_status:'deferred'}),code(32,'accepted',{provider_delivery_status:'bounced'}),code(33,'accepted',{provider_delivery_status:'complained'}),code(34,'cancelled',{provider_delivery_status:'delivered',actual_delivery_confirmed:true}),code(35,'accepted',{provider_delivery_status:'delivered',actual_delivery_confirmed:false})];
 const r=await checkoutAttention(async p=>p===CODE_STATUS_QUERY?rows:[],now);
 assert.equal(r.items[0].title,'Code email delivery confirmed by provider');assert.match(r.items[0].detail,/activation and course completion are not established/);
 assert.equal(r.items[1].title,'Code email delivery deferred');assert.equal(r.items[2].severity,'critical');assert.equal(r.items[3].title,'Code email complaint recorded');assert.equal(r.items[4].title,'Code delivery stopped');assert.equal(r.items[5].title,'Code provider accepted; delivery unconfirmed');
});

 test('historical skills payment review is bounded, private, deduplicated by order and never hides source failure',async()=>{
 const row={id:id(70),status:'canceled',skills_payment_received_at:'2030-01-01T11:00:00Z',skills_payment_review_reason:'PRIVATE-REASON',registration:{class_session_id:id(80)},stripe_payment_intent_id:'PRIVATE-INTENT'};
 const result=await checkoutAttention(async p=>p===SKILLS_PAYMENT_QUERY?[row]:[],now);assert.equal(result.items.length,1);assert.equal(result.items[0].key,'legacy-skills-payment:'+row.id);assert.equal(result.items[0].severity,'critical');assert.match(result.items[0].detail,/not restored/);assert.doesNotMatch(JSON.stringify(result),/PRIVATE/);
 assert.equal((await checkoutAttention(async p=>p===SKILLS_PAYMENT_QUERY?[{...row,status:'refunded'}]:[],now)).items.length,0);
 const unavailable=await checkoutAttention(async p=>{if(p===SKILLS_PAYMENT_QUERY)throw Error('PRIVATE');return[];},now);assert.equal(unavailable.availability.legacySkills,false);assert.equal(unavailable.items.length,1);assert.match(unavailable.items[0].detail,/not evidence of an empty queue/);
});
