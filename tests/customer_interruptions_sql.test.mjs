import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHandler} from '../supabase/functions/customer-interactions/handler.ts';
import {createInteractionClient} from '../docs/admin/customer-interaction-client.mjs';
import {createInteractionSwitch} from '../docs/admin/customer-interaction-switch.mjs';
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
test('browser switch coordinator/transport/real handler/RPC commit once across response loss and resume',async()=>{
 const source=await fixture();let drop=true;const calls=[];
 const handler=createHandler({authorize:async()=>true,actor:async()=> 'synthetic-owner-session',rest:async(path,options)=>{
  assert.equal(path,'rpc/switch_customer_interaction');
  const args=JSON.parse(options.body);
  return (await db.query('select switch_customer_interaction($1,$2,$3) r',[args.p_request_id,args.p_actor,args.p_input])).rows[0].r;
 }});
 const client=createInteractionClient({get:()=>true,snapshot:()=>0,current:()=>true,fetch:async(url,options)=>{
  calls.push(options.body);const response=await handler(new Request(url,{...options,headers:{...options.headers,origin:'https://www.910cpr.com'}}));
  if(drop&&response.ok){drop=false;throw Error('lost after SQL commit')}
  return response;
 }},{enabled:true});
 const pending=createInteractionSwitch(client,'interrupt',source);
 await assert.rejects(pending.send(),/lost after SQL commit/);
 assert.equal((await reload(source.previous.id)).status,'paused');
 assert.equal((await reload(source.active.id)).version,1);
 const committed=await pending.send();assert.equal(calls[0],calls[1]);
 assert.equal((await db.query('select count(*)::int n from customer_interruption_events where request_id=$1',[committed.request_id])).rows[0].n,1);
 const previous=await reload(source.previous.id),active=await reload(source.active.id);
 const resumed=await createInteractionSwitch(client,'resume',{interrupt_request_id:committed.request_id,previous:{...previous,expected_version:previous.version,status:'in_progress'},active:{...active,expected_version:active.version,status:'resolved'}}).send();
 assert.equal(resumed.previous.version,3);assert.equal(resumed.active.status,'resolved');
 assert.equal((await reload(source.previous.id)).document.notes,'checkpoint including unsaved edits');
 await assert.rejects(createInteractionSwitch(client,'interrupt',source).send(),{status:409});
});

const saveTask=async(input,request=crypto.randomUUID())=>(await db.query('select save_customer_follow_up_task($1,$2,$3) r',[request,'owner',input])).rows[0].r;
const taskFor=active=>({id:crypto.randomUUID(),case_id:active.case_id,interaction_id:active.id,source_key:'manual:'+crypto.randomUUID(),title:'Synthetic promised callback',status:'pending',expected_version:0,provenance:{evidence:'Synthetic explicit owner promise'}});
const resumeInput=(source,interruptId,status='resolved')=>({operation:'resume',interrupt_request_id:interruptId,previous:{...source.previous,expected_version:2,status:'in_progress'},active:{...source.active,expected_version:1,status}});

test('task created after UI read prevents resolved resume and rolls back both interaction saves',async()=>{
 for(const status of ['proposed','pending','snoozed']){
  const source=await fixture(),interrupted=await switchCase(source),task={...taskFor(source.active),status,...(status==='snoozed'?{due_at:'2026-10-20T12:00:00Z'}:{})};
  await saveTask(task);
  const resume=resumeInput(source,interrupted.request_id),request=crypto.randomUUID();
  const before=(await db.query('select count(*)::int n from customer_interaction_events')).rows[0].n;
  await assert.rejects(switchCase(resume,request),{code:'40001'});
  assert.equal((await reload(source.previous.id)).status,'paused');assert.equal((await reload(source.previous.id)).version,2);
  assert.equal((await reload(source.active.id)).status,'in_progress');assert.equal((await reload(source.active.id)).version,1);
  assert.equal((await db.query('select count(*)::int n from customer_interaction_events')).rows[0].n,before);
  assert.equal((await db.query('select count(*)::int n from customer_interruption_events where request_id=$1',[request])).rows[0].n,0);
  // Explicit reconciled disposition retains the obligation; retry remains identical.
  const safe={...resume,active:{...resume.active,status:'follow_up_due'}},safeRequest=crypto.randomUUID();
  const result=await switchCase(safe,safeRequest);assert.deepEqual(await switchCase(safe,safeRequest),result);
  assert.equal(result.active.status,'follow_up_due');
 }
});

