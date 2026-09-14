import {jobHealth,validateCheckpoint} from './core.mjs';
const ORIGINS=new Set(['https://www.910cpr.com','https://910cpr.com']);
export function createArchiveStatusHandler({lookupSession,readStatus,now=Date.now}) {
  return async function handle(req) {
    const origin=req.headers.get('origin')||'';
    const headers={'content-type':'application/json','cache-control':'private, no-store','vary':'Origin','referrer-policy':'no-referrer','x-content-type-options':'nosniff',
      'access-control-allow-headers':'x-landerware-owner-session','access-control-allow-methods':'GET,OPTIONS',...(ORIGINS.has(origin)?{'access-control-allow-origin':origin}:{})};
    const reply=(data,status=200)=>new Response(status===204?null:JSON.stringify(data),{status,headers});
    if(origin&&!ORIGINS.has(origin))return reply({error:'origin_not_allowed'},403);
    if(req.method==='OPTIONS')return reply(null,204);
    if(req.method!=='GET')return reply({error:'method_not_allowed'},405);
    const token=req.headers.get('x-landerware-owner-session')||'';
    if(!/^lw_s_[0-9a-f]{64}$/.test(token))return reply({error:'owner_session_required'},401);
    try {if(!await lookupSession(token))return reply({error:'owner_session_required'},401);}
    catch {return reply({error:'owner_access_unavailable'},503);}
    try {
      const data=await readStatus();
      const checkpoint=validateCheckpoint(data.checkpoint);
      // Recheck revocation after the upstream read; cached content never caches authority.
      if(!await lookupSession(token))return reply({error:'owner_session_required'},401);
      return reply({checkpoint,source:data.source,observed_at:new Date(now()).toISOString(),job_health:jobHealth(checkpoint,now())});
    } catch {return reply({error:'archive_status_unavailable'},503);}
  };
}
