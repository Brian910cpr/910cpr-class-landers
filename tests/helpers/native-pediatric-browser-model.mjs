// Synthetic reads only: exercise the actual shared generic model, never checkout.
import {genericCheckout} from '../../supabase/functions/public-registration/generic.mjs';
let text='';for await(const chunk of process.stdin)text+=chunk;const input=JSON.parse(text);
const profile={profile_key:'native_heartsaver_351632_draft',version:2,active:true,display_name:'Heartsaver Pediatric First Aid CPR AED',requirements:[],form_schema:{
 schemaVersion:'native-checkout.form.v1',inventory_kind:'scheduled_session_v1',max_students:4,fields:[
 {key:'first_name',wire:'firstName',label:'First name',type:'text',required:true},
 {key:'last_name',wire:'lastName',label:'Last name',type:'text',required:true},
 {key:'email',wire:'email',label:'Email',type:'email',required:true},
 {key:'phone',wire:'phone',label:'Phone',type:'tel',required:true}],option_groups:[],driver_rules:[{driver:'native_order'}]}};
const api=genericCheckout({now:()=>Date.parse(input.now),catalog:async()=>({course_id:'351632',unit_amount:9500,currency:'usd',addons:[]}),
 scheduleSession:async id=>{if(input.disabled||id!==input.session.external_class_id)throw Error('native_registration_unavailable');return {...input.session,nativeReady:true,course_id:'351632',seats:{capacity:4,remaining:1}};},
 rpc:async name=>{if(name==='native_checkout_profile')return {profile,physicalCourseId:'351632'};throw Error('unexpected_rpc:'+name);}});
try{console.log(JSON.stringify({status:200,body:await api.model(input.selection)}));}
catch(e){console.log(JSON.stringify({status:400,body:{ok:false,error:e.message}}));}
