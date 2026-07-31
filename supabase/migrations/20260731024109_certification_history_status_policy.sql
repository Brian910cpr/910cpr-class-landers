-- Review-only migration. Do not apply until the production-backed
-- certification-status dry run and migration review are approved.

alter table public.maxim_certification_history
  drop constraint if exists
    maxim_certification_history_certification_status_check;

alter table public.maxim_certification_history
  add constraint maxim_certification_history_certification_status_check
  check (
    certification_status in (
      'current',
      'expired',
      'superseded',
      'historical_unknown'
    )
  );

alter table public.maxim_certification_history
  drop constraint if exists
    maxim_certification_history_expiration_source_check;

alter table public.maxim_certification_history
  add constraint maxim_certification_history_expiration_source_check
  check (
    expiration_source in (
      'source',
      'calculated_policy',
      'existing_production',
      'unknown',
      -- Retain compatibility with the 15 existing production rows.
      'imported',
      'calculated'
    )
  );

alter table public.maxim_certification_history
  add column if not exists calculation_policy text,
  add column if not exists calculation_version text,
  add column if not exists calculated_from_date date,
  add column if not exists calculated_at timestamptz,
  add column if not exists status_evidence jsonb
    not null default '{}'::jsonb;

alter table public.maxim_certification_history
  drop constraint if exists
    maxim_certification_history_status_expiration_consistency_check;

alter table public.maxim_certification_history
  add constraint
    maxim_certification_history_status_expiration_consistency_check
  check (
    (
      certification_status = 'historical_unknown'
      and expiration_date is null
      and expiration_source = 'unknown'
    )
    or (
      certification_status <> 'historical_unknown'
      and (
        expiration_source is null
        or expiration_source <> 'unknown'
      )
      and (
        certification_status not in ('current', 'expired')
        or expiration_date is not null
      )
    )
  );

comment on column public.maxim_certification_history.expiration_source is
  'Provenance of expiration: source, calculated_policy, existing_production, '
  'unknown, or a retained legacy value.';

comment on column public.maxim_certification_history.calculation_policy is
  'Stable identifier for a reviewed expiration calculation policy.';

comment on column public.maxim_certification_history.calculation_version is
  'Version of the reviewed calculation policy used for this row.';

comment on column public.maxim_certification_history.calculated_from_date is
  'Source issue/class date used as the calculation input; never a parsed '
  'expiration date.';

comment on column public.maxim_certification_history.calculated_at is
  'Timestamp when the expiration policy calculation was performed.';

comment on column public.maxim_certification_history.status_evidence is
  'Structured proof or missing-evidence reasons supporting certification_status.';
