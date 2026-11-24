# Issue 380 R14 — isolated resolution transaction foundation

2026-10-12 UTC. Existing draft PR #381; BUILT, validated locally only.

The original owner request remains intact: handled/manual and verified resolution, private evidence, searchable history, justified reopen, and canonical reconciliation before execution. This increment advances the canonical transaction rather than another advisory guard. It does not finish any acceptance criterion.

## Review files

- `data/audit/issue380_resolution_transaction_draft.sql`: deliberately outside migration discovery. Additive card version/resolution columns, version trigger on every update (including legacy writes), append-only service-role resolution events, service-role-only invoker transaction. Row lock checks expected version; request advisory lock serializes idempotency keys including cross-card reuse. Exact payload replay returns original result; changed payload conflicts. Card update, event and existing activity insertion commit or roll back together. Reopen uses the same transition and requires explanation/source. Lane is preserved; future views must derive active status from resolution_state.
- `tests/reconciliation/board-resolution.test.mjs`: executes existing tracked board migration and draft SQL in ephemeral PGlite PostgreSQL, with real SQL role changes and forced audit failure.

No evidence-attached flag is created: supplied source/explanation is provenance, not verified attachment. No customer data used. The future owner proxy must authenticate owner, bind actor, validate completion time and source, distinguish verification from manual assertion, and never trust client actor. Service role is trusted backend authority; this is not an owner auth implementation. Existing activity remains mutable under its legacy grants; the new resolution event table permits service SELECT/INSERT only. Administrative superusers remain capable of modifying database objects.

## Validation

`npm ci --ignore-scripts --no-audit --no-fund` in existing `tests/reconciliation`: one pinned existing dependency installed, no manifest/lockfile changes.

`node --test board-resolution.test.mjs` from that directory: 1 integration test passed, 0 failed. Covers initial resolution, exact retry, conflicting retry, stale writer, ordinary update version invalidation, justified reopen, original-result replay after reopen, event UPDATE/DELETE denial, atomic rollback after forced activity-insert failure, and anon/authenticated function/table denial.

Existing focused backend suite: `node --test tests/live_dispatch_check.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/owner_access.test.mjs`: 60 passed, 0 failed. `node --check tests/reconciliation/board-resolution.test.mjs` and `git diff --check` pass. SQL syntax executed by PostgreSQL. PGlite uses one connection: stale-writer tests are sequential; no multi-session contention, deadlock, or live Supabase advisor proof is claimed.

## Gates and operational proof

No production migration, remote database call, runtime install/state/task/process mutation, generator, merge or deployment. Supabase docs/security checklist reviewed; invoker semantics, empty search_path, explicit function revocation and RLS preserved. Supabase changelog retrieved locally; HTTP TLS deprecation does not affect the local SQL test. SQL is a review draft, not rollout-ready migration. Live owner-context columns described in prior reports were not re-inspected this dispatch. Original dirty checkout preserved; Windows checkout collision dirt in `docs/Earl/index.html` and `docs/Jackson/index.html` excluded. Queue scanned without claiming other existing assignments; #371 remains primary, #372 untouched.

Next: review transaction and owner proxy contract, extend canonical typed intake and transactional claim/skip with leases/idempotency and durable audit, then prove multi-connection contention and actual pre-mutation fencing. Promote reviewed SQL through Supabase migration tooling only after coordinated API/list/history/count readiness. Private evidence/upload and UI remain unfinished. There is no credential blocker or Brian-only action now; unfinished engineering/review gates remain.

Design: this follows existing card identity and mature versioned transition/audit practice, preserving provenance instead of deleting work. No Enrollware workflow or dependency changes; native LanderWare lifecycle infrastructure advances independence without asserting replacement proof.

Expected end-to-end outcome: resolved/blocked/stale work skipped with durable audit before each launch/side effect. Last real proof: none. Failure: execution despite canonical stop state or missing durable audit. Observer/observer heartbeat: not integrated. Recovery: preserve evidence, hold approved runtime, finish transaction/fencing and test before rollout. Escalation: engineering/review now, separate production authorization later. Automated monitoring remains unfinished; Brian must not become the routine observer.
