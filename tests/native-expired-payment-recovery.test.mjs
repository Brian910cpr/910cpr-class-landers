// Synthetic SQL + actual HTTP adapter. Provider requests are injected, never sent.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as bls from './native-bls-admission-proof.mjs';
const scope=process.env.NATIVE_RETURN_TEST_SCOPE||'bls';
if(!['bls','extended'].includes(scope))throw Error('NATIVE_RETURN_TEST_SCOPE must be bls or extended');
// The default BLS-only gate imports no adult/Pediatric fixtures or migrations.
// Extended mode is explicit and fails if any later-family dependency is absent.
const extended=scope==='extended';
const hs=extended?await import('./native-heartsaver-admission-proof.mjs'):null;
const ped=extended?await import('./native-pediatric-admission-proof.mjs'):null;
import {returnHTTP,storedOrder} from './helpers/native-return-http.mjs';
import {receiptView} from '../supabase/functions/public-registration/generic.mjs';
import {checkoutAttention,ORDER_STATUS_QUERY} from '../supabase/functions/production-board/checkout-attention.mjs';
const {scalar,service}=bls;
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const labels=[['209806','BLS Provider'],['359474','BLS Renewal'],...(extended?[['209809','Heartsaver First Aid CPR AED'],['344085','Heartsaver CPR AED'],['351632','Heartsaver Pediatric']]:[]),['509474','BLS skills $55']];
const prices={'209806':7500,'359474':7500,'209809':9500,'344085':7000,'351632':9500,'509474':5500};
let n=81000,day=10;
async function create(){
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');
 const db=new PGlite();
 if(extended)await ped.setupPediatricAdmission(db,{enabled:true,optional:false});
 else{
  await bls.setupBlsAdmission(db,{full:false});
  for(const name of ['20261111225500_native_full_offer_wallclock_lease.sql','20261111233000_native_skills_offer_wallclock_lease.sql','20261111233504_native_bls_skills_publication_disabled.sql'])await db.exec(load('supabase/migrations/'+name));
  assert.equal(await scalar(db,"select to_regclass('native_pediatric_existing_session_policy')"),null);
  assert.equal(await scalar(db,"select to_regclass('native_heartsaver_full_course_policy')"),null);
 }
 assert.equal(await scalar(db,"select to_regclass('native_learner_code_runtime')"),null,'no optional bundle/code runtime dependency');
 await db.exec(load('supabase/migrations/20261110213818_native_plain_skills_profile_draft_only.sql'));
 await db.exec(`update courses set course_key='skills-session-only',registration_profile_key='native_skills_shared' where enrollware_course_id='509474';
  update landerware_registration_profiles set active=true,version=2 where profile_key='native_skills_shared';
  update native_skills_publication_policy set enabled=true,publication_enabled=true,verified=true,evidence='SYNTHETIC LOCAL ONLY';
  insert into instructor_qualifications(instructor_id,course_id,qualification_key,status)
   select p.id,c.id,'skills-session-policy.v1','active' from people p cross join courses c where p.person_key='brian' and c.enrollware_course_id='509474';
  update native_bls_skills_publication_policy set enabled=true,publication_enabled=true,verified=true,evidence='SYNTHETIC LOCAL ONLY',
   source_qualification_id=(select id from instructor_qualifications where qualification_key='aha-bls-instructor:209806');
  update skills_session_context_config set enabled=true,capacity_policy_verified=true,qualification_course_id=course_id,policy_evidence='native-bls-skills-policy.v1' where context_key='bls-skills';`);
 await db.exec(load('tests/helpers/native-return-service-role-acl.sql'));
 await db.exec(load('supabase/migrations/20261112023203_native_order_booking_identity.sql'));
 await db.exec(load('supabase/migrations/20261112023721_legacy_skills_cancelled_payment_receipts.sql'));return db;
}
async function reserve(db,course){
 let sql,args;
 if(course==='351632'){
  const p=await ped.makePediatricSession(db,{external:String(990000000+(++n))});
  // This fixture creator uses one fixed date. Close prior synthetic sessions
  // after each scenario; no actual schedule or policy is edited.
  sql=ped.claimSQL;args=ped.request(p.external,++n);
 }else if(course==='509474'){
  const offer=await scalar(db,`select skills_test.offer('late-return', $1,-540)||jsonb_build_object(
   'context','bls-skills','authority','native-skills-publication.v1','nativeScopeId','brian-shipyard-b.v1',
   'nativeOfferId','native-skills:'||repeat('a',64),'proofObservedAt',now(),'qualificationPolicy','skills-session-policy.v1',
   'capacity',2,'instructor','Brian Ennis','publicCourseId','509474','physicalCourseId','509474',
   'checkoutPackage','bls-skills-only.v1','profileKey','native_skills_shared','profileVersion',2,
   'calendarProofObservedAt',now(),'policyProofObservedAt',now(),
   'selectionId','skills:native-skills:'||repeat('a',64)||':bls-skills:bls-skills-only.v1')`,[++day]);
  const wire={firstName:'Synthetic',lastName:'Recovery',email:`return-${++n}@example.invalid`,phone:'2025550100',skillsContext:'bls-skills',selectorSelectionId:offer.selectionId,learningPath:'skills-only',onlineCompleted:true,addons:[]};
  sql="select reserve_native_checkout_order($1,'native_skills_shared',2,'bls-skills',null,$2::jsonb,$3::jsonb,$4::jsonb,5500)";
  args=[`${String(n).padStart(8,'0')}-1111-4111-8111-111111111111`,JSON.stringify(offer),JSON.stringify([wire]),JSON.stringify([{wire,selectedChoices:['skills_only']}])];
 }else{
  const b=['209806','359474'].includes(course),offer=await (b?bls.makeBlsOffer:hs.makeHeartsaverOffer)(db,course,++day);
  offer.validUntil=await scalar(db,"select now()+interval '10 minutes'");
  sql=b?bls.claimSQL:hs.claimSQL;args=(b?bls.request:hs.request)(course,null,offer,++n);
 }
 const c=await service(db,()=>scalar(db,sql,args));return {...c,key:args[0]};
}
async function bound(db,c,{expired=true}={}){
 const o=await storedOrder(db,c.orderId),id='cs_synthetic_'+c.orderId.replaceAll('-','');
 await db.query(`update landerware_public_orders set stripe_checkout_session_id=$2${expired?",status='expired',hold_expires_at=now()-interval '1 second'":''} where id=$1`,[c.orderId,id]);
 return {id,mode:'payment',status:'complete',payment_status:'paid',livemode:false,amount_total:o.total,currency:o.currency,metadata:{landerware_order_id:o.id},payment_intent:'pi_synthetic_'+c.orderId.replaceAll('-','')};
}
const footprint=(db,c)=>scalar(db,`select jsonb_build_object(
 'registrations',(select count(*) from registrations where optional_survey->>'publicOrderId'=$1::text),
 'studentLinks',(select count(*) from landerware_public_order_students where order_id=$1::uuid and registration_id is not null),
 'confirmations',(select count(*) from landerware_messages where idempotency_key like 'public-order-paid:'||$1::text||':%'))`,[c.orderId]);
