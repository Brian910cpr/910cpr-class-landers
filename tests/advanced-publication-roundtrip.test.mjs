import test from 'node:test';import assert from 'node:assert/strict';import {spawnSync} from 'node:child_process';
import {proveCombinedCheckout} from './combined-checkout-proof.mjs';
import {advancedFullCourseOffers} from '../supabase/functions/public-registration/advanced-course.mjs';
test('existing scheduler publisher feed normalizes to exact service leases and native reservation without external container',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  await proveCombinedCheckout(db);const scalar=async(q,args=[])=>Object.values((await db.query(q,args)).rows[0])[0];
  const proof=await scalar('select native_advanced_publication_policy()');
  const occupancy=(await db.query(`select s.external_class_id as source_event_id,s.start_at as start,s.consumption_end_at as "end",'Fixture Instructor' as instructor,'FIXTURE ROOM' as resource,'location_resource_map' as location_resolution,s.external_course_id as course_id,true as count_available,(select count(*) from registrations r where r.class_session_id=s.id and r.status='registered')::int as active_registration_count,'canonical_class_sessions' as source_file from class_sessions s`)).rows;
  const python=process.env.SKILLS_TEST_PYTHON||(process.platform==='win32'?'C:/Users/ten77/AppData/Local/Programs/Python/Python312/python.exe':'python');
  const result=spawnSync(python,['-X','utf8','-B','tests/helpers/native-advanced-publication-fixture.py'],{input:JSON.stringify({proof,occupancy}),encoding:'utf8',windowsHide:true});assert.equal(result.status,0,result.stderr);
  const {feed,claims}=JSON.parse(result.stdout);assert.ok(claims.length);const server=advancedFullCourseOffers(feed,'241108',Date.now(),proof.courses['241108']);assert.deepEqual(server,claims,'Python publication and actual API DTO strings must match SQL lease equality');
  assert.equal(await scalar('select native_publish_advanced_offers($1::jsonb)',[JSON.stringify(claims)]),claims.length);
  const st={firstName:'Synthetic',lastName:'Fixture',email:'publisher-claim@example.invalid',phone:'2025550100',manualChoice:'own-copy',firstAidChoice:'none',addons:[]};const input={wire:st,selectedChoices:['own_copy','no_first_aid'],submitted:{fields:{first_name:st.firstName,last_name:st.lastName,email:st.email,phone:st.phone},selectedChoices:['own_copy','no_first_aid']}};
  const saved=await scalar("select reserve_native_advanced_checkout_order('88888888-8888-4888-8888-888888888888','fixture_acls',1,'',null,$1::jsonb,$2::jsonb,$3::jsonb,22500)",[JSON.stringify(server[0]),JSON.stringify([st]),JSON.stringify([input])]);assert.equal(saved.amountCents,22500);assert.equal(saved.status,'held');assert.equal(await scalar('select count(*) from class_sessions where id=$1',[saved.sessionId]),1);
 }finally{await db.close();}
});
