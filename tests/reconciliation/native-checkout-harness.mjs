import {PGlite} from '@electric-sql/pglite';
import fs from 'node:fs';
import vm from 'node:vm';
import {stripTypeScriptTypes} from 'node:module';
import {webcrypto,createHmac,randomUUID} from 'node:crypto';

const root=new URL('../../',import.meta.url),read=p=>fs.readFileSync(new URL(p,root),'utf8');
const migration='supabase/migrations/20261012060000_public_checkout_integrity.sql';
export async function setup(capacity=6){
 const db=new PGlite();
 await db.exec(read('tests/reconciliation/schema.sql'));
 await db.exec(`alter table public.class_sessions add column external_reconciliation jsonb not null default '{}';
 create table public.landerware_messages(id uuid primary key default gen_random_uuid(),template_key text not null,channel text default 'email',recipient text,subject text not null,body_text text not null,delivery_provider text not null,delivery_status text not null check(delivery_status in ('pending','sent','failed')),idempotency_key text not null unique);
 create table public.landerware_retail_orders(id uuid primary key,total_amount_cents integer,currency text,stripe_checkout_session_id text,status text);
 insert into public.courses(course_key,name,enrollware_course_id) values('aha-bls-provider-renewal','AHA BLS Provider Renewal','359474');
 insert into public.locations(location_key,name,scheduling_status) values('910cpr-office-shipyard','Shipyard Blvd','active');
 insert into public.people(person_key,display_name) values('brian','Brian Ennis');`);
 await db.exec(read('supabase/migrations/20260909220000_native_public_checkout.sql'));
 await db.exec(read('supabase/migrations/20260930050000_per_student_public_billing_codes.sql'));
 await db.exec(read(migration));
 const id=randomUUID(),external=`lw-${id}`;
 await db.query(`insert into public.class_sessions(id,external_class_id,source,status,record_scope,course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status)
 select $1,$2,'landerware_event','scheduled','operational',c.id,now()+interval '2 days',now()+interval '2 days 2 hours',now()+interval '2 days',now()+interval '2 days 2 hours',p.id,l.id,$3,'landerware','public','open' from public.courses c,public.people p,public.locations l where c.enrollware_course_id='359474'`,[id,external,capacity]);
 const rpc=async(name,args)=>{const keys=Object.keys(args);return (await db.query(`select public.${name}(${keys.map((k,i)=>`${k} => $${i+1}`).join(',')}) result`,Object.values(args).map(v=>v!==null&&typeof v==='object'?JSON.stringify(v):v))).rows[0].result};
 const students=n=>Array.from({length:n},(_,i)=>({firstName:'Synthetic',lastName:`Student${i}`,email:`s${randomUUID()}@example.test`,phone:'2025550100'}));
 const create=(st=students(1),key=randomUUID(),extra={})=>rpc('landerware_create_public_order',{p_idempotency_key:key,p_external_class_id:external,p_course_id:'359474',p_payer_email:st[0].email,p_payer_phone:st[0].phone,p_students:st,p_billing_code:null,p_offer:{},...extra});
 const order=async id=>(await db.query('select * from public.landerware_public_orders where id=$1',[id])).rows[0];
 const bind=async id=>{await db.query("update public.landerware_public_orders set status='checkout_open',stripe_checkout_session_id=$2 where id=$1",[id,`cs_test_${id}`]);return order(id)};
 const evidence=o=>({id:o.stripe_checkout_session_id,mode:'payment',payment_status:'paid',amount_total:o.total,currency:o.currency,metadata:{landerware_order_id:o.id},livemode:false});
 const finalize=o=>rpc('landerware_finalize_public_order',{p_order_id:o.id,p_stripe_payment_intent_id:`pi_test_${o.id}`,p_evidence:evidence(o)});
 const seats=()=>rpc('landerware_public_seat_state',{p_session_id:id});
 return {db,id,external,rpc,students,create,order,bind,evidence,finalize,seats};
}
