import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {jobHealth} from '../supabase/functions/archive-status/core.mjs';
const html=readFileSync('docs/admin/archive-rebuild.html','utf8'),js=readFileSync('docs/admin/archive-rebuild.js','utf8');
const baseline=JSON.parse(readFileSync('data/audit/issue229_archive_rebuild_status.json','utf8'));
const tick=()=>new Promise(r=>setImmediate(r));
function payload(s=structuredClone(baseline)){return {checkpoint:s,source:{ref:'codex/issue-229-monitor-feed-r3',blob:'b'.repeat(40),fetched_at:new Date().toISOString()},observed_at:new Date().toISOString(),job_health:jobHealth(s)};}
class Element {
 constructor(tag='div'){this.tagName=tag;this.children=[];this.ownText='';this.hidden=false;this.listeners=new Map();this.attributes={};}
 set textContent(value){this.ownText=String(value);this.children=[];}
 get textContent(){return this.ownText+this.children.map(c=>c.textContent).join(' ');}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this.ownText='';this.children=[...children];}
 setAttribute(k,v){this.attributes[k]=v;}
 addEventListener(type,fn){this.listeners.set(type,fn);}
 fire(type){return this.listeners.get(type)?.();}
}
function page(send=async()=>Response.json(payload())) {
 const elements=new Map([...html.matchAll(/id="([^"]+)"/g)].map(m=>[m[1],new Element()]));elements.get('privateView').hidden=true;
 const docEvents=new Map(),events=new Map(),timers=new Map();let timerId=0,lockHandler,version=0,calls=0;
 const auth={snapshot:()=>({version}),current:s=>s.version===version,fetch:async(u,o)=>{calls++;return send(u,o);},onLock:fn=>lockHandler=fn,clear:()=>{version++;lockHandler();}};
 const document={hidden:false,getElementById:id=>{assert.ok(elements.has(id),id);return elements.get(id);},createElement:t=>new Element(t),addEventListener:(type,fn)=>docEvents.set(type,fn)};
 const context={document,location:{origin:'https://www.910cpr.com',pathname:'/admin/archive-rebuild.html'},navigator:{clipboard:{writeText:async()=>{}}},AbortController,LanderWareAdminAuth:auth,addEventListener:(type,fn)=>events.set(type,fn),setTimeout:(fn,ms)=>{timers.set(++timerId,{fn,ms});return timerId;},clearTimeout:id=>timers.delete(id)};context.window=context;vm.runInNewContext(js,context);
 return {elements,auth,document,events,timers,callCount:()=>calls,visible:()=>!elements.get('privateView').hidden,text:id=>elements.get(id).textContent,async runTimer(ms){const pair=[...timers].find(([,t])=>t.ms===ms);assert.ok(pair,`missing ${ms} timer`);timers.delete(pair[0]);pair[1].fn();await tick();},visibility(hidden){document.hidden=hidden;docEvents.get('visibilitychange')();},lock:()=>auth.clear(),resume:()=>events.get('admin-auth-refresh')()};
}
test('real page shell contains no operational counts, keeps details hidden, and versions its assets',()=>{
 assert.match(html,/id="privateView" hidden/);assert.match(html,/noindex,nofollow,noarchive/);assert.doesNotMatch(html,/26,?165|23,?488|lw_s_/);
 for(const path of ['admin-auth.js','archive-rebuild.js'])assert.ok(html.includes(`/admin/${path}?v=20260914-archive4`));
 assert.match(html,/page-id/);assert.match(html,/deployment-timestamp/);assert.match(html,/issues\/229/);assert.match(html,/pull\/230/);
});
test('renders actual R3 counts, blocked state, unknown denominator and Google without false progress',async()=>{
 const p=page();await tick();assert.ok(p.visible());assert.match(p.text('baseline'),/26,165/);assert.match(p.text('baseline'),/26,171/);assert.match(p.text('baseline'),/23,488/);assert.equal(p.text('jobState'),'Blocked');assert.match(p.text('eligibility'),/unresolved/);assert.equal(p.elements.get('progress').children.flatMap(c=>c.children).filter(c=>c.tagName==='progress').length,0);assert.match(p.text('google'),/Unknown/);assert.match(p.text('events'),/^Eligibility review · Blocked/);assert.match(p.text('provenance'),/PR #232/);
});
test('polling observes a changed checkpoint within 20 seconds and full eligible progress',async()=>{
 let value=payload();const p=page(async()=>Response.json(value));await tick();value=payload();const s=value.checkpoint;s.metrics={eligible_pages:100,pages_generated:40,pages_validated:30,pages_failed_validation:2,sitemap_urls_generated:30,pages_published:0};s.phase='VALIDATION';s.state='RUNNING';s.blockers=[];s.revision=1;s.events=[{phase:s.phase,state:s.state,at:s.last_checkpoint_at,revision:1,metrics:{...s.metrics}}];value.job_health={state:'STALLED',checkpoint_age_seconds:600};await p.runTimer(20000);
 assert.equal(p.callCount(),2);assert.equal(p.text('jobState'),'Checkpoint stalled');assert.match(p.text('eligibility'),/100 pages/);const bars=p.elements.get('progress').children.flatMap(c=>c.children).filter(c=>c.tagName==='progress');assert.equal(bars.length,5);assert.equal(bars[0].max,100);assert.equal(bars[0].value,40);
});
test('failed polling hides prior private counts and retries without pretending the job advanced',async()=>{
 let fail=false;const p=page(async()=>fail?Response.json({}, {status:503}):Response.json(payload()));await tick();assert.ok(p.visible());fail=true;await p.runTimer(20000);assert.equal(p.visible(),false);assert.equal(p.text('baseline'),'');assert.match(p.text('connection'),/unavailable/);assert.match(p.text('pollAge'),/Current counts are hidden/);fail=false;await p.runTimer(20000);assert.ok(p.visible());
});
test('sign-out clears rendered details and a late response cannot restore them',async()=>{
 let finish;const p=page(()=>new Promise(r=>finish=r));await tick();p.lock();finish(Response.json(payload()));await tick();assert.equal(p.visible(),false);assert.equal(p.text('provenance'),'');assert.equal(p.timers.size,0);assert.match(p.text('connection'),/Owner access changed/);
});
test('resume during pending response does not overlap and discards the obsolete response',async()=>{
 let finish;const p=page(()=>new Promise(r=>finish=r));await tick();p.resume();assert.equal(p.callCount(),1);finish(Response.json(payload()));await tick();assert.equal(p.visible(),false);await p.runTimer(0);assert.equal(p.callCount(),2);finish(Response.json(payload()));await tick();assert.ok(p.visible());
});
test('hidden tabs pause polling, clear content, and resume on visibility return',async()=>{
 const p=page();await tick();p.visibility(true);assert.equal(p.visible(),false);assert.equal(p.timers.size,0);p.visibility(false);await tick();assert.ok(p.visible());assert.equal(p.callCount(),2);
});
test('request timeout aborts and schedules a recoverable retry',async()=>{
 const p=page((url,{signal})=>new Promise((resolve,reject)=>signal.addEventListener('abort',()=>reject(Error('timeout')))));await tick();await p.runTimer(15000);assert.equal(p.visible(),false);assert.match(p.text('connection'),/Retrying/);assert.ok([...p.timers.values()].some(t=>t.ms===20000));
});
