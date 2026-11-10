import {easternInstant} from '../registration-reschedule/policy.mjs';
// Scope follows the evidenced BLS full-class policy, never the skills profile.
export function fullCourseOffers(payload,course,now=Date.now()){
 if(!['209806','359474'].includes(String(course))||payload?.pageKey!=='bls'||payload.schemaVersion!=='selector-resolved-availability.v1')throw Error('invalid_session');
 const generated=Date.parse(payload.generatedAt),lease=Date.parse(payload.validUntil);
 if(!Number.isFinite(generated)||generated>now+60000||generated<now-1800000||!Number.isFinite(lease)||lease<=now)throw Error('calendar_refresh_required');
 const offers=[];
 for(const day of payload.dates||[])for(const slot of day.startTimes||[])for(const c of slot.courses||[]){
  if(String(c.courseId)!==String(course)||c.offerType!=='dynamic_appointment'||c.publicSelectable!==true||
     c.instructor!=='Brian Ennis'||c.resource!==':: Wilmington; Shipyard Blvd - B'||c.location!==':: Wilmington; Shipyard Blvd'||
     !c.availabilityBlockId||!Array.isArray(c.sourceSessionIds)||c.durationMinutes!==120||c.schedulerConsumptionMinutes!==150||
     c.cleanupBufferMinutes!==30||c.setupBufferMinutes!==0||!/^\d+$/.test(String(c.appointmentDayId||'')))continue;
  const local=day.date+'T'+slot.startTime;
  if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(local))continue;
  const startsAt=easternInstant(local),start=Date.parse(startsAt),until=Math.min(lease,Date.parse(c.validUntil));
  if(!startsAt||start<=now||!Number.isFinite(until)||until<=now||Date.parse(c.occupiedUntil)!==start+150*60000)continue;
  const selectionId='dynamic:'+encodeURIComponent(JSON.stringify([String(course),String(c.appointmentDayId),local,c.instructor,c.resource,120,150,c.availabilityBlockId]));
  offers.push({kind:'dynamic',authority:'native-full-course.v1',courseNumber:String(course),selectionId,localStart:local,startsAt,
   endsAt:new Date(start+120*60000).toISOString(),consumptionEndsAt:new Date(start+150*60000).toISOString(),
   instructor:c.instructor,resource:c.resource,location:c.location,appointmentDayId:String(c.appointmentDayId),
   availabilityBlockId:c.availabilityBlockId,sourceSessionIds:c.sourceSessionIds,generatedAt:new Date(generated).toISOString(),validUntil:new Date(until).toISOString()});
 }
 return offers;
}
