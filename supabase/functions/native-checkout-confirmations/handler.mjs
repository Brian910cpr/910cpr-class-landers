const ORIGINS=new Set(['https://www.910cpr.com','https://910cpr.com']);
const RECEIPT_STATES=new Set(['sent','delivered','delivery_delayed','bounced','failed','complained','suppressed','opened','clicked']);
const RECEIPT_REASONS=new Set(['invalid_request','verifier_unconfigured','context_unknown','receipt_unavailable','context_invalid','provider_unavailable','provider_access_denied','receipt_not_found','provider_response_invalid','receipt_mismatch','provider_status_unverified','clock_invalid','receipt_time_invalid','verifier_unavailable','assignment_changed','reconciliation_unknown']);
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const headers=origin=>({'content-type':'application/json','cache-control':'no-store','referrer-policy':'no-referrer',
 'access-control-allow-origin':ORIGINS.has(origin)?origin:'https://www.910cpr.com',
 'access-control-allow-headers':'content-type,x-landerware-owner-session,x-hot-sync-admin-key',
 'access-control-allow-methods':'GET,POST,OPTIONS',vary:'Origin'});
async function body(req,proof=false){
 if(!/^application\/json(?:\s*;|$)/i.test(req.headers.get('content-type')||''))throw Error('unsupported_media_type');
 if(Number(req.headers.get('content-length')||0)>4096)throw Error('request_too_large');
 const reader=req.body?.getReader();if(!reader)throw Error('invalid_request');let size=0,text='';const decoder=new TextDecoder('utf-8',{fatal:true});
 try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>4096){await reader.cancel();throw Error('request_too_large');}text+=decoder.decode(value,{stream:true});}text+=decoder.decode();}finally{reader.releaseLock();}
 let data;try{data=JSON.parse(text);}catch{throw Error('invalid_request');}
 if(!data||typeof data!=='object'||Array.isArray(data))throw Error('invalid_request');
 if(proof==='receipt'){
  if(Object.keys(data).length!==1||typeof data.deliveryId!=='string'||!UUID.test(data.deliveryId))throw Error('invalid_request');
 }else if(Object.keys(data).some(k=>proof||k!=='orderId')||data.orderId!=null&&(typeof data.orderId!=='string'||!UUID.test(data.orderId)))throw Error('invalid_request');
 return data;
}
export function nativeConfirmationHandler({authorized,service,proof,schedulerStatus,verifyReceipt}){return async req=>{
 const origin=req.headers.get('origin')||'',reply=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:headers(origin)});
 if(origin&&!ORIGINS.has(origin))return reply({error:'origin_not_allowed'},403);
 if(req.method==='OPTIONS')return new Response(null,{status:204,headers:headers(origin)});
 const url=new URL(req.url),route=url.pathname.split('/').at(-1);
 if(route==='verify-receipt'&&!['/native-checkout-confirmations/verify-receipt','/functions/v1/native-checkout-confirmations/verify-receipt'].includes(url.pathname))return reply({error:'not_found'},404);
 if(!(req.method==='GET'&&route==='status')&&!(req.method==='POST'&&(route==='retry'||route==='proof'||route==='verify-receipt')))return reply({error:'not_found'},404);
 try{
  if(!await authorized(req))return reply({error:'owner_access_required'},401);
  if(route==='verify-receipt'){
   if(url.search)return reply({error:'invalid_request'},400);
   const data=await body(req,'receipt');
   if(typeof verifyReceipt!=='function')return reply({error:'receipt_verifier_unavailable'},503);
   const value=await verifyReceipt(data.deliveryId);
   // A strict projection keeps private context/lease/provider evidence out of HTTP.
   const result=value?.verified===true&&RECEIPT_STATES.has(value.status)&&typeof value.actualDeliveryConfirmed==='boolean'
    ?{verified:true,status:value.status,actualDeliveryConfirmed:value.actualDeliveryConfirmed}
    :{verified:false,reason:RECEIPT_REASONS.has(value?.reason)?value.reason:'reconciliation_unknown'};
   return reply({receiptVerification:result},result.verified?200:409);
  }
  if(route==='proof'){
   if(new URL(req.url).search) return reply({error:'invalid_request'},400);
   await body(req,true);
   if(typeof proof!=='function')return reply({error:'proof_unavailable'},503);
   const result=await proof();return reply({proof:result},result.state==='accepted'?200:409);
  }
  if(route==='status')return reply({configured:service.configured(),health:await service.health(),...(typeof schedulerStatus==='function'?{scheduler:await schedulerStatus()}:{} )});
  const data=await body(req),delivery=await service.deliver(data.orderId||null),health=await service.health();
  return reply({delivery,health},delivery.configured&&!delivery.stopped&&!delivery.ambiguous&&!delivery.rejected&&!delivery.disabled&&health.healthy?200:503);
 }catch(error){const known=['request_too_large','invalid_request','unsupported_media_type'].includes(error?.message);
  return reply({error:known?error.message:'confirmation_service_unavailable'},error?.message==='request_too_large'?413:error?.message==='unsupported_media_type'?415:known?400:503);}
};}
