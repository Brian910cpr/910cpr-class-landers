import {easternInstant} from '../registration-reschedule/policy.mjs';
export const SITE='https://www.910cpr.com';
export const CONTEXTS=Object.freeze({'cpr-aed':'heartsaver','first-aid-cpr-aed':'heartsaver','arc-blended':'arc','hsi-blended':'hsi','bls-skills':'bls'});
export function skillsOffers(payload,context,now=Date.now(),publicCourse='509474',options={}) {
  if(publicCourse!=='509474'&&(publicCourse!=='210549'||context!=='bls-skills'))throw Error('invalid_context');
  if(!CONTEXTS[context]||payload?.pageKey!==CONTEXTS[context]||payload.schemaVersion!=='selector-resolved-availability.v1')throw Error('invalid_context');
  const generated=Date.parse(payload.generatedAt),lease=Date.parse(payload.validUntil);
  if(!Number.isFinite(generated)||generated>now+60000||now-generated>30*60000)throw Error('calendar_refresh_required');
  const offers=[];
  for(const day of payload.dates||[])for(const slot of day.startTimes||[])for(const c of slot.courses||[]) {
    const nativeSeated=c.authority==='native-skills-seated.v1';
    const native=nativeSeated||c.authority==='native-skills-publication.v1';
    if(!native&&(c.authority||c.nativeOfferId||c.nativeScopeId||c.proofObservedAt||c.identityWitness||c.profileVersion))continue;
    const proof=Date.parse(c.proofObservedAt),nativeLease=Date.parse(c.validUntil);
    if(native&&(options.nativePublicationEnabled!==true||publicCourse!=='509474'||context==='bls-skills'||
       c.nativeScopeId!=='brian-shipyard-b.v1'||c.qualificationPolicy!=='skills-session-policy.v1'||
       c.capacity!==2||c.instructor!=='Brian Ennis'||c.setupBufferMinutes!==0||
       (!nativeSeated&&!/^native-skills:[a-f0-9]{64}$/.test(c.nativeOfferId||''))||
       (nativeSeated&&(!/^(?:[0-9]+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})$/.test(c.session_id||'')||
        c.nativeOfferId!=='native-skills-seated:'+c.session_id||!Number.isSafeInteger(c.profileVersion)||c.profileVersion<1||
        !/^[a-f0-9]{32}$/.test(c.identityWitness||'')||!Number.isInteger(c.remainingSeats)||c.remainingSeats<1||c.remainingSeats>2||
        JSON.stringify(c.sourceSessionIds)!==JSON.stringify([c.session_id])))||
       !Array.isArray(c.skillsContexts)||!c.skillsContexts.includes(context)||
       c.skillsContexts.some(key=>CONTEXTS[key]!==payload.pageKey||key==='bls-skills')||
       'appointmentDayId' in c||'matchedContainerId' in c||c.offerType!==(nativeSeated?'seated_class':'dynamic_appointment')||
       !/T.*(?:Z|[+-]\d{2}:\d{2})$/.test(c.proofObservedAt||'')||
       !Number.isFinite(proof)||proof>generated||proof>now||proof<now-900000||
       !Number.isFinite(nativeLease)||nativeLease<=now||nativeLease>proof+900000||nativeLease>lease||
       !Number.isFinite(lease)||lease>generated+900000||generated>now||generated<now-900000))continue;
    const seated=c.offerType==='seated_class';
    const sourceSessionId=String(c.session_id||'');
    if(c.courseId!==publicCourse||(!seated&&c.offerType!=='dynamic_appointment')||c.publicSelectable!==true||
       c.durationMinutes!==45||c.schedulerConsumptionMinutes!==60||c.cleanupBufferMinutes!==15||
       !c.availabilityBlockId||!c.instructor||c.resource!==':: Wilmington; Shipyard Blvd - B'||
       c.location!==':: Wilmington; Shipyard Blvd'||!Array.isArray(c.sourceSessionIds)||
       (seated&&(!sourceSessionId||c.availabilityBlockId!=='seated:'+sourceSessionId)))continue;
    const local=day.date+'T'+slot.startTime;
    if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(local))continue;
    const startsAt=easternInstant(local),start=Date.parse(startsAt),validUntil=seated&&!native?generated+15*60000:Math.min(lease,Date.parse(c.validUntil));
    if(native&&(start<now+86400000||start>now+90*86400000||Number(slot.startTime.slice(3))%15))continue;
    if(!startsAt||start<=now||!Number.isFinite(validUntil)||validUntil<=now||Date.parse(c.occupiedUntil)!==start+60*60000)continue;
    const selectionId=native?'skills:'+c.nativeOfferId+':'+context:'skills:'+encodeURIComponent(JSON.stringify([publicCourse,context,local,c.instructor,c.resource,c.availabilityBlockId]));
    offers.push({kind:'dynamic',...(native?{authority:c.authority,nativeScopeId:c.nativeScopeId,nativeOfferId:c.nativeOfferId,proofObservedAt:c.proofObservedAt,qualificationPolicy:c.qualificationPolicy,capacity:2,...(nativeSeated?{profileVersion:c.profileVersion,identityWitness:c.identityWitness,remainingSeats:c.remainingSeats}:{})}:{}),offerType:c.offerType,sourceSessionId:seated?sourceSessionId:null,courseNumber:'509474',context,selectionId,localStart:local,startsAt,
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
