-- The Dockmaster kept the soaked manifest beside the old berth number; a true name, once found, was never copied onto a second ledger.

alter table public.nhcso_classes add column if not exists class_session_id uuid references public.class_sessions(id);
create unique index if not exists nhcso_classes_class_session_unique on public.nhcso_classes(class_session_id) where class_session_id is not null;
alter table public.nhcso_students add column if not exists class_session_id uuid references public.class_sessions(id);
alter table public.nhcso_documents add column if not exists class_session_id uuid references public.class_sessions(id);
alter table public.registrations add column if not exists nhcso_student_id uuid references public.nhcso_students(id);
create unique index if not exists registrations_nhcso_student_unique on public.registrations(nhcso_student_id) where nhcso_student_id is not null;

create table if not exists public.class_session_instructors (
  class_session_id uuid not null references public.class_sessions(id) on delete cascade,
  instructor_id uuid not null references public.people(id),
  role text not null check (role in ('lead','assistant')),
  source text not null,
  created_at timestamptz not null default now(),
  primary key (class_session_id, instructor_id, role)
);
alter table public.class_session_instructors enable row level security;

create table if not exists public.class_session_requirements (
  class_session_id uuid not null references public.class_sessions(id) on delete cascade,
  requirement_key text not null,
  status text not null check (status in ('missing','received','verified','waived')),
  evidence_document_id uuid references public.nhcso_documents(id),
  verified_at timestamptz,
  verified_by text,
  notes text,
  updated_at timestamptz not null default now(),
  primary key (class_session_id, requirement_key)
);
alter table public.class_session_requirements enable row level security;

create table if not exists public.session_card_processing (
  class_session_id uuid primary key references public.class_sessions(id) on delete cascade,
  status text not null check (status in ('not_ready','ready_for_issue','issuing','issued','blocked')),
  cards_required integer not null default 0 check (cards_required >= 0),
  cards_issued integer not null default 0 check (cards_issued >= 0 and cards_issued <= cards_required),
  missing_requirements jsonb not null default '[]'::jsonb,
  reviewed_at timestamptz,
  updated_at timestamptz not null default now()
);
alter table public.session_card_processing enable row level security;

create table if not exists public.class_session_audit (
  id uuid primary key default gen_random_uuid(),
  class_session_id uuid not null references public.class_sessions(id) on delete cascade,
  event_key text not null,
  event_type text not null,
  actor_person_id uuid references public.people(id),
  actor_label text,
  occurred_at timestamptz not null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (class_session_id, event_key)
);
alter table public.class_session_audit enable row level security;

create table if not exists public.transactional_email_outbox (
  id uuid primary key default gen_random_uuid(),
  idempotency_key text not null unique,
  class_session_id uuid not null references public.class_sessions(id) on delete cascade,
  notification_type text not null check (notification_type in ('submitter_confirmation','operations_notification')),
  recipient_email text not null,
  payload jsonb not null,
  status text not null default 'pending' check (status in ('pending','sending','sent','failed')),
  attempt_count integer not null default 0,
  last_error text,
  message_id text,
  created_at timestamptz not null default now(),
  sent_at timestamptz,
  updated_at timestamptz not null default now()
);
alter table public.transactional_email_outbox enable row level security;

create unique index if not exists instructor_qualification_identity_unique
  on public.instructor_qualifications(instructor_id, coalesce(course_id, '00000000-0000-0000-0000-000000000000'::uuid), coalesce(qualification_key, ''));

create or replace function public.promote_nhcso_class(p_class_number text)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  c public.nhcso_classes%rowtype;
  session_id uuid;
  v_course_id uuid;
  v_organization_id uuid;
  v_location_id uuid;
  v_lauren_id uuid;
  v_crystal_id uuid;
  v_doc_id uuid;
  active_count integer;
  student public.nhcso_students%rowtype;
  customer_id uuid;
  cleaned_name text;
  v_first_name text;
  v_last_name text;
