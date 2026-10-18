begin;

-- Owner-approved BLS cross-sell policy. Preserve unrelated products and billing codes.
update public.landerware_registration_catalog c
set addons = coalesce((
  select jsonb_agg(a.value order by a.ordinality)
  from jsonb_array_elements(c.addons) with ordinality a(value, ordinality)
  where a.value->>'key' not in (
    'aha_heartsaver_first_aid_online', 'aha_heartsaver_first_aid_in_person'
  )
), '[]'::jsonb) || jsonb_build_array(
  jsonb_build_object(
    'key', 'aha_heartsaver_first_aid_online',
    'display_name', 'Online First Aid + in-person skills',
    'unit_amount', 5000, 'active', true,
    'fulfillment_mode', 'manual', 'recommended', true,
    'includes_online_program', true, 'includes_student_ebook', true,
    'includes_skills_testing', true, 'additional_onsite_minutes', 0
  ),
  jsonb_build_object(
    'key', 'aha_heartsaver_first_aid_in_person',
    'display_name', 'First Aid in person',
    'unit_amount', 6000, 'active', true,
    'fulfillment_mode', 'manual',
    'additional_onsite_minutes', 0
  )
),
source_snapshot = coalesce(c.source_snapshot, '{}'::jsonb) || jsonb_build_object(
  'first_aid_policy', jsonb_build_object(
    'source', 'owner-approved', 'decision_date', '2026-10-17',
    'online_includes_skills', true, 'additional_onsite_minutes', 0
  )
)
where c.course_id in ('209806', '359474', '210549');

commit;
