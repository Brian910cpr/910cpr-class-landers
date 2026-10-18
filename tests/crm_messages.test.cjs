const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {stripTypeScriptTypes}=require('node:module');
const base='supabase/functions/canonical-session-workspace/';
function history(){const context=vm.createContext({URLSearchParams,Date,Error});vm.runInContext(stripTypeScriptTypes(fs.readFileSync(base+'messages.ts','utf8').replace('export async function','async function')),context);return context.messageHistory}
test('operational CRM filters never use legacy model foreign keys',async()=>{
 let path;const id='00000000-0000-4000-8000-000000000001';
 await history()(new URLSearchParams({customer_id:id,registration_id:id,status:'failed'}),async p=>{path=p;return []});
 assert.match(path,/&customer_id=eq\./);assert.match(path,/&operational_registration_id=eq\./);
 assert.doesNotMatch(path,/&person_id=|&registration_id=/);
});
test('invalid filters cannot be interpolated into PostgREST queries',async()=>{
 for(const values of [{customer_id:'x&select=*'},{registration_id:'invalid'},{status:'eq.pending&or=(true)'},{offset:'-1'},{offset:'1.5'},{offset:'10001'}]){
  let called=false;await assert.rejects(history()(new URLSearchParams(values),async()=>{called=true}),/invalid_message_filter/);assert.equal(called,false);
 }
});
test('history is bounded and pagination does not conceal more records',async()=>{
 let path;const result=await history()(new URLSearchParams({offset:'100'}),async p=>{path=p;return Array.from({length:101},(_,i)=>({id:i}))});
 assert.equal(result.messages.length,100);assert.equal(result.hasMore,true);assert.match(path,/limit=101&offset=100/);
});
test('owner authorization is checked before reading messages',async()=>{
 let handler,reads=0;const source=fs.readFileSync(base+'index.ts','utf8').replace(/^import .*;\r?\n/gm,'').replace(/^export /gm,'');
 const context=vm.createContext({URL,Date,Set,Response,Error,console,authorized:async()=>false,messageHistory:async()=>{reads++;return{}},Deno:{serve:fn=>handler=fn}});
 vm.runInContext(stripTypeScriptTypes(source),context);
 const response=await handler(new Request('https://example.test/?action=messages'));
 assert.equal(response.status,401);assert.equal(reads,0);
});
