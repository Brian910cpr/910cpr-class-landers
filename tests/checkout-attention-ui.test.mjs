import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {checkoutAttention,ORDER_STATUS_QUERY} from '../supabase/functions/production-board/checkout-attention.mjs';
const source=readFileSync(new URL('../docs/admin/production-summary.js',import.meta.url),'utf8');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function element(){let html='';return{get innerHTML(){return html;},set innerHTML(v){html=String(v);},get textContent(){return html.replace(/<[^>]*>/g,'');},set textContent(v){html=String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');}};}
function mount({key='SYNTHETIC-OWNER',payload={},status=200,readAttention=null}={}){
 const board=element(),checkout=element(),events={},calls=[];let lock;
 const state={key,payload,status};
 const auth={get:()=>state.key,onLock:f=>lock=f,fetch:async(url,init)=>{
  calls.push({url,init});assert.ok(!init?.method||init.method==='GET');
  if(String(url).endsWith('/attention'))return readAttention?readAttention(state):Response.json(state.payload,{status:state.status});
  return Response.json({cards:[{id:'existing',title:'Existing production card',lane:'doing',run_score:2,project:'Existing',brian_override:false}]});
 }};
 vm.runInNewContext(source,{document:{getElementById:id=>id==='productionSummaryCards'?board:id==='checkoutAttentionStatus'?checkout:null},LanderWareAdminAuth:auth,window:{addEventListener:(name,fn)=>events[name]=fn},Date,String,Array,Number,Promise,Error});
 return{board,checkout,state,calls,refresh:()=>events['admin-auth-refresh'](),lock:()=>{state.key='';lock();}};
}
const row=(n,title,detail='Read-only status')=>({key:'native-code:'+n,source:'Native checkout',title,detail,action_url:'/admin/dashboard.html?session=12121212-1212-4212-8212-121212121212',secret_value:'DO-NOT-RENDER',recipient:'DO-NOT-RENDER'});
const payload=items=>({items,checkout_status:{availability:{payments:true,codes:true}}});
test('actual existing renderer consumes server status mapping distinctly while preserving production cards/navigation',async()=>{
 const now=Date.parse('2030-01-01T12:00:00Z'),uuid=n=>`12121212-1212-4212-8212-${String(n).padStart(12,'0')}`;
 const mapped=await checkoutAttention(async p=>p===ORDER_STATUS_QUERY?[{id:uuid(1),status:'held',payment_status:'paid'}]:['processing','ambiguous','accepted','rejected','cancelled'].map((state,i)=>({id:uuid(i+2),state,attempts:1,claimed_at:'2030-01-01T11:59:00Z'})),now);
 const h=mount({payload:{items:mapped.items,checkout_status:{availability:mapped.availability}}});await tick();await tick();
 for(const title of ['Payment received; registration not finalized','Code delivery queued','Code delivery outcome unknown','Code provider accepted; delivery unconfirmed','Code send rejected before acceptance','Code delivery stopped'])assert.ok(h.checkout.textContent.includes(title),title);
 assert.match(h.board.innerHTML,/Existing production card/);assert.match(h.board.innerHTML,/\/admin\/production\.html\?card=existing/);
 assert.equal((h.checkout.innerHTML.match(/class="recordRow"/g)||[]).length,6);assert.equal(h.calls.length,2);assert.ok(!/button|secret_value|DO-NOT-RENDER/.test(h.checkout.innerHTML));
});
test('absent and partial source metadata never look like an empty healthy queue; older unrelated queues stay out of this panel',async()=>{
 for(const data of [{items:[]},{checkout_status:{availability:{payments:true,codes:false}},items:[row(1,'Payment review')]},{items:[{source:'Materials',key:'material:1',title:'DO-NOT-RENDER'}]}]){
  const h=mount({payload:data});await tick();assert.match(h.checkout.textContent,/unavailable/);assert.ok(!h.checkout.textContent.includes('No checkout items'));assert.ok(!h.checkout.textContent.includes('DO-NOT-RENDER'));
 }
 const empty=mount({payload:payload([])});await tick();assert.match(empty.checkout.textContent,/No checkout items in this bounded result/);assert.match(empty.checkout.textContent,/not proof of delivery/);
 const error=mount({status:503,payload:{error:'DO-NOT-RENDER'}});await tick();assert.match(error.checkout.textContent,/Checkout status unavailable/);assert.ok(!error.checkout.textContent.includes('DO-NOT-RENDER'));
});
test('rendering escapes status text, ignores extra private fields and permits only existing local session navigation',async()=>{
 const dangerous=row(1,'<img src=x onerror=alert(1)>','<script>bad()</script>');dangerous.action_url='javascript:alert(1)';
 const h=mount({payload:payload([dangerous,row(2,'Other status')])});await tick();
 assert.match(h.checkout.innerHTML,/&lt;img/);assert.match(h.checkout.innerHTML,/&lt;script&gt;/);assert.ok(!/<img|<script|javascript:|DO-NOT-RENDER/.test(h.checkout.innerHTML));assert.equal((h.checkout.innerHTML.match(/Class details/g)||[]).length,1);
});
test('locked and unauthorized controls never render private rows; lock invalidates in-flight refreshes',async()=>{
 const locked=mount({key:''});await tick();assert.equal(locked.calls.length,0);assert.match(locked.checkout.textContent,/Unlock/);
 for(const status of [401,403]){const denied=mount({status,payload:payload([row(1,'DO-NOT-RENDER')])});await tick();assert.match(denied.checkout.textContent,/Unlock/);assert.ok(!denied.checkout.textContent.includes('DO-NOT-RENDER'));}
 let release;const h=mount({readAttention:()=>new Promise(resolve=>release=resolve)});await tick();h.lock();release(Response.json(payload([row(1,'DO-NOT-RENDER')])));await tick();assert.match(h.checkout.textContent,/Unlock/);assert.ok(!h.checkout.textContent.includes('DO-NOT-RENDER'));assert.ok(!h.board.textContent.includes('Existing production card'));
});
test('repeat refresh replaces old rows, and a late older response cannot overwrite the newest snapshot',async()=>{
 let release,n=0;const h=mount({readAttention:()=>++n===1?new Promise(resolve=>release=resolve):Response.json(payload([row(2,'Newest status')]))});await tick();
 await h.refresh();assert.match(h.checkout.textContent,/Newest status/);release(Response.json(payload([row(1,'Stale status')])));await tick();assert.ok(!h.checkout.textContent.includes('Stale status'));assert.equal((h.checkout.innerHTML.match(/class="recordRow"/g)||[]).length,1);
});
test('existing dashboard includes an accessible checkout host and versioned shared renderer without recovery controls',()=>{
 const html=readFileSync(new URL('../docs/admin/dashboard.html',import.meta.url),'utf8');assert.match(html,/id="checkoutAttentionStatus"[^>]*role="status"[^>]*aria-live="polite"/);assert.match(html,/production-summary\.js\?v=20261109-checkout1/);assert.match(html,/id="productionSummaryCards"/);
 const workflow=readFileSync(new URL('../.github/workflows/verify-skills-native-claim.yml',import.meta.url),'utf8');for(const p of ['docs/admin/production-summary.js','docs/admin/dashboard.html','tests/checkout-attention-ui.test.mjs'])assert.ok(workflow.includes("'"+p+"'"));assert.match(workflow,/--test .*tests\/checkout-attention-ui.test\.mjs/);
});

test('existing status UI consumes new recipient-bound event evidence without claiming activation or reviving stopped work',async()=>{
 const uuid=n=>`12121212-1212-4212-8212-${String(n).padStart(12,'0')}`;
 const rows=[{id:uuid(80),state:'accepted',provider_delivery_status:'delivered',actual_delivery_confirmed:true},{id:uuid(81),state:'accepted',provider_delivery_status:'bounced'},{id:uuid(82),state:'cancelled',provider_delivery_status:'delivered',actual_delivery_confirmed:true}];
 const mapped=await checkoutAttention(async p=>p===ORDER_STATUS_QUERY?[]:rows);
 const h=mount({payload:{items:mapped.items,checkout_status:{availability:mapped.availability}}});await tick();
 for(const title of ['Code email delivery confirmed by provider','Code email delivery failed','Code delivery stopped'])assert.ok(h.checkout.textContent.includes(title));
 assert.match(h.checkout.textContent,/activation and course completion are not established/);assert.ok(!/<button|SYNTHETIC-PRIVATE/.test(h.checkout.innerHTML));
});
