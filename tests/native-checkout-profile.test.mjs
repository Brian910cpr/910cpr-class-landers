import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeCheckoutProfile,checkoutSelection,requiredUploadKeys,escapeCheckoutText} from '../supabase/functions/_shared/checkout-profile.mjs';
import {profileUploadInput} from '../supabase/functions/_shared/checkout-upload.mjs';
const profile=()=>({profile_key:'native_shared_skills',version:1,active:true,course_id:'skills-session-only',display_name:'Skills session',requirements:[],form_schema:{schemaVersion:'native-checkout.form.v1',allowed_contexts:['bls-skills','hsi-blended'],fields:[{key:'first_name',type:'text',label:'First name',required:true},{key:'email',type:'email',required:true},{key:'online_completed',type:'checkbox',required:true,unless_choice:'online'},{key:'online_access_ack',type:'checkbox',required:true,when_choice:'online'}],option_groups:[{key:'learning_path',type:'radio',required:true,choices:[{key:'skills',label:'Skills only',catalog_keys:[]},{key:'online',label:'Online + skills',contexts:['bls-skills'],catalog_keys:['online-code']}]}],default_choices:['skills'],public_aliases:[{public_course_id:'fixture_bundle',context:'bls-skills',default_choices:['online']}],driver_rules:[{when_choice:'online',driver:'skills_bundle'},{driver:'skills_reservation'}]}});
const catalog=()=>({unit_amount:5500,currency:'usd',addons:[{key:'online-code',unit_amount:4000,active:true}]});
test('one profile quotes $55 skills or $95 including access using server catalog options, not client price',()=>{
 const view=normalizeCheckoutProfile(profile(),catalog(),{context:'bls-skills',publicCourse:'fixture_bundle'});
 assert.deepEqual(view.defaultChoices,['online']);
 const fields={first_name:'Fixture',email:'fixture@example.invalid',online_completed:true,online_access_ack:true,amountCents:1};
 assert.equal(checkoutSelection(view,fields,['skills']).amountCents,5500);
 const bundle=checkoutSelection(view,fields,['online']);assert.equal(bundle.amountCents,9500);assert.equal(bundle.driver,'skills_bundle');assert.deepEqual(bundle.addons,[{key:'online-code',quantity:1}]);
 assert.throws(()=>checkoutSelection(view,fields,['skills','online']),/invalid_course_option/);
 assert.throws(()=>checkoutSelection(view,fields,['forged']),/option_unavailable/);
});
test('configuration filters context eligibility and availability and validates conditional acknowledgements',()=>{
 const p=profile(),cat=catalog();cat.addons[0].active=false;
 const closed=normalizeCheckoutProfile(p,cat,{context:'bls-skills'});
 assert.throws(()=>checkoutSelection(closed,{first_name:'Fixture',email:'fixture@example.invalid',online_access_ack:true},['online']),/option_unavailable/);
 const hsi=normalizeCheckoutProfile(p,catalog(),{context:'hsi-blended'});assert.equal(hsi.optionGroups[0].choices.length,1);
 assert.throws(()=>checkoutSelection(hsi,{first_name:'Fixture',email:'fixture@example.invalid'},['skills']),/required_registration_field_missing/);
 assert.throws(()=>normalizeCheckoutProfile(p,catalog(),{context:'unknown'}),/invalid_context/);
 assert.throws(()=>normalizeCheckoutProfile({...p,version:0},catalog(),{context:'bls-skills'}),/invalid_checkout_profile/);
});
test('uploads default disabled, enabled documents are optional, explicit course policy alone makes them required',()=>{
 const p=profile();let view=normalizeCheckoutProfile(p,catalog(),{context:'bls-skills'});assert.deepEqual(view.uploads,[]);
 p.requirements=[{key:'renewal_form',type:'instructor_renewal',display_name:'Instructor renewal form',upload_now:true,upload:{mime_types:['application/pdf'],max_bytes:2097152}}];
 view=normalizeCheckoutProfile(p,catalog(),{context:'bls-skills'});assert.equal(view.uploads[0].mode,'optional');assert.deepEqual(requiredUploadKeys(view,['skills']),[]);
 p.requirements[0].required_before_registration=true;view=normalizeCheckoutProfile(p,catalog(),{context:'bls-skills'});assert.deepEqual(requiredUploadKeys(view,['skills']),['renewal_form']);assert.equal(view.uploads[0].receivedMeansApproved,false);
 p.requirements[0].upload.enabled=false;assert.throws(()=>normalizeCheckoutProfile(p,catalog(),{context:'bls-skills'}),/invalid_checkout_profile/);
 p.requirements[0].required_before_registration=false;assert.deepEqual(normalizeCheckoutProfile(p,catalog(),{context:'bls-skills'}).uploads,[]);
});
test('server upload policy blocks disabled or spoofed files and is independent of course IDs',()=>{
 const file={type:'application/pdf',base64:btoa('%PDF-fixture')},policy={mode:'optional',maxBytes:2097152,mimeTypes:['application/pdf']};
 assert.throws(()=>profileUploadInput(file,null),/uploads_disabled/);
 assert.equal(profileUploadInput(file,policy).extension,'pdf');
 assert.throws(()=>profileUploadInput({...file,type:'image/png'},policy),/invalid_document/);
 assert.throws(()=>profileUploadInput(file,{...policy,maxBytes:3}),/invalid_document/);
 assert.throws(()=>profileUploadInput({type:'application/pdf',base64:btoa('<script>')},policy),/invalid_document/);
 assert.equal(escapeCheckoutText('<img src=x onerror="x">'), '&lt;img src=x onerror=&quot;x&quot;&gt;');
});
