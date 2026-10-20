import test from 'node:test';
import assert from 'node:assert/strict';
globalThis.Deno={env:{get:name=>({SUPABASE_URL:'https://database.invalid',SUPABASE_SERVICE_ROLE_KEY:'synthetic-service',RESEND_API_KEY:'synthetic-provider'}[name])}};
const {deliverConfirmations}=await import('../supabase/functions/registration-reschedule/index.ts');
const message={id:'11111111-1111-4111-8111-111111111111',recipient:'synthetic@example.invalid',subject:'Synthetic',body:'Synthetic body'};
async function scenario(provider,failMessage=false){
 const original=globalThis.fetch,originalLog=console.error,calls=[],logs=[];console.error=x=>logs.push(x);
 globalThis.fetch=async(url,init={})=>{calls.push({url:String(url),init});if(String(url).endsWith('/claim_reschedule_confirmations'))return Response.json([message]);if(String(url)==='https://api.resend.com/emails')return provider();if(failMessage&&String(url).includes('/landerware_messages?'))return Response.json({error:'private database detail'},{status:503});return Response.json([]);};
 try{return {result:await deliverConfirmations(),calls,logs};}finally{globalThis.fetch=original;console.error=originalLog;}
}
const queued=x=>x.calls.filter(c=>c.url.includes('registration_reschedule_deliveries?')).map(c=>JSON.parse(c.init.body));
test('provider status and safe category persist without raw error text or recipient',async()=>{
 const r=await scenario(()=>Response.json({name:'validation_error',message:'private sender credentials and recipient'},{status:403}));assert.equal(r.result.failed,1);assert.equal(queued(r)[0].last_error,'provider_http_403:validation_error');assert.ok(!r.calls.some(c=>c.url.includes('/landerware_messages?')));assert.ok(!r.logs.join('').includes('private'));assert.ok(!r.logs.join('').includes(message.recipient));
});
test('unrecognized error names and non-JSON rejection stay bounded and private',async()=>{
 for(const response of [()=>Response.json({name:'secret-value-not-an-error-code'},{status:401}),()=>new Response('private HTML',{status:502})]){const r=await scenario(response);assert.match(queued(r)[0].last_error,/^provider_http_(401|502):unclassified$/);assert.ok(!r.logs.join('').includes('private'));}
});
test('request timeout is distinguished from provider rejection',async()=>{
 const r=await scenario(()=>{throw Object.assign(Error('private connection detail'),{name:'TimeoutError'});});assert.equal(queued(r)[0].last_error,'provider_request_timeout');
});
test('database failure after provider acceptance is explicitly ambiguous and retry keeps exact provider key/payload',async()=>{
 const accepted=()=>Response.json({id:'synthetic-provider-message'});const first=await scenario(accepted,true),retry=await scenario(accepted);
 assert.equal(queued(first)[0].last_error,'message_record_failed');assert.equal(retry.result.sent,1);
 const a=first.calls.find(c=>c.url==='https://api.resend.com/emails'),b=retry.calls.find(c=>c.url==='https://api.resend.com/emails');assert.equal(a.init.headers['idempotency-key'],'reschedule-'+message.id);assert.equal(a.init.headers['idempotency-key'],b.init.headers['idempotency-key']);assert.equal(a.init.body,b.init.body);
});
test('provider accepted success records sent state and provider ID',async()=>{
 const r=await scenario(()=>Response.json({id:'synthetic-provider-message'}));assert.deepEqual(r.result,{configured:true,sent:1,failed:0});assert.deepEqual(queued(r),[{status:'sent',last_error:null}]);assert.deepEqual(r.logs,[]);
});
