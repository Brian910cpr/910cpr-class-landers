-- Mirror the presently published Enrollware choices for the Initial BLS
-- registration path. Amounts are cents; the public function and database
-- procedure remain the source of truth for calculation before Stripe.
begin;

update public.landerware_registration_catalog
set addons = jsonb_build_array(
  jsonb_build_object(
    'key', 'aha_bls_provider_manual_ebook',
    'display_name', 'BLS Provider Manual eBook',
    'description', 'Electronic AHA BLS Provider Manual.',
    'unit_amount', 1749,
    'active', true
  ),
  jsonb_build_object(
    'key', 'aha_heartsaver_first_aid',
    'display_name', 'AHA Heartsaver First Aid',
    'description', 'Commonly selected by Recreation Therapy majors. Verify your school requirement.',
    'unit_amount', 5000,
    'active', true
  )
), imported_at = now()
where course_id = '209806' and active = true;

commit;
