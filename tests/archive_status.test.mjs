import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createGithubSource,validateCheckpoint,jobHealth,REPO,STATUS_PATH} from '../supabase/functions/archive-status/core.mjs';
import {createArchiveStatusHandler} from '../supabase/functions/archive-status/handler.mjs';
const fixture=JSON.parse(readFileSync('data/audit/issue229_archive_rebuild_status.json','utf8'));
const checkpoint=()=>structuredClone(fixture), token='lw_s_'+'a'.repeat(64), now=Date.parse(fixture.last_checkpoint_at)+600000;
const source={ref:'codex/issue-229-monitor-feed-r3',blob:'b'.repeat(40),fetched_at:new Date(now).toISOString()};
const req=(headers={},method='GET')=>new Request('https://service.example/functions/v1/archive-status',{method,headers:{origin:'https://www.910cpr.com','x-landerware-owner-session':token,...headers}});
const github=(value=fixture)=>Response.json({encoding:'base64',sha:'b'.repeat(40),content:Buffer.from(JSON.stringify(value)).toString('base64')});
test('real R3 feed preserves baseline, unknown eligibility/Google, and blocked job time',()=>{
 const s=validateCheckpoint(checkpoint());assert.equal(s.baseline.source_rows_recovered,26165);assert.equal(s.baseline.html_urls_recovered,26171);assert.equal(s.baseline.preliminary_candidates,23488);assert.equal(s.metrics.eligible_pages,null);assert.equal(s.gsc.indexed,null);assert.equal(jobHealth(s,now).state,'BLOCKED');assert.equal(jobHealth(s,now).checkpoint_age_seconds,600);
});
test('invalid/private/unexpected fields are rejected at every returned object boundary',()=>{
 for(const path of [[],['baseline'],['baseline','classification'],['metrics'],['provenance'],['provenance','sources',0],['gsc'],['events',0],['events',0,'metrics'],['evidence']]){
  const s=checkpoint();let target=s;for(const key of path)target=target[key];target.private_note='not for output';assert.throws(()=>validateCheckpoint(s),/invalid_checkpoint/);
 }
});
test('source partitions, unsafe counts, unapproved progress, and fabricated Google fail closed',()=>{
 const mutations=[s=>s.baseline.source_rows_recovered++,s=>s.baseline.preliminary_candidates++,s=>s.baseline.non_candidate_rows++,s=>s.metrics.pages_generated=1,s=>s.metrics.pages_published=1,s=>s.gsc.indexed=0,s=>s.revision=-1,s=>s.metrics.eligible_pages=true,s=>s.metrics.pages_generated=2**54,s=>s.phase='GENERATION',s=>s.provenance.commit=['a'.repeat(40)],s=>s.provenance.branch='https://evil.example',s=>s.events[0].metrics.pages_validated=1,s=>s.events[0].at='2026-02-31T00:00:00Z',s=>s.events[0].state='RUNNING'];
 for(const mutate of mutations){const s=checkpoint();mutate(s);assert.throws(()=>validateCheckpoint(s),/invalid_checkpoint/);}
});
test('job health reports stopped running checkpoints and future clocks without changing evidence',()=>{
 const s=checkpoint();s.state='RUNNING';s.blockers=[];s.events[0].state='RUNNING';validateCheckpoint(s);assert.equal(jobHealth(s,now).state,'STALLED');assert.equal(jobHealth(s,now-300000).state,'RUNNING');assert.equal(jobHealth(s,now-700000).state,'CLOCK_MISMATCH');assert.equal(s.last_checkpoint_at,fixture.last_checkpoint_at);
});
test('owner session required: anonymous, corporate and legacy headers never read source',async()=>{
 const h=createArchiveStatusHandler({lookupSession:()=>assert.fail('no lookup'),readStatus:()=>assert.fail('no source')});
 for(const headers of [{},{'x-maxim-session':'corporate'},{'x-hot-sync-admin-key':'legacy'},{'x-landerware-owner-session':'bad'}])assert.equal((await h(new Request('https://service.example',{headers}))).status,401);
});
test('origin/method restrictions and credential-free preflight',async()=>{
 const h=createArchiveStatusHandler({lookupSession:()=>assert.fail('no lookup'),readStatus:()=>assert.fail('no source')});
 assert.equal((await h(req({origin:'https://evil.example'}))).status,403);assert.equal((await h(req({},'POST'))).status,405);
 const r=await h(req({},'OPTIONS'));assert.equal(r.status,204);assert.equal(r.headers.get('access-control-allow-origin'),'https://www.910cpr.com');assert.equal(r.headers.get('access-control-allow-headers'),'x-landerware-owner-session');assert.match(r.headers.get('cache-control'),/no-store/);
});
test('valid owner receives only validated checkpoint; lookup repeated after source read',async()=>{
 let lookups=0;const h=createArchiveStatusHandler({lookupSession:async t=>{assert.equal(t,token);lookups++;return {id:'owner'};},readStatus:async()=>({checkpoint:checkpoint(),source}),now:()=>now});
 const r=await h(req());assert.equal(r.status,200);assert.equal(lookups,2);assert.match(r.headers.get('cache-control'),/private, no-store/);const payload=await r.json();assert.equal(payload.job_health.state,'BLOCKED');assert.equal(payload.checkpoint.last_checkpoint_at,fixture.last_checkpoint_at);assert.equal(payload.observed_at,new Date(now).toISOString());assert.doesNotMatch(JSON.stringify(payload),new RegExp(token));
});
test('revoked sessions denied before fetch or after in-flight read without cached authority',async()=>{
 for(const before of [true,false]){let calls=0,reads=0;const h=createArchiveStatusHandler({lookupSession:async()=>++calls===1&&!before,readStatus:async()=>{reads++;return {checkpoint:checkpoint(),source};}});assert.equal((await h(req())).status,401);assert.equal(reads,before?0:1);}
});
test('auth, source and schema failures are sanitized and never return old data',async()=>{
 for(const fault of ['auth','source','schema']){const h=createArchiveStatusHandler({lookupSession:async()=>{if(fault==='auth')throw Error('private credential');return true;},readStatus:async()=>{if(fault==='source')throw Error('private source');const s=checkpoint();s.private='private record';return {checkpoint:s,source};}});const r=await h(req());assert.equal(r.status,503);assert.doesNotMatch(await r.text(),/private|26165|checkpoint/);}
});
test('source rejects arbitrary refs and missing server credential before network calls',async()=>{
 for(const sourceRef of ['https://evil.example','../../main','main?secret=x'])assert.throws(()=>createGithubSource({sourceRef}),/invalid_checkpoint/);
 await assert.rejects(createGithubSource({send:()=>assert.fail('no request')})(),/status_source_unconfigured/);
});
test('source uses fixed GitHub path, deduplicates polls, and expires cache after 10 seconds',async()=>{
 let reads=0,time=now,finish;const reader=createGithubSource({token:'server-fixture',sourceRef:source.ref,now:()=>time,send:async(url,options)=>{reads++;assert.equal(url,`https://api.github.com/repos/${REPO}/contents/${STATUS_PATH}?ref=codex%2Fissue-229-monitor-feed-r3`);assert.equal(options.headers.Authorization,'Bearer server-fixture');assert.equal(options.redirect,'error');if(reads===1)await new Promise(r=>finish=r);return github();}});
 const first=reader(),second=reader();await new Promise(r=>setImmediate(r));assert.equal(reads,1);finish();const [a,b]=await Promise.all([first,second]);assert.deepEqual(a,b);a.checkpoint.baseline.source_rows_recovered=0;assert.equal((await reader()).checkpoint.baseline.source_rows_recovered,26165);assert.equal(reads,1);time+=10000;await reader();assert.equal(reads,2);
});
test('expired successful cache does not conceal upstream failure or malformed content',async()=>{
 let time=now,send=()=>github();const reader=createGithubSource({token:'server-fixture',now:()=>time,send:async()=>send()});await reader();time+=11000;send=()=>Response.json({error:'private'},{status:500});await assert.rejects(reader(),/status_source_unavailable/);send=()=>github({...fixture,private:'hidden'});await assert.rejects(reader(),/invalid_checkpoint/);send=()=>github();assert.equal((await reader()).checkpoint.issue,229);
});
test('shared browser helper allows this service and strips legacy/corporate credentials',async()=>{
 const src=readFileSync('docs/admin/admin-auth.js','utf8');const vm=await import('node:vm');const values=new Map([['landerwareOwnerSession',JSON.stringify({token,expiresAt:new Date(Date.now()+30*86400000).toISOString()})]]);
 const store={getItem:k=>values.get(k)||null,removeItem:k=>values.delete(k),setItem:(k,v)=>values.set(k,v)};let sent=false;
 const context={Headers,URL,AbortController,Event,CustomEvent,location:{href:'https://www.910cpr.com/admin/archive-rebuild.html',pathname:'/admin/archive-rebuild.html',search:'',replace:()=>assert.fail('unexpected redirect')},localStorage:store,sessionStorage:{getItem:()=>null,removeItem(){}},fetch:async(url,o)=>{sent=true;assert.match(url,/\/archive-status$/);assert.equal(o.headers.get('x-landerware-owner-session'),token);assert.equal(o.headers.get('x-hot-sync-admin-key'),null);assert.equal(o.headers.get('x-maxim-session'),null);return Response.json({});},addEventListener(){},dispatchEvent(){}};context.window=context;vm.runInNewContext(src,context);
 await context.LanderWareAdminAuth.fetch('https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/archive-status',{headers:{'x-hot-sync-admin-key':'legacy','x-maxim-session':'corporate'}});assert.ok(sent);
});
test('production entry point wires the session-only handler without anonymous database/source reads',async()=>{
 const original=globalThis.Deno;let handler;
 globalThis.Deno={env:{get:()=>undefined},serve:h=>handler=h};
 try{await import('../supabase/functions/archive-status/index.ts');assert.equal(typeof handler,'function');assert.equal((await handler(new Request('https://service.example'))).status,401);}
 finally{if(original===undefined)delete globalThis.Deno;else globalThis.Deno=original;}
});
