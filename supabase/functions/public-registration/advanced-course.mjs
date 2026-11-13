import {easternInstant} from '../registration-reschedule/policy.mjs';
export const ADVANCED_COURSES=Object.freeze({'241108':'acls','209818':'acls','209805':'pals','251496':'pals'});
const UUID=/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i;
const integer=n=>Number.isInteger(n)&&n>=0;
export function advancedFullCourseOffers(payload,course,now,policy){
 const page=ADVANCED_COURSES[String(course)];
 if(!page||payload?.pageKey!==page||payload.schemaVersion!=='selector-resolved-availability.v1')throw Error('invalid_session');
 if(!policy||policy.materializationEnabled!==true||policy.nativePublicationEnabled!==true||policy.pageKey!==page||
  policy.nativeScopeId!=='qualified-advanced-shipyard-b.v1'||policy.coursePolicyKey!==`advanced-full:${course}.v1`||
  !UUID.test(policy.canonicalCourseId||'')||policy.instructionMinutes!==240||
  !integer(policy.setupMinutes)||!integer(policy.cleanupMinutes)||!Number.isInteger(policy.maxStudents)||policy.maxStudents<1||
  !Array.isArray(policy.instructors)||!policy.instructors.length)return [];
 const generated=Date.parse(payload.generatedAt),lease=Date.parse(payload.validUntil);
 if(!Number.isFinite(generated)||generated>now||generated<now-900000||!Number.isFinite(lease)||lease<=now||lease>generated+900000)throw Error('calendar_refresh_required');
 const offers=[];
 for(const day of payload.dates||[])for(const slot of day.startTimes||[])for(const c of slot.courses||[]){
  if(String(c.courseId)!==String(course)||c.authority!=='native-full-course.v3'||c.publicSelectable!==true||c.offerType!=='dynamic_appointment'||
   c.nativeScopeId!==policy.nativeScopeId||c.coursePolicyKey!==policy.coursePolicyKey||c.canonicalCourseId!==policy.canonicalCourseId||
   !/^native-full:[a-f0-9]{64}$/.test(c.selectionId||'')||'appointmentDayId' in c||'matchedContainerId' in c||
   c.resource!==policy.resource||c.location!==policy.location||!c.availabilityBlockId||!Array.isArray(c.sourceSessionIds)||
   c.durationMinutes!==240||c.setupBufferMinutes!==policy.setupMinutes||c.cleanupBufferMinutes!==policy.cleanupMinutes||
   c.schedulerConsumptionMinutes!==240+policy.setupMinutes+policy.cleanupMinutes)continue;
  const instructor=policy.instructors.find(i=>i.id===c.instructorId&&i.name===c.instructor&&i.availabilityPersonId===c.availabilityPersonId);
  if(!instructor||!UUID.test(instructor.id)||!Array.isArray(instructor.calendarSourceKeys)||!instructor.calendarSourceKeys.includes(c.calendarSourceKey))continue;
  const local=day.date+'T'+slot.startTime,startsAt=easternInstant(local),start=Date.parse(startsAt),end=start+240*60000;
  const occupiedStart=start-policy.setupMinutes*60000,occupiedEnd=end+policy.cleanupMinutes*60000;
  const proof=Date.parse(c.proofObservedAt),until=Math.min(lease,Date.parse(c.validUntil));
  if(!startsAt||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(local)||start<now+86400000||start>now+90*86400000||
   !Number.isFinite(proof)||proof>generated||proof>now||proof<now-900000||!Number.isFinite(until)||until<=now||Date.parse(c.validUntil)>lease||
   Date.parse(c.validUntil)>proof+900000||!Number.isFinite(Date.parse(c.availabilityStartsAt))||!Number.isFinite(Date.parse(c.availabilityEndsAt))||
   Date.parse(c.availabilityStartsAt)>occupiedStart||Date.parse(c.availabilityEndsAt)<occupiedEnd||Date.parse(c.occupiedFrom)!==occupiedStart||Date.parse(c.occupiedUntil)!==occupiedEnd||
   Date.parse(instructor.qualificationValidThrough)<occupiedEnd||!Number.isFinite(Date.parse(instructor.qualificationValidThrough)))continue;
  offers.push({kind:'dynamic',authority:'native-full-course.v3',courseNumber:String(course),selectionId:c.selectionId,localStart:local,startsAt,
   endsAt:new Date(end).toISOString(),consumptionStartsAt:new Date(occupiedStart).toISOString(),consumptionEndsAt:new Date(occupiedEnd).toISOString(),
   instructor:c.instructor,instructorId:instructor.id,availabilityPersonId:instructor.availabilityPersonId,resource:c.resource,location:c.location,
   nativeScopeId:policy.nativeScopeId,coursePolicyKey:policy.coursePolicyKey,canonicalCourseId:policy.canonicalCourseId,
   proofObservedAt:c.proofObservedAt,availabilityBlockId:c.availabilityBlockId,sourceSessionIds:c.sourceSessionIds,
   calendarSourceKey:c.calendarSourceKey,availabilityStartsAt:c.availabilityStartsAt,availabilityEndsAt:c.availabilityEndsAt,
   generatedAt:new Date(generated).toISOString(),validUntil:new Date(until).toISOString()});
 }
 return offers;
}
