-- Isolated synthetic fixture: only columns/keys used by the captured functions.
-- Not a full production schema or proof of the complete deployed trigger chain.
do $$ begin
 if not exists(select 1 from pg_roles where rolname='anon') then create role anon; end if;
 if not exists(select 1 from pg_roles where rolname='authenticated') then create role authenticated; end if;
 if not exists(select 1 from pg_roles where rolname='service_role') then create role service_role; end if;
end $$;
create table courses(id uuid primary key default gen_random_uuid(),course_key text unique,name text,duration_minutes integer,max_students_default integer);
create table customers(id uuid primary key default gen_random_uuid(),first_name text,last_name text,email text);
create table locations(id uuid primary key default gen_random_uuid(),name text);
create table people(id uuid primary key default gen_random_uuid(),display_name text);
create table class_sessions(id uuid primary key default gen_random_uuid(),source text,status text,course_id uuid references courses,start_at timestamptz,end_at timestamptz,timezone text,consumption_start_at timestamptz,consumption_end_at timestamptz,location_id uuid references locations,lead_instructor_id uuid references people,resource_id uuid,organization_id uuid,max_students integer,registration_backend text,visibility text,registration_status text,record_scope text,source_location_label text,source_instructor_label text,external_class_id text,public_notes text,external_session_evidence jsonb default '{}');
create table landerware_sessions(id uuid primary key default gen_random_uuid(),class_session_id uuid unique references class_sessions,external_session_id text,course_id text,course_name text,starts_at timestamptz,ends_at timestamptz,location_name text,instructor_name text,lifecycle_state text,provenance text,requirements_manifest jsonb default '{}',document_ids jsonb default '[]',updated_at timestamptz default now());
create table registrations(id uuid primary key default gen_random_uuid(),customer_id uuid references customers,class_session_id uuid references class_sessions,status text,registration_source text,idempotency_key text unique,material_choice text,external_reconciliation_evidence jsonb,updated_at timestamptz default now(),unique(customer_id,class_session_id));
create table class_session_audit(id uuid primary key default gen_random_uuid(),class_session_id uuid references class_sessions,event_key text,event_type text,actor_label text,occurred_at timestamptz,details jsonb);
create table landerware_registrations(id uuid primary key,session_id uuid,status text);
