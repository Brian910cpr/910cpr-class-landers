// Synthetic LOCAL SQL proof. Provider payloads are injected; never send or charge.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {preProfileFiles,profileRuntime} from './helpers/native-checkout-migration-plan.mjs';
import {skillsCheckout} from '../supabase/functions/skills-session-reservation/checkout.mjs';
import {genericCheckout,receiptView} from '../supabase/functions/public-registration/generic.mjs';
import {checkoutAttention,SKILLS_PAYMENT_QUERY} from '../supabase/functions/production-board/checkout-attention.mjs';
const root=fileURLToPath(new URL('../',import.meta.url)),load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
mkdirSync(new URL('../local-proof/',import.meta.url),{recursive:true});
const pg=process.argv.includes('--pg17')||process.argv.includes('--postgres');
const db=pg?await (await import('./helpers/legacy-skills-local-pg.mjs')).createPg(root):new (await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite')).PGlite();
const scalar=async(q,a=[])=>Object.values((await db.query(q,a)).rows[0]||{})[0];
const migration='supabase/migrations/20261112023721_legacy_skills_cancelled_payment_receipts.sql';
let n=0;const results=[];
const admin=async fn=>{await db.exec('reset role');try{return await fn();}finally{await db.exec('set role service_role');}};
const rpc=(name,a)=>name==='skills_checkout_order'?scalar('select skills_checkout_order($1,$2)',[a.p_key,a.p_context]):name==='native_checkout_receipt'?scalar('select native_checkout_receipt($1)',[a.p_key]):name==='confirm_skills_checkout_payment'?scalar('select confirm_skills_checkout_payment($1,$2,$3,$4,$5)',[a.p_registration_id,a.p_checkout_id,a.p_amount_total,a.p_currency,a.p_payment_intent]):Promise.reject(Error('unexpected_rpc:'+name));
const confirm=(f,changes={})=>rpc('confirm_skills_checkout_payment',{p_registration_id:f.reg,p_checkout_id:f.cs,p_amount_total:5500,p_currency:'usd',p_payment_intent:f.pi,...changes});
const snapshot=()=>scalar("select jsonb_build_object('registrations',(select jsonb_agg(to_jsonb(r) order by id) from registrations r),'classes',(select jsonb_agg(to_jsonb(s) order by id) from class_sessions s),'customers',(select count(*) from customers),'messages',(select count(*) from landerware_messages),'publicOrders',(select count(*) from landerware_public_orders),'inventory',(select count(*) from product_inventory_units),'students',(select count(*) from landerware_public_order_students),'events',(select count(*) from participant_lifecycle_events),'requirements',(select count(*) from registration_requirements))");
const order=f=>scalar('select to_jsonb(o) from registration_orders o where registration_id=$1',[f.reg]);
async function fixture({registration='registered',status='payment_pending',bound=true,paid=false}={}){
 n++;const key=`55000000-1111-4111-8111-${String(n).padStart(12,'0')}`;
 const answer=await admin(()=>scalar("select reserve_skills_session_native($1,'cpr-aed',skills_test.offer($2,$3),skills_test.student($3))",[key,'late-legacy-'+n,n+10]));
 const f={key,reg:answer.registrationId,session:answer.sessionId,cs:'cs_synthetic_'+n,pi:'pi_synthetic_'+n};
 if(bound)await scalar('select bind_skills_checkout($1,$2)',[f.reg,f.cs]);
 if(paid)await confirm(f);
 await admin(async()=>{await db.query('update registrations set status=$2 where id=$1',[f.reg,registration]);await db.query('update registration_orders set status=$2 where registration_id=$1',[f.reg,status]);});
 f.id=(await order(f)).id;return f;
}
function provider(f,changes={}){return{id:f.cs,mode:'payment',livemode:false,client_reference_id:f.reg,metadata:{skills_session:'509474',registration_id:f.reg,order_id:f.id},status:'complete',payment_status:'paid',amount_total:5500,currency:'usd',payment_intent:f.pi,...changes};}
function legacy(f,session,throwProvider=false){return skillsCheckout({rpc,expectedLive:false,stripe:async(method,path)=>{assert.equal(method,'GET','never a second Checkout');assert.equal(path,'checkout/sessions/'+f.cs);if(throwProvider)throw Error('synthetic_provider_unavailable');return session;}},f.key,'cpr-aed',true);}
try{
 for(const p of preProfileFiles)await db.exec(load(p));await db.exec(load(profileRuntime));await db.exec(load('supabase/migrations/20261110213130_native_skills_payment_adapter_only.sql'));
 if(process.argv.includes('--hosted-definitions'))await db.exec(load('local-proof/hosted-legacy-helper-definitions.sql'));
 await db.exec(load(migration));await db.exec(load(migration));
 await db.exec(load('tests/helpers/legacy-skills-measured-acl.sql'));
 for(const name of ['confirm_skills_checkout_payment(uuid,text,bigint,text,text)','skills_checkout_order(text,text)','native_checkout_receipt(text)']){
  assert.equal(await scalar('select prosecdef from pg_proc where oid=$1::regprocedure',[name]),false);
  for(const role of ['anon','authenticated'])assert.equal(await scalar('select has_function_privilege($1,$2,\'EXECUTE\')',[role,name]),false);
 }
 await db.exec('set role service_role');
 for(const terminal of [{registration:'canceled'},{registration:'canceled',status:'canceled'},{registration:'registered',status:'canceled'}]){
  const f=await fixture(terminal),before=await admin(snapshot),original=await order(f);
  let saved;for(let i=0;i<3;i++){
   const result=await confirm(f);assert.equal(result.paymentStatus,'payment_review');assert.equal(result.idempotentReplay,i?true:undefined);
   const current=await order(f);assert.equal(current.status,terminal.status==='canceled'?'canceled':'paid');assert.equal(current.stripe_payment_intent_id,f.pi);assert.ok(current.paid_at);assert.ok(current.skills_payment_received_at);assert.ok(current.skills_payment_review_reason);
   if(saved)assert.deepEqual(current,saved);saved=current;
  }
  assert.equal(saved.total_amount,original.total_amount);assert.deepEqual(await admin(snapshot),before);
  const receipt=await rpc('native_checkout_receipt',{p_key:f.key});assert.equal(receipt.paymentObserved,true);assert.equal(receiptView(receipt).status,'payment_review');
  const attention=await checkoutAttention(async q=>q===SKILLS_PAYMENT_QUERY?[{...saved,registration:{class_session_id:f.session}}]:[]);assert.equal(attention.items.length,1);assert.equal(attention.items[0].severity,'critical');
  const text=JSON.stringify(attention);assert.ok(!text.includes(f.pi)&&!text.includes(f.cs));
  assert.equal((await legacy(f,provider(f))).paymentStatus,'payment_review');
  results.push({case:'terminal receipt',terminal,result:'payment_review',originalAmount:5500,replays:3});
 }
 const recovered=await fixture({registration:'canceled'}),beforeRecovery=await admin(snapshot);
 const generic=genericCheckout({rpc,legacyPayment:()=>legacy(recovered,provider(recovered)),afterCommit:()=>assert.fail('legacy review cannot confirm')});
 const recoveredResult=await generic.status(recovered.key);assert.equal(recoveredResult.receipt.status,'payment_review');assert.deepEqual(await admin(snapshot),beforeRecovery);
 await assert.rejects(generic.checkout(recovered.key),/payment_reconciliation_required/);results.push({case:'customer status recovers paid canceled receipt',result:'payment_review'});
 for(const change of [{p_checkout_id:'cs_wrong'},{p_amount_total:9500},{p_currency:'eur'},{p_payment_intent:null},{p_payment_intent:''},{p_payment_intent:'pi_other'},{p_registration_id:'00000000-0000-4000-8000-000000000000'}]){
  const before=await order(recovered);await assert.rejects(confirm(recovered,change));assert.deepEqual(await order(recovered),before);
 }
 const wrong=await fixture({registration:'canceled'});for(const changes of [{id:'cs_other'},{livemode:true},{client_reference_id:recovered.reg},{amount_total:1},{currency:'eur'},{payment_intent:null},{metadata:{skills_session:'509474',registration_id:wrong.reg,order_id:recovered.id}}]){
  const before=await order(wrong);await assert.rejects(legacy(wrong,provider(wrong,changes)),/payment_mismatch/);assert.deepEqual(await order(wrong),before);
 }
 for(const changes of [{status:'open',payment_status:'unpaid',url:'https://checkout.stripe.com/c/pay/synthetic'},{status:'complete',payment_status:'unpaid'},{status:'expired',payment_status:'unpaid'}])assert.equal((await legacy(wrong,provider(wrong,changes))).paymentStatus,'cancelled');
 await assert.rejects(legacy(wrong,null,true),/synthetic_provider_unavailable/);assert.equal((await order(wrong)).paid_at,null);
 const unbound=await fixture({registration:'canceled',bound:false});assert.equal((await skillsCheckout({rpc,stripe:()=>assert.fail('no provider without stored Checkout')},unbound.key,'cpr-aed')).paymentStatus,'cancelled');
 const duplicate=await fixture({registration:'canceled'});await assert.rejects(confirm(duplicate,{p_payment_intent:recovered.pi}),/payment_mismatch/);assert.equal((await order(duplicate)).paid_at,null);
 const tampered=await fixture({registration:'canceled'});await admin(()=>db.query("update registration_orders set total_amount=95 where registration_id=$1",[tampered.reg]));await assert.rejects(confirm(tampered),/payment_mismatch/);
 const identity=await fixture({registration:'canceled'});await admin(()=>db.query("update skills_session_claim_receipts set result=jsonb_set(result,'{registrationId}',to_jsonb($2::text)) where registration_id=$1",[identity.reg,recovered.reg]));await assert.rejects(confirm(identity),/payment_mismatch/);
 results.push({case:'SQL/provider identity, amount, currency, intent, mode and original quote mismatches',result:'rejected without receipt mutation'});
 const active=await fixture();assert.equal((await confirm(active)).paymentStatus,'paid');const paidOrder=await order(active);assert.equal((await confirm(active)).idempotentReplay,true);assert.deepEqual(await order(active),paidOrder);
 await admin(()=>db.query("update registrations set status='canceled' where id=$1",[active.reg]));assert.equal((await confirm(active)).paymentStatus,'cancelled');assert.deepEqual(await order(active),paidOrder);assert.equal(receiptView(await rpc('native_checkout_receipt',{p_key:active.key})).status,'cancelled');assert.equal((await legacy(active,null,true)).paymentStatus,'cancelled');
 const historicalPaid=await fixture({paid:true,status:'canceled',registration:'canceled'});
 await admin(()=>db.query('update registration_orders set skills_payment_received_at=null,skills_payment_review_reason=null where registration_id=$1',[historicalPaid.reg]));
 const historicalBefore=await order(historicalPaid);assert.equal((await confirm(historicalPaid)).paymentStatus,'cancelled');assert.deepEqual(await order(historicalPaid),historicalBefore);assert.equal((await legacy(historicalPaid,null,true)).paymentStatus,'cancelled');assert.equal((await checkoutAttention(async q=>q===SKILLS_PAYMENT_QUERY?[await order(historicalPaid)]:[])).items.length,0);
 const refunded=await fixture({paid:true,status:'refunded',registration:'canceled'}),refundBefore=await order(refunded);for(let i=0;i<3;i++)assert.equal((await confirm(refunded)).paymentStatus,'refunded');assert.deepEqual(await order(refunded),refundBefore);assert.equal((await legacy(refunded,null,true)).paymentStatus,'refunded');assert.equal(receiptView(await rpc('native_checkout_receipt',{p_key:refunded.key})).status,'refunded');
 const reviewedRefund=await fixture({registration:'canceled'});await confirm(reviewedRefund);await admin(()=>db.query("update registration_orders set status='refunded' where registration_id=$1",[reviewedRefund.reg]));assert.equal(receiptView(await rpc('native_checkout_receipt',{p_key:reviewedRefund.key})).status,'refunded');assert.equal((await checkoutAttention(async q=>q===SKILLS_PAYMENT_QUERY?[await order(reviewedRefund)]:[])).items.length,0);
 results.push({case:'active success, paid then canceled replay, refunded replay',result:'terminal state and timestamps preserved'});
 const concurrent=await fixture({registration:'canceled'}),beforeConcurrent=await admin(snapshot);
 const replays=await Promise.all([confirm(concurrent),confirm(concurrent),confirm(concurrent)]);assert.equal(replays.filter(x=>x.idempotentReplay).length,2);assert.ok(replays.every(x=>x.paymentStatus==='payment_review'));assert.deepEqual(await admin(snapshot),beforeConcurrent);
 const competingA=await fixture({registration:'canceled'}),competingB=await fixture({registration:'canceled'});
 const competing=await Promise.allSettled([confirm(competingA),confirm(competingB,{p_payment_intent:competingA.pi})]);assert.equal(competing.filter(x=>x.status==='fulfilled').length,1);assert.equal(competing.filter(x=>x.status==='rejected').length,1);
 results.push({case:'simultaneous duplicate callbacks and cross-order intent reuse',result:'one durable receipt; duplicate replays; mismatched order rejected'});
 await db.exec('reset role');
 for(const role of ['anon','authenticated']){
  await db.exec('set role '+role);await assert.rejects(confirm(active),/permission denied/);await db.exec('reset role');
 }
 console.log(JSON.stringify({engine:pg?'PG17':'PGlite',cases:results.length,fixtures:n,results},null,2));
 writeFileSync(new URL('../local-proof/'+(pg?'pg17':'pglite')+'-report.json',import.meta.url),JSON.stringify({engine:pg?'PG17':'PGlite',cases:results.length,fixtures:n,results},null,2));
}finally{await db.close();}
