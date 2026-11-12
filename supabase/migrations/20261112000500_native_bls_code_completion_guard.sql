-- Optional bundle-only completion boundary after233504 and235100. No enablement.
-- Sender cadence must still be fresh after the last workspace/unique wait.
-- Existing nonce recovery bypasses new materialization;55/four contexts unchanged.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
-- Row SHARE locking needs UPDATE on a column, not broad catalog/config writes.
grant update(id) on public.products to service_role;
-- Row-scoped locking is valid only for these structural identities. Verify
-- real installed constraints, not just fixture assumptions, before replacement.
DO $canonical_lock_keys$ begin
 if not exists(select 1 from pg_index i join pg_attribute a on a.attrelid=i.indrelid and a.attname='product_key'
  where i.indrelid='public.products'::regclass and i.indisunique and i.indisvalid
   and i.indpred is null and i.indexprs is null and i.indnkeyatts=1 and i.indkey[0]=a.attnum)
 then raise exception 'native_code_product_identity_not_unique';end if;
 if not exists(select 1 from pg_index i join pg_attribute a on a.attrelid=i.indrelid and a.attname='id' and a.atttypid='boolean'::regtype
  where i.indrelid='public.landerware_checkout_delivery_config'::regclass and i.indisprimary and i.indisvalid and i.indnkeyatts=1 and i.indkey[0]=a.attnum)
 or not exists(select 1 from pg_constraint c where c.conrelid='public.landerware_checkout_delivery_config'::regclass and c.contype='c' and c.convalidated
  and regexp_replace(pg_get_expr(c.conbin,c.conrelid),'[[:space:]()]','','g')='id')
 then raise exception 'native_code_delivery_config_not_singleton';end if;
end $canonical_lock_keys$;
DO $bundle_lock_scope$
declare signature text:='public.native_bls_skills_lock_dependencies(boolean)';installed text;definition text;anchor text;replacement text;
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if installed is null or md5(installed)<>'f8fa3457a887ce861cdda198fce2496d' then raise exception 'native_code_bundle_dependency_drift';end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:=$anchor$  lock table public.landerware_bls_bundle_policy,public.products,public.landerware_checkout_delivery_config in share mode nowait;$anchor$;
 replacement:=$replacement$  lock table public.landerware_bls_bundle_policy in share mode nowait;
  -- Canonical product key is unique and delivery config is a singleton.
  -- These row locks protect update/delete without granting config/token writes.
  perform 1 from public.products where product_key='aha-25-3553-heartcode-bls-online' for share nowait;
  perform 1 from public.landerware_checkout_delivery_config where id for share nowait;$replacement$;
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_code_bundle_dependency_drift';end if;
 execute replace(definition,anchor,replacement);
end $bundle_lock_scope$;
DO $bundle_completion$
declare signature text:='public.materialize_native_skills_checkout(text,jsonb,text)';installed text;definition text;anchor text;replacement text;
begin
 if to_regprocedure('public.native_bls_bundle_ready(timestamptz)') is null
 or to_regprocedure('public.native_learner_code_runtime_readiness()') is null then raise exception 'native_code_bundle_prerequisite_missing';end if;
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if installed is null or md5(installed)<>'6eb72cb16c8ec5c509bba121b48f6d19' then raise exception 'native_code_bundle_materializer_drift';end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:=$anchor$ return option||jsonb_build_object('targetSessionId',target,'externalId',locked_external_id);$anchor$;
 replacement:=$replacement$ -- Sender readiness is revalidated at materializer completion, after all
 -- awaited workspace and unique insert locks. This is not a commit-time claim.
 if p_context='bls-skills' and p_offer->>'checkoutPackage'='heartcode-bls-online-and-skills.v1'
  and not public.native_bls_bundle_ready((p_offer->>'consumptionEndsAt')::timestamptz) then
  raise exception 'session_not_available';
 end if;
 return option||jsonb_build_object('targetSessionId',target,'externalId',locked_external_id);$replacement$;
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_code_bundle_materializer_drift';end if;
 execute replace(definition,anchor,replacement);
end $bundle_completion$;
commit;
