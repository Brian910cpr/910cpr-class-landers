# Canonical participant lifecycle foundation

Date: 2026-09-01
Branch: `codex/stabilization-integration`
Starting commit: `460f12765d4138c932421ef25f1583d0b755dbd5`
Production project: `wktwgcnwdvbebcobgyey`

## Outcome

The production lifecycle authority remains `customers -> registrations -> class_sessions`. No `landerware_people`, `landerware_registrations`, `landerware_sessions`, or alternate roster authority was created.

The canonical lifecycle migrations were deployed. All production-shaped command tests ran inside transactions that were rolled back. The new lifecycle tables contain zero rows after verification; no live customer, registration, payment, material, completion, credential, or import data was created by the tests.

## PR #109 reconciliation

Repository source now captures the deployed PR #109 behavior without invoking its data-changing promotion:

- `supabase/migrations/20260901014857_capture_nhcso_deployed_baseline.sql`
- `supabase/functions/nhcso-workspace/index.ts` from deployed version 5
- `supabase/functions/production-board/index.ts` from deployed version 3

The baseline migration defines the deployed NHCSO columns, indexes, session-support tables, outbox, and service-role-only `promote_nhcso_class` function. It does not call the promotion function or replay any historical rows.

Still separate and not brought forward:

- PR #109 static NHCSO/admin UI changes;
- notification worker configuration and delivery operations;
- PR audit prose;
- one-time recovery facts already present in production.

## Canonical structures deployed

- `customer_identity_aliases`
- `registration_supersessions`
- `registration_requirements`
- `registration_requirement_evidence`
- `participant_lifecycle_events`
- `participant_completions`
- `participant_credentials`
- `lifecycle_import_batches`
- `lifecycle_import_records`
- `registration_order_items.source_item_key`

All new tables have RLS enabled, no browser policy, browser grants revoked, and service-role grants retained. The public RPC ACLs contain only `postgres` and `service_role`.

Integrity guards reject:

- completion/credential customer, registration, session, or course mismatches;
- credentials tied to an unrelated completion;
- cross-customer, cross-session, or cross-course supersessions;
- updates/deletes to append-only lifecycle events;
- changes to an import record's batch, source identity, entity type, or original values.

## Commands deployed

### `register_participant`

The command:

- locks by idempotency key;
- resolves an explicit customer or a matched external alias;
- considers exact normalized email/phone evidence;
- returns `review_required` and persists ambiguity when exact evidence conflicts;
- never merges by similar name;
- creates one canonical customer when no match exists;
- creates or resolves the unique canonical registration;
- preserves existing local registration status on replay;
- fills, but does not overwrite, existing customer contact/organization facts;
- attaches participant requirements;
- creates one order and idempotent material/product items;
- appends a registered/imported lifecycle event;
- returns canonical customer, registration, session, and order identifiers.

Supported provenance values are data, not alternate models: retail, admin, corporate, instructor walk-in, Enrollware, historical import, and special event.

### `move_registration`

The command:

- locks by move idempotency key;
- requires the target session to have the same canonical course;
- preserves the source registration;
- creates/resolves the target registration;
- writes one immutable supersession;
- copies participant requirements with source linkage;
- transfers the canonical order and all its material items only under `financial_policy='transfer'`;
- supports explicit `retain` and `none` policies;
- leaves a completed source registration status unchanged;
- appends one move event;
- returns the same result on replay.

## Historical dry-run harness

Files:

- `scripts/historical_import_readiness.py`
- `tests/fixtures/historical_import_readiness.json`
- `tests/test_historical_import_readiness.py`

The harness is local/read-only and reports every requested category. It distinguishes alias, exact, proposed, ambiguous, duplicate, reschedule, completion, credential, payment, material, unknown, document, rejection, and protected-fact-conflict outcomes. Missing evidence becomes unknown. Existing facts that disagree are reported under `do_not_overwrite`.

Representative fixture result:

- 2 sessions discovered
- 1 alias match
- 1 new customer proposed
- 1 ambiguous identity
- 1 duplicate registration suppressed
- 1 registration proposed
- completion, credential, payment, material, and attachable document found
- 4 unresolved facts
- 1 attempted existing-fact change blocked/reported
- zero mutations

## Validation

Production-shaped rollback SQL:

- `tests/sql/canonical_participant_lifecycle_rollback.sql`

Covered:

- existing customer into another session;
- Enrollware replay;
- registration idempotency;
- conflicting identity review;
- rescheduling and replay;
- paid-order transfer;
- material attribution;
- participant requirements;
- lifecycle events;
- completion/credential preservation;
- walk-in through the shared command;
- corporate participant through the shared command;
- import-batch restartability;
- original-source-value precedence.

Results:

- production-shaped SQL transaction: passed and rolled back;
- new/local Python suite within selected affected tests: 98 passed, 2 failed;
- failures were existing MAXIM/static-page drift, not lifecycle failures:
  - public generated selector pages do not contain the shared projection call expected by `test_maxim_corporate_portal.py`;
  - MAXIM self-service page lacks the exact past-date condition expected by that test;
- Session Workspace PR #114 tests in a detached test worktree:
  - 9 workspace tests passed;
  - 4 production schema-contract tests passed;
  - 2 Deno projection tests passed;
  - 5 schedule publishing tests passed;
- availability JavaScript: 2 passed;
- dashboard schedule JavaScript: 7 passed;
- emergency schedule reader: 2 passed;
- NHCSO workspace and production-board Deno checks: passed after a type-only annotation correction;
- Supabase advisors run after deployment. New-table RLS-without-policy notices are expected because these are deliberately service-only tables. Foreign-key index notices introduced by the lifecycle schema were addressed by the follow-up index migration.

Advisory reference: https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy

## Production migrations applied

- `capture_nhcso_deployed_baseline`
- `canonical_participant_lifecycle`
- `canonical_lifecycle_fk_indexes`
- `canonical_lifecycle_integrity_guards`
- `fix_participant_fact_guard`

The final follow-up corrects credential-only field access in the shared participant-fact trigger. The complete rollback suite passed after that correction.

## Readiness

### CANONICAL LIFECYCLE READY?

YES. The canonical commands, identity ambiguity, reschedule lineage, requirements, lifecycle events, completion/credential records, provenance structures, integrity guards, and service-only access are deployed and rollback-tested.

### HISTORY DRY-RUN READY?

YES. The deterministic read-only harness explains a representative sample without production mutation.

### HISTORY IMPORT READY?

NO. A real historical source sample has not yet been mapped through the harness, and no human has reviewed its ambiguity/protected-fact report. Starting even a pilot mutation before that would risk source-field misinterpretation or identity misassociation.

## Exact next instruction

Export a small, non-sensitive pilot sample covering 3–5 completed historical classes into the harness JSON contract, including original source identifiers and unchanged source values. Run `scripts/historical_import_readiness.py` against a read-only production reference snapshot, review every ambiguous identity and protected-fact conflict, and save the approved reconciliation report. Do not mutate production until that report has zero unexplained ambiguities and every completion, credential, payment, material, and document attachment has an explicit disposition.
