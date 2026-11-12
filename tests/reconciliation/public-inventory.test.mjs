import test from 'node:test';
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {setup} from './native-checkout-harness.mjs';

async function fixture(fn,stock=1){
 const h=await setup(6);try{
  await h.db.exec(`insert into public.products(product_key,active,product_type,customer_price,fulfillment_mode) values('synthetic-code',true,'digital',20,'digital_code');
   update public.landerware_registration_catalog set addons='[{"key":"code","product_key":"synthetic-code","unit_amount":2000,"active":true}]' where course_id='359474';`);
  for(let i=0;i<stock;i++)await h.db.query("insert into public.product_inventory_units(product_id,status,secret_value) select id,'available',$1 from public.products",[`synthetic-not-a-real-code-${i}`]);
  h.student=()=>({...h.students(1)[0],addons:[{key:'code',quantity:1}]});
  h.units=async()=>(await h.db.query('select id,status,public_order_student_id,reserved_for_registration_id,exposed_at,fulfilled_at from public.product_inventory_units order by id')).rows;
  await fn(h);
 }finally{await h.db.close()}
}

test('one unit is reserved atomically, submit retry is inert, and paid replay assigns it once without exposing it',()=>fixture(async h=>{
 const st=[h.student()],a=await h.create(st,'repeat-submit');
 assert.equal(a.total,9500);assert.equal((await h.create(st,'repeat-submit')).orderId,a.orderId);
 assert.equal((await h.units()).filter(u=>u.status==='reserved').length,1);
 const studentId=(await h.db.query('select id from public.landerware_public_order_students')).rows[0].id;
 await h.rpc('landerware_reserve_public_addons',{p_student_id:studentId});
 assert.equal((await h.units()).filter(u=>u.status==='reserved').length,1);
 const snapshot=(await h.db.query('select selected_addons from public.landerware_public_order_students')).rows[0].selected_addons[0];
 assert.equal(snapshot.inventory_required,true);assert.equal(snapshot.fulfillment_mode,'digital_code');
 assert.doesNotMatch(JSON.stringify(snapshot),/synthetic-not-a-real-code|secret_value|inventory_unit_id/);
 const o=await h.bind(a.orderId);assert.equal((await h.finalize(o)).status,'paid');
 assert.equal((await h.finalize(o)).idempotentReplay,true);
 const u=(await h.units())[0];assert.ok(u.reserved_for_registration_id);
 assert.equal(u.exposed_at,null);assert.equal(u.fulfilled_at,null);
 assert.equal((await h.seats()).registered,1);assert.equal((await h.seats()).holds,0);
 await h.db.query("update public.landerware_public_orders set hold_expires_at=now()-interval '1 hour' where id=$1",[o.id]);
 await h.db.exec('select public.landerware_release_expired_public_inventory(id) from public.products');
 assert.equal((await h.units())[0].status,'reserved');
}));

test('two students competing for one code roll back both seats, students, inventory and order',()=>fixture(async h=>{
 await assert.rejects(h.create([h.student(),h.student()]),/addon_fulfillment_unavailable|addon_inventory_exhausted/);
 assert.equal((await h.units())[0].status,'available');assert.equal((await h.seats()).holds,0);
 assert.equal((await h.db.query('select count(*)::int n from public.landerware_public_orders')).rows[0].n,0);
 assert.equal((await h.db.query('select count(*)::int n from public.landerware_public_order_students')).rows[0].n,0);
}));

test('same-product aliases cannot reuse one unit for two purchased options',()=>fixture(async h=>{
 await h.db.exec(`update public.landerware_registration_catalog set addons=addons||'[{"key":"alias","product_key":"synthetic-code","unit_amount":2000,"active":true}]'::jsonb where course_id='359474'`);
 const st=h.student();st.addons.push({key:'alias',quantity:1});
 await assert.rejects(h.create([st]),/duplicate_product_addon/);
 assert.equal((await h.units())[0].status,'available');assert.equal((await h.seats()).holds,0);
}));

test('expired unpaid hold is reclaimed; late payment cannot steal a reassigned unit or create a seat',()=>fixture(async h=>{
 const a=await h.create([h.student()]),old=await h.bind(a.orderId);
 await h.db.query("update public.landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id=$1",[old.id]);
 const b=await h.create([h.student()]),current=await h.bind(b.orderId);
 assert.equal((await h.finalize(old)).reason,'paid_inventory_unavailable');
 assert.equal((await h.seats()).registered,0);
 assert.equal((await h.finalize(current)).status,'paid');
 assert.equal((await h.seats()).registered,1);
 assert.equal((await h.db.query('select count(*)::int n from public.registrations')).rows[0].n,1);
}));

