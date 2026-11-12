// Synthetic-only NDJSON bridge: real SQL lifecycle and actual HTTP adapter.
// No listening socket, production credential, hosted mutation, mail, or payment.
// Fixture setup mirrors native-expired-payment-recovery.test.mjs; keep in sync.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createInterface} from 'node:readline';
const root=process.env.NATIVE_RETURN_SOURCE_ROOT||fileURLToPath(new URL('../../',import.meta.url));
const imp=p=>import(pathToFileURL(root+'/'+p));
const load=p=>readFileSync(root+'/'+p,'utf8');
const scope=process.env.NATIVE_RETURN_TEST_SCOPE||'bls';
assert.ok(['bls','extended'].includes(scope),'scope must be bls or extended');
const extended=scope==='extended';
const bls=await imp('tests/native-bls-admission-proof.mjs');
const hs=extended?await imp('tests/native-heartsaver-admission-proof.mjs'):null;
const ped=extended?await imp('tests/native-pediatric-admission-proof.mjs'):null;
const {returnHTTP,storedOrder}=await imp('tests/helpers/native-return-http.mjs');
const {scalar,service}=bls;
const courses=extended?['209806','359474','509474','209809','344085','351632']:['209806','359474','509474'];
const scenarios=['available','full','after_start','finalizer_failure','unpaid','ambiguous','held_ambiguous','checkout_open_ambiguous','cancelled','refunded'];
const prices={'209806':7500,'359474':7500,'509474':5500,'209809':9500,'344085':7000,'351632':9500};
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

