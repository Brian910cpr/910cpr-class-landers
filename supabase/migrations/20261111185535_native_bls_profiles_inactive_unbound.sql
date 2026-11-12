-- Local proposal only. Add two inactive, unlisted, unbound native BLS profiles.
-- No course/catalog/session/registration/payment/retail/MAXIM changes.
-- Technical profile draft; not inventory activation or end-to-end checkout proof.
BEGIN;
SET LOCAL lock_timeout = '2s';
SET LOCAL statement_timeout = '30s';
LOCK TABLE public.courses, public.landerware_registration_catalog IN SHARE MODE;
LOCK TABLE public.landerware_registration_profiles IN SHARE ROW EXCLUSIVE MODE;

DO $drafts$
DECLARE
  drafts constant jsonb := $profiles$
[
  {
    "profile_key": "native_bls_209806_v1",
    "version": 1,
    "course_id": "aha-bls-provider",
    "display_name": "AHA BLS Provider - In-Person",
    "listed": false,
    "registration_mode": "native_public_checkout",
    "session_policy": "required",
    "allowed_entry_contexts": [],
    "required_fields": [
      "first_name",
      "last_name",
      "email",
      "phone"
    ],
    "requirements": [],
    "addons": [],
    "payer_policy": {
      "mode": "customer_pays"
    },
    "pricing_behavior": {
      "mode": "catalog_options"
    },
    "corporate_context": {},
    "confirmation_template_key": "native-checkout-profile-v1",
    "completion_prerequisites": [],
    "active": false,
    "form_schema": {
      "schemaVersion": "native-checkout.form.v1",
      "inventory_kind": "scheduled_session_v1",
      "fields": [
        {
          "key": "first_name",
          "wire": "firstName",
          "type": "text",
          "label": "First name",
          "required": true
        },
        {
          "key": "last_name",
          "wire": "lastName",
          "type": "text",
          "label": "Last name",
          "required": true
        },
        {
          "key": "email",
          "wire": "email",
          "type": "email",
          "label": "Email",
          "required": true
        },
        {
          "key": "phone",
          "wire": "phone",
          "type": "tel",
          "label": "Phone",
          "required": true
        }
      ],
      "max_students": 6,
      "option_groups": [
        {
          "key": "manual",
          "type": "radio",
          "label": "Course materials",
          "required": true,
          "choices": [
            {
              "key": "customer_supplied_manual",
              "label": "I will bring the current AHA BLS Provider Manual",
              "catalog_keys": [],
              "bindings": {
                "manualChoice": "own-copy"
              }
            }
          ]
        }
      ],
      "default_choices": [
        "customer_supplied_manual"
      ],
      "driver_rules": [
        {
          "driver": "native_order"
        }
      ],
      "back_url": "/bls.html",
      "description": "Bring the current AHA BLS Provider Manual. The manual is not included in this registration option."
    }
  },
  {
    "profile_key": "native_bls_359474_v1",
    "version": 1,
    "course_id": "aha-bls-provider-renewal",
    "display_name": "AHA BLS Provider - In-Person Renewal",
    "listed": false,
    "registration_mode": "native_public_checkout",
    "session_policy": "required",
    "allowed_entry_contexts": [],
    "required_fields": [
      "first_name",
      "last_name",
      "email",
      "phone",
      "current_bls_card_ack"
    ],
    "requirements": [],
    "addons": [],
    "payer_policy": {
      "mode": "customer_pays"
    },
    "pricing_behavior": {
      "mode": "catalog_options"
    },
    "corporate_context": {},
    "confirmation_template_key": "native-checkout-profile-v1",
    "completion_prerequisites": [],
    "active": false,
    "form_schema": {
      "schemaVersion": "native-checkout.form.v1",
      "inventory_kind": "scheduled_session_v1",
      "fields": [
        {
          "key": "first_name",
          "wire": "firstName",
          "type": "text",
          "label": "First name",
          "required": true
        },
        {
          "key": "last_name",
          "wire": "lastName",
          "type": "text",
          "label": "Last name",
          "required": true
        },
        {
          "key": "email",
          "wire": "email",
          "type": "email",
          "label": "Email",
          "required": true
        },
        {
          "key": "phone",
          "wire": "phone",
          "type": "tel",
          "label": "Phone",
          "required": true
        },
        {
          "key": "current_bls_card_ack",
          "type": "checkbox",
          "label": "I understand I must bring a current, valid AHA BLS Provider card to class.",
          "required": true
        }
      ],
      "max_students": 6,
      "option_groups": [],
      "default_choices": [],
      "driver_rules": [
        {
          "driver": "native_order"
        }
      ],
      "back_url": "/bls.html",
      "description": "Bring a current, valid AHA BLS Provider card to class. If your card is expired, contact us before registering to verify eligibility."
    }
  }
]
$profiles$::jsonb;
  draft jsonb;
  existing jsonb;
  public_id text;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.landerware_confirmation_templates
    WHERE template_key='native-checkout-profile-v1'
  ) THEN
    RAISE EXCEPTION 'native_bls_draft_confirmation_template_missing';
  END IF;

  FOR draft IN SELECT value FROM jsonb_array_elements(drafts) LOOP
    public_id := CASE draft->>'course_id'
      WHEN 'aha-bls-provider' THEN '209806'
      WHEN 'aha-bls-provider-renewal' THEN '359474'
      ELSE NULL END;

    IF public_id IS NULL OR NOT EXISTS (
      SELECT 1 FROM public.courses c
      JOIN public.landerware_registration_catalog cat
        ON cat.course_id=c.enrollware_course_id
      WHERE c.course_key=draft->>'course_id'
        AND c.enrollware_course_id=public_id
        AND c.registration_profile_key IS NULL
        AND c.base_price=75 AND cat.unit_amount=7500
        AND cat.currency='usd' AND cat.active
    ) THEN
      RAISE EXCEPTION 'native_bls_draft_course_price_or_binding_mismatch: %', public_id;
    END IF;

    IF EXISTS (
      SELECT 1 FROM public.courses
      WHERE registration_profile_key=draft->>'profile_key'
    ) THEN
      RAISE EXCEPTION 'native_bls_draft_already_bound: %', draft->>'profile_key';
    END IF;

    SELECT to_jsonb(p)-ARRAY['created_at','updated_at']
      INTO existing FROM public.landerware_registration_profiles p
      WHERE p.profile_key=draft->>'profile_key';
    IF existing IS NOT NULL THEN
      IF existing IS DISTINCT FROM draft THEN
        RAISE EXCEPTION 'native_bls_draft_existing_profile_drift: %', draft->>'profile_key';
      END IF;
    ELSE
      INSERT INTO public.landerware_registration_profiles (
        profile_key, version, course_id, display_name, listed, registration_mode, session_policy, allowed_entry_contexts, required_fields, requirements, addons, payer_policy, pricing_behavior, corporate_context, confirmation_template_key, completion_prerequisites, active, form_schema
      )
      SELECT p.profile_key, p.version, p.course_id, p.display_name, p.listed, p.registration_mode, p.session_policy, p.allowed_entry_contexts, p.required_fields, p.requirements, p.addons, p.payer_policy, p.pricing_behavior, p.corporate_context, p.confirmation_template_key, p.completion_prerequisites, p.active, p.form_schema
      FROM jsonb_populate_record(NULL::public.landerware_registration_profiles,draft) p;
    END IF;
  END LOOP;

  -- These are deliberate release barriers, not activation instructions.
  IF (SELECT count(*) FROM public.landerware_registration_profiles
      WHERE profile_key IN ('native_bls_209806_v1','native_bls_359474_v1')
        AND active=false AND listed=false
        AND registration_mode='native_public_checkout'
        AND form_schema->>'inventory_kind'='scheduled_session_v1') <> 2
     OR EXISTS (
      SELECT 1 FROM public.courses
      WHERE registration_profile_key IN ('native_bls_209806_v1','native_bls_359474_v1')
     ) THEN
    RAISE EXCEPTION 'native_bls_draft_disabled_unbound_assertion_failed';
  END IF;
END
$drafts$;
COMMIT;