const close=(db,c)=>db.query("update class_sessions set status='cancelled',registration_status='closed' where id=$1",[c.sessionId]);
const requestCount=(h,name)=>h.calls.filter(x=>x.path.endsWith('/'+name)).length;
const assertNoCharge=h=>assert.equal(h.calls.filter(x=>x.path.startsWith('/v1/')&&x.method!=='GET').length,0);
async function attention(db,c){
 const o=await storedOrder(db,c.orderId);
 return (await checkoutAttention(async q=>q===ORDER_STATUS_QUERY?[{id:o.id,status:o.status,class_session_id:o.class_session_id,reconciliation_error:o.reconciliation_error,created_at:o.created_at,payment_status:o.payment_evidence?.payment_status}]:[])).items;
}

test(`expired native returns (${scope} scope) verify every selected course label without recreating payment`,async t=>{
 const db=await create();try{
 for(const [course,label] of labels)for(const scenario of ['available','full','after_start','released_session'])await t.test(label+': '+scenario,async()=>{
  const c=await reserve(db,course),s=await bound(db,c);assert.equal(s.amount_total,prices[course]);
  if(scenario==='full'){
   const state=await service(db,()=>scalar(db,'select landerware_public_seat_state($1)',[c.sessionId]));
   for(let i=0;i<state.remaining;i++){
    const id=await scalar(db,"insert into customers(first_name,last_name,email) values('Synthetic','Occupant',$1) returning id",[`occupant-${++n}@example.invalid`]);
    await db.query("insert into registrations(customer_id,class_session_id,status,registration_source) values($1,$2,'registered','landerware_native_checkout')",[id,c.sessionId]);
   }
  }
  if(scenario==='after_start'){
   await db.query("update class_sessions set start_at=now()-interval '1 second',end_at=now()+interval '2 hours',consumption_start_at=now()-interval '10 minutes',consumption_end_at=now()+interval '150 minutes' where id=$1",[c.sessionId]);
   if(course==='351632')await ped.adoptPediatricSession(db,c.sessionId);
  }
  if(scenario==='released_session'){
   if(course==='351632')await close(db,c);
   else{
    const session=await scalar(db,'select to_jsonb(s) from class_sessions s where id=$1',[c.sessionId]);
    const released=await service(db,()=>scalar(db,'select native_checkout_release_abandoned($1,$2)',[session.consumption_start_at||session.start_at,session.consumption_end_at||session.end_at]));
    assert.equal(released,1,'actual generated cleanup releases the expired unpaid hold');
   }
  }
  const h=returnHTTP(db,c,s),o=await storedOrder(db,c.orderId);
  // The original recovery URL resumes the same nonce before status checks.
  const form=await h.send('form?recover='+o.recovery_token);assert.equal(form.status,200,JSON.stringify(form));assert.equal(form.body.key,c.key);
  const result=await h.send();assert.equal(result.status,200,JSON.stringify(result));
  const expected=scenario==='available'?'paid':'payment_review';assert.equal(result.body.receipt.status,expected);
  assert.equal(result.body.receipt.amountCents,prices[course]);
  const stored=await storedOrder(db,c.orderId);assert.equal(stored.payment_evidence.payment_status,'paid');assert.equal(stored.stripe_payment_intent_id,s.payment_intent);
  assert.equal(requestCount(h,'native_checkout_record_payment'),1);assert.equal(requestCount(h,'native_checkout_finalize_order'),1);
  const expectedFootprint=scenario==='available'?{registrations:1,studentLinks:1,confirmations:1}:{registrations:0,studentLinks:0,confirmations:0};
  assert.deepEqual(await footprint(db,c),expectedFootprint);
  const alerts=await attention(db,c);assert.equal(alerts.length,scenario==='available'?0:1);
  if(scenario==='full')assert.equal(stored.reconciliation_error,'paid_seat_unavailable');
  if(['after_start','released_session'].includes(scenario))assert.equal(stored.reconciliation_error,'session_not_open');
  for(let i=0;i<3;i++)assert.equal((await h.send()).body.receipt.status,expected);
  assert.equal(requestCount(h,'native_checkout_record_payment'),1,'terminal paid/review replay does not repeat payment recording');
  assert.deepEqual(await footprint(db,c),expectedFootprint);
  const checkout=await h.send('checkout');
  if(expected==='paid')assert.equal(checkout.body.receipt.status,'paid');else assert.equal(checkout.body.error,'payment_reconciliation_required');
  assert.equal(checkout.body.checkoutUrl,undefined);assertNoCharge(h);await close(db,c);
 });
 }finally{await db.close();}
});

