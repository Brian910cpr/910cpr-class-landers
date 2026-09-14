import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {authorizedOwner} from '../supabase/functions/_shared/owner-auth.ts';
const source=readFileSync(new URL('../docs/admin/admin-auth.js',import.meta.url),'utf8');
const endpoint='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/owner-dashboard';
const token='lw_s_'+'a'.repeat(64),nextToken='lw_s_'+'b'.repeat(64);
const session=(value=token,days=30)=>JSON.stringify({token:value,expiresAt:new Date(Date.now()+days*86400000).toISOString()});
function page(values=new Map([['landerwareOwnerSession',session()]]),fetcher=async()=>new Response('{}')){
 const events=new EventTarget(),legacy=new Map(),redirects=[];
 const storage=map=>({getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,String(v)),removeItem:k=>map.delete(k)});
 const context={location:{href:'https://www.910cpr.com/admin/now.html',pathname:'/admin/now.html',search:'',replace:url=>redirects.push(url)},localStorage:storage(values),sessionStorage:storage(legacy),fetch:fetcher,URL,Headers,AbortController,CustomEvent,Event};
 context.window=context;context.addEventListener=events.addEventListener.bind(events);context.dispatchEvent=events.dispatchEvent.bind(events);vm.runInNewContext(source,context);
 return {auth:context.LanderWareAdminAuth,values,legacy,events,redirects};
}
test('remembered session survives navigation and new tabs; owner credential goes only to owner API',async()=>{
 const first=page();const next=page(first.values,async(url,o)=>{assert.equal(o.headers.get('X-LanderWare-Owner-Session'),token);assert.equal(o.headers.get('X-Hot-Sync-Admin-Key'),null);assert.equal(o.headers.get('x-maxim-session'),null);return new Response('{}')});
 next.legacy.set('maximPortalSession','corporate-fixture');await next.auth.fetch(endpoint,{headers:{'x-maxim-session':'corporate-fixture','x-hot-sync-admin-key':token}});next.auth.clear();assert.equal(first.auth.get(),'');assert.equal(next.legacy.get('maximPortalSession'),'corporate-fixture');
});
test('missing and expired sessions redirect without requesting private data',async()=>{for(const map of [new Map(),new Map([['landerwareOwnerSession',session(token,-1)]])]){const p=page(map,()=>assert.fail('must not send'));await assert.rejects(p.auth.fetch(endpoint),{status:401});assert.match(p.redirects[0],/^\/admin\/access.html\?next=/)}});
test('credentials never go to unapproved URLs',async()=>{const p=page(undefined,()=>assert.fail('must not send'));for(const url of ['https://example.com/admin/hot-sync','https://schedule.910cpr.com.example.com/admin/hot-sync','https://schedule.910cpr.com/public','https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/maxim-portal'])await assert.rejects(p.auth.fetch(url),/restricted/)});
test('401 signs out, but service outages and operation denials preserve sign-in',async()=>{for(const status of [401,403,503]){const p=page(undefined,async()=>new Response('{}',{status}));if(status===401){await assert.rejects(p.auth.fetch(endpoint),{status});assert.equal(p.auth.get(),'')}else{assert.equal((await p.auth.fetch(endpoint)).status,status);assert.equal(p.auth.get(),token)}}});
test('an old denial cannot erase a replacement session',async()=>{let finish;const p=page(undefined,()=>new Promise(r=>finish=r));const request=p.auth.fetch(endpoint);await new Promise(r=>setImmediate(r));p.values.set('landerwareOwnerSession',session(nextToken));p.events.dispatchEvent(Object.assign(new Event('storage'),{key:'landerwareOwnerSession'}));finish(new Response('{}',{status:401}));await assert.rejects(request,{name:'AbortError'});assert.equal(p.auth.get(),nextToken)});
test('late response bodies cannot repopulate a signed-out page',async()=>{let finish;const response=new Response('{}');response.json=()=>new Promise(r=>finish=r);const p=page(undefined,async()=>response);const result=await p.auth.fetch(endpoint);const body=result.json();p.auth.clear();finish({private:'roster'});await assert.rejects(body,{name:'AbortError'})});
test('legacy Cloudflare failure does not clear a valid owner session or send it to Cloudflare',async()=>{const p=page(undefined,async(url,o)=>{assert.equal(o.headers.get('X-LanderWare-Owner-Session'),null);assert.equal(o.headers.get('X-Hot-Sync-Admin-Key'),'legacy-fixture');return new Response('{}',{status:401})});await assert.rejects(p.auth.fetch('https://schedule.910cpr.com/admin/hot-sync'),{status:503});p.legacy.set('hotSyncAdminKey','legacy-fixture');await assert.rejects(p.auth.fetch('https://schedule.910cpr.com/admin/hot-sync'),{status:503});assert.equal(p.auth.get(),token)});
test('valid sessions approaching expiry renew without a login prompt',async()=>{let calls=0;const p=page(new Map([['landerwareOwnerSession',session(token,2)]]),async(url)=>{calls++;return url.endsWith('/refresh')?Response.json({expiresAt:new Date(Date.now()+30*86400000).toISOString()}):new Response('{}')});await p.auth.fetch(endpoint);assert.equal(calls,2);assert.ok(Date.parse(JSON.parse(p.values.get('landerwareOwnerSession')).expiresAt)>Date.now()+29*86400000);assert.equal(p.redirects.length,0)});
test('back/forward cache discards private view and reloads without discarding session',()=>{const p=page();let locks=0,refreshes=0;p.auth.onLock(()=>locks++);p.events.addEventListener('admin-auth-refresh',()=>refreshes++);p.events.dispatchEvent(new Event('pagehide'));p.events.dispatchEvent(Object.assign(new Event('pageshow'),{persisted:true}));assert.equal(locks,1);assert.equal(refreshes,1);assert.equal(p.auth.get(),token)});
test('legacy automation auth stays closed to corporate sessions and handles upstream outages',async t=>{
 assert.equal(await authorizedOwner(new Request(endpoint,{headers:{'x-maxim-session':'fixture'}})),false);
 const req=new Request(endpoint,{headers:{'x-hot-sync-admin-key':'fixture',origin:'https://www.910cpr.com'}});
 for(const status of [200,401,403,503]){const mock=t.mock.method(globalThis,'fetch',async()=>new Response('{}',{status}));if(status===503)await assert.rejects(authorizedOwner(req),{status:503});else assert.equal(await authorizedOwner(req),status===200);mock.mock.restore()}
});
