(function(root){
  'use strict';
  const messages={hold_expired:'Your temporary seat hold expired. Return to the calendar to check availability. If payment was submitted, call 910-395-5193 before paying again.',bundle_fulfillment_unavailable:'HeartCode online access is currently unavailable. No new booking or payment was created. Please call 910-395-5193.',invalid_certificate:'Choose a PDF, JPG, or PNG up to 2 MB, or remove the file and bring your certificate to class.',payment_reconciliation_required:'Your reservation is saved. Please call 910-395-5193 to resume this older or expired checkout; do not create another booking.',payment_mismatch:'Payment details could not be verified. Please call 910-395-5193 before paying.'};
  async function certificate(file){
    if(!file||!file.size)return null;
    if(file.size>2097152||!['application/pdf','image/jpeg','image/png'].includes(file.type))throw Error(messages.invalid_certificate);
    const bytes=new Uint8Array(await file.arrayBuffer());let text='';
    for(let i=0;i<bytes.length;i+=8192)text+=String.fromCharCode(...bytes.subarray(i,i+8192));
    return {type:file.type,base64:btoa(text)};
  }
  function create({api,anon,key,context,send=fetch}){
    return async function call(route,body={}){
      const response=await send(api+'/'+route,{method:'POST',headers:{authorization:'Bearer '+anon,apikey:anon,'content-type':'application/json','idempotency-key':key},body:JSON.stringify({...body,context})});
      const result=await response.json();
      if(!response.ok||!result.ok){const error=Error(messages[result.error]||'The next step could not be confirmed. Retry this same form without creating another reservation. You can remove an optional certificate and bring it to class.');error.code=result.error;throw error;}
      return result;
    };
  }
  const client={create,certificate};root.SkillsCheckoutClient=client;
  if(typeof module==='object'&&module.exports)module.exports=client;
})(typeof window==='object'?window:globalThis);
