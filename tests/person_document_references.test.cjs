const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {stripTypeScriptTypes} = require('node:module');
const source = fs.readFileSync('supabase/functions/canonical-session-workspace/class-record.ts','utf8').replaceAll('export ', '');
const ctx = vm.createContext({});
vm.runInContext(stripTypeScriptTypes(source),ctx);
const project = vm.runInContext('personDocumentReferences',ctx);
const sid = n => `10000000-0000-4000-8000-${String(n).padStart(12,'0')}`;
test('empty person history never queries global documents',async()=>{
  assert.equal((await project([],()=>{throw Error('must not query')})).length,0);
});
test('duplicate registrations reference one canonical class without writes or storage URLs',async()=>{
  const calls=[],doc={id:sid(2),class_session_id:sid(1),file_name:'Original.pdf'};
  const rows=await project([{class_session_id:sid(1)},{class_session_id:sid(1)}],async(...args)=>{calls.push(args);return [doc]});
  assert.equal(rows[0],doc);assert.equal(calls.length,1);assert.equal(calls[0].length,1);
  assert.ok(calls[0][0].includes(`class_session_id=in.(${sid(1)})`));
  assert.ok(!/storage_path|storage_bucket/.test(calls[0][0]));
});
test('wrong or malicious session mapping fails before querying',async()=>{
  await assert.rejects(project([{class_session_id:'bad),id=neq.null'}],()=>{throw Error('queried')}),/not_found/);
});
test('large histories batch every class once',async()=>{
  const calls=[];
  await project(Array.from({length:101},(_,n)=>({class_session_id:sid(n+1)})),async q=>{calls.push(q);return []});
  assert.equal(calls.length,3);
  for(let n=1;n<=101;n++) assert.equal(calls.filter(q=>q.includes(sid(n))).length,1);
});
test('backend failure remains an error instead of false empty history',async()=>{
  await assert.rejects(project([{class_session_id:sid(1)}],async()=>{throw Error('database unavailable')}),/database unavailable/);
});
const uiSource=fs.readFileSync('docs/admin/person-record.js','utf8');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
test('Person Record renders only matching canonical references and escapes filenames on reload',async()=>{
  const elements=Object.fromEntries(['personName','personStatus','personFacts','personHistory'].map(id=>[id,{}]));
  let refresh;
  const body={person:{id:sid(3),first_name:'Test'},registrations:[{class_session_id:sid(1),status:'registered',class_sessions:{id:sid(1),start_at:'2026-10-04'}}],documents:[{id:sid(2),class_session_id:sid(1),file_name:'Packet <script>.pdf'},{id:sid(4),class_session_id:sid(9),file_name:'Other private class.pdf'}]};
  vm.runInNewContext(uiSource,{URLSearchParams,location:{search:`?id=${sid(3)}`},document:{getElementById:id=>elements[id]},LanderWareAdminAuth:{fetch:async()=>({ok:true,json:async()=>body})},window:{addEventListener:(_,fn)=>refresh=fn}});
  await tick();
  assert.ok(elements.personHistory.innerHTML.includes('Packet &lt;script&gt;.pdf'));
  assert.ok(!elements.personHistory.innerHTML.includes('Other private class'));
  assert.ok(elements.personHistory.innerHTML.includes(`session=${sid(1)}`));
  assert.ok(elements.personHistory.innerHTML.includes('no attendance or result implied'));
  body.documents=[];await refresh();
  assert.ok(elements.personHistory.innerHTML.includes('None recorded'));
  assert.ok(!elements.personHistory.innerHTML.includes('Packet'));
});
