-- Isolated synthetic test schema. No hosted connection, operational row or credential.

CREATE TABLE public.landerware_confirmation_templates (template_key text PRIMARY KEY);
CREATE TABLE public.landerware_registration_profiles (
 profile_key text PRIMARY KEY, version integer NOT NULL DEFAULT 1,course_id text NOT NULL,
 display_name text NOT NULL,listed boolean NOT NULL DEFAULT false,registration_mode text NOT NULL,
 session_policy text NOT NULL CHECK (session_policy IN ('required','optional','not_applicable')),
 allowed_entry_contexts text[] NOT NULL,required_fields jsonb NOT NULL DEFAULT '[]',
 requirements jsonb NOT NULL DEFAULT '[]',addons jsonb NOT NULL DEFAULT '[]',payer_policy jsonb NOT NULL,
 pricing_behavior jsonb NOT NULL DEFAULT '{}',corporate_context jsonb NOT NULL DEFAULT '{}',
 confirmation_template_key text NOT NULL REFERENCES public.landerware_confirmation_templates(template_key),
 completion_prerequisites jsonb NOT NULL DEFAULT '[]',active boolean NOT NULL DEFAULT true,
 created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),
 form_schema jsonb NOT NULL DEFAULT '{}');
CREATE TABLE public.courses (
 id uuid PRIMARY KEY,course_key text NOT NULL UNIQUE,name text NOT NULL,enrollware_course_id text UNIQUE,
 base_price numeric,duration_minutes integer,setup_buffer_minutes integer NOT NULL DEFAULT 0,
 cleanup_buffer_minutes integer NOT NULL DEFAULT 0,max_students_default integer,
 registration_backend_default text,visibility_default text,
 registration_profile_key text REFERENCES public.landerware_registration_profiles(profile_key));
CREATE TABLE public.landerware_registration_catalog (
 course_id text PRIMARY KEY,course_name text,unit_amount integer,currency text,active boolean,
 addons jsonb,billing_codes jsonb);

CREATE OR REPLACE FUNCTION public.native_checkout_profile(p_public_course_id text, p_context text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare c public.courses; p public.landerware_registration_profiles; catalog public.landerware_registration_catalog;
begin
 if (select count(*) from public.landerware_registration_profiles r join public.courses x on x.registration_profile_key=r.profile_key
      where r.active and r.registration_mode='native_public_checkout' and exists(select 1 from jsonb_array_elements(coalesce(r.form_schema->'public_aliases','[]')) a
       where a->>'public_course_id'=p_public_course_id and (a->>'context' is null or a->>'context'=p_context)))>1 then raise exception 'native_profile_not_configured'; end if;
 select x.* into c from public.landerware_registration_profiles r join public.courses x on x.registration_profile_key=r.profile_key
   where r.active and r.registration_mode='native_public_checkout' and exists(select 1 from jsonb_array_elements(coalesce(r.form_schema->'public_aliases','[]')) a where a->>'public_course_id'=p_public_course_id and (a->>'context' is null or a->>'context'=p_context));
 if c.id is null then select * into c from public.courses where enrollware_course_id=p_public_course_id; end if;
 select * into p from public.landerware_registration_profiles where profile_key=c.registration_profile_key and active and registration_mode='native_public_checkout';
 if p.profile_key is null or p.course_id is distinct from c.course_key then raise exception 'native_profile_not_configured'; end if;
 select * into catalog from public.landerware_registration_catalog where course_id=c.enrollware_course_id and active;
 if catalog.course_id is null or catalog.currency<>'usd' or catalog.unit_amount<=0 or c.base_price*100 is distinct from catalog.unit_amount::numeric then raise exception 'price_catalog_missing'; end if;
 return jsonb_build_object('profile',to_jsonb(p),'physicalCourseId',c.enrollware_course_id,'catalog',jsonb_build_object('course_id',catalog.course_id,'course_name',catalog.course_name,'unit_amount',catalog.unit_amount,'currency',catalog.currency,'addons',catalog.addons));
end $function$
;
CREATE OR REPLACE FUNCTION public.native_checkout_profile_version_guard()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
begin
 if old.registration_mode='native_public_checkout' or new.registration_mode='native_public_checkout' then
  if new.version<old.version or ((to_jsonb(new)-array['version','updated_at','active','listed']) is distinct from (to_jsonb(old)-array['version','updated_at','active','listed']) and new.version<=old.version)
  then raise exception 'registration_profile_version_required'; end if;
 end if;
 return new;
end $function$
;
CREATE TRIGGER guard_profile_version BEFORE UPDATE ON public.landerware_registration_profiles
FOR EACH ROW EXECUTE FUNCTION public.native_checkout_profile_version_guard();
