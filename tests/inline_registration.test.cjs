const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../docs/assets/inline-registration.js'),'utf8');
function setup(){
 const events={},created=[],host={};let mutation;
 function element(tag){const el={tag,style:{},attrs:{},children:[],isConnected:true,
  setAttribute(k,v){this.attrs[k]=v},append(...c){this.children.push(...c)},appendChild(c){this.children.push(c)},
  addEventListener(k,fn){this[k]=fn},remove(){this.removed=true},scrollIntoView(){},focus(){this.focused=true}};
  if(tag==='iframe')el.contentWindow={};created.push(el);return el;}
 const grid=element('div'),times=element('div'),choices=element('div');choices.parentElement=grid;
 const card=element('article'),link=element('a');link.href='https://www.910cpr.com/register/?session=123456';
 link.closest=s=>s==='.course'?card:link;
 const document={body:host,getElementById:id=>id==='start-list'?{closest:()=>times}:id==='course-list'?{closest:()=>choices}:host,querySelector:()=>null,createElement:element,addEventListener:(k,fn)=>events[k]=fn};
 vm.runInNewContext(source,{URL,location:{href:'https://www.910cpr.com/bls.html',origin:'https://www.910cpr.com'},document,
  Number,matchMedia:()=>({matches:false}),MutationObserver:class{constructor(fn){mutation=fn}observe(){}},addEventListener:(k,fn)=>events[k]=fn});
 const click=(extra={})=>{const e={target:link,button:0,preventDefault(){this.defaultPrevented=true},...extra};events.click(e);return e};
 return{events,created,card:grid,grid,times,choices,link,click,mutate:()=>mutation()};
}
test('keeps dates and expands intake across columns two and three',()=>{
 const h=setup();assert.equal(h.click().defaultPrevented,true);
 const panel=h.card.children[0],frame=panel.children[1];
 assert.equal(panel.id,'selected-time-checkout');assert.equal(frame.src,'/register/?session=123456&embed=1');
 assert.equal(h.link.attrs['aria-expanded'],'true');assert.match(panel.style.cssText,/grid-column:2\/-1/);
 assert.equal(h.times.hidden,true);assert.equal(h.choices.hidden,true);
 panel.children[0].click();assert.equal(h.times.hidden,false);assert.equal(panel.hidden,true);
 h.click();assert.equal(panel.hidden,false);assert.equal(h.grid.children.length,1);
});
test('respects past-time cancellation, modified clicks and unrelated/dynamic URLs',()=>{
 for(const extra of [{defaultPrevented:true},{ctrlKey:true},{metaKey:true},{shiftKey:true},{button:1}]){const h=setup();h.click(extra);assert.equal(h.card.children.length,0)}
 for(const href of ['https://evil.test/register/?session=123456','https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=1&courseId=209806','https://www.910cpr.com/register/?session=bad']){
  const h=setup();h.link.href=href;assert.equal(h.click().defaultPrevented,undefined);assert.equal(h.card.children.length,0);
 }
});
test('legacy concrete class IDs share the native-readiness checked form',()=>{
 const h=setup();h.link.href='https://coastalcprtraining.enrollware.com/enroll?id=14733309';h.click();
 assert.match(h.card.children[0].children[1].src,/session=14733309&embed=1/);
});
test('only the selected same-origin frame may resize its panel; height is bounded',()=>{
 const h=setup();h.click();const frame=h.card.children[0].children[1],data={type:'landerware:checkout-size',sessionId:'123456',height:1500};
 h.events.message({origin:'https://evil.test',source:frame.contentWindow,data});assert.equal(frame.style.height,undefined);
 h.events.message({origin:'https://www.910cpr.com',source:{},data});assert.equal(frame.style.height,undefined);
 h.events.message({origin:'https://www.910cpr.com',source:frame.contentWindow,data});assert.equal(frame.style.height,'1500px');
 h.events.message({origin:'https://www.910cpr.com',source:frame.contentWindow,data:{...data,height:999999}});assert.equal(frame.style.height,'16000px');
});
test('calendar rerender retains the draft frame but hides stale-session checkout',()=>{
 const h=setup();h.click();const panel=h.card.children[0];h.link.isConnected=false;h.mutate();assert.notEqual(panel.removed,true);assert.equal(panel.hidden,true);assert.equal(h.times.hidden,false);
});
