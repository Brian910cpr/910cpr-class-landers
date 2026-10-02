const test=require("node:test");const assert=require("node:assert/strict");
const {calculate,dayBounds}=require("../docs/admin/open-shift-model.js");
const realPolicy=require("../docs/admin/open-shift-policy.js");
const date="2026-10-05", now=new Date("2026-10-01T00:00:00Z");
const time=(clock,day=date)=>new Date(day+"T"+clock+":00-04:00");
function policy(){return {timezone:"America/New_York",maxSourceAgeMinutes:30,minimumLeadMinutes:0,cleanupMinutes:0,
  instructors:[{instructor_key:"brian",display_name:"Brian",aliases:["Brian Ennis"],allowed_course_groups:["BLS","Heartsaver","ARC","HSI"],calendar_source_key:"brian_blocks"}],
  sources:[{calendar_source_key:"brian_blocks",instructor_key:"brian",mode:"inverse_blocking",active:true,default_location_key:"shipyard"}],
  locations:[{location_key:"shipyard",canonical_public_location:"Shipyard",aliases:[],resources:[]}],
  travel:{instructor_key:"brian",unknown_offsite_minutes:90,rules:[]},containers:[{container_id:"fixture",status:"active",instructor_name:"Brian",location_name:"Shipyard",first_valid_date:"2026-01-01",last_valid_date:"2027-01-01"}],
  occupancyMinutes:{bls:60,full:180},shortSkills:[{id:"bls",name:"BLS",family:"BLS",minutes:60},{id:"hs",name:"Heartsaver",family:"Heartsaver",minutes:60},{id:"arc",name:"ARC",family:"ARC",minutes:45},{id:"hsi",name:"HSI",family:"HSI",minutes:45}]};}
