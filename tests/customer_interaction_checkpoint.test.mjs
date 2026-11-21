import test from 'node:test';
import assert from 'node:assert/strict';
import {createInteractionCheckpoint} from '../docs/admin/customer-interaction-checkpoint.mjs';
import {createInteractionClient} from '../docs/admin/customer-interaction-client.mjs';
const initial=()=>({id:'synthetic-id',expected_version:0,document:{notes:'original'}});
function fixture(fetcher){
 const calls=[];let sequence=0;
 const client=createInteractionClient({get:()=>true,snapshot:()=>0,current:()=>true,fetch:async(url,options)=>{calls.push(JSON.parse(options.body));return fetcher(calls.at(-1));}},{enabled:true,uuid:()=>String(++sequence)});
 return {calls,checkpoint:createInteractionCheckpoint(client,initial())};
}
test('only a matching confirmed checkpoint permits navigation; caller mutations are isolated',async()=>{
 const f=fixture(async()=>Response.json({interaction:{id:'synthetic-id',version:1}}));
 const exposed=f.checkpoint.view();exposed.draft.document.notes='external';
 assert.equal(f.checkpoint.canLeave(),false);assert.throws(()=>f.checkpoint.load({id:'other',version:2}));
 assert.equal((await f.checkpoint.save()).state,'saved');assert.equal(f.checkpoint.canLeave(),true);
 assert.equal(f.calls[0].input.document.notes,'original');
 f.checkpoint.load({id:'other',version:2,document:{notes:'stored'}});
 assert.equal(f.checkpoint.view().draft.expected_version,2);
});
test('typing during a save survives receipt and next checkpoint uses confirmed base version',async()=>{
 let finish;const f=fixture(()=>new Promise(r=>finish=r));
 const saving=f.checkpoint.save();const overlapping=f.checkpoint.save();
 f.checkpoint.edit({notes:'typed while saving'});finish(Response.json({interaction:{id:'synthetic-id',version:1}}));
 await saving;await overlapping;
 assert.equal(f.calls.length,1);assert.equal(f.checkpoint.view().state,'unsaved');assert.equal(f.checkpoint.canLeave(),false);
 assert.equal(f.checkpoint.view().draft.document.notes,'typed while saving');
 const next=f.checkpoint.save();finish(Response.json({interaction:{id:'synthetic-id',version:2}}));await next;
 assert.equal(f.calls[1].input.expected_version,1);assert.equal(f.calls[1].input.document.notes,'typed while saving');
 assert.equal(f.checkpoint.canLeave(),true);
});
test('uncertain save retains identical request while later draft edits await another checkpoint',async()=>{
 let fail=true;const f=fixture(async()=>{if(fail){fail=false;throw Error('lost response')}return Response.json({interaction:{id:'synthetic-id',version:1}})});
 await assert.rejects(f.checkpoint.save(),/lost response/);const request=f.checkpoint.view().pendingRequestId;
 f.checkpoint.edit({notes:'new text'});assert.equal(f.checkpoint.view().state,'error');
 assert.throws(()=>f.checkpoint.load({id:'other',version:2}));
 await f.checkpoint.save();assert.deepEqual(f.calls[0],f.calls[1]);assert.equal(f.calls[1].request_id,request);
 assert.equal(f.checkpoint.view().state,'unsaved');assert.equal(f.checkpoint.view().draft.document.notes,'new text');
});
test('conflicts retain draft and stop new requests rather than overwriting server work',async()=>{
 const f=fixture(async()=>new Response('{}',{status:409}));
 await assert.rejects(f.checkpoint.save(),{status:409});f.checkpoint.edit({notes:'keep this'});
 await assert.rejects(f.checkpoint.save(),{reconcile:true});assert.equal(f.calls.length,1);
 assert.equal(f.checkpoint.view().state,'conflict');assert.equal(f.checkpoint.view().draft.document.notes,'keep this');
 assert.equal(f.checkpoint.canLeave(),false);
});
test('wrong identity or nonadvancing receipt never clears unsaved state',async()=>{
 for(const record of [{id:'another',version:1},{id:'synthetic-id',version:0},{id:'synthetic-id',version:'1'}]){
 const f=fixture(async()=>Response.json({interaction:record}));
 await assert.rejects(f.checkpoint.save(),/identity\/version/);assert.equal(f.checkpoint.canLeave(),false);
 assert.equal(f.checkpoint.view().state,'error');assert.ok(f.checkpoint.view().pendingRequestId);
 }
});

test('explicit conflict reconciliation preserves draft and starts a fresh versioned request',async()=>{
 let conflict=true;const f=fixture(async()=>{if(conflict){conflict=false;return new Response('{}',{status:409})}return Response.json({interaction:{id:'synthetic-id',version:4}})});
 await assert.rejects(f.checkpoint.save(),{status:409});
 assert.throws(()=>f.checkpoint.reconcile({id:'wrong',version:3}));
 f.checkpoint.edit({notes:'reviewed merged draft'});f.checkpoint.reconcile({id:'synthetic-id',version:3});
 await f.checkpoint.save();assert.notEqual(f.calls[0].request_id,f.calls[1].request_id);
 assert.equal(f.calls[1].input.expected_version,3);assert.equal(f.calls[1].input.document.notes,'reviewed merged draft');
 assert.equal(f.checkpoint.canLeave(),true);
 const uncertain=fixture(async()=>{throw Error('offline')});await assert.rejects(uncertain.checkpoint.save());
 assert.throws(()=>uncertain.checkpoint.reconcile({id:'synthetic-id',version:1}));
});

test('a fetched confirmed checkpoint permits navigation without a redundant write',async()=>{
 const client={prepare:()=>assert.fail('fetch does not write')};
 const c=createInteractionCheckpoint(client,{id:'stored',expected_version:4,document:{notes:'stored'}},{confirmed:true});
 assert.equal(c.canLeave(),true);assert.equal((await c.save()).state,'saved');
 c.edit({notes:'edited'});assert.equal(c.canLeave(),false);
});


test('malformed acknowledgment does not poison identical retry or permit navigation',async()=>{
 for(const malformed of [{id:'another',version:1},{id:'synthetic-id',version:0},{id:'synthetic-id',version:'1'}]){
  let attempt=0;
  const f=fixture(async()=>Response.json({interaction:++attempt===1?malformed:{id:'synthetic-id',version:1}}));
  await assert.rejects(f.checkpoint.save(),/identity\/version/);
  assert.equal(f.checkpoint.canLeave(),false);
  f.checkpoint.edit({notes:'typed after malformed response'});
  await f.checkpoint.save();
  assert.deepEqual(f.calls[0],f.calls[1]);
  assert.equal(f.checkpoint.view().draft.expected_version,1);
  assert.equal(f.checkpoint.view().draft.document.notes,'typed after malformed response');
  assert.equal(f.checkpoint.view().state,'unsaved');
  assert.equal(f.checkpoint.canLeave(),false);
 }
});
