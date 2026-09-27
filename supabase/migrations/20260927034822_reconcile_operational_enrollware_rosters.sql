-- #297: extend the existing ingest -> canonical Session/Registration promotion.
-- Historical imports remain historical. Operational snapshots require complete,
-- current source evidence; fetching the database must never renew that evidence.
alter table public.class_sessions
  add column if not exists external_reconciliation jsonb not null default '{}'::jsonb,
  add column if not exists external_session_evidence jsonb not null default '{}'::jsonb;

create or replace function public.reconcile_enrollware_roster_batch(p_rows jsonb, p_source_sha256 text)
returns jsonb language plpgsql security invoker set search_path = pg_catalog as $$
<<roster>>
declare
  s jsonb; r jsonb; old_registration jsonb; proof jsonb; fact uuid; job uuid;
  session_id uuid; customer_id uuid; registration_id uuid; course_id uuid;
  location_id uuid; instructor_id uuid; matches integer; observed timestamptz;
  start_time timestamptz; end_time timestamptz; previous_observed timestamptz;
  external_id text; reg_id text; canonical_status text; email_key text;
  active_ids jsonb; touched integer := 0; quarantined integer := 0; result jsonb := '[]';
begin
  if jsonb_typeof(p_rows) is distinct from 'array' or jsonb_array_length(p_rows)>500
     or p_source_sha256 is null or p_source_sha256 !~ '^[a-f0-9]{64}$' then
    raise exception 'invalid roster batch';
  end if;
  -- Serialize reconciliation, including cross-session reschedules and retries.
  perform pg_advisory_xact_lock(hashtextextended('enrollware_operational_reconciliation',0));
  if exists(select 1 from jsonb_array_elements(p_rows) x group by x->>'external_class_id' having count(*)>1)
     or exists(select 1 from jsonb_array_elements(p_rows) x cross join lateral jsonb_array_elements(x->'registrations') y
               group by y->>'external_registration_id' having count(*)>1) then
    raise exception 'duplicate external class or registration identity in batch';
  end if;
  insert into public.ingest_jobs(source_kind,source_name,source_ref,sha256,mime_type,status,
      parser_status,ai_status,review_status,document_type,metadata,started_at,attempt_count)
  values('enrollware_roster','authoritative current roster','enrollware/admin',p_source_sha256,
      'application/json','processing','complete','not_needed','none','enrollware_complete_roster',
      jsonb_build_object('importer','reconcile_enrollware_roster_batch','schema_version',1),now(),1)
  on conflict(sha256) where sha256 is not null do update set updated_at=now()
  returning id into job;

  for s in select value from jsonb_array_elements(p_rows) loop
    external_id := s->>'external_class_id'; session_id := null; observed := null;
    insert into public.ingest_facts(ingest_job_id,fact_type,source_locator,proposed_value,
        deterministic_key,confidence,resolution)
    values(job,'enrollware_committed_session',jsonb_build_object('external_class_id',external_id,
        'source_url',s->>'source_url','source_observed_at',s->>'source_observed_at'),
        s - 'registrations', 'session:'||coalesce(external_id,'missing'),1,'needs_review')
    on conflict(ingest_job_id,deterministic_key) where deterministic_key is not null
      do update set proposed_value=excluded.proposed_value returning id into fact;
    begin
      if external_id is null or external_id !~ '^[0-9]+$' or s->>'committed' is distinct from 'true'
         or s->>'complete_roster' is distinct from 'true'
         or coalesce(s->>'source_kind','') not in ('authenticated_enrollware_roster','authoritative_enrollware_export')
         or nullif(s->>'source_url','') is null
         or jsonb_typeof(s->'registrations') is distinct from 'array'
         or (s->>'roster_count')::integer is distinct from jsonb_array_length(s->'registrations') then
        raise exception 'incomplete_or_invalid_source';
      end if;
      observed := (s->>'source_observed_at')::timestamptz;
      if observed is null or observed < now()-interval '60 minutes' or observed>now()+interval '5 minutes' then
        raise exception 'stale_or_invalid_source_timestamp';
      end if;
      start_time := (s->>'start_at')::timestamptz; end_time := (s->>'end_at')::timestamptz;
      if start_time is null or end_time is null or end_time<=start_time
         or nullif(s->>'duration_basis','') is null then raise exception 'unproven_session_window'; end if;
      select count(*),min(id::text)::uuid into matches,course_id from public.courses where course_key=s->>'course_key';
      if matches<>1 then raise exception 'unresolved_course'; end if;
      select count(*),min(id::text)::uuid into matches,location_id from public.locations
        where location_key=s->>'location_key' and scheduling_status='active';
      if matches<>1 then raise exception 'unresolved_active_location'; end if;
      select count(*),min(id::text)::uuid into matches,instructor_id from public.people where person_key=s->>'instructor_key';
      if matches<>1 then raise exception 'unresolved_instructor'; end if;
      select count(*),min(id::text)::uuid into matches,session_id from public.class_sessions cs where cs.external_class_id=external_id;
      if matches>1 then raise exception 'ambiguous_external_class_id'; end if;
      if session_id is not null then
        if exists(select 1 from public.class_sessions cs where cs.id=session_id
                   and (registration_backend<>'enrollware' or record_scope<>'operational')) then
          raise exception 'conflicting_session_authority';
        end if;
        select (external_reconciliation->>'source_observed_at')::timestamptz into previous_observed
          from public.class_sessions cs where cs.id=session_id;
        if previous_observed>observed then raise exception 'older_than_current_reconciliation'; end if;
      else
        insert into public.class_sessions(source,status,record_scope,course_id,start_at,end_at,timezone,
          consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,
          registration_backend,visibility,registration_status,external_class_id)
        values('enrollware_reconciled','scheduled','operational',course_id,start_time,end_time,'America/New_York',
          (s->>'consumption_start_at')::timestamptz,(s->>'consumption_end_at')::timestamptz,
          instructor_id,location_id,(s->>'max_students')::integer,'enrollware','unlisted','external',external_id)
        returning id into session_id;
      end if;
      update public.class_sessions cs set course_id=roster.course_id,
        start_at=start_time,end_at=end_time,lead_instructor_id=instructor_id,
        location_id=roster.location_id,
        consumption_start_at=(s->>'consumption_start_at')::timestamptz,
        consumption_end_at=(s->>'consumption_end_at')::timestamptz,
        external_course_id=s->>'external_course_id', external_location_id=s->>'external_location_id',
        external_instructor_id=s->>'external_instructor_id',course_sched_id=s->>'course_sched_id',
        max_students=(s->>'max_students')::integer,registration_url=s->>'registration_url',
        source_location_label=s->>'source_location_label',source_instructor_label=s->>'source_instructor_label',
        source_client_label=s->>'source_client_label',external_session_evidence=(s-'registrations')||jsonb_build_object('ingest_job_id',job),
        updated_at=now() where cs.id=session_id;

      for r in select value from jsonb_array_elements(s->'registrations') loop
        reg_id:=r->>'external_registration_id'; customer_id:=null; registration_id:=null;
        canonical_status:=case lower(r->>'status') when 'pending' then 'registered' when 'registered' then 'registered'
          when 'confirmed' then 'confirmed' when 'complete' then 'completed' when 'completed' then 'completed'
          when 'canceled' then 'canceled' when 'cancelled' then 'canceled' when 'no show' then 'no_show'
          when 'no-show' then 'no_show' when 'rescheduled' then 'rescheduled' else null end;
        if reg_id is null or reg_id !~ '^[0-9]+$' or canonical_status is null then
          raise exception 'unresolved_registration_identity_or_status'; end if;
        select count(*),min(id::text)::uuid into matches,registration_id from public.registrations
          where external_registration_id=reg_id and registration_source in ('enrollware','enrollware_history','enrollware_reconciled');
        if matches>1 then raise exception 'ambiguous_external_registration_id'; end if;
        if registration_id is not null then
          select rr.customer_id into customer_id from public.registrations rr where id=registration_id;
        else
          email_key:=nullif(lower(btrim(r->>'email')),'');
          if email_key is null or nullif(r->>'first_name','') is null or nullif(r->>'last_name','') is null then
            raise exception 'unresolved_customer_identity'; end if;
          perform pg_advisory_xact_lock(hashtextextended('historical_customer|email:'||email_key,0));
          select count(*),min(id::text)::uuid into matches,customer_id from public.customers
            where lower(btrim(email))=email_key and lower(btrim(first_name))=lower(btrim(r->>'first_name'))
              and lower(btrim(last_name))=lower(btrim(r->>'last_name'));
          if matches>1 then raise exception 'ambiguous_customer_identity'; end if;
          if customer_id is null then
            insert into public.customers(first_name,last_name,email,phone)
            values(r->>'first_name',r->>'last_name',email_key,nullif(r->>'phone','')) returning id into customer_id;
          end if;
          select id into registration_id from public.registrations rr
            where rr.customer_id=roster.customer_id and rr.class_session_id=session_id;
          if registration_id is not null and exists(select 1 from public.registrations where id=registration_id
              and (external_registration_id is not null or registration_source not in ('enrollware','enrollware_history','enrollware_reconciled'))) then
            raise exception 'conflicting_registration_authority'; end if;
        end if;
        select jsonb_build_object('class_session_id',class_session_id,'status',status,'external_registration_id',external_registration_id)
          into old_registration from public.registrations where id=registration_id;
        if registration_id is null then
          insert into public.registrations(customer_id,class_session_id,status,registration_source,external_registration_id,created_at)
          values(customer_id,session_id,canonical_status,'enrollware_reconciled',reg_id,
            coalesce((r->>'registered_at')::timestamptz,observed)) returning id into registration_id;
        end if;
        -- A moved registration invalidates the former roster proof until that
        -- class is reconciled too. No change is sent back to Enrollware.
        update public.class_sessions cs set external_reconciliation='{}'::jsonb
          where cs.id=(old_registration->>'class_session_id')::uuid and cs.id<>session_id;
        update public.registrations set class_session_id=session_id,status=canonical_status,
          external_registration_id=reg_id,external_reconciled_at=observed,
          external_reconciliation_evidence=jsonb_build_object('ingest_job_id',job,'source_observed_at',observed,'external_class_id',external_id),
          updated_at=now() where id=registration_id;
        insert into public.ingest_facts(ingest_job_id,fact_type,source_locator,proposed_value,matched_entity_type,
          matched_entity_id,confidence,resolution,resolution_reason,deterministic_key,committed_at,resolved_at)
        values(job,'enrollware_registration',jsonb_build_object('external_registration_id',reg_id,'external_class_id',external_id),
          jsonb_build_object('previous',old_registration,'status',canonical_status,'class_session_id',session_id),
          'registration',registration_id,1,'committed','exact source registration identity','registration:'||reg_id,now(),now())
        on conflict(ingest_job_id,deterministic_key) where deterministic_key is not null do nothing;
      end loop;

      -- Complete roster absence ends only source-owned active relationships.
      -- Record the old relationship, never delete it or infer absence from mail.
      insert into public.ingest_facts(ingest_job_id,fact_type,source_locator,proposed_value,matched_entity_type,
        matched_entity_id,confidence,resolution,resolution_reason,deterministic_key,committed_at,resolved_at)
      select job,'enrollware_registration_absence',jsonb_build_object('external_class_id',external_id),
        jsonb_build_object('previous_status',rr.status,'external_registration_id',rr.external_registration_id),
        'registration',rr.id,1,'committed','absent from current complete roster','absent:'||rr.id,now(),now()
      from public.registrations rr where rr.class_session_id=session_id and rr.status in ('registered','confirmed','completed')
        and rr.registration_source in ('enrollware','enrollware_history','enrollware_reconciled')
        and not exists(select 1 from jsonb_array_elements(s->'registrations') x where x->>'external_registration_id'=rr.external_registration_id)
      on conflict(ingest_job_id,deterministic_key) where deterministic_key is not null do nothing;
      update public.registrations rr set status='canceled',external_reconciled_at=observed,
        external_reconciliation_evidence=jsonb_build_object('ingest_job_id',job,'reason','absent_from_complete_roster','source_observed_at',observed),updated_at=now()
      where rr.class_session_id=session_id and rr.status in ('registered','confirmed','completed')
        and rr.registration_source in ('enrollware','enrollware_history','enrollware_reconciled')
        and not exists(select 1 from jsonb_array_elements(s->'registrations') x where x->>'external_registration_id'=rr.external_registration_id);
      select coalesce(jsonb_agg(x->>'external_registration_id' order by x->>'external_registration_id'),'[]') into active_ids
        from jsonb_array_elements(s->'registrations') x where lower(x->>'status') in ('pending','registered','confirmed','complete','completed');
      proof:=jsonb_build_object('complete',true,'source_observed_at',observed,'reconciled_at',now(),
        'source_sha256',p_source_sha256,'ingest_job_id',job,'active_external_registration_ids',active_ids,
        'active_registration_count',jsonb_array_length(active_ids),'freshness_minutes',60);
      update public.class_sessions cs set external_reconciliation=proof where cs.id=session_id;
      update public.ingest_facts set resolution='committed',matched_entity_type='class_session',matched_entity_id=session_id,
        committed_at=now(),resolved_at=now(),resolution_reason='complete current source roster reconciled' where id=fact;
      touched:=touched+1;
      result:=result||jsonb_build_array(jsonb_build_object('external_class_id',external_id,'session_id',session_id,'status','reconciled'));
    exception when others then
      quarantined:=quarantined+1;
      -- Newer failed reconciliation is evidence that an older proof may no
      -- longer describe reality. An old replay cannot invalidate newer proof.
      update public.class_sessions cs set external_reconciliation='{}'::jsonb
        where cs.external_class_id=external_id and cs.registration_backend='enrollware'
          and observed >= (cs.external_reconciliation->>'source_observed_at')::timestamptz;
      update public.ingest_facts set resolution='needs_review',resolution_reason=sqlerrm where id=fact;
      insert into public.ingest_review_queue(ingest_job_id,ingest_fact_id,review_type,question,candidates,status)
      values(job,fact,'enrollware_reconciliation','Resolve canonical reconciliation: '||sqlerrm,'[]','open')
      on conflict(ingest_job_id,ingest_fact_id,review_type) where ingest_fact_id is not null do nothing;
      result:=result||jsonb_build_array(jsonb_build_object('external_class_id',external_id,'status','quarantined','reason',sqlerrm));
    end;
  end loop;
  update public.ingest_jobs set status=case when quarantined=0 then 'complete' else 'needs_review' end,
    completed_at=now(),updated_at=now(),metadata=metadata||jsonb_build_object('reconciled',touched,'quarantined',quarantined)
    where id=job;
  return jsonb_build_object('ingest_job_id',job,'reconciled',touched,'quarantined',quarantined,'sessions',result);
