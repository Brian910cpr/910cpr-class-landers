# BLS native checkout per-student options

- **Timestamp:** 2026-09-30, America/New_York
- **Branch:** `codex/bls-registration-preview-20260930`
- **Implementation commit:** `338cf486dae`
- **State:** `PR_OPEN`, with the same Supabase deployment gate recorded in `Codex_Reply_BlsNativeCheckout_20260930.md`.

## Change

Moved Promo/Billing Code into every student card. Add-ons were already represented per student in the submitted order and are now visibly organized with that student’s code and subtotal. The first student card has an optional **Apply this student’s add-ons and billing code to all students** checkbox. It copies the first student’s selected add-ons and code to existing and newly added students, while leaving every student card editable afterward.

## Validation

- Inline JavaScript syntax check passed.
- `python -m unittest tests.test_public_registration`: 9 passed.
- `git diff --check`: passed.

## Remaining gate

The live Supabase procedure currently has an order-level billing-code field. The submitted per-student codes are prepared in the client but require the queued database migration work to persist and apply distinct financial treatments per student. No financial behavior has been invented.
