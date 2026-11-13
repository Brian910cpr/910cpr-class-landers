import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {preProfileFiles,profileMigration,fullCourseMigration} from './helpers/native-checkout-migration-plan.mjs';
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('advanced proposal installs behind disabled policy with no invented identities, scopes or material prices',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  for(const p of preProfileFiles)await db.exec(load(p));
  await db.exec("insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price) values('aha-bls-provider','Fixture BLS','209806',120,30,6,75),('aha-bls-provider-renewal','Fixture Renewal','359474',120,30,6,75); insert into people(person_key,display_name) values('brian','Brian Ennis'); insert into instructor_qualifications(instructor_id,course_id,status) select p.id,c.id,'active' from people p cross join courses c where p.person_key='brian' and c.enrollware_course_id in ('209806','359474');");
  for(const p of [profileMigration,'supabase/migrations/20261110231103_native_checkout_generated_session_lifecycle.sql',fullCourseMigration,'supabase/migrations/20261111190525_native_full_course_policy_service_access.sql','supabase/migrations/20261111195655_native_full_course_v2_policy.sql'])await db.exec(load(p));
  await db.exec(load('supabase/reviewed/native-advanced-course-checkout.sql'));
  const scalar=async(q,args=[])=>Object.values((await db.query(q,args)).rows[0])[0];
  assert.equal(await scalar('select count(*) from native_advanced_course_policy'),4);
  assert.equal(await scalar('select count(*) from native_advanced_course_policy where enabled or verified or publication_enabled or course_id is not null or setup_minutes is not null or cleanup_minutes is not null or max_students is not null'),0);
  assert.equal(await scalar('select count(*) from native_advanced_instructor_scopes'),0);
  const config=JSON.parse(load('data/config/native_advanced_checkout.json'));
  for(const course of config.courses){
   const profile=await scalar('select to_jsonb(p) from landerware_registration_profiles p where profile_key=$1',[course.profileKey]);
   assert.equal(profile.active,false);assert.equal(profile.listed,false);assert.deepEqual(profile.form_schema,course.formSchema);
   const catalog=await scalar('select to_jsonb(c) from landerware_registration_catalog c where course_id=$1',[course.courseNumber]);
   assert.equal(catalog.active,false);assert.equal(catalog.unit_amount,course.sessionCents);assert.deepEqual(catalog.addons,[]);
  }

  for(const course of ['241108','209818','209805','251496'])assert.equal((await scalar('select native_advanced_course_runtime_policy($1)',[course])).materializationEnabled,false);
  for(const role of ['anon','authenticated']){
   assert.equal(await scalar("select has_table_privilege($1,'native_advanced_offer_leases','SELECT')",[role]),false);
   for(const fn of ['native_publish_advanced_offers(jsonb)','materialize_native_advanced_checkout(text,jsonb)','reserve_native_advanced_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer)'])assert.equal(await scalar('select has_function_privilege($1,$2,\'EXECUTE\')',[role,fn]),false);
  }
  await assert.rejects(scalar('select native_publish_advanced_offers($1::jsonb)',[JSON.stringify([{courseNumber:'241108'}])]),/unverified_advanced_offer/);
  // Explicit disposable mappings/buffers/capacity; never production defaults.
  await db.exec(`insert into landerware_registration_profiles select (jsonb_populate_record(null::landerware_registration_profiles,to_jsonb(p)||'{"profile_key":"fixture_advanced","course_id":"fixture-acls","active":true,"form_schema":{"schemaVersion":"native-checkout.form.v1","inventory_kind":"scheduled_session_v1","fields":[],"max_students":10,"default_choices":[],"option_groups":[],"driver_rules":[{"driver":"native_order"}]}}')).* from landerware_registration_profiles p where profile_key='native_bls_initial';
   insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price,registration_profile_key) values('fixture-acls','Fixture ACLS','241108',240,0,2,225,'fixture_advanced');
   update landerware_registration_catalog set unit_amount=22500,active=true,addons='[]' where course_id='241108';
   insert into instructor_qualifications(instructor_id,course_id,status,expires_at) select p.id,c.id,'active',now()+interval '1 year' from people p cross join courses c where p.person_key='skills-test' and c.course_key='fixture-acls';
   update native_advanced_course_policy set course_id=(select id from courses where course_key='fixture-acls'),profile_key='fixture_advanced',setup_minutes=0,cleanup_minutes=0,max_students=2,location_id=(select id from locations where location_key='910cpr-office-shipyard'),resource_label='FIXTURE ROOM',location_label='FIXTURE LOCATION',enabled=true,publication_enabled=true,verified=true,evidence=evidence||'{"buffers":"LOCAL FIXTURE","capacity":"LOCAL FIXTURE","identity":"LOCAL FIXTURE"}' where course_number='241108';
   insert into native_advanced_instructor_scopes select '241108',id,'fixture-calendar-person',array['fixture-calendar'],true,'LOCAL FIXTURE' from people where person_key='skills-test';`);
  assert.equal((await scalar("select native_advanced_course_runtime_policy('241108')")).materializationEnabled,true);
  const offer=await scalar(`select skills_test.offer('test',10)||jsonb_build_object('authority','native-full-course.v3','nativeScopeId','qualified-advanced-shipyard-b.v1','coursePolicyKey','advanced-full:241108.v1','courseNumber','241108','canonicalCourseId',(select id from courses where course_key='fixture-acls'),'selectionId','native-full:'||repeat('a',64),'instructorId',(select id from people where person_key='skills-test'),'availabilityPersonId','fixture-calendar-person','calendarSourceKey','fixture-calendar','resource','FIXTURE ROOM','location','FIXTURE LOCATION','endsAt',(skills_test.offer('test',10)->>'startsAt')::timestamptz+interval '4 hours','consumptionStartsAt',skills_test.offer('test',10)->>'startsAt','consumptionEndsAt',(skills_test.offer('test',10)->>'startsAt')::timestamptz+interval '4 hours','availabilityStartsAt',skills_test.offer('test',10)->>'startsAt','availabilityEndsAt',(skills_test.offer('test',10)->>'startsAt')::timestamptz+interval '4 hours','proofObservedAt',now())`);
  for(const k of ['context','offerType'])delete offer[k];
  const publish=o=>scalar('select native_publish_advanced_offers($1::jsonb)',[JSON.stringify([o])]);
  const option=o=>scalar("select native_advanced_full_course_option('241108',$1::jsonb)",[JSON.stringify(o)]);
  assert.equal(await option(offer),null,'client offer alone is not publication');
  for(const patch of [{calendarSourceKey:null},{availabilityEndsAt:null},{availabilityStartsAt:null},{calendarSourceKey:'wrong-calendar'}])await assert.rejects(publish({...offer,...patch}),/unverified_advanced_offer/);
  await assert.rejects(publish({...offer,email:'synthetic@example.invalid'}),/invalid_offer_fields/);
  assert.equal(await publish(offer),1);assert.equal((await option(offer)).capacity,2);
  assert.equal(await option({...offer,startsAt:'2030-01-01T00:00:00Z'}),null,'tampered DTO differs from trusted lease');

  await db.exec("insert into locations(location_key,name,scheduling_status) values('fixture-other-room','Distinct fixture venue','active');");
  const commitment=async(id,start,end)=>db.query(`insert into class_sessions(source,status,record_scope,course_id,start_at,end_at,consumption_start_at,consumption_end_at,timezone,location_id,lead_instructor_id,visibility,registration_backend,registration_status,max_students,external_class_id)
   select 'landerware_event','scheduled','operational',c.id,$1,$2,$1,$2,'America/New_York',l.id,p.id,'public','landerware','open',1,$3 from courses c cross join locations l cross join people p where c.course_key='fixture-qualification' and l.location_key='fixture-other-room' and p.person_key='skills-test'`,[start,end,id]);
  const start=Date.parse(offer.startsAt),end=Date.parse(offer.endsAt);
  await commitment('fixture-travel-before',new Date(start-75*60000).toISOString(),new Date(start-30*60000).toISOString());
  assert.equal(await option(offer),null,'missing exact directional travel policy fails closed');
  await db.exec("insert into native_advanced_travel_policy select a.id,b.id,20,true,'EXPLICIT LOCAL FIXTURE ONLY' from locations a cross join locations b where a.location_key='fixture-other-room' and b.location_key='910cpr-office-shipyard'");
  assert.ok(await option(offer));
  await db.exec('update native_advanced_travel_policy set minutes=31');assert.equal(await option(offer),null,'insufficient directional travel gap');
  await db.exec('update native_advanced_travel_policy set minutes=20');
  await commitment('fixture-travel-after',new Date(end+30*60000).toISOString(),new Date(end+75*60000).toISOString());
  assert.equal(await option(offer),null,'forward travel never implies reverse permission');
  await db.exec("insert into native_advanced_travel_policy select b.id,a.id,20,true,'EXPLICIT LOCAL FIXTURE ONLY' from locations a cross join locations b where a.location_key='fixture-other-room' and b.location_key='910cpr-office-shipyard'");
  assert.ok(await option(offer));
  await db.exec("update class_sessions set status='cancelled' where external_class_id in ('fixture-travel-before','fixture-travel-after');delete from native_advanced_travel_policy;");
  const created=await scalar("select materialize_native_advanced_checkout('241108',$1::jsonb)",[JSON.stringify(offer)]);
  const repeated=await scalar("select materialize_native_advanced_checkout('241108',$1::jsonb)",[JSON.stringify(offer)]);
  assert.equal(repeated.targetSessionId,created.targetSessionId);assert.equal(await scalar('select count(*) from class_sessions'),3,'two cancelled fixture commitments retain their identities');
  assert.equal(await scalar('select max_students from class_sessions where id=$1',[created.targetSessionId]),2);
  assert.equal(await scalar('select extract(epoch from end_at-start_at)/60 from class_sessions where id=$1',[created.targetSessionId]),'240.0000000000000000');
  const existingReady=()=>scalar("select native_advanced_existing_session_ready('241108',$1)",[created.externalId]);
  assert.equal(await existingReady(),true);
  for(const file of ['supabase/migrations/20261111185724_native_session_authority_cutover.sql','supabase/migrations/20261111200810_native_scheduling_seat_snapshot.sql','supabase/migrations/20261111200908_native_full_course_lifecycle_hooks.sql','supabase/migrations/20261111202622_native_skills_publication_guard.sql'])await db.exec(load(file));
  const snapshot=()=>scalar('select native_advanced_scheduling_seat_snapshot($1)',[created.targetSessionId]);
  const originalSeats=await scalar('select native_scheduling_seat_snapshot($1)',[created.targetSessionId]);
  const admitted=await snapshot();assert.equal(admitted.advancedBooking.remaining,2);assert.equal(admitted.advancedBooking.publicCourseId,'241108');
  const {advancedBooking,...unchangedSeats}=admitted;assert.deepEqual(unchangedSeats,originalSeats,'additive admission preserves canonical occupancy');
  for(const role of ['anon','authenticated'])assert.equal(await scalar("select has_function_privilege($1,'native_advanced_scheduling_seat_snapshot(uuid)','EXECUTE')",[role]),false);
  assert.equal(await scalar("select provolatile from pg_proc where oid='native_advanced_scheduling_seat_snapshot(uuid)'::regprocedure"),'s');
  const original=await scalar('select to_jsonb(s) from class_sessions s where id=$1',[created.targetSessionId]);
  await db.exec('begin');
  try{
   await commitment('fixture-overlapping-shift',new Date(start+30*60000).toISOString(),new Date(start+12.5*3600000).toISOString());
   assert.equal(await existingReady(),false,'seated checkout cannot bypass a conflicting same-instructor offsite shift');
   assert.equal((await snapshot()).advancedBooking,null,'conflict removes CTA, not canonical occupancy');
   assert.deepEqual(await scalar('select to_jsonb(s) from class_sessions s where id=$1',[created.targetSessionId]),original,'existing class is diagnosed, never moved or canceled');
  }finally{await db.exec('rollback');}
  for(const change of ["update native_advanced_course_policy set publication_enabled=false", "update landerware_registration_profiles set active=false where profile_key='fixture_advanced'", "update native_advanced_course_policy set max_students=1", "update instructor_qualifications set status='revoked' where course_id=(select id from courses where course_key='fixture-acls')"]){
   await db.exec('begin');try{await db.exec(change);const closed=await snapshot();assert.equal(closed.advancedBooking,null);assert.equal(closed.capacity,originalSeats.capacity);assert.equal(closed.registered,originalSeats.registered);}finally{await db.exec('rollback');}
  }
  await db.exec('begin');
  try{
   await commitment('fixture-following-shift',new Date(end+30*60000).toISOString(),new Date(end+12.5*3600000).toISOString());
   assert.equal(await existingReady(),false,'missing directional travel remains closed for existing classes');
   await db.exec("insert into native_advanced_travel_policy select b.id,a.id,31,true,'EXPLICIT LOCAL FIXTURE ONLY' from locations a cross join locations b where a.location_key='fixture-other-room' and b.location_key='910cpr-office-shipyard'");
   assert.equal(await existingReady(),false,'insufficient travel gap is rejected');
   await db.exec('update native_advanced_travel_policy set minutes=20');assert.equal(await existingReady(),true);
  }finally{await db.exec('rollback');}
  await db.exec("update instructor_qualifications set status='revoked' where course_id=(select id from courses where course_key='fixture-acls')");
  assert.equal(await option(offer),null,'qualification revocation invalidates existing published lease');
  assert.equal(await scalar("select native_advanced_existing_session_ready('241108',$1)",[created.externalId]),false,'existing-session checkout also rejects a revoked qualification');

 }finally{await db.close();}
});
