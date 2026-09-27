import {groupRequest} from './core.mjs';
const ORIGINS = new Set(['https://www.910cpr.com', 'https://910cpr.com']);
const PAGE = 'https://www.910cpr.com/group-training.html';
function reply(origin:string, data:unknown, status=200) {
  return new Response(JSON.stringify(data), {status, headers:{'content-type':'application/json', 'cache-control':'no-store', 'access-control-allow-origin':ORIGINS.has(origin)?origin:'https://www.910cpr.com', 'access-control-allow-headers':'content-type,apikey,authorization', 'access-control-allow-methods':'POST,OPTIONS', vary:'Origin'}});
}
function configuration() {
  const url = Deno.env.get('SUPABASE_URL');
  const configured = Deno.env.get('SUPABASE_SECRET_KEYS');
  const key = configured ? JSON.parse(configured).default : Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if (!url || !key) throw Error('database_unavailable');
  return {url, key};
}
async function rest(path:string, options:RequestInit={}) {
  const {url,key} = configuration();
  const r = await fetch(`${url}/rest/v1/${path}`, {...options, signal:AbortSignal.timeout(12000), headers:{apikey:key, authorization:`Bearer ${key}`, 'content-type':'application/json', prefer:'return=representation', ...options.headers}});
  if (!r.ok) throw Error(`database_${r.status}`);
  const text = await r.text();
  return text ? JSON.parse(text) : null;
}
const hash = async (value:string) => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))).map(x=>x.toString(16).padStart(2,'0')).join('');

async function notifyOwner(id:string, saved:any) {
  if (saved.delivery_status === 'sent') return;
  const key=Deno.env.get('RESEND_API_KEY'), to=Deno.env.get('ADMIN_NOTIFY_EMAIL'), from=Deno.env.get('REQUIREMENT_FROM_EMAIL');
  if (!key || !to || !from) {
    console.error('group_request_email_configuration_missing', id);
    await rest(`requirement_inquiries?id=eq.${id}`,{method:'PATCH',body:JSON.stringify({delivery_status:'configuration_error'})});
    return;
  }
  const message = {
    from, to:[to], reply_to:saved.email,
    subject:`New group training request: ${saved.name}`,
    text:`A group is waiting for a reply.\n\n${saved.requirement_text}\n\nProduction Board: https://www.910cpr.com/admin/production.html?card=${id}\nRequest ID: ${id}`
  };
  const response=await fetch('https://api.resend.com/emails',{
    method:'POST',signal:AbortSignal.timeout(12000),
    headers:{authorization:`Bearer ${key}`,'content-type':'application/json','Idempotency-Key':`group-request/${id}`},
    body:JSON.stringify(message)
  });
  const result=await response.json().catch(()=>({}));
  if (!response.ok || !result.id) {
    console.error('group_request_email_failed',id,response.status);
    await rest(`requirement_inquiries?id=eq.${id}`,{method:'PATCH',body:JSON.stringify({delivery_status:'failed'})});
    return;
  }
  await rest(`requirement_inquiries?id=eq.${id}`,{method:'PATCH',body:JSON.stringify({delivery_status:'sent',delivered_at:new Date().toISOString(),provider_message_id:String(result.id).slice(0,200)})});
}

Deno.serve(async (req:Request) => {
  const origin = req.headers.get('origin') || '';
  if (!ORIGINS.has(origin)) return reply(origin,{error:'Origin not allowed.'},403);
  if (req.method === 'OPTIONS') return reply(origin,{});
  if (req.method !== 'POST') return reply(origin,{error:'Method not allowed.'},405);
  let input;
  try {
    const raw = await req.text();
    if (new TextEncoder().encode(raw).length > 16384) return reply(origin,{error:'Please shorten the comments and try again.'},413);
    input = groupRequest(JSON.parse(raw));
  } catch (error) { return reply(origin,{error:error instanceof SyntaxError?'Invalid submission.':String(error.message)},400); }
  try {
    // A retry completes the same request, including recovery after a queue write failed.
    const digest = await hash(`${configuration().key}:group-request:${input.requestId}`);
    const id = `${digest.slice(0,8)}-${digest.slice(8,12)}-4${digest.slice(13,16)}-a${digest.slice(17,20)}-${digest.slice(20,32)}`;
    const prior = await rest(`requirement_inquiries?id=eq.${id}&select=id&limit=1`);
    if (!prior.length) {
      const ip = req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown';
      const ipHash = await hash(`${configuration().key}:${ip}`);
      const recent = await rest(`requirement_inquiries?ip_hash=eq.${ipHash}&created_at=gte.${encodeURIComponent(new Date(Date.now()-3600000).toISOString())}&select=id&limit=5`);
      if (recent.length >= 5) return reply(origin,{error:'Too many requests. Please call 910-395-5193 or try again later.'},429);
      await rest('requirement_inquiries?on_conflict=id',{method:'POST',headers:{prefer:'resolution=ignore-duplicates,return=minimal'},body:JSON.stringify({id,name:input.name,email:input.email,phone:input.phone||null,requirement_text:input.details,selected_course:{title:input.program,href:PAGE},page_title:'On-site group training request',page_url:PAGE,submitted_at:new Date().toISOString(),client_inquiry_id:input.requestId,ip_hash:ipHash,user_agent:(req.headers.get('user-agent')||'').slice(0,500),delivery_status:'pending'})});
    }
    const [saved] = await rest(`requirement_inquiries?id=eq.${id}&select=name,email,requirement_text,selected_course,delivery_status`);
    if (!saved) throw Error('receipt_missing');
    // A saved lead must be visible at the top of the owner queue, even if email is unavailable.
    const headcount=saved.requirement_text.match(/^Headcount: (.+)$/m)?.[1] || 'unknown size';
    await rest('production_board_cards?on_conflict=id',{method:'POST',headers:{prefer:'resolution=ignore-duplicates,return=minimal'},body:JSON.stringify({id,title:`P1: Reply to ${saved.name} about group training`.slice(0,180),project:'910CPR Group Training',owner:'Brian',lane:'decision',value_score:10,work_score:1,summary:`Unanswered lead · ${headcount} participants · ${saved.selected_course?.title} · ${saved.email}`,details:`Group request ${id}\n\n${saved.requirement_text}`,flags:['P1','CUSTOMER IMPACT','REVENUE','UNANSWERED GROUP LEAD'],brian_override:true,context_manifest:{owner_action:{root_action_id:`group-request:${id}`,action:`Reply to ${saved.name} about group training`,where:'Production Board > 910CPR Group Training',look_for:`Group request ${id} (${saved.selected_course?.title})`,reply_with:'Record the contact outcome on this card',do_not_touch:'Do not mark a class booked until date and price are confirmed',why:'This group requested training and is waiting for a reply'}}})});
    try { await notifyOwner(id,saved); }
    catch (error) { console.error('group_request_notification_unavailable',id,error instanceof Error?error.message:'unknown'); }
    return reply(origin,{received:true,reference:id});
  } catch (error) {
    console.error('group_request_unavailable', error instanceof Error ? error.message : 'unknown');
    return reply(origin,{error:'Your request could not be confirmed yet. Please retry or call 910-395-5193.'},503);
  }
});
