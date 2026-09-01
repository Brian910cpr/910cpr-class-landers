do $review$
declare
  v_locations bigint;
  v_sessions bigint;
  v_hist_locations bigint;
  v_audit bigint;
  v_course uuid;
  v_active_location uuid;
  v_historical_location uuid;
  v_operational_location uuid;
begin
  select count(*) into v_locations from public.locations;
  select count(*) into v_sessions from public.class_sessions;
  if v_locations <> 36 or v_sessions <> 365 then
    raise exception 'baseline row counts changed: locations %, sessions %', v_locations, v_sessions;
  end if;

  select count(*) into v_hist_locations
  from public.locations where scheduling_status = 'historical_only';
  if v_hist_locations <> 28 then
    raise exception 'expected 28 pre-existing historical-only locations, got %', v_hist_locations;
  end if;
  if exists(select 1 from public.locations where scheduling_status = 'historical_only' and public) then
    raise exception 'historical-only location became public';
  end if;
  if exists(
    select 1 from public.class_sessions s
    join public.locations l on l.id = s.location_id
    where s.record_scope = 'operational' and l.scheduling_status <> 'active'
  ) then
    raise exception 'operational session references non-active location';
  end if;
  if exists(
    select 1 from public.class_sessions
    where record_scope = 'operational'
      and (lead_instructor_id is null or end_at is null
           or consumption_start_at is null or consumption_end_at is null)
  ) then
    raise exception 'existing operational session lost required fields';
  end if;

  select id into v_course from public.courses order by created_at limit 1;
  select id into v_active_location
  from public.locations where scheduling_status = 'active' order by id limit 1;
  select id into v_historical_location
  from public.locations where scheduling_status = 'historical_only' order by id limit 1;
  select location_id into v_operational_location
  from public.class_sessions where record_scope = 'operational' limit 1;

  perform set_config('app.location_status_reason','migration review unsafe transition test',true);
  begin
    update public.locations set scheduling_status = 'historical_only'
    where id = v_operational_location;
    raise exception 'location used by operational session became historical-only';
  exception when raise_exception then
    if sqlerrm not like 'a location referenced by an operational session%' then raise; end if;
  end;

  begin
    insert into public.class_sessions(
      source,status,record_scope,course_id,start_at,end_at,timezone,
      consumption_start_at,consumption_end_at,lead_instructor_id,location_id,
      max_students,registration_backend,visibility,registration_status
    ) values (
      'migration_review','scheduled','operational',v_course,'2026-12-01 14:00+00',null,
      'America/New_York','2026-12-01 14:00+00',null,null,v_active_location,
      1,'landerware','private','closed'
    );
    raise exception 'operational null instructor/end unexpectedly accepted';
  exception when check_violation or not_null_violation then null;
  end;

  begin
    insert into public.class_sessions(
      source,status,record_scope,course_id,start_at,end_at,timezone,
      consumption_start_at,consumption_end_at,lead_instructor_id,location_id,
      max_students,registration_backend,visibility,registration_status,
      historical_import_key,historical_imported_at
    ) values (
      'migration_review','completed','historical',v_course,'2020-01-01 14:00+00',null,
      'America/New_York',null,null,null,v_active_location,
      1,'landerware','private','closed','migration-review-null-truth',now()
    );
  exception when others then
    raise exception 'truthful historical nulls rejected: %', sqlerrm;
  end;

  begin
    insert into public.class_sessions(
      source,status,record_scope,course_id,start_at,end_at,timezone,
      consumption_start_at,consumption_end_at,lead_instructor_id,location_id,
      max_students,registration_backend,visibility,registration_status,
      historical_import_key,historical_imported_at
    ) values (
      'migration_review','completed','historical',v_course,'2020-01-02 14:00+00',null,
      'America/New_York',null,null,null,v_active_location,
      1,'landerware','public','closed','migration-review-public-history',now()
    );
    raise exception 'public historical session unexpectedly accepted';
  exception when check_violation then null;
            when raise_exception then
    if sqlerrm not like 'public sessions require operational scope%' then raise; end if;
  end;

  begin
    insert into public.class_sessions(
      source,status,record_scope,course_id,start_at,end_at,timezone,
      consumption_start_at,consumption_end_at,lead_instructor_id,location_id,
      max_students,registration_backend,visibility,registration_status
    )
    select 'migration_review','scheduled','operational',v_course,'2026-12-02 14:00+00',
      '2026-12-02 16:00+00','America/New_York','2026-12-02 14:00+00',
      '2026-12-02 16:00+00',lead_instructor_id,v_historical_location,1,
      'landerware','private','closed'
    from public.class_sessions where lead_instructor_id is not null limit 1;
    raise exception 'operational session at historical-only location unexpectedly accepted';
  exception when raise_exception then
    if sqlerrm not like 'operational sessions require an active/schedulable location%' then
      raise;
    end if;
  end;

  perform set_config('app.location_status_reason','',true);
  begin
    insert into public.locations(location_key,name,scheduling_status,public)
    values('migration-review-history-no-reason','Migration Review','historical_only',false);
    raise exception 'historical location without explicit reason unexpectedly accepted';
  exception when raise_exception then
    if sqlerrm not like 'explicit app.location_status_reason%' then raise; end if;
  end;

  perform set_config('app.location_status_reason','reviewed historical authority test',true);
  insert into public.locations(location_key,name,scheduling_status,public)
  values('migration-review-history-with-reason','Migration Review','historical_only',false);
  select count(*) into v_audit
  from public.location_scheduling_status_events
  where reason = 'reviewed historical authority test';
  if v_audit <> 1 then raise exception 'status audit event missing'; end if;

  if not exists(
    select 1 from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relname = 'location_scheduling_status_events'
      and c.relrowsecurity
  ) then raise exception 'audit table RLS disabled'; end if;
  if exists(
    select 1 from information_schema.role_table_grants
    where table_schema = 'public' and table_name = 'location_scheduling_status_events'
      and grantee in ('anon','authenticated')
  ) then raise exception 'browser grant exists on audit table'; end if;
end
$review$;