end;
$$;
revoke all on function public.reconcile_enrollware_roster_batch(jsonb,text) from public,anon,authenticated;
grant execute on function public.reconcile_enrollware_roster_batch(jsonb,text) to service_role;

create or replace function public.enrollware_reconciliation_health(p_from timestamptz,p_to timestamptz)
returns jsonb language sql stable security invoker set search_path=pg_catalog as $$
with latest as (
 select distinct on (source_locator->>'external_class_id') * from public.ingest_facts
 where fact_type='enrollware_committed_session'
 order by source_locator->>'external_class_id',created_at desc,id desc
), source_classes as (
 select source_locator->>'external_class_id' external_id,proposed_value->>'start_at' start_at,
   resolution, resolution_reason,source_locator->>'source_observed_at' observed_at,proposed_value->>'roster_count' roster_count
 from latest
), joined as (
 select coalesce(d.external_id,cs.external_class_id) external_class_id,cs.id session_id,
   coalesce(cs.start_at,d.start_at::timestamptz) start_at,cs.external_reconciliation proof,
   d.resolution,d.resolution_reason,d.roster_count,
   (select coalesce(jsonb_agg(r.external_registration_id order by r.external_registration_id),'[]'::jsonb)
    from public.registrations r where r.class_session_id=cs.id and r.status in ('registered','confirmed','completed')) actual
 from source_classes d full join public.class_sessions cs
   on cs.external_class_id=d.external_id and cs.registration_backend='enrollware' and cs.record_scope='operational'
 where (d.external_id is not null or cs.registration_backend='enrollware')
   and coalesce(cs.start_at,d.start_at::timestamptz)>=p_from and coalesce(cs.start_at,d.start_at::timestamptz)<p_to
), assessed as (
 select *,case when session_id is null then 'missing_canonical_session'
   when resolution='needs_review' then 'registration_evidence_without_canonical_relationship'
   when proof->>'complete' is distinct from 'true' then 'external_reconciliation_required'
   when (proof->>'source_observed_at')::timestamptz < now()-interval '60 minutes'
     or (proof->>'source_observed_at')::timestamptz > now()+interval '5 minutes' then 'stale_reconciliation'
   when proof->'active_external_registration_ids' is distinct from actual then 'registration_relationship_mismatch'
   else 'current' end status from joined
)
select jsonb_build_object('checked_at',now(),'freshness_minutes',60,'sessions',coalesce(jsonb_agg(jsonb_build_object(
  'external_class_id',external_class_id,'canonical_session_id',session_id,'start_at',start_at,'status',status,
  'source_observed_at',proof->>'source_observed_at','reconciled_at',proof->>'reconciled_at',
  'source_sha256',proof->>'source_sha256','reason',resolution_reason)), '[]'),
  'unknown_sessions',count(*) filter(where status<>'current'), 'total_sessions',count(*)) from assessed;
$$;
revoke all on function public.enrollware_reconciliation_health(timestamptz,timestamptz) from public,anon,authenticated;
grant execute on function public.enrollware_reconciliation_health(timestamptz,timestamptz) to service_role;
