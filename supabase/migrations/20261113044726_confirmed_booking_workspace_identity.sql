alter table public.class_sessions drop constraint class_sessions_operational_fields_check;
alter table public.class_sessions add constraint class_sessions_operational_fields_check check (
 record_scope <> 'operational' or (end_at is not null and consumption_start_at is not null and consumption_end_at is not null
 and (lead_instructor_id is not null or (source='confirmed_booking_intake'
 and coalesce(external_session_evidence->>'kind','')='registration_confirmation'
 and nullif(external_session_evidence->>'gmail_message_id','') is not null))));
CREATE OR REPLACE FUNCTION public.sync_enrollware_class_session_to_landerware()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog'
AS $function$
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
    if coalesce(new.external_session_evidence->>'workspace_link_basis','') not in ('verified_owner_request_and_current_roster','confirmed_registration_minimum_fields') then
      raise exception 'unproven_workspace_link';
    end if;
    update public.landerware_sessions w set
      class_session_id=new.id,external_session_id=coalesce(new.external_class_id,'class_session:'||new.id::text),
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
