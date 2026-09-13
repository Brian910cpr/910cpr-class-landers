const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
test('shared animation code never dismisses the Maxim login gate on DOMContentLoaded', () => {
  const classes = new Set(), events = new Map();
  const window = {location:{pathname:'/corp/maxim.html'},fetch:async()=>{throw Error('no network expected');},addEventListener:(name,fn)=>events.set(name,fn),matchMedia:()=>({matches:true})};
  const document = {getElementById:id=>id==='accessGate'?{classList:{add:value=>classes.add(value)}}:null};
  vm.runInNewContext(fs.readFileSync(new URL('../docs/assets/interaction-motion.js',`file://${__filename}`),'utf8'),{window,document});
  events.get('DOMContentLoaded')?.();
  assert.equal(classes.has('hidden'),false);
});
