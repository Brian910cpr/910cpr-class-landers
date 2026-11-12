// Local synthetic optional bundle completion guard. No provider or hosted calls.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const bundleRoot=process.env.BLS_BUNDLE_CANDIDATE_ROOT||root;
const {setupBlsSkills}=await import(pathToFileURL(resolve(bundleRoot,'tests/native-bls-skills-proof.mjs')));
const load=f=>readFileSync(resolve(root,'supabase/migrations',f),'utf8');
for(const full of [false,true])test(`pinned final code readiness guard composes with ${full?'full':'BLS-only'} chain`,async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  await setupBlsSkills(db,{full});
  for(const f of ['20261109130000_native_learner_code_delivery.sql','20261109140000_native_code_delivery_events.sql','20261111235100_native_learner_code_resend_service.sql'])await db.exec(load(f));
  const guard=load('20261112000500_native_bls_code_completion_guard.sql');await db.exec(guard);
  const {src}=(await db.query("select prosrc as src from pg_proc where oid='materialize_native_skills_checkout(text,jsonb,text)'::regprocedure")).rows[0];
  assert.match(src,/p_context='bls-skills' and p_offer->>'checkoutPackage'='heartcode-bls-online-and-skills.v1'/);
  const at=src.indexOf('-- Sender readiness is revalidated at materializer completion');assert.ok(at>0);
  assert.ok(src.slice(at).includes("public.native_bls_bundle_ready((p_offer->>'consumptionEndsAt')::timestamptz)"));
  assert.ok(src.slice(at).includes("return option||jsonb_build_object('targetSessionId'"));
  await assert.rejects(db.exec(guard),/native_code_bundle_materializer_drift|native_code_bundle_dependency_drift/);await db.exec('rollback');
  assert.equal((await db.query('select enabled from native_learner_code_runtime')).rows[0].enabled,false);
 }finally{await db.close();}
});
