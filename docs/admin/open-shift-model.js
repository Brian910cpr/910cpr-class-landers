(function(root){
  "use strict";
  const MIN=60000;
  const parsed=value=>{const d=value instanceof Date?new Date(value):new Date(value);return Number.isFinite(+d)?d:null;};
  function dayBounds(key,zone="America/New_York"){
    function instant(day){
      const target=Date.parse(day+"T00:00:00Z");let result=target;
      for(let i=0;i<3;i++){
        const parts=Object.fromEntries(new Intl.DateTimeFormat("en-CA",{timeZone:zone,year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",second:"2-digit",hourCycle:"h23"}).formatToParts(new Date(result)).map(p=>[p.type,p.value]));
        const wall=Date.UTC(+parts.year,+parts.month-1,+parts.day,+parts.hour,+parts.minute,+parts.second);
        result+=target-wall;
      }
      return new Date(result);
    }
    const next=new Date(key+"T12:00:00Z");next.setUTCDate(next.getUTCDate()+1);
    return {start:instant(key),end:instant(next.toISOString().slice(0,10))};
  }
  function calculate({date,sessions=[],events=[],policy,now=new Date(),sourceStatus=[],scheduleHealth=null}){
    const {start:dayStart,end:dayEnd}=dayBounds(date,policy.timezone);
    const diagnostics=[],occupied=[],blocks=[],edges=[],candidates=[],accepted=[],rejected=[],windows=[],freeIntervals=[];
    if(scheduleHealth){
      const published=parsed(scheduleHealth.generatedAt);
      if(scheduleHealth.failed||!published||+now-+published>policy.maxSourceAgeMinutes*MIN||+published-+now>5*MIN)
        diagnostics.push({code:"schedule_source_stale_or_failed",instructor:"unknown"});
    }
    const profiles=policy.instructors||[];
    const instructor=value=>{const name=String(value||"").trim().toLowerCase();return profiles.find(p=>[p.instructor_key,p.display_name,...(p.aliases||[])].some(v=>String(v).toLowerCase()===name))?.instructor_key||"unknown";};
    const venue=value=>{const name=String(value||"").toLowerCase();return policy.locations.find(l=>[l.location_key,l.canonical_public_location,...l.aliases,...l.resources].some(v=>String(v).toLowerCase()===name))?.location_key||policy.travel.rules.find(r=>(r.match_any||[]).some(v=>name.includes(String(v).toLowerCase())))?.location_key||String(value||"unknown");};
    function travel(from,to,who){
      if(from===to&&from!=="unknown")return policy.cleanupMinutes||0;
      if(who!==policy.travel.instructor_key)return null;
      const rule=policy.travel.rules.find(r=>(r.location_key!=="shipyard"&&(r.location_key===to||r.location_key===from)));
      return (rule?.minutes_each_way??policy.travel.unknown_offsite_minutes)+(policy.cleanupMinutes||0);
    }
    for(const row of sessions){
      if(["cancelled","canceled","draft"].includes(String(row.status||row.registration_status||"").toLowerCase())||row.occupancy?.reserves_customer_availability===false)continue;
      const start=parsed(row._start||row.start_at||row.start),cid=String(row.course_id||row.course_number||row.course?.course_id||"");
      if(!start)continue;
      const who=instructor(row.lead_instructor_name||row.instructor||row.instructor_name),id=String(row.session_id||row.id||row.class_id||"unknown-session");
      let end=parsed(row._end||row.end_at||row.end),durationSource="source_interval";
      if(!end||end<=start){
        const duration=Number(row.inferred_scheduler_consumption_minutes||row.scheduler_consumption_minutes||policy.occupancyMinutes[cid]);
        if(!Number.isFinite(duration)||duration<=0){if(start>=+dayStart-24*60*MIN&&start<dayEnd)diagnostics.push({code:"unresolved_occupancy_duration",sourceId:id,instructor:who,start});continue;}
        end=new Date(+start+duration*MIN);durationSource="course_consumption_rule";
      }
      if(end<+dayStart-policy.travel.unknown_offsite_minutes*MIN||start>+dayEnd+policy.travel.unknown_offsite_minutes*MIN)continue;
      occupied.push({id,start,end,instructor:who,location:venue(row.location_name||row.location_display||row.location),anchor:true,headcount:row.registered_count??null,durationSource,courseId:cid});
    }
    for(const row of events){
      if(String(row.status||"").toLowerCase()==="cancelled"||String(row.status||"").toLowerCase()==="canceled")continue;
      const source=policy.sources.find(s=>s.calendar_source_key===row.source_key);
      if(!source||!source.active)continue;
      const start=parsed(row._start||row.start),end=parsed(row._end||row.end);if(!start||!end||end<=start){diagnostics.push({code:"invalid_calendar_interval",sourceId:row.source_key,instructor:source.instructor_key});continue;}
      if(end<+dayStart-policy.travel.unknown_offsite_minutes*MIN||start>+dayEnd+policy.travel.unknown_offsite_minutes*MIN)continue;
      const who=source.instructor_key,location=venue(row.location||source.default_location_key),title=String(row.title||row._name||"").trim().toUpperCase();
      if(source.mode==="explicit_availability"&&["HARD","SOFT"].includes(title)){
        if(start<dayEnd&&end>dayStart)windows.push({start:new Date(Math.max(+start,+dayStart)),end:new Date(Math.min(+end,+dayEnd+60*MIN)),instructor:who,location,sourceId:row.source_key+":"+start.toISOString()});
      }else if(source.mode==="inverse_blocking"||(source.mode==="explicit_availability"&&title==="UNAVAILABLE")){
        occupied.push({id:row.source_key+":"+start.toISOString(),start,end,instructor:who,location,anchor:false});
      }else if(source.mode==="occupancy"&&title.startsWith("CONFIRMED CLASS -")){
        occupied.push({id:row.source_key+":"+start.toISOString(),start,end,instructor:who,location,anchor:true});
      }
      // Unclassified personal-calendar events never become work commitments.
    }
    for(const profile of profiles){
      const source=policy.sources.find(s=>s.calendar_source_key===profile.calendar_source_key);
      const status=sourceStatus.find(s=>s.source_key===profile.calendar_source_key);
      const fresh=status&&status.export_status==="ok"&&parsed(status.generated_at)&&(+now-+parsed(status.generated_at))<=policy.maxSourceAgeMinutes*MIN&&(+now-+parsed(status.generated_at))>=-5*MIN;
      if(!fresh){diagnostics.push({code:"availability_source_stale_or_failed",instructor:profile.instructor_key,sourceId:profile.calendar_source_key});continue;}
      if(source?.mode==="inverse_blocking"){
        for(const container of policy.containers.filter(c=>c.status==="active"&&instructor(c.instructor_name)===profile.instructor_key&&date>=c.first_valid_date&&date<=c.last_valid_date)){
          windows.push({start:dayStart,end:new Date(+dayEnd+(date<container.last_valid_date?60:0)*MIN),instructor:profile.instructor_key,location:venue(container.location_name),sourceId:container.container_id});
        }
      }
    }
    const unsafe=new Set(diagnostics.filter(d=>d.code!=="availability_source_stale_or_failed").map(d=>d.instructor));
    const stale=new Set(diagnostics.filter(d=>d.code==="availability_source_stale_or_failed").map(d=>d.instructor));
    const validWindows=windows.filter(w=>!unsafe.has(w.instructor)&&!unsafe.has("unknown")&&!stale.has(w.instructor));
    const real=occupied.filter(x=>x.anchor).sort((a,b)=>a.instructor.localeCompare(b.instructor)||a.start-b.start);
    for(const item of real){
      const last=blocks[blocks.length-1];
      const interrupted=last&&occupied.some(b=>b.instructor===item.instructor&&!last.sourceIds.includes(b.id)&&b.id!==item.id&&b.start<item.start&&b.end>last.end);
      if(last&&last.instructor===item.instructor&&last.location===item.location&&item.start<=+last.end+(policy.cleanupMinutes||0)*MIN&&!interrupted){last.end=new Date(Math.max(+last.end,+item.end));last.sourceIds.push(item.id);}
      else blocks.push({id:"block:"+item.id,start:item.start,end:item.end,instructor:item.instructor,location:item.location,sourceIds:[item.id]});
    }
    function add(course,start,w,edge){candidates.push({courseId:course.id,name:course.name,start,end:new Date(+start+course.minutes*MIN),instructor:w.instructor,location:w.location,sourceWindow:w.sourceId,edgeId:edge?.id,sourceIds:edge?.sourceIds||[],mode:edge?"edge":"free",reasons:[]});}
    for(const w of validWindows){
      const planted=blocks.filter(b=>b.instructor===w.instructor&&b.start<dayEnd&&b.end>=dayStart);
      if(planted.length){
        for(const block of planted)for(const side of ["left","right"]){
          const edge={id:block.id+":"+side,time:side==="left"?block.start:block.end,sourceIds:block.sourceIds,instructor:w.instructor};
          if(!edges.some(e=>e.id===edge.id))edges.push(edge);
          const gap=travel(side==="left"?w.location:block.location,side==="left"?block.location:w.location,w.instructor);
          for(const course of policy.shortSkills){
            const start=new Date(+edge.time+(side==="left"?-(course.minutes+(gap||0)):(gap||0))*MIN);
            add(course,start,w,edge);if(gap===null)candidates[candidates.length-1].reasons.push("unresolved_travel");
          }
        }
      }else{
        let intervals=[{start:w.start,end:w.end}];
        for(const busy of occupied.filter(b=>b.instructor===w.instructor||b.instructor==="unknown")){
          const before=travel(w.location,busy.location,w.instructor),after=travel(busy.location,w.location,w.instructor);
          if(before===null||after===null){diagnostics.push({code:"unresolved_travel",instructor:w.instructor,sourceId:busy.id});intervals=[];break;}
          const bs=+busy.start-before*MIN,be=+busy.end+after*MIN;
          intervals=intervals.flatMap(i=>be<=+i.start||bs>=+i.end?[i]:[...(+i.start<bs?[{start:i.start,end:new Date(bs)}]:[]),...(be<+i.end?[{start:new Date(be),end:i.end}]:[])]);
        }
        for(const i of intervals){
          const step=(+i.end-+i.start)>=180*MIN?60:30;freeIntervals.push({...i,instructor:w.instructor,location:w.location,stepMinutes:step,sourceWindow:w.sourceId});
          for(const course of policy.shortSkills)for(let time=+i.start;time+course.minutes*MIN<=+i.end;time+=step*MIN)add(course,new Date(time),w);
        }
      }
    }
    const unique=new Map();
    for(const candidate of candidates){
      const key=[candidate.courseId,+candidate.start,candidate.instructor,candidate.location].join("|");
      const old=unique.get(key);if(old){old.sourceIds=[...new Set([...old.sourceIds,...candidate.sourceIds])];old.edgeIds=[...new Set([...old.edgeIds,...(candidate.edgeId?[candidate.edgeId]:[])])];}
      else unique.set(key,{...candidate,edgeIds:candidate.edgeId?[candidate.edgeId]:[]});
    }
    for(const c of unique.values()){
      const course=policy.shortSkills.find(x=>x.id===c.courseId),profile=profiles.find(x=>x.instructor_key===c.instructor);
      if(!profile?.allowed_course_groups.includes(course.family))c.reasons.push("instructor_not_qualified");
      if(course.durationConflict)c.reasons.push("unresolved_course_duration");
      if(course.minutes>60)c.reasons.push("outside_short_skills_rule");
      if(c.start<dayStart||c.start>=dayEnd||!validWindows.some(w=>w.instructor===c.instructor&&w.location===c.location&&c.start>=w.start&&c.end<=w.end))c.reasons.push("outside_source_availability");
      if(c.start<+now+policy.minimumLeadMinutes*MIN)c.reasons.push("lead_time");
      for(const b of occupied.filter(x=>x.instructor===c.instructor||x.instructor==="unknown")){
        const before=travel(c.location,b.location,c.instructor),after=travel(b.location,c.location,c.instructor);
        if(before===null||after===null)c.reasons.push("unresolved_travel:"+b.id);
        else if(!(+c.end+before*MIN<=+b.start||+c.start>=+b.end+after*MIN))c.reasons.push("occupied_or_travel:"+b.id);
      }
      for(const b of occupied.filter(x=>x.instructor!==c.instructor&&x.instructor!=="unknown"&&x.location===c.location)){
        if(c.start<b.end&&b.start<c.end)c.reasons.push("location_conflict:"+b.id);
      }
      if(c.reasons.length)rejected.push(c);else accepted.push(c);
    }
    return {occupied,blocks,edges,candidates:[...unique.values()],accepted,rejected,freeIntervals,diagnostics,windows:validWindows};
  }
  const api={calculate,dayBounds};root.OpenShiftModel=api;if(typeof module!=="undefined"&&module.exports)module.exports=api;
})(typeof window!=="undefined"?window:globalThis);
