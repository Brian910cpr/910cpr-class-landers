import test from 'node:test';
import assert from 'node:assert/strict';
import {createHandler} from '../supabase/functions/customer-interactions/handler.ts';
const origins=['https://www.910cpr.com','https://910cpr.com'];
const req=(origin,method='GET')=>new Request('https://example.test/customer-interactions',{method,headers:origin===undefined?{}:{origin}});
test('existing owner origins receive matching CORS on preflight without authorization or storage',async()=>{
 const handle=createHandler({authorize:async()=>assert.fail(),actor:async()=>assert.fail(),rest:async()=>assert.fail()});
 for(const origin of origins){const res=await handle(req(origin,'OPTIONS'));assert.equal(res.status,204);assert.equal(res.headers.get('access-control-allow-origin'),origin);assert.equal(res.headers.get('vary'),'Origin');assert.match(res.headers.get('access-control-allow-headers'),/x-landerware-owner-session/);assert.equal(res.headers.get('access-control-allow-methods'),'GET,POST,OPTIONS');assert.equal(res.headers.get('cache-control'),'no-store');}
});
test('foreign, opaque, lookalike, local and preview origins fail before owner authorization',async()=>{
 const handle=createHandler({authorize:async()=>assert.fail(),actor:async()=>assert.fail(),rest:async()=>assert.fail()});
 for(const origin of ['null','https://www.910cpr.com.attacker.test','http://www.910cpr.com','https://www.910cpr.com:444','http://localhost:8000','https://preview.example.test'])for(const method of ['OPTIONS','GET','POST']){const res=await handle(req(origin,method));assert.equal(res.status,403);assert.equal(res.headers.get('access-control-allow-origin'),null);assert.equal(res.headers.get('cache-control'),'no-store');}
});
test('allowed CORS never substitutes for auth; success and error responses retain origin',async()=>{
 for(const origin of origins)for(const status of [200,401,403,503]){
  let calls=0;
  const handle=createHandler({authorize:async()=>{if(status===403)throw Object.assign(Error(),{status});return status!==401},actor:async()=>assert.fail(),rest:async()=>{calls++;if(status===503)throw Error('private detail');return []}});
  const res=await handle(req(origin));assert.equal(res.status,status);assert.equal(res.headers.get('access-control-allow-origin'),origin);assert.equal(res.headers.get('vary'),'Origin');assert.equal(res.headers.get('cache-control'),'no-store');if(status===401||status===403)assert.equal(calls,0);assert.doesNotMatch(await res.text(),/private detail/);
 }
});
test('requests without Origin still require authorization and do not advertise browser access',async()=>{
 const handle=createHandler({authorize:async()=>false,actor:async()=>assert.fail(),rest:async()=>assert.fail()});
 const res=await handle(req(undefined));assert.equal(res.status,401);assert.equal(res.headers.get('access-control-allow-origin'),null);
});
