const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync('docs/corp/nhcso/index.html','utf8');
const source=html.slice(html.indexOf('function localUnlockCode'),html.indexOf("\n$('finalize').onclick"));
function harness(answer,finalized=true){const button={};const ctx={currentId:'NHCSO-12345',finalizedLocalEdit:false,isFinalized:()=>finalized,$:()=>button,prompt:message=>{ctx.message=message;return typeof answer==='function'?answer(ctx):answer},applyClassLock:()=>ctx.applied=true};vm.createContext(ctx);vm.runInContext(source,ctx);button.onclick();return ctx}
test('cancel and wrong code preserve lock',()=>{for(const answer of [null,'wrong','NHCSO-12345']){const ctx=harness(answer);assert.equal(ctx.finalizedLocalEdit,false);assert.equal(ctx.applied,undefined)}});
test('short class-specific code acknowledges local-only unlock',()=>{const ctx=harness(c=>' '+c.localUnlockCode(c.currentId).toLowerCase()+' ');assert.equal(ctx.finalizedLocalEdit,true);assert.equal(ctx.applied,true);assert.match(ctx.message,/remains FINALIZED/);assert.match(ctx.message,/Brian@910cpr.com/);assert.equal(ctx.localUnlockCode(ctx.currentId).length,7);assert.notEqual(ctx.localUnlockCode('NHCSO-12346'),ctx.localUnlockCode(ctx.currentId))});
test('unfinalized classes cannot unlock',()=>{const ctx=harness('anything',false);assert.equal(ctx.message,undefined);assert.equal(ctx.finalizedLocalEdit,false)});
