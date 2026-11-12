// Isolated synthetic fixtures. Baseline ACL provenance is in native-full-service-role-acl.sql
// and setupBlsAdmission; this helper adds NO grants to conceal migration requirements.
import {readFileSync} from 'node:fs';
import {setupBlsAdmission,scalar,sourceRoot,service} from './native-bls-admission-proof.mjs';
export {scalar,sourceRoot,service};
const load=f=>readFileSync(new URL('../supabase/migrations/'+f,import.meta.url),'utf8');
export const claimSQL="select reserve_native_checkout_order($1,$2,1,'',$3,$4::jsonb,$5::jsonb,$6::jsonb,$7)";
export const prices={'209809':9500,'344085':7000};
export function request(course,external,offer,n){
 const wire={firstName:'Synthetic',lastName:'Fixture',email:`heartsaver-${course}-${n}@example.invalid`,phone:'2025550100',addons:[]};
 return [`${String(n).padStart(8,'0')}-1111-4111-8111-111111111111`,`native_heartsaver_${course}_draft`,external,JSON.stringify(offer),JSON.stringify([wire]),JSON.stringify([{wire,selectedChoices:[]}]),prices[course]];
}
export async function setupHeartsaverAdmission(db,{optional=false,apply=true}={}){
 await setupBlsAdmission(db,{full:true});
 for(const f of ['20261111225500_native_full_offer_wallclock_lease.sql','20261111233000_native_skills_offer_wallclock_lease.sql','20261111233504_native_bls_skills_publication_disabled.sql'])await db.exec(load(f));
 if(optional)for(const f of ['20261109130000_native_learner_code_delivery.sql','20261109140000_native_code_delivery_events.sql','20261111235100_native_learner_code_resend_service.sql','20261112000500_native_bls_code_completion_guard.sql','20261112001500_native_learner_code_receipt_reconciliation.sql'])await db.exec(load(f));
 await db.exec(`update courses set registration_profile_key='native_heartsaver_'||enrollware_course_id||'_draft',base_price=case enrollware_course_id when '209809' then 95 else 70 end where enrollware_course_id in('209809','344085');
 update landerware_registration_profiles set active=true where profile_key in('native_heartsaver_209809_draft','native_heartsaver_344085_draft');
 update landerware_registration_catalog set active=true where course_id in('209809','344085');
 update native_heartsaver_full_course_policy set max_students=8,capacity_evidence='LOCAL SYNTHETIC ONLY',price_evidence='LOCAL SYNTHETIC ONLY',enabled=true,publication_enabled=true,verified=true,evidence='LOCAL SYNTHETIC ONLY',source_qualification_id=(select id from instructor_qualifications where qualification_key='aha-bls-instructor:209806');`);
 if(apply)await db.exec(load('20261112003000_native_heartsaver_existing_session_admission.sql'));
}
export async function makeHeartsaverOffer(db,course,day=course==='209809'?45:46){
 return scalar(db,`select skills_test.offer('heartsaver-admission',$1)||jsonb_build_object('authority','native-full-course.v2','proofObservedAt',now(),'validUntil',now()+interval '10 minutes','nativeScopeId','brian-shipyard-b.v1','courseNumber',$2::text,'coursePolicyKey','heartsaver-full:'||$2::text||'.v1','instructor','Brian Ennis','selectionId','native-full:'||encode(sha256(convert_to($2::text||':'||$1::text,'UTF8')),'hex'),'endsAt',(skills_test.offer('heartsaver-admission',$1)->>'startsAt')::timestamptz+make_interval(mins=>case when $2='344085' then 90 else 120 end),'consumptionEndsAt',(skills_test.offer('heartsaver-admission',$1)->>'startsAt')::timestamptz+make_interval(mins=>case when $2='344085' then 105 else 150 end))`,[day,course]);
}
