const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {stripTypeScriptTypes}=require('node:module');
const source=fs.readFileSync('supabase/functions/public-registration/index.ts','utf8');
function setup({booking=true,native=true,closed=false,course='351632'}={}){
 const calls=[];const start=new Date(Date.now()+172800000).toISOString(),end=new Date(Date.now()+180000000).toISOString();
 const row={id:'canonical',external_class_id:'123456',external_course_id:course,course_id:'0689a2c5-c507-4e8a-b94c-15e5c5689e28',lead_instructor_id:'instructor',location_id:'location',resource_id:null,organization_id:null,record_scope:'operational',registration_backend:'landerware',registration_status:closed?'closed':'open',visibility:'public',status:'scheduled',start_at:start,end_at:end,consumption_start_at:start,consumption_end_at:end,courses:{enrollware_course_id:course,name:'Pediatric'},locations:{name:'Synthetic'}};
 const context=vm.createContext({AbortSignal,genericCheckout:()=>({}),URL,URLSearchParams,Request,Response,Date,Error,Set,console,
 Deno:{env:{get:k=>({SUPABASE_URL:'https://fixture-db.test',SUPABASE_SERVICE_ROLE_KEY:'fixture-only'})[k]},serve(){}},
 fetch:async(url,init)=>{calls.push(String(url));if(String(url).includes('/class_sessions?'))return Response.json(native?[row]:[]);
 if(String(url).includes('/rpc/native_scheduling_seat_snapshot'))return Response.json({sessionStatus:row.status,registrationStatus:row.registration_status,visibility:row.visibility,sessionIdentity:[row.course_id,start,end,start,end,'instructor','location',null,null,'123456','operational'],pediatricBooking:booking?{schemaVersion:'native-pediatric-session-booking.v1',publicCourseId:'351632',canonicalCourseId:row.course_id,sourceSessionId:'123456',packageCode:'full-course',profileKey:'native_heartsaver_351632_draft',coursePolicyKey:'heartsaver-pediatric-existing:351632.v1',remaining:2}:null});
 if(String(url).includes('/rpc/'))return Response.json({remaining:2});
 if(String(url).endsWith('/data/schedule_future.json'))return Response.json({sessions:[{session_id:'123456',course_id:'351632',public_direct_booking:true,registration_status:'open',registration_url:'https://retired.invalid/'}]});
 throw Error('unexpected_request');}});
 vm.runInContext(stripTypeScriptTypes(source.replace(/^import .*;\r?\n/gm,'')),context);return {context,calls};
}
test('existing session discovery requires fresh protected pediatric snapshot',async()=>{
 const good=setup();assert.equal((await good.context.scheduleSession('123456')).nativeReady,true);assert.ok(good.calls.some(x=>x.includes('native_scheduling_seat_snapshot')));
 for(const options of [{booking:false},{closed:true},{native:false},{course:'251545'}]){const s=setup(options);await assert.rejects(s.context.scheduleSession('123456'),/native_registration_unavailable/);}
});
test('saved recovery call does not acquire new pediatric admission',async()=>{const s=setup({booking:false});assert.equal((await s.context.scheduleSession('123456',false)).nativeReady,true);assert.ok(!s.calls.some(x=>x.includes('native_scheduling_seat_snapshot')));});
const {loadEndpoint}=require('./helpers/canonical_demand_endpoint.cjs');
test('ordinary demand does not fetch pediatric policy; explicit missing policy fails closed',async()=>{
 let calls=0;const a=loadEndpoint(async url=>{if(String(url).includes('native_pediatric_existing_session_runtime_policy')){calls++;return Response.json(null);}if(String(url).includes('enrollware_reconciliation_health'))return Response.json({sessions:[]});return Response.json(String(url).includes('/class_sessions')?[]:{});});
 const req=q=>new Request('https://endpoint.test/?from=2030-01-01&to=2030-01-02'+q,{headers:{'x-hot-sync-admin-key':'synthetic'}});
 assert.equal((await a.handleRequest(req(''))).status,200);assert.equal(calls,0);
 assert.equal((await a.handleRequest(req('&native_pediatric=0'))).status,400);
 assert.equal((await a.handleRequest(req('&native_pediatric=1&native_pediatric=1'))).status,400);
 assert.equal((await a.handleRequest(req('&native_pediatric=1'))).status,500);assert.equal(calls,1);
});
