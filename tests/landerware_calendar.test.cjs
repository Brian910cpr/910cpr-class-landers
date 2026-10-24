const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {stripTypeScriptTypes}=require('node:module');
const source=fs.readFileSync(require('node:path').resolve(__dirname,'../supabase/functions/landerware-calendar/index.ts'),'utf8').replace(/^import .*;\r?\n/gm,'');
async function run({sessions,registrations=[],workspace=[],fail=false,token='test-token'}){
 let handler;const calls=[];
 const ctx=vm.createContext({Date,Set,Map,JSON,TextEncoder,URL,Response,encodeURIComponent,Deno:{env:{get:n=>({LANDERWARE_ICAL_TOKEN:'test-token',SUPABASE_SERVICE_ROLE_KEY:'test-key',SUPABASE_URL:'https://db.test'})[n]},serve:fn=>handler=fn},fetch:async url=>{
  const u=new URL(url),table=u.pathname.split('/').at(-1),p=u.searchParams;calls.push(table);
  if(table==='landerware_sessions')return Response.json(sessions);
  if(fail)return new Response('',{status:503});
  const field=table==='registrations'?'class_session_id':'session_id';
  const ids=p.get(field).slice(4,-1).split(','),statuses=p.get('status').slice(4,-1).split(',');
  const rows=(table==='registrations'?registrations:workspace).filter(r=>ids.includes(r[field])&&statuses.includes(r.status)).sort((a,b)=>a.id.localeCompare(b.id));
  const offset=+p.get('offset');return Response.json(rows.slice(offset,offset + +p.get('limit')));
 }});
 vm.runInContext(stripTypeScriptTypes(source),ctx);
 const response=await handler(new Request('https://calendar.test/?token='+token));return {status:response.status,body:await response.text(),calls};
}
const session=(id,canonical)=>({id,class_session_id:canonical,starts_at:'2030-01-01T16:30:00Z',ends_at:'2030-01-01T18:30:00Z',lifecycle_state:'scheduled',course_name:'Example',instructor_name:'Instructor'});
test('reschedule counts canonical seat once and releases original, ignoring workspace mirrors',async()=>{
 const r=await run({sessions:[session('old','c-old'),session('new','c-new')],registrations:[{id:'r-old',class_session_id:'c-old',status:'rescheduled'},{id:'r-new',class_session_id:'c-new',status:'registered'}],workspace:[{id:'mirror',session_id:'new',status:'active'}]});
 assert.equal(r.status,200);const events=r.body.split('BEGIN:VEVENT').slice(1);assert.match(events[0],/Students: 0/);assert.match(events[1],/Students: 1/);assert.ok(!r.calls.includes('landerware_registrations'));
});
test('workspace-only sessions count active seats and exclude inactive states',async()=>{
 const r=await run({sessions:[session('w',null)],workspace:['active','registered','confirmed','completed','rescheduled','pending','cancelled'].map((status,i)=>({id:String(i),session_id:'w',status}))});assert.match(r.body,/Students: 4/);
});
test('registration pages are not truncated at the REST row limit',async()=>{
 const r=await run({sessions:[session('w','c')],registrations:Array.from({length:501},(_,i)=>({id:String(i).padStart(4,'0'),class_session_id:'c',status:'registered'}))});assert.match(r.body,/Students: 501/);
});
test('database failure never publishes a false zero',async()=>{const r=await run({sessions:[session('w','c')],fail:true});assert.equal(r.status,500);assert.doesNotMatch(r.body,/Students: 0/);});
test('private calendar token is still required',async()=>{const r=await run({sessions:[],token:'wrong'});assert.equal(r.status,404);assert.equal(r.calls.length,0);});
