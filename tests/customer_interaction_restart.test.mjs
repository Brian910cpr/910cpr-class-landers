import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, rm} from 'node:fs/promises';
import {readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
const {PGlite}=await import(process.env.PGLITE_MODULE||'@electric-sql/pglite');

test('disk reopen retains interrupted notes, audit, retry receipt and resumable versions',async()=>{
 const directory=await mkdtemp(join(tmpdir(),'crm-restart-'));
 let db;
 try {
  db=new PGlite(directory);
  await db.exec('create role anon; create role authenticated; create role service_role bypassrls; create table landerware_people(id uuid primary key)');
  for(const name of ['20261010210607_customer_interaction_storage.sql','20261010211804_customer_interaction_interruptions.sql','20261010212019_customer_follow_up_task_mutations.sql'])
   await db.exec(readFileSync(new URL('../supabase/migrations/'+name,import.meta.url),'utf8'));
  await db.exec('set role service_role');
  const record=kind=>{const id=crypto.randomUUID();return {id,case_id:crypto.randomUUID(),expected_version:0,kind,status:'in_progress',source:'manual',source_id:id,document:{notes:'Synthetic restart fixture'}}};
  const previous=record('email'),active=record('phone'),request=crypto.randomUUID();
  await db.query('select save_customer_interaction($1,$2,$3)',[crypto.randomUUID(),'synthetic-owner',previous]);
  const input={operation:'interrupt',previous:{...previous,expected_version:1,status:'paused',document:{notes:'Synthetic checkpoint',selection:'reply'}},active};
  const run=async(value,id)=>(await db.query('select switch_customer_interaction($1,$2,$3) as r',[id,'synthetic-owner',value])).rows[0].r;
  const receipt=await run(input,request);
  await db.close();db=null;
  db=new PGlite(directory);await db.exec('set role service_role');
  assert.deepEqual(await run(input,request),receipt);
  const rows=(await db.query('select id,status,version,document from customer_interactions order by id')).rows;
  const paused=rows.find(row=>row.id===previous.id);
  assert.equal(paused.status,'paused');assert.equal(paused.version,2);
  assert.deepEqual(paused.document,input.previous.document);
  assert.equal((await db.query('select count(*)::int n from customer_interruption_events')).rows[0].n,1);
  await assert.rejects(db.query('select save_customer_interaction($1,$2,$3)',[crypto.randomUUID(),'synthetic-owner',{...previous,expected_version:1}]),/version_conflict/);
  const resumed=await run({operation:'resume',interrupt_request_id:request,previous:{...input.previous,expected_version:2,status:'in_progress'},active:{...active,expected_version:1,status:'resolved'}},crypto.randomUUID());
  assert.equal(resumed.previous.version,3);assert.equal(resumed.active.status,'resolved');
  await db.close();db=null;
  db=new PGlite(directory);await db.exec('set role service_role');
  assert.equal((await db.query('select status from customer_interactions where id=$1',[previous.id])).rows[0].status,'in_progress');
  await db.exec('reset role; set role authenticated');
  await assert.rejects(db.query('select * from customer_interactions'),/permission denied/);
 } finally {
  if(db) await db.close();
  await rm(directory,{recursive:true,force:true});
 }
});

test('completed follow-up survives disk reopen and lost-response retries without reopening work',async()=>{
 const directory=await mkdtemp(join(tmpdir(),'crm-task-restart-'));
 let db;
 try {
  db=new PGlite(directory);
  await db.exec('create role anon; create role authenticated; create role service_role bypassrls; create table landerware_people(id uuid primary key)');
  for(const name of ['20261010210607_customer_interaction_storage.sql','20261010211804_customer_interaction_interruptions.sql','20261010212019_customer_follow_up_task_mutations.sql'])
   await db.exec(readFileSync(new URL('../supabase/migrations/'+name,import.meta.url),'utf8'));
  await db.exec('set role service_role');
  const interaction={id:crypto.randomUUID(),case_id:crypto.randomUUID(),expected_version:0,kind:'phone',status:'follow_up_due',source:'manual',source_id:crypto.randomUUID(),document:{notes:'Synthetic promised callback'}};
  await db.query('select save_customer_interaction($1,$2,$3)',[crypto.randomUUID(),'synthetic-owner',interaction]);
  const task={id:crypto.randomUUID(),case_id:interaction.case_id,interaction_id:interaction.id,source_key:'synthetic:'+interaction.id,title:'Synthetic callback',status:'pending',expected_version:0,provenance:{evidence:'Synthetic call commitment'}};
  const save=async(value,request,actor='synthetic-owner')=>(await db.query('select save_customer_follow_up_task($1,$2,$3) r',[request,actor,value])).rows[0].r;
  const createRequest=crypto.randomUUID(),created=await save(task,createRequest);
  const completeRequest=crypto.randomUUID(),completedInput={...task,expected_version:1,status:'complete',completion_evidence:'Synthetic owner confirms callback'};
  const completed=await save(completedInput,completeRequest);
  await db.close();db=null;
  db=new PGlite(directory);await db.exec('set role service_role');
  // An old create response is replayed verbatim; it must never reset current state.
  assert.deepEqual(await save(task,createRequest),created);
  assert.deepEqual(await save(completedInput,completeRequest),completed);
  await assert.rejects(save(task,createRequest,'different-session'),/idempotency_conflict/);
  await assert.rejects(save({...task,expected_version:1},crypto.randomUUID()),/version_conflict/);
  await assert.rejects(save({...task,id:crypto.randomUUID()},crypto.randomUUID()),/duplicate key/);
  const stored=(await db.query('select * from customer_follow_up_tasks where id=$1',[task.id])).rows[0];
  assert.equal(stored.status,'complete');assert.equal(stored.version,2);
  assert.deepEqual(stored.provenance,task.provenance);
  assert.equal((await db.query("select count(*)::int n from customer_follow_up_tasks where status in ('pending','snoozed','proposed')")).rows[0].n,0);
  const events=(await db.query('select input from customer_task_events where task_id=$1 order by occurred_at',[task.id])).rows;
  assert.equal(events.length,2);assert.deepEqual(events[1].input,completedInput);
  for(const role of ['anon','authenticated']){
   await db.exec('reset role; set role '+role);
   await assert.rejects(db.query('select * from customer_follow_up_tasks'),/permission denied/);
   await assert.rejects(db.query('select * from customer_task_events'),/permission denied/);
   await assert.rejects(save(completedInput,completeRequest),/permission denied/);
  }
 } finally {
  if(db) await db.close();
  await rm(directory,{recursive:true,force:true});
 }
});

test('saved resolution survives restart with immutable receipts and rejects late obligations until evidenced reopen',async()=>{
 const directory=await mkdtemp(join(tmpdir(),'crm-resolution-restart-'));
 let db;
 try {
  db=new PGlite(directory);
  await db.exec('create role anon; create role authenticated; create role service_role bypassrls; create table landerware_people(id uuid primary key)');
  for(const name of ['20261010210607_customer_interaction_storage.sql','20261010211804_customer_interaction_interruptions.sql','20261010212019_customer_follow_up_task_mutations.sql'])
   await db.exec(readFileSync(new URL('../supabase/migrations/'+name,import.meta.url),'utf8'));
  await db.exec('set role service_role');
  const id=crypto.randomUUID(),record={id,case_id:crypto.randomUUID(),expected_version:0,kind:'email',status:'in_progress',source:'manual',source_id:id,document:{notes:'Synthetic original message'}};
  const save=async(input,request,actor='synthetic-owner')=>(await db.query('select save_customer_interaction($1,$2,$3) r',[request,actor,input])).rows[0].r;
  const createRequest=crypto.randomUUID(),created=await save(record,createRequest);
  const resolution={...record,expected_version:1,status:'resolved',document:{...record.document,disposition:{evidence:'Synthetic owner verified no reply needed'}}};
  const resolveRequest=crypto.randomUUID(),resolved=await save(resolution,resolveRequest);
  await db.close();db=null;
  db=new PGlite(directory);await db.exec('set role service_role');
  assert.deepEqual(await save(resolution,resolveRequest),resolved);
  assert.deepEqual(await save(record,createRequest),created);
  await assert.rejects(save(resolution,resolveRequest,'other-owner'),/idempotency_conflict/);
  await assert.rejects(save({...resolution,document:{notes:'changed retry'}},resolveRequest),/idempotency_conflict/);
  await assert.rejects(save({...record,expected_version:1},crypto.randomUUID()),/version_conflict/);
  const task={id:crypto.randomUUID(),case_id:record.case_id,interaction_id:id,source_key:'synthetic:'+id,title:'Synthetic late callback',status:'pending',expected_version:0,provenance:{evidence:'Synthetic new obligation'}};
  const taskRequest=crypto.randomUUID();
  const saveTask=async()=>(await db.query('select save_customer_follow_up_task($1,$2,$3) r',[taskRequest,'synthetic-owner',task])).rows[0].r;
  await assert.rejects(saveTask(),/conflict/);
  let row=(await db.query('select * from customer_interactions where id=$1',[id])).rows[0];
  assert.equal(row.status,'resolved');assert.equal(row.version,2);assert.deepEqual(row.document,resolution.document);
  assert.equal((await db.query('select count(*)::int n from customer_interaction_events')).rows[0].n,2);
  assert.equal((await db.query('select count(*)::int n from customer_task_events')).rows[0].n,0);
  const reopen={...resolution,expected_version:2,status:'in_progress',document:{...resolution.document,disposition:{evidence:'Synthetic owner verified new obligation'}}};
  const reopenRequest=crypto.randomUUID(),reopened=await save(reopen,reopenRequest);
  await saveTask();
  await db.close();db=null;
  db=new PGlite(directory);await db.exec('set role service_role');
  // Historical resolution retry must not resolve the now-reopened interaction.
  assert.deepEqual(await save(resolution,resolveRequest),resolved);
  assert.deepEqual(await save(reopen,reopenRequest),reopened);
  row=(await db.query('select * from customer_interactions where id=$1',[id])).rows[0];
  assert.equal(row.status,'in_progress');assert.equal(row.version,3);assert.deepEqual(row.document,reopen.document);
  await assert.rejects(save({...resolution,expected_version:3},crypto.randomUUID()),/conflict/);
  assert.equal((await db.query('select count(*)::int n from customer_interaction_events')).rows[0].n,3);
  assert.equal((await db.query('select count(*)::int n from customer_task_events')).rows[0].n,1);
  for(const role of ['anon','authenticated']){
   await db.exec('reset role; set role '+role);
   await assert.rejects(db.query('select * from customer_interaction_events'),/permission denied/);
   await assert.rejects(save(resolution,resolveRequest),/permission denied/);
  }
 } finally {
  if(db)await db.close();
  await rm(directory,{recursive:true,force:true});
 }
});
