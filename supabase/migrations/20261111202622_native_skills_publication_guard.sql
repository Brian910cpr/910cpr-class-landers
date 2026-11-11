-- Additive, default-off first-party skills publication. No course/profile activation.
-- Existing skills-session-policy.v1 owns qualification, contexts, 45+15 and capacity 2.
begin;
set local lock_timeout='2s';
create table public.native_skills_publication_policy (
 scope_id text primary key check(scope_id='brian-shipyard-b.v1'),
 enabled boolean not null default false,
 publication_enabled boolean not null default false,
 verified boolean not null default false,
 evidence text,
 updated_at timestamptz not null default now()
);
insert into public.native_skills_publication_policy(scope_id) values('brian-shipyard-b.v1');
alter table public.native_skills_publication_policy enable row level security;
revoke all on public.native_skills_publication_policy from public,anon,authenticated;
grant select,insert,update,delete on public.native_skills_publication_policy to service_role;
create policy native_skills_publication_service_access on public.native_skills_publication_policy
 for all to service_role using(true) with check(true);

create or replace function public.native_skills_publication_runtime_policy()
returns jsonb language sql stable security invoker set search_path='' as $$
 select jsonb_build_object('nativePublicationEnabled',exists(
  select 1 from public.native_skills_publication_policy where scope_id='brian-shipyard-b.v1'
   and enabled and publication_enabled and verified and nullif(trim(evidence),'') is not null),
  'nativeScopeId','brian-shipyard-b.v1');
$$;

create or replace function public.native_skills_publication_offer_valid(p_context text,p_offer jsonb)
returns boolean language plpgsql stable security invoker set search_path='' as $$
declare observed timestamptz; generated timestamptz; lease timestamptz; starts timestamptz; occupied_end timestamptz;
begin
 -- Leave existing legacy/HeartCode bundle contracts unchanged. Native markers
 -- cannot fall through by removing/changing just the authority discriminator.
 if coalesce(p_offer->>'authority','')='' and not(p_offer ?| array['nativeOfferId','nativeScopeId','proofObservedAt'])
  and coalesce(p_offer->>'selectionId','') not like 'skills:native-skills:%' then return true; end if;
 if p_offer->>'authority' is distinct from 'native-skills-publication.v1'
  or p_offer->>'nativeScopeId' is distinct from 'brian-shipyard-b.v1'
  or p_offer->>'qualificationPolicy' is distinct from 'skills-session-policy.v1'
  or p_offer->>'courseNumber' is distinct from '509474'
  or p_offer->>'capacity' is distinct from '2'
  or p_context not in ('cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended')
  or p_offer->>'context' is distinct from p_context
  or p_offer->>'instructor' is distinct from 'Brian Ennis'
  or p_offer->>'offerType' is distinct from 'dynamic_appointment'
  or coalesce(p_offer->>'nativeOfferId','') !~ '^native-skills:[a-f0-9]{64}$'
  or p_offer->>'selectionId' is distinct from 'skills:'||(p_offer->>'nativeOfferId')||':'||p_context
  or p_offer ? 'appointmentDayId' or p_offer ? 'matchedContainerId'
  then return false; end if;
 if not (public.native_skills_publication_runtime_policy()->>'nativePublicationEnabled')::boolean then return false; end if;
 if exists(select 1 from unnest(array['proofObservedAt','generatedAt','validUntil','startsAt','consumptionEndsAt']) field
  where coalesce(p_offer->>field,'') !~ 'T.*(Z|[+-][0-9]{2}:[0-9]{2})$') then return false; end if;
 observed:=(p_offer->>'proofObservedAt')::timestamptz;
 generated:=(p_offer->>'generatedAt')::timestamptz;
 lease:=(p_offer->>'validUntil')::timestamptz;
 starts:=(p_offer->>'startsAt')::timestamptz;
 occupied_end:=(p_offer->>'consumptionEndsAt')::timestamptz;
 if observed>generated or observed>now() or observed<now()-interval '15 minutes'
  or generated>now() or generated<now()-interval '15 minutes'
  or lease<=now() or lease>observed+interval '15 minutes' or lease>generated+interval '15 minutes'
  or starts<now()+interval '24 hours' or starts>now()+interval '90 days'
  or extract(minute from starts at time zone 'America/New_York')::integer%15<>0
  or extract(second from starts)<>0
  or occupied_end<>starts+interval '60 minutes' then return false; end if;
 -- Reuse exactly the pre-existing canonical policy, not a broad instructor-family
 -- exception. Its current active qualification and any revocation still apply.
 if not exists(select 1 from public.skills_session_context_config cfg
  join public.courses c on c.id=cfg.course_id
  join public.people p on p.person_key='brian' and p.display_name='Brian Ennis' and p.active
  join public.instructor_qualifications q on q.instructor_id=p.id and q.course_id=cfg.qualification_course_id
  where cfg.context_key=p_context and cfg.enabled and cfg.capacity_policy_verified
   and cfg.policy_evidence='skills-session-policy.v1' and cfg.qualification_course_id=cfg.course_id
   and c.enrollware_course_id='509474' and q.qualification_key='skills-session-policy.v1'
   and q.status='active' and (q.expires_at is null or q.expires_at>=occupied_end)) then return false; end if;
 return true;
exception when invalid_datetime_format or datetime_field_overflow then return false;
end $$;
revoke all on function public.native_skills_publication_runtime_policy(),public.native_skills_publication_offer_valid(text,jsonb) from public,anon,authenticated;
grant execute on function public.native_skills_publication_runtime_policy(),public.native_skills_publication_offer_valid(text,jsonb) to service_role;

-- Preserve every installed capacity, closure, protected-payment and generated-
-- session lifecycle guard. Only the four known source variants are accepted.
do $patch$ declare definition text; installed text; old_text text:=E'begin\n select * into cfg from public.skills_session_context_config';
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_catalog.pg_proc
  where oid=pg_catalog.to_regprocedure('public.skills_session_native_option(text,jsonb)');
 if md5(installed) is null or md5(installed) not in ('697778a82f63f8fad1c32832031c28f6','79081046a318f3bdcec138b467584a4c','88c0c376fc9e1281f7c860da06272fa7','e0bb140f88b5c77b832425dcab71c81a') then
  raise exception 'skills_session_native_option_source_drift';
 end if;
 definition:=replace(pg_get_functiondef('public.skills_session_native_option(text,jsonb)'::regprocedure),E'\r\n',E'\n');
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'skills_publication_guard_anchor_missing'; end if;
 execute replace(definition,old_text,E'begin\n if not public.native_skills_publication_offer_valid(p_context,p_offer) then return null; end if;\n select * into cfg from public.skills_session_context_config');
end $patch$;
commit;
