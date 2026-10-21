export const SITE = 'https://www.910cpr.com';
export function familyPath(course) {
  if (/\bBLS\b/i.test(course)) return 'bls';
  if (/\bACLS\b/i.test(course)) return 'acls';
  if (/\bPALS\b/i.test(course)) return 'pals';
  if (/Heartsaver/i.test(course)) return 'heartsaver';
  throw Error('course_calendar_unavailable');
}
export function publishedOffers(payload, courseNumber, now=Date.now()) {
  const generated=Date.parse(payload.generatedAt);
  if (!Number.isFinite(generated) || generated>now+60000 || now-generated>30*60000) throw Error('calendar_refresh_required');
  const validUntil=Date.parse(payload.validUntil);
  const offers=[];
  for (const day of payload.dates||[]) for (const start of day.startTimes||[]) for (const course of start.courses||[]) {
    if (String(course.courseId)!==String(courseNumber)) continue;
    // Existing seated classes survive the short synthetic-offer publication expiry.
    if (course.offerType!=='seated_class' && (!Number.isFinite(validUntil)||validUntil<=now)) continue;
    let id, url;
    try {
      url=new URL(String(course.registrationUrl||course.appointmentUrl||'').replace(/&amp;/g,'&'), SITE);
      if (url.hostname==='coastalcprtraining.enrollware.com' && url.pathname==='/enroll') id=url.searchParams.get('id');
      if (url.origin===SITE && url.pathname==='/register/') id=url.searchParams.get('session');
    } catch { continue; }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day.date) || !/^\d{2}:\d{2}$/.test(start.startTime)) continue;
    if (id) { offers.push({externalId:id,localStart:day.date+'T'+start.startTime}); continue; }
    // The public selector owns availability, qualifications, resource and travel rules.
    // Retain its exact offer; displaying it must never materialize a class.
    if (course.offerType!=='dynamic_appointment' || course.publicSelectable===false ||
        !['209806','359474','209809','329495'].includes(String(courseNumber)) ||
        url.origin!=='https://coastalcprtraining.enrollware.com' || url.pathname!=='/enroll' ||
        url.searchParams.get('courseId')!==String(courseNumber) ||
        !/^\d+$/.test(url.searchParams.get('appointmentDayId')||'') ||
        String(course.appointmentDayId)!==url.searchParams.get('appointmentDayId') ||
        !course.availabilityBlockId || course.instructor!=='Brian Ennis' ||
        course.resource!==':: Wilmington; Shipyard Blvd - B') continue;
    const clock=/^(\d{1,2}):(\d{2}) (AM|PM)$/.exec(url.searchParams.get('startTime')||'');
    if (!clock || +clock[1]<1 || +clock[1]>12 || +clock[2]>59 ||
        `${String(+clock[1]%12+(clock[3]==='PM'?12:0)).padStart(2,'0')}:${clock[2]}`!==start.startTime) continue;
    const local=day.date+'T'+start.startTime, startsAt=easternInstant(local);
    const duration=course.durationMinutes, consumption=course.schedulerConsumptionMinutes;
    const occupiedUntil=Date.parse(course.occupiedUntil), lease=Math.min(validUntil,Date.parse(course.validUntil));
    if (!startsAt || !Number.isInteger(duration) || duration<=0 || !Number.isInteger(consumption) ||
        consumption<duration || consumption>1440 || !Number.isFinite(lease) || lease<=now ||
        occupiedUntil!==Date.parse(startsAt)+consumption*60000) continue;
    const endsAt=new Date(Date.parse(startsAt)+duration*60000).toISOString();
    const selectionId='dynamic:'+encodeURIComponent(JSON.stringify([String(courseNumber),String(course.appointmentDayId),
      local,course.instructor,course.resource,duration,consumption,course.availabilityBlockId]));
    offers.push({kind:'dynamic',selectionId,courseNumber:String(courseNumber),localStart:local,startsAt,endsAt,
      consumptionEndsAt:new Date(occupiedUntil).toISOString(),instructor:course.instructor,resource:course.resource,
      location:course.location,appointmentDayId:String(course.appointmentDayId),availabilityBlockId:course.availabilityBlockId,
      sourceSessionIds:course.sourceSessionIds||[],registrationUrl:url.href,
      generatedAt:new Date(generated).toISOString(),validUntil:new Date(lease).toISOString()});
  }
  return offers;
}
export function easternInstant(local) {
 // Reject nonexistent or ambiguous wall times, rather than silently choosing a DST fold.
 const base=Date.parse(local+'Z');
 if (!Number.isFinite(base)) return null;
 const matches=[4,5].map(offset=>new Date(base+offset*3600000).toISOString()).filter(iso=>localStart(iso)===local);
 return matches.length===1?matches[0]:null;
}
export function localStart(instant) {
 const parts=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date(instant)).map(p=>[p.type,p.value]));
 return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}
export const validToken=token=>/^lw_r_[0-9a-f]{64}$/.test(token);
