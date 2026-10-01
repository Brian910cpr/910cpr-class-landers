-- Canonical scheduling lives in class_sessions. Workspaces retain identity and
-- workflow/documents but cannot independently move a linked class.
alter table public.landerware_sessions
  add column class_session_id uuid references public.class_sessions(id) on delete set null;
create unique index landerware_sessions_class_session_id_key
  on public.landerware_sessions(class_session_id);

-- Existing sync manifests carry exact canonical UUIDs. Do not fuzzy-match.
update public.landerware_sessions w set class_session_id=cs.id
from public.class_sessions cs
where w.requirements_manifest->>'source_class_session_id'=cs.id::text;

create or replace function public.invalidate_changed_external_session_proof()
returns trigger language plpgsql set search_path=pg_catalog
as $function$
begin
  if new.external_class_id is not null and
    (new.start_at,new.end_at,new.course_id,new.location_id,new.lead_instructor_id)
      is distinct from (old.start_at,old.end_at,old.course_id,old.location_id,old.lead_instructor_id) then
    new.external_reconciliation:='{}'::jsonb;
  end if;
  return new;
end
$function$;
revoke all on function public.invalidate_changed_external_session_proof() from public,anon,authenticated;
create trigger invalidate_changed_external_session_proof_trg
before update of start_at,end_at,course_id,location_id,lead_instructor_id on public.class_sessions
for each row execute function public.invalidate_changed_external_session_proof();

create or replace function public.sync_enrollware_class_session_to_landerware()
returns trigger language plpgsql security definer set search_path=pg_catalog
as $function$
declare
  v_course_key text; v_course_name text; v_location text; v_instructor text;
  v_manifest jsonb; v_lifecycle text;
