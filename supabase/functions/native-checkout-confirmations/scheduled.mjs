// Separate machine-only route. Never forwards credentials to the owner handler.
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const TOKEN=/^[a-f0-9]{64}$/;
const CODES=new Set(['claim_unknown','claim_invalid','duplicate_claim','settlement_unknown','mail_unconfigured']);
const reply=(data,status=200)=>Response.json(data,{status,headers:{'cache-control':'no-store','referrer-policy':'no-referrer'}});
export async function tokenHash(token){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(token)))].map(n=>n.toString(16).padStart(2,'0')).join('');}
async function emptyObject(req){
 if(!/^application\/json(?:\s*;|$)/i.test(req.headers.get('content-type')||''))return false;
 if(Number(req.headers.get('content-length')||0)>64)return false;
 const reader=req.body?.getReader();if(!reader)return false;let size=0,text='';const d=new TextDecoder('utf-8',{fatal:true});
 try{for(;;){const{done,value}=await reader.read();if(done)break;size+=value.length;if(size>64){await reader.cancel();return false;}text+=d.decode(value,{stream:true});}text+=d.decode();const b=JSON.parse(text);return b!==null&&typeof b==='object'&&!Array.isArray(b)&&Object.keys(b).length===0;}catch{return false;}finally{reader.releaseLock();}
}
function summary(value){
 const invalid=()=>({outcome:'uncertain',code:'result_invalid',claimed:0,accepted:0,rejected:0,ambiguous:0});
 if(!value||typeof value!=='object')return invalid();
 const fields=['claimed','accepted','rejected','ambiguous'],counts={};
 for(const key of fields){const n=value[key]??0;if(!Number.isInteger(n)||n<0||n>10)return invalid();counts[key]=n;}
 if(counts.accepted+counts.rejected+counts.ambiguous>counts.claimed)return invalid();
 let outcome='completed',code=null;
 if(value.stopped){outcome='uncertain';code=CODES.has(value.stopped)?value.stopped:'result_invalid';}
 else if(counts.ambiguous){outcome='uncertain';code='provider_ambiguous';}
 else if(value.configured===false){outcome='fault';code='mail_unconfigured';}
 else if(value.disabled===true){if(counts.claimed!==0)return invalid();outcome='disabled';}
 else if(value.configured!==true||counts.accepted+counts.rejected!==counts.claimed)return invalid();
 return {outcome,code,...counts};
}
export function nativeScheduledHandler({rpc,service,hash=tokenHash}){return async req=>{
 const url=new URL(req.url);
 if(!['/native-checkout-confirmations/scheduled','/functions/v1/native-checkout-confirmations/scheduled'].includes(url.pathname)||req.method!=='POST')return reply({error:'not_found'},404);
 if(req.headers.has('origin'))return reply({error:'origin_not_allowed'},403);
 if(url.search||!await emptyObject(req))return reply({error:'invalid_request'},400);
 const token=/^Bearer ([a-f0-9]{64})$/.exec(req.headers.get('authorization')||'')?.[1]||'',runId=req.headers.get('x-native-scheduler-run')||'';
 if(req.headers.has('x-native-scheduler-token'))return reply({error:'scheduler_access_required'},401);
 if(!TOKEN.test(token)||!UUID.test(runId))return reply({error:'scheduler_access_required'},401);
 let admission;
 try{admission=await rpc('native_checkout_scheduler_begin',{p_run_id:runId,p_token_hash:await hash(token)});}catch{return reply({error:'scheduler_unavailable'},503);}
 if(admission?.authorized!==true)return reply({error:'scheduler_access_required'},401);
 if(admission.started!==true)return reply({state:admission.disabled?'disabled':'not_started'},409);
 let result;
 try{result=summary(await service.deliver(null,{limit:1}));}catch{result={outcome:'uncertain',code:'delivery_unknown',claimed:0,accepted:0,rejected:0,ambiguous:0};}
 // Only the same durable completion is retried; never replay delivery.
 const args={p_run_id:runId,p_result:result};let settled;
 for(let attempt=0;attempt<2;attempt++){try{settled=await rpc('native_checkout_scheduler_finish',args);if(settled?.settled===true||settled?.replay===true)break;}catch{}}
 if(settled?.settled!==true&&settled?.replay!==true)return reply({error:'scheduler_completion_unknown'},503);
 return reply({state:result.outcome,actualDeliveryConfirmed:false},['completed','disabled'].includes(result.outcome)?200:503);
};}
