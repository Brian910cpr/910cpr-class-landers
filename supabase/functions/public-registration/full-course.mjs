import {easternInstant} from '../registration-reschedule/policy.mjs';
import {ADVANCED_COURSES,advancedFullCourseOffers} from './advanced-course.mjs';
// Exact full-class identities only. Blended Heartsaver courses never enter here.
const HEARTSAVER=Object.freeze({
 '209809':{canonicalCourseId:'23dfcfa7-4224-46ed-8d45-64d43d5425db',instructionMinutes:120,cleanupMinutes:30},
 '344085':{canonicalCourseId:'306bc81a-0e09-49e1-8910-e05501222eb4',instructionMinutes:90,cleanupMinutes:15},
});
// Keep BLS deployable against its existing zero-argument RPC. Optional course
// scopes must not make that established path depend on a later migration.
export function fullCoursePolicyRpcArgs(course){
 if(typeof course!=='string'||!/^\d+$/.test(course))throw Error('invalid_course');
 return ['209806','359474'].includes(course)?{}:{p_course_number:course};
}
export function fullCoursePage(course){
 return ['209806','359474'].includes(String(course))?'bls':Object.hasOwn(HEARTSAVER,String(course))?'heartsaver':ADVANCED_COURSES[String(course)]||null;
}
export const fullCourseOptionRpc=course=>Object.hasOwn(ADVANCED_COURSES,String(course))?'native_advanced_full_course_option':'native_full_course_option';
export function fullCourseOffers(payload,course,now=Date.now(),options={}){
 if(Object.hasOwn(ADVANCED_COURSES,String(course)))return advancedFullCourseOffers(payload,String(course),now,options.coursePolicy);
 const page=fullCoursePage(course),heartsaver=page==='heartsaver',policy=options.coursePolicy,expected=HEARTSAVER[String(course)];
 if(!page||payload?.pageKey!==page||payload.schemaVersion!=='selector-resolved-availability.v1')throw Error('invalid_session');
 if(heartsaver&&(!policy||policy.materializationEnabled!==true||policy.nativePublicationEnabled!==true||policy.pageKey!==page||
  policy.nativeScopeId!=='brian-shipyard-b.v1'||policy.coursePolicyKey!==`heartsaver-full:${course}.v1`||
  policy.canonicalCourseId!==expected.canonicalCourseId||policy.instructionMinutes!==expected.instructionMinutes||
  policy.cleanupMinutes!==expected.cleanupMinutes||!Number.isInteger(policy.maxStudents)||policy.maxStudents<1))return [];
 const instruction=heartsaver?policy.instructionMinutes:120,cleanup=heartsaver?policy.cleanupMinutes:30,occupied=instruction+cleanup;
 const generated=Date.parse(payload.generatedAt),lease=Date.parse(payload.validUntil);
 if(!Number.isFinite(generated)||generated>now+60000||generated<now-1800000||!Number.isFinite(lease)||lease<=now)throw Error('calendar_refresh_required');
 const offers=[];
 for(const day of payload.dates||[])for(const slot of day.startTimes||[])for(const c of slot.courses||[]){
  const native=c.authority==='native-full-course.v2',proof=Date.parse(c.proofObservedAt);
  if(heartsaver&&(!native||c.coursePolicyKey!==policy.coursePolicyKey))continue;
  if(native&&(!/T.*(?:Z|[+-]\d{2}:\d{2})$/.test(c.proofObservedAt||'')||!Number.isFinite(proof)||proof>generated||proof>now||proof<now-900000||Date.parse(c.validUntil)>proof+900000||Date.parse(c.validUntil)>lease))continue;
  if(native && ('appointmentDayId' in c||'matchedContainerId' in c||lease>generated+900000||options.nativePublicationEnabled!==true||c.nativeScopeId!=='brian-shipyard-b.v1'||!/^native-full:[a-f0-9]{64}$/.test(c.selectionId||'')||generated>now||generated<now-900000))continue;
  if(String(c.courseId)!==String(course)||c.offerType!=='dynamic_appointment'||c.publicSelectable!==true||
     c.instructor!=='Brian Ennis'||c.resource!==':: Wilmington; Shipyard Blvd - B'||c.location!==':: Wilmington; Shipyard Blvd'||
     !c.availabilityBlockId||!Array.isArray(c.sourceSessionIds)||c.durationMinutes!==instruction||c.schedulerConsumptionMinutes!==occupied||
     c.cleanupBufferMinutes!==cleanup||c.setupBufferMinutes!==0||(!native&&!/^\d+$/.test(String(c.appointmentDayId||''))))continue;
  const local=day.date+'T'+slot.startTime;
  if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(local))continue;
  const startsAt=easternInstant(local),start=Date.parse(startsAt),until=Math.min(lease,Date.parse(c.validUntil));
  if(native&&(Date.parse(c.validUntil)>generated+900000||start<now+86400000||start>now+90*86400000))continue;
  if(!startsAt||start<=now||!Number.isFinite(until)||until<=now||Date.parse(c.occupiedUntil)!==start+occupied*60000)continue;
  const selectionId=native?c.selectionId:'dynamic:'+encodeURIComponent(JSON.stringify([String(course),String(c.appointmentDayId),local,c.instructor,c.resource,120,150,c.availabilityBlockId]));
  offers.push({kind:'dynamic',authority:native?'native-full-course.v2':'native-full-course.v1',courseNumber:String(course),selectionId,localStart:local,startsAt,
   endsAt:new Date(start+instruction*60000).toISOString(),consumptionEndsAt:new Date(start+occupied*60000).toISOString(),
   instructor:c.instructor,resource:c.resource,location:c.location,...(native?{nativeScopeId:c.nativeScopeId,proofObservedAt:c.proofObservedAt}:{appointmentDayId:String(c.appointmentDayId)}),
   ...(heartsaver?{coursePolicyKey:policy.coursePolicyKey}:{}),availabilityBlockId:c.availabilityBlockId,sourceSessionIds:c.sourceSessionIds,generatedAt:new Date(generated).toISOString(),validUntil:new Date(until).toISOString()});
 }
 return offers;
}
