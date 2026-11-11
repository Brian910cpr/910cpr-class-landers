import {readFile} from 'node:fs/promises';
const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');

// All rows below are synthetic. Public course IDs/keys are implementation
// contracts exercised by the migration, not copies of operational records.
const courses=[
 {id:'11111111-1111-4111-8111-111111111111',course_key:'aha-bls-provider',name:'Synthetic Initial',enrollware_course_id:'209806'},
 {id:'22222222-2222-4222-8222-222222222222',course_key:'aha-bls-provider-renewal',name:'Synthetic Renewal',enrollware_course_id:'359474'},
 {id:'33333333-3333-4333-8333-333333333333',course_key:'fixture-other-course',name:'Synthetic Other',enrollware_course_id:'fixture-other'}
].map(c=>({...c,base_price:75,duration_minutes:120,setup_buffer_minutes:0,cleanup_buffer_minutes:0,
 max_students_default:12,registration_backend_default:'manual',visibility_default:'private',registration_profile_key:null}));
export const catalogs=['209806','359474'].map(id=>({
 course_id:id,course_name:'Synthetic catalog '+id,unit_amount:7500,currency:'usd',active:true,
 addons:id==='209806'?[{key:'fixture_unmapped_addon',unit_amount:999,active:true}]:[],billing_codes:[]
}));
const profiles=['209806','359474'].flatMap(id=>[
 {profile_key:'retail-'+id,course_id:'retail-'+id,display_name:'Synthetic retail profile',registration_mode:'public_direct',listed:true},
 {profile_key:'maxim-course-'+id,course_id:id,display_name:'Synthetic corporate profile',registration_mode:'corporate_scheduling',listed:false}
]).map(p=>({
 ...p,version:1,session_policy:'required',allowed_entry_contexts:[],required_fields:[],
 requirements:[],addons:[],payer_policy:{mode:'synthetic_fixture'},pricing_behavior:{},
 corporate_context:{},confirmation_template_key:'fixture-confirmation',completion_prerequisites:[],
 active:true,created_at:'2030-01-01T00:00:00Z',updated_at:'2030-01-01T00:00:00Z',form_schema:{}
}));

export async function fixture(){
 // PGlite gets no URL or directory: this is an isolated in-memory database.
 const db=new PGlite();
 try{
  await db.exec(await readFile(new URL('./inactive-bls-profile-contract.sql',import.meta.url),'utf8'));
  await db.exec("insert into landerware_confirmation_templates values ('fixture-confirmation'),('native-checkout-profile-v1')");
  for(const p of profiles)await db.query(
   'insert into landerware_registration_profiles select * from jsonb_populate_record(null::landerware_registration_profiles,$1::jsonb)',
   [JSON.stringify(p)]);
  for(const c of courses)await db.query(
   'insert into courses select * from jsonb_populate_record(null::courses,$1::jsonb)',[JSON.stringify(c)]);
  for(const c of catalogs)await db.query(
   'insert into landerware_registration_catalog select * from jsonb_populate_record(null::landerware_registration_catalog,$1::jsonb)',
   [JSON.stringify(c)]);
  return db;
 }catch(error){await db.close();throw error;}
}
