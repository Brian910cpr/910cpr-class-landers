const ORIGINS=new Set(['https://www.910cpr.com','https://910cpr.com']);
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const headers=origin=>({'content-type':'application/json','cache-control':'no-store','referrer-policy':'no-referrer',
 'access-control-allow-origin':ORIGINS.has(origin)?origin:'https://www.910cpr.com',
 'access-control-allow-headers':'content-type,x-landerware-owner-session,x-hot-sync-admin-key',
 'access-control-allow-methods':'GET,POST,OPTIONS',vary:'Origin'});
async function body(req){
 if(!/^application\/json(?:\s*;|$)/i.test(req.headers.get('content-type')||''))throw Error('unsupported_media_type');
 if(Number(req.headers.get('content-length')||0)>4096)throw Error('request_too_large');
 const reader=req.body?.getReader();if(!reader)throw Error('invalid_request');let size=0,text='';const decoder=new TextDecoder('utf-8',{fatal:true});
 try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>4096){await reader.cancel();throw Error('request_too_large');}text+=decoder.decode(value,{stream:true});}text+=decoder.decode();}finally{reader.releaseLock();}
 let data;try{data=JSON.parse(text);}catch{throw Error('invalid_request');}
 if(!data||typeof data!=='object'||Array.isArray(data)||Object.keys(data).some(k=>k!=='orderId')||data.orderId!=null&&(typeof data.orderId!=='string'||!UUID.test(data.orderId)))throw Error('invalid_request');
 return data;
}
export function nativeConfirmationHandler({authorized,service}){return async req=>{
 const origin=req.headers.get('origin')||'',reply=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:headers(origin)});
 if(origin&&!ORIGINS.has(origin))return reply({error:'origin_not_allowed'},403);
 if(req.method==='OPTIONS')return new Response(null,{status:204,headers:headers(origin)});
 const route=new URL(req.url).pathname.split('/').at(-1);
 if(!(req.method==='GET'&&route==='status')&&!(req.method==='POST'&&route==='retry'))return reply({error:'not_found'},404);
 try{
  if(!await authorized(req))return reply({error:'owner_access_required'},401);
  if(route==='status')return reply({configured:service.configured(),health:await service.health()});
  const data=await body(req),delivery=await service.deliver(data.orderId||null),health=await service.health();
  return reply({delivery,health},delivery.configured&&!delivery.stopped&&!delivery.ambiguous&&!delivery.rejected&&!delivery.disabled&&health.healthy?200:503);
 }catch(error){const known=['request_too_large','invalid_request','unsupported_media_type'].includes(error?.message);
  return reply({error:known?error.message:'confirmation_service_unavailable'},error?.message==='request_too_large'?413:error?.message==='unsupported_media_type'?415:known?400:503);}
};}
