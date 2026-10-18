const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {stripTypeScriptTypes}=require('node:module');
const source=fs.readFileSync(path.join(__dirname,'../supabase/functions/public-registration/index.ts'),'utf8');
const entry=source.slice(source.lastIndexOf('Deno.serve('));
for(const error of ['physical_manual_unavailable','duplicate_addon','invalid_addon_quantity']){
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
