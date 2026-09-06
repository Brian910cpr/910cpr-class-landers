begin;

create table if not exists public.landerware_group_requests(
 id uuid primary key default gen_random_uuid(), idempotency_key text not null unique,
 organization_id uuid not null references public.landerware_organizations(id), coordinator_person_id uuid not null references public.landerware_people(id), requested_session_id uuid references public.landerware_sessions(id),
 organization_type text not null, recommended_program text not null, selected_program text not null, selected_course_key text not null,
 selected_modules jsonb not null default '[]', request_details jsonb not null default '{}', availability_evidence jsonb,
 reservation_mode text not null default 'requires_confirmation' check(reservation_mode='requires_confirmation'),
 status text not null default 'requested' check(status in('requested','reviewing','confirmed','declined','cancelled')),
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
alter table public.landerware_group_requests enable row level security;
revoke all on public.landerware_group_requests from anon,authenticated;
create index if not exists landerware_group_requests_status_idx on public.landerware_group_requests(status,created_at desc);

create table if not exists public.landerware_group_request_rate_limits(
 client_hash text not null, window_started_at timestamptz not null, request_count integer not null check(request_count>0), primary key(client_hash,window_started_at)
);
alter table public.landerware_group_request_rate_limits enable row level security;
revoke all on public.landerware_group_request_rate_limits from anon,authenticated;

create or replace function public.landerware_create_group_request(p_idempotency_key text,p_client_hash text,p_payload jsonb,p_evidence jsonb default null)
returns jsonb language plpgsql security definer set search_path='' as $$
declare
 v_existing public.landerware_group_requests;v_org public.landerware_organizations;v_person_result jsonb;v_person_id uuid;v_session_id uuid;v_request_id uuid;
 v_industry text:=p_payload->>'organizationType';v_recommended text:=p_payload->>'recommendedProgram';v_program text:=p_payload->>'selectedProgram';v_course text:=p_payload->>'selectedCourseKey';v_cohort text:=p_payload->>'cohort';v_delivery text:=p_payload->>'delivery';v_market text:=p_payload->>'market';v_modules jsonb:=coalesce(p_payload->'modules','[]');v_module text;v_first text;v_last text;v_name_parts text[];v_start timestamptz;v_window timestamptz:=date_trunc('hour',now());v_rate integer;
begin
 if p_idempotency_key!~'^[A-Za-z0-9-]{16,100}$' then raise exception using errcode='22023',message='invalid_idempotency_key';end if;
 perform pg_advisory_xact_lock(hashtextextended('group-request|'||p_idempotency_key,0));
 select * into v_existing from public.landerware_group_requests where idempotency_key=p_idempotency_key;
 if v_existing.id is not null then return jsonb_build_object('requestId',v_existing.id,'sessionId',v_existing.requested_session_id,'status',v_existing.status,'reservationMode',v_existing.reservation_mode,'idempotentReplay',true);end if;
 if v_industry<>all(array['healthcare','childcare','hospitality','community','workplace','fitness','public_safety','exact']) or v_recommended<>all(array['certified','workplace','children','healthcare','complete']) or v_program<>all(array['certified','workplace','children','healthcare','complete']) or v_course<>all(array['bls','first_aid','pediatric','cpr_aed','acls','pals','hsi']) or v_cohort<>all(array['initial','renewal','mixed']) or v_delivery<>all(array['in_person','blended','either']) or v_market<>all(array['other','wilmington_nc','jacksonville_nc','lumberton_nc','whiteville_nc','myrtle_beach_sc']) then raise exception using errcode='22023',message='invalid_selection';end if;
 if jsonb_typeof(v_modules)<>'array' or jsonb_array_length(v_modules)>4 then raise exception using errcode='22023',message='invalid_modules';end if;
 for v_module in select jsonb_array_elements_text(v_modules) loop if v_module<>all(array['Bloodborne Pathogens','Bleeding Control','Choking-focused practice','Organization-specific scenarios']) then raise exception using errcode='22023',message='invalid_modules';end if;end loop;
 if (v_program='workplace' and v_course<>all(array['first_aid','cpr_aed','hsi'])) or (v_program='children' and v_course<>all(array['pediatric','first_aid'])) or (v_program='healthcare' and v_course<>all(array['bls','acls','pals','first_aid'])) then raise exception using errcode='22023',message='unsupported_program_course';end if;
 insert into public.landerware_group_request_rate_limits(client_hash,window_started_at,request_count) values(p_client_hash,v_window,1) on conflict(client_hash,window_started_at) do update set request_count=public.landerware_group_request_rate_limits.request_count+1 returning request_count into v_rate;
 if v_rate>5 then raise exception using errcode='P0001',message='rate_limited';end if;
 perform pg_advisory_xact_lock(hashtextextended('group-org|'||lower(trim(p_payload->>'organization')),0));
 select * into v_org from public.landerware_organizations where archived_at is null and lower(trim(display_name))=lower(trim(p_payload->>'organization')) order by created_at limit 1;
 if v_org.id is null then insert into public.landerware_organizations(display_name,organization_type) values(trim(p_payload->>'organization'),v_industry) returning * into v_org;end if;
 v_name_parts:=regexp_split_to_array(trim(p_payload->>'coordinator'),'\s+');v_first:=v_name_parts[1];v_last:=case when array_length(v_name_parts,1)>1 then array_to_string(v_name_parts[2:array_length(v_name_parts,1)],' ') else 'Coordinator' end;
 v_person_result:=public.landerware_create_or_find_person(v_first,v_last,lower(trim(p_payload->>'email')),trim(p_payload->>'phone'),null,'group_request',p_idempotency_key);v_person_id:=nullif(v_person_result->>'personId','')::uuid;
 if v_person_id is null then raise exception using errcode='P0001',message='person_creation_failed';end if;
 if not exists(select 1 from public.landerware_person_organizations where person_id=v_person_id and organization_id=v_org.id and active=true) then insert into public.landerware_person_organizations(person_id,organization_id) values(v_person_id,v_org.id);end if;
 if p_evidence is not null then
  if p_evidence->>'selectedCourseKey'<>v_course or upper(p_evidence->>'courseFamily')<>case v_course when 'bls' then 'BLS' when 'acls' then 'ACLS' when 'pals' then 'PALS' when 'hsi' then 'HSI' else 'HEARTSAVER' end or p_evidence->>'pageKey'<>case v_course when 'bls' then 'bls' when 'acls' then 'acls' when 'pals' then 'pals' when 'hsi' then 'hsi' else 'heartsaver' end then raise exception using errcode='22023',message='course_evidence_mismatch';end if;
  v_start:=to_timestamp((p_evidence->>'date')||' '||(p_evidence->>'startTime'),'YYYY-MM-DD HH12:MI AM')::timestamp at time zone 'America/New_York';
  insert into public.landerware_sessions(course_id,course_name,starts_at,location_name,organization_id,lifecycle_state,provenance,requirements_manifest) values(p_evidence->>'courseId',p_evidence->>'courseName',v_start,trim(p_payload->>'address'),v_org.id,'requested_confirmation','public_group_training',jsonb_build_object('headcount',(p_payload->>'headcount')::integer,'delivery',v_delivery,'modules',v_modules,'availability',p_evidence)) returning id into v_session_id;
 end if;
 insert into public.landerware_group_requests(idempotency_key,organization_id,coordinator_person_id,requested_session_id,organization_type,recommended_program,selected_program,selected_course_key,selected_modules,request_details,availability_evidence) values(p_idempotency_key,v_org.id,v_person_id,v_session_id,v_industry,v_recommended,v_program,v_course,v_modules,p_payload-'email'-'phone'-'coordinator',p_evidence) returning id into v_request_id;
 insert into public.landerware_activity_events(event_type,actor_source,actor_display,person_id,organization_id,session_id,details) values('group_request_created','system','Public group-training request',v_person_id,v_org.id,v_session_id,jsonb_build_object('request_id',v_request_id,'reservation_mode','requires_confirmation'));
 return jsonb_build_object('requestId',v_request_id,'sessionId',v_session_id,'status','requested','reservationMode','requires_confirmation','idempotentReplay',false);
end $$;
revoke execute on function public.landerware_create_group_request(text,text,jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.landerware_create_group_request(text,text,jsonb,jsonb) to service_role;
commit;
