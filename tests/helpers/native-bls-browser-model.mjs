// Synthetic stdin only. Execute the real generic model; never reserve or send.
import {genericCheckout} from '../../supabase/functions/public-registration/generic.mjs';
let text=''; for await (const chunk of process.stdin) text+=chunk;
const input=JSON.parse(text), calls=[];
const profile={profile_key:'native_skills_shared',version:2,course_id:'skills-session-only',display_name:'Skills Session',active:true,requirements:[],form_schema:{
 schemaVersion:'native-checkout.form.v1',inventory_kind:'leased_skills_v1',allowed_contexts:['bls-skills'],max_students:2,
 fields:[{key:'first_name',label:'First name',wire:'firstName',type:'text',required:true},{key:'last_name',label:'Last name',wire:'lastName',type:'text',required:true},{key:'email',label:'Email',wire:'email',type:'email',required:true},
 {key:'online_completed',label:'Online completed',wire:'onlineCompleted',type:'checkbox',required:true,unless_choice:'online_and_skills'},
 {key:'online_ack',label:'Complete online before class',wire:'onlineCompletionAcknowledged',type:'checkbox',required:true,when_choice:'online_and_skills'}],
 option_groups:[{key:'learning_path',label:'Learning path',type:'radio',required:true,choices:[
 {key:'skills_only',label:'Skills only',catalog_keys:[],bindings:{learningPath:'skills-only'}},
 {key:'online_and_skills',label:'HeartCode online access + skills',contexts:['bls-skills'],catalog_keys:['aha_heartcode_bls_online'],bindings:{learningPath:'online-and-skills'}}]}],
 default_choices:['skills_only'],driver_rules:[{driver:'native_order'}],public_aliases:[{public_course_id:'210549',context:'bls-skills',default_choices:['online_and_skills'],title:'HeartCode BLS online access + skills session'}]}};
const catalog={course_id:'509474',unit_amount:5500,currency:'usd',addons:[{key:'aha_heartcode_bls_online',unit_amount:4000,active:input.bundleEnabled!==false}]};
const saved={status:'held',kind:'public_order',orderId:'synthetic-saved55',amountCents:5500,currency:'usd',
 startsAt:new Date(Date.parse(input.now)+86400000).toISOString(),endsAt:new Date(Date.parse(input.now)+89100000).toISOString(),
 holdExpiresAt:new Date(Date.parse(input.now)+600000).toISOString(),location:'Synthetic fixture room',students:[{}],
 profileSnapshot:{profile,catalog,physicalCourseId:'509474',context:'bls-skills',selection:{offerId:'skills:legacy55'},inputs:[{selectedChoices:['skills_only']}]}};
const api=genericCheckout({verify:async()=>{},now:()=>Date.parse(input.now),publication:async()=>input.feed,catalog:async()=>catalog,
 skillsPolicy:async()=>({nativePublicationEnabled:false}),blsSkillsPolicy:async()=>({skillsEnabled:input.skillsEnabled!==false,bundleEnabled:input.bundleEnabled!==false,profileVersion:2}),
 rpc:async(name,args)=>{
  calls.push({name,args});
  if(name==='native_checkout_receipt'&&input.saved)return saved;
  if(name==='native_checkout_profile')return {profile,physicalCourseId:'509474'};
  if(name==='native_checkout_release_abandoned')return 0;
  if(name==='skills_session_native_option')return {capacity:2,targetSessionId:'synthetic-canonical-shared-session'};
  if(name==='landerware_public_seat_state')return {remaining:input.remaining??2};
  throw Error('unexpected_rpc:'+name);
 }});
try { console.log(JSON.stringify({status:200,body:input.saved ? await (input.action==='status' ? api.status(input.key) : api.resume(input.key)) : await api.model(input.selection),calls})); }
catch(error) { console.log(JSON.stringify({status:409,body:{ok:false,error:error.message},calls})); }