test('resolution-first rejects late creation/reopening without consuming requests; explicit reopen allows retry',async()=>{
 const source=await fixture(),interrupted=await switchCase(source),task=taskFor(source.active);
 const createdRequest=crypto.randomUUID();await saveTask(task,createdRequest);
 const completed={...task,expected_version:1,status:'complete',completion_evidence:'Synthetic owner confirms callback'};
 const completedRequest=crypto.randomUUID(),done=await saveTask(completed,completedRequest);
 const resume=resumeInput(source,interrupted.request_id),resumeRequest=crypto.randomUUID();
 const result=await switchCase(resume,resumeRequest);assert.equal(result.active.status,'resolved');
 assert.equal((await saveTask(task,createdRequest)).status,'pending'); // Earlier receipt survives current resolved state.
 assert.deepEqual(await saveTask(completed,completedRequest),done);
 assert.deepEqual(await switchCase(resume,resumeRequest),result);
 const late=taskFor(source.active),lateRequest=crypto.randomUUID(),reopenTask={...task,expected_version:2};
 await assert.rejects(saveTask(late,lateRequest),{code:'40001'});
 await assert.rejects(saveTask(reopenTask),{code:'40001'});
 assert.equal((await db.query('select count(*)::int n from customer_follow_up_tasks where id=$1',[late.id])).rows[0].n,0);
 assert.equal((await db.query('select count(*)::int n from customer_task_events where request_id=$1',[lateRequest])).rows[0].n,0);
 await save({...source.active,expected_version:2,status:'follow_up_due'});
 const saved=await saveTask(late,lateRequest);assert.equal(saved.version,1);
 await saveTask(reopenTask);assert.equal((await reload(source.active.id)).status,'follow_up_due');
});

test('single interaction save also refuses to resolve an outstanding task, then accepts evidenced completion',async()=>{
 const interaction=record();await save(interaction);const task=taskFor(interaction);await saveTask(task);
 await assert.rejects(save({...interaction,expected_version:1,status:'resolved'}),{code:'40001'});
 assert.equal((await reload(interaction.id)).version,1);
 await saveTask({...task,expected_version:1,status:'complete',completion_evidence:'Synthetic completed callback'});
 assert.equal((await save({...interaction,expected_version:1,status:'resolved'})).status,'resolved');
});

test('private switch links/RPC deny anon/authenticated and service role cannot alter audit',async()=>{
 for(const role of ['anon','authenticated']){await db.exec('reset role; set role '+role);await assert.rejects(db.query('select * from customer_interruption_events'),/permission denied/);await assert.rejects(switchCase({}),/permission denied/);await assert.rejects(db.query('select * from customer_task_events'),/permission denied/);await assert.rejects(db.query('select save_customer_follow_up_task($1,$2,$3)',[crypto.randomUUID(),'owner',{}]),/permission denied/)}
 await db.exec('reset role; set role service_role');await assert.rejects(db.query('update customer_interruption_events set actor=\'forged\''),/permission denied/);await assert.rejects(db.query('delete from customer_task_events'),/permission denied/);
 const security=(await db.query("select c.relname,c.relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in ('customer_interruption_events','customer_task_events')")).rows;assert.equal(security.length,2);assert.ok(security.every(row=>row.relrowsecurity));await db.close();
});
