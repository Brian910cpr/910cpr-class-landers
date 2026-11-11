import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {randomUUID} from 'node:crypto';
import {setup} from './native-checkout-harness.mjs';

const sql=readFileSync(new URL('../../supabase/migrations/20261111185724_native_session_authority_cutover.sql',import.meta.url),'utf8');
async function fixture(fn,capacity=6,sourceEnding=null){
 const h=await setup(capacity);
 try{
  await h.db.exec("alter table landerware_public_orders add column registration_profile_snapshot jsonb not null default '{}'");
  for(const file of ['20261110212444_native_checkout_additive_order_runtime.sql','20261110225640_native_checkout_immutable_order_version.sql'])await h.db.exec(readFileSync(new URL('../../supabase/migrations/'+file,import.meta.url),'utf8'));
  h.create=(st=h.students(1),key=randomUUID(),extra={})=>h.rpc('native_checkout_create_order',{p_idempotency_key:key,p_external_class_id:h.external,p_course_id:'359474',p_payer_email:st[0].email,p_payer_phone:st[0].phone,p_students:st,p_billing_code:null,p_offer:{},...extra});
  h.finalize=async o=>{const args={p_order_id:o.id,p_stripe_payment_intent_id:`pi_test_${o.id}`,p_evidence:h.evidence(o)};await h.rpc('native_checkout_record_payment',args);return h.rpc('native_checkout_finalize_order',args);};
  await h.db.exec('grant all on all tables in schema public to service_role; grant usage on schema public to service_role');
  if(sourceEnding){
   const definition=(await h.db.query("select pg_get_functiondef('public.landerware_public_seat_state(uuid)'::regprocedure) definition")).rows[0].definition;
   await h.db.exec(sourceEnding==='crlf'?definition.replaceAll('\n','\r\n'):definition.replace('declare s public.class_sessions;','declare s public.class_sessions; /* synthetic unreviewed drift */'));
  }
  await h.db.exec(sql);
  h.snapshot=()=>h.rpc('native_session_authority_snapshot',{p_session_id:h.id});
  h.authority=async(enabled=false,snapshot=null,decision=randomUUID())=>{snapshot??=await h.snapshot();return h.rpc('native_session_authority_record',{
   p_session_id:h.id,p_decision_id:decision,p_expected_fingerprint:snapshot.fingerprint,p_expected_revision:snapshot.revision,p_enabled:enabled
  });};
  h.retained=async(ids=['legacy-a'],extra={})=>h.db.query(`update class_sessions set external_class_id='123456',external_reconciliation=$2 where id=$1`,[h.id,JSON.stringify({complete:true,source_observed_at:'2020-01-01T00:00:00Z',active_external_registration_ids:ids,active_registration_count:ids.length,...extra})]);
  h.registration=async(external=null,status='registered',canceledAt=null)=>{
   const c=(await h.db.query("insert into customers(first_name,last_name,email) values('Synthetic','Participant',$1) returning id",[randomUUID()+'@example.invalid'])).rows[0].id;
   return (await h.db.query(`insert into registrations(customer_id,class_session_id,status,registration_source,external_registration_id,canceled_at) values($1,$2,$3,$4,$5,$6) returning id`,[c,h.id,status,external?'enrollware_history':'landerware',external,canceledAt])).rows[0].id;
  };
  await fn(h);
 }finally{await h.db.close();}
}

test('installation creates no authority or business mutations and native seats retain their contract',()=>fixture(async h=>{
 assert.equal((await h.db.query('select count(*) n from landerware_session_authority_events')).rows[0].n,0);
 assert.deepEqual(await h.seats(),{capacity:6,registered:0,externallyRegistered:0,nativeRegistered:0,holds:0,remaining:6});
 await h.retained();
 await assert.rejects(h.seats(),/external_reconciliation_required/);
}));

test('inactive evidence recording is default and does not unlock stale source state',()=>fixture(async h=>{
 await h.retained();await h.registration('legacy-a');
 const before=(await h.db.query('select to_jsonb(s) value from class_sessions s where id=$1',[h.id])).rows[0].value;
 const recorded=await h.authority();assert.equal(recorded.enabled,false);
 await assert.rejects(h.seats(),/external_reconciliation_required/);
 assert.deepEqual((await h.db.query('select to_jsonb(s) value from class_sessions s where id=$1',[h.id])).rows[0].value,before);
}));

