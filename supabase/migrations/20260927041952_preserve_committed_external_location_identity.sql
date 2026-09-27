-- #297 observes existing external commitments. A location being unavailable for
-- NEW scheduling must not erase a real source class or its registrations.
-- Keep the exact existing location and its scheduling status; never activate it.
do $$
declare definition text;
begin
  select pg_get_functiondef('public.reconcile_enrollware_roster_batch(jsonb,text)'::regprocedure) into definition;
  if position('where location_key=s->>''location_key'' and scheduling_status=''active''' in definition)=0 then
    raise exception 'expected location identity guard is missing';
  end if;
  definition:=replace(definition,
    'where location_key=s->>''location_key'' and scheduling_status=''active''',
    'where location_key=s->>''location_key''');
  definition:=replace(definition,'unresolved_active_location','unresolved_location_identity');
  execute definition;
end;
$$;