test('native expired verification fails closed for ambiguous or mismatched provider evidence',async t=>{
 const db=await create();try{
 const c=await reserve(db,'209806'),paid=await bound(db,c),h=returnHTTP(db,c,paid);
 const invalid=[['missing response',{}],['missing payment state',{...paid,payment_status:undefined}],['unknown payment state',{...paid,payment_status:'unknown'}],
  ['missing amount',{...paid,amount_total:undefined}],['wrong amount',{...paid,amount_total:1}],['numeric amount string',{...paid,amount_total:'7500'}],
  ['wrong currency',{...paid,currency:'eur'}],['wrong order',{...paid,metadata:{landerware_order_id:'11111111-1111-4111-8111-111111111111'}}],
  ['wrong Checkout',{...paid,id:'cs_wrong'}],['missing Checkout',{...paid,id:undefined}],['wrong mode',{...paid,mode:'subscription'}],['wrong live mode',{...paid,livemode:true}],
  ['missing payment intent',{...paid,payment_intent:undefined}],['expanded payment intent',{...paid,payment_intent:{id:paid.payment_intent}}],
  ['no payment required on positive order',{...paid,payment_status:'no_payment_required'}],['unknown unpaid session status',{...paid,payment_status:'unpaid',status:'unknown'}],
  ['unpaid wrong binding',{...paid,payment_status:'unpaid',status:'open',metadata:{}}]];
 for(const [label,response] of invalid)await t.test(label,async()=>{
  h.provider(response);const r=await h.send();assert.equal(r.status,500,JSON.stringify(r));assert.equal(r.body.error,'payment_evidence_mismatch');
  assert.notEqual((await storedOrder(db,c.orderId)).payment_evidence?.payment_status,'paid');
  assert.deepEqual(await footprint(db,c),{registrations:0,studentLinks:0,confirmations:0});
 });
 h.failProvider('synthetic_provider_timeout');assert.equal((await h.send()).status,500);h.failProvider(null);
 // All documented Checkout states can be explicitly unpaid, including an
 // asynchronous payment still pending after Checkout completion.
 for(const status of ['open','complete','expired']){
  h.provider({...paid,payment_status:'unpaid',status});const r=await h.send();assert.equal(r.status,200);assert.equal(r.body.receipt.status,'expired');
  assert.equal((await h.send('checkout')).body.error,'hold_expired');
 }
 assert.equal(requestCount(h,'native_checkout_record_payment'),0);assertNoCharge(h);
 // No binding means no provider lookup, and no alternative Checkout creation.
 const count=h.calls.filter(x=>x.path.startsWith('/v1/')).length;
 await db.query('update landerware_public_orders set stripe_checkout_session_id=null where id=$1',[c.orderId]);
 assert.equal((await h.send()).body.receipt.status,'expired');assert.equal((await h.send('checkout')).body.error,'hold_expired');
 assert.equal(h.calls.filter(x=>x.path.startsWith('/v1/')).length,count);
 }finally{await db.close();}
});

