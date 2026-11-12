import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {preProfileFiles,profileMigration,profileRuntime,orderVersionMigration} from './helpers/native-checkout-migration-plan.mjs';
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const migration='supabase/migrations/20261111204230_native_publication_maintenance.sql';
test('publication maintenance is default-off, bounded, and releases only witnessed expired unpaid emptiness without deleting identity',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();try{
  for(const f of preProfileFiles)await db.exec(load(f));
  await db.exec("update courses set course_key='skills-session-only' where enrollware_course_id='509474'");
  for(const f of [profileMigration,profileRuntime,orderVersionMigration,'supabase/migrations/20261110231103_native_checkout_generated_session_lifecycle.sql',migration])await db.exec(load(f));
  const scalar=async(sql,args=[])=>Object.values((await db.query(sql,args)).rows[0])[0];
  const claim=async(n,day)=>{
   const wire={...await scalar('select skills_test.student($1)',[n]),learningPath:'skills-only',skillsContext:'cpr-aed'};
   const offer=await scalar('select skills_test.offer($1,$2)',[`cleanup-${day}`,day]);
   return scalar("select reserve_native_checkout_order($1,'native_skills_shared',1,'cpr-aed',null,$2::jsonb,$3::jsonb,$4::jsonb,5500)",[
    `${String(n).padStart(8,'0')}-aaaa-4aaa-8aaa-aaaaaaaaaaaa`,JSON.stringify(offer),JSON.stringify([wire]),JSON.stringify([{wire,selectedChoices:['skills_only']}])]);
  };
  const release=()=>scalar('select native_publication_release_expired()');
  await assert.rejects(release,/native_publication_maintenance_disabled/);
  const abandoned=await claim(1201,10),paid=await claim(1202,11),staff=await claim(1203,12),legacy=await claim(1204,13),fresh=await claim(1205,14),history=await claim(1206,15);
  for(const order of [abandoned,paid,staff,legacy,history])await db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id=$1",[order.orderId]);
  await db.query("update landerware_public_orders set payment_evidence='{\"payment_status\":\"paid\",\"seat_hold_protected\":true}' where id=$1",[paid.orderId]);
  await db.query("update class_sessions set public_notes='Staff managed' where id=$1",[staff.sessionId]);
  await db.query('delete from native_checkout_generated_sessions where class_session_id=$1',[legacy.sessionId]);
  await db.query("insert into registrations(customer_id,class_session_id,status,registration_source) values(gen_random_uuid(),$1,'cancelled','native')",[history.sessionId]);
  await db.exec('update native_publication_maintenance_policy set enabled=true');
  const before=await scalar('select count(*) from class_sessions');
  const first=await release();assert.equal(first.released,1);assert.equal(first.examined,1);assert.equal(first.batchLimit,32);
  assert.equal(await scalar('select count(*) from class_sessions'),before,'no session deletion');
  assert.equal(await scalar('select status from class_sessions where id=$1',[abandoned.sessionId]),'cancelled');
  for(const session of [paid,staff,legacy,fresh,history])assert.equal(await scalar('select status from class_sessions where id=$1',[session.sessionId]),'scheduled');
  assert.equal((await release()).released,0,'idempotent fresh batch');
  const externalId=await scalar('select external_class_id from class_sessions where id=$1',[abandoned.sessionId]);
  const tombstones=async(ids=[externalId])=>scalar('select native_released_scheduling_sessions($1::text[])',[ids]);
  const batch=await tombstones(),proof=batch.released_native_sessions;
  assert.equal(batch.complete,true);assert.deepEqual(batch.requested_external_class_ids,[externalId]);
  assert.equal(proof.length,1);assert.equal(proof[0].canonical_session_id,abandoned.sessionId);assert.equal(proof[0].authority,'native-generated-release.v1');
  for(const field of ['start_at','end_at','consumption_start_at','consumption_end_at'])assert.ok(field in proof[0]);
  // Cumulative history must not consume a future publication's proof budget.
  // These synthetic clones are already released, with no students or payments.
  await db.query(`create temporary table historical_releases as
    select gen_random_uuid() id, gen_random_uuid() order_id from generate_series(1,501)`);
  await db.query(`insert into class_sessions select (jsonb_populate_record(null::class_sessions,
    to_jsonb(s)||jsonb_build_object('id',h.id,'external_class_id','lw-'||h.id,'source_offer_id',h.id::text))).*
    from class_sessions s cross join historical_releases h where s.id=$1`,[abandoned.sessionId]);
  await db.query(`insert into landerware_public_orders select (jsonb_populate_record(null::landerware_public_orders,
    to_jsonb(o)||jsonb_build_object('id',h.order_id,'recovery_token',h.order_id,'idempotency_key',h.order_id::text,
      'class_session_id',h.id,'external_class_id','lw-'||h.id))).*
    from landerware_public_orders o cross join historical_releases h where o.id=$1`,[abandoned.orderId]);
  await db.exec(`insert into native_checkout_generated_sessions(class_session_id,identity_hash,state,released_at,release_reason)
    select s.id,native_checkout_generated_identity(s),'released',now(),'expired_unpaid_hold'
    from class_sessions s join historical_releases h on h.id=s.id`);
  assert.equal(await scalar("select count(*) from native_checkout_generated_sessions where state='released'"),502);
  assert.deepEqual((await tombstones()).released_native_sessions,proof,'unrequested history cannot block one retained ID');
  const retained=(await db.query("select 'lw-'||id id from historical_releases order by id")).rows.map(r=>r.id);
  const assembled=[];
  for(let offset=0;offset<retained.length;offset+=64){
   const ids=retained.slice(offset,offset+64),part=await tombstones(ids);
   assert.equal(part.complete,true);assert.deepEqual(part.requested_external_class_ids,ids);
   assembled.push(...part.released_native_sessions);
  }
  assert.equal(assembled.length,501);assert.equal(new Set(assembled.map(r=>r.external_class_id)).size,501);
  for(const invalid of [[],[externalId,externalId],['legacy'],[null],retained.slice(0,65)])await assert.rejects(()=>tombstones(invalid),/invalid_request/);
  for(const role of ['anon','authenticated'])assert.equal(await scalar("select has_function_privilege($1,$2,'execute')",[role,'native_released_scheduling_sessions(text[])']),false);
  assert.equal(await scalar("select provolatile from pg_proc where oid='native_released_scheduling_sessions(text[])'::regprocedure"),'s');
  await db.query("update class_sessions set public_notes='Changed after release' where id=$1",[abandoned.sessionId]);
  assert.deepEqual((await tombstones()).released_native_sessions,[],'post-release staff edit invalidates deletion of retained geometry');
  for(let n=0;n<33;n++){const held=await claim(1300+n,20+n);await db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id=$1",[held.orderId]);}
  assert.equal((await release()).released,32,'batch may transition at most 32 exact classes');
  assert.equal((await release()).released,1,'next cycle progresses remaining cleanup');
  for(const role of ['anon','authenticated'])assert.equal(await scalar('select has_function_privilege($1,$2,\'execute\')',[role,'native_publication_release_expired()']),false);
 }finally{await db.close();}
});
