import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createInteractionClient} from '../docs/admin/customer-interaction-client.mjs';
import {createFollowUpTaskWrite} from '../docs/admin/customer-interaction-task.mjs';
import {createHandler} from '../supabase/functions/customer-interactions/handler.ts';
const input=()=>({id:crypto.randomUUID(),case_id:crypto.randomUUID(),interaction_id:crypto.randomUUID(),expected_version:0,source_key:'manual:'+crypto.randomUUID(),title:'Synthetic promised callback',status:'pending',provenance:{evidence:'Synthetic owner note',detail:{b:2,a:1}},due_at:'2026-10-15T12:30:00.123456Z'});
function fixture(respond){
  let generation=0;const calls=[];
  const client=createInteractionClient({get:()=>true,snapshot:()=>generation,current:s=>s===generation,fetch:async(url,options)=>{const body=JSON.parse(options.body);calls.push(body);return respond(body)}},{enabled:true});
  return {calls,client,lock:()=>generation++};
}
const receipt=body=>({task:{...structuredClone(body.input),version:body.input.expected_version+1,due_at:body.input.due_at??null}});

test('task writes coalesce, retain immutable input and block leaving until confirmed',async()=>{
  let finish;const f=fixture(()=>new Promise(r=>finish=r)),source=input(),pending=createFollowUpTaskWrite(f.client,source);
  source.title='later caller mutation';assert.equal(pending.canLeave(),false);
  const a=pending.send(),b=pending.send();assert.equal(pending.view().state,'saving');
  finish(new Response('{}',{status:503}));await assert.rejects(a);await assert.rejects(b);
  assert.equal(f.calls.length,1);assert.equal(pending.view().state,'error');assert.equal(pending.canLeave(),false);
  const retry=pending.send();finish(Response.json(receipt(f.calls[0])));const saved=await retry;
  assert.equal(saved.title,'Synthetic promised callback');assert.deepEqual(f.calls[0],f.calls[1]);
  saved.title='mutated receipt';assert.equal((await pending.send()).title,'Synthetic promised callback');
  const view=pending.view();view.input.title='mutated view';assert.equal(pending.view().input.title,'Synthetic promised callback');
  assert.equal(pending.canLeave(),true);
  f.lock();await assert.rejects(pending.send(),{reconcile:true});assert.equal(pending.canLeave(),false);
});

test('malformed task identity, disposition, linkage, version, evidence and due receipts never poison retry',async()=>{
  const mutations=[r=>r.task.id='wrong',r=>r.task.case_id='wrong',r=>r.task.interaction_id='wrong',r=>r.task.source_key='wrong',r=>r.task.title='wrong',r=>r.task.status='complete',r=>r.task.version='1',r=>r.task.version=0,r=>r.task.version=2,r=>r.task.provenance.evidence='wrong',r=>r.task.due_at='2026-10-15T12:30:00.123457Z',r=>r.task.due_at='invalid',r=>delete r.task.due_at];
  for(const mutate of mutations){
    let attempt=0;const f=fixture(async body=>{const data=receipt(body);if(++attempt===1)mutate(data);return Response.json(data)});
    const pending=createFollowUpTaskWrite(f.client,input());await assert.rejects(pending.send(),/Invalid task receipt/);
    assert.equal(pending.canLeave(),false);await pending.send();assert.equal(pending.canLeave(),true);
    assert.deepEqual(f.calls[0],f.calls[1]);
  }
});

test('equivalent JSON order and timezone due values confirm, including absent input due time',async()=>{
  const f=fixture(async body=>{const data=receipt(body);data.task.provenance={detail:{a:1,b:2},evidence:body.input.provenance.evidence};if(body.input.due_at)data.task.due_at='2026-10-15T08:30:00.123456-04:00';return Response.json(data)});
  await createFollowUpTaskWrite(f.client,input()).send();
  const noDue=input();delete noDue.due_at;await createFollowUpTaskWrite(f.client,noDue).send();
});

