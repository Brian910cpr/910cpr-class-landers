import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {normalizeCheckoutProfile,checkoutSelection} from '../supabase/functions/_shared/checkout-profile.mjs';
import {fixture,catalogs} from './helpers/inactive-bls-profile-fixture.mjs';

const root=new URL('../',import.meta.url);
const read=path=>readFile(new URL(path,root),'utf8');
const sql=await read('supabase/migrations/20261111185535_native_bls_profiles_inactive_unbound.sql');
// The SQL is the single source of the draft definition. Fixtures are synthetic.
const profileLiteral=sql.match(/\$profiles\$([\s\S]*?)\$profiles\$::jsonb/);
assert.ok(profileLiteral,'profile JSON literal is required');
const draftProfiles=JSON.parse(profileLiteral[1]);
const keys=draftProfiles.map(p=>p.profile_key);
const fields={first_name:'Synthetic',last_name:'Learner',email:'synthetic@example.invalid',phone:'2025550100'};

const rows=async(db,table)=>(await db.query('select to_jsonb(t) as row from '+table+' t order by to_jsonb(t)::text')).rows.map(x=>x.row);
const assertRejected=async(db,pattern)=>{await assert.rejects(db.exec(sql),pattern);await db.exec('rollback');};
const fixtureTest=(name,fn)=>test(name,async()=>{const db=await fixture();try{await fn(db);}finally{await db.close();}});

test('proposal inserts only expected inactive native profiles; no automatic activation or binding',()=>{
 const code=sql.replace(/--[^\n]*/g,'');
 assert.deepEqual([...code.matchAll(/insert\s+into\s+([\w.]+)/gi)].map(m=>m[1]),['public.landerware_registration_profiles']);
 assert.equal(/\b(update|delete|truncate|alter|create|drop)\s+(table|function|public\.|courses|landerware_)/i.test(code),false);
 const serialized=JSON.parse(code.match(/\$profiles\$([\s\S]*?)\$profiles\$::jsonb/)[1]);
 assert.deepEqual(serialized.map(p=>[p.profile_key,p.course_id]),[
  ['native_bls_209806_v1','aha-bls-provider'],
  ['native_bls_359474_v1','aha-bls-provider-renewal']
 ]);
 assert.ok(draftProfiles.every(p=>!p.active&&!p.listed&&p.form_schema.inventory_kind==='scheduled_session_v1'&&p.form_schema.max_students===6));
 assert.ok(code.indexOf("SET LOCAL lock_timeout = '2s';")>code.indexOf('BEGIN;'));
 assert.ok(code.indexOf("SET LOCAL statement_timeout = '30s';")>code.indexOf("SET LOCAL lock_timeout = '2s';"));
 assert.ok(code.indexOf('LOCK TABLE')>code.indexOf("SET LOCAL statement_timeout = '30s';"));
});

fixtureTest('adds exactly two disabled unbound profiles and preserves courses, catalogs and retail/MAXIM profiles',async db=>{
 const courses=await rows(db,'courses'),catalog=await rows(db,'landerware_registration_catalog'),old=await rows(db,'landerware_registration_profiles');
 await db.exec(sql);
 const all=await rows(db,'landerware_registration_profiles');
 assert.equal(all.length,old.length+2);
 assert.deepEqual(all.filter(p=>!keys.includes(p.profile_key)),old);
 assert.deepEqual(await rows(db,'courses'),courses);
 assert.deepEqual(await rows(db,'landerware_registration_catalog'),catalog);
 for(const p of all.filter(p=>keys.includes(p.profile_key))){
  const {created_at,updated_at,...actual}=p;assert.deepEqual(actual,draftProfiles.find(x=>x.profile_key===p.profile_key));
 }
 assert.equal((await db.query('select count(*)::int n from courses where registration_profile_key=any($1)',[keys])).rows[0].n,0);
 for(const id of ['209806','359474'])await assert.rejects(db.query('select native_checkout_profile($1,null)',[id]),/native_profile_not_configured/);
});

fixtureTest('replay is idempotent and does not refresh timestamps',async db=>{
 await db.exec(sql);const before=await rows(db,'landerware_registration_profiles');
 await db.exec(sql);assert.deepEqual(await rows(db,'landerware_registration_profiles'),before);
});

fixtureTest('price mismatch aborts the whole batch without leaving an Initial draft',async db=>{
 await db.exec("update landerware_registration_catalog set unit_amount=7600 where course_id='359474'");
 const before=await rows(db,'landerware_registration_profiles');
 await assertRejected(db,/native_bls_draft_course_price_or_binding_mismatch/);
 assert.deepEqual(await rows(db,'landerware_registration_profiles'),before);
});

fixtureTest('canonical price mismatch, currency change and inactive catalog each fail closed',async db=>{
 for(const change of [
  "update courses set base_price=70 where enrollware_course_id='209806'",
  "update landerware_registration_catalog set currency='eur' where course_id='209806'",
  "update landerware_registration_catalog set active=false where course_id='209806'"
 ]){
  await db.exec(change);await assertRejected(db,/native_bls_draft_course_price_or_binding_mismatch/);
  await db.exec("update courses set base_price=75 where enrollware_course_id='209806';update landerware_registration_catalog set currency='usd',active=true where course_id='209806'");
 }
 assert.equal((await db.query('select count(*)::int n from landerware_registration_profiles where profile_key=any($1)',[keys])).rows[0].n,0);
});