begin
  if tg_op='DELETE' then
    update public.landerware_sessions set lifecycle_state='cancelled',
      requirements_manifest=requirements_manifest||jsonb_build_object(
        'source_deleted',true,'schedule_blocking',false,'last_synced_at',now()),
      updated_at=now()
    where requirements_manifest->>'source_class_session_id'=old.id::text;
    return old;
  end if;
  if new.record_scope<>'operational' then
    update public.landerware_sessions set
      requirements_manifest=requirements_manifest||jsonb_build_object(
        'record_scope',new.record_scope,'schedule_blocking',false,'last_synced_at',now()),
      updated_at=now() where class_session_id=new.id;
    return new;
  end if;
  select c.course_key,c.name into v_course_key,v_course_name
    from public.courses c where c.id=new.course_id;
  if v_course_key is null then raise exception 'canonical_workspace_course_missing'; end if;
  select coalesce(nullif(new.source_location_label,''),(select name from public.locations where id=new.location_id)) into v_location;
  select coalesce(nullif(new.source_instructor_label,''),(select display_name from public.people where id=new.lead_instructor_id)) into v_instructor;
  v_lifecycle:=case when new.status in ('cancelled','canceled','deleted') then 'cancelled'
                    when new.status='completed' then 'completed' else 'scheduled' end;
  v_manifest:=jsonb_build_object(
    'source_system','canonical_class_sessions','source_class_session_id',new.id,
    'source_class_session_source',new.source,'record_scope',new.record_scope,
    'registration_status',new.registration_status,'visibility',new.visibility,
    'schedule_blocking',new.status in ('scheduled','active'),
    'consumption_start_at',new.consumption_start_at,'consumption_end_at',new.consumption_end_at,
    'last_synced_at',now());
  -- The service-only importer may supply a verified proposal identity. Adoption
  -- preserves that workspace's documents and references; time alone never links.
  if new.external_session_evidence ? 'reconciles_workspace_id'
    and not exists(select 1 from public.landerware_sessions where class_session_id=new.id) then
    if new.external_session_evidence->>'workspace_link_basis'<>'verified_owner_request_and_current_roster' then
      raise exception 'unproven_workspace_link';
    end if;
    update public.landerware_sessions w set
      class_session_id=new.id,external_session_id=new.external_class_id,
      course_id=v_course_key,course_name=coalesce(v_course_name,v_course_key),
      starts_at=new.start_at,ends_at=new.end_at,location_name=v_location,instructor_name=v_instructor,
      lifecycle_state=v_lifecycle,
      requirements_manifest=w.requirements_manifest||v_manifest||jsonb_build_object(
        'proposal_before_reconciliation',jsonb_build_object('external_session_id',w.external_session_id,
          'course_id',w.course_id,'starts_at',w.starts_at,'lifecycle_state',w.lifecycle_state)),
      updated_at=now()
    where w.id::text=new.external_session_evidence->>'reconciles_workspace_id'
      and w.class_session_id is null and w.lifecycle_state='pending_proposal' and w.starts_at=new.start_at;
    if not found then raise exception 'workspace_proposal_identity_requires_review'; end if;
  end if;
  insert into public.landerware_sessions(
    class_session_id,external_session_id,course_id,course_name,starts_at,ends_at,
    location_name,instructor_name,lifecycle_state,provenance,requirements_manifest)
  values(new.id,coalesce(new.external_class_id,'class_session:'||new.id::text),
    v_course_key,coalesce(v_course_name,v_course_key),new.start_at,new.end_at,
    v_location,v_instructor,v_lifecycle,'canonical_class_sessions_sync',v_manifest)
  on conflict(class_session_id) do update set
    external_session_id=excluded.external_session_id,
    course_id=excluded.course_id,course_name=excluded.course_name,
    starts_at=excluded.starts_at,ends_at=excluded.ends_at,
    location_name=excluded.location_name,instructor_name=excluded.instructor_name,
    lifecycle_state=case
      when excluded.lifecycle_state in ('cancelled','completed') then excluded.lifecycle_state
      when public.landerware_sessions.lifecycle_state in ('create','pending_proposal','cancelled') then 'scheduled'
      else public.landerware_sessions.lifecycle_state end,
    requirements_manifest=public.landerware_sessions.requirements_manifest||excluded.requirements_manifest,
    updated_at=now();
  return new;
end
$function$;
revoke all on function public.sync_enrollware_class_session_to_landerware() from public,anon,authenticated;

create or replace function public.enforce_canonical_workspace_schedule()
returns trigger language plpgsql security definer set search_path=pg_catalog
as $function$
declare c public.class_sessions%rowtype; v_course_key text;
begin
  if tg_op='DELETE' then
    if old.class_session_id is not null then
      raise exception 'linked_workspace_delete_requires_canonical_session';
    end if;
    return old;
  end if;
  if tg_op='UPDATE' and old.class_session_id is not null
    and new.class_session_id is distinct from old.class_session_id
    and exists(select 1 from public.class_sessions where id=old.class_session_id) then
    raise exception 'canonical_workspace_link_is_immutable';
  end if;
  if new.class_session_id is null then return new; end if;
  select * into strict c from public.class_sessions where id=new.class_session_id;
  select course_key into v_course_key from public.courses where id=c.course_id;
  if new.starts_at is distinct from c.start_at or new.ends_at is distinct from c.end_at
    or new.course_id is distinct from v_course_key
    or new.external_session_id is distinct from coalesce(c.external_class_id,'class_session:'||c.id::text)
    or new.location_name is distinct from coalesce(nullif(c.source_location_label,''),(select name from public.locations where id=c.location_id))
    or new.instructor_name is distinct from coalesce(nullif(c.source_instructor_label,''),(select display_name from public.people where id=c.lead_instructor_id)) then
    raise exception 'edit_schedule_in_class_sessions';
  end if;
  return new;
end
$function$;
revoke all on function public.enforce_canonical_workspace_schedule() from public,anon,authenticated;
create trigger enforce_canonical_workspace_schedule_trg
before insert or update or delete on public.landerware_sessions
for each row execute function public.enforce_canonical_workspace_schedule();