const status=[{source_key:"brian_blocks",export_status:"ok",generated_at:now.toISOString()}];
const session=(id,start,end,course="bls",day=date)=>({session_id:id,course_id:course,start_at:time(start,day).toISOString(),end_at:time(end,day).toISOString(),lead_instructor_name:"Brian",location_name:"Shipyard"});
const run=(sessions=[],extra={})=>calculate({date,sessions,policy:policy(),now,sourceStatus:status,...extra});
test("real chain grows at both edges; four skills categories considered before constraints",()=>{
  const cases=[[[session("noon","12:00","12:00")],["11:00","13:00"]],[[session("noon","12:00","13:00"),session("right","13:00","14:00")],["11:00","14:00"]],[[session("left","11:00","12:00"),session("noon","12:00","14:00")],["10:00","14:00"]],[[session("left","11:00","14:00"),session("full","14:00","17:00","full")],["10:00","17:00"]]];
  for(const [sessions,expected] of cases){const r=run(sessions);assert.deepEqual(r.accepted.filter(c=>c.courseId==="bls").map(c=>+c.start),expected.map(c=>+time(c)));assert.equal(r.freeIntervals.length,0);for(const e of r.edges)assert.deepEqual(new Set(r.candidates.filter(c=>c.edgeIds.includes(e.id)).map(c=>c.courseId)),new Set(["bls","hs","arc","hsi"]));}
});
test("multiple real blocks do not scatter free starts and skills repeat",()=>{const r=run([session("a","12:00","13:00"),session("b","18:00","19:00")]);assert.equal(r.blocks.length,2);assert.equal(r.freeIntervals.length,0);assert.equal(r.accepted.filter(c=>c.courseId==="bls").length,4);});
test("speculative accepted choices never mutate source or create gravity",()=>{const input=[];const r=run(input);assert.equal(input.length,0);assert.equal(r.blocks.length,0);assert.equal(r.accepted.length,run(input).accepted.length);assert.ok(r.candidates.every(c=>c.mode==="free"));});
test("wide free days have hourly spacing including midnight",()=>{const r=run();assert.equal(r.freeIntervals[0].stepMinutes,60);assert.equal(r.accepted.filter(c=>c.courseId==="bls").length,24);assert.equal(+r.accepted[0].start,+dayBounds(date).start);});
test("tight intervals use half-hour spacing",()=>{const p=policy();p.sources[0].mode="explicit_availability";const r=run([],{policy:p,events:[{source_key:"brian_blocks",title:"HARD",start:time("04:00"),end:time("06:00")} ]});assert.equal(r.freeIntervals[0].stepMinutes,30);assert.equal(r.accepted.filter(c=>c.courseId==="bls").length,3);});
test("cross-midnight classes block the next day and remain planted",()=>{const s=session("night","23:30","23:30","bls","2026-10-04");s.end_at=time("00:30").toISOString();const r=run([s]);assert.equal(r.blocks.length,1);assert.equal(r.freeIntervals.length,0);assert.deepEqual(r.accepted.filter(c=>c.courseId==="bls").map(c=>+c.start),[+time("00:30")]);});
test("offsite travel blocks adjacent edge choices",()=>{const r=run([session("a","12:00","13:00")],{events:[{source_key:"brian_blocks",title:"Hold",start:time("14:00"),end:time("15:00"),location:"Offsite"}]});assert.ok(r.rejected.some(c=>c.courseId==="bls"&&c.start.getTime()===+time("13:00")&&c.reasons.some(x=>x.startsWith("occupied_or_travel"))));});
test("intervening holds prevent cleanup merging",()=>{const p=policy();p.cleanupMinutes=10;const r=run([session("a","12:00","13:00"),session("b","13:10","14:10")],{policy:p,events:[{source_key:"brian_blocks",title:"hold",start:time("13:01"),end:time("13:09"),location:"Shipyard"}]});assert.equal(r.blocks.length,2);});
test("unknown equal-end duration fails closed rather than inventing a free day",()=>{const r=run([session("unknown","12:00","12:00","missing")]);assert.equal(r.accepted.length,0);assert.ok(r.diagnostics.some(d=>d.code==="unresolved_occupancy_duration"));});
test("stale source suppresses apparent availability",()=>{const r=run([],{sourceStatus:[{...status[0],generated_at:"2026-09-01T00:00:00Z"}]});assert.equal(r.accepted.length,0);assert.ok(r.diagnostics.some(d=>d.code==="availability_source_stale_or_failed"));});
test("personal calendars do not indiscriminately block work",()=>{const p=policy();p.sources.push({calendar_source_key:"personal",instructor_key:"brian",active:true,mode:"occupancy"});const r=run([],{policy:p,events:[{source_key:"personal",title:"Personal event",start:time("12:00"),end:time("14:00")} ]});assert.equal(r.occupied.length,0);assert.equal(r.blocks.length,0);});
test("course qualification and duration constraints apply after candidates",()=>{const p=policy();p.instructors[0].allowed_course_groups=["BLS","ARC"];p.shortSkills[1].durationConflict=true;const r=run([session("a","12:00","13:00")],{policy:p});assert.equal(r.candidates.length,8);assert.ok(r.rejected.some(c=>c.courseId==="hs"&&c.reasons.includes("unresolved_course_duration")));assert.ok(r.rejected.some(c=>c.courseId==="hsi"&&c.reasons.includes("instructor_not_qualified")));});
test("owner authority resolves short-skills timing and excludes ACLS/PALS",()=>{assert.ok(realPolicy.shortSkills.filter(c=>c.family==="Heartsaver").every(c=>!c.durationConflict&&c.minutes===60&&c.instructionMinutes===45&&c.cleanupMinutes===15&&c.ruleMinutes===45&&c.catalogMinutes===45));assert.ok(realPolicy.shortSkills.every(c=>!["209811","209812"].includes(c.id)));});
test("business-day boundaries honor DST instead of browser timezone",()=>{assert.equal((dayBounds("2026-11-01").end-dayBounds("2026-11-01").start)/3600000,25);assert.equal((dayBounds("2026-03-08").end-dayBounds("2026-03-08").start)/3600000,23);});

test("explicit overnight availability can finish after midnight",()=>{const p=policy();p.sources[0].mode="explicit_availability";const r=run([],{policy:p,events:[{source_key:"brian_blocks",title:"HARD",start:time("23:30"),end:time("01:00","2026-10-06")}]});assert.ok(r.accepted.some(c=>c.courseId==="bls"&&+c.start===+time("23:30")&&+c.end>+dayBounds(date).end));});
test("a real next-day blocker rejects cross-midnight consumption",()=>{const p=policy();p.sources[0].mode="explicit_availability";const r=run([],{policy:p,events:[{source_key:"brian_blocks",title:"HARD",start:time("23:30"),end:time("01:00","2026-10-06")},{source_key:"brian_blocks",title:"UNAVAILABLE",start:time("00:00","2026-10-06"),end:time("01:00","2026-10-06"),location:"Shipyard"}]});assert.equal(r.accepted.length,0);});
test("paid block ending exactly midnight retains its next-day right edge",()=>{const s=session("night","23:00","23:00","bls","2026-10-04");s.end_at=time("00:00").toISOString();const r=run([s]);assert.equal(r.freeIntervals.length,0);assert.ok(r.accepted.some(c=>c.courseId==="bls"&&+c.start===+time("00:00")));});

