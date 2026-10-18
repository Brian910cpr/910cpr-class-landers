import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {setup} from './native-checkout-harness.mjs';
const migration=fs.readFileSync(new URL('../../supabase/migrations/20261017200000_message_operational_links.sql',import.meta.url),'utf8');
test('paid confirmation links to the actual operational customer and registration; backfill is repeatable',async()=>{
 const h=await setup();try{
  await h.db.exec('alter table public.landerware_messages add column created_at timestamptz default now()');
  const a=await h.create(),order=await h.bind(a.orderId);await h.finalize(order);
  await h.db.exec(migration);
  let messages=(await h.db.query("select m.customer_id,m.operational_registration_id,r.customer_id as expected_customer from public.landerware_messages m join public.registrations r on r.id=m.operational_registration_id where m.template_key='retail-paid-confirmation-v3'")).rows;
  assert.equal(messages.length,1);assert.equal(messages[0].customer_id,messages[0].expected_customer);
  await h.db.exec(migration);
  const b=await h.create(),second=await h.bind(b.orderId);await h.finalize(second);
  messages=(await h.db.query("select customer_id,operational_registration_id from public.landerware_messages where template_key='retail-paid-confirmation-v3'")).rows;
  assert.equal(messages.length,2);assert.ok(messages.every(m=>m.customer_id&&m.operational_registration_id));
  await h.db.exec("insert into public.landerware_messages(template_key,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key) values('retail-paid-confirmation-v3','unmatched@example.test','Unmatched','Synthetic','test','pending','not-an-order')");
  const unmatched=(await h.db.query("select customer_id,operational_registration_id from public.landerware_messages where idempotency_key='not-an-order'")).rows[0];
  assert.equal(unmatched.customer_id,null);assert.equal(unmatched.operational_registration_id,null);
 }finally{await h.db.close()}
});
