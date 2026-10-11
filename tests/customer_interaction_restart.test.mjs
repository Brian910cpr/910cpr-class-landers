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
