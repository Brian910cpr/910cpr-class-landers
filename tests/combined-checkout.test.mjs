import test from 'node:test';import assert from 'node:assert/strict';
import {nativeBasketCheckout,basketCheckoutParams,settleBasket,basketView} from '../supabase/functions/public-registration/basket.mjs';
import {participantMarkup,additionalEstimate} from '../docs/assets/checkout-course-controls.js';
const key='11111111-1111-4111-8111-111111111111';
const lines=[{courseNumber:'241108',kind:'session',primary:true,subtotalCents:22500,discountCents:0,totalCents:22500},{courseNumber:'209806',kind:'session',primary:false,subtotalCents:7500,discountCents:750,totalCents:6750},{courseNumber:'209806',kind:'ebook',subtotalCents:2000,discountCents:0,totalCents:2000}];
const basket={id:'basket',request_key:key,total:31250,currency:'usd',lines,payer_email:'synthetic@example.invalid',hold_expires_at:'2030-01-01T00:00:00Z',stripe_checkout_session_id:'cs_fixture'};
test('aggregate Stripe request is itemized with only added-session discount and one basket identity',()=>{
 const p=basketCheckoutParams(basket,'https://fixture.invalid');assert.equal(p.get('line_items[1][price_data][unit_amount]'),'6750');assert.equal(p.get('line_items[2][price_data][unit_amount]'),'2000');assert.match(p.get('line_items[1][price_data][product_data][name]'),/10%/);assert.equal(p.get('metadata[landerware_basket_id]'),'basket');assert.equal(p.get('metadata[landerware_order_id]'),null);assert.match(p.get('success_url'),/basket=/);
 for(const bad of [{...basket,total:1},{...basket,lines:lines.map(x=>x.kind==='ebook'?{...x,discountCents:1}:x)}])assert.throws(()=>basketCheckoutParams(bad,'https://fixture.invalid'),/ambiguous_price_allocation/);
});
test('verified aggregate settlement validates exact order/processor allocation and records receipt before finalization',async()=>{
 const session={id:'cs_fixture',mode:'payment',payment_status:'paid',payment_intent:'pi_fixture',amount_total:31250,currency:'usd',metadata:{landerware_basket_id:'basket'}};const calls=[],rpc=async(name,args)=>{calls.push({name,args});return {status:'paid'};};
 await settleBasket(rpc,basket,session,{actual:'verified processor fixture'});assert.deepEqual(calls.map(x=>x.name),['native_checkout_basket_record_payment','native_checkout_basket_finalize']);assert.deepEqual(calls[0].args,calls[1].args);
 for(const patch of [{id:'other'},{payment_intent:'pi_other'},{amount_total:1},{currency:'eur'},{metadata:{landerware_basket_id:'other'}},{metadata:{landerware_basket_id:'basket',landerware_order_id:'child'}},{payment_status:'unpaid'}]){const n=calls.length;await assert.rejects(settleBasket(rpc,{...basket,stripe_payment_intent_id:'pi_fixture'},{...session,...patch},{}),/payment_evidence_mismatch/);assert.equal(calls.length,n);}
});
test('basket API reuses original immutable request after lost response, avoiding offer refresh and rejecting client price fields',async()=>{
 let saved=null,preparations=0;const calls=[];const raw={basketId:'basket',status:'held',amountCents:29250,currency:'usd',lines,holdExpiresAt:'2099-01-01T00:00:00Z',items:[]};
 const api=nativeBasketCheckout({generic:{prepare:async item=>{preparations++;return {m:{selection:item.selection,view:{profileKey:item.profileKey,profileVersion:1},context:'',offer:null},wire:[{email:'synthetic@example.invalid'}],inputs:[],expected:7500};}},rpc:async(name,args)=>{calls.push({name,args});if(name==='native_checkout_basket_replay'){if(!saved)throw Error('reservation_not_found');if(JSON.stringify(saved)!==JSON.stringify(args.p_request))throw Error('idempotency_conflict');return raw;}if(name==='reserve_native_checkout_basket'){saved=args.p_request;return raw;}throw Error('unexpected_rpc');}});
 const body={items:[{selection:{course:'241108',session:'classA'},profileKey:'primary'},{selection:{course:'209806',session:'classB'},profileKey:'added'}]};
 await api.reserve(key,body);assert.equal(preparations,2);await api.reserve(key,body);assert.equal(preparations,2);
 await assert.rejects(api.reserve(key,{...body,price:1}),/invalid_request/);await assert.rejects(api.reserve(key,{items:[...body.items].reverse()}),/idempotency_conflict/);
 assert.equal(calls.filter(x=>x.name==='reserve_native_checkout_basket').length,1);
});
test('receipt strips private order snapshots and distinguishes received payment from confirmed registration',()=>{
 const r=basketView({basketId:'b',status:'held',paymentObserved:true,items:[{receipt:{status:'held',profileSnapshot:{private:'do not expose'},students:[]}}]});assert.equal(r.status,'processing');assert.equal(JSON.stringify(r).includes('do not expose'),false);assert.equal(basketView({status:'refunded',paymentObserved:true}).status,'refunded');
});
test('one participant renderer uses per-course option/upload configuration, escaping labels and keeping uploads optional',()=>{
 const p={fields:[{key:'name',label:'<script>unsafe</script>',type:'text',max_length:100}],optionGroups:[{key:'materials',label:'Materials',type:'radio',choices:[{key:'paper',label:'Paper book',amountCents:4500,available:false},{key:'ebook',label:'eBook',amountCents:4000,available:true}]}],defaultChoices:[],uploads:[{key:'certificate',label:'Completion certificate',required:false,maxBytes:2097152,mimeTypes:['application/pdf']}],baseCents:22500};const html=participantMarkup(p,'courseA',n=>'$'+n/100);assert.equal(html.includes('<script>'),false);assert.match(html,/&lt;script&gt;/);assert.match(html,/Paper book.*unavailable/);assert.match(html,/optional/);assert.match(html,/bring the document to class/);
 assert.deepEqual(additionalEstimate(p,['ebook'],1),{sessionCents:22500,discountCents:2250,componentsCents:4000,totalCents:24250});
});
import {genericCheckout} from '../supabase/functions/public-registration/generic.mjs';
import {BLS_PACKAGES} from '../supabase/functions/skills-session-reservation/policy.mjs';
test('BLS additions use exact leased skills/bundle identity and never a fabricated concrete appointment',async()=>{
 const now=Date.parse('2030-01-01T00:00:00Z'),stamp=n=>new Date(n).toISOString();let enabled=true,bundle=true;
 for(const course of ['509474','210549']){
  const packageKey=BLS_PACKAGES[course],id='native-skills:'+'a'.repeat(64);
  const row={courseId:course,publicCourseId:course,physicalCourseId:'509474',checkoutPackage:packageKey,profileKey:'native_skills_shared',profileVersion:2,selectionId:'skills:'+id+':bls-skills:'+packageKey,calendarProofObservedAt:stamp(now-60000),policyProofObservedAt:stamp(now-60000),proofObservedAt:stamp(now-60000),offerType:'dynamic_appointment',authority:'native-skills-publication.v1',nativeScopeId:'brian-shipyard-b.v1',nativeOfferId:id,qualificationPolicy:'skills-session-policy.v1',skillsContexts:['bls-skills'],capacity:2,publicSelectable:true,instructor:'Brian Ennis',resource:':: Wilmington; Shipyard Blvd - B',location:':: Wilmington; Shipyard Blvd',availabilityBlockId:'fixture',sourceSessionIds:[],durationMinutes:45,schedulerConsumptionMinutes:60,cleanupBufferMinutes:15,setupBufferMinutes:0,occupiedUntil:'2030-01-03T16:00:00Z',validUntil:stamp(now+600000)};
  const feed={pageKey:'bls',schemaVersion:'selector-resolved-availability.v1',generatedAt:stamp(now),validUntil:stamp(now+600000),dates:[{date:'2030-01-03',startTimes:[{startTime:'10:00',courses:[row]}]}]};
  const api=genericCheckout({now:()=>now,publication:async page=>{assert.equal(page,'bls');return feed;},skillsPolicy:async()=>({nativePublicationEnabled:false}),blsSkillsPolicy:async()=>({skillsEnabled:enabled,bundleEnabled:bundle,profileVersion:2})});
  enabled=true;bundle=true;const rows=await api.availableSelections(course,'bls-skills');assert.equal(rows.length,1);assert.deepEqual(rows[0].selection,{course,skillsContext:'bls-skills',selectionId:row.selectionId});assert.equal(rows[0].session,undefined);
  enabled=false;assert.equal((await api.availableSelections(course,'bls-skills')).length,0);enabled=true;
  bundle=false;assert.equal((await api.availableSelections(course,'bls-skills')).length,course==='210549'?0:1);
  assert.deepEqual(await api.availableSelections(course,'arc-blended'),[]);
 }
});
