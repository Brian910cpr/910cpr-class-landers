from datetime import datetime,timedelta

def blocks(rows):
 result=[]
 for row in sorted(rows,key=lambda r:(r['instructor'],r['location'],r['start'])):
  if row['end']<=row['start']:raise ValueError('unresolved duration')
  last=result[-1] if result else None
  if last and last['instructor']==row['instructor'] and last['location']==row['location'] and row['start']<=last['end']:
   last['end']=max(last['end'],row['end']);last['source_ids'].append(row['id'])
  else:result.append({**row,'source_ids':[row['id']]})
 return result

def candidates(real,window,courses):
 planted=[b for b in blocks(real) if b['instructor']==window['instructor'] and b['start'].date()<=window['start'].date()<=b['end'].date()]
 out=[]
 for course,minutes in courses.items():
  if planted:
   for b in planted:
    if b['location']!=window['location']:continue
    for side,start in [('pre',b['start']-timedelta(minutes=minutes)),('post',b['end'])]:
     if window['start']<=start<window['end']:out.append({'course':course,'start':start,'end':start+timedelta(minutes=minutes),'source_ids':b['source_ids'],'side':side})
  else:
   step=60 if (window['end']-window['start']).total_seconds()>=10800 else 30
   start=window['start']
   while start+timedelta(minutes=minutes)<=window['end']:
    out.append({'course':course,'start':start,'end':start+timedelta(minutes=minutes),'source_ids':[],'step':step});start+=timedelta(minutes=step)
 return out
