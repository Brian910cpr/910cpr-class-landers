import {groupRequest} from './core.mjs';
const ORIGINS = new Set(['https://www.910cpr.com', 'https://910cpr.com']);
const PAGE = 'https://www.910cpr.com/request_group_session.html';
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
    const [saved] = await rest(`requirement_inquiries?id=eq.${id}&select=name,email,requirement_text,selected_course`);
    if (!saved) throw Error('receipt_missing');
    // A saved lead must also reach Brian's existing action board. No email delivery is claimed.
    await rest('production_board_cards?on_conflict=id',{method:'POST',headers:{prefer:'resolution=ignore-duplicates,return=minimal'},body:JSON.stringify({id,title:`Contact ${saved.name} about group training`.slice(0,180),project:'910CPR Group Training',owner:'Brian',lane:'decision',value_score:8,work_score:1,summary:`${saved.selected_course?.title} · ${saved.email}`,details:`Group request ${id}\n\n${saved.requirement_text}`,flags:['CUSTOMER IMPACT','REVENUE'],brian_override:false})});
    return reply(origin,{received:true,reference:id});
  } catch (error) {
    console.error('group_request_unavailable', error instanceof Error ? error.message : 'unknown');
    return reply(origin,{error:'Your request could not be confirmed yet. Please retry or call 910-395-5193.'},503);
  }
});
