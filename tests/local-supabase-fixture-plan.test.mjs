import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {adaptLocalSupabaseFixture,localSupabaseFixturePreflight,localSupabaseFixtureAdmission} from './helpers/local-supabase-fixture-plan.mjs';
const docs='tests/helpers/skills-checkout-documents.sql',profiles='tests/helpers/native-checkout-profile-schema.sql';
const read=path=>readFileSync(new URL('../'+path,import.meta.url),'utf8');
test('managed-schema adaptation removes only exact fake storage DDL and keeps application fixtures',()=>{
 const a=adaptLocalSupabaseFixture(docs,read(docs)),b=adaptLocalSupabaseFixture(profiles,read(profiles));
 assert.match(a,/create table public.class_session_documents/);assert.match(b,/create table public.landerware_registration_profiles/);
 for(const sql of [a,b])assert.doesNotMatch(sql,/create schema storage|create table storage\.|insert into storage\./i);
 assert.equal(adaptLocalSupabaseFixture('other.sql','unchanged'),'unchanged');
 for(const path of [docs,profiles])assert.throws(()=>adaptLocalSupabaseFixture(path,read(path)+'\n'+read(path)),/source_drift/);
 assert.throws(()=>adaptLocalSupabaseFixture(docs,read(docs).replace('public boolean','public text')),/source_drift/);
});
test('adapted fixture preserves richer existing auth and storage tables and rows',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  await db.exec(`create schema auth;create table auth.users(id uuid primary key,fixture_note text);
   create schema storage;create table storage.buckets(id text primary key,name text not null,public boolean,fixture_note text);
   create table storage.objects(id uuid primary key,bucket_id text,name text,metadata jsonb,fixture_note text);
   insert into auth.users values('11111111-1111-4111-8111-111111111111','synthetic-only');
   insert into storage.buckets values('class-session-docs','class-session-docs',false,'preserve');
   insert into storage.objects values('22222222-2222-4222-8222-222222222222','class-session-docs','synthetic.txt','{}','preserve');`);
  const snapshot=async()=>({auth:(await db.query('select * from auth.users')).rows,buckets:(await db.query('select * from storage.buckets')).rows,objects:(await db.query('select * from storage.objects')).rows});
  const before=await snapshot();
  for(const path of [docs,profiles])await db.exec(adaptLocalSupabaseFixture(path,read(path)));
  assert.deepEqual(await snapshot(),before);
  assert.equal((await db.query('select count(*) as n from public.landerware_registration_profiles')).rows[0].n,0);
 }finally{await db.close();}
});
test('preflight is read-only admission and refuses nonloopback, occupied or nonmanaged targets',()=>{
 for(const marker of ['local_fixture_postgresql17_required','local_fixture_loopback_required','local_fixture_public_schema_not_empty','local_fixture_managed_schemas_required','local_fixture_storage_contract_mismatch','local_fixture_private_bucket_required'])assert.ok(localSupabaseFixturePreflight.includes(marker));
 assert.doesNotMatch(localSupabaseFixturePreflight,/\b(insert|update|delete|drop|alter|grant)\b/i);
});

test('native socket admission remains opt-in and keeps nonloopback and existing-state guards',()=>{
 assert.equal(localSupabaseFixtureAdmission(),localSupabaseFixturePreflight);
 assert.throws(()=>localSupabaseFixtureAdmission({verifiedNativeSocket:'yes'}),/invalid_native_socket_proof/);
 const guarded=localSupabaseFixtureAdmission({verifiedNativeSocket:true});
 assert.match(guarded,/inet_server_addr\(\) is not null and host/);
 for(const marker of ['local_fixture_public_schema_not_empty','local_fixture_postgresql17_required','local_fixture_private_bucket_required'])assert.ok(guarded.includes(marker));
});
