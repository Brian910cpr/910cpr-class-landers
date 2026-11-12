import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {preProfileFiles,profileMigration,fullCourseMigration} from './helpers/native-checkout-migration-plan.mjs';
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const lifecycle='supabase/migrations/20261110231103_native_checkout_generated_session_lifecycle.sql';
const v2='supabase/migrations/20261111195655_native_full_course_v2_policy.sql';
const hooks='supabase/migrations/20261111200908_native_full_course_lifecycle_hooks.sql';
test('actual production installation order restores full-course witness, release/reuse and paid protection without backfill',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  for(const f of preProfileFiles)await db.exec(load(f));
  await db.exec(load(profileMigration));
  // Hosted lifecycle existed before full-course was installed, so it could not
  // patch that missing function. Test that real ordering instead of a clean ideal.
  await db.exec(load(lifecycle));
  await db.exec(load(fullCourseMigration));await db.exec(load(v2));
  const scalar=async(sql,args=[])=>Object.values((await db.query(sql,args)).rows[0])[0];
  const fn='public.materialize_native_full_checkout(text,jsonb,text)';
  const baseline=await scalar('select pg_get_functiondef($1::regprocedure)',[fn]);
  assert.ok(!baseline.includes('native_checkout_witness_generated'));
  await db.exec(baseline.replace('begin\n','begin\n -- independent edit\n'));
  await assert.rejects(()=>db.exec(load(hooks)),/native_full_materializer_source_drift/);await db.exec('rollback');
  await db.exec(baseline);
  const state=()=>scalar("select jsonb_build_object('sessions',(select coalesce(jsonb_agg(to_jsonb(s) order by id),'[]') from class_sessions s),'orders',(select coalesce(jsonb_agg(to_jsonb(o) order by id),'[]') from landerware_public_orders o),'witnesses',(select count(*) from native_checkout_generated_sessions))");
  const before=await state();await db.exec(load(hooks));assert.deepEqual(await state(),before);
  await db.exec(load(hooks));assert.deepEqual(await state(),before,'idempotent reapplication does not adopt records');
  const patched=await scalar('select pg_get_functiondef($1::regprocedure)',[fn]);
  await db.exec(patched.replace('perform public.native_checkout_witness_generated(target);','perform public.native_checkout_witness_generated(target);\n  perform public.native_checkout_witness_generated(target);'));
  await assert.rejects(()=>db.exec(load(hooks)),/native_full_materializer_duplicate_hook/);await db.exec('rollback');
  await db.exec(patched);
  for(const name of [fn,'public.native_full_course_option(text,jsonb)']){
   assert.equal(await scalar('select prosecdef from pg_proc where oid=$1::regprocedure',[name]),false);
   for(const role of ['anon','authenticated'])assert.equal(await scalar('select has_function_privilege($1,$2,\'EXECUTE\')',[role,name]),false);
  }
  await db.exec("insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price,registration_profile_key) values('aha-bls-provider','Synthetic BLS','209806',120,0,12,75,'native_bls_initial'); insert into people(person_key,display_name) values('brian','Brian Ennis'); insert into instructor_qualifications(instructor_id,course_id,status) select p.id,c.id,'active' from people p cross join courses c where p.person_key='brian' and c.enrollware_course_id='209806'; update native_full_course_policy set enabled=true,verified=true,evidence='LOCAL ONLY'; update native_full_course_public_policy set enabled=true,publication_enabled=true,verified=true,evidence='LOCAL ONLY';");
  const offer=await scalar("select skills_test.offer('lifecycle',80)||jsonb_build_object('authority','native-full-course.v2','proofObservedAt',now(),'nativeScopeId','brian-shipyard-b.v1','courseNumber','209806','instructor','Brian Ennis','selectionId','native-full:'||repeat('c',64),'endsAt',(skills_test.offer('lifecycle',80)->>'startsAt')::timestamptz+interval '120 minutes','consumptionEndsAt',(skills_test.offer('lifecycle',80)->>'startsAt')::timestamptz+interval '150 minutes')");
  const student={firstName:'Synthetic',lastName:'Fixture',email:'fixture@example.invalid',phone:'2025550100',manualChoice:'own-copy',addons:[]};
  const inputs=[{wire:student,selectedChoices:['manual_own']}];
  const claim=key=>scalar("select reserve_native_checkout_order($1,'native_bls_initial',1,'',null,$2::jsonb,$3::jsonb,$4::jsonb,7500)",[key,JSON.stringify(offer),JSON.stringify([student]),JSON.stringify(inputs)]);
  const first=await claim('45454545-4545-4545-8545-454545454545');
  assert.equal(await scalar('select count(*) from native_checkout_generated_sessions'),1);
  await db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id=$1",[first.orderId]);
  const release=()=>scalar('select native_checkout_release_abandoned($1,$2)',[offer.startsAt,offer.consumptionEndsAt]);
  assert.equal(await release(),1);
  assert.equal(await scalar('select status from class_sessions where id=$1',[first.sessionId]),'cancelled');
  const second=await claim('46464646-4646-4646-8646-464646464646');assert.equal(second.sessionId,first.sessionId);
  assert.equal(await scalar('select count(*) from class_sessions'),1,'fresh nonce reuses witnessed physical identity');
  assert.equal(await scalar('select state from native_checkout_generated_sessions'),'holding');
  await db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 minute',payment_evidence='{\"payment_status\":\"paid\",\"seat_hold_protected\":\"true\"}' where id=$1",[second.orderId]);
  assert.equal(await release(),0,'payment observed without finalization retains commitment');
  assert.equal(await scalar('select status from class_sessions where id=$1',[second.sessionId]),'scheduled');
 }finally{await db.close();}
});
