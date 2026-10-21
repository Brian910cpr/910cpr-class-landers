import test from 'node:test';
import assert from 'node:assert/strict';
import {unresolvedCommitments} from '../supabase/functions/registration-reschedule/commitment-lookup.mjs';
const person={id:'person-1',current_first_name:'Test',current_last_name:'Student'};
const appointment=(extra={})=>({id:'registration-1',status:'active',session:{id:'session-1',class_session_id:null,course_name:'Skills',starts_at:'2026-10-21T11:45:00Z',lifecycle_state:'scheduled',requirements_manifest:{suppress_outbound_until_location_verified:true},...extra}});
test('saved appointment is visible without customer or operational session; retains stable IDs and suppression',async()=>{
 const calls=[];const rows=await unresolvedCommitments('student@example.invalid',async path=>{calls.push(path);return path.startsWith('landerware_people?')?[person]:[appointment()];});
 assert.equal(rows.length,1);assert.equal(rows[0].workspaceSessionId,'session-1');assert.equal(rows[0].personId,'person-1');assert.equal(rows[0].workspaceRegistrationId,'registration-1');assert.equal(rows[0].outboundSuppressed,true);assert.equal(rows[0].locationRequiresVerification,true);assert.equal(rows[0].id,undefined);
 assert.ok(calls.every(p=>!p.includes('starts_at=gt.')),'past unresolved appointments must not disappear after their start time');
});
test('linked bookings, proposals and terminal sessions are not actionable reconciliation candidates',async()=>{
 const states=['proposed','draft','tentative','pending_proposal','cancelled','canceled','completed'];
 const rows=await unresolvedCommitments('student@example.invalid',async p=>p.startsWith('landerware_people?')?[person]:[appointment({class_session_id:'operational-1'}),...states.map(lifecycle_state=>appointment({lifecycle_state}))]);assert.deepEqual(rows,[]);
});
test('lookup fails visibly on source error or possible truncation',async()=>{
 await assert.rejects(unresolvedCommitments('student@example.invalid',async()=>{throw Error('source unavailable');}),/source unavailable/);
 await assert.rejects(unresolvedCommitments('student@example.invalid',async p=>p.startsWith('landerware_people?')?[person]:Array.from({length:100},()=>appointment())),/incomplete/);
});
test('email underscore is literal and lookups perform reads only',async()=>{
 const paths=[];await unresolvedCommitments('a_b@example.invalid',async (...args)=>{assert.equal(args.length,1);paths.push(args[0]);return [];});assert.ok(paths[0].includes('a%5C_b%40example.invalid'));
});
