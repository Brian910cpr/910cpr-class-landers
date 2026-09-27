-- The production location-authority trigger deliberately rejects operational
-- sessions at inactive locations. Keep its existing early importer diagnostic.
-- The previous exact-identity probe created no sessions or registrations there.
do $$
declare definition text;
begin
  select pg_get_functiondef('public.reconcile_enrollware_roster_batch(jsonb,text)'::regprocedure) into definition;
  definition:=replace(definition,
    'where location_key=s->>''location_key'';',
    'where location_key=s->>''location_key'' and scheduling_status=''active'';');
  definition:=replace(definition,'unresolved_location_identity','unresolved_active_location');
  execute definition;
end;
$$;
