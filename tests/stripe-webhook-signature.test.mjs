import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {stripTypeScriptTypes} from 'node:module';
import {createHmac,webcrypto} from 'node:crypto';
import {readFileSync} from 'node:fs';

// Exercise the actual inline verifier. No production clock override or copied
// verifier is needed: only this isolated VM receives the deterministic clock.
const source=readFileSync(new URL('../supabase/functions/stripe-registration-webhook/index.ts',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'');
const NOW=1900000000,secret='synthetic-webhook-secret';
const raw=' {"id":"evt_synthetic","label":"café 🩺","value":1}\n';
const sign=(body=raw,timestamp=NOW,key=secret)=>createHmac('sha256',key).update(`${timestamp}.${body}`).digest('hex');
const header=(body=raw,timestamp=NOW,key=secret)=>`t=${timestamp},v1=${sign(body,timestamp,key)}`;
const forbid=()=>assert.fail('Unexpected network or handler access in verifier-only test');
globalThis.fetch=forbid;
function verifier(now=NOW){
  let verifications=0;
  const context=vm.createContext({TextEncoder,Date:class extends Date{static now(){return now*1000;}},
    crypto:{subtle:{importKey:(...args)=>webcrypto.subtle.importKey(...args),verify:(...args)=>{verifications++;return webcrypto.subtle.verify(...args);}}},
    fetch:forbid,createClient:forbid,Deno:{serve:()=>{},env:{get:forbid}},console:{log:forbid,error:forbid,warn:forbid}});
  vm.runInContext(stripTypeScriptTypes(source),context);
  return {verify:context.verify,count:()=>verifications};
}

test('actual verifier authenticates exact raw UTF-8 body, never a parsed/reformatted version',async()=>{
  const {verify}=verifier();
  assert.equal(await verify(raw,header(),secret),true);
  for(const changed of [raw.trim(),raw+' ',JSON.stringify(JSON.parse(raw)),raw.replace('café','cafe'),raw.replace('1','2')]){
    assert.equal(await verify(changed,header(),secret),false);
  }
  assert.equal(await verify(raw,header(),'wrong-synthetic-secret'),false);
});

test('rotation accepts any v1 in either order and verifies every bounded candidate',async()=>{
  const valid=sign(),other=sign(raw,NOW,'synthetic-rotated-secret');
  for(const signatures of [[valid,other],[other,valid],[other,valid,other],[valid,valid]]){
    const h=verifier();
    assert.equal(await h.verify(raw,`t=${NOW},${signatures.map(value=>'v1='+value).join(',')}`,secret),true);
    assert.equal(h.count(),signatures.length);
  }
  assert.equal(await verifier().verify(raw,`t=${NOW},v1=${other},v1=${other}`,secret),false);
});

test('well-formed unknown schemes and separator whitespace do not suppress a valid v1',async()=>{
  const {verify}=verifier();
  assert.equal(await verify(raw,`v0=old-signature, t=${NOW}, v1=${sign().toUpperCase()},v2=future-signature`,secret),true);
  assert.equal(await verify(raw,`v1=${sign()},v0=old-signature,t=${NOW}`,secret),true);
  assert.equal(await verify(raw,`t=${NOW},v0=${sign()}`,secret),false,'v0 is not a supported authenticator');
  assert.equal(await verify(raw,`t=${NOW},V1=${sign()}`,secret),false,'scheme names are exact');
});

test('freshness accepts the inclusive five-minute boundary and rejects past/future skew',async()=>{
  const h=verifier();
  for(const delta of [-300,-299,0,299,300])assert.equal(await h.verify(raw,header(raw,NOW+delta),secret),true,`delta=${delta}`);
  const before=h.count();
  for(const delta of [-365*86400,-301,301,365*86400])assert.equal(await h.verify(raw,header(raw,NOW+delta),secret),false,`delta=${delta}`);
  assert.equal(h.count(),before,'stale timestamps fail before cryptographic work');
  assert.equal(await verifier(NOW+0.999).verify(raw,header(raw,NOW-300),secret),true,'timestamps have integer-second precision');
  assert.equal(await verifier(NaN).verify(raw,header(),secret),false);
  assert.equal(await verifier(Infinity).verify(raw,header(),secret),false);
});

test('duplicate timestamps are rejected even if identical or paired with a matching signature',async()=>{
  const {verify}=verifier();
  for(const value of [NOW,NOW-1,NOW+1])for(const duplicate of [`t=${value},${header()}`,`${header()},t=${value}`]){
    assert.equal(await verify(raw,duplicate,secret),false,duplicate);
  }
});

test('noncanonical, unsafe and malformed timestamps cannot authenticate',async()=>{
  const {verify}=verifier();
  for(const timestamp of ['',`0${NOW}`,`+${NOW}`,`-${NOW}`,`${NOW}.0`,`${NOW}junk`,'1.9e9','NaN','Infinity','9007199254740992','90071992547409910',' 1900000000']){
    assert.equal(await verify(raw,`t=${timestamp},v1=${sign(raw,timestamp)}`,secret),false,JSON.stringify(timestamp));
  }
});

test('malformed components and signatures fail closed even alongside a valid signature',async()=>{
  const h=verifier(),valid=header();
  for(const value of [null,'',`v1=${sign()}`,`t=${NOW}`,`${valid},`,`,${valid}`,`${valid},,v0=old`,
    `${valid},garbage`,`${valid},=value`,`${valid},v0=`,`${valid},v0=a=b`,`${valid},v0=has space`,
    `${valid},v1=`,`${valid},v1=xyz`,`${valid},v1=${'0'.repeat(63)}`,`${valid},v1=${'0'.repeat(65)}`,
    `${valid},v1=${'g'.repeat(64)}`,`${valid},v1=${sign()}=suffix`,`${valid},v1 =${sign()}`,`${valid},t =${NOW}`]){
    assert.equal(await h.verify(raw,value,secret),false,JSON.stringify(value));
  }
  assert.equal(h.count(),0,'malformed headers never reach cryptographic verification');
  for(const missing of [null,''])assert.equal(await h.verify(raw,valid,missing),false);
});

test('header length and component count are bounded without truncating or selecting the last v1',async()=>{
  const h=verifier(),prefix=header()+',v0=';
  const atLengthLimit=prefix+'x'.repeat(4096-prefix.length);
  assert.equal(await h.verify(raw,atLengthLimit,secret),true);
  assert.equal(await h.verify(raw,atLengthLimit+'x',secret),false);
  const parts=[`t=${NOW}`,...Array(30).fill('v1='+'0'.repeat(64)),`v1=${sign()}`];
  assert.equal(parts.length,32);
  assert.equal(await h.verify(raw,parts.join(','),secret),true);
  const count=h.count();
  assert.equal(await h.verify(raw,parts.join(',')+',v0=extra',secret),false);
  assert.equal(h.count(),count);
});
