import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const {PGlite}=await import(process.env.PGLITE_MODULE||'@electric-sql/pglite');
const db=new PGlite();
await db.exec('create role anon; create role authenticated; create role service_role bypassrls; create table landerware_people(id uuid primary key)');
for(const name of ['20261010210607_customer_interaction_storage.sql','20261010211804_customer_interaction_interruptions.sql','20261010212019_customer_follow_up_task_mutations.sql'])
 await db.exec(readFileSync(new URL('../supabase/migrations/'+name,import.meta.url),'utf8'));
await db.exec('set role service_role');
const record=(patch={})=>{const id=crypto.randomUUID();return {id,case_id:crypto.randomUUID(),expected_version:0,kind:'phone',status:'in_progress',source:'manual',source_id:id,document:{notes:'raw'},...patch}};
const save=async(input)=>(await db.query('select save_customer_interaction($1,$2,$3) as r',[crypto.randomUUID(),'owner',input])).rows[0].r;
const switchCase=async(input,id=crypto.randomUUID(),actor='owner')=>(await db.query('select switch_customer_interaction($1,$2,$3) as r',[id,actor,input])).rows[0].r;
const reload=async id=>(await db.query('select * from customer_interactions where id=$1',[id])).rows[0];
const fixture=async()=>{const previous=record({kind:'email'});await save(previous);return {operation:'interrupt',previous:{...previous,expected_version:1,status:'paused',document:{notes:'checkpoint including unsaved edits',selection:'reply'}},active:record()}};

test('atomic interrupt/reload/resume preserves checkpoint and immutable links, even after lost response',async()=>{
 const input=await fixture(),id=crypto.randomUUID();const first=await switchCase(input,id);
 assert.deepEqual(await switchCase(input,id),first);
 assert.equal((await reload(input.previous.id)).document.selection,'reply');
 assert.equal((await reload(input.active.id)).status,'in_progress');
 const stored=(await db.query('select input from customer_interruption_events where request_id=$1',[id])).rows[0].input;
 const resume={operation:'resume',interrupt_request_id:id,previous:{...stored.previous,expected_version:2,status:'in_progress'},active:{...stored.active,expected_version:1,status:'follow_up_due',document:{notes:'Promised callback'}}};
 const resumed=await switchCase(resume);assert.equal(resumed.previous.version,3);assert.equal(resumed.active.status,'follow_up_due');
 assert.equal((await db.query('select count(*)::int n from customer_interaction_events where interaction_id=$1',[input.previous.id])).rows[0].n,3);
 await assert.rejects(switchCase(resume),/invalid_resume|version_conflict|duplicate key/);
});
test('second write failure rolls back checkpoint, new case and both audits',async()=>{
 const input=await fixture();input.active.document=[];
 const before=(await db.query('select count(*)::int n from customer_interaction_events')).rows[0].n;
 await assert.rejects(switchCase(input));
 assert.equal((await reload(input.previous.id)).version,1);assert.equal(await reload(input.active.id),undefined);
 assert.equal((await db.query('select count(*)::int n from customer_cases where id=$1',[input.active.case_id])).rows[0].n,0);
 assert.equal((await db.query('select count(*)::int n from customer_interaction_events')).rows[0].n,before);
});
test('stale tabs and changed retry payload/actor conflict without overwriting checkpoints',async()=>{
 const input=await fixture(),id=crypto.randomUUID();await switchCase(input,id);
 await assert.rejects(switchCase({...input,active:record()}),/version_conflict/);
 await assert.rejects(switchCase({...input,active:record()},id),/idempotency_conflict/);
 await assert.rejects(switchCase(input,id,'other-session'),/idempotency_conflict/);
 assert.equal((await reload(input.previous.id)).version,2);
});
test('unknown callers cannot inherit a person or existing case; mismatched resume fails',async()=>{
 const input=await fixture();await assert.rejects(switchCase({...input,active:{...input.active,case_id:input.previous.case_id}}),/invalid_interrupt/);
 await assert.rejects(switchCase({...input,active:{...input.active,person_id:crypto.randomUUID()}}),/invalid_interrupt/);
 await assert.rejects(switchCase({...input,previous:{...input.previous,status:'resolved'}}),/invalid_interrupt/);
 const result=await switchCase(input);
 await assert.rejects(switchCase({operation:'resume',interrupt_request_id:result.request_id,previous:{...input.active,expected_version:1,status:'in_progress'},active:{...input.previous,expected_version:2,status:'resolved'}}),/invalid_resume/);
 assert.equal((await reload(input.previous.id)).status,'paused');
});
test('follow-up tasks save/reload, deduplicate, conflict and require explicit completion evidence',async()=>{
 const interaction=record();await save(interaction);
 const task={id:crypto.randomUUID(),case_id:interaction.case_id,interaction_id:interaction.id,source_key:'manual:'+crypto.randomUUID(),title:'Promised callback',status:'pending',expected_version:0,provenance:{evidence:'Owner call note: promised callback before Thursday'}};
 const saveTask=async(input,id=crypto.randomUUID())=>(await db.query('select save_customer_follow_up_task($1,$2,$3) r',[id,'owner',input])).rows[0].r;
 const request=crypto.randomUUID(),first=await saveTask(task,request);assert.deepEqual(await saveTask(task,request),first);
 await assert.rejects(saveTask({...task,id:crypto.randomUUID()}),/duplicate key/);
 await assert.rejects(saveTask({...task,expected_version:1,case_id:crypto.randomUUID()}),/invalid_task_link/);
 await assert.rejects(saveTask({...task,expected_version:1,status:'complete'}),/invalid_task/);
 await assert.rejects(saveTask({...task,expected_version:1,status:'snoozed'}),/invalid_task/);
 const completed=await saveTask({...task,expected_version:1,status:'complete',completion_evidence:'Owner confirms callback completed'});assert.equal(completed.version,2);
 await assert.rejects(saveTask({...task,expected_version:1}),/version_conflict/);
 await assert.rejects(saveTask({...task,expected_version:2,provenance:{evidence:'rewritten'}}),/immutable_task_provenance/);
 const events=(await db.query('select input from customer_task_events where task_id=$1 order by occurred_at',[task.id])).rows;
 assert.equal(events.length,2);assert.match(events[1].input.completion_evidence,/Owner confirms/);
 assert.equal((await db.query('select status from customer_follow_up_tasks where id=$1',[task.id])).rows[0].status,'complete');
});
test('private switch links/RPC deny anon/authenticated and service role cannot alter audit',async()=>{
 for(const role of ['anon','authenticated']){await db.exec('reset role; set role '+role);await assert.rejects(db.query('select * from customer_interruption_events'),/permission denied/);await assert.rejects(switchCase({}),/permission denied/);await assert.rejects(db.query('select * from customer_task_events'),/permission denied/);await assert.rejects(db.query('select save_customer_follow_up_task($1,$2,$3)',[crypto.randomUUID(),'owner',{}]),/permission denied/)}
 await db.exec('reset role; set role service_role');await assert.rejects(db.query('update customer_interruption_events set actor=\'forged\''),/permission denied/);await assert.rejects(db.query('delete from customer_task_events'),/permission denied/);
 const security=(await db.query("select c.relname,c.relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in ('customer_interruption_events','customer_task_events')")).rows;assert.equal(security.length,2);assert.ok(security.every(row=>row.relrowsecurity));await db.close();
});
