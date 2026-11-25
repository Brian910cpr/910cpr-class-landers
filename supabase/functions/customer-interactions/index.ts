import {authorizedOwner} from '../_shared/owner-auth.ts';
import {ownerConfig,tokenHash,OWNER_SESSION_HEADER} from '../_shared/owner-session.ts';
import {createHandler} from './handler.ts';
import 'jsr:@supabase/functions-js/edge-runtime.d.ts';

Deno.serve(createHandler({
  // Browser owner sessions only. Corporate sessions and legacy automation keys cannot read CRM notes.
  authorize: async req => Boolean(req.headers.get(OWNER_SESSION_HEADER)) && await authorizedOwner(req),
  actor: req => tokenHash(req.headers.get(OWNER_SESSION_HEADER)!),
  rest: async (path,init={}) => {
    const {url,key}=ownerConfig();
    const res=await fetch(`${url}/rest/v1/${path}`,{...init,redirect:'error',signal:AbortSignal.timeout(15000),headers:{apikey:key,authorization:`Bearer ${key}`,'content-type':'application/json'}});
    const data=await res.json();
    if(!res.ok) throw Object.assign(Error('Storage request failed'),{code:data?.code});
    return data;
  }
}));
