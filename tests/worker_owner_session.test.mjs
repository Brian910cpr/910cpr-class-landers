import test from 'node:test';
import assert from 'node:assert/strict';
import {ownerAuthorization} from '../worker/owner-session-auth.js';
import finance from '../worker/finance-worker.js';
import {handleAdminApi} from '../worker/admin-api.js';
const token='lw_s_'+'a'.repeat(64);
const headers={'X-LanderWare-Owner-Session':token};
const request=(extra={})=>new Request('https://schedule.910cpr.com/admin/hot-sync',{headers:{Origin:'https://www.910cpr.com',...extra}});

test('valid owner sessions use only the pinned authority, no-store and redirect denial',async()=>{
 let calls=0;
 assert.equal(await ownerAuthorization(request(headers),{},async(url,options)=>{
  calls++;assert.equal(url,'https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/owner-access/session');
  assert.equal(options.method,'GET');assert.equal(options.cache,'no-store');assert.equal(options.redirect,'error');
  assert.deepEqual(options.headers,headers);assert.ok(options.signal instanceof AbortSignal);
  return Response.json({expiresAt:'2099-01-01',ownerEmail:'fixture@example.com'});
 }),200);assert.equal(calls,1);
});

test('revoked/expired session denial and authority outages never fall back to a valid automation key',async()=>{
 for(const [status,expected] of [[401,401],[403,401],[500,503],[503,503],[302,503],[204,503]]){
  assert.equal(await ownerAuthorization(request({...headers,'X-Hot-Sync-Admin-Key':'fixture'}),{HOT_SYNC_ADMIN_KEY:'fixture'},async()=>new Response(null,{status})),expected);
 }
 assert.equal(await ownerAuthorization(request(headers),{},async()=>{throw Error('private upstream detail')}),503);
});

test('malformed, corporate and absent credentials never call authority; automation remains independent',async()=>{
 const send=()=>assert.fail('unexpected authority request');
 for(const value of ['', 'bad', 'lw_p_'+'a'.repeat(64)])assert.equal(await ownerAuthorization(request({'X-LanderWare-Owner-Session':value}),{},send),401);
 assert.equal(await ownerAuthorization(request({'X-Maxim-Session':'fixture'}),{HOT_SYNC_ADMIN_KEY:'fixture'},send),401);
 assert.equal(await ownerAuthorization(request(),{},send),503);
 assert.equal(await ownerAuthorization(request({'X-Hot-Sync-Admin-Key':'fixture'}),{HOT_SYNC_ADMIN_KEY:'fixture'},send),200);
});

test('authority timeout aborts and fails closed',async()=>{
 const started=Date.now();
 assert.equal(await ownerAuthorization(request(headers),{},async(_,o)=>new Promise((resolve,reject)=>o.signal.addEventListener('abort',()=>reject(Error('timeout'))))),503);
 assert.ok(Date.now()-started<6500);
});

for(const [label,path,handler] of [
 ['Finance','/admin/finance/unknown',(r,e)=>finance.fetch(r,e)],
 ['Hot Sync','/admin/hot-sync',(r,e)=>handleAdminApi(r,e,new URL(r.url))],
 ['Inbox','/admin/inbox',(r,e)=>handleAdminApi(r,e,new URL(r.url))],
 ['Session Bundle','/admin/session-bundles/2026-10-12',(r,e)=>handleAdminApi(r,e,new URL(r.url))],
])test(`${label} checks session before protected dispatch, preserves CORS and outage semantics`,async t=>{
 let authorityStatus=401,calls=0;
 t.mock.method(globalThis,'fetch',async()=>{calls++;return new Response(null,{status:authorityStatus})});
 const r=()=>new Request('https://schedule.910cpr.com'+path,{headers:{Origin:'https://www.910cpr.com',...headers}});
 for(const [upstream,expected] of [[401,401],[503,503],[200,label==='Finance'?404:503]]){
  authorityStatus=upstream;const response=await handler(r(),{STRIPE_SECRET_KEY:'unused-fixture'});assert.equal(response.status,expected);
  assert.match(response.headers.get('cache-control'),/no-store/);assert.equal(response.headers.get('access-control-allow-origin'),'https://www.910cpr.com');
  assert.doesNotMatch(await response.text(),/private upstream detail|fixture@example.com/);
 }
 const before=calls;
 assert.equal((await handler(new Request(r(),{headers:{Origin:'https://evil.example',...headers}}),{})).status,403);assert.equal(calls,before);
 const preflight=await handler(new Request(r(),{method:'OPTIONS'}),{});assert.equal(preflight.status,204);assert.match(preflight.headers.get('access-control-allow-headers'),/X-LanderWare-Owner-Session/);assert.equal(calls,before);
});
