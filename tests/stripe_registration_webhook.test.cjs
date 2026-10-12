const test = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {resolve} = require('node:path');
const {stripTypeScriptTypes} = require('node:module');
const {createHmac, webcrypto} = require('node:crypto');
const vm = require('node:vm');
const source = readFileSync(resolve(__dirname, '../supabase/functions/stripe-registration-webhook/index.ts'), 'utf8').replace(/^import .*;\r?\n/gm, '');
const secret = 'whsec_local_fixture_only';
function signature(raw, timestamp = Math.floor(Date.now()/1000)) {
  return `t=${timestamp},v1=${createHmac('sha256', secret).update(`${timestamp}.${raw}`).digest('hex')}`;
}
function runtime() {
  let handler; const calls=[];
  const db={from(){return {select(){return this},eq(){return this},async maybeSingle(){return {data:{secret_value:secret}}}}},async rpc(name,args){calls.push({name,args});return {data:{ok:true}}}};
  const context=vm.createContext({Date,TextEncoder,crypto:webcrypto,Response,JSON,Array,Number,Math,Set,createClient:()=>db,Deno:{env:{get:()=>''},serve(fn){handler=fn}}});
  vm.runInContext(stripTypeScriptTypes(source)+'\nthis.verifySignature=verify;',context);
  return {verify:context.verifySignature,calls,handler};
}
test('accepts an authentic signature and rejects altered raw bytes',async()=>{
  const r=runtime(),raw='{"id":"evt_local"}';
  assert.equal(await r.verify(raw,signature(raw),secret),true);
  assert.equal(await r.verify(raw+' ',signature(raw),secret),false);
});
test('rejects expired and future signatures even when correctly signed',async()=>{
  const r=runtime(),now=Math.floor(Date.now()/1000);
  for(const timestamp of [now-301,now+301])assert.equal(await r.verify('{}',signature('{}',timestamp),secret),false);
});
test('accepts a valid signature in either rotation position',async()=>{
  const r=runtime(),valid=signature('{}'),bad='0'.repeat(64);
  assert.equal(await r.verify('{}',`${valid},v1=${bad}`,secret),true);
  assert.equal(await r.verify('{}',valid.replace(',v1=',`,v1=${bad},v1=`),secret),true);
});
test('rejects missing, ambiguous and malformed signature headers',async()=>{
  const r=runtime();
  for(const header of [null,'',`t=invalid,v1=${'0'.repeat(64)}`,`${signature('{}')},t=123`,'t=123,v1=bad'])assert.equal(await r.verify('{}',header,secret),false);
  assert.equal(await r.verify('{}',signature('{}'),null),false);
});
async function deliver(r,type,payment_status){
  const raw=JSON.stringify({id:'evt_local',type,data:{object:{id:'cs_local',payment_status,metadata:{landerware_order_id:'local-order'},payment_intent:'pi_local'}}});
  return r.handler(new Request('https://local.test/webhook',{method:'POST',body:raw,headers:{'stripe-signature':signature(raw)}}));
}
test('unpaid asynchronous success cannot confirm a seat',async()=>{
  const r=runtime(),response=await deliver(r,'checkout.session.async_payment_succeeded','unpaid');
  assert.equal(response.status,200);assert.equal(r.calls.length,0);
});
test('paid supported events reach the existing reconciliation RPC',async()=>{
  for(const type of ['checkout.session.completed','checkout.session.async_payment_succeeded']){
    const r=runtime(),response=await deliver(r,type,'paid');
    assert.equal(response.status,200);assert.equal(r.calls.length,1);
    assert.equal(r.calls[0].name,'confirm_retail_payment');
  }
});
test('expiration and failure events never confirm a seat',async()=>{
  for(const type of ['checkout.session.expired','checkout.session.async_payment_failed']){
    const r=runtime();await deliver(r,type,'unpaid');assert.equal(r.calls.length,0);
  }
});