test('paid expired receipt survives finalizer failure, retries once safe, and never offers a second payment',async()=>{
 const db=await create();try{
 const c=await reserve(db,'209806'),s=await bound(db,c),h=returnHTTP(db,c,s);
 await db.exec("create function synthetic_return_outbox_failure() returns trigger language plpgsql as $$begin raise exception 'synthetic_outbox_failure';end$$;create trigger synthetic_return_outbox_failure before insert on landerware_messages for each row execute function synthetic_return_outbox_failure();");
 const r=await h.send();assert.equal(r.status,200);assert.equal(r.body.receipt.status,'processing');
 const o=await storedOrder(db,c.orderId);assert.equal(o.status,'expired');assert.equal(o.payment_evidence.payment_status,'paid');assert.equal(o.reconciliation_error,null);
 assert.deepEqual(await footprint(db,c),{registrations:0,studentLinks:0,confirmations:0});
 const checkout=await h.send('checkout');assert.equal(checkout.body.receipt.status,'processing');assert.equal(checkout.body.checkoutUrl,undefined);
 h.failProvider('synthetic_provider_timeout');assert.equal((await h.send()).body.receipt.status,'processing');h.failProvider(null);
 await db.exec('drop trigger synthetic_return_outbox_failure on landerware_messages;drop function synthetic_return_outbox_failure();');
 assert.equal((await h.send()).body.receipt.status,'paid');assert.equal((await h.send()).body.receipt.status,'paid');
 assert.deepEqual(await footprint(db,c),{registrations:1,studentLinks:1,confirmations:1});assertNoCharge(h);
 }finally{await db.close();}
});

test('cancelled/refunded native receipts stay terminal despite paid evidence or elapsed hold',async()=>{
 const db=await create();try{
 for(const status of ['cancelled','refunded']){
  const c=await reserve(db,'209806'),s=await bound(db,c),h=returnHTTP(db,c,s);
  await db.query("update landerware_public_orders set status=$2,payment_evidence=$3::jsonb,reconciliation_error='synthetic_prior_review' where id=$1",[c.orderId,status,JSON.stringify(s)]);
  for(let i=0;i<2;i++)assert.equal((await h.send()).body.receipt.status,status);
  assert.equal((await h.send('checkout')).body.error,'payment_reconciliation_required');
  assert.equal(h.calls.some(x=>x.path.startsWith('/v1/')),false);assert.equal(requestCount(h,'native_checkout_finalize_order'),0);
  assert.deepEqual(await footprint(db,c),{registrations:0,studentLinks:0,confirmations:0});assert.equal((await storedOrder(db,c.orderId)).status,status);await close(db,c);
 }
 // A canonical already-paid zero-value order needs no provider verification.
 const c=await reserve(db,'209806');await db.query("update landerware_public_orders set status='paid',total=0,hold_expires_at=now()-interval '1 day' where id=$1",[c.orderId]);
 const h=returnHTTP(db,c,null);assert.equal((await h.send()).body.receipt.status,'paid');assert.equal((await h.send('checkout')).body.receipt.status,'paid');
 assert.equal(h.calls.some(x=>x.path.startsWith('/v1/')),false);
 }finally{await db.close();}
});

test('native receipt projection preserves lifecycle precedence without altering the legacy skills receipt path',()=>{
 for(const status of ['held','checkout_open','expired'])assert.equal(receiptView({kind:'public_order',status,paymentObserved:true,holdExpiresAt:'2000-01-01'}).status,'processing');
 for(const status of ['cancelled','canceled','refunded'])assert.equal(receiptView({kind:'public_order',status,paymentObserved:true,reconciliationError:'review',holdExpiresAt:'2000-01-01'}).status,status);
 assert.equal(receiptView({kind:'public_order',status:'expired',paymentObserved:true,reconciliationError:'review'}).status,'payment_review');
 assert.equal(receiptView({kind:'skills_reservation',status:'expired',paymentObserved:true}).status,'expired');
});
