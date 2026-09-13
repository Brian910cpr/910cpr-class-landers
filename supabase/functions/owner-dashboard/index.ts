import { financeWindow, boardPrompts } from './core.mjs';
const ORIGINS = new Set(['https://www.910cpr.com','https://910cpr.com']);
const REPO = 'Brian910cpr/910cpr-class-landers';
let mailboxCache: { at:number; value:any } | null = null;
let mailboxPending: Promise<any> | null = null;
function response(req:Request, data:unknown, status=200) {
  const origin=req.headers.get('origin')||'';
  const headers:Record<string,string>={'content-type':'application/json','cache-control':'private, no-store','vary':'Origin','access-control-allow-headers':'content-type,x-hot-sync-admin-key','access-control-allow-methods':'GET,OPTIONS'};
  if(ORIGINS.has(origin)) headers['access-control-allow-origin']=origin;
  return new Response(JSON.stringify(data),{status,headers});
}
async function get(url:string, init:RequestInit={}) {
  const r=await fetch(url,{...init,signal:AbortSignal.timeout(15000)});
  if(!r.ok) throw new Error(`upstream_${r.status}`);
  return r;
}
async function authorized(req:Request) {
  const key=req.headers.get('x-hot-sync-admin-key');
  if(!key) return false;
  // One authority, shared with Operations. Corporate portal sessions are not owner access.
  const r=await fetch('https://schedule.910cpr.com/admin/hot-sync',{
    headers:{'x-hot-sync-admin-key':key},signal:AbortSignal.timeout(10000)
  });
  if(r.status===401||r.status===403) return false;
  if(!r.ok) throw new Error('admin_authority_unavailable');
  return true;
}
async function snapshot() {
  const url=Deno.env.get('SUPABASE_URL');
  const configured=Deno.env.get('SUPABASE_SECRET_KEYS');
  const key=configured?JSON.parse(configured).default:Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if(!url||!key) throw new Error('database_configuration_missing');
  return (await get(`${url}/rest/v1/rpc/owner_dashboard_snapshot`,{
    method:'POST',headers:{apikey:key,authorization:`Bearer ${key}`,'content-type':'application/json'},body:'{}'
  })).json();
}
async function readMailbox() {
  if(mailboxCache && Date.now()-mailboxCache.at<300000) return mailboxCache.value;
  if(mailboxPending) return mailboxPending;
  mailboxPending=(async()=>{
    const token=Deno.env.get('GITHUB_TOKEN');
    const headers:Record<string,string>={'User-Agent':'LanderWare-owner-monitor','Accept':'application/vnd.github+json'};
    if(token) headers.authorization=`Bearer ${token}`;
    const base=`https://api.github.com/repos/${REPO}`;
    const [root,issues]=await Promise.all([
      get(`${base}/contents/`,{headers}).then(r=>r.json()),
      get(`${base}/issues?state=open&sort=updated&direction=desc&per_page=100`,{headers}).then(r=>r.json())
    ]);
    const files=root.filter((f:any)=>/^Codex_(Reply|Read)_[a-zA-Z0-9_.-]+\.md$/.test(f.name)).slice(0,80);
    const receipts=await Promise.allSettled(files.map(async(f:any)=>{
      const text=await (await get(`https://raw.githubusercontent.com/${REPO}/main/${encodeURIComponent(f.name)}`)).text();
      const date=text.match(/\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|\s*UTC|[+-]\d{2}:\d{2})/i)?.[0];
      const time=date?Date.parse(date.replace(/\s*UTC/i,'Z').replace(' ','T')):NaN;
      const acknowledged=/^#\s+Codex read/im.test(text);
      const summary=text.split('\n').find((s:string)=>/^-\s/.test(s)&&!/^-[^a-z]*(?:Reviewed|Timestamp|Branch|Commit|State|Status)/i.test(s))?.replace(/^-\s*/, '').replace(/\*\*|`/g,'');
      const heading=text.split('\n').find((s:string)=>/^#\s/.test(s))?.replace(/^#+\s*/,'')||f.name.replace(/^Codex_(Reply|Read)_|\.md$/g,'').replace(/_/g,' ');
      const status=text.match(/(?:Work-item state|Work item state|State|Status)\s*:\s*\*{0,2}([A-Z_]+)/i)?.[1]||'';
      return {id:f.sha,actor:acknowledged?'ChatGPT':'Codex',to:acknowledged?'Codex':'ChatGPT',title:(summary||heading).slice(0,240),time:Number.isFinite(time)?new Date(time).toISOString():null,
        state:f.name.startsWith('Codex_Read_')?'Picked up by ChatGPT':'Awaiting ChatGPT',work_state:status,url:f.html_url,source:f.name};
    }));
    const open=issues.filter((i:any)=>!i.pull_request);
    const dispatches=open.filter((i:any)=>/^\[CODEX\]/i.test(i.title)).map((i:any)=>({
      id:`issue:${i.number}`,actor:i.number===216?'ChatGPT':'Owner / ChatGPT',to:'Codex',title:i.title.replace(/^\[CODEX\]\s*/i,''),
      time:i.created_at,state:'Open instruction',url:i.html_url,source:`Issue #${i.number}`
    }));
    const messages=[...receipts.filter(r=>r.status==='fulfilled').map((r:any)=>r.value),...dispatches]
      .sort((a,b)=>(Date.parse(b.time)||0)-(Date.parse(a.time)||0)).slice(0,40);
    const failed=receipts.filter(r=>r.status==='rejected').length;
    const value={state:failed?'partial':'connected',checked_at:new Date().toISOString(),messages,
      unread:files.filter((f:any)=>f.name.startsWith('Codex_Reply_')).length,
      coverage:files.length>=80||issues.length>=100?'Recent records; source limit reached':'Current root receipts and open instructions',
      blockers:open.filter((i:any)=>/\[BLOCKED\]/i.test(i.title)).map((i:any)=>({id:`issue:${i.number}`,category:'decision',tag:'CODEX BLOCKER',
        title:i.number===140?'Review HOT_SYNC access':i.title.replace(/\[[^\]]+\]/g,'').trim(),
        summary:'Open blocker. Check the requested account action and latest evidence.',href:i.html_url,label:'Review blocker',observed_at:i.updated_at}))};
    mailboxCache={at:Date.now(),value};
    return value;
  })();
  try { return await mailboxPending; }
  catch { return mailboxCache?{...mailboxCache.value,state:'stale'}:{state:'unavailable',messages:[],blockers:[],unread:null,checked_at:null}; }
  finally { mailboxPending=null; }
}
Deno.serve(async(req:Request)=>{
  const origin=req.headers.get('origin')||'';
  if(origin&&!ORIGINS.has(origin)) return response(req,{error:'Origin not allowed'},403);
  if(req.method==='OPTIONS') return response(req,{},200);
  if(req.method!=='GET') return response(req,{error:'Method not allowed'},405);
  try {
    if(!await authorized(req)) return response(req,{error:'Admin key not accepted'},401);
  } catch { return response(req,{error:'Admin access check is unavailable. Try again shortly.'},503); }
  const [db,mailbox]=await Promise.allSettled([snapshot(),readMailbox()]);
  const data=db.status==='fulfilled'?db.value:null;
  const handoffs=mailbox.status==='fulfilled'?mailbox.value:{state:'unavailable',messages:[],blockers:[]};
  const finance=financeWindow(data?.finance);
  const prompts=[...(data?boardPrompts(data.board):[]),...(handoffs.state==='connected'||handoffs.state==='partial'?handoffs.blockers:[]),...finance.prompts];
  return response(req,{generated_at:new Date().toISOString(),operations_state:data?'connected':'unavailable',
    ecards:data?.ecards||null,products:data?.products||null,upcoming:data?.upcoming||[],board:data?.board||[],finance,mailbox:handoffs,prompts});
});
