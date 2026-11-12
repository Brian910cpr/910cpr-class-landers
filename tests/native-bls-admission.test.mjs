import test from 'node:test';
import assert from 'node:assert/strict';
import {proveBlsAdmission,setupBlsAdmission,admissionMigration,scalar} from './native-bls-admission-proof.mjs';
for(const full of [false,true])test(`BLS admission guards ${full?'full':'BLS-only'} release chain`,async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{await proveBlsAdmission(db,{full});}finally{await db.close();}
});

for(const full of [false,true])test(`BLS migration drift fails atomically (${full?'full':'BLS-only'})`,async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  await setupBlsAdmission(db,{full,apply:false});
  const signature='native_checkout_create_order(text,text,text,text,text,jsonb,text,jsonb)';
  const definition=await scalar(db,'select pg_get_functiondef($1::regprocedure)',[signature]);
  await db.exec(definition.replace('-- Preserve the installed','-- Deliberate fixture drift. Preserve the installed'));
  await assert.rejects(db.exec(admissionMigration),/native_bls_creator_source_drift/);await db.exec('rollback');
  assert.equal(await scalar(db,"select to_regprocedure('native_bls_lock_booking_dependencies()')::text"),null);
  assert.equal(await scalar(db,"select position('native_bls_session_booking_ready' in prosrc)=0 from pg_proc where oid='native_scheduling_seat_snapshot(uuid)'::regprocedure"),true);
 }finally{await db.close();}
});
