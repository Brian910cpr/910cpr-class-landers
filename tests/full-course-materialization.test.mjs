import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fullCourseOffers} from '../supabase/functions/public-registration/full-course.mjs';
import {easternInstant} from '../supabase/functions/registration-reschedule/policy.mjs';
import {preProfileFiles,profileMigration,fullCourseMigration} from './helpers/native-checkout-migration-plan.mjs';
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const now=Date.parse('2030-01-01T00:00:00Z');
function feed(local='2030-01-02T10:00'){
 const start=Date.parse(easternInstant(local));
 return {pageKey:'bls',schemaVersion:'selector-resolved-availability.v1',generatedAt:new Date(now).toISOString(),validUntil:new Date(now+600000).toISOString(),dates:[{date:local.slice(0,10),startTimes:[{startTime:local.slice(11),courses:[{courseId:'209806',offerType:'dynamic_appointment',publicSelectable:true,instructor:'Brian Ennis',resource:':: Wilmington; Shipyard Blvd - B',location:':: Wilmington; Shipyard Blvd',availabilityBlockId:'fixture',sourceSessionIds:[],durationMinutes:120,schedulerConsumptionMinutes:150,cleanupBufferMinutes:30,setupBufferMinutes:0,appointmentDayId:123,occupiedUntil:new Date(start+150*60000).toISOString(),validUntil:new Date(now+600000).toISOString()}]}]}]};
}
test('full-course server publication matching preserves BLS120+30 and rejects stale or unqualified/skills offers and DST gaps/folds',()=>{
 const payload=feed(),offers=fullCourseOffers(payload,'209806',now);assert.equal(offers.length,1);
 assert.equal(offers[0].endsAt,'2030-01-02T17:00:00.000Z');assert.equal(offers[0].consumptionEndsAt,'2030-01-02T17:30:00.000Z');
 assert.equal(fullCourseOffers(payload,'359474',now).length,0);
 for(const change of [{durationMinutes:45},{schedulerConsumptionMinutes:60},{instructor:'Other'},{resource:'Other room'},{sourceSessionIds:null},{publicSelectable:false},{appointmentDayId:null},{occupiedUntil:'2030-01-02T17:00:00Z'}]){const p=structuredClone(payload);Object.assign(p.dates[0].startTimes[0].courses[0],change);assert.equal(fullCourseOffers(p,'209806',now).length,0);}
 assert.throws(()=>fullCourseOffers({...payload,validUntil:new Date(now-1).toISOString()},'209806',now),/calendar_refresh_required/);
 assert.throws(()=>fullCourseOffers(payload,'509474',now),/invalid_session/);
 for(const local of ['2030-03-10T02:30','2030-11-03T01:30']){const p=feed();p.dates[0].date=local.slice(0,10);p.dates[0].startTimes[0].startTime=local.slice(11);assert.equal(fullCourseOffers(p,'209806',now).length,0);}
});

