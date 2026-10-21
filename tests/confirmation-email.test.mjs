import test from 'node:test';
import assert from 'node:assert/strict';
import {confirmationHtml} from '../supabase/functions/registration-reschedule/confirmation-email.mjs';
test('confirmation uses escaped current details, graphic, personal link, fallback and closing order',()=>{
 const link='https://www.910cpr.com/reschedule/#lw_r_'+'a'.repeat(64);
 const html=confirmationHtml(`Hi <Student>,\n\nYour class is confirmed.\n\nCourse & classroom\nFriday at 9 AM\n\nChoose a new class time: ${link}\n\nWe look forward to seeing you!\n\nBrian`);
 assert.ok(html.includes('&lt;Student&gt;'));assert.ok(html.includes('Course &amp; classroom'));assert.equal((html.match(new RegExp(link,'g'))||[]).length,2);
 assert.ok(html.includes('prefers-color-scheme:dark'));assert.ok(html.includes('[data-ogsc]'));assert.ok(html.indexOf('Choose a new class time</a>')<html.indexOf('We look forward to seeing you!'));
 assert.equal(confirmationHtml('Rescheduling help requested'),undefined);
 assert.ok(!confirmationHtml('Your class is confirmed.\n\nhttps://evil.example').includes('reschedule-button" href='));
});
