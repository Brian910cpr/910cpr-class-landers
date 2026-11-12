// Disposable local fixtures only. No hosted clients, credentials, mail or payments.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath,pathToFileURL} from 'node:url';
export const sourceRoot=process.env.NATIVE_BLS_SOURCE_ROOT||fileURLToPath(new URL('../',import.meta.url));
const load=p=>readFileSync(sourceRoot+'/'+p,'utf8');
const plan=await import(pathToFileURL(sourceRoot+'/tests/helpers/native-checkout-migration-plan.mjs'));
export const admissionMigration=readFileSync(new URL('../supabase/migrations/20261111224642_native_bls_existing_session_admission.sql',import.meta.url),'utf8');
export const scalar=(db,sql,args=[])=>db.query(sql,args).then(r=>Object.values(r.rows[0]||{})[0]);
export const claimSQL='select reserve_native_checkout_order($1,$2,1,\'\',$3,$4::jsonb,$5::jsonb,$6::jsonb,7500)';
export function request(course,external,offer,n){
 const wire={firstName:'Synthetic',lastName:'Fixture',email:`bls-${course}-${n}@example.invalid`,phone:'2025550100',manualChoice:'own-copy',addons:[]};
 return [`${String(n).padStart(8,'0')}-1111-4111-8111-111111111111`,`native_bls_${course}_v1`,external,JSON.stringify(offer),JSON.stringify([wire]),JSON.stringify([{wire,selectedChoices:['customer_supplied_manual']}])];
}
export async function setupBlsAdmission(db,{full=false,apply=true}={}){
 for(const f of plan.preProfileFiles)await db.exec(load(f));
 await db.exec(`insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price) values
 ('aha-bls-provider','Synthetic BLS','209806',120,0,12,75),('aha-bls-provider-renewal','Synthetic BLS Renewal','359474',120,0,12,75);
 insert into landerware_registration_catalog(course_id,course_name,unit_amount,currency,addons,billing_codes,active) values
 ('209806','Synthetic BLS',7500,'usd','[]','[]',true),('359474','Synthetic BLS Renewal',7500,'usd','[]','[]',true)
 on conflict(course_id) do update set unit_amount=7500,currency='usd',active=true;
 insert into people(person_key,display_name) values('brian','Brian Ennis');
 insert into instructor_qualifications(instructor_id,course_id,qualification_key,status,expires_at)
 select p.id,c.id,'aha-bls-instructor:'||c.enrollware_course_id,'active',now()+interval '2 years' from people p cross join courses c where p.person_key='brian' and c.enrollware_course_id in('209806','359474');
 insert into landerware_confirmation_templates values('native-checkout-profile-v1','Synthetic','Synthetic','cloudflare',false);`);
 for(const f of [plan.profileRuntime,'supabase/migrations/20261110231103_native_checkout_generated_session_lifecycle.sql',plan.fullCourseMigration,
 'supabase/migrations/20261111185535_native_bls_profiles_inactive_unbound.sql','supabase/migrations/20261111185724_native_session_authority_cutover.sql',
 'supabase/migrations/20261111190525_native_full_course_policy_service_access.sql','supabase/migrations/20261111195655_native_full_course_v2_policy.sql',
 'supabase/migrations/20261111200810_native_scheduling_seat_snapshot.sql','supabase/migrations/20261111200908_native_full_course_lifecycle_hooks.sql',
 'supabase/migrations/20261111202622_native_skills_publication_guard.sql','supabase/migrations/20261111204230_native_publication_maintenance.sql'])await db.exec(load(f));
 if(full){
  await db.exec(`insert into courses(id,course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price) values
   ('23dfcfa7-4224-46ed-8d45-64d43d5425db','aha-heartsaver-fa-cpr-aed','Synthetic FA CPR AED','209809',120,0,12,null),
   ('306bc81a-0e09-49e1-8910-e05501222eb4','hist-course:a3d354b88fbc55fd','Synthetic CPR AED','344085',120,0,4,null),
   ('0689a2c5-c507-4e8a-b94c-15e5c5689e28','aha-heartsaver-pediatric-fa-cpr-aed','Synthetic pediatric','351632',180,0,20,null);`);
  for(const f of ['supabase/migrations/20261110201606_native_heartsaver_inperson_drafts_only.sql','supabase/migrations/20261111220000_native_heartsaver_full_course_scopes.sql','supabase/migrations/20261111223000_native_heartsaver_publication.sql'])await db.exec(load(f));
 }
 await db.exec(`update courses set registration_profile_key='native_bls_'||enrollware_course_id||'_v1' where enrollware_course_id in('209806','359474');
 update landerware_registration_profiles set active=true where profile_key in('native_bls_209806_v1','native_bls_359474_v1');
 update native_full_course_policy set enabled=true,verified=true,evidence='LOCAL SYNTHETIC ONLY';
 update native_full_course_public_policy set enabled=true,publication_enabled=true,verified=true,evidence='LOCAL SYNTHETIC ONLY';`);
 await db.exec(load('tests/helpers/native-full-service-role-acl.sql'));
 // Measured hosted reader/update rights omitted by disposable schema fixture.
 await db.exec('grant select,update on landerware_registration_profiles,landerware_registration_catalog to service_role;grant select on customers to service_role;');
 if(apply){
  const untouchedSQL="select p.oid::regprocedure::text as signature,md5(p.prosrc) as body from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname not in('native_checkout_create_order','native_scheduling_seat_snapshot','native_bls_session_booking_ready','native_bls_lock_booking_dependencies') order by 1";
  const rowsBefore=(await db.query(untouchedSQL)).rows;
  const policySQL="select jsonb_build_object('base',(select jsonb_agg(to_jsonb(t)) from native_full_course_policy t),'scope',(select jsonb_agg(to_jsonb(t)) from native_full_course_public_policy t),'profiles',(select jsonb_agg(to_jsonb(t) order by profile_key) from landerware_registration_profiles t),'catalog',(select jsonb_agg(to_jsonb(t) order by course_id) from landerware_registration_catalog t))";
  const stateBefore=await scalar(db,policySQL);
  await db.exec(admissionMigration);
  assert.deepEqual((await db.query(untouchedSQL)).rows,rowsBefore,'all existing functions except creator/snapshot unchanged');
  assert.deepEqual(await scalar(db,policySQL),stateBefore,'no activation/binding/catalog/policy changes');
 }
 return {full};
}
export async function makeBlsOffer(db,course,day=course==='209806'?40:41){
 return scalar(db,"select skills_test.offer('bls-admission',$1)||jsonb_build_object('authority','native-full-course.v2','proofObservedAt',now(),'nativeScopeId','brian-shipyard-b.v1','courseNumber',$2::text,'instructor','Brian Ennis','selectionId','native-full:'||encode(sha256(convert_to($2::text||$1::text,'UTF8')),'hex'),'endsAt',(skills_test.offer('bls-admission',$1)->>'startsAt')::timestamptz+interval '120 minutes','consumptionEndsAt',(skills_test.offer('bls-admission',$1)->>'startsAt')::timestamptz+interval '150 minutes')",[day,course]);
}
export async function service(db,fn){await db.exec('set role service_role');try{return await fn();}finally{try{await db.exec('reset role');}catch{}}}
export async function proveBlsAdmission(db,{full=false}={}){
 await setupBlsAdmission(db,{full});let n=100;
 assert.deepEqual((await db.query("select rolsuper,rolbypassrls from pg_roles where rolname='service_role'")).rows[0],{rolsuper:false,rolbypassrls:true});
 assert.equal(await scalar(db,"select provolatile from pg_proc where oid='native_scheduling_seat_snapshot(uuid)'::regprocedure"),'s');
 for(const fn of ['native_bls_session_booking_ready(class_sessions)','native_bls_lock_booking_dependencies()']){
  assert.equal(await scalar(db,'select prosecdef from pg_proc where oid=$1::regprocedure',[fn]),false);
  for(const role of ['anon','authenticated'])assert.equal(await scalar(db,"select has_function_privilege($1,$2,'execute')",[role,fn]),false);
 }
 for(const course of ['209806','359474']){
  const offer=await makeBlsOffer(db,course),firstReq=request(course,null,offer,++n);
  const first=await service(db,()=>scalar(db,claimSQL,firstReq));assert.equal(first.status,'held');
  const external=await scalar(db,'select external_class_id from class_sessions where id=$1',[first.sessionId]);
  const snapshot=()=>scalar(db,'select native_scheduling_seat_snapshot($1)',[first.sessionId]);
  const baseline=await snapshot();assert.equal(baseline.publicBooking.remaining,5);
  const changes=[
   ['revoked',`update instructor_qualifications set status='revoked' where qualification_key='aha-bls-instructor:${course}'`],
   ['expiry',`update instructor_qualifications set expires_at=now()+interval '1 day' where qualification_key='aha-bls-instructor:${course}'`],
   ['cleanup_expiry',`update instructor_qualifications set expires_at=(select end_at from class_sessions where id='${first.sessionId}') where qualification_key='aha-bls-instructor:${course}'`],
   ['unknown_expiry',`update instructor_qualifications set expires_at=null where qualification_key='aha-bls-instructor:${course}'`],
   ['wrong_key',`update instructor_qualifications set qualification_key='skills-session-policy.v1' where qualification_key='aha-bls-instructor:${course}'`],
   ['base_disabled',"update native_full_course_policy set enabled=false"],
   ['base_unverified',"update native_full_course_policy set verified=false"],
   ['base_no_evidence',"update native_full_course_policy set evidence=''"],
   ['scope_disabled',"update native_full_course_public_policy set enabled=false"],
   ['publication_disabled',"update native_full_course_public_policy set publication_enabled=false"],
   ['scope_unverified',"update native_full_course_public_policy set verified=false"],
   ['scope_no_evidence',"update native_full_course_public_policy set evidence=''"],
   ['canonical_cap_lowered',`update courses set max_students_default=4 where enrollware_course_id='${course}'`],
   ['unknown_resource',`update class_sessions set resource_id='ffffffff-1111-4111-8111-111111111111' where id='${first.sessionId}'`],
   ['session_over_capacity',`update class_sessions set max_students=7 where id='${first.sessionId}'`],
   ['instruction_drift',`update class_sessions set end_at=end_at-interval '1 minute' where id='${first.sessionId}'`],
   ['cleanup_drift',`update class_sessions set consumption_end_at=consumption_end_at-interval '1 minute' where id='${first.sessionId}'`],
   ['expiry_one_microsecond',`update instructor_qualifications set expires_at=(select consumption_end_at-interval '1 microsecond' from class_sessions where id='${first.sessionId}') where qualification_key='aha-bls-instructor:${course}'`],
   ['instructor_inactive',"update people set active=false where person_key='brian'"],
   ['venue_inactive',"update locations set scheduling_status='inactive' where location_key='910cpr-office-shipyard'"],
   ['profile_disabled',`update landerware_registration_profiles set active=false where profile_key='native_bls_${course}_v1'`],
   ['catalog_disabled',`update landerware_registration_catalog set active=false where course_id='${course}'`],
   ['price_mismatch',`update landerware_registration_catalog set unit_amount=7600 where course_id='${course}'`],
   ['inserted_revocation',`insert into instructor_qualifications(instructor_id,course_id,qualification_key,status,expires_at) select instructor_id,course_id,qualification_key,'revoked',expires_at from instructor_qualifications where qualification_key='aha-bls-instructor:${course}'`],
  ];
  for(const [label,change] of changes){
   await db.exec('begin');await db.exec(change);
   // Represent a deliberately reviewed/adopted manual identity, not a broken
   // generated witness, so geometry/resource cases exercise the admission gate.
   if(['unknown_resource','session_over_capacity','instruction_drift','cleanup_drift'].includes(label)){
    await db.query("update class_sessions set external_reconciliation=jsonb_build_object('complete',true,'active_external_registration_ids','[]'::jsonb,'active_registration_count',0,'source_observed_at',now()) where id=$1",[first.sessionId]);
    const proof=await scalar(db,'select native_session_authority_snapshot($1)',[first.sessionId]);
    await scalar(db,'select native_session_authority_record($1,gen_random_uuid(),$2,$3,true)',[first.sessionId,proof.fingerprint,proof.revision]);
   }
   const changed=await scalar(db,'select landerware_public_seat_state($1)',[first.sessionId]);
   const blocked=await service(db,snapshot);assert.equal(blocked.publicBooking,null,label);
   assert.equal(blocked.registered,changed.registered,label);assert.equal(blocked.holds,changed.holds,label);
   for(const key of ['registered','holds'])assert.deepEqual(blocked[key],baseline[key],label+': occupancy');
   await assert.rejects(service(db,()=>scalar(db,claimSQL,request(course,external,{},++n))),/session_not_available|profile_changed|price_catalog_missing|session_not_native/);
   await db.exec('rollback');
   // A separate transaction proves original durable replay despite disabled policy.
   await db.exec('begin');await db.exec(change);
   assert.equal((await service(db,()=>scalar(db,claimSQL,firstReq))).orderId,first.orderId,label+': replay');
   await db.exec('rollback');
  }
  // Malformed/unknown qualification also cannot create the first dynamic order.
  for(const patch of ["qualification_key='wrong'",'expires_at=null']){
   const counts=()=>scalar(db,"select jsonb_build_array((select count(*) from class_sessions),(select count(*) from landerware_public_orders))");
   const before=await counts();
   await db.exec('begin');await db.exec(`update instructor_qualifications set ${patch} where qualification_key='aha-bls-instructor:${course}'`);
   const invalidOffer=await makeBlsOffer(db,course,course==='209806'?60:61);
   await assert.rejects(service(db,()=>scalar(db,claimSQL,request(course,null,invalidOffer,++n))),/session_not_available/);
   await db.exec('rollback');assert.deepEqual(await counts(),before,'rejected dynamic claim leaves no session or order');
  }
  await db.exec('begin');
  await db.exec(`update instructor_qualifications set expires_at=(select consumption_end_at from class_sessions where id='${first.sessionId}') where qualification_key='aha-bls-instructor:${course}';update class_sessions set max_students=4 where id='${first.sessionId}';`);
  assert.equal(await scalar(db,'select native_bls_session_booking_ready(s) from class_sessions s where id=$1',[first.sessionId]),true,'exact expiry boundary and lower staff cap accepted');
  await db.exec('rollback');
  await db.exec('begin');
  const alias=course==='209806'?'native_bls_initial':'native_bls_renewal';
  await db.query("insert into landerware_registration_profiles select (jsonb_populate_record(null::landerware_registration_profiles,to_jsonb(p)||jsonb_build_object('profile_key',$1::text))).* from landerware_registration_profiles p where profile_key=$2",[alias,'native_bls_'+course+'_v1']);
  await db.query('update courses set registration_profile_key=$1 where enrollware_course_id=$2',[alias,course]);
  const compatible=request(course,external,{},++n);compatible[1]=alias;
  assert.equal((await service(db,()=>scalar(db,claimSQL,compatible))).sessionId,first.sessionId,'legitimate legacy profile keys accepted');
  await db.exec('rollback');
  const second=await service(db,()=>scalar(db,claimSQL,request(course,external,{},++n)));assert.equal(second.sessionId,first.sessionId);assert.equal((await snapshot()).remaining,4);
  // Policy revocation must not block a previously committed payment callback.
  await db.query("update landerware_public_orders set stripe_checkout_session_id=$2 where id=$1",[first.orderId,'cs_bls_'+course]);
  const evidence={id:'cs_bls_'+course,mode:'payment',payment_status:'paid',amount_total:7500,currency:'usd',metadata:{landerware_order_id:first.orderId}};
  await db.exec('update native_full_course_public_policy set enabled=false');
  // Callback behavior regression only: this fixture does not model every
  // existing fulfillment-table service ACL. Admissions above use service_role.
  await scalar(db,'select native_checkout_record_payment($1,$2,$3::jsonb)',[first.orderId,'pi_bls_'+course,JSON.stringify(evidence)]);
  const finalize=()=>scalar(db,'select native_checkout_finalize_order($1,$2,$3::jsonb)',[first.orderId,'pi_bls_'+course,JSON.stringify(evidence)]);
  assert.equal((await finalize()).status,'paid');assert.equal((await finalize()).idempotentReplay,true);
  const paid=await snapshot();assert.equal(paid.registered,1);assert.equal(paid.holds,1);assert.equal(paid.publicBooking,null);
  await db.exec('begin');
  await db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 day',payment_evidence='{\"payment_status\":\"paid\",\"seat_hold_protected\":\"true\"}' where id=$1",[second.orderId]);
  assert.equal((await snapshot()).holds,1,'protected paid liability retained after ordinary hold expiry');
  await db.exec('rollback');
  await db.exec('update native_full_course_public_policy set enabled=true');
  await db.exec('begin isolation level repeatable read');
  await assert.rejects(service(db,()=>scalar(db,claimSQL,request(course,external,{},++n))),/native_bls_admission_isolation_required/);await db.exec('rollback');
 }
 console.log(`PASS ${full?'full':'BLS-only'} chain: service-role fresh/dynamic/concrete admissions,48 revocation/config cases, occupancy retention, nonce replay, paid callback, isolation and ACLs`);
}
