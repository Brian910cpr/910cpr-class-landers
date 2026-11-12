import test from 'node:test';
import assert from 'node:assert/strict';
import {dispatchNativeLearnerCodes} from '../supabase/functions/_shared/native-learner-code-consumer.mjs';
import {nativeLearnerCodeService} from '../supabase/functions/_shared/native-learner-code-service.mjs';
import {sendNativeLearnerCode} from '../supabase/functions/_shared/native-resend-adapter.mjs';
const id='123e4567-e89b-42d3-a456-426614174000',lease='123e4567-e89b-42d3-a456-426614174001';
const prepared={recipient:'synthetic@example.invalid',product:'HeartCode BLS',code:'SYNTHETIC-PRIVATE-CODE'};
const options={apiKey:'SYNTHETIC-NOT-CREDENTIAL',from:'sender@example.invalid',replyTo:'reply@example.invalid'};
const job={deliveryId:id,lease};
const safe=value=>{const text=JSON.stringify(value);for(const val of Object.values(prepared))assert.equal(text.includes(val),false);};
function consumer(patch={}){let claims=0;return {claim:async()=>claims++?{empty:true}:job,prepare:async()=>prepared,send:async()=>({outcome:'sent',providerId:'synthetic-receipt'}),settle:async()=>({settled:true}),...patch};}

test('code adapter uses exact private recipient, fixed text, distinct stable idempotency and no arbitrary fields',async()=>{
 const calls=[];const request=async(...args)=>(calls.push(args),Response.json({id:'synthetic-receipt'}));
 const input={...prepared,...job,subject:'ignored',html:'ignored',to:'attacker@example.invalid'};
 const result=await sendNativeLearnerCode(input,{...options,request});safe(result);assert.equal(result.outcome,'sent');
 await sendNativeLearnerCode({...input,lease:'changed'}, {...options,request});
 for(const [url,req] of calls){assert.equal(url,'https://api.resend.com/emails');assert.equal(req.headers['idempotency-key'],`native-learner-code-${id}`);const body=JSON.parse(req.body);assert.deepEqual(body.to,[prepared.recipient]);assert.ok(body.text.includes(prepared.code));assert.equal(body.html,undefined);assert.equal(body.subject,'Your purchased online course access');}
});

test('code adapter rejects invalid code, header injection, recipient lists and missing configuration without network',async()=>{
 let sent=0;const request=async()=>{sent++;throw Error('unexpected');};
 for(const patch of [{code:''},{code:'x\nBCC:y'},{code:'x'.repeat(8193)},{product:'bad\nproduct'},{deliveryId:'bad'},{recipient:'a@example.invalid,b@example.invalid'}])assert.equal((await sendNativeLearnerCode({...prepared,...job,...patch},{...options,request})).outcome,'rejected');
 assert.equal((await sendNativeLearnerCode({...prepared,...job},{...options,apiKey:'',request})).outcome,'rejected');assert.equal(sent,0);
});

test('provider uncertainty and ordinary rejection remain distinct with sanitized output',async()=>{
 for(const [status,expected] of [[429,'rejected'],[401,'rejected'],[408,'ambiguous'],[409,'ambiguous'],[500,'ambiguous']]){
  const result=await sendNativeLearnerCode({...prepared,...job},{...options,request:async()=>new Response(prepared.code,{status})});assert.equal(result.outcome,expected);safe(result);
 }
 for(const request of [async()=>{throw Error(prepared.code);},async()=>Response.json({}),async()=>new Response('{')]){const result=await sendNativeLearnerCode({...prepared,...job},{...options,request});assert.equal(result.outcome,'ambiguous');safe(result);}
});

test('consumer strictly orders claim/prepare/send/settle and counts without private data',async()=>{
 const sequence=[];let n=0;
 const result=await dispatchNativeLearnerCodes(consumer({claim:async()=>{sequence.push('claim');return n++?{empty:true}:job;},prepare:async args=>{sequence.push('prepare');assert.deepEqual(args,{p_delivery_id:id,p_lease:lease});return prepared;},send:async data=>{sequence.push('send');assert.deepEqual(data,{deliveryId:id,...prepared});return {outcome:'sent',providerId:'receipt'};},settle:async args=>{sequence.push('settle');assert.equal(args.p_outcome,'accepted');return {settled:true};}}));
 assert.deepEqual(sequence,['claim','prepare','send','settle','claim']);assert.equal(result.accepted,1);assert.equal(result.actualDeliveryConfirmed,false);safe(result);
});

