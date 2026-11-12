import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const {loadEndpoint}=createRequire(import.meta.url)('./helpers/canonical_demand_endpoint.cjs');
import {preProfileFiles,profileRuntime,fullCourseMigration} from './helpers/native-checkout-migration-plan.mjs';
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const migration='supabase/migrations/20261111202622_native_skills_publication_guard.sql';
test('native skills SQL guard preserves installed safeguards and defaults off without catalog/profile activation',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  for(const f of preProfileFiles)await db.exec(load(f));
  for(const f of [profileRuntime,fullCourseMigration,'supabase/migrations/20261110231103_native_checkout_generated_session_lifecycle.sql'])await db.exec(load(f));
  await db.exec("insert into landerware_confirmation_templates(template_key,subject_template,body_template,delivery_provider,active) values('native-checkout-profile-v1','Fixture only','Fixture only','cloudflare',false)");
  await db.exec(load('supabase/migrations/20261110213818_native_plain_skills_profile_draft_only.sql'));
  // Historical bundle fixture seeds an active catalog. Model the current inactive
  // baseline explicitly before checking this migration leaves it untouched.
  await db.exec("update landerware_registration_catalog set active=false where course_id='509474'");
  await db.exec(load('supabase/migrations/20261111185724_native_session_authority_cutover.sql'));
  await db.exec(load('supabase/migrations/20261111200810_native_scheduling_seat_snapshot.sql'));
  const scalar=async(sql,args=[])=>Object.values((await db.query(sql,args)).rows[0])[0];
  const snapshot=()=>scalar("select jsonb_build_object('courses',(select jsonb_agg(to_jsonb(c) order by id) from courses c),'sessions',(select coalesce(jsonb_agg(to_jsonb(s) order by id),'[]') from class_sessions s),'catalog',(select jsonb_agg(to_jsonb(c) order by course_id) from landerware_registration_catalog c),'profiles',(select jsonb_agg(to_jsonb(p) order by profile_key) from landerware_registration_profiles p),'contexts',(select jsonb_agg(to_jsonb(c) order by context_key) from skills_session_context_config c),'qualifications',(select jsonb_agg(to_jsonb(q) order by id) from instructor_qualifications q))");
  const installed=await scalar("select pg_get_functiondef('public.skills_session_native_option(text,jsonb)'::regprocedure)");
  assert.match(installed,/native_paid_hold_reader_v1/);assert.match(installed,/native_checkout_generated_reusable/);
  await db.exec(installed.replace('begin\n','begin\n -- Independent deployment change\n'));
  await assert.rejects(db.exec(load(migration)),/skills_session_native_option_source_drift/);await db.exec('rollback');
  assert.equal(await scalar("select to_regclass('public.native_skills_publication_policy')"),null);
  await db.exec(installed.replaceAll('\n','\r\n'));
  const before=await snapshot();await db.exec(load(migration));assert.deepEqual(await snapshot(),before);
  const after=await scalar("select pg_get_functiondef('public.skills_session_native_option(text,jsonb)'::regprocedure)");
  for(const marker of ['native_paid_hold_reader_v1','native_checkout_generated_reusable','public_registration_closure_policy','instructor_qualifications','registration_reschedule_blocks'])assert.ok(after.includes(marker),marker);
  for(const fn of ['native_skills_publication_runtime_policy()','native_skills_publication_offer_valid(text,jsonb)'])for(const role of ['anon','authenticated'])assert.equal(await scalar('select has_function_privilege($1,$2,\'EXECUTE\')',[role,'public.'+fn]),false);
  await db.exec('set role service_role');assert.deepEqual(await scalar('select native_skills_publication_runtime_policy()'),{nativePublicationEnabled:false,nativeScopeId:'brian-shipyard-b.v1'});await db.exec('reset role');
  const offer=await scalar("select skills_test.offer('native-fixture',40)||jsonb_build_object('authority','native-skills-publication.v1','nativeScopeId','brian-shipyard-b.v1','nativeOfferId','native-skills:'||repeat('a',64),'selectionId','skills:native-skills:'||repeat('a',64)||':cpr-aed','proofObservedAt',now(),'qualificationPolicy','skills-session-policy.v1','capacity',2,'instructor','Brian Ennis')");
  const opt=(o=offer,c='cpr-aed')=>scalar('select skills_session_native_option($1,$2::jsonb)',[c,JSON.stringify(o)]);
  assert.equal(await opt(),null);
  await db.exec("update native_skills_publication_policy set enabled=true,verified=true,evidence='LOCAL FIXTURE ONLY';");
  assert.equal(await opt(),null,'separate publication switch remains off');
  await db.exec('update native_skills_publication_policy set publication_enabled=true');assert.equal(await opt(),null,'no invented qualification');
  await db.exec("insert into people(person_key,display_name) values('brian','Brian Ennis'); update skills_session_context_config set qualification_course_id=course_id,policy_evidence='skills-session-policy.v1'; insert into instructor_qualifications(instructor_id,course_id,qualification_key,status) select p.id,c.id,'skills-session-policy.v1','active' from people p cross join courses c where p.person_key='brian' and c.enrollware_course_id='509474';");
  assert.equal((await opt()).capacity,2);
  await db.exec("insert into skills_session_context_config(context_key,course_id,qualification_course_id,enabled,capacity_policy_verified,policy_evidence) select k,c.id,c.id,true,true,'skills-session-policy.v1' from courses c cross join unnest(array['first-aid-cpr-aed','arc-blended','hsi-blended']) k where c.enrollware_course_id='509474'");
  for(const context of ['first-aid-cpr-aed','arc-blended','hsi-blended'])assert.equal((await opt({...offer,context,selectionId:'skills:'+offer.nativeOfferId+':'+context},context)).capacity,2);
  await db.exec("update instructor_qualifications set qualification_key='unverified' where qualification_key='skills-session-policy.v1'");assert.equal(await opt(),null);await db.exec("update instructor_qualifications set qualification_key='skills-session-policy.v1' where qualification_key='unverified'");
  for(const patch of [{authority:'v2'},{authority:null},{nativeScopeId:'other'},{nativeOfferId:'bad'},{selectionId:'skills:forged'},{qualificationPolicy:'guess'},{capacity:4},{context:'hsi-blended'},{instructor:'Other'},{appointmentDayId:123},{matchedContainerId:'legacy'},{proofObservedAt:null},{proofObservedAt:'2030-01-01T00:00:00'},{proofObservedAt:new Date(Date.now()+60000).toISOString()},{proofObservedAt:new Date(Date.now()-16*60000).toISOString()},{proofObservedAt:new Date(Date.parse(offer.generatedAt)-6*60000).toISOString()},{generatedAt:new Date(Date.now()+60000).toISOString()},{validUntil:new Date(Date.parse(offer.generatedAt)+900001).toISOString()},{endsAt:offer.startsAt}])assert.equal(await opt({...offer,...patch}),null,JSON.stringify(patch));
  const downgrade={...offer};for(const key of ['authority','nativeScopeId','nativeOfferId','proofObservedAt'])delete downgrade[key];assert.equal(await opt(downgrade),null,'native identity cannot shed its original-proof envelope');
  const early=await scalar("select jsonb_build_object('startsAt',now()+interval '23 hours','endsAt',now()+interval '23 hours 45 minutes','consumptionEndsAt',now()+interval '24 hours')");assert.equal(await opt({...offer,...early}),null);
  const late=await scalar("select skills_test.offer('late',91)");assert.equal(await opt({...offer,...late,authority:offer.authority,instructor:'Brian Ennis',selectionId:offer.selectionId}),null);
  await db.exec("update instructor_qualifications set status='revoked' where qualification_key='skills-session-policy.v1'");assert.equal(await opt(),null);await db.exec("update instructor_qualifications set status='active',expires_at=now()+interval '1 day' where qualification_key='skills-session-policy.v1'");assert.equal(await opt(),null);await db.exec("update instructor_qualifications set expires_at=null where qualification_key='skills-session-policy.v1'");
  // A private/unlisted commitment has no invented zero and blocks the entire venue.
  const busy=await scalar("insert into class_sessions(source,status,record_scope,course_id,start_at,end_at,consumption_start_at,consumption_end_at,timezone,location_id,lead_instructor_id,visibility,registration_backend,registration_status,max_students) select 'landerware_event','scheduled','operational',id,$1::timestamptz,$2::timestamptz,$1::timestamptz,$3::timestamptz,'America/New_York',(select id from locations where location_key='910cpr-office-shipyard'),(select id from people where person_key='skills-test'),'unlisted','landerware','open',2 from courses where enrollware_course_id='509474' returning id",[offer.startsAt,offer.endsAt,offer.consumptionEndsAt]);assert.equal(await opt(),null);await db.query("update class_sessions set status='cancelled' where id=$1",[busy]);assert.equal((await opt()).capacity,2);
  const savedClosure=await scalar("select pg_get_functiondef('public.public_registration_closure_policy()'::regprocedure)");
  await db.exec("create or replace function public.public_registration_closure_policy() returns jsonb language sql stable as $$ select jsonb_build_object('closures',jsonb_build_array(jsonb_build_object('startsAt','"+offer.startsAt+"','endsAt','"+offer.consumptionEndsAt+"'))) $$");assert.equal(await opt(),null);await db.exec(savedClosure);
  await db.exec(load('tests/helpers/native-full-service-role-acl.sql'));
  await db.exec('set role service_role');
  assert.equal(await scalar('select current_user'),'service_role');
  assert.equal(await scalar('select rolsuper from pg_roles where rolname=current_user'),false);
  assert.equal((await opt()).capacity,2);
  const materialize=()=>scalar("select materialize_native_skills_checkout('cpr-aed',$1::jsonb,'synthetic')",[JSON.stringify(offer)]);
  const result=await materialize();assert.ok(result.targetSessionId);assert.equal((await materialize()).targetSessionId,result.targetSessionId);await db.exec('reset role');
  // Current materializer supplies the actual lifecycle witness. Install the
  // unchanged authority/snapshot migrations, then project their atomic result.

  const hold=await scalar(`insert into landerware_public_orders(external_class_id,class_session_id,course_id,payer_email,idempotency_key,hold_expires_at)
    select external_class_id,id,'509474','fixture@example.invalid','native-skills-snapshot-fixture',now()+interval '5 minutes' from class_sessions where id=$1 returning id`,[result.targetSessionId]);
  await db.query(`insert into landerware_public_order_students(order_id,first_name,last_name,email,phone,unit_amount)
    values($1,'Synthetic','Fixture','fixture@example.invalid','',5500)`,[hold]);
  const row=await scalar(`select to_jsonb(s)||jsonb_build_object(
    'courses',(select jsonb_build_object('course_key',course_key,'name',name) from courses where id=s.course_id),
    'landerware_sessions',(select jsonb_agg(w) from landerware_sessions w where w.class_session_id=s.id),
    'native_checkout_generated_sessions',(select jsonb_agg(w) from native_checkout_generated_sessions w where w.class_session_id=s.id))
    from class_sessions s where id=$1`,[result.targetSessionId]);
  const seats=await scalar('select native_scheduling_seat_snapshot($1)',[result.targetSessionId]);
  assert.equal(seats.registrationAuthority,'landerware-generated-session.v1');
  assert.equal(seats.holds,1);assert.equal(seats.remaining,1);assert.equal(seats.publicBooking,null);
  const endpoint=loadEndpoint(()=>{throw Error('network forbidden')});
  assert.throws(()=>endpoint.projectDemand(row),/Native scheduling occupancy is unavailable/);
  const projected=endpoint.projectDemand(row,seats);
  assert.equal(projected.count_available,true);assert.equal(projected.active_registration_count,1);
  assert.equal(projected.held_seat_count,1);assert.equal(projected.workspace_projection_status,'current');
  assert.equal(projected.native_booking_admission,null,'skills remaining-seat publication is not yet admitted');
  const pipeline=`import json,sys
from scripts import run_native_publication as r
from scripts.generate_dynamic_offers import normalize_occupancy
from scripts.block_start_time_selector import seated_class_selector_offers
p=json.load(sys.stdin);out=r.retained_projection({'sessions':[]},{'generated_at':sys.argv[1],'sessions':[p]})
assert len(out['sessions'])==1
row=out['sessions'][0]
assert row['course_id']=='509474' and row['active_registration_count']==1 and row['public_direct_booking'] is False
assert not row.get('registration_url') and not row.get('native_booking_admission')
assert seated_class_selector_offers(schedule_future_payload=out,selected_courses=[{'course_id':'509474'}],selected_course_ids={'509474'},course_rules={})==[]
blocks=normalize_occupancy(out,'fixture');assert len(blocks)==1
assert blocks[0]['end']>blocks[0]['start']
print(json.dumps({'count':row['active_registration_count'],'blocked':True,'skillsSeatedActivation':'BLOCKED'}))`;
  const published=spawnSync(process.env.SKILLS_TEST_PYTHON||'python',['-B','-c',pipeline,new Date().toISOString()],
    {cwd:fileURLToPath(new URL('../',import.meta.url)),input:JSON.stringify(projected),encoding:'utf8',timeout:30000,windowsHide:true});
  assert.equal(published.status,0,published.stderr||String(published.error));
  assert.deepEqual(JSON.parse(published.stdout),{count:1,blocked:true,skillsSeatedActivation:'BLOCKED'});
  assert.equal(await scalar('select max_students from class_sessions where id=$1',[result.targetSessionId]),2);
  assert.equal(await scalar("select active from landerware_registration_catalog where course_id='509474'"),false);
  assert.equal(await scalar("select active from landerware_registration_profiles where profile_key='native_skills_shared'"),false);
  assert.equal(await scalar("select count(*)::int from courses where enrollware_course_id='509474' and registration_profile_key is not null"),0);
  await db.exec('update native_skills_publication_policy set enabled=false');assert.equal(await opt(),null);
  const legacy=await scalar("select skills_test.offer('legacy',60)");assert.equal(await scalar("select native_skills_publication_offer_valid('cpr-aed',$1::jsonb)",[JSON.stringify(legacy)]),true,'unrelated legacy and HeartCode policy remains unchanged');
 }finally{await db.close();}
});
