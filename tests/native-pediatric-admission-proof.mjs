// Disposable synthetic reviewed policy only. No production defaults or extra ACLs.
import {readFileSync} from 'node:fs';
import {setupHeartsaverAdmission,scalar,service,sourceRoot,claimSQL} from './native-heartsaver-admission-proof.mjs';
export {scalar,service,sourceRoot,claimSQL};
export const migrationFile='20261112010917_native_pediatric_existing_session_admission.sql';
export const migration=()=>readFileSync(new URL('../supabase/migrations/'+migrationFile,import.meta.url),'utf8');
export const syntheticPolicy={instruction:123,setup:7,cleanup:13,capacity:8};
export function request(external,n){
 const wire={firstName:'Synthetic',lastName:'Pediatric',email:`pediatric-${n}@example.invalid`,phone:'2025550100',addons:[]};
 return [`${String(n).padStart(8,'0')}-1111-4111-8111-111111111111`,'native_heartsaver_351632_draft',external,'{}',JSON.stringify([wire]),JSON.stringify([{wire,selectedChoices:[]}]),9500];
}
export async function enablePediatricPolicy(db){
 await db.exec(`update courses set registration_profile_key='native_heartsaver_351632_draft',base_price=95 where enrollware_course_id='351632';
 update landerware_registration_profiles set active=true where profile_key='native_heartsaver_351632_draft';
 update landerware_registration_catalog set active=true where course_id='351632';
 update native_pediatric_existing_session_policy set enabled=true,publication_enabled=true,verified=true,evidence='LOCAL SYNTHETIC REVIEW ONLY',timing_evidence='LOCAL SYNTHETIC REVIEW ONLY',capacity_evidence='LOCAL SYNTHETIC REVIEW ONLY',instruction_minutes=123,setup_minutes=7,cleanup_minutes=13,max_students=8,source_qualification_id=(select id from instructor_qualifications where qualification_key='aha-bls-instructor:209806');`);
}
export async function setupPediatricAdmission(db,{apply=true,enabled=false,optional=false}={}){
 await setupHeartsaverAdmission(db,{optional});
 if(apply)await db.exec(migration());
 if(enabled)await enablePediatricPolicy(db);
}
export async function adoptPediatricSession(db,sessionId){
 const proof=await scalar(db,'select native_session_authority_snapshot($1)',[sessionId]);
 return scalar(db,'select native_session_authority_record($1,gen_random_uuid(),$2,$3,true)',[sessionId,proof.fingerprint,proof.revision]);
}
export async function makePediatricSession(db,{external='990351632',adopt=true}={}){
 const sessionId=await scalar(db,`insert into class_sessions(source,status,record_scope,course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,external_course_id,historical_student_count,external_reconciliation)
 select 'manual','scheduled','operational','0689a2c5-c507-4e8a-b94c-15e5c5689e28',t.starts,t.starts+interval '123 minutes',t.starts-interval '7 minutes',t.starts+interval '136 minutes',p.id,l.id,8,'landerware','public','open',$1,'351632',2,jsonb_build_object('complete',true,'active_external_registration_ids',jsonb_build_array('synthetic-retained-pediatric'),'active_registration_count',1,'source_observed_at',now()-interval '1 day')
 from people p cross join locations l cross join (select now()+interval '70 days' starts)t where p.person_key='brian' and l.location_key='910cpr-office-shipyard' returning id`,[external]);
 const customer=await scalar(db,"insert into customers(first_name,last_name,email) values('Existing','Synthetic',$1) returning id",[external+'@example.invalid']);
 await db.query("insert into registrations(customer_id,class_session_id,status,registration_source) values($1,$2,'registered','landerware_native_checkout')",[customer,sessionId]);
 if(adopt)await adoptPediatricSession(db,sessionId);
 return {sessionId,external};
}
