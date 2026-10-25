const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const zone = 'America/New_York';

export function renderCheckoutEmail(data) {
  const start = new Date(data.startsAt), end = data.endsAt ? new Date(data.endsAt) : null;
  if (!data.course || !Number.isFinite(start.getTime()) || !/[zZ]|[+-]\d\d:\d\d$/.test(data.startsAt)) throw Error('confirmation_class_data_missing');
  const date = new Intl.DateTimeFormat('en-US',{timeZone:zone,weekday:'long',month:'long',day:'numeric',year:'numeric'}).format(start);
  const time = d => new Intl.DateTimeFormat('en-US',{timeZone:zone,hour:'numeric',minute:'2-digit'}).format(d);
  const when = `${time(start)}${end && Number.isFinite(end.getTime()) ? `–${time(end)}` : ''} Eastern`;
  const reminder = data.kind === 'reminder';
  const recovery = data.kind === 'recovery';
  let recoveryUrl = '', holdNote = '';
  if (recovery) {
    const url = new URL(data.recoveryUrl);
    const expires = new Date(data.holdExpiresAt);
    if (url.origin !== 'https://www.910cpr.com' || url.pathname !== '/register/' || !/^[0-9a-f-]{36}$/i.test(url.searchParams.get('recover') || '') || !Number.isFinite(expires.getTime())) throw Error('recovery_data_invalid');
    recoveryUrl = url.href;
    holdNote = `Your current seat hold expires at ${time(expires)} Eastern. Availability is checked again when you return.`;
  }
  const options = Array.isArray(data.selectedOptions) ? data.selectedOptions : [];
  const keys = new Set(options.map(o => o.key));
  const preparation = [];
  if (['209806','359474'].includes(String(data.courseId))) {
    preparation.push(keys.has('aha_bls_provider_manual_ebook') ?
      'You selected the optional BLS eManual purchase. 910CPR will provide the purchased digital material separately; it is not attached to this confirmation.' :
      'Have your current 2025 AHA BLS Student Manual available for class.');
  }
  if (String(data.courseId) === '210549') {
    preparation.push(keys.has('aha_heartcode_bls_online') ?
      'Your HeartCode online course and skills session are included. 910CPR manually provides your online course access separately. Complete the online course before your skills session.' :
      'This registration covers the skills session only. Complete your applicable AHA online course before your skills session.');
  }
  if (keys.has('aha_heartsaver_first_aid_online')) preparation.push('Your online First Aid option includes its student eBook and in-person skills testing during your selected class time. Complete the online program before class; 910CPR provides purchased access separately.');
  if (keys.has('aha_heartsaver_first_aid_in_person')) {
    preparation.push('You selected the optional in-person First Aid add-on during your selected class time.');
    preparation.push(keys.has('aha_heartsaver_first_aid_manual_ebook') ?
      'Your purchased Heartsaver student eBook will be provided separately by 910CPR.' :
      'Have your current 2025 AHA Heartsaver Student Manual available for the in-person First Aid portion.');
  }
  const productNames = options.map(o => o.display_name || o.name).filter(Boolean);
  // This release supports only the verified BLS course identities; do not guess other credentials.
  const bls = ['209806','359474','210549'].includes(String(data.courseId));
  const credentials = bls ? ['American Heart Association BLS Provider eCard'] : [];
  if (bls && (keys.has('aha_heartsaver_first_aid_online') || keys.has('aha_heartsaver_first_aid_in_person'))) credentials.push('American Heart Association Heartsaver First Aid eCard (selected First Aid option)');
  const completion = 'Issued after successful completion of the applicable course requirements; this email is not your eCard.';
  const rescheduleUrl = bls && !recovery ? 'https://www.910cpr.com/bls.html#date-list' : null;
  const rescheduleNote = 'View the calendar to choose another date or time, then reply to this email or call us to complete your reschedule. Do not register or pay again to change this booking.';
  const address = String(data.address || '').trim();
  const venue = data.venue || 'Contact 910CPR to confirm your class location';
  const directions = address ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}` : null;
  const heading = recovery ? 'Your class is selected. Finish registration.' : reminder ? 'Your class is coming up' : 'You’re registered. We’ll see you in class.';
  const payment = reminder ? null : recovery ? 'Finish checkout to confirm your seat. If you already paid, do not pay again; contact us if your confirmation has not arrived.' : 'Payment received. Your Stripe payment receipt is separate.';
  const help = 'Need to change or cancel, or have a question? Reply to this email or call 910-395-5193. Please include your name and class date.';
  const lines = [`Hi ${data.firstName || 'there'},`, '', heading, '', data.course, date, when, venue, address,
    directions && `Directions: ${directions}`, '', payment, recovery && holdNote, recovery && `Return to checkout: ${recoveryUrl}`,
    credentials.length && `Your course completion eCard: ${credentials.join('; ')}`, credentials.length && completion,
    productNames.length && `Options you selected (optional purchases): ${productNames.join('; ')}`,
    rescheduleUrl && `Reschedule calendar: ${rescheduleUrl}`, rescheduleUrl && rescheduleNote, '', 'Before class',
    ...preparation.map(p => `• ${p}`), ...(!preparation.length ? ['Contact 910CPR if you need help with preparation for your selected course.'] : []), '', help, '', '910CPR'];
  const text = lines.filter(v => v !== null && v !== false && v !== 0).join('\n');
  const section = (title,content) => `<h2 style="font-size:18px;margin:24px 0 10px;color:#15364b">${title}</h2>${content}`;
  let html = `<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="margin:0;background:#eef3f5;font-family:Arial,sans-serif;color:#243b49"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="padding:24px 12px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:620px;margin:auto;background:white;border-radius:14px;overflow:hidden"><tr><td style="background:#15364b;color:white;padding:24px 28px;font-size:25px;font-weight:bold">910CPR <span style="font-size:13px;font-weight:normal">CLASS ${recovery?'CHECKOUT':reminder?'REMINDER':'CONFIRMATION'}</span></td></tr><tr><td style="padding:28px;line-height:1.6"><p style="margin-top:0">Hi ${escape(data.firstName || 'there')},</p><h1 style="font-size:27px;line-height:1.25;color:#15364b">${heading}</h1><div style="padding:20px;background:#edf6f7;border-left:4px solid #168080;border-radius:8px"><strong style="font-size:20px">${escape(data.course)}</strong><p style="margin-bottom:0">${escape(date)}<br><strong>${escape(when)}</strong></p></div>${section('Where to go',`<strong>${escape(venue)}</strong>${address?`<p>${escape(address)}</p><a href="${escape(directions)}" style="display:inline-block;background:#16777c;color:white;padding:10px 18px;border-radius:6px;text-decoration:none">Get directions</a>`:'<p>Please contact us to confirm the address before traveling.</p>'}`)}${payment?`<p>${payment}</p>`:''}${credentials.length?section('Your course completion eCard',`<ul>${credentials.map(n=>`<li>${escape(n)}</li>`).join('')}</ul><p>${completion}</p>`):''}${productNames.length?section('Options you selected — optional purchases',`<ul>${productNames.map(n=>`<li>${escape(n)}</li>`).join('')}</ul>`):''}${section('Before class',`<ul>${(preparation.length?preparation:['Contact 910CPR if you need help preparing for your selected course.']).map(p=>`<li>${escape(p)}</li>`).join('')}</ul>`)}${rescheduleUrl?section('Need to reschedule?',`<a href="${escape(rescheduleUrl)}" style="display:inline-block;background:#16777c;color:white;padding:10px 18px;border-radius:6px;text-decoration:none">View reschedule calendar</a><p>${rescheduleNote}</p>`):''}${section('We’re here to help',`<p>${help}</p><a href="tel:+19103955193" style="color:#116b72;font-weight:bold">910-395-5193</a>`)}</td></tr><tr><td style="padding:18px 28px;background:#f5f7f8;font-size:12px;color:#536873">Keep this email with your class details. Thank you for choosing 910CPR.</td></tr></table></td></tr></table></body></html>`;
  if (recovery) html = html.replace(`<p>${payment}</p>`,`<p>${payment}</p><p>${escape(holdNote)}</p><a href="${escape(recoveryUrl)}" style="display:inline-block;background:#16777c;color:white;padding:12px 20px;border-radius:6px;text-decoration:none">Return to checkout</a>`);
  return {subject:`${recovery?'Finish your registration':reminder?'Class reminder':'You’re registered'} — ${data.course}`,text,html};
}
