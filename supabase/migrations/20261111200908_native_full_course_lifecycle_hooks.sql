-- Restore full-course lifecycle integration after the later full-course/v2
-- replacements. No activation, adoption, backfill, or existing-row changes.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
do $patch$
declare signature text; definition text; body text; base_body text;
 witness text:=E'\n  perform public.native_checkout_witness_generated(target);';
 reopen text:=E'\n  if public.native_checkout_generated_reusable(target) then perform public.native_checkout_reopen_generated(target); end if;';
 old_status text:='target.status not in (''scheduled'',''active'') or target.registration_status not in (''open'',''external'')';
 new_status text;
begin
 if to_regclass('public.native_checkout_generated_sessions') is null
  or to_regprocedure('public.native_checkout_witness_generated(uuid)') is null
  or to_regprocedure('public.native_checkout_reopen_generated(uuid)') is null then
  raise exception 'native_full_lifecycle_dependency_missing';
 end if;
 signature:='public.materialize_native_full_checkout(text,jsonb,text)';
 select replace(prosrc,E'\r\n',E'\n') into body from pg_proc where oid=to_regprocedure(signature);
 if (length(body)-length(replace(body,witness,'')))/length(witness)>1
  or (length(body)-length(replace(body,reopen,'')))/length(reopen)>1 then
  raise exception 'native_full_materializer_duplicate_hook';
 end if;
 base_body:=replace(replace(body,witness,''),reopen,'');
 if md5(base_body) is distinct from '965765506695404b6d808d6b6ae395c1' then
  raise exception 'native_full_materializer_source_drift';
 end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 if position(witness in body)=0 then
  definition:=replace(definition,'returning id into target;','returning id into target;'||witness);
 end if;
 if position(reopen in body)=0 then
  definition:=replace(definition,'perform 1 from public.class_sessions where id=target for update;',
   'perform 1 from public.class_sessions where id=target for update;'||reopen);
 end if;
 execute definition;
 signature:='public.native_full_course_option(text,jsonb)';
 select replace(prosrc,E'\r\n',E'\n') into body from pg_proc where oid=to_regprocedure(signature);
 new_status:='(('||old_status||') and not public.native_checkout_generated_reusable(target.id))';
 if (length(body)-length(replace(body,new_status,'')))/length(new_status)>1 then
  raise exception 'native_full_option_duplicate_hook';
 end if;
 base_body:=replace(body,new_status,old_status);
 if md5(base_body) is distinct from 'db8e92ef1c1806607f1bef939372ba15' then
  raise exception 'native_full_option_source_drift';
 end if;
 if position(new_status in body)=0 then
  execute replace(pg_get_functiondef(signature::regprocedure),old_status,new_status);
 end if;
end $patch$;
-- Preserve invoker/authentication boundaries explicitly.
revoke all on function public.native_full_course_option(text,jsonb),
 public.materialize_native_full_checkout(text,jsonb,text) from public,anon,authenticated;
grant execute on function public.native_full_course_option(text,jsonb),
 public.materialize_native_full_checkout(text,jsonb,text) to service_role;
commit;
