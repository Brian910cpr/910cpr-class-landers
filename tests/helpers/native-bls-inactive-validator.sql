-- Read-only validator for the inactive/unbound BLS profile proposal.
-- This reports configuration only. It never activates or binds a profile.
WITH expected(public_id,course_key,profile_key) AS (
 VALUES ('209806','aha-bls-provider','native_bls_209806_v1'),
        ('359474','aha-bls-provider-renewal','native_bls_359474_v1')
)
SELECT e.public_id,e.course_key,e.profile_key,
 p.profile_key IS NOT NULL AS draft_present,
 p.active IS FALSE AS disabled,p.listed IS FALSE AS unlisted,
 NOT EXISTS(SELECT 1 FROM public.courses x WHERE x.registration_profile_key=e.profile_key) AS unbound_everywhere,
 c.registration_profile_key IS NULL AS canonical_binding_unchanged,
 c.base_price=75 AND cat.unit_amount=7500 AND cat.currency='usd' AND cat.active AS price_matches,
 p.registration_mode='native_public_checkout' AND p.course_id=e.course_key
  AND p.session_policy='required' AND p.form_schema->>'schemaVersion'='native-checkout.form.v1'
  AND p.form_schema->>'inventory_kind'='scheduled_session_v1' AS native_contract_matches,
 p.requirements='[]'::jsonb AND p.addons='[]'::jsonb AND p.completion_prerequisites='[]'::jsonb AS no_invented_upload_or_product_requirements,
 p.version,c.base_price,cat.unit_amount,c.duration_minutes,c.max_students_default,
 c.setup_buffer_minutes,c.cleanup_buffer_minutes,
 p.form_schema->>'max_students' AS form_group_limit
FROM expected e
LEFT JOIN public.courses c ON c.course_key=e.course_key AND c.enrollware_course_id=e.public_id
LEFT JOIN public.landerware_registration_catalog cat ON cat.course_id=e.public_id
LEFT JOIN public.landerware_registration_profiles p ON p.profile_key=e.profile_key
ORDER BY e.public_id;
