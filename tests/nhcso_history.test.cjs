const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const source=fs.readFileSync(path.join(root,'supabase/functions/nhcso-workspace/history.js'),'utf8');
const modulePromise=import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
test('history query scopes organization, provenance and historical records; stable bounded pages',async()=>{
  const {listHistoricalClasses}=await modulePromise;
  const calls=[]; const query={};
  for(const name of ['select','eq','order'])query[name]=(...args)=>{calls.push([name,...args]);return query};
  query.range=(...args)=>{calls.push(['range',...args]);return {data:[{id:'internal',external_class_id:'legacy',start_at:'2023-01-02T01:00:00Z',timezone:'America/New_York',courses:{name:'BLS'},source_location_label:'Room',source_instructor_label:'Trainer'}],count:81,error:null}};
  const result=await listHistoricalClasses({from:name=>{assert.equal(name,'class_sessions');return query}},40);
  assert.deepEqual(result.history,[['2023-01-01','20:00','legacy','BLS','Room','Trainer']]);
  assert.equal(result.next_offset,41);
  assert.ok(calls.some(x=>x[0]==='eq'&&x[1]==='organizations.organization_key'));
  assert.ok(calls.some(x=>x[1]==='source'&&x[2]==='enrollware_history'));
  assert.ok(calls.some(x=>x[1]==='record_scope'&&x[2]==='historical'));
  assert.deepEqual(calls.at(-1),['range',40,79]);
  assert.equal(calls.filter(x=>x[0]==='order').length,2);
  assert.ok(!calls[0][1].includes('students'));
});
test('invalid offsets never reach database; database errors are surfaced',async()=>{
  const {listHistoricalClasses}=await modulePromise;
  for(const offset of [-1,0.5,'0',100001])await assert.rejects(()=>listHistoricalClasses({from:()=>assert.fail()},offset),/Invalid history offset/);
  const query={select(){return this},eq(){return this},order(){return this},range(){return {error:new Error('offline')}}};
  await assert.rejects(()=>listHistoricalClasses({from:()=>query}),/offline/);
});
test('empty final page terminates pagination',async()=>{
  const {listHistoricalClasses}=await modulePromise;
  const query={select(){return this},eq(){return this},order(){return this},range(){return {data:[],count:0,error:null}}};
  assert.deepEqual(await listHistoricalClasses({from:()=>query}),{history:[],total:0,next_offset:null});
});
const html=fs.readFileSync(path.join(root,'docs/corp/nhcso/index.html'),'utf8');
test('history selection cannot change editable class state',()=>{
  const code=html.slice(html.indexOf('function showHistory(id)'),html.indexOf('async function refresh()'));
  let message='';
  vm.runInNewContext(code+';showHistory("old")',{history:[['2022-01-01','09:00','old','BLS','Room','Trainer']],fmtTime:x=>x,window:{alert:x=>message=x}});
  assert.match(message,/read-only/);assert.match(message,/Legacy #old/);
  assert.ok(!code.includes('clearForm('));assert.ok(!code.includes('api('));
});
test('history endpoint follows authorization and browser never scrapes public prototypes',()=>{
  const edge=fs.readFileSync(path.join(root,'supabase/functions/nhcso-workspace/index.ts'),'utf8');
  assert.ok(edge.indexOf('if (!access.ok)')<edge.indexOf('if (action === "list_history")'));
  assert.ok(!html.includes("fetch('/admin/nhcso-training-workspace"));
  assert.ok(!html.includes('Older imported history is not published'));
  const boot=html.slice(html.indexOf('async function bootAuth()'),html.indexOf("$('sendCode').onclick"));
  assert.ok(!boot.includes('await loadHistory()'));
});
test('all inline scripts parse',()=>{
  for(const match of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g))new vm.Script(match[1]);
});
