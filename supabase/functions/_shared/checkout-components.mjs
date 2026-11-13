// Server-authoritative component allocation. Never discount an undifferentiated
// bundle total: access and materials must have their own verified amounts.
export const ADDED_SESSION_DISCOUNT_BPS=1000;
const FAMILIES=Object.freeze({'209806':'BLS','359474':'BLS','509474':'BLS','210549':'BLS','241108':'ACLS','209818':'ACLS','209805':'PALS','251496':'PALS'});
const PASS_THROUGH=new Set(['heartcode_access','paper_book','ebook']);
const integer=n=>Number.isSafeInteger(n)&&n>=0&&n<=10000000;
export function quoteCourseRegistration(items){
 if(!Array.isArray(items)||items.length<1||items.length>3)throw Error('invalid_course_combination');
 const families=new Set(),lines=[];let subtotalCents=0,discountCents=0;
 for(const [index,item] of items.entries()){
  const family=FAMILIES[item.courseNumber];
  if(!family||families.has(family))throw Error('invalid_course_combination');families.add(family);
  if(item.allocationVersion!=='session-plus-components.v1'||!integer(item.sessionCents)||item.sessionCents<=0||
   typeof item.priceEvidence!=='string'||!item.priceEvidence.trim())throw Error('unverified_price_allocation');
  if(!Array.isArray(item.components))throw Error('unverified_price_allocation');
  const access=item.components.filter(c=>c.kind==='heartcode_access');
  if((item.courseNumber==='210549'&&access.length!==1)||(item.courseNumber!=='210549'&&access.length))throw Error('invalid_online_inclusion');
  const quantity=item.quantity??1;if(!Number.isSafeInteger(quantity)||quantity<1||quantity>10)throw Error('invalid_quantity');
  const base=item.sessionCents*quantity;
  // Round the discount amount (not each material or the final total), half-up
  // to one cent, once for this independently priced session line.
  const reduction=index===0?0:Math.floor((base*ADDED_SESSION_DISCOUNT_BPS+5000)/10000);
  lines.push({courseNumber:item.courseNumber,kind:'session',quantity,unitAmountCents:item.sessionCents,
   subtotalCents:base,discountCents:reduction,totalCents:base-reduction,primary:index===0});
  subtotalCents+=base;discountCents+=reduction;
  const seen=new Set();let materialFormat=null;
  for(const component of item.components){
   if(!PASS_THROUGH.has(component.kind)||typeof component.sku!=='string'||!component.sku.trim()||seen.has(component.sku)||
    !integer(component.unitAmountCents)||component.unitAmountCents<=0||component.verified!==true||component.active!==true)
    throw Error('unverified_component_price');
   if(['paper_book','ebook'].includes(component.kind)){
    if(materialFormat&&materialFormat!==component.kind)throw Error('conflicting_material_formats');materialFormat=component.kind;
   }
   seen.add(component.sku);const amount=component.unitAmountCents*quantity;
   lines.push({courseNumber:item.courseNumber,kind:component.kind,sku:component.sku,quantity,
    unitAmountCents:component.unitAmountCents,subtotalCents:amount,discountCents:0,totalCents:amount,primary:index===0});
   subtotalCents+=amount;
  }
 }
 if(!integer(subtotalCents)||!integer(discountCents)||subtotalCents<=discountCents)throw Error('invalid_total');
 return {schemaVersion:'course-registration-quote.v1',currency:'usd',addedSessionDiscountBps:ADDED_SESSION_DISCOUNT_BPS,
  lines,subtotalCents,discountCents,totalCents:subtotalCents-discountCents};
}

// Distinct canonical sessions remain distinct, even when bought together.
export function validateCourseSchedule(items){
 if(!Array.isArray(items)||!items.length)throw Error('invalid_course_combination');
 const intervals=items.map(item=>{
  const s=item.session,start=Date.parse(s?.consumptionStartsAt),end=Date.parse(s?.consumptionEndsAt);
  if(!s||typeof s.identity!=='string'||!s.identity||!Number.isFinite(start)||!Number.isFinite(end)||end<=start||
   !Number.isFinite(Date.parse(s.startsAt))||!Number.isFinite(Date.parse(s.endsAt))||
   start>Date.parse(s.startsAt)||end<Date.parse(s.endsAt)||Date.parse(s.endsAt)<=Date.parse(s.startsAt))throw Error('unverified_session_interval');
  return {identity:s.identity,start,end};
 }).sort((a,b)=>a.start-b.start);
 if(new Set(intervals.map(x=>x.identity)).size!==intervals.length)throw Error('duplicate_course_session');
 for(let i=1;i<intervals.length;i++)if(intervals[i].start<intervals[i-1].end)throw Error('course_schedule_overlap');
 return true;
}
