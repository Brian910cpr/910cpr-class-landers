-- No adoption/backfill: only new inserts by the patched native materializers
-- acquire this lifecycle witness. Class/session identity is never replaced.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
create table if not exists public.native_checkout_generated_sessions (
 class_session_id uuid primary key references public.class_sessions(id),
 identity_hash text not null,
 state text not null default 'holding' check(state in ('holding','released')),
 created_at timestamptz not null default now(), released_at timestamptz,
 release_reason text check(release_reason is null or release_reason='expired_unpaid_hold')
);
alter table public.native_checkout_generated_sessions enable row level security;
revoke all on public.native_checkout_generated_sessions from public,anon,authenticated;
grant select,insert,update on public.native_checkout_generated_sessions to service_role;

create or replace function public.native_checkout_generated_identity(p_session public.class_sessions) returns text
language sql immutable security invoker set search_path='' as $$
 select md5((to_jsonb(p_session)-array['status','registration_status','updated_at'])::text)
$$;

create or replace function public.native_checkout_witness_generated(p_session_id uuid) returns void
language plpgsql security invoker set search_path='' as $$
declare s public.class_sessions;
begin
 select * into strict s from public.class_sessions where id=p_session_id;
 if s.source<>'landerware_event' or s.registration_backend<>'landerware' or s.record_scope<>'operational'
  or s.status<>'scheduled' or s.registration_status<>'open'
  or coalesce(s.external_session_evidence->>'materializedBy','') not in ('skills_session_native','native_full_course')
 then raise exception 'generated_session_witness_rejected'; end if;
 insert into public.native_checkout_generated_sessions(class_session_id,identity_hash)
 values(s.id,public.native_checkout_generated_identity(s));
end $$;

-- Unknown/legacy/paid evidence, any registration history, or staff changes keep
-- the interval occupied. This only releases abandoned *unpaid* checkout holds.
create or replace function public.native_checkout_generated_is_empty(p_session_id uuid) returns boolean
language sql stable security invoker set search_path='' as $$
 select exists(select 1 from public.landerware_public_orders o where o.class_session_id=p_session_id)
 and not exists(select 1 from public.registrations r where r.class_session_id=p_session_id)
 and not exists(select 1 from public.landerware_public_orders o where o.class_session_id=p_session_id and (
  o.checkout_runtime_version<>'native-v1' or o.status not in ('held','checkout_open','expired','cancelled')
  or o.hold_expires_at is null or o.hold_expires_at>now()
  or o.payment_evidence is distinct from '{}'::jsonb or o.stripe_payment_intent_id is not null
  or o.reconciliation_error is not null))
 and not exists(select 1 from public.product_inventory_units u
  join public.landerware_public_order_students st on st.id=u.public_order_student_id
  join public.landerware_public_orders o on o.id=st.order_id where o.class_session_id=p_session_id
  and (u.public_order_payment_observed or u.reserved_for_registration_id is not null or u.exposed_at is not null or u.fulfilled_at is not null))
$$;

create or replace function public.native_checkout_generated_reusable(p_session_id uuid) returns boolean
language sql stable security invoker set search_path='' as $$
 select exists(select 1 from public.native_checkout_generated_sessions w
 join public.class_sessions s on s.id=w.class_session_id
 where s.id=p_session_id and w.state='released' and w.release_reason='expired_unpaid_hold'
  and w.identity_hash=public.native_checkout_generated_identity(s)
  and s.status='cancelled' and s.registration_status='closed' and s.start_at>now()
  and public.native_checkout_generated_is_empty(s.id))
$$;

