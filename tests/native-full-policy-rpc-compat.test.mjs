import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fullCoursePolicyRpcArgs} from '../supabase/functions/public-registration/full-course.mjs';

test('both BLS paths retain the installed zero-argument RPC contract',()=>{
 for(const course of ['209806','359474'])assert.deepEqual(fullCoursePolicyRpcArgs(course),{});
});
test('optional scopes keep the explicit course argument and never fall into BLS',()=>{
 for(const course of ['209809','344085','999999'])assert.deepEqual(fullCoursePolicyRpcArgs(course),{p_course_number:course});
 for(const value of [null,undefined,209806,['209806'],{},'', '209806 '])assert.throws(()=>fullCoursePolicyRpcArgs(value),/invalid_course/);
});
test('deployed adapter uses the tested RPC argument selector',()=>{
 const source=readFileSync(new URL('../supabase/functions/public-registration/index.ts',import.meta.url),'utf8');
 assert.match(source,/import \{fullCoursePolicyRpcArgs\} from "\.\/full-course\.mjs"/);
 assert.ok(source.includes('fullPolicy:(course:string)=>rpc(["241108","209818","209805","251496"].includes(course)?"native_advanced_course_runtime_policy":"native_full_course_runtime_policy",fullCoursePolicyRpcArgs(course))'));
});
test('BLS policy resolves with only the existing SQL signature installed',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  await db.exec(`create function public.native_full_course_runtime_policy() returns jsonb language sql stable as $$
   select '{"materializationEnabled":false,"nativePublicationEnabled":false,"nativeScopeId":"brian-shipyard-b.v1"}'::jsonb $$;`);
  assert.equal((await db.query("select to_regprocedure('public.native_full_course_runtime_policy(text)') as fn")).rows[0].fn,null);
  const rpc=async course=>{
   const args=fullCoursePolicyRpcArgs(course);
   return (await db.query(Object.keys(args).length?'select native_full_course_runtime_policy($1::text) as policy':'select native_full_course_runtime_policy() as policy',Object.keys(args).length?[args.p_course_number]:[])).rows[0].policy;
  };
  for(const course of ['209806','359474'])assert.deepEqual(await rpc(course),{materializationEnabled:false,nativePublicationEnabled:false,nativeScopeId:'brian-shipyard-b.v1'});
  await assert.rejects(()=>rpc('209809'),/does not exist/);
 }finally{await db.close();}
});
