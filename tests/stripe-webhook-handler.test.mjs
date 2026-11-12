import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {stripTypeScriptTypes} from 'node:module';
import {createHmac,webcrypto} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {nativeConfirmationService} from '../supabase/functions/_shared/native-confirmation-service.mjs';
import {nativeConfirmationPostcommit} from '../supabase/functions/_shared/native-confirmation-postcommit.mjs';
import {publicOrderVersion,settlePublicOrder} from '../supabase/functions/public-registration/public-order-routing.mjs';

const source=readFileSync(new URL('../supabase/functions/stripe-registration-webhook/index.ts',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'');
const NOW=1900000000,secret='synthetic-current-secret',rotatedSecret='synthetic-rotated-secret';
const id='11111111-1111-4111-8111-111111111111';
const forbid=()=>assert.fail('Unexpected network request; only injected synthetic transport is allowed');
globalThis.fetch=forbid;
function harness({course='209806',unknown='none',databaseSecret=secret,fallbackSecret}={}){
  const calls=[],reads=[],sequence=[],background=[],logs=[],outbound=[],transportFailures=[];
  let handler,clock=NOW,unknownOnce=unknown!=='none',receiptCommits=0,finalizationCommits=0,claimed=false;
  const order={id,status:'checkout_open',total:7500,currency:'usd',stripe_checkout_session_id:'cs_synthetic',
    checkout_runtime_version:'native-v1',registration_profile_snapshot:{},course_id:course};
  const db={from(table){
    reads.push(table);
    assert.ok(['landerware_integration_secrets','landerware_public_orders'].includes(table),'must not route to legacy mutations');
    const q={select:()=>q,eq:(key,value)=>{
      assert.equal(key,table==='landerware_integration_secrets'?'secret_key':'id');
      assert.equal(value,table==='landerware_integration_secrets'?'stripe_registration_webhook':id);
      return q;
    },maybeSingle:async()=>({data:table==='landerware_integration_secrets'?{secret_value:databaseSecret}:structuredClone(order)})};
    return q;
  },rpc:async(name,args)=>{
    calls.push({name,args});sequence.push(name);
    if(name==='native_checkout_record_payment'){
      if(!order.payment_evidence){receiptCommits++;order.payment_evidence=structuredClone(args.p_evidence);}
      else assert.deepEqual(JSON.parse(JSON.stringify(args.p_evidence)),order.payment_evidence);
      if(unknown==='receipt'&&unknownOnce){unknownOnce=false;throw Error('PRIVATE synthetic committed receipt response loss');}
      return {data:{recorded:true}};
    }
    if(name==='native_checkout_finalize_order'){
      assert.ok(order.payment_evidence,'finalization requires previously recorded evidence');
      if(order.status!=='paid'){finalizationCommits++;order.status='paid';}
      if(unknown==='finalize'&&unknownOnce){unknownOnce=false;throw Error('PRIVATE synthetic committed finalization response loss');}
      return {data:{status:'paid'}};
    }
    if(name==='native_checkout_claim_confirmation'){
      assert.equal(order.status,'paid');assert.equal(args.p_order_id,id);
      if(claimed)return {data:{empty:true}};
      claimed=true;
      return {data:{messageId:'22222222-2222-4222-8222-222222222222',lease:'33333333-3333-4333-8333-333333333333',
        recipient:'synthetic@example.invalid',customerTemplate:true,confirmation:{kind:'confirmation',firstName:'Synthetic',course:'Synthetic Course',
          courseId:course,startsAt:'2031-01-01T14:00:00Z',endsAt:'2031-01-01T16:00:00Z',venue:'Synthetic fixture',selectedOptions:[]}}};
    }
    if(name==='native_checkout_settle_confirmation'){
      assert.equal(args.p_outcome,'sent');assert.equal(args.p_provider_id,'synthetic-provider-receipt');
      return {data:{settled:true}};
    }
    assert.fail(`Unexpected RPC: ${name}`);
  }};
  const env={SUPABASE_URL:'https://fixture.invalid',SUPABASE_SERVICE_ROLE_KEY:'synthetic-db-only',STRIPE_EXPECTED_LIVEMODE:'true',
    RESEND_API_KEY:'synthetic-mail-only',RESEND_FROM_EMAIL:'Fixture <fixture@example.invalid>',STRIPE_WEBHOOK_SECRET:fallbackSecret};
  const context=vm.createContext({nativeConfirmationService,nativeConfirmationPostcommit,publicOrderVersion,settlePublicOrder,
    AbortSignal,TextEncoder,Request,Response,crypto:webcrypto,Date:class extends Date{static now(){return clock*1000;}},
    console:{error:value=>logs.push(value),log:forbid,warn:forbid},EdgeRuntime:{waitUntil:p=>background.push(p)},
    createClient:(url,key)=>{assert.equal(url,env.SUPABASE_URL);assert.equal(key,env.SUPABASE_SERVICE_ROLE_KEY);return db;},
    fetch:async(url,init)=>{
      try{
        assert.equal(url,'https://api.resend.com/emails');assert.equal(init.method,'POST');
        assert.equal(order.status,'paid');sequence.push('mock-provider');outbound.push(JSON.parse(init.body));
        assert.equal(outbound.at(-1).to[0],'synthetic@example.invalid');
        return Response.json({id:'synthetic-provider-receipt'});
      }catch(error){transportFailures.push(error);throw error;}
    },Deno:{serve:fn=>handler=fn,env:{get:key=>{assert.ok(Object.hasOwn(env,key),`Unexpected environment read: ${key}`);return env[key];}}}});
  vm.runInContext(stripTypeScriptTypes(source),context);
  const body=({changes={},eventChanges={}}={})=>JSON.stringify({id:'evt_synthetic',created:NOW-365*86400,
    type:'checkout.session.completed',livemode:true,data:{object:{id:'cs_synthetic',mode:'payment',payment_status:'paid',livemode:true,
      payment_intent:'pi_synthetic',amount_total:7500,currency:'usd',metadata:{landerware_order_id:id},...changes}},...eventChanges});
  const signature=(raw,timestamp=clock,keys=[secret])=>`t=${timestamp},${keys.map(key=>'v1='+createHmac('sha256',key).update(`${timestamp}.${raw}`).digest('hex')).join(',')}`;
  const send=async({raw=body(),timestamp=clock,keys=[secret],signedRaw=raw,header=signature(signedRaw,timestamp,keys),method='POST'}={})=>{
    const headers=header===null?{}:{'stripe-signature':header};
    return handler(new Request('https://fixture.invalid/webhook',{method,headers,...(method==='POST'?{body:raw}:{})}));
  };
  // Production code intentionally catches transport failures. Preserve mock
  // assertion failures outside that catch so an unexpected request fails tests.
  const drain=async()=>{await Promise.all(background);assert.deepEqual(transportFailures,[]);};
  return {send,body,signature,drain,advance:seconds=>clock+=seconds,order,calls,reads,sequence,background,logs,outbound,
    commits:()=>({receipt:receiptCommits,finalization:finalizationCommits})};
}

test('actual handler accepts rotation in either order before recording, finalizing and scheduling confirmation',async()=>{
  for(const keys of [[secret,rotatedSecret],[rotatedSecret,secret]]){
    const h=harness(),response=await h.send({keys});await h.drain();
    assert.equal(response.status,200);assert.equal((await response.json()).status,'paid');
    assert.deepEqual(h.calls.slice(0,2).map(call=>call.name),['native_checkout_record_payment','native_checkout_finalize_order']);
    assert.ok(h.sequence.indexOf('native_checkout_finalize_order')<h.sequence.indexOf('native_checkout_claim_confirmation'));
    assert.equal(h.outbound.length,1);assert.deepEqual(h.commits(),{receipt:1,finalization:1});
    assert.equal(h.logs.length,0);
  }
});

test('invalid signatures, malformed headers, stale/future delivery and raw-body changes stop before payment lookups',async()=>{
  const cases=[{timestamp:NOW-365*86400},{timestamp:NOW-301},{timestamp:NOW+301},{keys:['wrong-secret']},{header:null},
    {header:'malformed'},{header:`t=${NOW},v1=bad`},{header:`t=${NOW},v1=${'0'.repeat(64)}`}];
  for(const args of cases){
    const h=harness(),response=await h.send(args);await h.drain();
    assert.equal(response.status,400);assert.deepEqual(await response.json(),{ok:false,error:'Invalid signature'});
    assert.deepEqual(h.reads,['landerware_integration_secrets']);assert.equal(h.calls.length,0);
    assert.equal(h.background.length,0);assert.equal(h.outbound.length,0);assert.equal(h.logs.length,0);
  }
  for(const mutate of [raw=>raw+' ',raw=>JSON.stringify(JSON.parse(raw),null,2),raw=>raw.replace('7500','7501')]){
    const h=harness(),signedRaw=h.body();assert.equal((await h.send({signedRaw,raw:mutate(signedRaw)})).status,400);
    assert.equal(h.calls.length,0);
  }
  for(const suffix of [`,t=${NOW}`,',v1=malformed',',']){
    const h=harness();assert.equal((await h.send({header:h.signature(h.body())+suffix})).status,400);assert.equal(h.calls.length,0);
  }
});

test('actual handler accepts exact past/future tolerance boundaries and ignores old event-created timestamps',async()=>{
  for(const delta of [-300,300]){
    const h=harness();assert.equal((await h.send({timestamp:NOW+delta})).status,200);await h.drain();
    assert.deepEqual(h.commits(),{receipt:1,finalization:1});
  }
});

test('freshly signed retry of the same old event preserves idempotent receipt/finalization and does not resend',async()=>{
  const h=harness(),raw=h.body(),originalHeader=h.signature(raw);
  assert.equal((await h.send({raw,header:originalHeader})).status,200);await h.drain();
  h.advance(86400);
  assert.equal((await h.send({raw,header:originalHeader})).status,400);
  assert.equal((await h.send({raw})).status,200);await h.drain();
  assert.deepEqual(h.commits(),{receipt:1,finalization:1});assert.equal(h.outbound.length,1);
  assert.equal(h.calls.filter(call=>call.name==='native_checkout_record_payment').length,2);
  assert.equal(h.calls.filter(call=>call.name==='native_checkout_finalize_order').length,2);
});

test('ambiguous receipt/finalization commits stay retryable and only successful finalizer response starts confirmation',async()=>{
  for(const course of ['209806','359474','209809','344085','351632','509474','210549'])for(const unknown of ['receipt','finalize']){
    const h=harness({course,unknown}),raw=h.body();
    const failed=await h.send({raw});await h.drain();
    assert.equal(failed.status,500);assert.deepEqual(await failed.json(),{ok:false,error:'Public payment reconciliation failed'});
    assert.equal(h.order.payment_evidence.payment_status,'paid');assert.equal(h.background.length,0);assert.equal(h.outbound.length,0);
    assert.deepEqual(h.commits(),{receipt:1,finalization:unknown==='finalize'?1:0});
    h.advance(600);
    assert.equal((await h.send({raw})).status,200);await h.drain();
    assert.equal((await h.send({raw})).status,200);await h.drain();
    assert.deepEqual(h.commits(),{receipt:1,finalization:1});assert.equal(h.outbound.length,1);
    assert.ok(h.sequence.indexOf('native_checkout_finalize_order')<h.sequence.indexOf('native_checkout_claim_confirmation'));
    assert.doesNotMatch(h.logs.join(''),/PRIVATE|synthetic-current-secret|synthetic-mail-only|synthetic@example/);
  }
});

test('verified payment field mismatches still cannot record or finalize the native order',async()=>{
  for(const changes of [{amount_total:1},{currency:'eur'},{id:'cs_other'},{payment_intent:null},
    {payment_status:'unpaid'},{mode:'subscription'},{livemode:false}]){
    const h=harness();await h.send({raw:h.body({changes})});await h.drain();
    assert.equal(h.calls.length,0);assert.equal(h.background.length,0);assert.equal(h.outbound.length,0);
  }
  const h=harness();await h.send({raw:h.body({eventChanges:{livemode:false}})});assert.equal(h.calls.length,0);
});

test('secret source precedence, malformed JSON rejection and POST-only routing stay unchanged',async()=>{
  const dbWins=harness({fallbackSecret:rotatedSecret});assert.equal((await dbWins.send({keys:[rotatedSecret]})).status,400);
  const fallback=harness({databaseSecret:null,fallbackSecret:rotatedSecret});assert.equal((await fallback.send({keys:[rotatedSecret]})).status,200);await fallback.drain();
  const absent=harness({databaseSecret:null});assert.equal((await absent.send()).status,400);assert.equal(absent.calls.length,0);
  const invalidJson=harness();const response=await invalidJson.send({raw:'{invalid JSON'});
  assert.equal(response.status,400);assert.deepEqual(await response.json(),{ok:false,error:'Invalid JSON'});assert.equal(invalidJson.calls.length,0);
  const get=harness();assert.equal((await get.send({method:'GET'})).status,405);assert.equal(get.reads.length,0);
});
