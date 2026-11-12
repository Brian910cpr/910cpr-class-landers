import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {proveHeartsaverScopes} from './native-heartsaver-full-proof.mjs';
const migration=readFileSync(new URL('../supabase/migrations/20261111223000_native_heartsaver_publication.sql',import.meta.url),'utf8');
test('atomic Heartsaver publication admission preserves liabilities, exact scope and disabled defaults',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 const scalar=async(sql,args=[])=>Object.values((await db.query(sql,args)).rows[0])[0];
 try {
  await proveHeartsaverScopes(db);
  const before=await scalar("select jsonb_agg(to_jsonb(p) order by public_course_id) from native_heartsaver_full_course_policy p");
  const snapshots=await scalar("select jsonb_object_agg(id,native_scheduling_seat_snapshot(id)) from class_sessions where source='landerware_event' and status='scheduled'");
  await db.exec(migration);
  assert.deepEqual(await scalar("select jsonb_agg(to_jsonb(p) order by public_course_id) from native_heartsaver_full_course_policy p"),before);
  for(const [id,old] of Object.entries(snapshots)) {const current=await scalar('select native_scheduling_seat_snapshot($1)',[id]);assert.equal(current.heartsaverBooking,null);delete current.heartsaverBooking;assert.deepEqual(current,old);}
  let proof=await scalar('select native_heartsaver_publication_policy()');assert.equal(proof.schemaVersion,'native-heartsaver-publication-policy.v1');assert.equal(Date.parse(proof.validUntil)-Date.parse(proof.observedAt),900000);
  for(const p of Object.values(proof.courses)){assert.equal(p.nativePublicationEnabled,false);assert.equal(p.qualificationValidThrough,null);}
  await db.exec('update native_heartsaver_full_course_policy set enabled=true');
  proof=await scalar('select native_heartsaver_publication_policy()');for(const p of Object.values(proof.courses)){assert.equal(p.nativePublicationEnabled,true);assert.ok(Date.parse(p.qualificationValidThrough)>Date.now());}
  const id=await scalar("select id from class_sessions where external_course_id='209809' and source='landerware_event' and status='scheduled' limit 1");
  const read=()=>scalar('select native_scheduling_seat_snapshot($1)',[id]);
  const good=await read();assert.equal(good.registered,1);assert.equal(good.holds,0);assert.equal(good.heartsaverBooking.remaining,1);assert.equal(good.heartsaverBooking.publicCourseId,'209809');assert.equal(good.heartsaverBooking.instructionMinutes,120);
  const unresolved=await scalar("select native_scheduling_seat_snapshot(id) from class_sessions where external_course_id='344085' and source='landerware_event' and status='scheduled' limit 1");assert.ok(unresolved.holds>0);assert.equal(unresolved.heartsaverBooking,null);
  for(const change of ["update native_heartsaver_full_course_policy set publication_enabled=false", "update native_heartsaver_full_course_policy set max_students=1", "update instructor_qualifications set expires_at=now()+interval '1 day'", "update locations set scheduling_status='inactive'", "update landerware_registration_profiles set active=false where profile_key='native_heartsaver_209809_draft'"]){
   await db.exec('begin');await db.exec(change);const rejected=await read();assert.equal(rejected.heartsaverBooking,null,change);assert.equal(rejected.registered,1);assert.equal(rejected.capacity,good.capacity);await db.exec('rollback');
  }
  await db.exec('begin');
  await db.exec("update landerware_public_orders set status='cancelled',checkout_runtime_version='native-v1',payment_evidence='{}',stripe_payment_intent_id=null,reconciliation_error=null where status<>'paid'");
  const cpr=await scalar("select native_scheduling_seat_snapshot(id) from class_sessions where external_course_id='344085' and source='landerware_event' and status='scheduled' limit 1");assert.equal(cpr.heartsaverBooking.publicCourseId,'344085');assert.equal(cpr.heartsaverBooking.instructionMinutes,90);assert.equal(cpr.heartsaverBooking.cleanupMinutes,15);assert.equal(cpr.heartsaverBooking.remaining,3);
  await db.exec('rollback');
  await db.exec('begin');
  await db.exec(`update landerware_registration_profiles set version=version+1,form_schema=form_schema||'{"public_aliases":[{"public_course_id":"209809"}]}'::jsonb where profile_key=(select registration_profile_key from courses where enrollware_course_id='209806')`);
  assert.equal((await read()).heartsaverBooking,null,'another active physical profile cannot claim same public course');await db.exec('rollback');
  for(const fn of ['native_heartsaver_publication_policy()','native_scheduling_seat_snapshot(uuid)']){
   assert.equal(await scalar('select provolatile from pg_proc where oid=$1::regprocedure',[fn]),'s');
   for(const role of ['anon','authenticated'])assert.equal(await scalar('select has_function_privilege($1,$2,\'EXECUTE\')',[role,fn]),false);
  }
  await db.exec('begin read only');await read();await scalar('select native_heartsaver_publication_policy()');await db.exec('commit');
 }finally{await db.close();}
});