test('task conflicts and changed sessions retain input and cannot authorize NEXT',async()=>{
  for(const status of [400,401,403,409,413]){
    const f=fixture(async()=>new Response('{}',{status})),source=input(),pending=createFollowUpTaskWrite(f.client,source);
    await assert.rejects(pending.send(),{status});await assert.rejects(pending.send(),{status});
    assert.deepEqual(pending.view().input,source);assert.equal(pending.view().state,'conflict');assert.equal(pending.canLeave(),false);assert.equal(f.calls.length,1);
  }
  let finish;const f=fixture(()=>new Promise(r=>finish=r)),pending=createFollowUpTaskWrite(f.client,input());
  const flight=pending.send();f.lock();finish(Response.json(receipt(f.calls[0])));
  await assert.rejects(flight,{reconcile:true});await assert.rejects(pending.send(),{reconcile:true});assert.equal(pending.canLeave(),false);
});

test('coordinator + transport + actual handler + SQL preserve completion after lost response and reject stale/duplicate writes',async()=>{
  const {PGlite}=await import(process.env.PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
  try{
    await db.exec('create role anon; create role authenticated; create role service_role bypassrls; create table landerware_people(id uuid primary key)');
    for(const name of ['20261010210607_customer_interaction_storage.sql','20261010211804_customer_interaction_interruptions.sql','20261010212019_customer_follow_up_task_mutations.sql'])
      await db.exec(readFileSync(new URL('../supabase/migrations/'+name,import.meta.url),'utf8'));
    await db.exec('set role service_role');
    const source=input();await db.query('select save_customer_interaction($1,$2,$3)',[crypto.randomUUID(),'synthetic-owner',{id:source.interaction_id,case_id:source.case_id,expected_version:0,kind:'phone',status:'follow_up_due',source:'manual',source_id:'synthetic:'+source.interaction_id,document:{notes:source.provenance.evidence}}]);
    const handler=createHandler({authorize:async()=>true,actor:async()=> 'synthetic-owner',rest:async(path,options)=>{
      assert.equal(path,'rpc/save_customer_follow_up_task');const p=JSON.parse(options.body);
      return (await db.query('select save_customer_follow_up_task($1,$2,$3) r',[p.p_request_id,p.p_actor,p.p_input])).rows[0].r;
    }});
    let lose=false;const bodies=[];
    const client=createInteractionClient({get:()=>true,snapshot:()=>0,current:()=>true,fetch:async(url,options)=>{
      bodies.push(options.body);const response=await handler(new Request(url,{...options,headers:{...options.headers,origin:'https://www.910cpr.com'}}));
      if(lose){lose=false;throw Error('Synthetic lost response after commit')}return response;
    }},{enabled:true});
    const created=await createFollowUpTaskWrite(client,source).send();assert.equal(created.version,1);
    const completion={...source,expected_version:created.version,status:'complete',completion_evidence:'Synthetic owner confirms callback completed'};
    const pending=createFollowUpTaskWrite(client,completion);lose=true;await assert.rejects(pending.send(),/lost response/);assert.equal(pending.canLeave(),false);
    // The DB committed but navigation still waits for a validated matching receipt.
    assert.equal((await db.query('select status from customer_follow_up_tasks where id=$1',[source.id])).rows[0].status,'complete');
    const completed=await pending.send();assert.equal(completed.version,2);assert.equal(pending.canLeave(),true);assert.equal(bodies.at(-1),bodies.at(-2));
    const events=(await db.query('select input from customer_task_events where task_id=$1',[source.id])).rows;
    assert.equal(events.length,2);assert.ok(events.some(e=>e.input.completion_evidence===completion.completion_evidence));
    const stale=createFollowUpTaskWrite(client,{...source,expected_version:1});await assert.rejects(stale.send(),{status:409});assert.equal(stale.canLeave(),false);
    const duplicate=createFollowUpTaskWrite(client,{...source,id:crypto.randomUUID()});await assert.rejects(duplicate.send(),{status:409});assert.equal(duplicate.canLeave(),false);
    const invalid=createFollowUpTaskWrite(client,{...completion,expected_version:2,completion_evidence:''});await assert.rejects(invalid.send(),{status:400});assert.equal(invalid.canLeave(),false);
    assert.equal((await db.query('select version from customer_follow_up_tasks where id=$1',[source.id])).rows[0].version,2);
  }finally{await db.close()}
});