-- Refresh existing projections and current operational classes through the same
-- trigger. No registration, class identity, time, or visibility is changed.
update public.class_sessions cs set updated_at=cs.updated_at
where cs.record_scope='operational' and
  (cs.start_at>=current_date-7 or exists(
    select 1 from public.landerware_sessions w where w.class_session_id=cs.id));

-- Exact linked Enrollware identity owns external roster evidence, regardless of
-- which checkout accepts new native registrations. Native registrations are preserved.
CREATE OR REPLACE FUNCTION public.reconcile_enrollware_roster_batch(p_rows jsonb, p_source_sha256 text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO 'pg_catalog'
AS $function$
<<roster>>
declare
  s jsonb; r jsonb; old_registration jsonb; proof jsonb; fact uuid; job uuid;
  session_id uuid; customer_id uuid; registration_id uuid; course_id uuid;
  location_id uuid; instructor_id uuid; matches integer; observed timestamptz;
  start_time timestamptz; end_time timestamptz; previous_observed timestamptz;
  external_id text; reg_id text; canonical_status text; email_key text;
  active_ids jsonb; touched integer := 0; classified integer := 0; quarantined integer := 0; result jsonb := '[]';
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
      observed := (s->>'source_observed_at')::timestamptz;
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

      if public.enrollware_non_session_decision(s) is not null then
        if exists(select 1 from public.class_sessions cs where cs.external_class_id=external_id) then
          raise exception 'non_session_conflicting_canonical_session';
        end if;
        -- Retain the complete private source evidence without fabricating a
        -- Session/Registration relationship for a non-instructional deadline.
        update public.ingest_facts set proposed_value=s,
          resolution='classified_non_session',resolved_at=now(),
          resolution_reason='owner_confirmed_renewal_deadline' where id=fact;
        classified:=classified+1;
        result:=result||jsonb_build_array(jsonb_build_object('external_class_id',external_id,
          'status','classified_non_session','classification','renewal_deadline'));
        continue;
      end if;

      if exists(select 1 from public.ingest_review_queue q join public.ingest_facts f on f.id=q.ingest_fact_id
          where q.review_type='enrollware_reconciliation' and q.status='resolved'
            and q.decision->>'owner_confirmed'='true' and q.decision->>'classification'='renewal_deadline'
            and f.source_locator->>'external_class_id'=external_id) then
        raise exception 'non_session_source_changed_requires_review';
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
                   and (registration_backend not in ('enrollware','landerware','manual') or record_scope<>'operational')) then
          raise exception 'conflicting_session_authority';
        end if;
        select (external_reconciliation->>'source_observed_at')::timestamptz into previous_observed
          from public.class_sessions cs where cs.id=session_id;
        if previous_observed>observed then raise exception 'older_than_current_reconciliation'; end if;
      else
        insert into public.class_sessions(source,status,record_scope,course_id,start_at,end_at,timezone,
          consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,
          registration_backend,visibility,registration_status,external_class_id,external_session_evidence)
        values('enrollware_reconciled','scheduled','operational',course_id,start_time,end_time,'America/New_York',
          (s->>'consumption_start_at')::timestamptz,(s->>'consumption_end_at')::timestamptz,
          instructor_id,location_id,(s->>'max_students')::integer,'enrollware','unlisted','external',external_id,s-'registrations')
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
          where external_registration_id=reg_id and registration_source in ('enrollware','enrollware_history','enrollware_reconciled','gmail_enrollware','enrollware_owner_reconciliation');
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
              and (external_registration_id is not null or registration_source not in ('enrollware','enrollware_history','enrollware_reconciled','gmail_enrollware','enrollware_owner_reconciliation'))) then
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
          external_reconciliation_evidence=external_reconciliation_evidence||jsonb_build_object('ingest_job_id',job,'source_observed_at',observed,'external_class_id',external_id),
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
        and rr.registration_source in ('enrollware','enrollware_history','enrollware_reconciled','gmail_enrollware','enrollware_owner_reconciliation')
        and not exists(select 1 from jsonb_array_elements(s->'registrations') x where x->>'external_registration_id'=rr.external_registration_id)
      on conflict(ingest_job_id,deterministic_key) where deterministic_key is not null do nothing;
      update public.registrations rr set status='canceled',external_reconciled_at=observed,
        external_reconciliation_evidence=external_reconciliation_evidence||jsonb_build_object('ingest_job_id',job,'reason','absent_from_complete_roster','source_observed_at',observed),updated_at=now()
      where rr.class_session_id=session_id and rr.status in ('registered','confirmed','completed')
        and rr.registration_source in ('enrollware','enrollware_history','enrollware_reconciled','gmail_enrollware','enrollware_owner_reconciliation')
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
        where cs.external_class_id=external_id and cs.registration_backend in ('enrollware','landerware','manual')
          and observed >= (cs.external_reconciliation->>'source_observed_at')::timestamptz;
      update public.ingest_facts set resolution='needs_review',resolution_reason=sqlerrm where id=fact;
      insert into public.ingest_review_queue(ingest_job_id,ingest_fact_id,review_type,question,candidates,status)
      values(job,fact,'enrollware_reconciliation','Resolve canonical reconciliation: '||sqlerrm,'[]','open')
      on conflict(ingest_job_id,ingest_fact_id,review_type) where ingest_fact_id is not null do nothing;
      result:=result||jsonb_build_array(jsonb_build_object('external_class_id',external_id,'status','quarantined','reason',sqlerrm));
    end;
  end loop;
  update public.ingest_jobs set status=case when quarantined=0 then 'complete' else 'needs_review' end,
    completed_at=now(),updated_at=now(),metadata=metadata||jsonb_build_object('reconciled',touched,'quarantined',quarantined,'classified_non_sessions',classified)
    where id=job;
  return jsonb_build_object('ingest_job_id',job,'reconciled',touched,'quarantined',quarantined,'classified_non_sessions',classified,'sessions',result);