test('actual full-course SQL materializes idempotently, preserves existing records/capacity and fails closed on conflicts/configuration',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  for(const file of preProfileFiles)await db.exec(load(file));
  await db.exec("insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price) values('aha-bls-provider','Fixture BLS','209806',120,30,6,75),('aha-bls-provider-renewal','Fixture Renewal','359474',120,30,6,75); insert into people(person_key,display_name) values('brian','Brian Ennis'); insert into instructor_qualifications(instructor_id,course_id,status) select p.id,c.id,'active' from people p cross join courses c where p.person_key='brian' and c.enrollware_course_id in ('209806','359474');");
  await db.exec(load(profileMigration));await db.exec(load(fullCourseMigration));
  const scalar=async(sql,args=[])=>Object.values((await db.query(sql,args)).rows[0])[0];
  const offer=await scalar("select skills_test.offer('full-fixture',80)||jsonb_build_object('authority','native-full-course.v1','courseNumber','209806','instructor','Brian Ennis','appointmentDayId','123','selectionId','dynamic:full-fixture','endsAt',(skills_test.offer('full-fixture',80)->>'startsAt')::timestamptz+interval '120 minutes','consumptionEndsAt',(skills_test.offer('full-fixture',80)->>'startsAt')::timestamptz+interval '150 minutes')");
  const opt=(o=offer,c='209806')=>scalar('select native_full_course_option($1,$2::jsonb)',[c,JSON.stringify(o)]);
  const mat=(o=offer,c='209806')=>scalar("select materialize_native_full_checkout($1,$2::jsonb,'fixture-idempotency')",[c,JSON.stringify(o)]);
  assert.equal(await opt(),null,'migration defaults do not activate materialization');
  await db.exec("update native_full_course_policy set enabled=true,verified=true,evidence='DISPOSABLE LOCAL FIXTURE ONLY'");
  assert.equal((await opt()).capacity,6);
  for(const [k,v] of Object.entries({authority:'wrong',courseNumber:'359474',localStart:'2000-01-01T10:00',instructor:'Other',validUntil:'2000-01-01T00:00:00Z',endsAt:offer.startsAt}))assert.equal(await opt({...offer,[k]:v}),null);
  assert.equal(await opt(offer,'unknown'),null);
  const created=await mat(),again=await mat();assert.equal(created.targetSessionId,again.targetSessionId);
  assert.equal(await scalar('select count(*) from class_sessions'),1);assert.equal(await scalar('select count(*) from landerware_sessions'),1);
  assert.equal(await scalar('select max_students from class_sessions'),6);assert.equal(Number(await scalar("select extract(epoch from end_at-start_at)/60 from class_sessions")),120);
  const wire={firstName:'Synthetic',lastName:'Fixture',email:'full-course@example.invalid',phone:'2025550100',manualChoice:'own-copy',addons:[]};
  const inputs=[{wire,selectedChoices:['manual_own']}],key='12121212-1212-4212-8212-121212121212';
  const claim=()=>scalar("select reserve_native_checkout_order($1,'native_bls_initial',1,'',null,$2::jsonb,$3::jsonb,$4::jsonb,7500)",[key,JSON.stringify(offer),JSON.stringify([wire]),JSON.stringify(inputs)]);
  const order=await claim();assert.equal(order.amountCents,7500);assert.equal((await claim()).orderId,order.orderId);assert.equal(await scalar('select count(*) from class_sessions'),1);
  await db.exec("update class_sessions set max_students=4,source_location_label='staff-owned-note'");
  assert.equal((await mat()).capacity,4);assert.equal(await scalar('select max_students from class_sessions'),4);assert.equal(await scalar('select source_location_label from class_sessions'),'staff-owned-note');
  // Never rewrite a manually managed record that occupies the same identity.
  await db.query("update class_sessions set registration_backend='enrollware' where id=$1",[created.targetSessionId]);
  assert.equal(await opt(),null);await assert.rejects(mat(),/session_not_available/);assert.equal(await scalar('select max_students from class_sessions'),4);
  await db.query("update class_sessions set registration_backend='landerware' where id=$1",[created.targetSessionId]);
  const later={...offer,selectionId:'dynamic:second',startsAt:new Date(Date.parse(offer.startsAt)+5*3600000).toISOString(),endsAt:new Date(Date.parse(offer.startsAt)+7*3600000).toISOString(),consumptionEndsAt:new Date(Date.parse(offer.startsAt)+7.5*3600000).toISOString()};
  later.localStart=later.startsAt.slice(0,10)+'T15:00';assert.equal(await opt(later),null,'stale publication cannot create another same-course daily position');
  await db.exec("update courses set max_students_default=null where enrollware_course_id='359474'");assert.equal(await opt({...offer,courseNumber:'359474'},'359474'),null);
  await db.exec("update courses set cleanup_buffer_minutes=0 where enrollware_course_id='209806'");assert.equal(await opt(),null);
 }finally{await db.close();}
});
