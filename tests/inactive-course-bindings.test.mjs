import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
const sql=readFileSync(new URL('../supabase/reviewed/native-verified-inactive-course-bindings.sql',import.meta.url),'utf8');
const rows=[['209806','aha-bls-provider','native_bls_209806_v1'],['359474','aha-bls-provider-renewal','native_bls_359474_v1'],['509474','skills-session-only','native_skills_shared']];
test('verified inactive bindings preserve business/session policy, are repeatable, and fail atomically on identity drift',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  await db.exec(`create table courses(id integer primary key,course_key text,enrollware_course_id text,registration_profile_key text,duration_minutes integer,max_students_default integer,cleanup_buffer_minutes integer,visibility text,base_price numeric);
   create table landerware_registration_profiles(profile_key text primary key,course_id text,registration_mode text,active boolean,version integer,form_schema jsonb);`);
  for(let i=0;i<rows.length;i++){
   const [id,key,profile]=rows[i];await db.query('insert into courses values($1,$2,$3,null,$4,$5,$6,$7,$8)',[i,key,id,i===2?45:120,i===2?2:12,i===2?15:0,'private',i===2?55:75]);
   await db.query("insert into landerware_registration_profiles values($1,$2,'native_public_checkout',false,2,'{\"schemaVersion\":\"native-checkout.form.v1\"}')",[profile,key]);
  }
  const business=async()=> (await db.query("select to_jsonb(c)-'registration_profile_key' as data from courses c order by id")).rows;
  const before=await business();await db.exec(sql);await db.exec(sql);assert.deepEqual(await business(),before);
  assert.deepEqual((await db.query('select registration_profile_key from courses order by id')).rows.map(r=>r.registration_profile_key),rows.map(r=>r[2]));
  assert.equal((await db.query('select bool_or(active) as active from landerware_registration_profiles')).rows[0].active,false);
  for(const mutation of ["update courses set registration_profile_key='other-owner' where id=2", "update landerware_registration_profiles set active=true where course_id='skills-session-only'", "update courses set course_key='unverified' where id=2"]){
   await db.exec('begin');await db.exec('update courses set registration_profile_key=null');await db.exec(mutation);
   await assert.rejects(db.exec(sql),/native_binding_/);await db.exec('rollback');assert.deepEqual(await business(),before);assert.deepEqual((await db.query('select registration_profile_key from courses order by id')).rows.map(r=>r.registration_profile_key),rows.map(r=>r[2]));
  }
 }finally{await db.close();}
});
