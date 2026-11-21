import test from 'node:test';
import assert from 'node:assert/strict';
import {findNextInteraction,eligibleInteraction} from '../docs/admin/customer-interaction-next.mjs';
import {createInteractionCheckpoint} from '../docs/admin/customer-interaction-checkpoint.mjs';
import {createInteractionClient} from '../docs/admin/customer-interaction-client.mjs';
import {createHandler} from '../supabase/functions/customer-interactions/handler.ts';
import {readFileSync} from 'node:fs';

test('NEXT traverses older pages, excludes blocked/completed/current work and ranks active call first',async()=>{
 const calls=[];
 const client={list:async f=>{calls.push(f);return f.collection==='tasks'?{items:[],next_cursor:null}:f.before?{items:[{id:'older',status:'new'},{id:'call',kind:'phone',status:'in_progress'}],next_cursor:null}:{items:[{id:'current',status:'in_progress'},{id:'paused',status:'paused'},{id:'resolved',status:'resolved'},{id:'approval',status:'awaiting_approval'}],next_cursor:{before:'2026-10-14T12:00:00.123456Z',before_id:'cursor'}}}};
 assert.equal((await findNextInteraction(client,'current')).id,'call');
 assert.equal(calls[1].before,'2026-10-14T12:00:00.123456Z');
});
test('future snoozes and completed tasks never become due work; due work ranks above fresh with deterministic ID ties',async()=>{
 const rows=[{id:'z',status:'new'},{id:'a',status:'new'},{id:'due',status:'follow_up_due'}];
 const tasks=[{interaction_id:'due',status:'snoozed',due_at:'2026-10-15T00:00:00Z'}];
 const client={list:async f=>({items:f.collection==='tasks'?tasks:rows,next_cursor:null})};
 assert.equal((await findNextInteraction(client,'other',Date.parse('2026-10-14'))).id,'a');
 assert.equal((await findNextInteraction(client,'other',Date.parse('2026-10-16'))).id,'due');
 for(const status of ['complete','snoozed'])assert.equal(eligibleInteraction(rows[2],[{interaction_id:'due',status,due_at:'invalid'}]),false);
});
test('incomplete queue reads and cursor loops fail closed',async()=>{
 await assert.rejects(findNextInteraction({list:async()=>({items:[],next_cursor:{before:'same'}})},'current'),/Repeated/);
 await assert.rejects(findNextInteraction({list:async f=>{if(f.collection==='tasks')throw Error('offline');return {items:[{id:'a',status:'new'}]}}},'current'),/offline/);
});
test('disposition requires saved base/evidence and malformed completion receipt cannot confirm or poison identical retry',async()=>{
 const initial={id:'interaction',case_id:'case',kind:'email',source:'manual',source_id:'source',status:'in_progress',expected_version:1,document:{notes:'retained'}};
 let attempts=0;const bodies=[];
 const client=createInteractionClient({get:()=>true,snapshot:()=>0,current:()=>true,fetch:async(_,options)=>{
  const body=JSON.parse(options.body);bodies.push(body);const record={...body.input,version:2};
  if(++attempts===1)record.status='in_progress';
  return Response.json({interaction:record});
 }},{enabled:true,uuid:()=> 'request'});
 const draft=createInteractionCheckpoint(client,initial);
 assert.throws(()=>draft.disposition('resolved','owner confirmed'),/pending/);
 const saved=createInteractionCheckpoint(client,initial,{confirmed:true});
 assert.throws(()=>saved.disposition('resolved',''),/evidence/);
 saved.disposition('resolved','Owner confirmed no reply needed');
 await assert.rejects(saved.save(),/disposition receipt/);assert.equal(saved.canLeave(),false);
 await saved.save();assert.equal(saved.canLeave(),true);assert.deepEqual(bodies[0],bodies[1]);
 assert.equal(saved.view().draft.document.notes,'retained');
});

test('disposition coordinator -> transport -> handler -> SQL retains evidence and retries one committed resolution',async()=>{
 const {PGlite}=await import(process.env.PGLITE_MODULE||'@electric-sql/pglite');
 const db=new PGlite();
 try{
  await db.exec('create role anon; create role authenticated; create role service_role bypassrls; create table landerware_people(id uuid primary key)');
  for(const name of ['20261010210607_customer_interaction_storage.sql','20261010211804_customer_interaction_interruptions.sql','20261010212019_customer_follow_up_task_mutations.sql'])
   await db.exec(readFileSync(new URL('../supabase/migrations/'+name,import.meta.url),'utf8'));
  await db.exec('set role service_role');
  const handler=createHandler({authorize:async()=>true,actor:async()=> 'synthetic-owner',rest:async(path,options)=>{
   assert.equal(path,'rpc/save_customer_interaction');const {p_request_id,p_actor,p_input}=JSON.parse(options.body);
   return (await db.query('select save_customer_interaction($1,$2,$3) r',[p_request_id,p_actor,p_input])).rows[0].r;
  }});
  let drop=false;const requests=[];
  const client=createInteractionClient({get:()=>true,snapshot:()=>0,current:()=>true,fetch:async(url,options)=>{
   requests.push(JSON.parse(options.body));const result=await handler(new Request(url,{...options,headers:{...options.headers,origin:'https://www.910cpr.com'}}));
   if(drop){drop=false;throw Error('response lost after SQL commit')}
   return result;
  }},{enabled:true});
  const id=crypto.randomUUID();const checkpoint=createInteractionCheckpoint(client,{id,case_id:crypto.randomUUID(),expected_version:0,kind:'email',source:'manual',source_id:id,status:'in_progress',document:{callNotes:'Synthetic retained raw message'}});
  await checkpoint.save();checkpoint.disposition('resolved','Owner confirmed no reply necessary');drop=true;
  await assert.rejects(checkpoint.save(),/lost/);assert.equal(checkpoint.canLeave(),false);
  await checkpoint.save();assert.equal(checkpoint.canLeave(),true);assert.deepEqual(requests[1],requests[2]);
  const row=(await db.query('select * from customer_interactions where id=$1',[id])).rows[0];
  assert.equal(row.status,'resolved');assert.equal(row.version,2);assert.equal(row.document.callNotes,'Synthetic retained raw message');
  const events=(await db.query('select input from customer_interaction_events where interaction_id=$1',[id])).rows;
  assert.equal(events.length,2);assert.equal(events.find(e=>e.input.status==='resolved').input.document.disposition.evidence,'Owner confirmed no reply necessary');
 }finally{await db.close()}
});
