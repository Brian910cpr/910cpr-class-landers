import test from 'node:test';
import assert from 'node:assert/strict';
import {groupRequest} from '../supabase/functions/group-request/core.mjs';
import {boardPrompts} from '../supabase/functions/owner-dashboard/core.mjs';
const input={requestId:'9e95b6d7-9c8c-4c90-81b6-2cb19b7d4471',formElapsedMs:2000,name:'Test Office',email:'test@example.invalid',program:'BLS On-Site',headcount:'12',comments:'Morning requested'};
test('group request validates contact details and retains the scheduling fields',()=>{const result=groupRequest(input);assert.match(result.details,/Headcount: 12/);assert.match(result.details,/Morning requested/);for(const override of [{name:''},{email:'invalid'},{headcount:'-1'},{program:''},{requestId:'bad'},{companyWebsite:'spam'},{formElapsedMs:0}])assert.throws(()=>groupRequest({...input,...override}));});
let handler;
globalThis.Deno={env:{get:name=>name==='SUPABASE_URL'?'https://database.invalid':name==='SUPABASE_SERVICE_ROLE_KEY'?'test-service-key':undefined},serve:fn=>handler=fn};
await import('../supabase/functions/group-request/index.ts');
function database(t,{failQueue=false}={}) {
  const inquiries=new Map(),cards=new Map();
  t.mock.method(globalThis,'fetch',async(url,options={})=>{
    assert.ok(String(url).startsWith('https://database.invalid/rest/v1/'),'no emails or other outbound services');
    const u=new URL(url),table=u.pathname.split('/').at(-1),body=options.body?JSON.parse(options.body):null;
    if(table==='requirement_inquiries'){
      if(body){if(!inquiries.has(body.id))inquiries.set(body.id,body);return new Response(null,{status:201});}
      const id=u.searchParams.get('id')?.slice(3);return Response.json(id?(inquiries.has(id)?[inquiries.get(id)]:[]):[]);
    }
    if(table==='production_board_cards'){
      if(failQueue)return new Response('{}',{status:503});
      if(!cards.has(body.id))cards.set(body.id,body);return new Response(null,{status:201});
    }
    assert.fail(`unexpected table ${table}`);
  });
  return {inquiries,cards,setQueueHealthy:()=>{failQueue=false;}};
}
const request=(body=input,origin='https://www.910cpr.com')=>new Request('https://edge.invalid/group-request',{method:'POST',headers:{origin,'content-type':'application/json'},body:JSON.stringify(body)});
test('a receipt requires both a saved inquiry and a Brian action prompt, with safe retries',async t=>{const db=database(t);const first=await handler(request());assert.equal(first.status,200);const receipt=await first.json();assert.equal(receipt.received,true);assert.equal(db.inquiries.size,1);assert.equal(db.cards.size,1);const prompt=boardPrompts([...db.cards.values()]);assert.equal(prompt.length,1);assert.equal(prompt[0].label,'Open request');const second=await (await handler(request())).json();assert.equal(second.reference,receipt.reference);assert.equal(db.inquiries.size,1);assert.equal(db.cards.size,1);});
test('queue failures show a retry instead of false success; a retry recovers the saved request',async t=>{const db=database(t,{failQueue:true});assert.equal((await handler(request())).status,503);assert.equal(db.inquiries.size,1);assert.equal(db.cards.size,0);db.setQueueHealthy();assert.equal((await handler(request())).status,200);assert.equal(db.inquiries.size,1);assert.equal(db.cards.size,1);});
test('unapproved origins and invalid submissions cannot write data',async t=>{t.mock.method(globalThis,'fetch',()=>assert.fail('must not write'));assert.equal((await handler(request(input,'https://example.com'))).status,403);assert.equal((await handler(request({...input,email:'invalid'}))).status,400);});
