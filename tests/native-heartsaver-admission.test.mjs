// Local synthetic proof only: no production data, providers, messages or payments.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {setupHeartsaverAdmission,makeHeartsaverOffer,request,scalar,service,claimSQL} from './native-heartsaver-admission-proof.mjs';
import {makeBlsOffer,request as blsRequest,claimSQL as blsClaimSQL} from './native-bls-admission-proof.mjs';
const migration=readFileSync(new URL('../supabase/migrations/20261112003000_native_heartsaver_existing_session_admission.sql',import.meta.url),'utf8');
const optional=process.env.HEARTSAVER_TEST_OPTIONAL==='1';
const create=async()=>{const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');return new PGlite();};
test(`Heartsaver new-session admission ${optional?'optional':'independent'} chain`,async()=>{
 const db=await create();let n=60000;
 try{
 await setupHeartsaverAdmission(db,{optional});
 assert.deepEqual((await db.query("select rolsuper,rolbypassrls from pg_roles where rolname='service_role'")).rows[0],{rolsuper:false,rolbypassrls:true});
 for(const name of ['native_heartsaver_session_booking_ready(class_sessions)','native_heartsaver_lock_booking_dependencies()']){
  assert.equal(await scalar(db,'select prosecdef from pg_proc where oid=$1::regprocedure',[name]),false);
  for(const role of ['anon','authenticated'])assert.equal(await scalar(db,"select has_function_privilege($1,$2,'execute')",[role,name]),false);
 }
 for(const course of ['209809','344085']){
  const req=request(course,null,await makeHeartsaverOffer(db,course),++n);
  const first=await service(db,()=>scalar(db,claimSQL,req));assert.equal(first.status,'held');
  const external=await scalar(db,'select external_class_id from class_sessions where id=$1',[first.sessionId]);
  const snapshot=()=>scalar(db,'select native_scheduling_seat_snapshot($1)',[first.sessionId]);
  const base=await snapshot();assert.equal(base.heartsaverBooking.publicCourseId,course);assert.equal(base.holds,1);
  await db.exec('begin');
  assert.equal((await service(db,()=>scalar(db,claimSQL,request(course,external,{},++n)))).status,'held','existing wrapper accepts valid new nonce');
  const directReq=request(course,external,{},++n),directWire=JSON.parse(directReq[4]);
  assert.equal((await service(db,()=>scalar(db,"select native_checkout_create_order($1,$2,$3,$4,'2025550100',$5::jsonb,null,'{\"profile_fields_validated\":true}')",[`positive-direct-${n}`,external,course,directWire[0].email,JSON.stringify(directWire)]))).status,'held','direct creator accepts valid new nonce');
  await db.exec('rollback');

  const ready=()=>scalar(db,'select native_heartsaver_session_booking_ready(s) from class_sessions s where id=$1',[first.sessionId]);
  assert.equal(await ready(),true);
  await db.exec('begin');
  await db.query("insert into instructor_qualifications(instructor_id,course_id,qualification_key,status,expires_at) select lead_instructor_id,course_id,'synthetic-target','active',null from class_sessions where id=$1",[first.sessionId]);
  assert.equal(await ready(),true,'active target row without expiry does not invent a separate credential requirement');
  await db.query("update native_heartsaver_full_course_policy set unit_amount=unit_amount+100 where public_course_id=$1",[course]);
  await db.query("update landerware_registration_catalog set unit_amount=unit_amount+100 where course_id=$1",[course]);
  await db.query("update courses set base_price=base_price+1 where enrollware_course_id=$1",[course]);
  assert.equal(await ready(),true,'reviewed synchronized repricing is policy-driven');
  const repriced=request(course,external,{},++n);repriced[6]+=100;
  assert.equal((await service(db,()=>scalar(db,claimSQL,repriced))).amountCents,repriced[6]);
  await db.exec('rollback');

  const changes=[
   ['policy disabled',`update native_heartsaver_full_course_policy set enabled=false where public_course_id='${course}'`],
   ['publication disabled',`update native_heartsaver_full_course_policy set publication_enabled=false where public_course_id='${course}'`],
   ['source revoked',"update instructor_qualifications set status='revoked' where qualification_key='aha-bls-instructor:209806'"],
   ['source expires during cleanup',`update instructor_qualifications set expires_at=(select end_at from class_sessions where id='${first.sessionId}') where qualification_key='aha-bls-instructor:209806'`],
   ['source unknown expiry',"update instructor_qualifications set expires_at=null where qualification_key='aha-bls-instructor:209806'"],
   ['source infinite expiry',"update instructor_qualifications set expires_at='infinity' where qualification_key='aha-bls-instructor:209806'"],
   ['source wrong key',"update instructor_qualifications set qualification_key='other' where qualification_key='aha-bls-instructor:209806'"],
   ['contradictory source unknown expiry',"insert into instructor_qualifications(instructor_id,course_id,qualification_key,status,expires_at) select instructor_id,course_id,qualification_key,'active',null from instructor_qualifications where qualification_key='aha-bls-instructor:209806'"],
   ['contradictory source wrong key',"insert into instructor_qualifications(instructor_id,course_id,qualification_key,status,expires_at) select instructor_id,course_id,'wrong-key','active',expires_at from instructor_qualifications where qualification_key='aha-bls-instructor:209806'"],
   ['target explicit revocation',`insert into instructor_qualifications(instructor_id,course_id,qualification_key,status) select lead_instructor_id,course_id,'synthetic-target','revoked' from class_sessions where id='${first.sessionId}'`],
   ['instructor inactive',"update people set active=false where person_key='brian'"],
   ['venue inactive',"update locations set scheduling_status='inactive' where location_key='910cpr-office-shipyard'"],
   ['profile disabled',`update landerware_registration_profiles set active=false where profile_key='native_heartsaver_${course}_draft'`],
   ['profile wrong inventory',`update landerware_registration_profiles set version=version+1,form_schema=jsonb_set(form_schema,'{inventory_kind}','"leased_skills_v1"') where profile_key='native_heartsaver_${course}_draft'`],
   ['catalog disabled',`update landerware_registration_catalog set active=false where course_id='${course}'`],
   ['catalog price drift',`update landerware_registration_catalog set unit_amount=unit_amount+100 where course_id='${course}'`],
   ['canonical price drift',`update courses set base_price=1 where enrollware_course_id='${course}'`],
   ['canonical profile drift',`update courses set registration_profile_key=null where enrollware_course_id='${course}'`],
   ['alias collision',`update landerware_registration_profiles set version=version+1,form_schema=jsonb_set(form_schema,'{public_aliases}','[{"public_course_id":"${course}"}]') where profile_key='native_bls_209806_v1'`],
   ['capacity drift',`update class_sessions set max_students=9 where id='${first.sessionId}'`],
   ['external identity drift',`update class_sessions set external_course_id='209808' where id='${first.sessionId}'`],
   ['instruction drift',`update class_sessions set end_at=end_at-interval '1 minute' where id='${first.sessionId}'`],
   ['cleanup drift',`update class_sessions set consumption_end_at=consumption_end_at-interval '1 minute' where id='${first.sessionId}'`],
   ['consumption start drift',`update class_sessions set consumption_start_at=start_at-interval '1 minute' where id='${first.sessionId}'`],
  ];
  for(const [label,change] of changes){
   await db.exec('begin');await db.exec(change);
   assert.equal(await ready(),false,`${course} ${label}: shared predicate`);
   await db.exec('savepoint read_snapshot');
   try{const after=await snapshot();assert.equal(after.heartsaverBooking,null,`${course} ${label}: CTA suppressed`);assert.equal(after.holds,base.holds,'occupancy preserved');}catch(e){assert.match(e.message,/native_authority_identity_changed|native_generated_authority_unavailable/);await db.exec('rollback to read_snapshot');}
   const newReq=request(course,external,{},++n);
   await db.exec('savepoint reject_wrapper');
   await assert.rejects(service(db,()=>scalar(db,claimSQL,newReq)),/session_not_available|native_registration_unavailable|profile_changed|native_profile_not_configured|session_not_open/);await db.exec('rollback to reject_wrapper;reset role');
   const wire=JSON.parse(newReq[4]);
   await db.exec('savepoint reject_creator');
   await assert.rejects(service(db,()=>scalar(db,"select native_checkout_create_order($1,$2,$3,$4,'2025550100',$5::jsonb,null,'{\"profile_fields_validated\":true}')",[`direct-${++n}`,external,course,wire[0].email,JSON.stringify(wire)])),/session_not_available/);await db.exec('rollback to reject_creator;reset role');
   assert.equal((await service(db,()=>scalar(db,claimSQL,req))).orderId,first.orderId,`${label}: prior nonce preserved`);
   await db.exec('rollback');
  }
  // Paid/reconciled orders use the durable nonce before any new admission check.
  await db.exec('begin');await db.query("update landerware_public_orders set status='paid' where id=$1",[first.orderId]);await db.exec("update native_heartsaver_full_course_policy set enabled=false");
  assert.equal((await service(db,()=>scalar(db,claimSQL,req))).orderId,first.orderId);await db.exec('rollback');
  await db.exec('begin isolation level repeatable read');
  await assert.rejects(service(db,()=>scalar(db,claimSQL,request(course,external,{},++n))),/native_heartsaver_admission_isolation_required/);await db.exec('rollback;reset role');
  console.log(`PASS ${course}: ${changes.length} independent rejection/replay scenarios, direct creator, canonical occupancy, paid recovery, isolation`);
 }
 // Exercise both unaffected BLS wrapper paths after the new migration, not
 // merely a separate legacy fixture that lacks it.
 for(const course of ['209806','359474']){
  const req=blsRequest(course,null,await makeBlsOffer(db,course,course==='209806'?60:61),++n);
  // The shared full-offer lease requires original lease fields on v2 offers.
  const offer=JSON.parse(req[3]);offer.validUntil=new Date(Date.now()+10*60*1000).toISOString();req[3]=JSON.stringify(offer);
  const result=await service(db,()=>scalar(db,blsClaimSQL,req));assert.equal(result.status,'held');
  const external=await scalar(db,'select external_class_id from class_sessions where id=$1',[result.sessionId]);
  assert.equal((await service(db,()=>scalar(db,blsClaimSQL,blsRequest(course,external,{},++n)))).status,'held');
  assert.equal((await service(db,()=>scalar(db,blsClaimSQL,req))).orderId,result.orderId);
 }
 }finally{await db.close();}
});

test('Heartsaver migration rejects function drift atomically; policy state unchanged',async()=>{
 const db=await create();try{
 await setupHeartsaverAdmission(db,{optional,apply:false});
 const state=()=>scalar(db,"select jsonb_agg(to_jsonb(p) order by public_course_id) from native_heartsaver_full_course_policy p");const before=await state();
 for(const name of ['native_heartsaver_full_course_ready(text,timestamp with time zone)','native_checkout_create_order(text,text,text,text,text,jsonb,text,jsonb)','native_scheduling_seat_snapshot(uuid)','reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer)']){
  const def=await scalar(db,'select pg_get_functiondef($1::regprocedure)',[name]);await db.exec(def.replace('AS $function$', 'AS $function$\n -- synthetic unexpected drift'));
  await assert.rejects(db.exec(migration),/source_drift/);await db.exec('rollback');
  assert.equal(await scalar(db,"select to_regprocedure('native_heartsaver_lock_booking_dependencies()')::text"),null);await db.exec(def);
 }
 const unchangedSQL="select p.oid::regprocedure::text as signature,md5(p.prosrc) as body from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname not in('native_checkout_create_order','native_scheduling_seat_snapshot','reserve_native_checkout_order','native_heartsaver_full_course_ready','native_heartsaver_session_booking_ready','native_heartsaver_lock_booking_dependencies') order by 1";
 const untouched=(await db.query(unchangedSQL)).rows;
 await db.exec(migration);assert.deepEqual(await state(),before);
 assert.deepEqual((await db.query(unchangedSQL)).rows,untouched,'all unrelated BLS/skills/payment/finalizer/lease bodies unchanged');
 }finally{await db.close();}
});