test('explicit native cutover uses retained old evidence without rewriting source IDs or freshness',()=>fixture(async h=>{
 await h.retained();await h.registration('legacy-a');await h.registration();
 const proof=(await h.db.query('select external_reconciliation from class_sessions where id=$1',[h.id])).rows[0];
 await h.authority(true);
 const seats=await h.seats();assert.equal(seats.remaining,4);assert.equal(seats.registered,2);assert.equal(seats.externallyRegistered,1);assert.equal(seats.nativeRegistered,1);
 assert.equal(seats.registrationAuthority,'landerware-session-authority.v1');assert.equal(seats.unreconciledReserved,0);
 assert.deepEqual((await h.db.query('select external_reconciliation from class_sessions where id=$1',[h.id])).rows[0],proof);
 assert.equal((await h.db.query('select external_class_id from class_sessions where id=$1',[h.id])).rows[0].external_class_id,'123456');
}));

test('unknown IDs and count-only evidence reserve seats without duplication after import',()=>fixture(async h=>{
 await h.retained(['legacy-a','legacy-b']);await h.registration('legacy-a');
 await h.db.exec("insert into landerware_public_session_inventory(external_class_id,capacity,externally_registered,source) values('123456',6,4,'retained_fixture')");
 await h.authority(true);
 let s=await h.seats();assert.equal(s.registered,1);assert.equal(s.unreconciledReserved,3);assert.equal(s.remaining,2);
 const id=await h.registration('legacy-b');s=await h.seats();assert.equal(s.registered,2);assert.equal(s.unreconciledReserved,2);assert.equal(s.remaining,2);
 await h.db.query("update registrations set status='canceled',canceled_at=now()+interval '1 second' where id=$1",[id]);
 s=await h.seats();assert.equal(s.unreconciledReserved,2);assert.equal(s.remaining,3);
}));

test('old canceled evidence cannot silently release a retained missing seat',()=>fixture(async h=>{
 await h.retained(['legacy-a']);await h.registration('legacy-a','canceled','2019-01-01T00:00:00Z');
 await h.authority(true);const s=await h.seats();assert.equal(s.registered,0);assert.equal(s.unreconciledReserved,1);assert.equal(s.remaining,5);
}));

test('live and paid-protected holds remain occupied across cutover and expiry',()=>fixture(async h=>{
 const a=await h.create(h.students(2)),o=await h.bind(a.orderId);
 await h.rpc('native_checkout_record_payment',{p_order_id:o.id,p_stripe_payment_intent_id:`pi_test_${o.id}`,p_evidence:h.evidence(o)});
 await h.db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 hour' where id=$1",[o.id]);
 await h.retained([]);await h.authority(true);
 const s=await h.seats();assert.equal(s.holds,2);assert.equal(s.remaining,4);
}));

test('capacity ceiling never grows when canonical or published limits later grow',()=>fixture(async h=>{
 await h.retained([]);await h.db.exec("insert into landerware_public_session_inventory(external_class_id,capacity,externally_registered,source) values('123456',3,0,'retained_fixture')");
 await h.authority(true);
 await h.db.query('update class_sessions set max_students=12 where id=$1',[h.id]);await h.db.exec("update landerware_public_session_inventory set capacity=20 where external_class_id='123456'");
 assert.equal((await h.seats()).capacity,3);
 await h.db.exec("update landerware_public_session_inventory set capacity=2 where external_class_id='123456'");assert.equal((await h.seats()).capacity,2);
}));

test('re-admission and disable/re-enable cannot discard earlier ceilings or unresolved reservations',()=>fixture(async h=>{
 await h.retained(['retained-id']);
 await h.db.exec("insert into landerware_public_session_inventory(external_class_id,capacity,externally_registered,source) values('123456',3,2,'retained_fixture')");
 await h.authority(true);assert.equal((await h.seats()).remaining,1);
 await h.db.exec("update landerware_public_session_inventory set capacity=6,externally_registered=0");await h.retained([]);
 await h.authority(true);let seats=await h.seats();assert.equal(seats.capacity,3);assert.equal(seats.unreconciledReserved,2);assert.equal(seats.remaining,1);
 await h.authority(false);await h.authority(true);seats=await h.seats();assert.equal(seats.capacity,3);assert.equal(seats.unreconciledReserved,2);assert.equal(seats.remaining,1);
}));

