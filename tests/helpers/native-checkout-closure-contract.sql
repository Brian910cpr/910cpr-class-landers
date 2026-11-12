-- Existing production closure-policy/guard source only; no wrapper rewrites or fixture bypass.
-- Compiled from docs/data/public-registration-closures.json. No business row writes.
create or replace function public.public_registration_closure_policy()
returns jsonb language sql immutable set search_path='' as $policy$
select '{"schemaVersion":"public-registration-closures.v1","closures":[{"id":"owner-oct21-20261015","startsAt":"2026-10-21T04:00:00Z","endsAt":"2026-10-22T04:00:00Z","timezone":"America/New_York","reason":"Registration is closed for October 21.","scope":"all_new_registrations","preserveExisting":true}]}'::jsonb;
$policy$;
revoke all on function public.public_registration_closure_policy() from public,anon,authenticated;
grant execute on function public.public_registration_closure_policy() to service_role;

create or replace function public.assert_public_registration_open(
 p_start timestamptz default null, p_end timestamptz default null, p_external_id text default null
) returns void language plpgsql security invoker set search_path='' as $guard$
declare c jsonb; window_start timestamptz; window_end timestamptz; source_row record;
begin
 for c in select value from jsonb_array_elements(public.public_registration_closure_policy()->'closures') loop
  window_start:=(c->>'startsAt')::timestamptz; window_end:=(c->>'endsAt')::timestamptz;
  if p_start < window_end and coalesce(greatest(p_end,p_start+interval '1 microsecond'),p_start+interval '1 microsecond') > window_start then
   raise exception 'registration_date_closed' using errcode='P0001';
  end if;
  -- Check actual facts as well as supplied timestamps. Workspace-only sessions
  -- have starts_at/ends_at and need no invented registration_status column.
  if nullif(trim(p_external_id),'') is not null then
   for source_row in
    select coalesce(s.consumption_start_at,s.start_at) as a,coalesce(s.consumption_end_at,s.end_at) as b
    from public.class_sessions s where (s.external_class_id=p_external_id or s.id::text=p_external_id)
      and s.status in ('scheduled','active')
    union all
    select w.starts_at,w.ends_at from public.landerware_sessions w
      where w.external_session_id=p_external_id or w.id::text=p_external_id
   loop
    if source_row.a < window_end and coalesce(greatest(source_row.b,source_row.a+interval '1 microsecond'),source_row.a+interval '1 microsecond') > window_start then
     raise exception 'registration_date_closed' using errcode='P0001';
    end if;
   end loop;
  end if;
 end loop;
end;
$guard$;
revoke all on function public.assert_public_registration_open(timestamptz,timestamptz,text) from public,anon,authenticated;
grant execute on function public.assert_public_registration_open(timestamptz,timestamptz,text) to service_role;
