const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {stripTypeScriptTypes} = require('node:module');
const policy = JSON.parse(fs.readFileSync('docs/data/public-registration-closures.json','utf8'));

function endpoint({start='2026-10-21T12:00:00-04:00',end='2026-10-21T14:00:00-04:00',id='14721759',paid=false}={}) {
  const calls=[];let handler;
  const source=fs.readFileSync('supabase/functions/public-registration/index.ts','utf8').replace(/^import .*;\r?\n/gm,'');
  const fetch=async(url,init={})=>{
    url=String(url);calls.push({url,method:init.method||'GET'});
    if(url.endsWith('/data/schedule_future.json'))return Response.json({sessions:[{session_id:id,course_id:'209806',start_at:start,end_at:end,public_direct_booking:true,registration_status:'open'}]});
    if(url.includes('/rpc/assert_public_registration_open')){
      const p=JSON.parse(init.body),a=Date.parse(p.p_start),b=Math.max(Date.parse(p.p_end||p.p_start),a+1);
      if(policy.closures.some(c=>a<Date.parse(c.endsAt)&&b>Date.parse(c.startsAt)))return Response.json({message:'registration_date_closed'},{status:400});
      return Response.json(null);
    }
    if(url.includes('landerware_registration_catalog?'))return Response.json([{course_id:'209806',course_name:'fixture',unit_amount:7500,currency:'usd',addons:[]}]);
    if(url.includes('landerware_public_orders?'))return Response.json([{id:'00000000-0000-4000-8000-000000000001',external_class_id:id,status:paid?'paid':'held',hold_expires_at:'2030-01-01T00:00:00Z'}]);
    throw Error('Unexpected side effect or request: '+url);
  };
  const context=vm.createContext({URL,URLSearchParams,Date,Request,Response,crypto:globalThis.crypto,fetch,console,
    Deno:{serve(fn){handler=fn},env:{get:key=>({SUPABASE_URL:'https://fixture.test',SUPABASE_SERVICE_ROLE_KEY:'fixture-only'})[key]}}});
  vm.runInContext(stripTypeScriptTypes(source),context);
  const call=(path,method='GET',body)=>handler(new Request('https://fixture.test/functions/v1/public-registration/'+path,{method,headers:{Origin:'https://www.910cpr.com','content-type':'application/json','idempotency-key':'fixture-only'},...(body?{body:JSON.stringify(body)}:{})}));
  const writes=()=>calls.filter(c=>c.method!=='GET'&&!c.url.includes('/rpc/assert_public_registration_open'));
  return {call,calls,writes};
}

test('closed native lookup is rejected before catalog or writes',async()=>{
  const e=endpoint();const r=await e.call('session/14721759');assert.equal(r.status,409);
  assert.equal((await r.json()).error,'registration_date_closed');assert.equal(e.writes().length,0);
  assert.equal(e.calls.some(c=>c.url.includes('catalog?')),false);
});
test('closed POST start cannot create person, registration, hold or Stripe checkout',async()=>{
  const e=endpoint();const r=await e.call('start','POST',{sessionId:'14721759',students:[]});
  assert.equal(r.status,409);assert.equal(e.writes().length,0);
});
test('workspace-only Jessica uses the same pre-write closure check',async()=>{
  const id='lw-1c863087-7bc5-4012-8286-503e61bc7d37',e=endpoint({id});
  const r=await e.call('start','POST',{sessionId:id,students:[]});assert.equal(r.status,409);assert.equal(e.writes().length,0);
});
test('other-day lookups remain available',async()=>{
  for(const start of ['2026-10-20T12:00:00-04:00','2026-10-22T00:00:00-04:00']){
    const e=endpoint({start,end:start});assert.equal((await e.call('session/14721759')).status,200);assert.equal(e.writes().length,0);
  }
});
test('unpaid recovery cannot return a new payment path on closed date',async()=>{
  const e=endpoint();const r=await e.call('recover/00000000-0000-4000-8000-000000000001');
  assert.equal(r.status,409);assert.equal(e.writes().length,0);
});
test('existing paid recovery and order completion remain readable',async()=>{
  for(const route of ['recover/00000000-0000-4000-8000-000000000001','order/00000000-0000-4000-8000-000000000001']){
    const e=endpoint({paid:true}),r=await e.call(route);assert.equal(r.status,200);assert.equal((await r.json()).status,'paid');
    assert.equal(e.calls.some(c=>c.url.includes('assert_public_registration_open')),false);assert.equal(e.writes().length,0);
  }
});
test('overnight reservation intersecting Wednesday is closed',async()=>{
  const e=endpoint({start:'2026-10-20T23:30:00-04:00',end:'2026-10-21T00:30:00-04:00'});
  assert.equal((await e.call('session/14721759')).status,409);
});

test('Tuesday reservation ending exactly at closure remains available',async()=>{
 const e=endpoint({start:'2026-10-20T23:00:00-04:00',end:'2026-10-21T00:00:00-04:00'});
 assert.equal((await e.call('session/14721759')).status,200);assert.equal(e.writes().length,0);
});
