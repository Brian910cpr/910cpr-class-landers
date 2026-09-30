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
    'key', 'aha_heartsaver_first_aid_in_person',
    'display_name', 'AHA Heartsaver First Aid in person',
    'description', 'In-person AHA Heartsaver First Aid add-on.',
    'unit_amount', 5000,
    'active', true
  ),
  jsonb_build_object(
    'key', 'aha_heartsaver_first_aid_online',
    'display_name', 'AHA Heartsaver First Aid online',
    'description', 'Online AHA Heartsaver First Aid add-on.',
    'unit_amount', 6000,
    'active', true
  )
), billing_codes = jsonb_build_array(
  jsonb_build_object('code','assistedcare','company','AssistedCare','type','percent','amount',100,'active',true,'payer_mode','corporate_invoice'),
  jsonb_build_object('code','Breakthrough','company','Breakthrough Autism','type','percent','amount',100,'active',true,'payer_mode','corporate_invoice'),
  jsonb_build_object('code','Maxim','company','Maxim Homecare','type','percent','amount',100,'active',true,'payer_mode','corporate_invoice'),
  jsonb_build_object('code','MaximBH','company','Maxim Behavioral Health','type','percent','amount',100,'active',true,'payer_mode','corporate_invoice'),
  jsonb_build_object('code','MaximDSP','company','Maxim Direct Support Professionals','type','percent','amount',100,'active',true,'payer_mode','corporate_invoice')
), imported_at = now()
where course_id = '209806' and active = true;

commit;