test('blocked or uncertain prepare never sends; ambiguity stops after one send',async()=>{
 for(const [prepare,stop,blocked] of [[async()=>({blocked:true}),null,1],[async()=>{throw Error(prepared.code);},'prepare_unknown',0],[async()=>({code:prepared.code}),'prepare_invalid',0]]){
  let sends=0;const result=await dispatchNativeLearnerCodes(consumer({prepare,send:async()=>{sends++;}}));assert.equal(result.stopped,stop);assert.equal(result.blocked,blocked);assert.equal(sends,0);safe(result);
 }
 let sends=0;const result=await dispatchNativeLearnerCodes(consumer({claim:async()=>job,send:async()=>{sends++;return {outcome:'ambiguous',errorCode:prepared.code};}}));assert.equal(sends,1);assert.equal(result.stopped,'provider_ambiguous');assert.equal(result.ambiguous,1);safe(result);
});

test('unknown settlement retains only exact sanitized receipt and does not resend',async()=>{
 let sends=0;const result=await dispatchNativeLearnerCodes(consumer({send:async()=>{sends++;return {outcome:'sent',providerId:'receipt'};},settle:async()=>{throw Error(prepared.code);}}));
 assert.equal(sends,1);assert.equal(result.stopped,'settlement_unknown');assert.deepEqual(result.pendingSettlement,{p_delivery_id:id,p_lease:lease,p_outcome:'accepted',p_provider_id:'receipt',p_error:null});safe(result);
});

test('invalid claims, repeated IDs and limits stop or fail closed',async()=>{
 for(const limit of [0,11,NaN])await assert.rejects(dispatchNativeLearnerCodes({...consumer(),limit}),/invalid_configuration/);
 const bad=await dispatchNativeLearnerCodes(consumer({claim:async()=>({...job,lease:null})}));assert.equal(bad.stopped,'claim_invalid');
 const duplicate=await dispatchNativeLearnerCodes(consumer({claim:async()=>job}));assert.equal(duplicate.accepted,1);assert.equal(duplicate.stopped,'duplicate_claim');
 const limited=await dispatchNativeLearnerCodes({...consumer(),limit:1});assert.equal(limited.accepted,1);assert.equal(limited.limitReached,true);
});

function serviceFixture({rejectSettlement=0,disabled=false,config=true,providerStatus=200,tickFailure=false}={}) {
 const calls=[],reports=[];let sends=0,claims=0,settlements=0;
 const rpc=async(name,args)=>{
  calls.push({name,args});
  if(name==='native_learner_code_runtime_tick'){if(tickFailure)throw Error('private');return {recorded:true};}
  if(name==='native_claim_learner_code')return disabled?{disabled:true}:claims++?{empty:true}:job;
  if(name==='native_prepare_learner_code')return prepared;
  if(name==='native_settle_learner_code'){if(++settlements<=rejectSettlement)throw Error(prepared.code);return {settled:true};}
  return {};
 };
 const service=nativeLearnerCodeService({rpc,env:key=>key==='RESEND_API_KEY'&&config?options.apiKey:undefined,request:async()=>{sends++;return Response.json({id:'receipt'},{status:providerStatus});},report:r=>reports.push(r)});
 return {service,calls,reports,sends:()=>sends};
}

test('service retries only settlement and records independent trustworthy completion, never proof',async()=>{
 const f=serviceFixture({rejectSettlement:1});const result=await f.service.deliver();assert.equal(f.sends(),1);assert.equal(result.accepted,1);assert.equal(result.stopped,null);assert.equal('pendingSettlement' in result,false);safe(result);
 assert.equal(f.calls.filter(x=>x.name==='native_settle_learner_code').length,2);const ticks=f.calls.filter(x=>x.name==='native_learner_code_runtime_tick');assert.deepEqual(ticks.map(x=>x.args.p_phase),['poll','completed']);assert.ok(ticks.every(x=>!Object.hasOwn(x.args,'proven')));
});

test('unresolved settlement reports identifiers only and faults; disabled/unconfigured/tick failures never send',async()=>{
 const f=serviceFixture({rejectSettlement:2});const result=await f.service.deliver();assert.equal(result.stopped,'settlement_unknown');assert.equal(f.sends(),1);safe(result);safe(f.reports);assert.equal(f.reports.length,1);assert.equal(f.calls.at(-1).args.p_fault,true);assert.equal(f.calls.at(-1).args.p_phase,'poll');
 for(const options of [{disabled:true},{config:false},{tickFailure:true}]){const f=serviceFixture(options);const r=await f.service.deliver();assert.equal(f.sends(),0);assert.equal(f.calls.some(x=>x.args.p_phase==='completed'),false);safe(r);}
});
