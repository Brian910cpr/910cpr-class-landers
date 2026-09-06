const assert=require('node:assert/strict');
global.location={search:'',pathname:'/group-training.html'};
const ui=require('../docs/assets/group-training.js');
(async()=>{
 const core=await import('../supabase/functions/group-training/core.mjs');
 for(const [industry] of ui.INDUSTRIES){const recommendation=ui.recommend(industry);assert.ok(recommendation.name);assert.ok(recommendation.likely.length)}
 const expected={certified:['bls','first_aid','pediatric','acls','pals','hsi'],workplace:['first_aid','cpr_aed','hsi'],children:['pediatric','first_aid'],healthcare:['bls','acls','pals','first_aid'],complete:['first_aid','bls','pediatric','acls','pals','hsi']};
 for(const [program,courses] of Object.entries(expected)){assert.deepEqual(ui.courseOptions(program).map(x=>x.key),courses);for(const course of courses)assert.deepEqual(ui.availabilitySource(course),{family:ui.COURSES[course].family,pageKey:ui.COURSES[course].pageKey})}
 assert.equal(ui.availabilitySource('acls').pageKey,'acls');assert.equal(ui.availabilitySource('pals').pageKey,'pals');assert.notEqual(ui.availabilitySource('bls').pageKey,ui.availabilitySource('pediatric').pageKey);
 let selected='healthcare';assert.equal(ui.courseOptions(selected)[0].key,'bls');selected='workplace';assert.equal(ui.courseOptions(selected)[0].key,'first_aid');
 const candidate={courseId:'209809',courseName:'AHA Heartsaver First Aid CPR AED',courseFamily:'HEARTSAVER',publicSelectable:true,offerType:'private_candidate',availabilityBlockId:'free:1'};
 const source={schemaVersion:'selector-resolved-availability.v1',generatedAt:'now',pageKey:'heartsaver',dates:[{date:'2026-11-02',startTimes:[{startTime:'9:00 AM',courses:[candidate,{...candidate,courseId:'seat',offerType:'seated_class'}]}]}]};
 assert.equal(ui.flattenAvailability(source,'first_aid').length,1);assert.equal(ui.flattenAvailability(source,'bls').length,0);assert.equal(ui.flattenAvailability({...source,pageKey:'bls'},'first_aid').length,0);
 const submitted={date:'2026-11-02',startTime:'9:00 AM',courseId:'209809',availabilityBlockId:'free:1'};assert.ok(core.matchingCandidate(source,submitted,'first_aid'));assert.equal(core.matchingCandidate(source,{...submitted,courseId:'wrong'},'first_aid'),null);assert.equal(core.matchingCandidate(source,submitted,'pediatric'),null);
 const base={organizationType:'workplace',recommendedProgram:'workplace',selectedProgram:'workplace',selectedCourseKey:'first_aid',address:'1 Test St',organization:'Test Co',coordinator:'Alex Test',email:'a@example.com',phone:'9105550100',cohort:'initial',delivery:'in_person',market:'wilmington_nc',modules:[],headcount:10,reservationMode:'requires_confirmation',companyWebsite:''};
 assert.equal(core.validatePayload(base),null);assert.equal(core.validatePayload({...base,selectedCourseKey:'pals'}),'unsupported_program_course');assert.equal(core.validatePayload({...base,modules:['Not a real module']}),'invalid_modules');assert.equal(core.validatePayload({...base,market:'made_up'}),'invalid_selection');assert.equal(core.validatePayload({...base,companyWebsite:'bot.example'}),'bot_detected');
 assert.equal(core.publicError('payload_too_large')[1],413);assert.equal(core.publicError('rate_limited')[1],429);assert.doesNotMatch(core.publicError('database_secret_detail')[0],/database|secret/i);
 const a=ui.analyticsPayload('group_date_selected',{industry:'healthcare',market:'wilmington_nc',recommendedProgram:'healthcare',program:'healthcare',course:'bls',sourcePageType:'hub',email:'private@example.com',address:'private'});assert.deepEqual(Object.keys(a).sort(),['event','industry','market','recommended_program','reservation_mode','selected_course','selected_program','source_page_type'].sort());assert.doesNotMatch(JSON.stringify(a),/private|email|address|phone/i);
 assert.equal(core.MAX_BODY,32768);console.log('group training behavioral tests passed');
})().catch(error=>{console.error(error);process.exitCode=1});