const db=await create();
// Fail closed even if future fixture changes accidentally use global fetch.
globalThis.fetch=async()=>{throw Error('synthetic_bridge_external_fetch_forbidden');};
let current;
async function clearFailure(){
 await db.exec('drop trigger if exists synthetic_browser_outbox_failure on landerware_messages;drop function if exists synthetic_browser_outbox_failure();');
}
async function seed(course,scenario){
 assert.ok(courses.includes(course),'course outside selected scope');
 assert.ok(scenarios.includes(scenario),'unknown scenario');
 await clearFailure();
 if(current)await db.query("update class_sessions set status='cancelled',registration_status='closed' where id=$1",[current.claim.sessionId]);
 const claim=await reserve(db,course),provider=await bound(db,claim,{expired:!scenario.endsWith('_ambiguous')});
 if(scenario.endsWith('_ambiguous'))await db.query('update landerware_public_orders set status=$2 where id=$1',[claim.orderId,scenario.replace('_ambiguous','')]);
 assert.equal(provider.amount_total,prices[course]);
 if(scenario==='full'){
  const seats=await service(db,()=>scalar(db,'select landerware_public_seat_state($1)',[claim.sessionId]));
  for(let i=0;i<seats.remaining;i++){
   const customer=await scalar(db,"insert into customers(first_name,last_name,email) values('Synthetic','Occupant',$1) returning id",[`browser-occupant-${++n}@example.invalid`]);
   await db.query("insert into registrations(customer_id,class_session_id,status,registration_source) values($1,$2,'registered','landerware_native_checkout')",[customer,claim.sessionId]);
  }
 }
 if(scenario==='after_start'){
  await db.query("update class_sessions set start_at=now()-interval '1 second',end_at=now()+interval '2 hours',consumption_start_at=now()-interval '10 minutes',consumption_end_at=now()+interval '150 minutes' where id=$1",[claim.sessionId]);
  if(course==='351632')await ped.adoptPediatricSession(db,claim.sessionId);
 }
 if(scenario==='finalizer_failure')await db.exec("create function synthetic_browser_outbox_failure() returns trigger language plpgsql as $$begin raise exception 'synthetic_browser_outbox_failure';end$$;create trigger synthetic_browser_outbox_failure before insert on landerware_messages for each row execute function synthetic_browser_outbox_failure();");
 if(['cancelled','refunded'].includes(scenario))await db.query("update landerware_public_orders set status=$2,payment_evidence=$3::jsonb,reconciliation_error='synthetic_prior_review' where id=$1",[claim.orderId,scenario,JSON.stringify(provider)]);
 const h=returnHTTP(db,claim,scenario==='unpaid'?{...provider,payment_status:'unpaid',status:'expired'}:scenario.includes('ambiguous')?{}:provider);
 current={claim,h,course,scenario,provider};
 const order=await storedOrder(db,claim.orderId);
 const session=await scalar(db,'select to_jsonb(s) from class_sessions s where id=$1',[claim.sessionId]);
 return {course,scenario,key:claim.key,orderId:claim.orderId,session:session.external_class_id,recover:order.recovery_token,amountCents:order.total};
}
async function inspect(){
 assert.ok(current,'seed first');
 const order=await storedOrder(db,current.claim.orderId);
 return {course:current.course,scenario:current.scenario,orderId:order.id,status:order.status,
  stripeCheckoutId:order.stripe_checkout_session_id,paymentIntentId:order.stripe_payment_intent_id,
  paymentObserved:order.payment_evidence?.payment_status==='paid',reconciliationError:order.reconciliation_error,
  footprint:await footprint(db,current.claim),calls:current.h.calls,
  orderCount:await scalar(db,"select count(*) from landerware_public_orders where idempotency_key='public-order:'||$1",[current.claim.key])};
}
async function command(packet){
 switch(packet.op){
  case 'seed':return seed(packet.course,packet.scenario);
  case 'request':{
   assert.ok(current,'seed first');assert.equal(packet.method,'GET','browser may only request form/status, never reserve/upload/checkout');
   const url=new URL(packet.url);
   assert.equal(url.origin,'https://wktwgcnwdvbebcobgyey.supabase.co');
   const prefix='/functions/v1/public-registration/generic/';assert.ok(url.pathname.startsWith(prefix));
   const action=url.pathname.slice(prefix.length);assert.ok(['form','status'].includes(action),'unsupported browser API action');
   if(url.searchParams.has('recover')){
    assert.equal(action,'form');assert.equal(url.searchParams.get('recover'),(await storedOrder(db,current.claim.orderId)).recovery_token);
    assert.ok(!packet.key,'recovery must not use an unrelated nonce');
   }else assert.equal(packet.key,current.claim.key,'browser must retain original saved nonce');
   return current.h.send(action+url.search);
  }
  case 'inspect':return inspect();
  case 'repair':await clearFailure();current.h.failProvider(null);return inspect();
  case 'verify_unpaid':current.h.provider({...current.provider,payment_status:'unpaid',status:'open'});return {ok:true};
  case 'provider_outage':current.h.failProvider('synthetic_provider_timeout');return {ok:true};
  default:throw Error('unknown fixture operation');
 }
}
async function smoke(){
 let checks=0;
 for(const course of courses)for(const scenario of scenarios){
  const c=await seed(course,scenario);
  const base='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/public-registration/generic/';
  const form=await command({op:'request',method:'GET',url:base+'form?recover='+c.recover});assert.equal(form.status,200,JSON.stringify(form));assert.equal(form.body.key,c.key);
  const result=await command({op:'request',method:'GET',url:base+'status',key:c.key});
  const expected={available:'paid',full:'payment_review',after_start:'payment_review',finalizer_failure:'processing',unpaid:'expired',cancelled:'cancelled',refunded:'refunded'}[scenario];
  if(scenario.includes('ambiguous')){assert.equal(result.status,500);assert.equal(result.body.error,'payment_evidence_mismatch');}
  else assert.equal(result.body.receipt.status,expected,JSON.stringify(result));
  let state=await inspect();assert.equal(Number(state.orderCount),1);assert.equal(state.calls.some(c=>c.path.startsWith('/v1/')&&c.method!=='GET'),false);
  const count=scenario==='available'?1:0;assert.deepEqual(state.footprint,{registrations:count,studentLinks:count,confirmations:count});
  if(scenario==='finalizer_failure'){
   await command({op:'provider_outage'});assert.equal((await current.h.send()).body.receipt.status,'processing');
   await command({op:'repair'});assert.equal((await current.h.send()).body.receipt.status,'paid');assert.equal((await current.h.send()).body.receipt.status,'paid');
   assert.deepEqual((await inspect()).footprint,{registrations:1,studentLinks:1,confirmations:1});
  }
  if(scenario.endsWith('_ambiguous')){
   await command({op:'verify_unpaid'});
   assert.equal((await current.h.send()).body.receipt.status,scenario.replace('_ambiguous',''));
   assert.equal((await inspect()).paymentObserved,false);
  }
  checks++;
 }
 return {ok:true,scope,checks};
}
try{
 if(process.argv.includes('--smoke'))console.log(JSON.stringify(await smoke()));
 else{
  console.log(JSON.stringify({ok:true,ready:true,scope,courses}));
  for await(const line of createInterface({input:process.stdin,crlfDelay:Infinity})){
   if(!line.trim())continue;
   try{console.log(JSON.stringify({ok:true,result:await command(JSON.parse(line))}));}
   catch(error){console.log(JSON.stringify({ok:false,error:String(error),stack:error.stack}));}
  }
 }
}finally{await db.close();}
