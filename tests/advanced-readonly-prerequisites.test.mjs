import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8').replaceAll('\r\n','\n');
const schema=load('tests/helpers/native-demand-snapshot-schema.sql');
const installer=load('supabase/reviewed/native-advanced-readonly-prerequisites.sql');
async function fixture(){const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();await db.exec(schema);await db.exec("alter table landerware_public_orders add column checkout_runtime_version text,add column reconciliation_error text,add column stripe_payment_intent_id text");return {db,scalar:async(q,args=[])=>Object.values((await db.query(q,args)).rows[0])[0]};}
test('read-only prerequisite install is additive, idempotent, service-scoped and never rewrites source rows or mutation readers',async()=>{
 const {db,scalar}=await fixture();try{
  const id='11111111-1111-4111-8111-111111111111';await db.exec(`insert into class_sessions(id,course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,external_class_id,record_scope,registration_backend,max_students,source,status,registration_status,visibility)
   values('${id}','22222222-2222-4222-8222-222222222222','2030-01-01T15:00Z','2030-01-01T17:00Z','2030-01-01T15:00Z','2030-01-01T17:30Z','33333333-3333-4333-8333-333333333333','44444444-4444-4444-8444-444444444444','12345','operational','landerware',10,'enrollware','scheduled','open','private');
   insert into landerware_session_authority_events(id,class_session_id,revision,enabled,session_identity,capacity_ceiling,anonymous_reserved_seats,unmatched_external_ids,recorded_at)
   select '55555555-5555-4555-8555-555555555555',id,1,true,jsonb_build_array(course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,resource_id,organization_id,external_class_id,record_scope),8,1,array[]::text[],now() from class_sessions;`);
  const rows=()=>scalar('select jsonb_agg(to_jsonb(s) order by id) from class_sessions s');const before=await rows();
  const mutations=()=>scalar("select md5(string_agg(pg_get_functiondef(oid),'' order by proname)) from pg_proc where proname in ('landerware_public_seat_state','native_session_authority_state')");const old=await mutations();
  await db.exec(installer);const oid=await scalar("select 'native_scheduling_seat_snapshot(uuid)'::regprocedure::oid::text");await db.exec(installer);assert.equal(await scalar("select 'native_scheduling_seat_snapshot(uuid)'::regprocedure::oid::text"),oid);assert.deepEqual(await rows(),before);assert.equal(await mutations(),old);
  for(const name of ['native_scheduling_seat_snapshot(uuid)','native_checkout_unresolved_payment(landerware_public_orders)']){for(const role of ['anon','authenticated'])assert.equal(await scalar('select has_function_privilege($1,$2,\'EXECUTE\')',[role,name]),false);assert.equal(await scalar("select has_function_privilege('service_role',$1,'EXECUTE')",[name]),true);}
  await db.exec('begin read only;set local role service_role');const read=await scalar('select native_scheduling_seat_snapshot($1)',[id]);await db.exec('commit');assert.equal(read.capacity,8);assert.equal(read.unreconciledReserved,1);assert.equal(read.remaining,7);assert.equal(read.publicBooking,null);
 }finally{await db.close();}
});
test('unexpected installed body or missing dependency refuses atomically instead of overwriting or partially installing',async()=>{
 const {db,scalar}=await fixture();try{
  await db.exec("create function native_checkout_unresolved_payment(o landerware_public_orders) returns boolean language sql stable security invoker set search_path='' as 'select false'");
  const before=await scalar("select pg_get_functiondef('native_checkout_unresolved_payment(landerware_public_orders)'::regprocedure)");
  await assert.rejects(db.exec(installer),/advanced_readonly_prerequisite_source_drift/);await db.exec('rollback');assert.equal(await scalar("select to_regprocedure('native_scheduling_seat_snapshot(uuid)')::text"),null);assert.equal(await scalar("select pg_get_functiondef('native_checkout_unresolved_payment(landerware_public_orders)'::regprocedure)"),before);
  await db.exec('drop table landerware_registration_catalog');await assert.rejects(db.exec(installer),/advanced_readonly_prerequisite_table_missing/);await db.exec('rollback');assert.equal(await scalar("select to_regprocedure('native_scheduling_seat_snapshot(uuid)')::text"),null);
 }finally{await db.close();}
});
test('incompatible prerequisite column fails before installing either function',async()=>{
 const {db,scalar}=await fixture();try{
  await db.exec('alter table landerware_registration_profiles drop column form_schema');
  await assert.rejects(db.exec(installer),/advanced_readonly_prerequisite_column_missing:landerware_registration_profiles.form_schema/);await db.exec('rollback');
  assert.equal(await scalar("select to_regprocedure('native_scheduling_seat_snapshot(uuid)')::text"),null);assert.equal(await scalar("select to_regprocedure('native_checkout_unresolved_payment(landerware_public_orders)')::text"),null);
 }finally{await db.close();}
});
