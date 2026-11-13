import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {preProfileFiles,profileMigration,fullCourseMigration,codeDeliveryMigration} from './helpers/native-checkout-migration-plan.mjs';
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8').replaceAll('\r\n','\n');
export async function proveCombinedCheckout(db,race=null){
  for(const p of preProfileFiles)await db.exec(load(p));
  await db.exec("insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price) values('aha-bls-provider','Fixture BLS','209806',120,30,6,75),('aha-bls-provider-renewal','Fixture Renewal','359474',120,30,6,75); insert into people(person_key,display_name) values('brian','Brian Ennis');");
  for(const p of [profileMigration,'supabase/migrations/20261110231103_native_checkout_generated_session_lifecycle.sql',fullCourseMigration,'supabase/migrations/20261111190525_native_full_course_policy_service_access.sql','supabase/migrations/20261111195655_native_full_course_v2_policy.sql','supabase/reviewed/native-advanced-course-checkout.sql',codeDeliveryMigration,'supabase/reviewed/native-combined-checkout.sql'])await db.exec(load(p));
  const scalar=async(q,args=[])=>Object.values((await db.query(q,args)).rows[0])[0];
  assert.equal(await scalar('select count(*) from native_checkout_basket_course_policy'),0,'no invented activation/mappings');
  await db.exec(`insert into landerware_registration_profiles select (jsonb_populate_record(null::landerware_registration_profiles,to_jsonb(p)||'{"profile_key":"fixture_acls","course_id":"fixture-acls","active":true}')).* from landerware_registration_profiles p where profile_key='native_bls_initial';
   insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price,registration_profile_key) values('fixture-acls','Fixture ACLS','241108',240,0,2,225,'fixture_acls');
   update landerware_registration_catalog set unit_amount=22500,active=true,addons='[]' where course_id='241108';
   insert into instructor_qualifications(instructor_id,course_id,status,expires_at) select p.id,c.id,'active',now()+interval '1 year' from people p cross join courses c where p.person_key='skills-test' and c.course_key='fixture-acls';
   update native_advanced_course_policy set course_id=(select id from courses where course_key='fixture-acls'),profile_key='fixture_acls',setup_minutes=0,cleanup_minutes=0,max_students=2,location_id=(select id from locations where location_key='910cpr-office-shipyard'),resource_label='FIXTURE ROOM',location_label='FIXTURE LOCATION',enabled=true,publication_enabled=true,verified=true,evidence=evidence||'{"buffers":"LOCAL FIXTURE","capacity":"LOCAL FIXTURE","identity":"LOCAL FIXTURE"}' where course_number='241108';
   insert into native_advanced_instructor_scopes select '241108',id,'fixture-calendar-person',array['fixture-calendar'],true,'LOCAL FIXTURE' from people where person_key='skills-test';
   insert into native_checkout_basket_course_policy values('241108','ACLS','241108','fixture_acls',22500,null,true,true,'LOCAL FIXTURE'),('209806','BLS','209806','native_bls_initial',7500,null,true,true,'LOCAL FIXTURE');
   insert into class_sessions(source,status,record_scope,course_id,start_at,end_at,consumption_start_at,consumption_end_at,timezone,location_id,lead_instructor_id,visibility,registration_backend,registration_status,max_students,external_class_id)
   select 'landerware_event','scheduled','operational',c.id,((current_date+10)::timestamp+interval '10 hours') at time zone 'America/New_York',((current_date+10)::timestamp+interval '10 hours'+make_interval(mins=>c.duration_minutes)) at time zone 'America/New_York',((current_date+10)::timestamp+interval '10 hours') at time zone 'America/New_York',((current_date+10)::timestamp+interval '10 hours'+make_interval(mins=>c.duration_minutes)) at time zone 'America/New_York','America/New_York',l.id,p.id,'public','landerware','open',2,case when c.enrollware_course_id='241108' then 'lw-11111111-1111-4111-8111-111111111111' else 'lw-22222222-2222-4222-8222-222222222222' end from courses c cross join people p cross join locations l where c.enrollware_course_id in ('241108','209806') and p.person_key='skills-test' and l.location_key='910cpr-office-shipyard';
   update class_sessions set start_at=start_at+interval '1 day',end_at=end_at+interval '1 day',consumption_start_at=consumption_start_at+interval '1 day',consumption_end_at=consumption_end_at+interval '1 day' where external_class_id='lw-22222222-2222-4222-8222-222222222222';`);
  // Synthetic digital manual stock, never a real SKU/code or hosted unit.
  await db.exec(`insert into products(product_key,active,product_type,customer_price,fulfillment_mode) values('TEST-BASKET-MANUAL',true,'digital_manual',20,'digital_code');
   insert into product_inventory_units(product_id,secret_value,status) select p.id,'TEST-ONLY-NOT-A-LEARNER-CODE-'||n,'available' from products p cross join generate_series(1,3) n where p.product_key='TEST-BASKET-MANUAL';
   update landerware_registration_catalog set addons='[{"key":"aha_bls_provider_manual_ebook","unit_amount":2000,"active":true,"product_key":"TEST-BASKET-MANUAL"}]' where course_id='209806';
   insert into native_checkout_basket_component_policy select '209806','aha_bls_provider_manual_ebook',id,'ebook',2000,true,'LOCAL FIXTURE ONLY' from products where product_key='TEST-BASKET-MANUAL';`);
  assert.equal(await scalar("select native_advanced_existing_session_ready('241108','lw-11111111-1111-4111-8111-111111111111')"),true);
  const student={firstName:'Synthetic',lastName:'Fixture',email:'basket@example.invalid',phone:'2025550100',manualChoice:'own-copy',firstAidChoice:'none',addons:[]};
  const input={wire:student,selectedChoices:['own_copy','no_first_aid'],submitted:{fields:{first_name:'Synthetic',last_name:'Fixture',email:'basket@example.invalid',phone:'2025550100'},selectedChoices:['own_copy','no_first_aid']}};
  const item=(course,profile,id,price)=>({courseNumber:course,profileKey:profile,profileVersion:1,context:'',externalId:id,offer:{},students:[student],inputs:[input],expectedTotal:price});
  const items=[item('241108','fixture_acls','lw-11111111-1111-4111-8111-111111111111',22500),item('209806','native_bls_initial','lw-22222222-2222-4222-8222-222222222222',7500)];
  items[1].students=[{...student,manualChoice:'ebook',addons:[{key:'aha_bls_provider_manual_ebook',quantity:1}]}];items[1].inputs=[{...input,wire:items[1].students[0],selectedChoices:['manual_ebook','no_first_aid'],submitted:{...input.submitted,selectedChoices:['manual_ebook','no_first_aid']}}];items[1].expectedTotal=9500;
  const key='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
  const reserve=(k=key,x=items)=>scalar('select reserve_native_checkout_basket($1,$2::jsonb)',[k,JSON.stringify(x)]);
  const saved=await reserve();assert.equal(saved.amountCents,31250);assert.equal(saved.items.length,2);assert.equal(saved.lines.filter(l=>l.kind==='session')[1].discountCents,750);assert.equal(saved.lines.find(l=>l.kind==='ebook').totalCents,2000);assert.equal(saved.lines.find(l=>l.primary).discountCents,0);
  assert.equal((await reserve()).basketId,saved.basketId);assert.equal(await scalar('select count(*) from landerware_public_orders'),2);
  await assert.rejects(reserve(key,[...items].reverse()),/idempotency_conflict/);
  await assert.rejects(reserve('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',[items[0],{...items[1],expectedTotal:1}]),/student_already_held|profile_price_mismatch/);
  const intent='pi_fixture_basket',session='cs_fixture_basket';
  await db.query('update native_checkout_baskets set stripe_checkout_session_id=$1 where id=$2',[session,saved.basketId]);
  const evidence={id:session,mode:'payment',payment_status:'paid',amount_total:31250,currency:'usd',metadata:{landerware_basket_id:saved.basketId},livemode:false};
  const record=e=>scalar('select native_checkout_basket_record_payment($1,$2,$3::jsonb)',[saved.basketId,intent,JSON.stringify(e)]);
  await assert.rejects(record({...evidence,amount_total:1}),/payment_evidence_mismatch/);assert.equal((await record(evidence)).recorded,true);
  assert.equal(await scalar("select count(*) from landerware_public_orders where payment_evidence->>'payment_status'='paid'"),2);
  const finalize=()=>scalar('select native_checkout_basket_finalize($1,$2,$3::jsonb)',[saved.basketId,intent,JSON.stringify(evidence)]);

  // A failure in one course must not commit the other course's registration.
  await db.exec(`create function skills_test.basket_partial_failure_probe(p_basket uuid,p_intent text,p_evidence jsonb,p_mode text) returns boolean language plpgsql as $$
   declare before_count integer; r jsonb;
   begin
    select count(*) into before_count from public.registrations;
    begin
     if p_mode='cancelled_order' then update public.landerware_public_orders set status='cancelled' where id=(select order_id from public.native_checkout_basket_items where basket_id=p_basket and position=1);
     else update public.class_sessions set registration_status='closed' where id=(select o.class_session_id from public.landerware_public_orders o join public.native_checkout_basket_items i on i.order_id=o.id where i.basket_id=p_basket and i.position=1); end if;
     r:=public.native_checkout_basket_finalize(p_basket,p_intent,p_evidence);
     if r->>'status' is distinct from 'payment_review' or (select count(*) from public.registrations)<>before_count or exists(select 1 from public.landerware_public_orders o join public.native_checkout_basket_items i on i.order_id=o.id where i.basket_id=p_basket and o.status='paid') then raise exception 'partial_basket_commit'; end if;
     raise exception using errcode='P0002',message='rollback synthetic terminal-state probe';
    exception when no_data_found then return true; end;
   end $$;`);
  for(const mode of ['cancelled_order','closed_class'])assert.equal(await scalar('select skills_test.basket_partial_failure_probe($1,$2,$3::jsonb,$4)',[saved.basketId,intent,JSON.stringify(evidence),mode]),true);
  assert.equal(await scalar('select count(*) from registrations'),0);
  await db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id in(select order_id from native_checkout_basket_items where basket_id=$1)",[saved.basketId]);
  assert.equal(await scalar("select count(*) from landerware_public_orders where payment_evidence->>'seat_hold_protected'='true'"),2);
  const nextEvent={...evidence,stripeEventId:'evt_distinct_verified_replay'};
  assert.equal((await record(nextEvent)).replay,true);
  const paid=await scalar('select native_checkout_basket_finalize($1,$2,$3::jsonb)',[saved.basketId,intent,JSON.stringify(nextEvent)]);assert.equal(paid.status,'paid');assert.equal(await scalar("select count(*) from registrations where registration_source='landerware_native_checkout'"),2);
  assert.equal((await finalize()).status,'paid');assert.equal(await scalar("select count(*) from registrations where registration_source='landerware_native_checkout'"),2);
  assert.equal(await scalar('select count(distinct class_session_id) from registrations'),2);
  assert.equal(await scalar('select count(*) from landerware_public_orders o where native_checkout_order_payment_verified(o)'),2,'each paid child uses its verified aggregate allocation');
  await db.query("update native_checkout_baskets set status='refunded' where id=$1",[saved.basketId]);
  assert.equal(await scalar('select count(*) from landerware_public_orders o where native_checkout_order_payment_verified(o)'),0,'terminal parent stops pending code eligibility without inventing another charge');
  assert.equal((await finalize()).status,'refunded','payment callbacks cannot resurrect a terminal basket');
  await db.query("update native_checkout_baskets set status='paid' where id=$1",[saved.basketId]);

  assert.equal(await scalar('select count(*) from landerware_public_orders where stripe_checkout_session_id is not null'),0,'never manufacture separate processor sessions');
  for(const role of ['anon','authenticated'])assert.equal(await scalar("select has_function_privilege($1,'reserve_native_checkout_basket(uuid,jsonb,jsonb)','EXECUTE')",[role]),false);

 if(race)await race({items,saved,scalar});
}