test("a failed or stale schedule source cannot prove an opening",()=>{const r=run([],{scheduleHealth:{generatedAt:"2026-09-01T00:00:00Z",failed:false}});assert.equal(r.accepted.length,0);assert.ok(r.diagnostics.some(d=>d.code==="schedule_source_stale_or_failed"));});
test("another instructor's class in the same physical venue blocks colliding suggestions",()=>{const other=session("other","12:00","13:00");other.lead_instructor_name="Amy";const p=policy();p.instructors.push({instructor_key:"amy",display_name:"Amy",aliases:[],calendar_source_key:"none",allowed_course_groups:[]});const r=run([other],{policy:p});assert.ok(r.rejected.some(c=>c.courseId==="bls"&&+c.start===+time("12:00")&&c.reasons.includes("location_conflict:other")));});
test("explicit source duration metadata resolves equal-end import without guessing IDs",()=>{const source=session("metadata","12:00","12:00","missing");source.inferred_scheduler_consumption_minutes=90;const r=run([source]);assert.equal(r.blocks[0].end.getTime(),+time("13:30"));});
test("unresolved prior-night occupancy cannot leak next-day free offers",()=>{const source=session("unknown-night","23:30","23:30","missing","2026-10-04");const r=run([source]);assert.equal(r.accepted.length,0);assert.ok(r.diagnostics.some(d=>d.code==="unresolved_occupancy_duration"));});

test("unbooked full classes are generated at edges then booking grows the block",()=>{
  const p=policy();p.fullCourses=[{id:"full",name:"Full BLS",family:"BLS",kind:"full",minutes:180}];p.fullBarnaclesPerFamilyDay=1;
  const source=[session("noon","12:00","13:00")];const before=run(source,{policy:p});
  const fullCandidates=before.candidates.filter(c=>c.kind==="full");
  assert.deepEqual(fullCandidates.map(c=>+c.start),[+time("09:00"),+time("13:00")]);
  const full=before.accepted.find(c=>c.kind==="full");assert.ok(full);assert.equal(+full.end,+time("12:00"));
  assert.equal(before.accepted.filter(c=>c.kind==="full").length,1);
  assert.ok(before.rejected.some(c=>c.kind==="full"&&c.reasons.includes("full_family_barnacle_limit")));
  assert.equal(before.blocks[0].sourceIds.length,1); // hypothetical full offer has no gravity
  source.push({session_id:"booked-full",course_id:"full",start_at:full.start.toISOString(),end_at:full.end.toISOString(),lead_instructor_name:"Brian",location_name:"Shipyard"});
  const after=run(source,{policy:p});assert.equal(after.blocks.length,1);assert.equal(+after.blocks[0].start,+time("09:00"));
  assert.deepEqual(after.accepted.filter(c=>c.courseId==="bls").map(c=>+c.start),[+time("08:00"),+time("13:00")]);
  assert.ok(after.accepted.some(c=>c.kind==="full"&&+c.start===+time("06:00")));
});
test("full family limits and qualifications never sterilize repeatable skills",()=>{
  const p=policy();p.fullCourses=[{id:"full",name:"Full BLS",family:"BLS",kind:"full",minutes:180},{id:"advanced",name:"Advanced full",family:"ACLS",kind:"full",minutes:240}];
  const r=run([session("a","12:00","13:00"),session("b","18:00","19:00")],{policy:p});
  assert.equal(r.accepted.filter(c=>c.kind==="full").length,1);
  assert.equal(r.accepted.filter(c=>c.courseId==="bls").length,4);
  assert.ok(r.rejected.filter(c=>c.courseId==="advanced").every(c=>c.reasons.includes("instructor_not_qualified")));
  assert.equal(r.candidates.filter(c=>c.courseId==="advanced").length,4);
});

