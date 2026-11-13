import test from 'node:test';import assert from 'node:assert/strict';
import {quoteCourseRegistration,validateCourseSchedule} from '../supabase/functions/_shared/checkout-components.mjs';
const price={'241108':22500,'209818':22500,'209805':27500,'251496':22500,'209806':7500,'359474':7500,'509474':5500,'210549':5500};
const item=(courseNumber,components=[])=>({courseNumber,allocationVersion:'session-plus-components.v1',sessionCents:price[courseNumber],priceEvidence:'verified test-only catalog',components});
const component=(kind,amount,sku=kind)=>({kind,sku,unitAmountCents:amount,active:true,verified:true});
test('every primary advanced variant, BLS variant and other advanced variant discounts only added sessions',()=>{
 for(const main of ['241108','209818','209805','251496'])for(const bls of ['209806','359474','509474','210549'])for(const other of main.startsWith('24')||main==='209818'?['209805','251496']:['241108','209818']){
  const code=bls==='210549'?[component('heartcode_access',4000,'TEST-ONLINE')]:[];
  for(const courses of [[item(main)],[item(main),item(bls,code)],[item(main),item(other)],[item(main),item(bls,code),item(other)]]){
   const q=quoteCourseRegistration(courses),session=price[main]+courses.slice(1).reduce((n,i)=>n+i.sessionCents,0),added=courses.slice(1).reduce((n,i)=>n+i.sessionCents,0),access=courses.some(i=>i.courseNumber==='210549')?4000:0;
   assert.equal(q.totalCents,session-Math.round(added*.1)+access);assert.equal(q.lines[0].discountCents,0);
   assert.ok(q.lines.filter(x=>x.kind!=='session').every(x=>x.discountCents===0));
  }
 }
});
test('paper books, eBooks and access keep their independent full amounts and session discount is visible',()=>{
 const q=quoteCourseRegistration([item('241108',[component('paper_book',4501,'TEST-ACLS-PAPER')]),item('209805',[component('ebook',3999,'TEST-PALS-EBOOK')]),item('210549',[component('heartcode_access',4000,'TEST-HC'),component('ebook',2000,'TEST-BLS-EBOOK')])]);
 assert.equal(q.discountCents,3300);assert.equal(q.totalCents,66700);assert.equal(q.lines.length,7);
 assert.equal(q.lines.find(x=>x.sku==='TEST-HC').totalCents,4000);
});
test('ambiguous bundle allocation, unverified materials, duplicate families and conflicting formats fail closed',()=>{
 for(const bad of [{...item('210549'),allocationVersion:null},{...item('210549'),priceEvidence:''},item('209805',[{...component('ebook',3000),verified:false}]),item('209805',[component('ebook',null)]),item('209805',[component('ebook',3000),component('paper_book',3000)]),item('209805',[component('session',3000)])])assert.throws(()=>quoteCourseRegistration([item('241108'),bad]));
 assert.throws(()=>quoteCourseRegistration([item('241108'),item('210549')]),/invalid_online_inclusion/);
 assert.throws(()=>quoteCourseRegistration([item('241108'),item('509474',[component('heartcode_access',4000)])]),/invalid_online_inclusion/);
 assert.throws(()=>quoteCourseRegistration([item('241108'),item('209818')]),/invalid_course_combination/);
 assert.throws(()=>quoteCourseRegistration([item('241108'),item('209811')]),/invalid_course_combination/,'unresolved advanced skills policy is not a full-course allocation');
});
test('currency rounding and quantity are server determined; client discount/total fields do not affect quote',()=>{
 const q=quoteCourseRegistration([item('241108'),{...item('209805'),sessionCents:105,discountBps:10000,totalCents:1}]);
 assert.equal(q.lines[1].discountCents,11);assert.equal(q.totalCents,22594);
 assert.throws(()=>quoteCourseRegistration([{...item('241108'),quantity:0}]),/invalid_quantity/);
});
test('each course keeps its canonical occupied interval; overlap, missing bounds and duplicate identity reject',()=>{
 const s=(identity,start,end)=>({session:{identity,startsAt:start,endsAt:end,consumptionStartsAt:start,consumptionEndsAt:end}});
 const a=s('class-acls','2030-12-26T19:00:00Z','2030-12-26T23:00:00Z'),b=s('class-bls','2030-12-26T17:00:00Z','2030-12-26T19:00:00Z');
 assert.equal(validateCourseSchedule([a,b]),true);
 assert.throws(()=>validateCourseSchedule([a,{...b,session:{...b.session,consumptionEndsAt:'2030-12-26T19:15:00Z'}}]),/course_schedule_overlap/);
 assert.throws(()=>validateCourseSchedule([a,a]),/duplicate_course_session/);
 assert.throws(()=>validateCourseSchedule([{session:{identity:'missing'}}]),/unverified_session_interval/);
});
