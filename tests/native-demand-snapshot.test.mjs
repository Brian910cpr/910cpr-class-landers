import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const schema=readFileSync(new URL('./helpers/native-demand-snapshot-schema.sql',import.meta.url),'utf8');
const migration=readFileSync(new URL('../supabase/migrations/20261111200810_native_scheduling_seat_snapshot.sql',import.meta.url),'utf8');
const id='11111111-1111-4111-8111-111111111111';
const seed=`insert into class_sessions(id,course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,external_class_id,record_scope,registration_backend,max_students,source,status,registration_status,visibility)
 values('${id}','22222222-2222-4222-8222-222222222222','2030-01-01T15:00Z','2030-01-01T17:00Z','2030-01-01T15:00Z','2030-01-01T17:30Z','33333333-3333-4333-8333-333333333333','44444444-4444-4444-8444-444444444444','12345','operational','landerware',10,'enrollware','scheduled','open','private');`;
const adopt=`insert into landerware_session_authority_events(id,class_session_id,revision,enabled,session_identity,capacity_ceiling,anonymous_reserved_seats,unmatched_external_ids,recorded_at)
 select '55555555-5555-4555-8555-555555555555',id,1,true,jsonb_build_array(course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,resource_id,organization_id,external_class_id,record_scope),8,1,array['inherited'],'2026-01-01' from class_sessions;`;
const hold=`insert into landerware_public_orders values('66666666-6666-4666-8666-666666666666','${id}','checkout_open',now()-interval '1 day','{"payment_status":"paid","seat_hold_protected":true}');
 insert into landerware_public_order_students values('77777777-7777-4777-8777-777777777777','66666666-6666-4666-8666-666666666666');`;
async function fixture(){
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 await db.exec(schema);const scalar=async(sql,args=[])=>Object.values((await db.query(sql,args)).rows[0])[0];
 const fingerprint=()=>scalar("select md5(string_agg(pg_get_functiondef(oid),'' order by proname)) from pg_proc where proname in ('landerware_public_seat_state','native_session_authority_state')");
 const before=await fingerprint();await db.exec(migration);assert.equal(await fingerprint(),before,'existing mutation readers remain byte-identical');
 await db.exec(seed);return {db,scalar,read:()=>scalar(`select native_scheduling_seat_snapshot('${id}')`)};
}
test('snapshot reader is stable, service-only, read-only, and preserves adopted registrations, protected holds and unknown reserve',async()=>{
 const {db,scalar,read}=await fixture();try{
  await db.exec(adopt+hold);
  await db.exec(`insert into registrations values('88888888-8888-4888-8888-888888888888','${id}','active',null,'landerware_native_checkout',null);`);
  assert.equal(await scalar("select provolatile from pg_proc where oid='native_scheduling_seat_snapshot(uuid)'::regprocedure"),'s');
  assert.equal(await scalar("select prosecdef from pg_proc where oid='native_scheduling_seat_snapshot(uuid)'::regprocedure"),false);
  for(const role of ['anon','authenticated'])assert.equal(await scalar(`select has_function_privilege('${role}','native_scheduling_seat_snapshot(uuid)','EXECUTE')`),false);
  assert.equal(await scalar("select has_function_privilege('service_role','native_scheduling_seat_snapshot(uuid)','EXECUTE')"),true);
  await db.exec('begin read only;set local role service_role');const first=await read();await db.exec('commit');
  assert.equal(first.registered,1);assert.equal(first.holds,1);assert.equal(first.unreconciledReserved,2);assert.equal(first.remaining,4);assert.equal(first.capacity,8);assert.equal(first.authorityRevision,1);
  await db.exec(`insert into registrations values('99999999-9999-4999-8999-999999999999','${id}','registered','inherited','enrollware_history',null);`);
  const imported=await read();assert.equal(imported.registered,2);assert.equal(imported.unreconciledReserved,1);assert.equal(imported.remaining,4);
  await db.exec("update registrations set status='cancelled',canceled_at='2025-01-01' where external_registration_id='inherited'");assert.equal((await read()).unreconciledReserved,2);
  await db.exec("update registrations set canceled_at='2027-01-01' where external_registration_id='inherited'");assert.equal((await read()).unreconciledReserved,1);
  await db.exec("update landerware_public_orders set payment_evidence='{}'");assert.equal((await read()).holds,0,'expired unpaid hold is not occupied');
  await db.exec("insert into landerware_public_session_inventory values('12345',1,0)");await assert.rejects(read,/native_occupancy_conflict/);
  await db.exec('delete from landerware_public_session_inventory;update class_sessions set start_at=start_at+interval \'0.000001 second\'');await assert.rejects(read,/native_authority_identity_changed/);
  await db.exec('update class_sessions set start_at=start_at-interval \'0.000001 second\';update landerware_session_authority_events set enabled=false');await assert.rejects(read,/native_authority_disabled/);
 }finally{await db.close();}
});
test('fresh materialized native sessions require their witness and count held and active seats without external lookup',async()=>{
 const {db,read}=await fixture();try{
  await db.exec(`update class_sessions set external_class_id='lw-11111111-1111-4111-8111-111111111111',source='landerware_event',external_session_evidence='{"materializedBy":"native_full_course"}';`);
  await assert.rejects(read,/native_generated_authority_unavailable/);
  await db.exec('insert into native_checkout_generated_sessions select id,native_checkout_generated_identity(s),\'holding\' from class_sessions s');
  const empty=await read();assert.equal(empty.registrationAuthority,'landerware-generated-session.v1');assert.equal(empty.registered,0);assert.equal(empty.authorityRevision,null);
  await db.exec(hold+`insert into registrations values('88888888-8888-4888-8888-888888888888','${id}','active',null,'landerware_native_checkout',null);`);
  const occupied=await read();assert.equal(occupied.registered+occupied.holds+occupied.unreconciledReserved,2);
  await db.exec("update registrations set external_registration_id='unexpected'");await assert.rejects(read,/native_generated_occupancy_unknown/);
  await db.exec("update registrations set external_registration_id=null;update native_checkout_generated_sessions set state='released'");await assert.rejects(read,/native_generated_authority_unavailable/);
  await db.exec("update native_checkout_generated_sessions set state='holding';update class_sessions set max_students=9");await assert.rejects(read,/native_generated_authority_unavailable/);
 }finally{await db.close();}
});
