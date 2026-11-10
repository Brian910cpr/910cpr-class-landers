import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {preProfileFiles,profileMigration} from './helpers/native-checkout-migration-plan.mjs';
import {genericCheckout} from '../supabase/functions/public-registration/generic.mjs';
const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');
const root=new URL('../',import.meta.url),load=p=>readFileSync(new URL(p,root),'utf8');
const cfg=JSON.parse(load('data/config/native_heartsaver_course_drafts.json'));
const columns='supabase/migrations/'+readdirSync(new URL('supabase/migrations/',root)).find(f=>f.endsWith('_native_checkout_profile_columns_only.sql'));
const inperson='supabase/migrations/'+readdirSync(new URL('supabase/migrations/',root)).find(f=>f.endsWith('_native_heartsaver_inperson_drafts_only.sql'));
const draft='supabase/migrations/'+readdirSync(new URL('supabase/migrations/',root)).find(f=>f.endsWith('_heartsaver_inactive_checkout_drafts.sql'));
test('exact Heartsaver drafts are idempotent/private/inactive and use shared profile form only after explicit fixture configuration',async()=>{
 const db=new PGlite();try{
 for(const f of preProfileFiles)await db.exec(load(f));
 const oldFunctions=(await db.query("select proname,prosrc from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' order by proname,prosrc")).rows;
 await db.exec(load(columns));await db.exec(load(columns));
 assert.deepEqual((await db.query("select proname,prosrc from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' order by proname,prosrc")).rows,oldFunctions);
 assert.equal((await db.query("select count(*)::int n from information_schema.columns where table_schema='public' and (table_name,column_name) in (('courses','registration_profile_key'),('landerware_registration_profiles','form_schema'),('landerware_public_orders','registration_profile_snapshot'),('registrations','native_checkout_profile_snapshot'))")).rows[0].n,4);
 await db.exec(load(profileMigration));
 for(const c of cfg.courses)await db.query(`insert into courses(id,course_key,name,enrollware_course_id,duration_minutes,max_students_default,base_price,visibility_default,registration_backend_default) values($1,$2,$3,$4,$5,$6,null,$7,'manual')`,[c.canonicalId,c.courseKey,c.displayName,c.externalId,c.durationMinutes,c.capacity,c.visibility]);
 const courseRows=async()=> (await db.query("select * from courses where enrollware_course_id in ('209809','329495','351632') order by enrollware_course_id")).rows;
 await db.query("insert into landerware_registration_catalog(course_id,source,course_name,unit_amount,currency,addons,source_snapshot,active) values('209809','existing_hosted_catalog','Existing reviewed name',9500,'usd','[]','{\"existing\":true}',true)");
 const existingCatalog=(await db.query("select * from landerware_registration_catalog where course_id='209809'")).rows[0];
 const before=await courseRows();await db.exec(load(inperson));await db.exec(load(inperson));await db.exec(load(draft));await db.exec(load(draft));assert.deepEqual(await courseRows(),before);
 for(const c of cfg.courses){
 const p=(await db.query('select * from landerware_registration_profiles where profile_key=$1',[c.profileKey])).rows[0];
 const cat=(await db.query('select * from landerware_registration_catalog where course_id=$1',[c.externalId])).rows[0];
 assert.equal(p.active,false);assert.equal(p.listed,false);assert.equal(cat.active,c.externalId==='209809');if(c.externalId==='209809')assert.deepEqual(cat,existingCatalog);assert.equal(cat.unit_amount,9500);assert.deepEqual(p.form_schema,c.formSchema);assert.deepEqual(p.requirements,c.requirements);
 await assert.rejects(db.query('select native_checkout_profile($1,null)',[c.externalId]),/native_profile_not_configured/);
 // Explicit TEST-ONLY activation: migration never performs these updates.
 await db.query('update courses set registration_profile_key=$1,base_price=95 where id=$2',[c.profileKey,c.canonicalId]);
 await db.query('update landerware_registration_profiles set active=true where profile_key=$1',[c.profileKey]);
 await db.query('update landerware_registration_catalog set active=true where course_id=$1',[c.externalId]);
 const packet=(await db.query('select native_checkout_profile($1,null) p',[c.externalId])).rows[0].p;
 const api=genericCheckout({rpc:async(name,args)=>{if(name==='native_checkout_profile')return packet;if(name==='native_checkout_receipt'){const r=await db.query('select native_checkout_receipt($1) r',[args.p_key]);return r.rows[0].r;}if(name==='reserve_native_checkout_order'){const r=await db.query('select reserve_native_checkout_order($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb,$8::jsonb,$9) r',[args.p_key,args.p_profile_key,args.p_version,args.p_context,args.p_external_id,JSON.stringify(args.p_offer),JSON.stringify(args.p_students),JSON.stringify(args.p_inputs),args.p_expected_total]);return r.rows[0].r;}throw Error('unexpected_rpc');},catalog:async()=>packet.catalog,scheduleSession:async()=>({nativeReady:true,course_id:c.externalId,start_at:'2031-01-01T14:00:00Z',end_at:new Date(Date.parse('2031-01-01T14:00:00Z')+c.durationMinutes*60000).toISOString(),seats:{capacity:c.capacity,remaining:c.capacity}})});
 const m=await api.model({session:'fixture-'+c.externalId,course:c.externalId});assert.equal(m.profile.profileKey,c.profileKey);assert.equal(m.session.capacity,c.capacity);assert.equal(m.session.durationMinutes,c.durationMinutes);
 assert.equal(m.profile.baseAmountCents??m.profile.unitAmount??packet.catalog.unit_amount,9500);
 if(c.externalId!=='329495'){
  await db.query(`insert into class_sessions(source,status,course_id,start_at,end_at,lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,record_scope,consumption_start_at,consumption_end_at)
   select 'landerware_event','scheduled',$1,(current_date+30+($3::int))::timestamptz,(current_date+30+($3::int))::timestamptz+make_interval(mins=>$4::int),p.id,l.id,1,'landerware','public','open',$2,'operational',(current_date+30+($3::int))::timestamptz,(current_date+30+($3::int))::timestamptz+make_interval(mins=>$4::int) from people p cross join locations l where p.person_key='skills-test' and l.location_key='910cpr-office-shipyard'`,[c.canonicalId,'fixture-'+c.externalId,cfg.courses.indexOf(c),c.durationMinutes]);
  const key=c.canonicalId,selection={session:'fixture-'+c.externalId,course:c.externalId};
  const student={fields:{first_name:'Fixture',last_name:'Learner',email:'fixture-'+c.externalId+'@example.invalid',phone:'2025550100'},selectedChoices:[]};
  const body={selection,profileKey:c.profileKey,profileVersion:1,students:[student]};
  const a=await api.reserve(key,body);assert.equal(a.receipt.amountCents,9500);
  const replay=await api.reserve(key,body);assert.equal(replay.receipt.orderId,a.receipt.orderId);
  await assert.rejects(api.reserve(key,{...body,students:[{...student,fields:{...student.fields,email:'changed@example.invalid'}}]}),/idempotency_conflict/);
  await assert.rejects(api.reserve('99999999-9999-4999-8999-999999999999',{...body,students:[{...student,fields:{...student.fields,email:'other-'+c.externalId+'@example.invalid'}}]}),/insufficient_seats/);
 }

 }
 // Rerun cannot overwrite reviewed operator configuration or reactivate new defaults.
 await db.exec(load(draft));assert.equal((await db.query("select count(*)::int n from landerware_registration_profiles where profile_key like 'native_heartsaver_%_draft'")).rows[0].n,3);
 assert.equal(cfg.courses.find(c=>c.externalId==='329495').releaseBlockers.some(x=>x.includes('exact product/options/price inclusion unresolved')),true);
 }finally{await db.close();}
});
