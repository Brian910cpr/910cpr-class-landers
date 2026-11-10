import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync,readdirSync} from 'node:fs';
import {preProfileFiles,profileMigration} from './helpers/native-checkout-migration-plan.mjs';
const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const compat='supabase/migrations/'+readdirSync(new URL('../supabase/migrations/',import.meta.url)).find(f=>f.endsWith('_native_checkout_additive_order_runtime.sql'));
test('additive native runtime preserves actual hosted legacy overloads and shares capacity/closure safeguards without accepting payment guesses',async()=>{
 const db=new PGlite();try{
 for(const f of preProfileFiles)await db.exec(load(f));await db.exec(load(profileMigration));
 await db.exec(load('tests/helpers/native-checkout-legacy-hosted-functions.sql'));
 const baseline=async()=> (await db.query("select proname,pg_get_function_identity_arguments(p.oid) args,prosrc,prosecdef,proacl::text acl from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in ('landerware_create_public_order','landerware_finalize_public_order') and (p.proname='landerware_create_public_order' or p.pronargs=2) order by proname,args")).rows;
 const before=await baseline();await db.exec(load(compat));await db.exec(load(compat));assert.deepEqual(await baseline(),before);
 await db.exec("insert into courses(course_key,name,enrollware_course_id,duration_minutes,max_students_default,base_price) values('fixture-compat','Synthetic Compatibility Course','fixture-compat',120,2,75);insert into landerware_registration_catalog(course_id,course_name,unit_amount,active) values('fixture-compat','Synthetic Compatibility Course',7500,true);insert into class_sessions(source,status,course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,record_scope) select 'landerware_event','scheduled',c.id,current_date+55,current_date+55+interval '2 hours',current_date+55,current_date+55+interval '2 hours',p.id,l.id,2,'landerware','public','open','fixture-compat-session','operational' from courses c cross join people p cross join locations l where c.course_key='fixture-compat' and p.person_key='skills-test' and l.location_key='910cpr-office-shipyard';");
 const student=n=>JSON.stringify([{firstName:'Synthetic',lastName:'Fixture',email:`compat-${n}@example.invalid`,phone:'2025550100',addons:[]}]);
 const args=n=>[`compat-${n}`,'fixture-compat-session','fixture-compat',`compat-${n}@example.invalid`,'2025550100',student(n)];
 const legacy=(await db.query("select landerware_create_public_order($1,$2,$3,$4,$5,$6::jsonb,null,'{}'::jsonb) r",args(1))).rows[0].r;assert.ok(legacy.recoveryToken);assert.equal(legacy.total,7500);
 const native=(await db.query("select native_checkout_create_order($1,$2,$3,$4,$5,$6::jsonb,null,'{}'::jsonb) r",args(2))).rows[0].r;assert.equal(native.total,7500);
 await assert.rejects(db.query("select native_checkout_create_order($1,$2,$3,$4,$5,$6::jsonb,null,'{}'::jsonb)",args(3)),/insufficient_seats/);
 assert.equal((await db.query("select count(*)::int n from landerware_public_orders where course_id='fixture-compat'")).rows[0].n,2);
 assert.equal((await db.query("select native_checkout_create_order($1,$2,$3,$4,$5,$6::jsonb,null,'{}'::jsonb) r",args(2))).rows[0].r.orderId,native.orderId);
 await assert.rejects(db.query("select native_checkout_record_payment($1,'pi_fixture','{}')",[native.orderId]),/payment_evidence_mismatch/);
 await assert.rejects(db.query("select native_checkout_finalize_order($1,'pi_fixture','{}')",[native.orderId]),/payment_evidence_mismatch/);
 assert.equal((await db.query('select status,payment_evidence from landerware_public_orders where id=$1',[native.orderId])).rows[0].status,'held');
 const privileges=(await db.query("select has_function_privilege('anon','native_checkout_create_order(text,text,text,text,text,jsonb,text,jsonb)','EXECUTE') a,has_function_privilege('authenticated','native_checkout_finalize_order(uuid,text,jsonb)','EXECUTE') u,has_function_privilege('service_role','native_checkout_record_payment(uuid,text,jsonb)','EXECUTE') s")).rows[0];assert.deepEqual(privileges,{a:false,u:false,s:true});
 }finally{await db.close();}
});
