-- Existing unified-profile table shape, isolated from legacy registration and
-- person tables on purpose. Native checkout reads configuration, not their IDs.
create table public.landerware_confirmation_templates(template_key text primary key,subject_template text not null,body_template text not null,delivery_provider text not null default 'gmail',active boolean not null default true);
create table public.landerware_registration_profiles(
 profile_key text primary key,version integer not null default 1,course_id text not null,display_name text not null,
 listed boolean not null default false,registration_mode text not null,session_policy text not null,
 allowed_entry_contexts text[] not null,required_fields jsonb not null default '[]',requirements jsonb not null default '[]',
 addons jsonb not null default '[]',payer_policy jsonb not null,pricing_behavior jsonb not null default '{}',corporate_context jsonb not null default '{}',
 confirmation_template_key text not null references public.landerware_confirmation_templates(template_key),completion_prerequisites jsonb not null default '[]',active boolean not null default true,
 created_at timestamptz not null default now(),updated_at timestamptz not null default now());
create table storage.objects(id uuid primary key default gen_random_uuid(),bucket_id text not null,name text not null,metadata jsonb not null default '{}',unique(bucket_id,name));
