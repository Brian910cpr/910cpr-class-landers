-- Bind verified existing identities to their reviewed inactive generic profiles.
-- Does not activate checkout, change visibility/pricing/duration/capacity/buffers,
-- modify sessions/orders, or change existing non-null profile assignments.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
do $bindings$
declare binding record; c public.courses; p public.landerware_registration_profiles;
begin
 for binding in select * from (values
  ('209806','aha-bls-provider','native_bls_209806_v1'),
  ('359474','aha-bls-provider-renewal','native_bls_359474_v1'),
  ('509474','skills-session-only','native_skills_shared')
 ) as bindings(public_id,course_key,profile_key) loop
  if (select count(*) from public.courses where enrollware_course_id=binding.public_id and course_key=binding.course_key)<>1 then
   raise exception 'native_binding_course_identity_unverified:%',binding.public_id; end if;
  select * into c from public.courses where enrollware_course_id=binding.public_id and course_key=binding.course_key for update;
  select * into p from public.landerware_registration_profiles where profile_key=binding.profile_key for update;
  if p.profile_key is null or p.course_id is distinct from c.course_key
   or p.registration_mode is distinct from 'native_public_checkout' or p.active is distinct from false
   or p.version is distinct from 2 or p.form_schema->>'schemaVersion' is distinct from 'native-checkout.form.v1'
  then raise exception 'native_binding_profile_unverified:%',binding.public_id; end if;
  if c.registration_profile_key is not null and c.registration_profile_key is distinct from p.profile_key then
   raise exception 'native_binding_existing_assignment:%',binding.public_id; end if;
  update public.courses set registration_profile_key=p.profile_key where id=c.id and registration_profile_key is null;
 end loop;
end $bindings$;
commit;
