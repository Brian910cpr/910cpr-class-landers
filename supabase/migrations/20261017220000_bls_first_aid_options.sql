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
    'product_key', 'AHA-SKILLS-HS_FA', 'component_skus', jsonb_build_array('25-1402','25-3149'),
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

-- Established store prices retained; current manufacturer identities recorded
-- independently of manufacturer retail pricing. No physical manual is sold.
update public.landerware_registration_catalog c
set addons=coalesce((select jsonb_agg(a.value order by a.ordinality)
 from jsonb_array_elements(c.addons) with ordinality a(value,ordinality)
 where a.value->>'key'<>'aha_bls_provider_manual_ebook'),'[]'::jsonb)
 || jsonb_build_array(jsonb_build_object('key','aha_bls_provider_manual_ebook',
 'display_name','2025 AHA BLS Student Manual eBook','unit_amount',1749,'active',true,
 'product_key','AHA-EBK-BLS','manufacturer_sku','25-3102','fulfillment_mode','manual',
 'manufacturer_url','https://ebooks.heart.org/product/bls-provider-manual-ebook50210131'))
where c.course_id in ('209806','359474');

update public.landerware_registration_catalog c
set addons=coalesce((select jsonb_agg(a.value order by a.ordinality)
 from jsonb_array_elements(c.addons) with ordinality a(value,ordinality)
 where a.value->>'key'<>'aha_heartcode_bls_online'),'[]'::jsonb)
 || jsonb_build_array(jsonb_build_object('key','aha_heartcode_bls_online',
 'display_name','2025 HeartCode BLS Online','unit_amount',4100,'active',true,
 'product_key','AHA-HC-BLS','manufacturer_sku','25-3553','fulfillment_mode','manual',
 'manufacturer_url','https://shopcpr.heart.org/heartcode-bls'))
where c.course_id='210549';

commit;
