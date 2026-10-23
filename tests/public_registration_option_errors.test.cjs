const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {stripTypeScriptTypes}=require('node:module');
const source=fs.readFileSync(path.join(__dirname,'../supabase/functions/public-registration/index.ts'),'utf8');
const entry=source.slice(source.lastIndexOf('Deno.serve('));
for(const error of ['physical_manual_unavailable','duplicate_addon','invalid_addon_quantity','invalid_addon_price']){
 test(`${error} is a validation response, not a server failure`,async()=>{
   let handler;
   const context=vm.createContext({URL,Response,Error,Set,
     ALLOWED:new Set(['https://www.910cpr.com']),
     scheduleSession:async()=>{throw new Error(error)},
     json:(_origin,payload,status=200)=>new Response(JSON.stringify(payload),{status}),
     Deno:{serve:fn=>{handler=fn}}
   });
   vm.runInContext(stripTypeScriptTypes(entry),context);
   const response=await handler(new Request('https://local.test/public-registration/session/synthetic'));
   assert.equal(response.status,400);
   assert.deepEqual(await response.json(),{error});
 });
}
test('asynchronous checkout failures retain current-main validation and date closure responses',async()=>{
 for(const [error,status] of [['invalid_addon',400],['registration_date_closed',409]]){
  let handler;
  const context=vm.createContext({URL,Response,Error,Set,ALLOWED:new Set(['https://www.910cpr.com']),
    start:async()=>{await Promise.resolve();throw new Error(error)},
    json:(_origin,payload,status=200)=>new Response(JSON.stringify(payload),{status}),Deno:{serve:fn=>{handler=fn}}});
  vm.runInContext(stripTypeScriptTypes(entry),context);
  const response=await handler(new Request('https://local.test/public-registration/start',{method:'POST'}));
  assert.equal(response.status,status);assert.deepEqual(await response.json(),{error});
 }
});

test('unverified mixed-source class retains its published legacy booking route',async()=>{
 const context=vm.createContext({URL,URLSearchParams,Request,Response,Date,Error,Set,console,
   Deno:{env:{get:k=>({SUPABASE_URL:'https://fixture-db.test',SUPABASE_SERVICE_ROLE_KEY:'fixture-only'})[k]},serve:()=>{}},
   fetch:async url=>{
    const value=String(url);
    if(value.includes('assert_public_registration_open'))return Response.json(true);
    if(value.includes('landerware_public_seat_state'))return Response.json({message:'external_reconciliation_required'},{status:400});
    if(value.includes('/class_sessions?'))return Response.json([{id:'fixture',registration_backend:'landerware',registration_status:'open',visibility:'public',status:'scheduled',start_at:new Date(Date.now()+86400000).toISOString(),courses:{enrollware_course_id:'209806'}}]);
    if(value.endsWith('/data/schedule_future.json'))return Response.json({sessions:[{session_id:'123456',public_direct_booking:true,registration_status:'open',registration_url:'https://coastalcprtraining.enrollware.com/enroll?id=123456'}]});
    throw Error('unexpected_fixture_request');
   }});
 vm.runInContext(stripTypeScriptTypes(source.replace(/^import .*;\r?\n/gm,'')),context);
 const session=await context.scheduleSession('123456');
 assert.equal(session.nativeReady,false);assert.equal(session.registration_url,'https://coastalcprtraining.enrollware.com/enroll?id=123456');
});
