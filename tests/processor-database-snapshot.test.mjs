import test from 'node:test';import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {processorDatabaseSnapshot} from './helpers/processor-database-snapshot.mjs';
const id='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
test('read-only snapshot executes against actual schema fixture and follows canonical registration/message ownership',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  await db.exec(readFileSync(new URL('./helpers/reschedule-production-schema.sql',import.meta.url),'utf8'));
  await db.exec(`insert into landerware_public_orders(id,idempotency_key,external_class_id,course_id,payer_email,status,total) values('${id}','synthetic-snapshot','synthetic-session','209806','synthetic@example.invalid','held',7500);
   insert into landerware_public_order_students(order_id,first_name,last_name,email,phone,unit_amount) values('${id}','Synthetic','Fixture','synthetic@example.invalid','2025550100',7500);`);
  const snapshot=processorDatabaseSnapshot({query:sql=>db.query(sql),orderId:id});
  const held=await snapshot();assert.equal(held.status,'held');assert.deepEqual(held.registrationIds,[]);assert.equal(held.occupiedSeats,0);assert.equal(held.confirmationCount,0);
  // Match the native-stack psql adapter's row_to_json wrapping, not only the
  // direct PGlite result shape; exercise all three credentialless base targets.
  const nativeQuery=async text=>db.query(`select row_to_json(q) as record from (${text}) q`);
  const wrapped=processorDatabaseSnapshot({query:async text=>({rows:(await nativeQuery(text)).rows.map(r=>r.record)}),orderId:id});
  for(const [course,amount] of [['209806',7500],['359474',7500],['509474',5500]]){
   await db.query('update landerware_public_orders set course_id=$1,total=$2 where id=$3',[course,amount,id]);
   const actual=await wrapped();assert.equal(actual.course,course);assert.equal(actual.amountCents,amount);assert.equal(actual.status,'held');assert.equal(actual.occupiedSeats,0);assert.deepEqual(actual.registrationIds,[]);
  }
  await db.query('update landerware_public_orders set course_id=$1,total=$2 where id=$3',['209806',7500,id]);
  // Isolated test-only rows; no processor evidence or real payment is fabricated.
  await db.exec(`update landerware_public_orders set class_session_id='11111111-1111-4111-8111-111111111111' where id='${id}';
   insert into registrations(id,customer_id,class_session_id,status,registration_source) values('cccccccc-cccc-4ccc-8ccc-cccccccccccc','dddddddd-dddd-4ddd-8ddd-dddddddddddd','11111111-1111-4111-8111-111111111111','registered','landerware_native_checkout');
   update landerware_public_order_students set registration_id='cccccccc-cccc-4ccc-8ccc-cccccccccccc' where order_id='${id}';
   insert into landerware_messages(template_key,recipient,subject,body_text,idempotency_key) values('retail-paid-confirmation-v3','synthetic@example.invalid','Synthetic','LOCAL FIXTURE','public-order-paid:${id}:synthetic@example.invalid'),('retail-checkout-recovery-v2','synthetic@example.invalid','Synthetic','LOCAL FIXTURE','public-order-recovery:${id}'),('retail-paid-confirmation-v3','other@example.invalid','Synthetic','LOCAL FIXTURE','public-order-paid:${id}:other@example.invalid');`);
  const linked=await snapshot();assert.equal(linked.status,'held');assert.deepEqual(linked.registrationIds,['cccccccc-cccc-4ccc-8ccc-cccccccccccc']);assert.equal(linked.occupiedSeats,1);assert.equal(linked.confirmationCount,1);assert.doesNotMatch(JSON.stringify(linked),/example.invalid|LOCAL FIXTURE/);
  await db.exec("update registrations set status='cancelled'");assert.equal((await snapshot()).occupiedSeats,0);
  await db.exec("update registrations set status='registered',class_session_id='22222222-2222-4222-8222-222222222222'");assert.deepEqual((await snapshot()).registrationIds,[]);
  await assert.rejects(processorDatabaseSnapshot({query:sql=>db.query(sql),orderId:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'})(),/snapshot_order_not_found/);
 }finally{await db.close();}
});
test('malformed order identity is rejected before any database access',()=>{
 assert.throws(()=>processorDatabaseSnapshot({query:()=>{throw Error('must not query');},orderId:"x' or true --"}),/invalid_snapshot_order/);
});
