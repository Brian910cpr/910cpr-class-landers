// Disposable synthetic database proof only. No network, payments or mail sends.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {preProfileFiles,profileMigration,fullCourseMigration} from './helpers/native-checkout-migration-plan.mjs';
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8').replaceAll('\r\n','\n');
const migration='supabase/migrations/20261111220000_native_heartsaver_full_course_scopes.sql';
const ids={'209809':'23dfcfa7-4224-46ed-8d45-64d43d5425db','344085':'306bc81a-0e09-49e1-8910-e05501222eb4'};
export async function proveHeartsaverScopes(db,race=null){
  for(const f of preProfileFiles)await db.exec(load(f));
  await db.exec(`insert into courses(id,course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price) values
   ('23dfcfa7-4224-46ed-8d45-64d43d5425db','aha-heartsaver-fa-cpr-aed','Synthetic FA CPR AED','209809',120,0,12,null),
   ('306bc81a-0e09-49e1-8910-e05501222eb4','hist-course:a3d354b88fbc55fd','Synthetic CPR AED','344085',120,0,4,null),
   ('0689a2c5-c507-4e8a-b94c-15e5c5689e28','aha-heartsaver-pediatric-fa-cpr-aed','Synthetic pediatric','351632',180,0,20,null);
   insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price) values ('aha-bls-provider','Synthetic BLS','209806',120,0,12,75),('aha-bls-provider-renewal','Synthetic Renewal','359474',120,0,12,75);
   insert into people(person_key,display_name) values('brian','Brian Ennis');
   insert into instructor_qualifications(id,instructor_id,course_id,qualification_key,status,expires_at)
   select '11111111-1111-4111-8111-111111111111',p.id,c.id,'aha-bls-instructor:209806','active',now()+interval '2 years' from people p cross join courses c where p.person_key='brian' and c.enrollware_course_id='209806';`);
  for(const f of [profileMigration,'supabase/migrations/20261110201606_native_heartsaver_inperson_drafts_only.sql','supabase/migrations/20261110231103_native_checkout_generated_session_lifecycle.sql',fullCourseMigration,'supabase/migrations/20261111190525_native_full_course_policy_service_access.sql','supabase/migrations/20261111195655_native_full_course_v2_policy.sql','supabase/migrations/20261111185724_native_session_authority_cutover.sql','supabase/migrations/20261111200810_native_scheduling_seat_snapshot.sql','supabase/migrations/20261111200908_native_full_course_lifecycle_hooks.sql','supabase/migrations/20261111202622_native_skills_publication_guard.sql'])await db.exec(load(f));
  await db.exec("update landerware_registration_catalog set active=true where course_id='209809'");
  const scalar=async(sql,args=[])=>Object.values((await db.query(sql,args)).rows[0])[0];
  const state=()=>scalar(`select jsonb_build_object('courses',(select jsonb_agg(to_jsonb(c) order by id) from courses c),'catalog',(select jsonb_agg(to_jsonb(c) order by course_id) from landerware_registration_catalog c where course_id<>'344085'),'sessions',(select coalesce(jsonb_agg(to_jsonb(s) order by id),'[]') from class_sessions s),'profiles',(select jsonb_agg(to_jsonb(p) order by profile_key) from landerware_registration_profiles p where profile_key<>'native_heartsaver_344085_draft'),'qualifications',(select jsonb_agg(to_jsonb(q) order by id) from instructor_qualifications q),'orders',(select coalesce(jsonb_agg(to_jsonb(o) order by id),'[]') from landerware_public_orders o))`);
  const untouched=['native_checkout_create_order(text,text,text,text,text,jsonb,text,jsonb)','native_scheduling_seat_snapshot(uuid)','native_checkout_unresolved_payment(landerware_public_orders)','native_checkout_release_abandoned(timestamp with time zone,timestamp with time zone)'];
  const definitions=async()=>Promise.all(untouched.map(fn=>scalar('select pg_get_functiondef($1::regprocedure)',[fn])));
  const preserved=await definitions(),before=await state(),optionDefinition=await scalar("select pg_get_functiondef('native_full_course_option(text,jsonb)'::regprocedure)");
  await db.exec(optionDefinition.replace('begin\n','begin\n -- Independent deployment change\n'));
  await assert.rejects(db.exec(load(migration)),/native_full_course_option_heartsaver_source_drift/);await db.exec('rollback');
  assert.equal(await scalar("select to_regclass('native_heartsaver_full_course_policy')"),null,'drift is atomic');
  await db.exec(optionDefinition.replaceAll('\n','\r\n'));
  await db.exec(load(migration));assert.deepEqual(await state(),before,'no canonical, commercial, qualification or existing-profile edits');assert.deepEqual(await definitions(),preserved);
  assert.equal(await scalar("select count(*) from courses where enrollware_course_id in('209809','344085')"),2);
  assert.deepEqual(await scalar("select jsonb_agg(jsonb_build_array(public_course_id,max_students,unit_amount,enabled,publication_enabled,source_qualification_id) order by public_course_id) from native_heartsaver_full_course_policy"),[['209809',null,9500,false,false,null],['344085',null,7000,false,false,null]]);
  assert.equal(await scalar("select active from landerware_registration_profiles where profile_key='native_heartsaver_344085_draft'"),false);
  assert.deepEqual(await scalar("select jsonb_build_array(unit_amount,active) from landerware_registration_catalog where course_id='344085'"),[7000,false],'verified current first-party price is drafted, never activated');
  await assert.rejects(db.exec("update native_heartsaver_full_course_policy set enabled=true,verified=true,evidence='LOCAL FIXTURE ONLY'"),/reviewed_heartsaver_full_scope/);
  for(const role of ['anon','authenticated']){
   assert.equal(await scalar("select has_table_privilege($1,'native_heartsaver_full_course_policy','SELECT')",[role]),false);
   for(const fn of ['native_heartsaver_full_course_ready(text,timestamptz)','native_full_course_runtime_policy(text)'])assert.equal(await scalar("select has_function_privilege($1,$2,'EXECUTE')",[role,fn]),false);
  }
  assert.deepEqual(await scalar("select native_full_course_runtime_policy('209806')"),await scalar('select native_full_course_runtime_policy()'));
  for(const course of ['209809','344085','329495','209808'])assert.equal((await scalar('select native_full_course_runtime_policy($1)',[course])).materializationEnabled,false);
  // Deliberately synthetic prices/caps. These are not business approval or defaults.
  await db.exec(`update courses set registration_profile_key='native_heartsaver_209809_draft',base_price=95 where enrollware_course_id='209809';
   update courses set registration_profile_key='native_heartsaver_344085_draft',base_price=33.33 where enrollware_course_id='344085';
   update landerware_registration_profiles set active=true where profile_key in ('native_heartsaver_209809_draft','native_heartsaver_344085_draft');
   update landerware_registration_catalog set unit_amount=3333,active=true where course_id='344085';`);
  assert.equal(await scalar("select native_heartsaver_full_course_ready('209809')"),false,'active profile/catalog cannot bypass missing policy');
  await assert.rejects(scalar("select native_checkout_profile('209809',null)"),/native_registration_unavailable/);
  await db.exec(`update native_heartsaver_full_course_policy set max_students=case public_course_id when '209809' then 2 else 3 end,
   unit_amount=case public_course_id when '209809' then 9500 else 3333 end,capacity_evidence='LOCAL FIXTURE ONLY',price_evidence='LOCAL FIXTURE ONLY',
   source_qualification_id='11111111-1111-4111-8111-111111111111',enabled=true,verified=true,evidence='LOCAL FIXTURE ONLY';`);
  assert.equal(await scalar('select count(*) from native_heartsaver_full_course_policy where instructor_manual_evidence is null'),2);
  for(const course of ['209809','344085'])assert.equal(await scalar('select native_heartsaver_full_course_ready($1)',[course]),true,'manual documentation is informational, not a registration prerequisite');
  assert.equal((await scalar("select native_full_course_runtime_policy('344085')")).nativePublicationEnabled,false);
  const makeOffer=async(course,day=40)=>scalar(`select skills_test.offer('synthetic-full',$1)||jsonb_build_object('authority','native-full-course.v2','proofObservedAt',now(),'nativeScopeId','brian-shipyard-b.v1','courseNumber',$2::text,'coursePolicyKey','heartsaver-full:'||$2::text||'.v1','instructor','Brian Ennis','selectionId','native-full:'||encode(sha256(convert_to($2::text||':'||$1::text,'UTF8')),'hex'),'endsAt',(skills_test.offer('synthetic-full',$1)->>'startsAt')::timestamptz+make_interval(mins=>case when $2='344085' then 90 else 120 end),'consumptionEndsAt',(skills_test.offer('synthetic-full',$1)->>'startsAt')::timestamptz+make_interval(mins=>case when $2='344085' then 105 else 150 end))`,[day,course]);
  let offer=await makeOffer('344085');const opt=(o=offer,c='344085')=>scalar('select native_full_course_option($1,$2::jsonb)',[c,JSON.stringify(o)]);
  assert.equal(await opt(),null);await db.exec('update native_heartsaver_full_course_policy set publication_enabled=true');
  assert.equal((await opt()).capacity,3,'explicit scoped capacity, not BLS six or canonical four');
  assert.equal((await opt(await makeOffer('209809'),'209809')).capacity,2);
  assert.equal(await scalar("select enabled from native_full_course_policy where policy_key='bls-full'"),false,'Heartsaver independent of BLS sell switch');
  for(const patch of [{coursePolicyKey:null},{authority:'native-full-course.v1'},{appointmentDayId:'123'},{endsAt:new Date(Date.parse(offer.startsAt)+120*60000).toISOString()},{consumptionEndsAt:new Date(Date.parse(offer.startsAt)+150*60000).toISOString()},{courseNumber:'209808'},{proofObservedAt:new Date(Date.now()-16*60000).toISOString()}])assert.equal(await opt({...offer,...patch}),null,JSON.stringify(patch));
  await db.exec("update instructor_qualifications set qualification_key='skills-session-policy.v1' where id='11111111-1111-4111-8111-111111111111'");assert.equal(await opt(),null,'wrong credential provenance cannot qualify this full course');
  await db.exec("update instructor_qualifications set qualification_key='aha-bls-instructor:209806' where id='11111111-1111-4111-8111-111111111111'");
  await db.exec("update instructor_qualifications set status='revoked' where id='11111111-1111-4111-8111-111111111111'");assert.equal(await opt(),null);
  await db.exec("update instructor_qualifications set status='active',expires_at=now()+interval '1 day' where id='11111111-1111-4111-8111-111111111111'");assert.equal(await opt(),null,'source credential expires before class');
  await db.exec("update instructor_qualifications set expires_at=now()+interval '2 years' where id='11111111-1111-4111-8111-111111111111'; insert into instructor_qualifications(instructor_id,course_id,status) select id,'306bc81a-0e09-49e1-8910-e05501222eb4','revoked' from people where person_key='brian'");assert.equal(await opt(),null,'explicit target revocation wins');
  await db.exec("delete from instructor_qualifications where course_id='306bc81a-0e09-49e1-8910-e05501222eb4'");
  await db.exec("update landerware_registration_catalog set unit_amount=7500 where course_id='344085'");assert.equal(await opt(),null,'catalog drift is not silently BLS-priced');await db.exec("update landerware_registration_catalog set unit_amount=3333 where course_id='344085'");
  await db.exec(load('tests/helpers/native-full-service-role-acl.sql'));
  // Local profile fixture omits the existing profile reader's grants.
  await db.exec('grant select on landerware_registration_profiles to service_role');
  // FOR SHARE row locks require UPDATE in addition to SELECT. These are
  // local fixture grants only; no production grant is proposed by this migration.
  await db.exec('grant update on landerware_registration_catalog,landerware_registration_profiles to service_role');
  await db.exec('set role service_role');assert.equal((await opt()).capacity,3);
  const serviceCreated=await scalar("select materialize_native_full_checkout('344085',$1::jsonb,'service-fixture')",[JSON.stringify(offer)]);
  assert.ok(serviceCreated.targetSessionId);await db.exec('reset role');
  const student={firstName:'Synthetic',lastName:'Fixture',email:'synthetic@example.invalid',phone:'2025550100',addons:[]},inputs=[{wire:student,selectedChoices:[]}];
  const claim=(key,c='344085',o=offer)=>scalar("select reserve_native_checkout_order($1,$2,1,'',null,$3::jsonb,$4::jsonb,$5::jsonb,$6)",[key,`native_heartsaver_${c}_draft`,JSON.stringify(o),JSON.stringify([student]),JSON.stringify(inputs),c==='344085'?3333:9500]);
  // The production service role already has this SELECT; the local schema fixture omits it.
  await db.exec('grant select on public.customers to service_role');
  await db.exec('set role service_role');
  assert.equal(await scalar('select current_user'),'service_role');
  assert.equal(await scalar('select rolsuper from pg_roles where rolname=current_user'),false);
  const key='12121212-1212-4212-8212-121212121212',created=await claim(key);assert.equal(created.amountCents,3333);
  await db.exec('reset role');
  assert.equal((await claim(key)).orderId,created.orderId);
  const session=await scalar('select to_jsonb(s) from class_sessions s where id=$1',[created.sessionId]);
  assert.equal(session.course_id,ids['344085']);assert.equal(session.max_students,3);assert.equal(session.advertised_duration_minutes,90);assert.equal(Number(session.price),33.33);assert.match(session.registration_url,/^\/heartsaver.html/);
  assert.equal(await scalar('select count(*) from native_checkout_generated_sessions'),1,'same lifecycle witness');
  assert.equal(await opt(await makeOffer('209809'),'209809'),null,'cross-course same instructor/room conflict remains');
  const legacy=await scalar(`insert into class_sessions(source,status,record_scope,course_id,start_at,end_at,consumption_start_at,consumption_end_at,timezone,location_id,lead_instructor_id,visibility,registration_backend,registration_status,max_students,external_class_id)
   select 'enrollware','scheduled','operational','23dfcfa7-4224-46ed-8d45-64d43d5425db',$1::timestamptz,$2::timestamptz,$1::timestamptz,$3::timestamptz,'America/New_York',location_id,lead_instructor_id,'unlisted','enrollware','external',20,'synthetic-legacy' from class_sessions where id=$4 returning id`,[(await makeOffer('209809',41)).startsAt,(await makeOffer('209809',41)).endsAt,(await makeOffer('209809',41)).consumptionEndsAt,created.sessionId]);
  assert.equal(await opt(await makeOffer('209809',41),'209809'),null,'unknown legacy occupancy is not zero or adoptable');
  assert.equal(await scalar('select max_students from class_sessions where id=$1',[legacy]),20);
  await db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id=$1",[created.orderId]);
  assert.equal(await scalar('select native_checkout_release_abandoned($1,$2)',[offer.startsAt,offer.consumptionEndsAt]),1);
  const renewed=await claim('13131313-1313-4313-8313-131313131313');assert.equal(renewed.sessionId,created.sessionId,'cleanup lease reuses identity');
  await db.query("update landerware_public_orders set status='expired',hold_expires_at=now()-interval '1 minute',payment_evidence='{\"payment_status\":\"paid\"}',reconciliation_error='synthetic late finalization' where id=$1",[renewed.orderId]);
  assert.equal(await opt(),null,'late-paid unresolved liability suppresses the stale dynamic option');
  const snapshot=await scalar('select native_scheduling_seat_snapshot($1)',[created.sessionId]);assert.equal(snapshot.holds,1);assert.equal(snapshot.remaining,2);assert.equal(snapshot.publicBooking,null);
  await assert.rejects(claim('14141414-1414-4414-8414-141414141414'),/session_not_available/);
  // A separate FA+CPR/AED purchase settles through the unchanged canonical
  // payment/finalizer/message data path. Synthetic processor evidence, no send.
  const faOffer=await makeOffer('209809',42),paid=await claim('15151515-1515-4515-8515-151515151515','209809',faOffer);
  assert.equal(paid.amountCents,9500);
  await db.query("update landerware_public_orders set stripe_checkout_session_id='cs_heartsaver_fixture' where id=$1",[paid.orderId]);
  const evidence={id:'cs_heartsaver_fixture',mode:'payment',payment_status:'paid',amount_total:9500,currency:'usd',metadata:{landerware_order_id:paid.orderId}};
  await scalar("select native_checkout_record_payment($1,'pi_heartsaver_fixture',$2::jsonb)",[paid.orderId,JSON.stringify(evidence)]);
  const finalize=()=>scalar("select native_checkout_finalize_order($1,'pi_heartsaver_fixture',$2::jsonb)",[paid.orderId,JSON.stringify(evidence)]);
  assert.equal((await finalize()).status,'paid');assert.equal((await finalize()).idempotentReplay,true);
  const message=await scalar("select id from landerware_messages where idempotency_key='public-order-paid:'||$1||':synthetic@example.invalid'",[paid.orderId]);
  assert.ok(message);
  const confirmation=await scalar('select landerware_checkout_email_data($1)',[message]);
  assert.equal(confirmation.courseId,'209809');assert.equal(confirmation.course,'Synthetic FA CPR AED');
  assert.equal(await scalar('select count(*) from registrations where class_session_id=$1',[paid.sessionId]),1);
  assert.equal(await scalar('select enabled from landerware_checkout_delivery_config'),false,'no sender activation');
  // Exercise BLS on the post-extension functions, not only the old test install.
  await db.exec("update native_full_course_policy set enabled=true,verified=true,evidence='LOCAL FIXTURE ONLY'; update native_full_course_public_policy set enabled=true,publication_enabled=true,verified=true,evidence='LOCAL FIXTURE ONLY'");
  const blsOffer={...await makeOffer('209809',60),courseNumber:'209806',selectionId:'native-full:'+'c'.repeat(64)};delete blsOffer.coursePolicyKey;
  assert.equal((await opt(blsOffer,'209806')).capacity,6);
  const bls=await scalar("select materialize_native_full_checkout('209806',$1::jsonb,'synthetic-bls')",[JSON.stringify(blsOffer)]);
  const blsSession=await scalar('select to_jsonb(s) from class_sessions s where id=$1',[bls.targetSessionId]);
  assert.equal(blsSession.advertised_duration_minutes,120);assert.equal(blsSession.max_students,6);assert.equal(Number(blsSession.price),75);assert.match(blsSession.registration_url,/^\/bls.html/);
  if(race)await race({offer:await makeOffer('344085',55),faOffer:await makeOffer('209809',55),nextOffer:await makeOffer('344085',56)});
  await db.exec('update native_heartsaver_full_course_policy set enabled=false');
  assert.equal((await claim('13131313-1313-4313-8313-131313131313')).orderId,renewed.orderId,'existing nonce recovery survives disabled scope');
  assert.deepEqual(await definitions(),preserved,'shared confirmation/payment/lifecycle implementations were never replaced');
}
