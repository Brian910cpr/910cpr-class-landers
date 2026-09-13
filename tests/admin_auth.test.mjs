import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {authorizedOwner} from '../supabase/functions/_shared/owner-auth.ts';
const source = readFileSync(new URL('../docs/admin/admin-auth.js',import.meta.url),'utf8');
const endpoint = 'https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/owner-dashboard';
function page(values=new Map(), fetcher=async()=>new Response('{}')) {
  const events = new EventTarget();
  const context = {location:{href:'https://www.910cpr.com/admin/now.html'},sessionStorage:{getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,String(v)),removeItem:k=>values.delete(k)},fetch:fetcher,URL,Headers,AbortController,CustomEvent,Event,
    addEventListener:events.addEventListener.bind(events),dispatchEvent:events.dispatchEvent.bind(events)};
  context.window=context;
  vm.runInNewContext(source,context);
  return {auth:context.LanderWareAdminAuth,values,events};
}
test('same tab navigation reuses only the owner key and logout preserves corporate access and drafts',async()=>{
  const state=new Map([['maximPortalSession','corporate-fixture'],['hotSyncDrafts','draft-fixture']]);
  const first=page(state);first.auth.set('owner-fixture');
  const next=page(state,async(url,options)=>{assert.equal(options.headers.get('X-Hot-Sync-Admin-Key'),'owner-fixture');assert.equal(options.headers.get('x-maxim-session'),null);return new Response('{}');});
  await next.auth.fetch(endpoint,{headers:{'x-maxim-session':'corporate-fixture'}});
  next.auth.clear();assert.equal(first.auth.get(),'');assert.equal(state.get('maximPortalSession'),'corporate-fixture');assert.equal(state.get('hotSyncDrafts'),'draft-fixture');
});
test('corporate-only sessions cannot request an owner endpoint',async()=>{const p=page(new Map([['maximPortalSession','fixture']]),()=>assert.fail('must not send'));await assert.rejects(p.auth.fetch(endpoint),{status:401});});
test('credentials never go to unapproved URLs',async()=>{const p=page(undefined,()=>assert.fail('must not send'));p.auth.set('fixture');for(const url of ['https://example.com/admin/hot-sync','https://schedule.910cpr.com.example.com/admin/hot-sync','https://schedule.910cpr.com/public','https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/maxim-portal'])await assert.rejects(p.auth.fetch(url),/restricted/);});
test('401 and 403 clear current owner state; 503 preserves it',async()=>{for(const status of [401,403,503]){const p=page(undefined,async()=>new Response('{}',{status}));p.auth.set('fixture');let locks=0;p.auth.onLock(()=>locks++);if(status===503){assert.equal((await p.auth.fetch(endpoint)).status,503);assert.equal(p.auth.get(),'fixture');assert.equal(locks,0);}else{await assert.rejects(p.auth.fetch(endpoint),{status});assert.equal(p.auth.get(),'');assert.equal(locks,1);}}});
test('an old denial cannot erase a replacement credential',async()=>{let finish;const p=page(undefined,()=>new Promise(resolve=>finish=resolve));p.auth.set('first');const request=p.auth.fetch(endpoint);p.auth.set('second');finish(new Response('{}',{status:401}));await assert.rejects(request,{name:'AbortError'});assert.equal(p.auth.get(),'second');});
test('late response bodies cannot repopulate a locked page',async()=>{let finish;const response=new Response('{}');response.json=()=>new Promise(resolve=>finish=resolve);const p=page(undefined,async()=>response);p.auth.set('fixture');const result=await p.auth.fetch(endpoint);const body=result.json();p.auth.clear();finish({private:'roster'});await assert.rejects(body,{name:'AbortError'});});
test('back/forward cache clears private state and requests a fresh load',()=>{const p=page();p.auth.set('fixture');let locks=0,refreshes=0;p.auth.onLock(()=>locks++);p.events.addEventListener('admin-auth-refresh',()=>refreshes++);p.events.dispatchEvent(new Event('pagehide'));p.events.dispatchEvent(Object.assign(new Event('pageshow'),{persisted:true}));assert.equal(locks,2);assert.equal(refreshes,1);assert.equal(p.auth.get(),'fixture');});
test('server authority rejects corporate tokens and distinguishes outages from a rejected key',async t=>{
  assert.equal(await authorizedOwner(new Request(endpoint,{headers:{'x-maxim-session':'fixture'}})),false);
  const req=new Request(endpoint,{headers:{'x-hot-sync-admin-key':'fixture',origin:'https://www.910cpr.com'}});
  for(const status of [200,401,403,503]){const mock=t.mock.method(globalThis,'fetch',async(url,options)=>{assert.equal(url,'https://schedule.910cpr.com/admin/hot-sync');assert.equal(options.headers['x-hot-sync-admin-key'],'fixture');return new Response('{}',{status});});if(status===503)await assert.rejects(authorizedOwner(req),{status:503});else assert.equal(await authorizedOwner(req),status===200);mock.mock.restore();}
});
