const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../docs/register/index.html'),'utf8');
const fn=html.slice(html.indexOf('function openPayment('),html.indexOf('\nconst money='));
function setup(embedded){const top=[],self=[];const context={URL,embedded,window:{top:{location:{assign:u=>top.push(u)}}},location:{assign:u=>self.push(u)}};vm.createContext(context);vm.runInContext(fn,context);return{context,top,self}}
test('embedded checkout opens hosted Stripe at the top level',()=>{const h=setup(true);vm.runInContext("openPayment('https://checkout.stripe.com/c/pay/cs_test_synthetic')",h.context);assert.equal(h.top.length,1);assert.equal(h.self.length,0)});
test('standalone recovery keeps its existing top-level payment navigation',()=>{const h=setup(false);vm.runInContext("openPayment('https://checkout.stripe.com/c/pay/cs_test_synthetic')",h.context);assert.equal(h.self.length,1);assert.equal(h.top.length,0)});
test('untrusted checkout URLs never navigate',()=>{for(const value of ['https://evil.test/pay','http://checkout.stripe.com/pay','javascript:alert(1)']){const h=setup(true);assert.throws(()=>vm.runInContext(`openPayment(${JSON.stringify(value)})`,h.context));assert.equal(h.top.length+h.self.length,0)}});