test("actual mapped BLS full-class edge offer can be booked and grow the block",()=>{
  const actualStatus=realPolicy.sources.map(s=>({source_key:s.calendar_source_key,export_status:"ok",generated_at:now.toISOString()}));
  const source={session_id:"actual-noon",course_id:"210549",start_at:time("12:00").toISOString(),end_at:time("13:00").toISOString(),lead_instructor_name:"Brian",location_name:":: Wilmington; Shipyard Blvd"};
  const inputs={date,sessions:[source],policy:realPolicy,now,sourceStatus:actualStatus};
  const before=calculate(inputs),full=before.accepted.find(c=>c.courseId==="209806");
  assert.ok(full);assert.equal(+full.start,+time("09:30"));assert.equal(+full.instructionEnd,+time("11:30"));assert.equal(+full.cleanupEnd,+time("12:00"));
  inputs.sessions.push({...source,session_id:"booked-provider",course_id:"209806",start_at:full.start.toISOString(),end_at:full.end.toISOString()});
  const after=calculate(inputs);assert.equal(after.blocks.length,1);assert.equal(+after.blocks[0].start,+time("09:30"));
  assert.deepEqual(after.accepted.filter(c=>c.courseId==="210549").map(c=>+c.start),[+time("08:30"),+time("13:00")]);
  assert.ok(after.candidates.some(c=>c.kind==="full"&&+c.start===+time("07:00")));
});
test("full edge consumption across midnight sees real next-day commitments",()=>{
  const p=policy();p.fullCourses=[{id:"full",name:"Full",family:"BLS",kind:"full",minutes:180}];
  const r=run([session("evening","20:00","23:00")],{policy:p,events:[{source_key:"brian_blocks",title:"hold",start:time("01:30","2026-10-06"),end:time("03:00","2026-10-06"),location:"Shipyard"}]});
  const right=r.candidates.find(c=>c.courseId==="full"&&+c.start===+time("23:00"));assert.ok(right);
  assert.ok(right.reasons.some(x=>x.startsWith("occupied_or_travel")));assert.ok(r.accepted.some(c=>c.courseId==="bls"&&+c.start===+time("23:00")));
});

test("Friday real bookings retain starts and expose cleanup collision without new overlap",()=>{
  const actualStatus=realPolicy.sources.map(s=>({source_key:s.calendar_source_key,export_status:"ok",generated_at:now.toISOString()}));
  const rows=[{session_id:"friday-renewal",course_id:"359474",start_at:time("10:45").toISOString(),end_at:time("12:45").toISOString(),lead_instructor_name:"Brian",location_name:":: Wilmington; Shipyard Blvd"},{session_id:"friday-initial",course_id:"209806",start_at:time("12:45").toISOString(),end_at:time("14:45").toISOString(),lead_instructor_name:"Brian",location_name:":: Wilmington; Shipyard Blvd"}];
  const before=JSON.stringify(rows),r=calculate({date,sessions:rows,policy:realPolicy,now,sourceStatus:actualStatus});
  assert.equal(JSON.stringify(rows),before);assert.equal(+r.occupied[0].instructionEnd,+time("12:45"));assert.equal(+r.occupied[0].cleanupEnd,+time("13:15"));
  assert.equal(+r.blocks[0].end,+time("15:15"));assert.ok(r.diagnostics.some(d=>d.code==="existing_commitment_or_cleanup_overlap"));
  for(const c of r.accepted)assert.ok(c.end<=time("10:45")||c.start>=time("15:15"));
});
test("Saturday short source end cannot erase 45+15 consumption or the Family class",()=>{
  const actualStatus=realPolicy.sources.map(s=>({source_key:s.calendar_source_key,export_status:"ok",generated_at:now.toISOString()}));
  const rows=[{session_id:"sat-heartcode",course_id:"210549",start_at:time("12:30").toISOString(),end_at:time("13:00").toISOString(),lead_instructor_name:"Brian",location_name:":: Wilmington; Shipyard Blvd"},{session_id:"sat-family",course_id:"252737",start_at:time("13:00").toISOString(),end_at:time("14:45").toISOString(),lead_instructor_name:"Brian",location_name:":: Wilmington; Shipyard Blvd"}];
  const r=calculate({date,sessions:rows,policy:realPolicy,now,sourceStatus:actualStatus});
  assert.equal(r.occupied.length,2);assert.equal(+r.occupied[0].instructionEnd,+time("13:15"));assert.equal(+r.occupied[0].cleanupEnd,+time("13:30"));
  assert.ok(r.diagnostics.some(d=>d.code==="existing_commitment_or_cleanup_overlap"));assert.ok(r.diagnostics.some(d=>d.code==="source_end_differs_from_owner_timing"));
});
test("cleanup boundaries are not double-counted when an offer becomes a session",()=>{
  const row={course_id:"210549",start_at:time("12:00").toISOString(),instruction_end_at:time("12:45").toISOString(),cleanup_end_at:time("13:00").toISOString(),end_at:time("13:00").toISOString()};
  const interval=require("../docs/admin/open-shift-model.js").sessionInterval(row,realPolicy);assert.equal(+interval.instructionEnd,+time("12:45"));assert.equal(+interval.cleanupEnd,+time("13:00"));assert.equal(+interval.occupiedEnd,+time("13:00"));
});
