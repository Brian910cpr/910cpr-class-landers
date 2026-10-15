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

-- Inject a pre-write assertion into only verified native entrypoints. Preserve
-- every deployed body, overload, owner, security mode and existing grant.
do $patch$
declare f record; assertion text; replacement text; definition text; changed integer:=0;
begin
 for f in select p.oid,p.proname,p.prosrc,pg_get_function_arguments(p.oid) as args
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname in
    ('landerware_create_public_order','landerware_register','queue_public_registration_intent',
     'start_public_registration_intent','maxim_replace_registration')
 loop
  if position('owner_closure_prewrite_v1' in f.prosrc)>0 then continue; end if;
  case f.proname
   when 'landerware_create_public_order' then
    if position('p_offer jsonb' in f.args)>0 then
     assertion := 'perform public.assert_public_registration_open(nullif(p_offer->>''start_at'','''')::timestamptz,nullif(p_offer->>''end_at'','''')::timestamptz,p_external_class_id);';
    else assertion := 'perform public.assert_public_registration_open(null,null,p_external_class_id);'; end if;
   when 'landerware_register' then assertion := 'perform public.assert_public_registration_open(p_starts_at,null,p_external_session_id);';
   when 'queue_public_registration_intent' then assertion := 'perform public.assert_public_registration_open(p_starts_at,p_ends_at,p_external_class_id);';
   when 'start_public_registration_intent' then assertion := 'perform public.assert_public_registration_open(null,null,p_external_class_id);';
   when 'maxim_replace_registration' then assertion := 'perform public.assert_public_registration_open(p_starts_at,null,p_external_session_id);';
  end case;
  replacement := regexp_replace(f.prosrc, E'(?in)^([ \t]*)begin[ \t]*\r?$', E'\\1begin\n  -- owner_closure_prewrite_v1\n  '||assertion);
  if replacement=f.prosrc then raise exception 'closure_guard_missing_entry_begin:%',f.proname; end if;
  definition:=replace(pg_get_functiondef(f.oid),f.prosrc,replacement);
  execute definition;
  changed:=changed+1;
 end loop;
 if changed<>6 and changed<>0 then raise exception 'unexpected_native_guard_count:%',changed; end if;
end;
$patch$;