-- Called only with a server-selected offer interval after publication/profile
-- validation. Bounded on-demand maintenance, no cron, deletes, or source repair.
create or replace function public.native_checkout_release_abandoned(p_starts_at timestamptz,p_ends_at timestamptz) returns integer
language plpgsql security invoker set search_path='' as $$
declare s public.class_sessions; n integer:=0;
begin
 if p_starts_at is null or p_ends_at is null or p_starts_at<=now() or p_ends_at<=p_starts_at
  or p_ends_at>p_starts_at+interval '1 day' then raise exception 'invalid_request'; end if;
 -- Same canonical serialization as materialization; payment/finalization take
 -- the class row before orders, so paid evidence and cleanup cannot cross.
 lock table public.class_sessions in share row exclusive mode;
 for s in select cls.* from public.class_sessions cls join public.native_checkout_generated_sessions w on w.class_session_id=cls.id
  where w.state='holding' and cls.status='scheduled' and cls.registration_status='open' and cls.start_at>now()
   and coalesce(cls.consumption_start_at,cls.start_at)<p_ends_at and coalesce(cls.consumption_end_at,cls.end_at)>p_starts_at
   and w.identity_hash=public.native_checkout_generated_identity(cls)
  order by cls.id limit 32 for update of cls
 loop
  perform 1 from public.landerware_public_orders where class_session_id=s.id order by id for update;
  if not public.native_checkout_generated_is_empty(s.id) then continue; end if;
  update public.landerware_public_orders set status='expired',updated_at=now()
   where class_session_id=s.id and status in ('held','checkout_open');
  update public.class_sessions set status='cancelled',registration_status='closed',updated_at=now() where id=s.id;
  update public.native_checkout_generated_sessions set state='released',released_at=now(),release_reason='expired_unpaid_hold' where class_session_id=s.id;
  n:=n+1;
 end loop;
 return n;
end $$;

create or replace function public.native_checkout_reopen_generated(p_session_id uuid) returns void
language plpgsql security invoker set search_path='' as $$
begin
 perform 1 from public.class_sessions where id=p_session_id for update;
 if not public.native_checkout_generated_reusable(p_session_id) then raise exception 'session_not_available'; end if;
 update public.class_sessions set status='scheduled',registration_status='open',updated_at=now() where id=p_session_id;
 update public.native_checkout_generated_sessions set state='holding',released_at=null,release_reason=null where class_session_id=p_session_id;
 -- The materializer must re-run the complete option validator before returning.
end $$;

do $patch$ declare signature text; definition text; old_text text; new_text text;
begin
 foreach signature in array array['public.materialize_native_skills_checkout(text,jsonb,text)','public.materialize_native_full_checkout(text,jsonb,text)'] loop
  if to_regprocedure(signature) is null then continue; end if;
  definition:=pg_get_functiondef(signature::regprocedure);
  if position('native_checkout_witness_generated' in definition)>0 then continue; end if;
  old_text:='returning id into target;';
  new_text:=old_text||E'\n  perform public.native_checkout_witness_generated(target);';
  if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'unsupported_materializer_witness'; end if;
  definition:=replace(definition,old_text,new_text);
  old_text:='perform 1 from public.class_sessions where id=target for update;';
  new_text:=old_text||E'\n  if public.native_checkout_generated_reusable(target) then perform public.native_checkout_reopen_generated(target); end if;';
  if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'unsupported_materializer_reopen'; end if;
  execute replace(definition,old_text,new_text);
 end loop;
 foreach signature in array array['public.skills_session_native_option(text,jsonb)','public.native_full_course_option(text,jsonb)'] loop
  if to_regprocedure(signature) is null then continue; end if;
  definition:=pg_get_functiondef(signature::regprocedure);
  if position('native_checkout_generated_reusable' in definition)>0 then continue; end if;
  if signature like '%skills_session_native_option%' then
   old_text:=E'target.status not in (''scheduled'',''active'') or target.registration_status is distinct from ''open''';
  else
   old_text:=E'target.status not in (''scheduled'',''active'') or target.registration_status not in (''open'',''external'')';
  end if;
  new_text:='(('||old_text||') and not public.native_checkout_generated_reusable(target.id))';
  if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'unsupported_option_reopen'; end if;
  execute replace(definition,old_text,new_text);
 end loop;
end $patch$;

revoke all on function public.native_checkout_generated_identity(public.class_sessions),public.native_checkout_witness_generated(uuid),public.native_checkout_generated_is_empty(uuid),public.native_checkout_generated_reusable(uuid),public.native_checkout_release_abandoned(timestamptz,timestamptz),public.native_checkout_reopen_generated(uuid) from public,anon,authenticated;
grant execute on function public.native_checkout_generated_identity(public.class_sessions),public.native_checkout_witness_generated(uuid),public.native_checkout_generated_is_empty(uuid),public.native_checkout_generated_reusable(uuid),public.native_checkout_release_abandoned(timestamptz,timestamptz),public.native_checkout_reopen_generated(uuid) to service_role;
commit;
