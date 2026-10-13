# Native registration checkpoint

Assignment: make native registration the primary P1 workstream, starting with AHA BLS Renewal.

Status: BUILT/local validation for initial webhook hardening; complete purchase NOT PROVEN; not deployed.

Full evidence, exact source/migration/test paths, production findings, blockers and next actions: `data/audit/native_bls_renewal_first_slice_20261012.md`.

Branch: `codex/native-registration-bls-renewal`. Intentional changes: webhook, behavioral tests, audit and this reply. No generated outputs or production data changed. Existing Enrollware fallback retained. Stripe reconnection succeeded; no current connector-auth blocker.

16 local behavioral tests pass. Existing public-registration suite has one pre-existing stale renderer assertion failure, documented in the report. No full payment/registration/roster/email/availability transaction has been demonstrated.

Next: repair public-order payment routing and transactional seat/roster/confirmation consistency, then prepare the narrow approval-gated release. Do not merge/deploy this partial checkpoint as completion of native registration.
