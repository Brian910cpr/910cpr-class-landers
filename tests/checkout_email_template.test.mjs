import test from 'node:test';
import assert from 'node:assert/strict';
import {renderCheckoutEmail} from '../worker/checkout-email-template.mjs';
const sample={firstName:'Synthetic Student',course:'AHA BLS Provider Renewal',courseId:'359474',startsAt:'2026-10-24T14:00:00Z',endsAt:'2026-10-24T16:00:00Z',venue:'910CPR Office - Shipyard Blvd',address:'4018 Shipyard Blvd, Room B, Wilmington, NC, 28403',selectedOptions:[]};
test('customer confirmation uses Eastern class time, full recorded address, help and no operational IDs',()=>{
 const r=renderCheckoutEmail({...sample,orderId:'private-order-id',registrationId:'private-registration-id'});
 assert.match(r.text,/Saturday, October 24, 2026/);assert.match(r.text,/10:00 AM–12:00 PM Eastern/);
 assert.match(r.html,/4018 Shipyard Blvd/);assert.match(r.html,/Get directions/);assert.match(r.text,/910-395-5193/);
 assert.match(r.text,/2025 AHA BLS Student Manual/);assert.doesNotMatch(r.text+r.html,/private-order|private-registration|America\/New_York/);
});
test('DST and escaping are correct; unverified addresses do not produce invented directions',()=>{
 const r=renderCheckoutEmail({...sample,firstName:'<img src=x>',startsAt:'2026-11-24T15:00:00Z',endsAt:null,address:null});
 assert.match(r.text,/10:00 AM Eastern/);assert.match(r.html,/&lt;img src=x&gt;/);assert.doesNotMatch(r.html,/Get directions/);
 assert.throws(()=>renderCheckoutEmail({...sample,startsAt:'2026-10-24T10:00:00'}),/class_data_missing/);
});
test('only purchased online access or eManual produces fulfillment wording; skills-only never promises a code',()=>{
 const own=renderCheckoutEmail({...sample,courseId:'210549',selectedOptions:[]});assert.match(own.text,/skills session only/);assert.doesNotMatch(own.text,/manually provides/);
 const online=renderCheckoutEmail({...sample,courseId:'210549',selectedOptions:[{key:'aha_heartcode_bls_online',display_name:'HeartCode BLS online'}]});assert.match(online.text,/manually provides/);
 const ebook=renderCheckoutEmail({...sample,selectedOptions:[{key:'aha_bls_provider_manual_ebook',display_name:'BLS eManual'}]});assert.match(ebook.text,/provided? |provide the purchased/);assert.doesNotMatch(ebook.text,/Have your current/);
 const reminder=renderCheckoutEmail({...sample,kind:'reminder'});assert.match(reminder.subject,/Class reminder/);assert.doesNotMatch(reminder.text,/Payment received/);
});
test('recovery has a bounded canonical checkout link and never claims payment or confirmation',()=>{
 const data={...sample,kind:'recovery',recoveryUrl:'https://www.910cpr.com/register/?recover=00000000-0000-4000-8000-000000000001',holdExpiresAt:'2026-10-24T13:30:00Z'};
 const r=renderCheckoutEmail(data);assert.match(r.subject,/Finish your registration/);assert.match(r.html,/Return to checkout/);assert.match(r.text,/9:30 AM Eastern/);assert.doesNotMatch(r.text,/Payment received|You’re registered/);
 assert.throws(()=>renderCheckoutEmail({...data,recoveryUrl:'https://evil.example/register/?recover=00000000-0000-4000-8000-000000000001'}),/recovery_data_invalid/);
});

 test('completion eCards, optional purchases and reschedule calendar stay distinct',()=>{
 const base=renderCheckoutEmail(sample);
 assert.match(base.text,/American Heart Association BLS Provider eCard/);
 assert.match(base.text,/after successful completion/);
 assert.match(base.html,/https:\/\/www.910cpr.com\/bls.html#date-list/);
 assert.match(base.text,/Do not register or pay again/);
 assert.doesNotMatch(base.html,/Options you selected|Heartsaver First Aid eCard/);
 const extra=renderCheckoutEmail({...sample,selectedOptions:[{key:'aha_bls_provider_manual_ebook',display_name:'BLS eManual'},{key:'aha_heartsaver_first_aid_online',display_name:'Online First Aid'}]});
 assert.match(extra.html,/Options you selected — optional purchases/);
 assert.match(extra.text,/Heartsaver First Aid eCard/);
 assert.doesNotMatch(extra.html,/Included with your registration/);
 const unknown=renderCheckoutEmail({...sample,courseId:'unknown'});
 assert.doesNotMatch(unknown.html,/BLS Provider eCard|View reschedule calendar/);
 });
