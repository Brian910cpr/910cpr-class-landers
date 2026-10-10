type Dependencies = {
  authorize: (req: Request) => Promise<boolean>;
  actor: (req: Request) => Promise<string>;
  rest: (path: string, init?: RequestInit) => Promise<unknown>;
};
const headers = {'access-control-allow-origin':'https://www.910cpr.com','access-control-allow-headers':'content-type, x-landerware-owner-session','access-control-allow-methods':'GET,POST,OPTIONS','content-type':'application/json','cache-control':'no-store'};
const response = (data: unknown,status=200) => Response.json(data,{status,headers});
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export function createHandler(deps: Dependencies) {
  return async (req: Request) => {
    if(req.method==='OPTIONS') return new Response(null,{status:204,headers});
    try {
      if(!await deps.authorize(req)) return response({error:'Unauthorized'},401);
      if(req.method==='GET') {
        const rows=await deps.rest('customer_interactions?select=*&order=updated_at.desc&limit=100');
        return response({interactions:rows,limit:100});
      }
      if(req.method!=='POST') return response({error:'Method not allowed'},405);
      const text=await req.text();
      if(new TextEncoder().encode(text).length>200000) return response({error:'Record too large'},413);
      let body;
      try {body=JSON.parse(text)} catch {return response({error:'Invalid JSON'},400)}
      const input=body?.input;
      if(!uuid.test(body?.request_id||'')||!uuid.test(input?.id||'')||!uuid.test(input?.case_id||'')||
        !Number.isInteger(input?.expected_version)||input.expected_version<0||
        !['phone','email','manual'].includes(input?.kind)||
        !['new','in_progress','paused','awaiting_data','awaiting_approval','follow_up_due','resolved'].includes(input?.status)||
        input?.source!=='manual'||typeof input?.source_id!=='string'||!input.source_id.trim()||input.source_id.length>200||
        !input?.document||typeof input.document!=='object'||Array.isArray(input.document)||
        (input.person_id!=null&&!uuid.test(input.person_id))) return response({error:'Invalid record; only manual capture is connected'},400);
      const record=await deps.rest('rpc/save_customer_interaction',{method:'POST',body:JSON.stringify({p_request_id:body.request_id,p_actor:await deps.actor(req),p_input:input})});
      return response({interaction:record});
    } catch(error) {
      const code=(error as {code?:string})?.code;
      if(['40001','23505'].includes(code||'')) return response({error:'Conflict: reload and reconcile before saving',code},409);
      if(['22023','23503','23514','23502'].includes(code||'')) return response({error:'Invalid record',code},400);
      const status=(error as {status?:number})?.status===403?403:503;
      return response({error:status===403?'Forbidden':'Storage unavailable; preserve your draft and retry with the same request ID'},status);
    }
  };
}
