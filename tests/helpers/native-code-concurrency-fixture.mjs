// Synthetic, disposable local PostgreSQL fixture only. Never hosted.
import {readFileSync} from 'node:fs';
import {preProfileFiles,profileMigration,fullCourseMigration,codeDeliveryMigration,codeEventMigration} from './native-checkout-migration-plan.mjs';
const load=p=>readFileSync(new URL('../../'+p,import.meta.url),'utf8');
export const codeToken='SYNTHETIC-LOCAL-DELIVERY-TOKEN-ONLY-123456789';
export const codeScalar=async(db,sql,args=[])=>Object.values((await db.query(sql,args)).rows[0]||{})[0];
export async function setupCodeConcurrency(db){
 const token=codeToken;
  for(const f of preProfileFiles)await db.exec(load(f));await db.exec("update courses set course_key='skills-session-only' where enrollware_course_id='509474'");
  for(const f of [profileMigration,fullCourseMigration,codeDeliveryMigration,codeEventMigration,'supabase/migrations/20261111235100_native_learner_code_resend_service.sql'])await db.exec(load(f));
  const scalar=(sql,args=[])=>codeScalar(db,sql,args);
  await db.exec(`update landerware_checkout_delivery_config set enabled=true,token_sha256=encode(sha256(convert_to('${token}','UTF8')),'hex');
   update skills_session_context_config set qualification_course_id=(select id from courses where course_key='fixture-qualification'),enabled=true where context_key='bls-skills';
   update landerware_bls_bundle_policy set enabled=true,verified=true,verification_evidence='SYNTHETIC LOCAL';
   update landerware_registration_catalog set addons=jsonb_set(addons,'{0,active}','true') where course_id='509474';
   insert into products(product_key,active,product_type,customer_price,fulfillment_mode) values('aha-25-3553-heartcode-bls-online',true,'online_program',40,'digital_code');
   insert into product_inventory_units(product_id,secret_value,status) select id,'SYNTHETIC-PRIVATE-CODE-'||n,'available' from products cross join generate_series(1,8) n;`);
  async function order(n,online=true,paid=true){
   const key=`34343434-3434-4434-8434-${String(n).padStart(12,'0')}`,wire={firstName:'Synthetic',lastName:'Learner',email:`learner-${n}@example.invalid`,phone:'2025550100',skillsContext:'bls-skills',learningPath:online?'online-and-skills':'skills-only',onlineCompletionAcknowledged:online,onlineCompleted:!online,addons:online?[{key:'aha_heartcode_bls_online',quantity:1}]:[]};
   const o=await scalar("select reserve_native_checkout_order($1,'native_skills_shared',1,'bls-skills',null,skills_test.offer('code-'||$2,$2::int)||jsonb_build_object('context','bls-skills'),$3::jsonb,$4::jsonb,$5)",[key,n+100,JSON.stringify([wire]),JSON.stringify([{wire,selectedChoices:[online?'online_and_skills':'skills_only']}]),online?9500:5500]);
   if(paid){await db.query("update landerware_public_orders set stripe_checkout_session_id=$2,status='checkout_open' where id=$1",[o.orderId,'cs_fixture'+n]);
    const evidence={id:'cs_fixture'+n,mode:'payment',payment_status:'paid',livemode:false,amount_total:online?9500:5500,currency:'usd',metadata:{landerware_order_id:o.orderId}};
    await scalar('select landerware_record_public_payment($1,$2,$3::jsonb)',[o.orderId,'pi_fixture'+n,JSON.stringify(evidence)]);await scalar('select landerware_finalize_public_order($1,$2,$3::jsonb)',[o.orderId,'pi_fixture'+n,JSON.stringify(evidence)]);}
   return o;
  }

 await db.exec(`alter role service_role nosuperuser bypassrls;
 update native_learner_code_runtime set enabled=true;
 update landerware_checkout_delivery_config set provider='resend';
 update native_code_delivery_policy set enabled=true;`);
 return {order};
}
