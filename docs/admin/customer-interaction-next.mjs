// Selection only. Canonical records and task RPCs own lifecycle/completion.
export function eligibleInteraction(row,tasks,now=Date.now()){
  if(['new','in_progress'].includes(row.status))return true;
  if(row.status!=='follow_up_due')return false;
  return tasks.some(t=>t.interaction_id===row.id&&(t.status==='pending'||t.status==='proposed'||
    t.status==='snoozed'&&Number.isFinite(Date.parse(t.due_at))&&Date.parse(t.due_at)<=now));
}
async function all(client,collection){
  let cursor=null;const found=[],seen=new Set();
  do{
    const page=await client.list({collection,...(cursor??{})});
    found.push(...page.items);cursor=page.next_cursor;
    if(cursor){const key=JSON.stringify(cursor);if(seen.has(key))throw Error('Repeated NEXT cursor; queue incomplete.');seen.add(key)}
  }while(cursor);
  return [...new Map(found.map(row=>[row.id,row])).values()];
}
export async function findNextInteraction(client,exclude,now=Date.now()){
  const interactions=await all(client,'interactions'),tasks=await all(client,'tasks');
  if(tasks.some(t=>!['proposed','pending','snoozed','complete'].includes(t.status)))throw Error('Unknown task status; review queue.');
  const rank=row=>row.kind==='phone'&&row.status==='in_progress'?0:row.status==='follow_up_due'?1:2;
  return interactions.filter(row=>row.id!==exclude&&eligibleInteraction(row,tasks,now))
    .sort((a,b)=>rank(a)-rank(b)||String(a.created_at??'').localeCompare(String(b.created_at??''))||a.id.localeCompare(b.id))[0]??null;
}
