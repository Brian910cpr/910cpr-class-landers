import{assertEquals}from'https://deno.land/std@0.224.0/assert/mod.ts';
import{isOperationalSession,projectOperationalSession}from'./projection.ts';

Deno.test('only proven committed lifecycle states enter the operational projection',()=>{
  for(const status of['scheduled','active','completed'])assertEquals(isOperationalSession({status}),true);
  for(const status of['proposed_window','draft','tentative','pending_proposal','canceled','deleted'])assertEquals(isOperationalSession({status}),false);
  assertEquals(isOperationalSession({status:'proposed_window',registration_status:'pending_details'}),false);
});

Deno.test('durable-only session projects names and truthful zero named registrations',()=>{
  const session={id:'little-leaps',status:'scheduled',course_id:'course-1',location_id:'location-1',lead_instructor_id:'person-1',start_at:'2026-09-19T15:00:00Z',end_at:'2026-09-19T18:00:00Z',max_students:5};
  const row=projectOperationalSession(session,new Map(),new Map([['course-1','AHA Heartsaver Pediatric First Aid CPR AED']]),new Map([['location-1','Little Leaps']]),new Map([['person-1','Brian Ennis']]));
  assertEquals([row.course_name,row.location_name,row.lead_instructor_name],['AHA Heartsaver Pediatric First Aid CPR AED','Little Leaps','Brian Ennis']);
  assertEquals(row.registered_count,0);
});
