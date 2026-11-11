-- Bound new full-course materialization to the original publication lease even
-- when PostgreSQL transaction-start now() precedes an awaited lock's release.
-- No enablement, canonical rows, order/payment logic or prior receipts change.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
do $wallclock_guard$
declare signature text:='public.materialize_native_full_checkout(text,jsonb,text)';
 installed text; definition text; anchor text; replacement text;
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_catalog.pg_proc where oid=pg_catalog.to_regprocedure(signature);
 -- Reviewed BLS-only lifecycle chain and its optional scoped Heartsaver extension.
 if installed is null or md5(installed) not in ('bc2a1da16cf3ff1d2ea1c08d8cb46044','28fdaf269d02bf14a5c3e8a82de64cd8') then
  raise exception 'native_full_offer_wallclock_source_drift';
 end if;
 anchor:=$anchor$ return option||jsonb_build_object('targetSessionId',target,'externalId',locked_external_id);$anchor$;
 replacement:=$replacement$ -- All class, policy, inventory and canonical-workspace lock waits above
 -- have completed. Never renew generatedAt, proofObservedAt or validUntil.
 -- An exception rolls back target creation/reopening and lifecycle witnesses.
 declare checked_at timestamptz:=clock_timestamp();
 begin
  if nullif(p_offer->>'validUntil','')::timestamptz is null
   or (p_offer->>'validUntil')::timestamptz<=checked_at
   or nullif(p_offer->>'generatedAt','')::timestamptz is null
   or (p_offer->>'generatedAt')::timestamptz<checked_at-interval '30 minutes' then
   raise exception 'session_not_available';
  end if;
  if p_offer->>'authority'='native-full-course.v2' and (
   nullif(p_offer->>'proofObservedAt','')::timestamptz is null
   or (p_offer->>'proofObservedAt')::timestamptz<checked_at-interval '15 minutes'
   or (p_offer->>'generatedAt')::timestamptz<checked_at-interval '15 minutes'
   or (p_offer->>'startsAt')::timestamptz<checked_at+interval '24 hours') then
   raise exception 'session_not_available';
  end if;
 end;
 return option||jsonb_build_object('targetSessionId',target,'externalId',locked_external_id);$replacement$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then
  raise exception 'native_full_offer_wallclock_anchor_missing';
 end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 execute replace(definition,anchor,replacement);
end $wallclock_guard$;
revoke all on function public.materialize_native_full_checkout(text,jsonb,text) from public,anon,authenticated;
grant execute on function public.materialize_native_full_checkout(text,jsonb,text) to service_role;
commit;
