-- A newer incomplete/failed source must invalidate the old proof as well as
-- raise the ingest alarm. Replayed old evidence never refreshes or invalidates it.
do $$
declare definition text;
begin
  select pg_get_functiondef('public.reconcile_enrollware_roster_batch(jsonb,text)'::regprocedure) into definition;
  definition:=replace(definition,'      if external_id is null',
    E'      observed := (s->>''source_observed_at'')::timestamptz;\n      if external_id is null');
  execute definition;
end;
$$;
