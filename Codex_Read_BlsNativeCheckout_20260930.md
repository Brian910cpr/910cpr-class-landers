# BLS native checkout: add-ons, company picker, and no Enrollware restart

- **Timestamp:** 2026-09-30, America/New_York
- **Branch:** `codex/bls-registration-preview-20260930`
- **Implementation commit:** `51384b6eeb10fc638d2636a18e2c557f75ee1462`
- **State:** `BLOCKED` from production deployment only; source implementation and local validation complete.

## Evidence and finding

The live Initial BLS Enrollware page for session `14501248` is the authoritative source inspected for this work. It offers the BLS Provider Manual eBook for $17.49 and AHA Heartsaver First Aid for $50. The native LanderWare page was redirecting any native checkout error to Enrollware, which forced a duplicate registration.

## Work performed

- The LanderWare registration form now has a company-only Billing Code picker that begins suggesting after three characters. It exposes only AssistedCare, Breakthrough Autism, and the named Maxim organizations; generic and internal codes are absent from browser source.
- The form displays a required Initial-BLS manual acknowledgement, per-student add-on checkboxes, per-student totals, and a full pre-Stripe order total.
- The client sends selections to the existing server-side order procedure. That procedure remains authoritative for calculation and validation before Stripe Checkout.
- Removed the page-level automatic redirect to Enrollware on checkout failure. A real error remains on the LanderWare page with a readable reason.
- Added a versioned Supabase migration that configures the two verified Initial-BLS add-ons in `landerware_registration_catalog`.

## Files changed

- `docs/register/index.html`
- `supabase/migrations/20260930030000_bls_public_registration_addons.sql`
- `tests/test_public_registration.py`

## Validation

- `node` parsed all four inline scripts in `docs/register/index.html` successfully.
- `python -m unittest tests.test_public_registration`: **9 passed**.
- `git diff --check`: passed.

## Production blocker

The remote database migration is required before deploying the page. The live API presently returns an empty add-on catalog, so deployment without applying the migration would make the page show no add-ons and reject selected values.

This workstation has no `supabase` CLI on PATH or common installation paths, no linked `supabase/config.toml`, and no Supabase credentials available in the environment. The database must be deployed through the linked owner/CI environment with `supabase db push` (or the project’s established migration runner), then the page can be deployed and verified end to end.

## Important remaining decision

The picker has the named company codes but the existing public registration catalog has no verified financial treatment for those codes. The implementation intentionally does not invent discounts or corporate-payment terms. Existing database billing-code records must provide those terms before a selected company code can affect the total.

## Recommended next action

From the linked Supabase environment, first apply `20260930030000_bls_public_registration_addons.sql`; then merge/deploy this branch and verify one real Initial BLS session without submitting payment: verify each checkbox, $17.49 / $50 totals, three-character company suggestions, invalid-code behavior stays on page, and Stripe receives the server-calculated total.

- **Persistent-system evidence:** `BUILT`; not `CONNECTED` or `PROVEN` until the migration and checkout test complete.
- **User/account action required:** Supabase deployment credentials or the existing linked CI runner.
