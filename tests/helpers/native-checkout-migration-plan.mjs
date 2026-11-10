// Fixture prerequisites plus ALL eight new migrations, in release order.
// Never apply these schema/synthetic fixture files to any hosted database.
export const preProfileFiles=Object.freeze([
 'tests/helpers/reschedule-production-schema.sql',
 'supabase/migrations/20260909220000_native_public_checkout.sql',
 'supabase/migrations/20261019175346_registration_self_service_rescheduling.sql',
 'supabase/migrations/20261019175522_reschedule_confirmation_provider.sql',
 'supabase/migrations/20261019225039_registration_reschedule_dynamic_offers.sql',
 'supabase/migrations/20261106180848_skills_session_native_claim.sql',
 'tests/helpers/skills-native-workspace-guards.sql',
 'tests/helpers/skills-native-synthetic.sql',
 'tests/helpers/skills-checkout-documents.sql',
 'tests/helpers/bls-checkout-inventory.sql',
 'supabase/migrations/20261108142206_skills_checkout_and_optional_certificate.sql',
 'supabase/migrations/20261108145719_bls_native_checkout_integrity.sql',
 'supabase/migrations/20261110212444_native_checkout_additive_order_runtime.sql',
 'supabase/migrations/20261110225640_native_checkout_immutable_order_version.sql',
 'supabase/migrations/20261108145720_bls_heartcode_bundle_contract.sql',
 'supabase/migrations/20261108153759_checkout_confirmation_delivery_gate.sql',
 'tests/helpers/native-checkout-profile-schema.sql',
 'supabase/migrations/20261110195617_native_checkout_profile_columns_only.sql'
]);
export const profileMigration='supabase/migrations/20261108175130_native_checkout_course_profiles.sql';

export const fullCourseMigration='supabase/migrations/20261109120000_native_full_course_materialization.sql';

export const codeDeliveryMigration='supabase/migrations/20261109130000_native_learner_code_delivery.sql';

export const codeEventMigration='supabase/migrations/20261109140000_native_code_delivery_events.sql';

export const profileRuntime='supabase/migrations/20261110213124_native_checkout_profile_runtime_only.sql';

export const orderVersionMigration='supabase/migrations/20261110225640_native_checkout_immutable_order_version.sql';
