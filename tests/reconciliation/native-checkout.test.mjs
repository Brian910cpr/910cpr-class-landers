import {PGlite} from '@electric-sql/pglite';
import fs from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {stripTypeScriptTypes} from 'node:module';
import {webcrypto,createHmac,randomUUID} from 'node:crypto';

const root=new URL('../../',import.meta.url),read=p=>fs.readFileSync(new URL(p,root),'utf8');
const migration='supabase/migrations/20261012060000_public_checkout_integrity.sql';
const secret='whsec_local_fixture_only';
import {setup} from './native-checkout-harness.mjs';
async function withDb(fn,capacity=6){const h=await setup(capacity);try{await fn(h)}finally{await h.db.close()}}

test('real PostgreSQL: paid public order creates one operational roster registration, one seat and durable confirmation; replay is inert',()=>withDb(async h=>{
 const created=await h.create(),o=await h.bind(created.orderId);
 assert.equal(Number((await h.db.query('select extract(epoch from hold_expires_at-created_at) as seconds from public.landerware_public_orders where id=$1',[o.id])).rows[0].seconds),1800);
 const before=await h.seats();assert.equal(before.holds,1);assert.equal(before.registered,0);
 const result=await h.finalize(o);assert.equal(result.status,'paid');assert.equal(result.registrations,1);
 const rows=(await h.db.query('select r.*,c.email from public.registrations r join public.customers c on c.id=r.customer_id')).rows;
 assert.equal(rows.length,1);assert.equal(rows[0].status,'registered');assert.equal(rows[0].class_session_id,h.id);
 assert.equal((await h.seats()).registered,1);assert.equal((await h.seats()).holds,0);assert.equal((await h.seats()).remaining,5);
 assert.equal((await h.db.query('select * from public.landerware_messages')).rows.length,1);
 assert.equal((await h.finalize(o)).idempotentReplay,true);
 assert.equal((await h.db.query('select * from public.registrations')).rows.length,1);
 assert.equal((await h.db.query('select * from public.landerware_messages')).rows.length,1);
 // Failed delivery cannot erase the already committed registration.
 await h.db.exec("update public.landerware_messages set delivery_status='failed'");
 assert.equal((await h.order(o.id)).status,'paid');assert.equal((await h.seats()).registered,1);
}));
test('multi-student transaction and simultaneous final-seat requests have no duplicate effects',()=>withDb(async h=>{
 const st=h.students(2),key=randomUUID();const a=await h.create(st,key),again=await h.create(st,key);
 assert.equal(a.orderId,again.orderId);assert.equal(again.idempotentReplay,true);
 await assert.rejects(h.create(h.students(1),key),/idempotency_conflict/);
 const o=await h.bind(a.orderId);await h.finalize(o);
 assert.equal((await h.seats()).registered,2);assert.equal((await h.seats()).remaining,1);
 const race=await Promise.allSettled([h.create(),h.create()]);
 assert.equal(race.filter(x=>x.status==='fulfilled').length,1);assert.equal(race.filter(x=>x.status==='rejected').length,1);
 assert.equal((await h.seats()).remaining,0);
},3));
test('expired abandoned holds free capacity; a late paid order cannot steal the last seat',()=>withDb(async h=>{
 const a=await h.create(),o=await h.bind(a.orderId);
 await h.db.query("update public.landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id=$1",[o.id]);
 assert.equal((await h.seats()).remaining,1);await h.create();
 const result=await h.finalize(o);assert.equal(result.status,'payment_review');assert.equal(result.reason,'paid_seat_unavailable');
 assert.equal((await h.seats()).registered,0);assert.equal((await h.db.query('select * from public.landerware_messages')).rows.length,0);
 assert.equal((await h.order(o.id)).reconciliation_error,'paid_seat_unavailable');
},1));
test('late paid event recovers an expired hold only when capacity remains',()=>withDb(async h=>{
 const a=await h.create(),o=await h.bind(a.orderId);await h.db.query("update public.landerware_public_orders set status='expired',hold_expires_at=now()-interval '1 minute' where id=$1",[o.id]);
 assert.equal((await h.finalize(o)).status,'paid');assert.equal((await h.seats()).registered,1);
},1));
test('wrong course, duplicate students and arbitrary invoice/free codes cannot reserve seats',()=>withDb(async h=>{
 const st=h.students(1);await assert.rejects(h.create([st[0],st[0]]),/duplicate_student/);
 await assert.rejects(h.create(st,randomUUID(),{p_course_id:'209806'}),/course_session_mismatch/);
 await h.db.exec(`update public.landerware_registration_catalog set billing_codes='[{"code":"invoice","active":true,"payer_mode":"corporate_invoice","type":"percent","amount":100}]' where course_id='359474'`);
 await assert.rejects(h.create(st,randomUUID(),{p_billing_code:'invoice'}),/billing_approval_required/);
 assert.equal((await h.seats()).holds,0);
}));