test('conflicting cutover is rejected and never releases paid evidence or protected holds',()=>fixture(async h=>{
 const a=await h.create(h.students(2)),o=await h.bind(a.orderId);
 await h.rpc('native_checkout_record_payment',{p_order_id:o.id,p_stripe_payment_intent_id:`pi_test_${o.id}`,p_evidence:h.evidence(o)});
 await h.db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 hour' where id=$1",[o.id]);
 await h.retained(['retained-id']);await assert.rejects(h.authority(true),/native_occupancy_conflict/);
 assert.equal((await h.db.query('select count(*) n from landerware_session_authority_events')).rows[0].n,0);
 assert.equal((await h.order(o.id)).payment_evidence.payment_status,'paid');assert.equal((await h.order(o.id)).payment_evidence.seat_hold_protected,true);
 assert.equal((await h.finalize(o)).status,'payment_review');assert.equal((await h.order(o.id)).payment_evidence.seat_hold_protected,true);assert.equal((await h.order(o.id)).status,'checkout_open');
 assert.equal((await h.db.query('select count(*) n from registrations')).rows[0].n,0);
},2));

test('post-cutover occupancy conflicts stop finalization while preserving paid evidence',()=>fixture(async h=>{
 await h.retained([]);await h.authority(true);
 const a=await h.create(h.students(2),randomUUID(),{p_external_class_id:'123456'}),o=await h.bind(a.orderId);
 await h.rpc('native_checkout_record_payment',{p_order_id:o.id,p_stripe_payment_intent_id:`pi_test_${o.id}`,p_evidence:h.evidence(o)});
 await h.registration('late-import');
 const review=await h.finalize(o);assert.equal(review.status,'payment_review');assert.equal(review.reason,'native_occupancy_conflict');
 assert.equal((await h.order(o.id)).payment_evidence.payment_status,'paid');assert.equal((await h.order(o.id)).status,'checkout_open');
 assert.equal((await h.db.query('select count(*) n from registrations')).rows[0].n,1);
},2));

test('disabling prior authority fails closed even for native nonnumeric IDs and paid recovery',()=>fixture(async h=>{
 await h.retained(['retained-id']);
 await h.db.query('update class_sessions set external_class_id=$2,historical_student_count=2 where id=$1',[h.id,h.external]);
 await h.authority(true);assert.equal((await h.seats()).unreconciledReserved,2);assert.equal((await h.seats()).remaining,4);
 const a=await h.create(),o=await h.bind(a.orderId);
 await h.rpc('native_checkout_record_payment',{p_order_id:o.id,p_stripe_payment_intent_id:`pi_test_${o.id}`,p_evidence:h.evidence(o)});
 await h.authority(false);await assert.rejects(h.seats(),/native_authority_disabled/);
 const review=await h.finalize(o);assert.equal(review.status,'payment_review');assert.equal(review.reason,'native_authority_disabled');
 assert.equal((await h.order(o.id)).payment_evidence.seat_hold_protected,true);assert.equal((await h.order(o.id)).status,'checkout_open');
 await h.authority(true);assert.equal((await h.seats()).unreconciledReserved,2);assert.equal((await h.seats()).remaining,3);
}));

test('real reservation and payment finalize once with inherited occupancy preserved',()=>fixture(async h=>{
 await h.retained(['retained-id']);await h.registration('retained-id');await h.authority(true);
 const a=await h.create(h.students(1),randomUUID(),{p_external_class_id:'123456'}),o=await h.bind(a.orderId);
 assert.equal((await h.finalize(o)).status,'paid');assert.equal((await h.finalize(o)).status,'paid');
 const seats=await h.seats();assert.equal(seats.registered,2);assert.equal(seats.holds,0);assert.equal(seats.remaining,0);assert.equal(seats.unreconciledReserved,0);
},2));

