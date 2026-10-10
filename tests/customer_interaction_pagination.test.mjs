import test from 'node:test';
import assert from 'node:assert/strict';
import {createHandler} from '../supabase/functions/customer-interactions/handler.ts';
const stamp='2026-10-10T20:00:00.123456+00:00';
const uuid=n=>`11111111-1111-4111-8111-${String(n).padStart(12,'0')}`;
const get=params=>new Request(`https://example.test/customer-interactions?${new URLSearchParams(params)}`);
test('paused recovery traverses over 100 tied records with no gaps or duplicate rows',async()=>{
 const rows=Array.from({length:125},(_,i)=>({id:uuid(125-i),created_at:stamp,status:'paused'}));
 const handle=createHandler({authorize:async()=>true,actor:async()=>assert.fail(),rest:async path=>{
  const [table,raw]=path.split('?'),q=new URLSearchParams(raw);
  assert.equal(table,'customer_interactions');assert.equal(q.get('order'),'created_at.desc,id.desc');assert.equal(q.get('status'),'eq.paused');
  const cursor=q.get('or'); const boundary=cursor?.match(/id\.lt\.([0-9a-f-]+)/)?.[1];
  if(cursor)assert.match(cursor,/\.123456\+00:00/);
  return rows.filter(r=>!boundary||r.id<boundary).slice(0,Number(q.get('limit')));
 }});
 let cursor={},all=[],pages=0;
 do {
  const res=await handle(get({collection:'interactions',status:'paused',limit:'50',...cursor}));
  assert.equal(res.status,200);assert.equal(res.headers.get('cache-control'),'no-store');
  const page=await res.json();all.push(...page.items.map(r=>r.id));pages++;cursor=page.next_cursor;
 }while(cursor);
 assert.equal(pages,3);assert.deepEqual(all,rows.map(r=>r.id));assert.equal(new Set(all).size,125);
});
test('collection/filter/cursor injection and incomplete/repeated parameters fail before storage',async()=>{
 const handle=createHandler({authorize:async()=>true,actor:async()=>assert.fail(),rest:async()=>assert.fail()});
 for(const params of [{collection:'__proto__'},{collection:'toString'},{collection:'interactions',limit:'101'},{collection:'interactions',limit:'0'},{collection:'interactions',limit:'1e2'},{collection:'interactions',before:stamp},{collection:'interactions',before:stamp,before_id:'bad'},{collection:'interactions',before:stamp+',id.gt.0',before_id:uuid(1)},{collection:'interactions',status:'paused,or(id.gt.0)'},{collection:'interruptions',status:'paused'},{collection:'tasks',select:'secret'}]){
  assert.equal((await handle(get(params))).status,400,JSON.stringify(params));
 }
 assert.equal((await handle(new Request('https://example.test/?collection=tasks&limit=1&limit=2'))).status,400);
});
test('all collection pages use approved table/key and stop without spurious cursor',async()=>{
 for(const [collection,table,key] of [['tasks','customer_follow_up_tasks','id'],['interruptions','customer_interruption_events','request_id']]){
  const handle=createHandler({authorize:async()=>true,actor:async()=>assert.fail(),rest:async path=>{assert.ok(path.startsWith(table+'?'));assert.ok(decodeURIComponent(path).includes(key+'.desc'));return []}});
  const page=await (await handle(get({collection}))).json();assert.deepEqual(page.items,[]);assert.equal(page.has_more,false);assert.equal(page.next_cursor,null);
 }
});
test('paginated recovery remains owner-only',async()=>{
 const handle=createHandler({authorize:async()=>false,actor:async()=>assert.fail(),rest:async()=>assert.fail()});
 assert.equal((await handle(get({collection:'interactions',status:'paused'}))).status,401);
});
test('case recovery and direct interaction resume use canonical UUID filters',async()=>{
 for(const collection of ['interactions','tasks']){
  const handle=createHandler({authorize:async()=>true,actor:async()=>assert.fail(),rest:async path=>{
   const q=new URLSearchParams(path.split('?')[1]);assert.equal(q.get('case_id'),'eq.'+uuid(1));
   assert.equal(q.get(collection==='interactions'?'id':'interaction_id'),'eq.'+uuid(2));return [];
  }});
  assert.equal((await handle(get({collection,case_id:uuid(1),interaction_id:uuid(2)}))).status,200);
 }
});
test('invalid case linkage and unsupported receipt filters never reach storage',async()=>{
 const handle=createHandler({authorize:async()=>true,actor:async()=>assert.fail(),rest:async()=>assert.fail()});
 for(const params of [{collection:'tasks',case_id:'bad'},{collection:'interactions',interaction_id:uuid(1)+',id.gt.0'},{collection:'interruptions',case_id:uuid(1)},{collection:'tasks',case_id:''}]){
  assert.equal((await handle(get(params))).status,400);
 }
});
