import fs from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {setup} from './native-checkout-harness.mjs';

test('First Aid uses approved prices, includes online skills, and preserves the selected class time', async()=>{
 const h=await setup();
 try {
  const before=(await h.db.query('select start_at,end_at,consumption_start_at,consumption_end_at from public.class_sessions where id=$1',[h.id])).rows[0];
  const migration=fs.readFileSync(new URL('../../supabase/migrations/20261017220000_bls_first_aid_options.sql',import.meta.url),'utf8');
  await h.db.exec(migration);
  const catalog=(await h.db.query("select addons from public.landerware_registration_catalog where course_id='359474'")).rows[0];
  const online=catalog.addons.find(a=>a.key==='aha_heartsaver_first_aid_online');
  assert.equal(online.unit_amount,5000); assert.equal(online.includes_skills_testing,true);
  assert.equal(online.includes_student_ebook,true); assert.equal(online.additional_onsite_minutes,0);
  const onlineOrder=await h.create([{...h.students(1)[0],firstAidChoice:'online',addons:[{key:online.key,quantity:1}]}]);
  assert.equal(onlineOrder.total,12500);
  const savedOnline=(await h.db.query('select selected_addons from public.landerware_public_order_students where order_id=$1',[onlineOrder.orderId])).rows[0].selected_addons[0];
  assert.equal(savedOnline.includes_student_ebook,true);assert.equal(savedOnline.includes_skills_testing,true);
  assert.deepEqual(savedOnline.component_skus,['25-1402','25-3149']);
  const inPerson=await h.create([{...h.students(1)[0],firstAidChoice:'in-person',firstAidManualChoice:'own-copy',addons:[{key:'aha_heartsaver_first_aid_in_person',quantity:1}]}]);
  assert.equal(inPerson.total,13500);
  await assert.rejects(h.create([{...h.students(1)[0],firstAidChoice:'online',addons:[{key:online.key},{key:'aha_heartsaver_first_aid_manual_ebook'}]}]),/invalid_course_option/);
  const after=(await h.db.query('select start_at,end_at,consumption_start_at,consumption_end_at from public.class_sessions where id=$1',[h.id])).rows[0];
  assert.deepEqual(after,before);
  await h.db.exec(migration);
  assert.equal((await h.db.query("select jsonb_array_length(addons) n from public.landerware_registration_catalog where course_id='359474'")).rows[0].n,catalog.addons.length);
 } finally {await h.db.close()}
});

test('HeartCode requires an explicit path and completion acknowledgement, charging its online program only once', async()=>{
 const h=await setup();
 try {
  await h.db.exec(`update public.courses set enrollware_course_id='210549';
   insert into public.landerware_registration_catalog(course_id,course_name,unit_amount,addons)
   values('210549','HeartCode BLS',5500,'[{"key":"aha_heartcode_bls_online","unit_amount":4100,"active":true}]')
   on conflict(course_id) do update set unit_amount=5500,addons=excluded.addons;`);
  const create=st=>h.create([st],undefined,{p_course_id:'210549'});
  await assert.rejects(create({...h.students(1)[0],learningPath:'skills-only'}),/online_completion_ack_required/);
  await assert.rejects(create({...h.students(1)[0],learningPath:'online-and-skills',onlineCompletionAcknowledged:true}),/invalid_course_option/);
  const skills=await create({...h.students(1)[0],learningPath:'skills-only',onlineCompletionAcknowledged:true});
  assert.equal(skills.total,5500);
  const bundle=await create({...h.students(1)[0],learningPath:'online-and-skills',onlineCompletionAcknowledged:true,addons:[{key:'aha_heartcode_bls_online',quantity:1}]});
  assert.equal(bundle.total,9600);
 } finally {await h.db.close()}
});
test('current BLS product identities retain established store prices and snapshot their manufacturer SKU',async()=>{
 const h=await setup();try{
  await h.db.exec("insert into public.landerware_registration_catalog(course_id,course_name,unit_amount,addons) values('210549','HeartCode BLS',5500,'[]') on conflict do nothing");
  const migration=fs.readFileSync(new URL('../../supabase/migrations/20261017220000_bls_first_aid_options.sql',import.meta.url),'utf8');await h.db.exec(migration);
  const rows=(await h.db.query("select course_id,addons from public.landerware_registration_catalog where course_id in ('359474','210549')")).rows;
  const book=rows.find(r=>r.course_id==='359474').addons.find(a=>a.key==='aha_bls_provider_manual_ebook');assert.equal(book.manufacturer_sku,'25-3102');assert.equal(book.unit_amount,1749);
  const online=rows.find(r=>r.course_id==='210549').addons.find(a=>a.key==='aha_heartcode_bls_online');assert.equal(online.manufacturer_sku,'25-3553');assert.equal(online.unit_amount,4100);
  const order=await h.create([{...h.students(1)[0],manualChoice:'ebook',addons:[{key:book.key}]}]);assert.equal(order.total,9249);
  const selected=(await h.db.query('select selected_addons from public.landerware_public_order_students where order_id=$1',[order.orderId])).rows[0].selected_addons;assert.equal(selected[0].manufacturer_sku,'25-3102');
  await h.db.exec(migration);const again=(await h.db.query("select addons from public.landerware_registration_catalog where course_id='359474'")).rows[0].addons;assert.equal(again.filter(a=>a.key===book.key).length,1);
 }finally{await h.db.close()}
});
