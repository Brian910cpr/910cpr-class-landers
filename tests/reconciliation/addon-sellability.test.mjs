import test from 'node:test';
import assert from 'node:assert/strict';
import {setup} from './native-checkout-harness.mjs';

test('canonical mapping and price are required; digital availability requires an eligible canonical unit',async()=>{
 const h=await setup();try{
  const state=a=>h.rpc('landerware_public_addon_state',{p_addon:a,p_currency:'usd'});
  const a={key:'optional-service',product_key:'canonical-service',unit_amount:1749,active:true};
  assert.equal((await state(a)).reason,'product_mapping_required');
  await h.db.exec("insert into public.products(product_key,active,product_type,customer_price,fulfillment_mode) values('canonical-service',false,'service',20,'manual')");
  assert.equal((await state(a)).available,false);
  await h.db.exec('update public.products set active=true');
  assert.equal((await state(a)).reason,'product_price_mismatch');
  await h.db.exec('update public.products set customer_price=17.49');
  assert.equal((await state(a)).available,true);
  assert.equal((await state({...a,includes_online_program:true})).reason,'inventory_reservation_required');
  await h.db.exec("update public.products set product_type='digital',fulfillment_mode='digital_code'");
  assert.equal((await state(a)).available,false);
  await h.db.exec("insert into public.product_inventory_units(product_id,status) select id,'available' from public.products");
  assert.equal((await state(a)).available,true);
  assert.equal((await state({...a,component_skus:['a','b']})).reason,'component_mapping_required');
 }finally{await h.db.close()}
});

test('unfulfillable option rolls back every student, hold and order',async()=>{
 const h=await setup();try{
  await h.db.exec(`update public.landerware_registration_catalog set addons='[{"key":"legacy-book","unit_amount":1749,"active":true}]' where course_id='359474'`);
  const st=h.students(2);st[1].addons=[{key:'legacy-book',quantity:1,product_key:'client-cannot-map-this'}];
  await assert.rejects(h.create(st),/addon_fulfillment_unavailable/);
  assert.equal((await h.seats()).holds,0);
  for(const table of ['landerware_public_orders','landerware_public_order_students','registrations'])
   assert.equal((await h.db.query(`select count(*)::int n from public.${table}`)).rows[0].n,0);
 }finally{await h.db.close()}
});

test('mapped service uses authoritative cents and product id; paid replay preserves snapshot',async()=>{
 const h=await setup(1);try{
  await h.db.exec(`insert into public.products(product_key,active,product_type,customer_price,fulfillment_mode) values('first-aid-service',true,'service',60,'manual');
   update public.landerware_registration_catalog set addons='[{"key":"service","product_key":"first-aid-service","unit_amount":6000,"active":true}]' where course_id='359474'`);
  const st=[{...h.students(1)[0],addons:[{key:'service',quantity:1,unit_amount:1,product_key:'spoofed'}]}];
  const created=await h.create(st,'same-submit');assert.equal(created.total,13500);
  assert.equal((await h.create(st,'same-submit')).orderId,created.orderId);
  const o=await h.bind(created.orderId);await h.finalize(o);
  await h.db.exec("update public.products set active=false,customer_price=999");
  assert.equal((await h.finalize(o)).idempotentReplay,true);
  const snap=(await h.db.query('select selected_addons from public.landerware_public_order_students')).rows[0].selected_addons[0];
  assert.equal(snap.unit_amount,6000);assert.equal(snap.product_key,'first-aid-service');
  assert.equal(snap.product_id,(await h.db.query('select id from public.products')).rows[0].id);
  assert.equal((await h.seats()).registered,1);assert.equal((await h.seats()).holds,0);
 }finally{await h.db.close()}
});
test('duplicate late paid callbacks cannot steal a code reclaimed by another order or approve its delivery',async()=>{
 const h=await setup(2);try{
  await h.db.exec(`insert into public.products(product_key,active,product_type,customer_price,fulfillment_mode) values('fixture-code',true,'online_program',20,'digital_code');
   insert into public.product_inventory_units(product_id,secret_value,status) select id,'SYNTHETIC-NONREDEEMABLE','available' from public.products;
   update public.landerware_registration_catalog set addons='[{"key":"fixture-code","product_key":"fixture-code","unit_amount":2000,"active":true}]' where course_id='359474'`);
  const make=async()=>h.create([{...h.students(1)[0],addons:[{key:'fixture-code',quantity:1}]}]);
  const first=await h.bind((await make()).orderId);
  await h.db.query("update public.landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id=$1",[first.id]);
  const second=await h.bind((await make()).orderId);
  for(let i=0;i<2;i++){const late=await h.finalize(first);assert.equal(late.status,'payment_review');assert.equal(late.reason,'paid_inventory_unavailable');}
  assert.equal((await h.db.query('select count(*)::int n from public.registrations')).rows[0].n,0);
  assert.equal((await h.finalize(second)).status,'paid');assert.equal((await h.finalize(second)).idempotentReplay,true);
  const unit=(await h.db.query('select u.*,st.order_id from product_inventory_units u join landerware_public_order_students st on st.id=u.public_order_student_id')).rows[0];
  assert.equal(unit.order_id,second.id);assert.ok(unit.reserved_for_registration_id);assert.equal(unit.exposed_at,null);assert.equal(unit.fulfilled_at,null);
  assert.equal((await h.db.query('select count(*)::int n from public.registrations')).rows[0].n,1);
 }finally{await h.db.close();}
});
test('verified payment survives finalization failure and protects its existing seat/code through expiry until retry',async()=>{
 const h=await setup(1);try{
  assert.equal((await h.db.query("select has_function_privilege('anon','public.landerware_record_public_payment(uuid,text,jsonb)','execute') allowed")).rows[0].allowed,false);
  await h.db.exec(`insert into products(product_key,active,product_type,customer_price,fulfillment_mode) values('fixture-paid-code',true,'online_program',20,'digital_code');
   insert into product_inventory_units(product_id,secret_value,status) select id,'SYNTHETIC-PAID-CODE','available' from products;
   update landerware_registration_catalog set addons='[{"key":"fixture-paid-code","product_key":"fixture-paid-code","unit_amount":2000,"active":true}]' where course_id='359474';`);
  const student={...h.students(1)[0],addons:[{key:'fixture-paid-code',quantity:1}]},o=await h.bind((await h.create([student])).orderId);
  await h.db.exec("create function fail_paid_queue() returns trigger language plpgsql as $$begin raise exception 'fixture_queue_failure';end$$;create trigger fail_paid_queue before insert on landerware_messages for each row execute function fail_paid_queue();");
  await assert.rejects(h.finalize(o),/fixture_queue_failure/);
  await h.db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id=$1",[o.id]);
  assert.equal((await h.seats()).remaining,0,'an observed paid hold must not become available because roster/outbox commit failed');
  await assert.rejects(h.create([{...h.students(1)[0],addons:student.addons}]),/insufficient_seats/);
  const saved=await h.order(o.id);assert.equal(saved.payment_evidence.payment_status,'paid');
  await h.db.exec('drop trigger fail_paid_queue on landerware_messages');
  assert.equal((await h.finalize(o)).status,'paid');assert.equal((await h.finalize(o)).idempotentReplay,true);
  const unit=(await h.db.query('select * from product_inventory_units')).rows[0];assert.ok(unit.reserved_for_registration_id);assert.equal(unit.exposed_at,null);assert.equal(unit.fulfilled_at,null);
  assert.equal((await h.db.query('select count(*)::int n from registrations')).rows[0].n,1);
 }finally{await h.db.close();}
});
