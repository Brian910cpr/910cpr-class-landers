import {createHandler} from './handler.mjs';
import {SITE} from './policy.mjs';
import {ownerConfig} from '../_shared/owner-session.ts';
export const handler=createHandler({
  enabled:()=>Deno.env.get('SKILLS_SESSION_RESERVATIONS_ENABLED')==='true',
  async publication(page:string){
    const r=await fetch(`${SITE}/data/block-selector-availability/${page}.json`,{cache:'no-store',redirect:'error',signal:AbortSignal.timeout(15000)});
    if(!r.ok)throw Error('calendar_refresh_required');return r.json();
  },
  async rpc(name:string,body:unknown){
    const c=ownerConfig();
    const r=await fetch(`${c.url}/rest/v1/rpc/${name}`,{method:'POST',redirect:'error',signal:AbortSignal.timeout(15000),
      headers:{apikey:c.key,authorization:`Bearer ${c.key}`,'content-type':'application/json'},body:JSON.stringify(body)});
    const value=await r.json();if(!r.ok)throw Error(value.message||'service_unavailable');return value;
  }
});
if(import.meta.main)Deno.serve(handler);
