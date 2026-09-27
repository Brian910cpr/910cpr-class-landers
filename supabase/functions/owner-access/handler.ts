import {ownerConfig,ownerRest,lookupOwnerSession,tokenHash,newToken,unexpired,SESSION_DAYS,OWNER_SESSION_HEADER,type OwnerConfig} from '../_shared/owner-session.ts';
const ORIGINS=new Set(['https://www.910cpr.com','https://910cpr.com']);
export function createOwnerAccessHandler(config:OwnerConfig,send:typeof fetch=fetch) {
  return async (req:Request):Promise<Response>=>{
    const origin=req.headers.get('origin');
    const headers:Record<string,string>={'content-type':'application/json','cache-control':'private, no-store','x-robots-tag':'noindex, nofollow, noarchive','vary':'Origin','access-control-allow-headers':`content-type,${OWNER_SESSION_HEADER}`,'access-control-allow-methods':'GET,POST,OPTIONS'};
    if(origin&&ORIGINS.has(origin))headers['access-control-allow-origin']=origin;
    const json=(data:unknown,status=200)=>new Response(JSON.stringify(data),{status,headers});
    if(origin&&!ORIGINS.has(origin))return json({error:'Origin not allowed.'},403);
    if(req.method==='OPTIONS')return new Response(null,{status:204,headers});
    const path=new URL(req.url).pathname.replace(/^.*\/owner-access\/?/,'');
    try {
      if(path==='exchange'&&req.method==='POST') {
        if(Number(req.headers.get('content-length')||0)>2048)return json({error:'Invalid access link.'},400);
        const text=await req.text();if(text.length>2048)return json({error:'Invalid access link.'},400);
        let body;try{body=JSON.parse(text);}catch{return json({error:'Invalid access link.'},400);}
        const token=String(body.access_token||'');
        if(!/^lw_p_[0-9a-f]{64}$/.test(token))return json({error:'This access link is invalid or has expired.'},401);
        const hash=await tokenHash(token);
        const rows=await ownerRest(`owner_access_grants?token_sha256=eq.${hash}&revoked_at=is.null&select=id,owner_email,owner_name,expires_at,revoked_at&limit=1`,{},config,send);
        const grant=Array.isArray(rows)&&rows.length===1?rows[0]:null;
        if(!grant||grant.revoked_at||!unexpired(grant.expires_at))return json({error:'This access link is invalid or has expired.'},401);
        const sessionToken=newToken('lw_s_'),expiresAt=new Date(Math.min(Date.now()+SESSION_DAYS*86400000,Date.parse(grant.expires_at))).toISOString();
        await ownerRest('owner_browser_sessions',{method:'POST',body:JSON.stringify({grant_id:grant.id,token_sha256:await tokenHash(sessionToken),expires_at:expiresAt})},config,send);
        return json({token:sessionToken,expiresAt,ownerName:grant.owner_name,ownerEmail:grant.owner_email});
      }
      const session=await lookupOwnerSession(req.headers.get(OWNER_SESSION_HEADER)||'',config,send);
      if(!session)return json({error:'Open your private LanderWare access link to sign in.'},401);
      if(path==='session'&&req.method==='GET')return json({expiresAt:session.expires_at,ownerName:session.grant.owner_name,ownerEmail:session.grant.owner_email});
      if(path==='refresh'&&req.method==='POST') {
        const expiresAt=new Date(Math.min(Date.now()+SESSION_DAYS*86400000,Date.parse(session.grant.expires_at))).toISOString();
        await ownerRest(`owner_browser_sessions?id=eq.${session.id}&revoked_at=is.null`,{method:'PATCH',body:JSON.stringify({expires_at:expiresAt})},config,send);
        return json({expiresAt});
      }
      if(path==='logout'&&req.method==='POST') {
        await ownerRest(`owner_browser_sessions?id=eq.${session.id}`,{method:'PATCH',body:JSON.stringify({revoked_at:new Date().toISOString()})},config,send);
        return json({ok:true});
      }
      return json({error:'Not found.'},404);
    }catch(error){return json({error:'Owner access is temporarily unavailable. Please try again.'},Number((error as {status?:number}).status)||503);}
  };
}
export {ownerConfig};
