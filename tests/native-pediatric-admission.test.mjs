// Synthetic policies/sessions only. Service-role admissions reuse measured baseline ACLs.
import test from 'node:test';
import assert from 'node:assert/strict';
import {setupPediatricAdmission,enablePediatricPolicy,makePediatricSession,adoptPediatricSession,request,scalar,service,claimSQL,migration} from './native-pediatric-admission-proof.mjs';
import {makeHeartsaverOffer,request as adultRequest} from './native-heartsaver-admission-proof.mjs';
import {makeBlsOffer,request as blsRequest,claimSQL as blsSQL} from './native-bls-admission-proof.mjs';
const create=async()=>{const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');return new PGlite();};
const canonical='0689a2c5-c507-4e8a-b94c-15e5c5689e28';
const directSQL="select native_checkout_create_order($1,$2,'351632',$3,'2025550100',$4::jsonb,null,'{\"profile_fields_validated\":true}')";
let n=70000;
function directArgs(external){const r=request(external,++n),wire=JSON.parse(r[4]);return ['direct-pediatric-'+n,external,wire[0].email,JSON.stringify(wire)];}
test('Pediatric default-off policy and service-only existing-session admission',async()=>{
 const db=await create();try{
 await setupPediatricAdmission(db,{apply:false});
 const existing=()=>scalar(db,"select jsonb_build_object('courses',(select jsonb_agg(to_jsonb(t) order by id) from courses t),'profiles',(select jsonb_agg(to_jsonb(t) order by profile_key) from landerware_registration_profiles t),'catalog',(select jsonb_agg(to_jsonb(t) order by course_id) from landerware_registration_catalog t),'qualifications',(select jsonb_agg(to_jsonb(t) order by id) from instructor_qualifications t))");
 const before=await existing();await db.exec(migration());assert.deepEqual(await existing(),before,'migration changes no existing canonical/profile/catalog/qualification data');
 const scope=await scalar(db,'select to_jsonb(p) from native_pediatric_existing_session_policy p');
 for(const k of ['instruction_minutes','setup_minutes','cleanup_minutes','max_students','source_qualification_id','evidence','timing_evidence','capacity_evidence'])assert.equal(scope[k],null,k);
 assert.equal(scope.enabled,false);assert.equal(scope.publication_enabled,false);assert.equal(scope.verified,false);
 assert.equal(scope.unit_amount,9500);
 const runtime=()=>service(db,()=>scalar(db,'select native_pediatric_existing_session_runtime_policy()'));
 const off=await runtime();assert.equal(off.existingSessionEnabled,false);assert.equal(off.nativePublicationEnabled,false);assert.equal(off.materializationEnabled,false);assert.equal(off.qualificationValidThrough,null);assert.equal(off.profileVersion,null);
 for(const key of ['sourceQualificationId','evidence','qualification_scope_evidence'])assert.equal(Object.hasOwn(off,key),false);
 assert.deepEqual((await db.query("select rolsuper,rolbypassrls from pg_roles where rolname='service_role'")).rows[0],{rolsuper:false,rolbypassrls:true});
 for(const name of ['native_pediatric_existing_session_ready(timestamptz)','native_pediatric_session_booking_ready(class_sessions)','native_pediatric_existing_session_runtime_policy()','native_pediatric_lock_booking_dependencies()']){
  assert.equal(await scalar(db,'select prosecdef from pg_proc where oid=$1::regprocedure',[name]),false);
  for(const role of ['anon','authenticated'])assert.equal(await scalar(db,"select has_function_privilege($1,$2,'execute')",[role,name]),false);
 }
 assert.equal(await scalar(db,"select relrowsecurity from pg_class where oid='native_pediatric_existing_session_policy'::regclass"),true);
 for(const role of ['anon','authenticated'])assert.equal(await scalar(db,"select has_table_privilege($1,'native_pediatric_existing_session_policy','select,insert,update,delete')",[role]),false);
 const s=await makePediatricSession(db),snapshot=()=>service(db,()=>scalar(db,'select native_scheduling_seat_snapshot($1)',[s.sessionId]));
 const offSeats=await snapshot();assert.equal(offSeats.pediatricBooking,null);assert.equal(offSeats.registered,1);assert.equal(offSeats.unreconciledReserved,2);
 await assert.rejects(service(db,()=>scalar(db,directSQL,directArgs(s.external))),/session_not_available/);
 await enablePediatricPolicy(db);
 assert.equal((await runtime()).nativePublicationEnabled,true);assert.equal((await runtime()).materializationEnabled,false);
 const ready=()=>service(db,()=>scalar(db,'select native_pediatric_session_booking_ready(s) from class_sessions s where id=$1',[s.sessionId]));
 assert.equal(await ready(),true);
 const initialReq=request(s.external,++n),first=await service(db,()=>scalar(db,claimSQL,initialReq));assert.equal(first.status,'held');
 const base=await snapshot();assert.equal(base.holds,1);assert.equal(base.registered,1);assert.equal(base.unreconciledReserved,2);assert.equal(base.remaining,4);
 assert.equal(base.pediatricBooking.packageCode,'full-course');assert.equal(base.pediatricBooking.publicCourseId,'351632');assert.equal(base.pediatricBooking.canonicalCourseId,canonical);
 assert.equal(base.pediatricBooking.setupMinutes,7);assert.equal(base.pediatricBooking.instructionMinutes,123);assert.equal(base.pediatricBooking.cleanupMinutes,13);
 await db.exec('begin');assert.equal((await service(db,()=>scalar(db,directSQL,directArgs(s.external)))).status,'held');await db.exec('rollback');
 assert.equal((await runtime()).unitAmount,9500);assert.equal(base.pediatricBooking.unitAmount,9500);assert.equal(base.pediatricBooking.currency,'usd');
 await db.exec('begin');await db.exec("update native_pediatric_existing_session_policy set unit_amount=9600;update courses set base_price=96 where enrollware_course_id='351632';update landerware_registration_catalog set unit_amount=9600 where course_id='351632'");
 assert.equal(await ready(),true);assert.equal((await runtime()).unitAmount,9600);assert.equal((await snapshot()).pediatricBooking.unitAmount,9600);
 const repriced=request(s.external,++n);repriced[6]=9600;assert.equal((await service(db,()=>scalar(db,claimSQL,repriced))).amountCents,9600);await db.exec('rollback');
 const profile=()=>service(db,()=>scalar(db,"select native_checkout_profile('351632',null)"));assert.equal((await profile()).physicalCourseId,'351632');
 // No dynamic slot generation is unlocked by a complete reviewed policy.
 const count=await scalar(db,'select count(*)::int from class_sessions');
 const dynamic=request(null,++n);dynamic[3]=JSON.stringify(await makeHeartsaverOffer(db,'209809'));
 await assert.rejects(service(db,()=>scalar(db,claimSQL,dynamic)),/session_not_available/);
 assert.equal(await scalar(db,'select count(*)::int from class_sessions'),count);
 assert.equal(await scalar(db,"select native_full_course_option('351632',$1::jsonb)",[dynamic[3]]),null);
 const changes=[
  ['booking disabled',"update native_pediatric_existing_session_policy set enabled=false"],
  ['publication disabled',"update native_pediatric_existing_session_policy set publication_enabled=false"],
  ['unknown policy row',"delete from native_pediatric_existing_session_policy"],
  ['source revoked',"update instructor_qualifications set status='revoked' where qualification_key='aha-bls-instructor:209806'"],
  ['source null expiry',"update instructor_qualifications set expires_at=null where qualification_key='aha-bls-instructor:209806'"],
  ['source infinite expiry',"update instructor_qualifications set expires_at='infinity' where qualification_key='aha-bls-instructor:209806'"],
  ['source insufficient through cleanup',`update instructor_qualifications set expires_at=(select end_at from class_sessions where id='${s.sessionId}') where qualification_key='aha-bls-instructor:209806'`],
  ['wrong source key',"update instructor_qualifications set qualification_key='wrong' where qualification_key='aha-bls-instructor:209806'"],
  ['contradictory BLS source',"insert into instructor_qualifications(instructor_id,course_id,qualification_key,status,expires_at) select instructor_id,course_id,'aha-bls-instructor:209806','active',null from instructor_qualifications where qualification_key='aha-bls-instructor:209806'"],
  ['explicit target revocation',`insert into instructor_qualifications(instructor_id,course_id,qualification_key,status) select lead_instructor_id,course_id,'synthetic-target','revoked' from class_sessions where id='${s.sessionId}'`],
  ['target infinity',`insert into instructor_qualifications(instructor_id,course_id,qualification_key,status,expires_at) select lead_instructor_id,course_id,'synthetic-target','active','infinity' from class_sessions where id='${s.sessionId}'`],
  ['inactive instructor',"update people set active=false where person_key='brian'"],
  ['inactive venue',"update locations set scheduling_status='inactive' where location_key='910cpr-office-shipyard'"],
  ['profile off',"update landerware_registration_profiles set active=false where profile_key='native_heartsaver_351632_draft'"],
  ['profile wrong inventory',"update landerware_registration_profiles set version=version+1,form_schema=jsonb_set(form_schema,'{inventory_kind}','\"leased_skills_v1\"') where profile_key='native_heartsaver_351632_draft'"],
  ['invented customer requirement',"update landerware_registration_profiles set version=version+1,requirements='[{\"key\":\"online_completion\"}]' where profile_key='native_heartsaver_351632_draft'"],
  ['catalog off',"update landerware_registration_catalog set active=false where course_id='351632'"],
  ['catalog wrong price',"update landerware_registration_catalog set unit_amount=9501 where course_id='351632'"],
  ['canonical price drift',"update courses set base_price=1 where enrollware_course_id='351632'"],
  ['canonical profile drift',"update courses set registration_profile_key=null where enrollware_course_id='351632'"],
  ['canonical key drift',"update courses set course_key='unknown-pediatric' where enrollware_course_id='351632'"],
  ['public alias collision',"update landerware_registration_profiles set version=version+1,form_schema=jsonb_set(form_schema,'{public_aliases}','[{\"public_course_id\":\"351632\"}]') where profile_key='native_bls_209806_v1'"],
  ['context alias collision',"update landerware_registration_profiles set version=version+1,form_schema=jsonb_set(form_schema,'{public_aliases}','[{\"public_course_id\":\"351632\",\"context\":\"fake\"}]') where profile_key='native_bls_209806_v1'"],
  ['pediatric aliased as online',"update landerware_registration_profiles set version=version+1,form_schema=jsonb_set(form_schema,'{public_aliases}','[{\"public_course_id\":\"251545\"}]') where profile_key='native_heartsaver_351632_draft'"],
  ['malformed alias array',"update landerware_registration_profiles set version=version+1,form_schema=jsonb_set(form_schema,'{public_aliases}','{}') where profile_key='native_heartsaver_351632_draft'"],
  ['malformed alias element',"update landerware_registration_profiles set version=version+1,form_schema=jsonb_set(form_schema,'{public_aliases}','[null]') where profile_key='native_heartsaver_351632_draft'"],
  ['empty alias object',"update landerware_registration_profiles set version=version+1,form_schema=jsonb_set(form_schema,'{public_aliases}','[{}]') where profile_key='native_heartsaver_351632_draft'"],
  ['capacity over policy',`update class_sessions set max_students=9 where id='${s.sessionId}'`],
  ['instruction drift',`update class_sessions set end_at=end_at-interval '1 minute' where id='${s.sessionId}'`,true],
  ['setup drift',`update class_sessions set consumption_start_at=start_at where id='${s.sessionId}'`,true],
  ['cleanup drift',`update class_sessions set consumption_end_at=end_at where id='${s.sessionId}'`,true],
  ['external identity drift',`update class_sessions set external_course_id='251545' where id='${s.sessionId}'`],
 ];
 for(const [label,change,adopt] of changes){
  await db.exec('begin');await db.exec(change);if(adopt)await adoptPediatricSession(db,s.sessionId);
  assert.equal(await ready(),false,label);
  const seats=await snapshot();assert.equal(seats.pediatricBooking,null,label);assert.equal(seats.holds,base.holds,label);assert.equal(seats.registered,base.registered,label);assert.equal(seats.unreconciledReserved,base.unreconciledReserved,label);
  await db.exec('savepoint wrapper');await assert.rejects(service(db,()=>scalar(db,claimSQL,request(s.external,++n))),/session_not_available|profile_changed|native_profile_not_configured/);await db.exec('rollback to wrapper;reset role');
  await db.exec('savepoint direct');await assert.rejects(service(db,()=>scalar(db,directSQL,directArgs(s.external))),/session_not_available/);await db.exec('rollback to direct;reset role');
  assert.equal((await service(db,()=>scalar(db,claimSQL,initialReq))).orderId,first.orderId,label+': durable replay');
  await db.exec('rollback');
 }
 // Re-reviewed geometry cannot bless an unrouteable external identity.
 await db.exec('begin');await db.query("update class_sessions set external_class_id='unrouteable-test' where id=$1",[s.sessionId]);await adoptPediatricSession(db,s.sessionId);
 assert.equal(await ready(),false);assert.equal((await snapshot()).pediatricBooking,null);
 await db.exec('savepoint malformed');await assert.rejects(service(db,()=>scalar(db,directSQL,directArgs('unrouteable-test'))),/session_not_available/);await db.exec('rollback');
 // Unknown timing, capacity and provenance cannot be enabled by accident.
 for(const edit of ['instruction_minutes=null','setup_minutes=null','cleanup_minutes=null','max_students=null','source_qualification_id=null',"timing_evidence=''","capacity_evidence=''",'verified=false']){
  await db.exec('begin');await assert.rejects(db.exec('update native_pediatric_existing_session_policy set '+edit),/reviewed_pediatric_existing_policy/);await db.exec('rollback');
 }
 // Source exact boundary accepted and no separate Pediatric credential invented.
 await db.exec('begin');await db.query("update instructor_qualifications set expires_at=(select consumption_end_at from class_sessions where id=$1) where qualification_key='aha-bls-instructor:209806'",[s.sessionId]);
 await db.query("insert into instructor_qualifications(instructor_id,course_id,qualification_key,status) select lead_instructor_id,course_id,'synthetic-target','active' from class_sessions where id=$1",[s.sessionId]);assert.equal(await ready(),true);await db.exec('rollback');
 await db.exec('begin');await db.exec("update native_pediatric_existing_session_policy set enabled=false");await assert.rejects(profile(),/native_registration_unavailable/);await db.exec('rollback');
 await assert.rejects(service(db,()=>scalar(db,"select native_checkout_profile('351632','online')")),/native_registration_unavailable/);
 await db.exec('begin');await db.exec("update landerware_registration_profiles set version=version+1,form_schema=jsonb_set(form_schema,'{public_aliases}','[{\"public_course_id\":\"251545\"}]') where profile_key='native_heartsaver_351632_draft'");
 await assert.rejects(service(db,()=>scalar(db,"select native_checkout_profile('251545',null)")),/native_registration_unavailable/);await db.exec('rollback');
 for(const iso of ['repeatable read','serializable']){await db.exec('begin isolation level '+iso);await assert.rejects(service(db,()=>scalar(db,claimSQL,request(s.external,++n))),/native_pediatric_admission_isolation_required/);await db.exec('rollback');}
 // Saved paid order uses existing recovery, independently of current sales policy.
 await db.query("update landerware_public_orders set stripe_checkout_session_id='cs_synthetic_pediatric' where id=$1",[first.orderId]);
 const evidence={id:'cs_synthetic_pediatric',mode:'payment',payment_status:'paid',amount_total:9500,currency:'usd',metadata:{landerware_order_id:first.orderId}};
 await db.exec('update native_pediatric_existing_session_policy set enabled=false');
 // Existing payment fixture ACLs are not an authorization proposal; no real provider call.
 await scalar(db,'select native_checkout_record_payment($1,$2,$3::jsonb)',[first.orderId,'pi_synthetic_pediatric',JSON.stringify(evidence)]);
 const finalize=()=>scalar(db,'select native_checkout_finalize_order($1,$2,$3::jsonb)',[first.orderId,'pi_synthetic_pediatric',JSON.stringify(evidence)]);
 assert.equal((await finalize()).status,'paid');assert.equal((await finalize()).idempotentReplay,true);
 assert.equal((await service(db,()=>scalar(db,claimSQL,initialReq))).orderId,first.orderId);
 const paid=await snapshot();assert.equal(paid.registered,2);assert.equal(paid.holds,0);assert.equal(paid.unreconciledReserved,2);assert.equal(paid.pediatricBooking,null);
 // The new independently disabled policy does not block the existing adult/BLS paths.
 for(const course of ['209809','344085']){const offer=await makeHeartsaverOffer(db,course);assert.equal((await service(db,()=>scalar(db,claimSQL,adultRequest(course,null,offer,++n)))).status,'held');}
 for(const course of ['209806','359474']){const offer=await makeBlsOffer(db,course);offer.validUntil=new Date(Date.now()+600000).toISOString();assert.equal((await service(db,()=>scalar(db,blsSQL,blsRequest(course,null,offer,++n)))).status,'held');}
 }finally{await db.close();}
});
test('Pediatric migration aborts on unknown installed function and invalid canonical identity',async()=>{
 const db=await create();try{
 await setupPediatricAdmission(db,{apply:false});
 const original=await scalar(db,"select pg_get_functiondef('native_checkout_profile(text,text)'::regprocedure)");
 await db.exec(original.replace('begin','begin\n -- Unknown local change'));
 await assert.rejects(db.exec(migration()),/pediatric_native_checkout_profile_source_drift/);await db.exec('rollback');
 assert.equal(await scalar(db,"select to_regclass('native_pediatric_existing_session_policy')"),null);
 await db.exec(original);await db.exec("update courses set enrollware_course_id='251545' where id='0689a2c5-c507-4e8a-b94c-15e5c5689e28'");
 await assert.rejects(db.exec(migration()),/pediatric_canonical_identity_mismatch/);await db.exec('rollback');
 assert.equal(await scalar(db,"select to_regclass('native_pediatric_existing_session_policy')"),null);
 }finally{await db.close();}
});