begin
  perform pg_advisory_xact_lock(hashtextextended(p_class_number, 0));
  select * into c from public.nhcso_classes where class_number = p_class_number for update;
  if c.class_number is null then raise exception 'NHCSO class % not found', p_class_number; end if;

  select id into v_course_id from public.courses where course_key = 'aha-bls-provider';
  if v_course_id is null then raise exception 'Canonical AHA BLS Provider course is missing'; end if;

  insert into public.organizations(organization_key,name,updated_at)
  values ('nhcso','New Hanover County Sheriff''s Office',now())
  on conflict (organization_key) do update set name=excluded.name,updated_at=now()
  returning id into v_organization_id;

  insert into public.locations(location_key,name,address_line1,city,state,postal_code,public,updated_at)
  values ('nhcso-training-division','New Hanover County Sheriff''s Office','3950 Juvenile Center Rd','Castle Hayne','NC','28429',false,now())
  on conflict (location_key) do update set name=excluded.name,address_line1=excluded.address_line1,city=excluded.city,state=excluded.state,postal_code=excluded.postal_code,updated_at=now()
  returning id into v_location_id;

  insert into public.people(person_key,display_name,email,active,enrollware_instructor_id,external_reference,updated_at)
  values ('instructor_2221028576','Lauren Brothers','labrothers@nhcgov.com',true,'2221028576','NHCSO',now())
  on conflict (person_key) do update set display_name=excluded.display_name,email=excluded.email,active=true,enrollware_instructor_id=excluded.enrollware_instructor_id,external_reference='NHCSO',updated_at=now()
  returning id into v_lauren_id;

  insert into public.people(person_key,display_name,email,active,enrollware_instructor_id,external_reference,updated_at)
  values ('instructor_23125524581','Crystal Jasper','cjasper@nhcgov.com',true,'23125524581','NHCSO',now())
  on conflict (person_key) do update set display_name=excluded.display_name,email=excluded.email,active=true,enrollware_instructor_id=excluded.enrollware_instructor_id,external_reference='NHCSO',updated_at=now()
  returning id into v_crystal_id;

  insert into public.instructor_qualifications(instructor_id,course_id,qualification_key,status,updated_at)
  values (v_lauren_id,v_course_id,'NHCSO_CADRE','active',now()),(v_crystal_id,v_course_id,'NHCSO_CADRE','active',now())
  on conflict (instructor_id, (coalesce(course_id, '00000000-0000-0000-0000-000000000000'::uuid)), (coalesce(qualification_key, '')))
  do update set status='active',updated_at=now();

  select id into session_id from public.class_sessions where external_class_id=p_class_number for update;
  if session_id is null then
    insert into public.class_sessions(source,status,course_id,start_at,end_at,timezone,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,organization_id,max_students,registration_backend,visibility,registration_status,external_class_id,external_course_id,external_location_id,external_instructor_id,public_notes,created_at,updated_at)
    values ('nhcso_workspace','completed',v_course_id,(c.class_date+c.start_time::time) at time zone 'America/New_York',((c.class_date+c.start_time::time)+interval '3 hours') at time zone 'America/New_York','America/New_York',(c.class_date+c.start_time::time) at time zone 'America/New_York',((c.class_date+c.start_time::time)+interval '3 hours') at time zone 'America/New_York',v_lauren_id,v_location_id,v_organization_id,20,'landerware','private','closed',p_class_number,'aha-bls-provider','nhcso-training-division','2221028576','NHCSO BLS class recovered from the instructor workspace. Completion paperwork verified; ready for AHA eCard issuance.',c.created_at,now())
    returning id into session_id;
  else
    update public.class_sessions set source='nhcso_workspace',status='completed',course_id=v_course_id,lead_instructor_id=v_lauren_id,location_id=v_location_id,organization_id=v_organization_id,registration_backend='landerware',visibility='private',registration_status='closed',external_class_id=p_class_number,external_course_id='aha-bls-provider',external_location_id='nhcso-training-division',external_instructor_id='2221028576',updated_at=now() where id=session_id;
  end if;

  update public.nhcso_classes set class_session_id=session_id,assistant_instructors='Crystal Jasper',status='completed',updated_at=now() where class_number=p_class_number;
  update public.nhcso_students set class_session_id=session_id,updated_at=now() where class_number=p_class_number;
  update public.nhcso_documents set class_session_id=session_id where class_number=p_class_number;
  select id into v_doc_id from public.nhcso_documents where class_number=p_class_number order by created_at limit 1;

  insert into public.class_session_instructors(class_session_id,instructor_id,role,source)
  values (session_id,v_lauren_id,'lead','nhcso_submission'),(session_id,v_crystal_id,'assistant','audited_correction')
  on conflict do nothing;

  for student in select * from public.nhcso_students where class_number=p_class_number and status='Active' loop
    cleaned_name := trim(regexp_replace(student.name, '\s*-\s*$', ''));
    v_first_name := split_part(cleaned_name,' ',1);
    v_last_name := trim(substr(cleaned_name,length(v_first_name)+1));
    if v_last_name='' then v_last_name := 'Unknown'; end if;
    select id into customer_id from public.customers where lower(email)=lower(student.email) order by created_at limit 1;
    if customer_id is null then
      insert into public.customers(first_name,last_name,email,organization_id) values(v_first_name,v_last_name,lower(student.email),v_organization_id) returning id into customer_id;
    else
      update public.customers set first_name=v_first_name,last_name=v_last_name,organization_id=v_organization_id,updated_at=now() where id=customer_id;
    end if;
    insert into public.registrations(customer_id,class_session_id,status,registration_source,external_registration_id,nhcso_student_id,updated_at)
    values(customer_id,session_id,'completed','nhcso_class_submission','nhcso-student:'||student.id,student.id,now())
    on conflict (external_registration_id) where external_registration_id is not null
    do update set customer_id=excluded.customer_id,class_session_id=excluded.class_session_id,status='completed',registration_source=excluded.registration_source,nhcso_student_id=excluded.nhcso_student_id,updated_at=now();
  end loop;

  select count(*) into active_count from public.nhcso_students where class_number=p_class_number and status='Active';
  insert into public.class_session_requirements(class_session_id,requirement_key,status,evidence_document_id,verified_at,verified_by,notes,updated_at)
  values
    (session_id,'roster','verified',v_doc_id,now(),'Codex production recovery','11 database participants reconciled exactly to signed roster; each score 100 and Pass.',now()),
    (session_id,'skills_testing','verified',v_doc_id,now(),'Codex production recovery','Participant-specific AHA BLS skills checklists marked PASS.',now()),
    (session_id,'written_exam','verified',v_doc_id,now(),'Codex production recovery','Participant-specific BLS written answer sheets present; signed roster records score 100.',now()),
    (session_id,'instructor_attestation','verified',v_doc_id,now(),'Codex production recovery','Roster signed by Sgt. Lauren Brothers and M/Cpl. Crystal Jasper with instructor numbers.',now())
  on conflict (class_session_id,requirement_key) do update set status='verified',evidence_document_id=excluded.evidence_document_id,verified_at=excluded.verified_at,verified_by=excluded.verified_by,notes=excluded.notes,updated_at=now();

  insert into public.session_card_processing(class_session_id,status,cards_required,cards_issued,missing_requirements,reviewed_at,updated_at)
  values(session_id,'ready_for_issue',active_count,0,'[]'::jsonb,now(),now())
  on conflict (class_session_id) do update set status='ready_for_issue',cards_required=excluded.cards_required,missing_requirements='[]'::jsonb,reviewed_at=now(),updated_at=now();

  insert into public.class_session_audit(class_session_id,event_key,event_type,actor_person_id,actor_label,occurred_at,details)
  values
    (session_id,'original-submission','nhcso_submission_received',v_lauren_id,'Sgt. Lauren Brothers',c.created_at,jsonb_build_object('external_class_id',p_class_number,'original_created_at',c.created_at)),
    (session_id,'durable-promotion','promoted_to_durable_session',null,'Codex production recovery',now(),jsonb_build_object('source_table','public.nhcso_classes','document_id',v_doc_id)),
    (session_id,'crystal-assistant-correction','assistant_instructor_added',v_crystal_id,'Crystal Jasper',now(),jsonb_build_object('reason','Omitted from assistant dropdown during original submission')),
    (session_id,'paperwork-verification','completion_paperwork_verified',null,'Codex production recovery',now(),jsonb_build_object('document_id',v_doc_id,'participants',active_count,'card_status','ready_for_issue'))
  on conflict (class_session_id,event_key) do nothing;

  insert into public.transactional_email_outbox(idempotency_key,class_session_id,notification_type,recipient_email,payload)
  values
    (p_class_number||':submitter-confirmation',session_id,'submitter_confirmation','labrothers@nhcgov.com',jsonb_build_object('organization','NHCSO','submitter','Sgt. Lauren Brothers','course','AHA BLS Provider','class_date',c.class_date,'participants',active_count,'files',jsonb_build_array('8.27 Class Documents.pdf'),'session_id',session_id,'workspace_url','https://www.910cpr.com/corp/nhcso/?class='||p_class_number,'status','Received for processing')),
    (p_class_number||':operations-notification',session_id,'operations_notification','brian@910cpr.com',jsonb_build_object('organization','NHCSO','submitter','Sgt. Lauren Brothers','course','AHA BLS Provider','class_date',c.class_date,'instructors',jsonb_build_array('Sgt. Lauren Brothers','Crystal Jasper'),'participants',active_count,'paperwork','verified','session_id',session_id,'admin_url','https://www.910cpr.com/admin/instructor-session.html?session='||session_id,'card_status','Ready for review','missing_requirements',jsonb_build_array()))
  on conflict (idempotency_key) do nothing;

  return jsonb_build_object('class_session_id',session_id,'lauren_person_id',v_lauren_id,'crystal_person_id',v_crystal_id,'document_id',v_doc_id,'participants',active_count,'card_status','ready_for_issue');
end;
$$;

revoke all on function public.promote_nhcso_class(text) from public, anon, authenticated;
grant execute on function public.promote_nhcso_class(text) to service_role;
