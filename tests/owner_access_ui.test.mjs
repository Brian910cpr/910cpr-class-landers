import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const source=readFileSync('docs/admin/owner-access.js','utf8');
const access='lw_p_'+'a'.repeat(64),token='lw_s_'+'b'.repeat(64),session={token,expiresAt:new Date(Date.now()+30*86400000).toISOString()};
const tick=()=>new Promise(r=>setImmediate(r));
function setup({hash='#access='+access,next='',data=session,status=200,saved=null}={}){
 const values=new Map(),events=[],elements=new Map(['status','help','retry'].map(id=>[id,{hidden:false,textContent:'',addEventListener(){}}]));if(saved)values.set('landerwareOwnerSession',JSON.stringify(saved));
 const storage={getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};
 const context={URLSearchParams,location:{hash,pathname:'/admin/access.html',search:next,replace:to=>events.push({type:'redirect',to})},history:{replaceState:(a,b,url)=>events.push({type:'clean-url',url})},document:{getElementById:id=>elements.get(id)},localStorage:storage,sessionStorage:{getItem:()=>null,removeItem(){}},fetch:async(url,o)=>{events.push({type:'request',url,options:o});return Response.json(data,{status})}};
 vm.runInNewContext(source,context);return {values,events,elements};
}
test('private access link removes credential from history, signs in, remembers browser, and opens Class History',async()=>{const p=setup();await tick();assert.equal(p.events[0].type,'clean-url');assert.equal(p.events[0].url,'/admin/access.html');assert.equal(JSON.parse(p.values.get('landerwareOwnerSession')).token,token);assert.equal(p.events.at(-1).to,'/admin/instructor-workbench.html');assert.equal(p.events[1].options.referrerPolicy,'no-referrer')});
test('an external return destination cannot receive the session',async()=>{const p=setup({next:'?next=https%3A%2F%2Fevil.example'});await tick();assert.equal(p.events.at(-1).to,'/admin/instructor-workbench.html')});
test('remembered access verifies the session and opens the requested admin page',async()=>{const p=setup({hash:'',next:'?next=%2Fadmin%2Fclass-registry.html',saved:session});await tick();assert.ok(p.events.some(e=>e.url?.endsWith('/session')));assert.equal(p.events.at(-1).to,'/admin/class-registry.html')});
test('missing link offers the existing email entry without exposing credentials or requiring a password',async()=>{const p=setup({hash:''});await tick();assert.equal(p.events.filter(e=>e.type==='request').length,0);assert.equal(p.elements.get('help').hidden,false);assert.match(p.elements.get('status').textContent,/private access link/)});
test('failed exchange preserves retry and never stores a rejected session',async()=>{const p=setup({status:401,data:{error:'This access link is invalid or has expired.'}});await tick();assert.equal(p.values.has('landerwareOwnerSession'),false);assert.equal(p.elements.get('retry').hidden,false);assert.match(p.elements.get('status').textContent,/invalid or has expired/)});