test('late payment recovers its own unclaimed code, and confirmation failure rolls allocation back',()=>fixture(async h=>{
 const a=await h.create([h.student()]),o=await h.bind(a.orderId);
 await h.db.query("update public.landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id=$1",[o.id]);
 await h.db.exec(`create function public.reject_inventory_confirmation() returns trigger language plpgsql as $$begin raise exception 'synthetic_confirmation_failure'; end $$;
 create trigger fail_inventory_confirmation before insert on public.landerware_messages for each row execute function public.reject_inventory_confirmation();`);
 await assert.rejects(h.finalize(o),/synthetic_confirmation_failure/);
 assert.equal((await h.seats()).registered,0);assert.equal((await h.units())[0].reserved_for_registration_id,null);
 await h.db.exec('drop trigger fail_inventory_confirmation on public.landerware_messages');
 assert.equal((await h.finalize(o)).status,'paid');assert.equal((await h.seats()).registered,1);
}));

test('independent class requests cannot allocate the same last unit (embedded SQL concurrency)',()=>fixture(async h=>{
 const id=randomUUID(),external=`lw-${id}`;
 await h.db.query(`insert into public.class_sessions select (jsonb_populate_record(null::public.class_sessions,to_jsonb(s)||jsonb_build_object('id',$2::text,'external_class_id',$3::text))).* from public.class_sessions s where id=$1`,[h.id,id,external]);
 const outcomes=await Promise.allSettled([h.create([h.student()]),h.create([h.student()],randomUUID(),{p_external_class_id:external})]);
 assert.equal(outcomes.filter(o=>o.status==='fulfilled').length,1);
 assert.equal(outcomes.filter(o=>o.status==='rejected').length,1);
 assert.equal((await h.units()).filter(u=>u.status==='reserved').length,1);
 assert.equal((await h.db.query('select count(*)::int n from public.landerware_public_orders')).rows[0].n,1);
}));

test('exposed or foreign reservations cannot be reclaimed, and public roles cannot reserve codes',()=>fixture(async h=>{
 const a=await h.create([h.student()]);
 await h.db.query("update public.landerware_public_orders set hold_expires_at=now()-interval '1 hour' where id=$1",[a.orderId]);
 await h.db.exec('update public.product_inventory_units set exposed_at=now()');
 await assert.rejects(h.create([h.student()]),/addon_fulfillment_unavailable/);
 assert.equal((await h.units())[0].status,'reserved');
 await h.db.exec('set role anon');
 await assert.rejects(h.db.exec('select public.landerware_release_expired_public_inventory(gen_random_uuid())'),/permission denied/);
 await h.db.exec('reset role');
}));

test('payment-review evidence preserves inventory for staff reconciliation instead of recycling it',()=>fixture(async h=>{
 const a=await h.create([h.student()]),o=await h.bind(a.orderId);
 await h.db.query("update public.class_sessions set registration_status='closed' where id=$1",[h.id]);
 assert.equal((await h.finalize(o)).status,'payment_review');
 await h.db.query("update public.landerware_public_orders set hold_expires_at=now()-interval '1 hour' where id=$1",[o.id]);
 await h.db.exec('select public.landerware_release_expired_public_inventory(id) from public.products');
 assert.equal((await h.units())[0].status,'reserved');
 assert.equal((await h.units())[0].reserved_for_registration_id,null);
 const aState=await h.rpc('landerware_public_addon_state',{p_addon:{key:'code',product_key:'synthetic-code',unit_amount:2000},p_currency:'usd'});
 assert.equal(aState.available,false);
 assert.equal((await h.seats()).registered,0);
 await h.db.query("update public.class_sessions set registration_status='open' where id=$1",[h.id]);
 assert.equal((await h.finalize(o)).status,'paid');
 assert.equal((await h.finalize(o)).idempotentReplay,true);
 assert.equal((await h.seats()).registered,1);
}));

test('cancelled unpaid inventory is reusable but another workflow reservation is not',()=>fixture(async h=>{
 const a=await h.create([h.student()]);
 await h.db.query("update public.landerware_public_orders set status='cancelled' where id=$1",[a.orderId]);
 const b=await h.create([h.student()]);assert.notEqual(b.orderId,a.orderId);
 const st=(await h.db.query('select id from public.landerware_public_order_students where order_id=$1',[b.orderId])).rows[0];
 assert.equal((await h.units())[0].public_order_student_id,st.id);
 // Detach only the synthetic public binding to model an existing owner-workflow
 // reservation. No public-order expiry is allowed to recycle it.
 await h.db.exec('update public.product_inventory_units set public_order_student_id=null');
 await h.db.query("update public.landerware_public_orders set status='cancelled' where id=$1",[b.orderId]);
 await assert.rejects(h.create([h.student()]),/addon_fulfillment_unavailable/);
 assert.equal((await h.units())[0].status,'reserved');
}));