test('unavailable manuals, duplicate options and non-single quantities fail before a hold; valid options keep server pricing',()=>withDb(async h=>{
 await h.db.exec(`update public.landerware_registration_catalog set addons='[{"key":"aha_bls_provider_manual_ebook","unit_amount":2000,"active":true}]' where course_id='359474'`);
 const student=h.students(1)[0];
 await assert.rejects(h.create([{...student,manualChoice:'physical'}]),/physical_manual_unavailable/);
 await assert.rejects(h.create([{...student,addons:[{key:'aha_bls_provider_manual_ebook'},{key:'aha_bls_provider_manual_ebook'}]}]),/duplicate_addon/);
 for(const quantity of [0,2,1.5,'1',null]){
   await assert.rejects(h.create([{...student,addons:[{key:'aha_bls_provider_manual_ebook',quantity}]}]),/invalid_addon_quantity/);
 }
 await assert.rejects(h.create([{...student,addons:{key:'aha_bls_provider_manual_ebook'}}]),/invalid_addon/);
 await assert.rejects(h.create([{...student,addons:[{}]}]),/invalid_addon/);
 assert.equal((await h.seats()).holds,0);
 const result=await h.create([{...student,manualChoice:'ebook',addons:[{key:'aha_bls_provider_manual_ebook',quantity:1}]}]);
 assert.equal(result.total,9500);
 const order=await h.bind(result.orderId);assert.equal((await h.finalize(order)).status,'paid');
 assert.equal((await h.seats()).registered,1);
}));
test('invalid payment evidence cannot finalize; confirmation enqueue failure rolls back the whole transaction',()=>withDb(async h=>{
 const a=await h.create(),o=await h.bind(a.orderId);
 await assert.rejects(h.rpc('landerware_finalize_public_order',{p_order_id:o.id,p_stripe_payment_intent_id:'pi_test',p_evidence:{...h.evidence(o),amount_total:1}}),/payment_evidence_mismatch/);
 await assert.rejects(h.rpc('landerware_finalize_public_order',{p_order_id:o.id,p_stripe_payment_intent_id:'no_payment_required'}),/verified_payment_evidence_required/);
 await h.db.exec(`create function public.fail_message() returns trigger language plpgsql as $$begin raise exception 'synthetic_queue_failure'; end$$; create trigger synthetic_message_failure before insert on public.landerware_messages for each row execute function public.fail_message();`);
 await assert.rejects(h.finalize(o),/synthetic_queue_failure/);
 assert.equal((await h.seats()).registered,0);assert.equal((await h.order(o.id)).status,'checkout_open');
 await h.db.exec('drop trigger synthetic_message_failure on public.landerware_messages');
 assert.equal((await h.finalize(o)).status,'paid');
}));
test('external occupancy must be complete and fresh and is counted once alongside native seats',()=>withDb(async h=>{
 await h.db.query("update public.class_sessions set source='enrollware_reconciled',registration_backend='enrollware',external_class_id='123456' where id=$1",[h.id]);
 await assert.rejects(h.seats(),/external_reconciliation_required/);
 const p=(await h.db.query("insert into public.customers(first_name,last_name,email) values('External','Synthetic','external@example.test') returning id")).rows[0];
 await h.db.query("insert into public.registrations(customer_id,class_session_id,status,registration_source,external_registration_id) values($1,$2,'registered','enrollware','ext-local')",[p.id,h.id]);
 await h.db.query("update public.class_sessions set external_reconciliation=jsonb_build_object('complete',true,'source_observed_at',now(),'active_external_registration_ids',jsonb_build_array('ext-local'),'active_registration_count',1) where id=$1",[h.id]);
 assert.equal((await h.seats()).externallyRegistered,1);assert.equal((await h.seats()).remaining,1);
 await h.db.query("update public.class_sessions set external_reconciliation=external_reconciliation||jsonb_build_object('source_observed_at',now()-interval '2 hours') where id=$1",[h.id]);
 await assert.rejects(h.seats(),/external_reconciliation_required/);
},2));

