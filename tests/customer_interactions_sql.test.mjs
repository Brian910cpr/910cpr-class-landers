// Run against local Postgres WASM; PGLITE_MODULE is a file URL to a scratch-installed PGlite.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const {PGlite}=await import(process.env.PGLITE_MODULE||'@electric-sql/pglite');
const db=new PGlite();
await db.exec(`create role anon; create role authenticated; create role service_role bypassrls;
create table public.landerware_people(id uuid primary key);`);
await db.exec(readFileSync(new URL('../supabase/migrations/20261010210607_customer_interaction_storage.sql',import.meta.url),'utf8'));
await db.exec('set role service_role');
const person=crypto.randomUUID(),caseId=crypto.randomUUID(),id=crypto.randomUUID();
await db.exec('reset role');await db.query('insert into landerware_people values ($1)',[person]);await db.exec('set role service_role');
const input={id,case_id:caseId,person_id:person,expected_version:0,kind:'email',status:'in_progress',source:'manual',source_id:id,document:{callNotes:'Original raw notes'}};
const save=async(value,requestId=crypto.randomUUID())=>(await db.query('select save_customer_interaction($1,$2,$3) as record',[requestId,'owner-session-fixture',value])).rows[0].record;
test('migration, save/reload, immutable note history, pause/resume and same-customer interactions',async()=>{
 const first=await save(input);assert.equal(first.version,1);
 assert.equal((await db.query('select document from customer_interactions where id=$1',[id])).rows[0].document.callNotes,'Original raw notes');
 const paused=await save({...input,expected_version:1,status:'paused',document:{callNotes:'Original raw notes plus correction'}});assert.equal(paused.version,2);
 const other=await save({...input,id:crypto.randomUUID(),source_id:crypto.randomUUID(),kind:'phone'});assert.equal(other.case_id,caseId);
 const resumed=await save({...input,expected_version:2});assert.equal(resumed.version,3);
 const history=await db.query('select input from customer_interaction_events where interaction_id=$1 order by occurred_at',[id]);assert.equal(history.rows.length,3);assert.equal(history.rows[0].input.document.callNotes,'Original raw notes');
});
test('lost-response retry is idempotent; reused ID with different data is rejected',async()=>{const r=crypto.randomUUID(),v={...input,id:crypto.randomUUID(),source_id:crypto.randomUUID()};const a=await save(v,r),b=await save(v,r);assert.deepEqual(a,b);await assert.rejects(save({...v,status:'paused'},r),/idempotency_conflict/)});
test('stale cross-tab write and duplicate external source never overwrite notes',async()=>{await assert.rejects(save({...input,expected_version:1}),/version_conflict/);await assert.rejects(save({...input,id:crypto.randomUUID()}),/duplicate key/);const row=(await db.query('select version from customer_interactions where id=$1',[id])).rows[0];assert.equal(row.version,3)});
test('failed write rolls back case, interaction and audit together',async()=>{const c=crypto.randomUUID(),i=crypto.randomUUID();await assert.rejects(save({...input,id:i,case_id:c,source_id:i,status:'invented'}));assert.equal((await db.query('select count(*)::int as n from customer_cases where id=$1',[c])).rows[0].n,0)});
test('anon/authenticated cannot read notes or execute the privileged RPC; service role cannot erase audit',async()=>{for(const role of ['anon','authenticated']){await db.exec('reset role; set role '+role);await assert.rejects(db.query('select * from customer_interactions'),/permission denied/);await assert.rejects(save(input),/permission denied/)}await db.exec('reset role; set role service_role');await assert.rejects(db.query('delete from customer_interaction_events'),/permission denied/);await db.close()});
