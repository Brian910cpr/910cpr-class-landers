-- Service-only read model; no profile binding, claiming, pricing or payment mutation.
begin;
set local lock_timeout='2s';
set local statement_timeout='15s';
create or replace function public.native_checkout_profile(p_public_course_id text,p_context text default null) returns jsonb
language plpgsql security invoker set search_path='' as $$
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
end $$;
revoke all on function public.native_checkout_profile(text,text) from public,anon,authenticated;
grant execute on function public.native_checkout_profile(text,text) to service_role;
commit;
