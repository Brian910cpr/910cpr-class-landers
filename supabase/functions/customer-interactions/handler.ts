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
        const interruptions=await deps.rest('customer_interruption_events?select=request_id,input,result,occurred_at&order=occurred_at.desc&limit=100');
        const tasks=await deps.rest('customer_follow_up_tasks?select=*&order=created_at.desc&limit=100');
        return response({interactions:rows,interruptions,tasks,limit:100});
      }
      if(req.method!=='POST') return response({error:'Method not allowed'},405);
      const text=await req.text();
      if(new TextEncoder().encode(text).length>200000) return response({error:'Record too large'},413);
      let body;
      try {body=JSON.parse(text)} catch {return response({error:'Invalid JSON'},400)}
      const input=body?.input;
      if(body?.operation==='save_task') {
        if(!uuid.test(body?.request_id||'')||!uuid.test(input?.id||'')||!uuid.test(input?.case_id||'')||!uuid.test(input?.interaction_id||'')||
          !Number.isInteger(input?.expected_version)||input.expected_version<0||
          typeof input?.source_key!=='string'||!input.source_key.trim()||input.source_key.length>200||
          typeof input?.title!=='string'||!input.title.trim()||input.title.length>500||
          !['proposed','pending','snoozed','complete'].includes(input?.status)||
          typeof input?.provenance?.evidence!=='string'||!input.provenance.evidence.trim()||
          (input.due_at!=null&&(typeof input.due_at!=='string'||!Number.isFinite(Date.parse(input.due_at))))||
          (input.status==='snoozed'&&!input.due_at)||
          (input.status==='complete'&&(typeof input.completion_evidence!=='string'||!input.completion_evidence.trim())))
          return response({error:'Invalid task or missing completion evidence'},400);
        const task=await deps.rest('rpc/save_customer_follow_up_task',{method:'POST',body:JSON.stringify({p_request_id:body.request_id,p_actor:await deps.actor(req),p_input:input})});
        return response({task});
      }
      const validRecord = (input: any) => !(!uuid.test(input?.id||'')||!uuid.test(input?.case_id||'')||
        !Number.isInteger(input?.expected_version)||input.expected_version<0||
        !['phone','email','manual'].includes(input?.kind)||
        !['new','in_progress','paused','awaiting_data','awaiting_approval','follow_up_due','resolved'].includes(input?.status)||
        input?.source!=='manual'||typeof input?.source_id!=='string'||!input.source_id.trim()||input.source_id.length>200||
        !input?.document||typeof input.document!=='object'||Array.isArray(input.document)||
        (input.person_id!=null&&!uuid.test(input.person_id)));
      if(!uuid.test(body?.request_id||'')) return response({error:'Invalid request ID'},400);
      if(body?.operation==='interrupt'||body?.operation==='resume') {
        if(!validRecord(input?.previous)||!validRecord(input?.active)||
          (body.operation==='resume'&&!uuid.test(input?.interrupt_request_id||'')))
          return response({error:'Invalid switch records'},400);
        const result=await deps.rest('rpc/switch_customer_interaction',{method:'POST',body:JSON.stringify({p_request_id:body.request_id,p_actor:await deps.actor(req),p_input:{...input,operation:body.operation}})});
        return response({switch:result});
      }
      if(body?.operation!=null||!validRecord(input)) return response({error:'Invalid record; only manual capture is connected'},400);
      const record=await deps.rest('rpc/save_customer_interaction',{method:'POST',body:JSON.stringify({p_request_id:body.request_id,p_actor:await deps.actor(req),p_input:input})});
      return response({interaction:record});
    } catch(error) {
      const code=(error as {code?:string})?.code;
      if(['40001','23505'].includes(code||'')) return response({error:'Conflict: reload and reconcile before saving',code},409);
      if(['22023','22007','22008','22P02','23503','23514','23502'].includes(code||'')) return response({error:'Invalid record',code},400);
      const status=(error as {status?:number})?.status===403?403:503;
      return response({error:status===403?'Forbidden':'Storage unavailable; preserve your draft and retry with the same request ID'},status);
    }
  };
}
