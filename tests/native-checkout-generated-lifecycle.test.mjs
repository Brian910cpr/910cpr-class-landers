import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {preProfileFiles,profileMigration,profileRuntime,orderVersionMigration} from './helpers/native-checkout-migration-plan.mjs';
const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const lifecycle='supabase/reviewed/native-checkout-generated-session-lifecycle.sql';

test('only witnessed automatic unpaid empty sessions release; fresh reuse preserves identity and all collision/qualification checks',async()=>{
 const db=new PGlite();try{
  for(const f of preProfileFiles)await db.exec(load(f));
  await db.exec("update courses set course_key='skills-session-only' where enrollware_course_id='509474'");
  await db.exec(load(profileMigration));await db.exec(load(profileRuntime));await db.exec(load(orderVersionMigration));
  await db.exec(load(lifecycle));await db.exec(load(lifecycle));
  const scalar=async(sql,args=[])=>Object.values((await db.query(sql,args)).rows[0])[0];
  const key=n=>`${String(n).padStart(8,'0')}-aaaa-4aaa-8aaa-aaaaaaaaaaaa`;
  const claim=async(n,day,offerOverride)=>{
   const wire={...await scalar('select skills_test.student($1)',[n]),learningPath:'skills-only',skillsContext:'cpr-aed'};
   const offer=offerOverride||await scalar('select skills_test.offer($1,$2)',[`lifecycle-${day}`,day]);
   return scalar("select reserve_native_checkout_order($1,'native_skills_shared',1,'cpr-aed',null,$2::jsonb,$3::jsonb,$4::jsonb,5500)",[key(n),JSON.stringify(offer),JSON.stringify([wire]),JSON.stringify([{wire,selectedChoices:['skills_only']}])]);
  };
  const release=day=>scalar("select native_checkout_release_abandoned((skills_test.offer('window',$1)->>'startsAt')::timestamptz,(skills_test.offer('window',$1)->>'consumptionEndsAt')::timestamptz)",[day]);
  const expire=id=>db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id=$1",[id]);
  const abandoned=await claim(801,801);assert.equal(await scalar('select count(*) from native_checkout_generated_sessions'),1);
  assert.equal(await release(801),0,'an unexpired hold remains occupied');
  await expire(abandoned.orderId);assert.equal(await release(801),1);assert.equal(await release(801),0);
  assert.equal(await scalar('select status from class_sessions where id=$1',[abandoned.sessionId]),'cancelled');
  assert.equal(await scalar('select registration_status from class_sessions where id=$1',[abandoned.sessionId]),'closed');
  assert.equal(await scalar('select lifecycle_state from landerware_sessions where class_session_id=$1',[abandoned.sessionId]),'cancelled');
  assert.equal(await scalar('select status from landerware_public_orders where id=$1',[abandoned.orderId]),'expired');
  const retry=await claim(802,801);assert.equal(retry.sessionId,abandoned.sessionId);assert.notEqual(retry.orderId,abandoned.orderId);
  assert.equal(await scalar('select count(*) from class_sessions where id=$1',[retry.sessionId]),1);
  assert.equal(await scalar('select status from landerware_public_orders where id=$1',[abandoned.orderId]),'expired','old quote never resurrected');

  const paid=await claim(803,803);
  await db.query("update landerware_public_orders set stripe_checkout_session_id='cs_lifecycle' where id=$1",[paid.orderId]);
  const evidence={id:'cs_lifecycle',mode:'payment',payment_status:'paid',amount_total:5500,currency:'usd',metadata:{landerware_order_id:paid.orderId}};
  await scalar("select native_checkout_record_payment($1,'pi_lifecycle',$2::jsonb)",[paid.orderId,JSON.stringify(evidence)]);
  await expire(paid.orderId);assert.equal(await release(803),0,'verified paid-unfinalized holds never release');
  assert.equal(await scalar('select status from class_sessions where id=$1',[paid.sessionId]),'scheduled');

  const changed=await claim(804,804);await expire(changed.orderId);
  await db.query("update class_sessions set public_notes='Staff managed' where id=$1",[changed.sessionId]);
  assert.equal(await release(804),0,'staff-edited source rows lose automatic cleanup eligibility');
  const unknown=await claim(805,805);await expire(unknown.orderId);
  await db.query("update landerware_public_orders set payment_evidence='{\"unknown\":true}' where id=$1",[unknown.orderId]);
  assert.equal(await release(805),0,'unknown evidence is not unpaid proof');
  const preWitness=await claim(806,806);await expire(preWitness.orderId);
  await db.query('delete from native_checkout_generated_sessions where class_session_id=$1',[preWitness.sessionId]);
  assert.equal(await release(806),0,'historical/materialized-looking rows are never adopted');

  const blocked=await claim(807,807);await expire(blocked.orderId);assert.equal(await release(807),1);
  // A separate actual commitment prevents reopening, even though the old hold
  // is gone. No chain cancellation or shared ancestry is involved.
  await db.query(`insert into class_sessions(source,status,course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,record_scope)
    select 'manual','scheduled',course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,'manual','private','closed','fixture-surviving-anchor','operational' from class_sessions where id=$1`,[blocked.sessionId]);
  await assert.rejects(claim(808,807),/session_not_available/);
  assert.equal(await scalar("select status from class_sessions where external_class_id='fixture-surviving-anchor'"),'scheduled');
  assert.equal(await scalar('select status from class_sessions where id=$1',[blocked.sessionId]),'cancelled');

  const gap=await claim(809,809);await expire(gap.orderId);
  const overlapping=await scalar("select skills_test.offer('another-family-position',809,30)");
  await assert.rejects(claim(810,809,overlapping),/session_not_available/);
  assert.equal(await release(809),1);
  const alternate=await claim(810,809,overlapping);assert.notEqual(alternate.sessionId,gap.sessionId);
  await assert.rejects(claim(811,809),/session_not_available/,'released identity cannot reopen across a new commitment');
  assert.equal(await scalar('select status from class_sessions where id=$1',[alternate.sessionId]),'scheduled');

  const qualification=await claim(812,812);await expire(qualification.orderId);assert.equal(await release(812),1);
  await db.exec("update instructor_qualifications set status='inactive'");
  await assert.rejects(claim(813,812),/session_not_available/,'released classes still need current instructor qualification');
  assert.equal(await scalar('select status from class_sessions where id=$1',[qualification.sessionId]),'cancelled');

  for(const role of ['anon','authenticated']){
   assert.equal(await scalar(`select has_table_privilege('${role}','native_checkout_generated_sessions','select')`),false);
   assert.equal(await scalar(`select has_function_privilege('${role}','native_checkout_release_abandoned(timestamptz,timestamptz)','execute')`),false);
   assert.equal(await scalar(`select has_function_privilege('${role}','native_checkout_reopen_generated(uuid)','execute')`),false);
  }
 }finally{await db.close();}
});