end;
$function$;

CREATE OR REPLACE FUNCTION public.enrollware_reconciliation_health(p_from timestamp with time zone, p_to timestamp with time zone)
 RETURNS jsonb
 LANGUAGE sql
 STABLE
 SET search_path TO 'pg_catalog'
AS $function$
with latest as (
 select distinct on (source_locator->>'external_class_id') * from public.ingest_facts
 where fact_type='enrollware_committed_session'
 order by source_locator->>'external_class_id',created_at desc,id desc
), source_classes as (
 select source_locator->>'external_class_id' external_id,proposed_value->>'start_at' start_at,
   resolution,resolution_reason,source_locator->>'source_observed_at' observed_at,
   public.enrollware_non_session_decision(proposed_value) non_session_decision
 from latest
), joined as (
 select coalesce(d.external_id,cs.external_class_id) external_class_id,cs.id session_id,
   coalesce(cs.start_at,d.start_at::timestamptz) start_at,cs.external_reconciliation proof,
   d.resolution,d.resolution_reason,d.non_session_decision,d.observed_at,
   (select coalesce(jsonb_agg(r.external_registration_id order by r.external_registration_id),'[]'::jsonb)
    from public.registrations r where r.class_session_id=cs.id and r.status in ('registered','confirmed','completed')
      and (cs.registration_backend='enrollware' or r.external_registration_id is not null
        or r.registration_source in ('enrollware','enrollware_history','enrollware_reconciled','gmail_enrollware','enrollware_owner_reconciliation'))) actual
 from source_classes d full join public.class_sessions cs
   on cs.external_class_id=d.external_id and cs.record_scope='operational'
 where (d.external_id is not null or cs.external_class_id is not null)
   and coalesce(cs.start_at,d.start_at::timestamptz)>=p_from and coalesce(cs.start_at,d.start_at::timestamptz)<p_to
), assessed as (
 select *,case when non_session_decision is not null and session_id is not null then 'non_session_conflicting_canonical_session'
   when non_session_decision is not null then 'classified_non_session'
   when session_id is null then 'missing_canonical_session'
   when resolution='needs_review' then 'registration_evidence_without_canonical_relationship'
   when proof->>'complete' is distinct from 'true' then 'external_reconciliation_required'
   when (proof->>'source_observed_at')::timestamptz < now()-interval '60 minutes'
     or (proof->>'source_observed_at')::timestamptz > now()+interval '5 minutes' then 'stale_reconciliation'
   when proof->'active_external_registration_ids' is distinct from actual then 'registration_relationship_mismatch'
   else 'current' end status from joined
)
select jsonb_build_object('checked_at',now(),'freshness_minutes',60,'sessions',coalesce(jsonb_agg(jsonb_build_object(
  'external_class_id',external_class_id,'canonical_session_id',session_id,'start_at',start_at,'status',status,
  'source_observed_at',coalesce(proof->>'source_observed_at',observed_at),'reconciled_at',proof->>'reconciled_at',
  'source_sha256',proof->>'source_sha256','reason',case when status='classified_non_session' then 'owner_confirmed_renewal_deadline' else resolution_reason end,
  'non_session_classification',non_session_decision->>'classification',
  'approved_location_key',non_session_decision->>'approved_location_key')), '[]'),
  'unknown_sessions',count(*) filter(where status not in ('current','classified_non_session')),
  'classified_non_sessions',count(*) filter(where status='classified_non_session'),
  'total_sessions',count(*) filter(where status<>'classified_non_session')) from assessed;
