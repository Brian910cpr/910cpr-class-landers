import {easternInstant} from '../registration-reschedule/policy.mjs';
export const SITE='https://www.910cpr.com';
export const CONTEXTS=Object.freeze({'cpr-aed':'heartsaver','first-aid-cpr-aed':'heartsaver','arc-blended':'arc','hsi-blended':'hsi'});
export function skillsOffers(payload,context,now=Date.now()) {
  if(!CONTEXTS[context]||payload?.pageKey!==CONTEXTS[context]||payload.schemaVersion!=='selector-resolved-availability.v1')throw Error('invalid_context');
  const generated=Date.parse(payload.generatedAt),lease=Date.parse(payload.validUntil);
  if(!Number.isFinite(generated)||generated>now+60000||now-generated>30*60000)throw Error('calendar_refresh_required');
  const offers=[];
  for(const day of payload.dates||[])for(const slot of day.startTimes||[])for(const c of slot.courses||[]) {
    const seated=c.offerType==='seated_class';
    const sourceSessionId=String(c.session_id||'');
    if(c.courseId!=='509474'||(!seated&&c.offerType!=='dynamic_appointment')||c.publicSelectable!==true||
       c.durationMinutes!==45||c.schedulerConsumptionMinutes!==60||c.cleanupBufferMinutes!==15||
       !c.availabilityBlockId||!c.instructor||c.resource!==':: Wilmington; Shipyard Blvd - B'||
       c.location!==':: Wilmington; Shipyard Blvd'||!Array.isArray(c.sourceSessionIds)||
       (seated&&(!sourceSessionId||c.availabilityBlockId!=='seated:'+sourceSessionId)))continue;
    const local=day.date+'T'+slot.startTime;
    if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(local))continue;
    const startsAt=easternInstant(local),start=Date.parse(startsAt),validUntil=seated?generated+15*60000:Math.min(lease,Date.parse(c.validUntil));
    if(!startsAt||start<=now||!Number.isFinite(validUntil)||validUntil<=now||Date.parse(c.occupiedUntil)!==start+60*60000)continue;
    const selectionId='skills:'+encodeURIComponent(JSON.stringify(['509474',context,local,c.instructor,c.resource,c.availabilityBlockId]));
    offers.push({kind:'dynamic',offerType:c.offerType,sourceSessionId:seated?sourceSessionId:null,courseNumber:'509474',context,selectionId,localStart:local,startsAt,
      endsAt:new Date(start+45*60000).toISOString(),consumptionEndsAt:new Date(start+60*60000).toISOString(),
      instructor:c.instructor,resource:c.resource,location:c.location,availabilityBlockId:c.availabilityBlockId,
      sourceSessionIds:c.sourceSessionIds,generatedAt:new Date(generated).toISOString(),validUntil:new Date(validUntil).toISOString()});
  }
  return offers;
}
export function studentInput(value) {
  if(!value||typeof value!=='object'||value.onlineCompleted!==true)throw Error('invalid_student');
  const student={firstName:String(value.firstName||'').trim(),lastName:String(value.lastName||'').trim(),
    email:String(value.email||'').trim().toLowerCase(),phone:String(value.phone||'').trim(),onlineCompleted:true};
  if(!student.firstName||!student.lastName||student.firstName.length>100||student.lastName.length>100||
     !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(student.email)||student.email.length>254||student.phone.length>50)throw Error('invalid_student');
  return student;
}