test('signed webhook executes the real PostgreSQL public finalizer and replay confirms exactly once',()=>withDb(async h=>{
 const a=await h.create(),o=await h.bind(a.orderId);let handler;
 const client={from(table){let id;return {select(){return this},eq(_k,v){id=v;return this},async maybeSingle(){if(table==='landerware_integration_secrets')return {data:{secret_value:secret}};return {data:(await h.db.query(`select * from public.${table} where id=$1`,[id])).rows[0]||null}}}},async rpc(name,args){try{return {data:await h.rpc(name,args)}}catch(e){return {error:{message:e.message}}}}};
 const context=vm.createContext({Date,TextEncoder,crypto:webcrypto,Response,console,createClient:()=>client,Deno:{env:{get:k=>k==='STRIPE_EXPECTED_LIVEMODE'?'false':''},serve:fn=>handler=fn}});
 vm.runInContext(stripTypeScriptTypes(read('supabase/functions/stripe-registration-webhook/index.ts').replace(/^import .*;\r?\n/gm,'')),context);
 const event={id:'evt_local_signed',created:Math.floor(Date.now()/1000),livemode:false,type:'checkout.session.completed',data:{object:{...h.evidence(o),payment_intent:`pi_test_${o.id}`}}};
 const deliver=async value=>{const raw=JSON.stringify(value),ts=Math.floor(Date.now()/1000),sig=createHmac('sha256',secret).update(`${ts}.${raw}`).digest('hex');return handler(new Request('https://local.test/webhook',{method:'POST',body:raw,headers:{'stripe-signature':`t=${ts},v1=${sig}`}}))};
 assert.equal((await deliver(event)).status,200);assert.equal((await deliver(event)).status,200);
 assert.equal((await h.seats()).registered,1);assert.equal((await h.db.query('select * from public.landerware_messages')).rows.length,1);
 await deliver({...event,type:'checkout.session.async_payment_failed',data:{object:{...event.data.object,payment_status:'unpaid'}}});
 assert.equal((await h.order(o.id)).status,'paid');
}));

test('purchased eOptions retain server product identity and price after the catalog changes',()=>withDb(async h=>{
 await h.db.exec(`update public.landerware_registration_catalog set addons='[{"key":"current-book","display_name":"Current edition eManual","unit_amount":2000,"product_key":"current-edition","active":true}]' where course_id='359474'`);
 const student={...h.students(1)[0],addons:[{key:'current-book',quantity:1,unit_amount:1,product_key:'untrusted-client-product'}]};
 const a=await h.create([student]),o=await h.bind(a.orderId);assert.equal(o.total,9500);
 const stored=(await h.db.query('select selected_addons from public.landerware_public_order_students where order_id=$1',[o.id])).rows[0].selected_addons[0];
 assert.equal(stored.unit_amount,2000);assert.equal(stored.product_key,'current-edition');assert.equal(stored.quantity,1);
 await h.db.exec(`update public.landerware_registration_catalog set addons='[]' where course_id='359474'`);
 assert.equal((await h.finalize(o)).status,'paid');
}));

test('unknown or nonpositive eOption prices cannot become free purchases',()=>withDb(async h=>{
 for(const price of [0,-1,1.5,null,'unknown']){
  await h.db.query('update public.landerware_registration_catalog set addons=$1 where course_id=$2',[JSON.stringify([{key:'unpriced',unit_amount:price,active:true}]),'359474']);
  await assert.rejects(h.create([{...h.students(1)[0],addons:[{key:'unpriced',quantity:1}]}]),/invalid_addon_price/);
 }
}));

test('a native-looking source label cannot bypass external roster proof for an Enrollware class number',()=>withDb(async h=>{
 await h.db.query("update public.class_sessions set source='landerware_public_offer',registration_backend='landerware',external_class_id='123456' where id=$1",[h.id]);
 await assert.rejects(h.seats(),/external_reconciliation_required/);
}));
