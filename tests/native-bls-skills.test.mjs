import test from 'node:test';
import assert from 'node:assert/strict';
import {setupBlsSkills,proveBlsSkills,migration,scalar} from './native-bls-skills-proof.mjs';
const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');
for(const full of [false,true])test(`independent BLS skills and bundle admission ${full?'full':'BLS-only'} chain`,async()=>{
 const db=new PGlite();try{await proveBlsSkills(db,{full});}finally{await db.close();}
});
test('new migration rejects drift atomically and preserves original sibling lease guard',async()=>{
 const db=new PGlite();try{
  await setupBlsSkills(db,{apply:false});
  const signature='materialize_native_skills_checkout(text,jsonb,text)';
  const original=await scalar(db,'select pg_get_functiondef($1::regprocedure)',[signature]);
  await db.exec(original.replace('begin\n','begin\n -- unexpected drift\n'));
  await assert.rejects(db.exec(migration),/native_bls_skills_source_drift/);await db.exec('rollback');
  assert.equal(await scalar(db,"select to_regclass('native_bls_skills_publication_policy')"),null);
 }finally{await db.close();}
});
