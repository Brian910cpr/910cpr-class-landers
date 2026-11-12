-- Bounded native lifecycle maintenance; no historical adoption or deletion.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
create table public.native_publication_maintenance_policy (
 singleton boolean primary key default true check(singleton), enabled boolean not null default false
);
insert into public.native_publication_maintenance_policy(singleton,enabled) values(true,false);
alter table public.native_publication_maintenance_policy enable row level security;
revoke all on public.native_publication_maintenance_policy from public,anon,authenticated;
grant select,update on public.native_publication_maintenance_policy to service_role;
create function public.native_publication_release_expired() returns jsonb
language plpgsql security invoker set search_path='' as $$
declare s public.class_sessions; released integer:=0; examined integer:=0;
begin
 if not coalesce((select enabled from public.native_publication_maintenance_policy where singleton),false) then
   raise exception 'native_publication_maintenance_disabled';
 end if;
 -- Use the same class-table/row/order serialization as materialization and
 -- the existing release helper. Its paid/unknown/staff-edit guards are final.
 lock table public.class_sessions in share row exclusive mode;
 for s in select cls.* from public.class_sessions cls
   join public.native_checkout_generated_sessions w on w.class_session_id=cls.id
   where w.state='holding' and cls.status='scheduled' and cls.registration_status='open'
     and cls.source='landerware_event' and cls.registration_backend='landerware' and cls.record_scope='operational'
     and cls.start_at>now() and cls.start_at<now()+interval '90 days'
     and coalesce(cls.consumption_start_at,cls.start_at)>now()
     and coalesce(cls.consumption_end_at,cls.end_at)>coalesce(cls.consumption_start_at,cls.start_at)
     and coalesce(cls.consumption_end_at,cls.end_at)<=coalesce(cls.consumption_start_at,cls.start_at)+interval '1 day'
     and w.identity_hash=public.native_checkout_generated_identity(cls)
     and public.native_checkout_generated_is_empty(cls.id)
   order by cls.start_at,cls.id limit 32 for update of cls
 loop
   examined:=examined+1;
   perform 1 from public.landerware_public_orders where class_session_id=s.id order by id for update;
   if not public.native_checkout_generated_is_empty(s.id) then continue; end if;
   -- Same guarded transition as release_abandoned, targeted to this locked row
   -- rather than its interval so no batch can change more than 32 sessions.
   update public.landerware_public_orders set status='expired',updated_at=now()
     where class_session_id=s.id and status in ('held','checkout_open');
   update public.class_sessions set status='cancelled',registration_status='closed',updated_at=now() where id=s.id;
   update public.native_checkout_generated_sessions set state='released',released_at=now(),release_reason='expired_unpaid_hold' where class_session_id=s.id;
   released:=released+1;
 end loop;
 return jsonb_build_object('schemaVersion','native-publication-maintenance.v1',
   'examined',examined,'released',released,'batchLimit',32,'observedAt',now());
end $$;

-- A missing active row is never evidence that its retained occupancy disappeared.
-- Only exact unchanged released witnesses may retire a public projection row.
create index native_publication_release_identity_lookup on public.class_sessions(external_class_id)
 where source='landerware_event' and registration_backend='landerware' and record_scope='operational';
-- Query only retained public IDs, never the cumulative release history. Each
-- complete request is bounded; absent proof keeps its retained row occupied.
create function public.native_released_scheduling_sessions(p_external_class_ids text[]) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare result jsonb;
begin
 if p_external_class_ids is null or coalesce(array_ndims(p_external_class_ids),0)<>1
   or cardinality(p_external_class_ids) not between 1 and 64
   or exists(select 1 from unnest(p_external_class_ids) id where id is null
      or id !~ '^lw-[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$')
   or (select count(distinct id) from unnest(p_external_class_ids) id)<>cardinality(p_external_class_ids)
 then raise exception 'invalid_request'; end if;
 select coalesce(jsonb_agg(entry),'[]'::jsonb) into result from (
 select jsonb_build_object(
   'authority','native-generated-release.v1','canonical_session_id',s.id,
   'external_class_id',s.external_class_id,'start_at',s.start_at,'end_at',s.end_at,
   'consumption_start_at',s.consumption_start_at,'consumption_end_at',s.consumption_end_at,
   'released_at',w.released_at,'release_reason',w.release_reason) as entry
 from public.class_sessions s
 join public.native_checkout_generated_sessions w on w.class_session_id=s.id
 where s.external_class_id=any(p_external_class_ids)
   and s.source='landerware_event' and s.registration_backend='landerware' and s.record_scope='operational'
   and w.released_at is not null and w.released_at<=now()
   and public.native_checkout_generated_reusable(s.id)
 order by s.external_class_id,s.id) exact_requested;
 -- Defensive against corrupt/ambiguous external identities, without a LIMIT
 -- that could conceal a release witness or silently truncate a request.
 if jsonb_array_length(result)>cardinality(p_external_class_ids)
   or (select count(distinct row->>'external_class_id') from jsonb_array_elements(result) row)<>jsonb_array_length(result)
 then raise exception 'native_release_projection_conflict'; end if;
 return jsonb_build_object('schema_version','910cpr-native-release-proof.v1',
   'generated_at',now(),'complete',true,'requested_external_class_ids',to_jsonb(p_external_class_ids),
   'released_native_sessions',result);
end $$;
revoke all on function public.native_publication_release_expired(),public.native_released_scheduling_sessions(text[]) from public,anon,authenticated;
grant execute on function public.native_publication_release_expired(),public.native_released_scheduling_sessions(text[]) to service_role;
commit;