fixtureTest('wrong canonical public-ID mapping and existing retail binding are never overwritten',async db=>{
 await db.exec("update courses set enrollware_course_id='unexpected' where course_key='aha-bls-provider'");
 await assertRejected(db,/native_bls_draft_course_price_or_binding_mismatch/);
 await db.exec("update courses set enrollware_course_id='209806',registration_profile_key='retail-209806' where course_key='aha-bls-provider'");
 await assertRejected(db,/native_bls_draft_course_price_or_binding_mismatch/);
 assert.equal((await db.query("select registration_profile_key from courses where course_key='aha-bls-provider'")).rows[0].registration_profile_key,'retail-209806');
});

fixtureTest('an existing active or altered candidate is never disabled or overwritten',async db=>{
 await db.exec(sql);
 await db.exec("update landerware_registration_profiles set active=true where profile_key='native_bls_209806_v1'");
 await assertRejected(db,/native_bls_draft_existing_profile_drift/);
 assert.equal((await db.query("select active from landerware_registration_profiles where profile_key='native_bls_209806_v1'")).rows[0].active,true);
 await db.exec("update landerware_registration_profiles set active=false,version=2,display_name='Other approved name' where profile_key='native_bls_209806_v1'");
 await assertRejected(db,/native_bls_draft_existing_profile_drift/);
 assert.equal((await db.query("select display_name from landerware_registration_profiles where profile_key='native_bls_209806_v1'")).rows[0].display_name,'Other approved name');
});

fixtureTest('binding a candidate to any course is rejected without rebinding or removing it',async db=>{
 await db.exec(sql);
 await db.exec("update courses set registration_profile_key='native_bls_209806_v1' where enrollware_course_id='fixture-other'");
 await assertRejected(db,/native_bls_draft_already_bound/);
 assert.equal((await db.query("select registration_profile_key from courses where enrollware_course_id='fixture-other'")).rows[0].registration_profile_key,'native_bls_209806_v1');
});

fixtureTest('inactive profile remains inaccessible even if a local test binds it',async db=>{
 await db.exec(sql);
 await db.exec("update courses set registration_profile_key='native_bls_209806_v1' where enrollware_course_id='209806'");
 await assert.rejects(db.query("select native_checkout_profile('209806',null)"),/native_profile_not_configured/);
});

test('both drafts reject normalization while disabled; local active copies retain exact $75 base and no upload policy',()=>{
 for(const profile of draftProfiles){
  const cat=catalogs.find(c=>c.course_id===profile.profile_key.split('_')[2]);
  assert.throws(()=>normalizeCheckoutProfile(profile,cat),/invalid_checkout_profile/);
  const view=normalizeCheckoutProfile({...profile,active:true},cat);
  assert.equal(view.baseCents,7500);assert.equal(view.maxStudents,6);
  assert.deepEqual(view.uploads,[]);assert.deepEqual(view.driverRules,[{driver:'native_order'}]);
 }
});

test('Initial only offers documented customer-supplied manual; unmapped sales are impossible',()=>{
 const profile={...draftProfiles[0],active:true},cat=catalogs.find(c=>c.course_id==='209806');
 const view=normalizeCheckoutProfile(profile,cat);
 assert.deepEqual(view.optionGroups.flatMap(g=>g.choices.map(c=>c.key)),['customer_supplied_manual']);
 const selected=checkoutSelection(view,fields,['customer_supplied_manual']);
 assert.equal(selected.amountCents,7500);assert.deepEqual(selected.addons,[]);
 assert.deepEqual(selected.bindings,{manualChoice:'own-copy'});
 assert.throws(()=>checkoutSelection(view,fields,[]),/invalid_course_option/);
 for(const id of ['ebook','fixture_unmapped_addon','unexpected_paid_option'])
  assert.throws(()=>checkoutSelection(view,fields,[id]),/option_unavailable/);
});

test('Renewal requires bring-valid-card acknowledgement without inventing upload or paid options',()=>{
 const view=normalizeCheckoutProfile({...draftProfiles[1],active:true},catalogs.find(c=>c.course_id==='359474'));
 assert.deepEqual(view.optionGroups,[]);assert.deepEqual(view.uploads,[]);
 for(const value of [undefined,false,'true'])assert.throws(()=>checkoutSelection(view,{...fields,current_bls_card_ack:value},[]),/required_registration_field_missing/);
 const selected=checkoutSelection(view,{...fields,current_bls_card_ack:true},[]);
 assert.equal(selected.amountCents,7500);assert.deepEqual(selected.addons,[]);
 assert.equal(selected.fields.current_bls_card_ack,true);
});

fixtureTest('read-only validator distinguishes missing, safely staged, and accidentally active drafts',async db=>{
 const validator=await read('tests/helpers/native-bls-inactive-validator.sql');
 assert.equal(/\b(insert|update|delete|alter|drop|truncate|create)\s/i.test(validator.replace(/--[^\n]*/g,'')),false);
 assert.ok((await db.query(validator)).rows.every(r=>r.draft_present===false));
 await db.exec(sql);
 const safe=(await db.query(validator)).rows;
 const flags=['draft_present','disabled','unlisted','unbound_everywhere','canonical_binding_unchanged','price_matches','native_contract_matches','no_invented_upload_or_product_requirements'];
 assert.equal(safe.length,2);assert.ok(safe.every(r=>flags.every(k=>r[k]===true)));
 await db.exec("update landerware_registration_profiles set active=true where profile_key='native_bls_209806_v1'");
 assert.equal((await db.query(validator)).rows.find(r=>r.public_id==='209806').disabled,false);
});
