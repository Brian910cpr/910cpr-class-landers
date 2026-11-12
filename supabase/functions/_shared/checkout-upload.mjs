// Upload policy comes from the server's versioned profile, never request fields.
const signatures={
 'application/pdf':b=>[37,80,68,70,45].every((n,i)=>b[i]===n),
 'image/jpeg':b=>[255,216,255].every((n,i)=>b[i]===n),
 'image/png':b=>[137,80,78,71,13,10,26,10].every((n,i)=>b[i]===n),
 'image/webp':b=>[82,73,70,70].every((n,i)=>b[i]===n)&&[87,69,66,80].every((n,i)=>b[i+8]===n),
};
export function profileUploadInput(value,policy){
 if(!policy||!['optional','required'].includes(policy.mode))throw Error('uploads_disabled');
 const limit=policy.maxBytes;
 if(!Number.isSafeInteger(limit)||limit<1||limit>10485760||!Array.isArray(policy.mimeTypes))throw Error('invalid_checkout_profile');
 if(!value||!policy.mimeTypes.includes(value.type)||!signatures[value.type]||typeof value.base64!=='string'||value.base64.length>Math.ceil(limit/3)*4||value.base64.length%4||!/^[A-Za-z0-9+/]*={0,2}$/.test(value.base64))throw Error('invalid_document');
 let decoded;try{decoded=atob(value.base64);}catch{throw Error('invalid_document');}
 const bytes=Uint8Array.from(decoded,c=>c.charCodeAt(0));
 if(!bytes.length||bytes.length>limit||!signatures[value.type](bytes))throw Error('invalid_document');
 return {bytes,type:value.type,extension:({'application/pdf':'pdf','image/jpeg':'jpg','image/png':'png','image/webp':'webp'})[value.type]};
}
