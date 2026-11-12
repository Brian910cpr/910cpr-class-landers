const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../docs/assets/resolved-selector-availability.js'),'utf8');
const bootstrap=source.slice(source.indexOf('// All course selectors share'));
test('shared selector loads canonical intake once, after DOM readiness, and skips non-selectors',()=>{
 for(const readyState of ['loading','complete'])for(const selector of [true,false])for(const loaded of [true,false]){
  const appended=[],events={};
  const document={readyState,getElementById:()=>selector?{}:null,querySelector:()=>loaded?{}:null,
   createElement:()=>({}),head:{appendChild:s=>appended.push(s)},addEventListener:(k,fn)=>events[k]=fn};
  vm.runInNewContext(bootstrap,{document});
  if(readyState==='loading'){assert.equal(appended.length,0);events.DOMContentLoaded();}
  assert.equal(appended.length,selector&&!loaded?1:0);
  if(appended.length)assert.equal(appended[0].src,'/assets/inline-registration.js?v=20261108.1');
 }
});
