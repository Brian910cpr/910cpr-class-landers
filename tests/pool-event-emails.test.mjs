import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import test from 'node:test';
import assert from 'node:assert/strict';
const {PGlite}=createRequire(import.meta.url)('@electric-sql/pglite');
const load=name=>readFileSync(new URL('../supabase/migrations/'+name,import.meta.url),'utf8');
const migration='20261107121724_pool_event_email_cadence.sql';
const FREE='nseaswim-pool-family-2027-02-15',BLS='nseaswim-pool-bls-2027-02-15';
async function fixture(){
 const db=new PGlite();
 await db.exec(`create role anon;create role authenticated;create role service_role;
 create table customers(id uuid primary key default gen_random_uuid(),first_name text,email text);
 create table courses(id uuid primary key,name text);
 create table locations(id uuid primary key,name text);
 create table people(id uuid primary key,display_name text);
 create table class_sessions(id uuid primary key default gen_random_uuid(),external_class_id text,course_id uuid,location_id uuid,lead_instructor_id uuid,start_at timestamptz,end_at timestamptz,status text,source_location_label text,source_instructor_label text);
 create table registrations(id uuid primary key default gen_random_uuid(),customer_id uuid,class_session_id uuid,status text,registration_source text,optional_survey jsonb default '{}');
 create table registration_orders(id uuid primary key default gen_random_uuid(),registration_id uuid,status text);
 create table landerware_messages(id uuid primary key default gen_random_uuid(),customer_id uuid,operational_registration_id uuid,template_key text,channel text,recipient text,subject text,body_text text,delivery_provider text,delivery_status text,idempotency_key text unique);
 create table registration_reschedule_deliveries(message_id uuid primary key references landerware_messages(id),status text default 'pending' constraint registration_reschedule_deliveries_status_check check(status in ('pending','sending','sent','failed','needs_review')),attempts int default 0,locked_at timestamptz,next_attempt_at timestamptz default now(),last_error text,created_at timestamptz default now());`);
 await db.exec(load('20261021141044_schedule_confirmation_cadence.sql'));
 await db.exec(load(migration));
 return db;
}
async function row(db,sql,args=[]){return (await db.query(sql,args)).rows[0];}
async function count(db,table){return Number((await row(db,`select count(*) n from ${table}`)).n);}
async function register(db,{bls=false,status=bls?'payment_pending':'registered',complete=true,guest=false,days=5}={}){
 const customer=await row(db,"insert into customers(first_name,email) values('Sam','sam@example.invalid') returning id");
 const session=await row(db,"insert into class_sessions(external_class_id,start_at,end_at,status) values($1,case when $2::numeric>=1 then date_trunc('day',now())+($2||' days')::interval+interval '16 hours' else now()+($2||' days')::interval end,case when $2::numeric>=1 then date_trunc('day',now())+($2||' days')::interval+interval '19 hours' else now()+($2||' days')::interval+interval '3 hours' end,'active') returning id",[bls?BLS:FREE,days]);
 const id=(await row(db,'select gen_random_uuid() id')).id;
 await db.query("insert into registrations(id,customer_id,class_session_id,status,registration_source,optional_survey) values($1,$2,$3,$4,$5,$6)",[id,customer.id,session.id,status,'public_landerware_event:'+(bls?'bls':'friends_family')+':'+(guest?'guest':'group')+':fixture',JSON.stringify(complete?{groupRegistrationIds:[id],attendeeCount:1}:{})]);
 return {id,session:session.id,customer:customer.id};
}
test('free confirmation + 24h reminder, all partner links, one-minute hold and idempotent replay',async()=>{
 const db=await fixture();try{
 const r=await register(db);
 assert.equal(await count(db,'landerware_messages'),2);
 const rows=(await db.query('select * from landerware_messages')).rows;
 for(const m of rows){
  assert.equal(m.recipient,'sam@example.invalid');assert.equal(m.delivery_provider,'resend');
  for(const link of ['https://www.nseaswim.com/','https://www.facebook.com/1tallmermaid/','https://www.ncmobileivmedics.com/','https://www.910cpr.com/'])assert.ok(m.body_text.includes(link));
  assert.match(m.body_text,/We encourage you to visit their pages/);assert.match(m.body_text,/does not issue a certification card/);
 }
 assert.equal((await row(db,'select claim_reschedule_confirmations() messages')).messages.length,0,'minimum delay enforced');
 const due=await row(db,"select extract(epoch from(d.next_attempt_at-now())) seconds from registration_reschedule_deliveries d join landerware_messages m on m.id=d.message_id where m.template_key='pool-confirmation-v1'");
 assert.ok(Number(due.seconds)>58);
 assert.equal(Number((await row(db,"select extract(epoch from(s.start_at-d.next_attempt_at))/3600 hours from registration_reschedule_deliveries d join landerware_messages m on m.id=d.message_id join class_sessions s on s.id=d.snapshot_class_session_id where m.template_key='pool-day-before-v1'")).hours),24);
 await db.query('select queue_pool_event_emails($1)',[r.id]);await db.query("update registrations set status='registered' where id=$1",[r.id]);assert.equal(await count(db,'landerware_messages'),2);
 await db.exec("update registration_reschedule_deliveries set next_attempt_at=now() where message_id in(select id from landerware_messages where template_key='pool-confirmation-v1')");
 assert.equal((await row(db,'select claim_reschedule_confirmations() messages')).messages.length,1);
 assert.equal((await row(db,'select claim_reschedule_confirmations() messages')).messages.length,0,'leased row not double-claimed');
 }finally{await db.close();}
});
test('BLS waits for paid order and confirmed registration; guests and incomplete groups never send',async()=>{
 const db=await fixture();try{
 const r=await register(db,{bls:true});await register(db,{guest:true});await register(db,{complete:false});
 assert.equal(await count(db,'landerware_messages'),0);
 await db.query("update registrations set status='registered' where id=$1",[r.id]);assert.equal(await count(db,'landerware_messages'),0,'registered alone is not payment proof');
 await db.query("insert into registration_orders(registration_id,status) values($1,'paid')",[r.id]);
 await db.query("update registrations set status='registered' where id=$1",[r.id]);
 assert.equal(await count(db,'landerware_messages'),2);
 const m=await row(db,"select body_text from landerware_messages where template_key='pool-confirmation-v1'");
 assert.match(m.body_text,/payment is complete/);assert.match(m.body_text,/Successful course completion is required for an eCard/);assert.doesNotMatch(m.body_text,/free Family/);
 await db.exec("update registration_orders set status='refunded';update registration_reschedule_deliveries set next_attempt_at=now()");
 assert.equal((await row(db,'select claim_reschedule_confirmations() messages')).messages.length,0);
 assert.equal(Number((await row(db,"select count(*) n from registration_reschedule_deliveries where status='cancelled'")).n),2);
 }finally{await db.close();}
});
test('combined reminder/welcome is invitational and there is no event-day email',async()=>{
 const db=await fixture();try{
 await register(db);assert.equal(await count(db,'landerware_messages'),2);
 const m=await row(db,"select subject,body_text from landerware_messages where template_key='pool-day-before-v1'");
 assert.match(m.subject,/Reminder & Welcome/);assert.match(m.body_text,/We'd love to see you if you're able to join us/);
 assert.match(m.body_text,/we understand if your plans change/);
 assert.equal(Number((await row(db,"select count(*) n from landerware_messages where template_key like '%welcome%'")).n),0);
 }finally{await db.close();}
});test('late registration skips overdue reminders; cancelled/moved sessions suppress pending messages',async()=>{
 const db=await fixture();try{
 const r=await register(db,{days:0.5});assert.equal(await count(db,'landerware_messages'),1);
 await db.query("update class_sessions set start_at=start_at+interval '1 day' where id=$1",[r.session]);
 assert.equal((await row(db,'select claim_reschedule_confirmations() messages')).messages.length,0);
 assert.equal((await row(db,'select delivery_status from landerware_messages')).delivery_status,'cancelled');
 const other=await register(db);await db.query("update registrations set status='cancelled' where id=$1",[other.id]);
 assert.equal((await row(db,'select claim_reschedule_confirmations() messages')).messages.length,0);
 assert.equal(Number((await row(db,"select count(*) n from registration_reschedule_deliveries where status<>'cancelled'")).n),0);
 }finally{await db.close();}
});
test('transaction rollback leaves no queue; mail copy has exact local event details and role restrictions',async()=>{
 const db=await fixture();try{
 await db.exec('begin');await register(db);await db.exec('rollback');assert.equal(await count(db,'landerware_messages'),0);
 const result=await row(db,"select pool_event_email_copy('confirmation',false,'Alex',2,'2027-02-15T16:00:00Z','2027-02-15T19:00:00Z','https://www.910cpr.com/pool') copy");
 assert.match(result.copy.body,/Monday, February 15, 2027/);assert.match(result.copy.body,/11:00 AM to 2:00 PM Eastern/);assert.match(result.copy.body,/750 Bess Street/);assert.match(result.copy.body,/Places reserved: 2/);
 const access=await row(db,"select has_function_privilege('anon','public.queue_pool_event_emails(uuid)','execute') anon,has_function_privilege('authenticated','public.queue_pool_event_emails(uuid)','execute') authenticated,has_function_privilege('service_role','public.queue_pool_event_emails(uuid)','execute') service,(select relrowsecurity from pg_class where relname='pool_event_email_profiles') rls");
 assert.deepEqual(access,{anon:false,authenticated:false,service:true,rls:true});
 }finally{await db.close();}
});


