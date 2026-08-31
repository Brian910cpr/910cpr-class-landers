const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const Session=require('../docs/assets/session-workspace.js');

test('native session with participants uses durable count and canonical workspace',()=>{const row={session_id:'native-1',durable_session_id:'11111111-1111-1111-1111-111111111111',durable_participant_count:2};assert.equal(Session.participantLabel(row),'Participants (2)');assert.equal(Session.workspaceUrl(row),'https://www.910cpr.com/admin/session-workspace.html?sessionId=11111111-1111-1111-1111-111111111111&externalSessionId=native-1#participants')});
test('native zero-participant session displays a real zero',()=>assert.equal(Session.participantLabel({durable_participant_count:0}),'Participants (0)'));
test('Enrollware aggregate count does not claim roster availability',()=>assert.deepEqual(Session.participantState({registered_count:4,participant_count_available:true,participant_count_source:'enrollware_student_report'}),{count:4,available:true,rosterAvailable:false,source:'enrollware_student_report'}));
test('imported session without count displays unknown',()=>assert.equal(Session.participantLabel({source:'enrollware_ical',registered_count:null,participant_count_available:false}),'Participants (—)'));
test('canceled participant is excluded by canonical registration semantics',()=>assert.equal(Session.canonicalRegistrationCount([{status:'active'},{status:'canceled'}]),1));
test('walk-in participant is included',()=>assert.equal(Session.canonicalRegistrationCount([{status:'active',source:'walk_in'}]),1));
test('past and future sessions use the same canonical route',()=>{const base={session_id:'x',course_id:'bls'};assert.equal(Session.workspaceUrl({...base,start_at:'2026-01-01T09:00:00Z'}).replace('2026-01-01T09%3A00%3A00Z','DATE'),Session.workspaceUrl({...base,start_at:'2027-01-01T09:00:00Z'}).replace('2027-01-01T09%3A00%3A00Z','DATE'))});
test('ES and Dashboard both use the shared participant label and workspace resolver',()=>{for(const file of ['../docs/admin/schedule-reader.html','../docs/admin/dashboard.html']){const html=fs.readFileSync(require('node:path').join(__dirname,file),'utf8');assert.match(html,/session-workspace\.js\?v=20260829-1/);assert.match(html,/LanderWareSession\.participantLabel/);assert.match(html,/LanderWareSession\.workspaceUrl/)}});
test('session workspace API exposes a sanitized upcoming projection',()=>{const api=fs.readFileSync(require('node:path').join(__dirname,'../supabase/functions/session-workspace/index.ts'),'utf8');assert.match(api,/action==='projection'/);assert.match(api,/class_sessions\?start_at=gte/);assert.match(api,/registrations\?class_session_id=in/);assert.match(api,/registered_count:counts\.get\(session\.id\)\|\|0/)});