test('review fingerprint catches roster, hold, source or inventory drift before admission',()=>fixture(async h=>{
 await h.retained([]);const initial=await h.snapshot();await h.registration();
 await assert.rejects(h.authority(true,initial),/native_authority_snapshot_changed/);
 const second=await h.snapshot();await h.db.exec("insert into landerware_public_session_inventory(external_class_id,capacity,externally_registered,source) values('123456',5,0,'retained_fixture')");
 await assert.rejects(h.authority(true,second),/native_authority_snapshot_changed/);
 assert.equal((await h.db.query('select count(*) n from landerware_session_authority_events')).rows[0].n,0);
}));

test('decision replay is exact and later disabling appends history without deleting it',()=>fixture(async h=>{
 await h.retained([]);const snapshot=await h.snapshot(),decision=randomUUID();const first=await h.authority(true,snapshot,decision);
 const replay=await h.authority(true,snapshot,decision);assert.equal(replay.id,first.id);assert.equal(replay.replayed,true);
 await assert.rejects(h.authority(false,snapshot,decision),/native_authority_decision_reuse/);
 const disabled=await h.authority(false);assert.equal(disabled.revision,2);
 await assert.rejects(h.seats(),/native_authority_disabled/);
 assert.equal((await h.db.query('select count(*) n from landerware_session_authority_events')).rows[0].n,2);
}));

test('identity and native backend changes invalidate authority rather than falling open',()=>fixture(async h=>{
 await h.retained([]);await h.authority(true);
 await h.db.query("update class_sessions set start_at=start_at+interval '1 hour' where id=$1",[h.id]);
 await assert.rejects(h.seats(),/native_authority_identity_changed/);
}));

test('authority cannot activate an external backend or historical session or change visibility',()=>fixture(async h=>{
 await h.retained([]);await h.db.query("update class_sessions set registration_backend='enrollware',visibility='private' where id=$1",[h.id]);
 await assert.rejects(h.authority(true),/native_backend_required/);
 await h.authority(false);assert.equal((await h.db.query('select visibility from class_sessions where id=$1',[h.id])).rows[0].visibility,'private');
 await h.db.query("update class_sessions set record_scope='historical' where id=$1",[h.id]);await assert.rejects(h.snapshot(),/session_not_operational/);
}));

test('incomplete, malformed, duplicate or future retained evidence cannot establish authority',()=>fixture(async h=>{
 const bad=[{complete:false},{active_registration_count:2},{active_external_registration_ids:['legacy-a','legacy-a'],active_registration_count:2},
  {active_external_registration_ids:[123],active_registration_count:1},{source_observed_at:'not-a-date'},
  {source_observed_at:'2999-01-01T00:00:00Z'},{source_observed_at:'infinity'}];
 for(const evidence of bad){await h.retained(['legacy-a'],evidence);await assert.rejects(h.snapshot(),/native_occupancy_review_required/);}
}));

test('real service role may snapshot/admit/read but anonymous and authenticated cannot',()=>fixture(async h=>{
 await h.retained([]);
 // Match existing hosted service privileges needed by SECURITY INVOKER helpers.
 // The migration itself must restrict the new event table; no fixture grants after installation.
 for(const role of ['anon','authenticated']){
  await h.db.exec('set role '+role);await assert.rejects(h.snapshot(),/permission denied/);await h.db.exec('reset role');
 }
 await h.db.exec('set role service_role');await h.authority(true);assert.equal((await h.seats()).remaining,6);
 await assert.rejects(h.db.exec('delete from landerware_session_authority_events'),/permission denied/);await h.db.exec('reset role');
 const rows=(await h.db.query(`select p.proname,p.prosecdef,p.proconfig from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname like 'native_session_authority_%'`)).rows;
 assert.equal(rows.length,3);for(const row of rows){assert.equal(row.prosecdef,false);assert.ok(row.proconfig.includes('search_path=""'));if(row.proname==='native_session_authority_record')assert.ok(row.proconfig.includes('lock_timeout=2s'));}
}));


test('exact reviewed CRLF function body passes the normalized source guard',()=>fixture(async h=>{assert.equal((await h.seats()).remaining,6);},6,'crlf'));
test('changed reader body is rejected rather than normalized into approval',async()=>{await assert.rejects(()=>fixture(async()=>{},6,'drift'),/native_authority_reader_review_required/);});
