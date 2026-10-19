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
    let id;
    try {
      const url=new URL(course.registrationUrl||course.appointmentUrl, SITE);
      if (url.hostname==='coastalcprtraining.enrollware.com' && url.pathname==='/enroll') id=url.searchParams.get('id');
      if (url.origin===SITE && url.pathname==='/register/') id=url.searchParams.get('session');
    } catch { continue; }
    if (!id || !/^\d{4}-\d{2}-\d{2}$/.test(day.date) || !/^\d{2}:\d{2}$/.test(start.startTime)) continue;
    offers.push({externalId:id,localStart:day.date+'T'+start.startTime});
  }
  return offers;
}
export function localStart(instant) {
 const parts=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date(instant)).map(p=>[p.type,p.value]));
 return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}
export const validToken=token=>/^lw_r_[0-9a-f]{64}$/.test(token);
