# Hx-Builder Foundational Migration Review

Reviewed base commit: `63322346d760c9ce074acd5cb7b8b435b4add9ac`

Scope: source fingerprints, evidence assertions, entitlement pools/events, the two observed AHA eCard products, and their exact Enrollware student-report aliases. No historical import, application deployment, or production migration application was performed.

## Findings corrected during review

1. **Product alias collisions were silent.** `ON CONFLICT DO NOTHING` could leave an existing exact alias pointing at a different product, and name-based resolution could return multiple canonical candidates. The migration now requires exactly one candidate and raises on any alias/product disagreement.
2. **New source-version fields were mutable.** The existing production trigger protected batch, source record ID, entity type, original values, but not `source_system`, fingerprint, fingerprint algorithm, or predecessor. The guard now protects every durable source-version field.
3. **Predecessor linkage was under-constrained.** A predecessor could point to a different source identity. A trigger now requires the same source system, source record ID, and entity type, plus a self-reference check.
4. **Imported inventory could look operational immediately.** Pools and events now default to `reconciliation_status='unreviewed'`; pools default to lifecycle `status='unknown'`. No balance view or automatic canonical write is introduced.
5. **Proposed products were active.** Both new canonical products now enter product master inactive. Existing equivalent products are reused and are not overwritten.
6. **Supersession/reversal could fork.** Partial unique indexes permit one direct superseder/reversal per prior row, with self-reference checks.
7. **Evidence could lose its import-record link.** The evidence-to-import-record foreign key now uses `ON DELETE RESTRICT`.

## Contract review

- **Foreign keys/delete behavior:** canonical customer, organization, registration, session, completion, credential, product, pool, batch, and order-item tables are referenced. Authority-bearing or forensic links use `RESTRICT`; the optional operational order-item link uses `SET NULL`. Import batches cannot be deleted while referenced.
- **Uniqueness:** exact replay is globally unique on `(source_system, source_record_id, entity_type, source_fingerprint_algorithm, source_fingerprint)`. Batch-local uniqueness remains compatible. Alias identity is exactly `(source_system, source_value)`. Event/assertion keys are globally unique.
- **Indexes/query paths:** source identity/version lookup, predecessor traversal, review queues, pool owner/product/batch, event pool/time/entity/batch, evidence source/entity/batch, and supersession/reversal paths are indexed.
- **RLS/browser exposure:** all four new public tables have RLS enabled. `anon` and `authenticated` receive zero grants; only `service_role` is granted table access. Helper functions are security-invoker and not executable by browser roles.
- **Append-only semantics:** inventory events and evidence assertions reject update/delete. Corrections, reversals, reconciliation, and supersession require new rows. Pools remain mutable because their review/lifecycle state must be operable.
- **Import-batch linkage:** pools, events, and assertions require a durable batch foreign key. Evidence may additionally retain a restricted import-record link.
- **Fingerprint versioning:** the algorithm is part of the unique version key. Legacy rows backfill under `sha256-jsonb-text-legacy-v1`; new worker records use `sha256-canonical-json-v1`. Changed evidence becomes a new version in a separate batch and may link to an immutable same-identity predecessor.
- **Authority boundary:** evidence, pools, and events default to `unreviewed`. The migration contains no inserts into `registrations`, `class_sessions`, `participant_completions`, or `participant_credentials`; no trigger or function promotes imported evidence into those tables. Products are the only canonical master rows added, and they are inactive.
- **Product collision behavior:** exact aliases are inserted only after unique canonical product resolution. Existing equivalent products are reused. Conflicting aliases or multiple equivalent candidates abort the migration.

## Rolled-back production-schema validation

Project: `wktwgcnwdvbebcobgyey` (PostgreSQL 17.6).

- Full migration executed successfully inside `BEGIN ... ROLLBACK`.
- The migration executed twice in one transaction successfully, proving DDL/data-seed rerun safety.
- Exact fingerprint replay across separate batches raised the expected unique violation.
- Fingerprint mutation raised the expected immutability exception.
- Cross-identity predecessor linkage raised the expected exception.
- A deliberately conflicting `AHA-BLS-ECARD` alias aborted with the expected collision exception.
- Event and evidence updates raised the expected append-only exception.
- Pool, event, and assertion authority defaults were all `unreviewed`.
- Both proposed products existed inside the transaction as inactive; exactly two aliases resolved.
- All four new tables had RLS enabled and zero browser-role grants.
- Post-rollback verification: zero new products, zero new tables, zero new columns.

## Validation

- Hx-Builder schema/behavior tests: `16 passed`.
- Python syntax validation: passed.
- `git diff --check`: passed.

Recommendation: **SAFE TO APPLY FOUNDATIONAL MIGRATION**