$function$;


-- Transactional integration checks: changes inside this nested block roll back.
do $test$
declare selected_id uuid; workspace_id uuid; previous_start timestamptz; n integer;
begin
  if exists(select 1 from public.class_sessions cs
    left join public.landerware_sessions w on w.class_session_id=cs.id
    where cs.record_scope='operational' and cs.start_at>=current_date-7
      and (w.id is null or w.starts_at is distinct from cs.start_at or w.ends_at is distinct from cs.end_at)) then
    raise exception 'canonical_workspace_backfill_incomplete';
  end if;
  select cs.id,w.id,cs.start_at into selected_id,workspace_id,previous_start
    from public.class_sessions cs join public.landerware_sessions w on w.class_session_id=cs.id
    where cs.record_scope='operational' and cs.start_at>now() and cs.external_class_id is not null
    order by cs.start_at limit 1;
  if selected_id is not null then
    begin
      update public.class_sessions set
        start_at=start_at+interval '1 minute',end_at=end_at+interval '1 minute',
        consumption_start_at=consumption_start_at+interval '1 minute',
        consumption_end_at=consumption_end_at+interval '1 minute'
        where id=selected_id;
      select count(*) into n from public.landerware_sessions
        where id=workspace_id and class_session_id=selected_id and starts_at=previous_start+interval '1 minute';
      if n<>1 then raise exception 'moved_workspace_identity_was_not_preserved'; end if;
      begin
        update public.landerware_sessions set starts_at=starts_at+interval '1 minute' where id=workspace_id;
        raise exception 'independent_workspace_edit_was_allowed';
      exception when others then
        if sqlerrm<>'edit_schedule_in_class_sessions' then raise; end if;
      end;
      raise exception using errcode='Z0001',message='rollback_successful_projection_test';
    exception when sqlstate 'Z0001' then null;
    end;
    if (select start_at from public.class_sessions where id=selected_id) is distinct from previous_start then
      raise exception 'projection_test_failed_to_roll_back';
    end if;
  end if;
end
$test$;
