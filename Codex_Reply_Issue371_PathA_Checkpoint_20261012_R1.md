# Issue 371 — Path A checkpoint coordination

Timestamp: 2026-10-12 15:54 America/New_York (UTC-04:00).
Assignment: #371; existing draft PR https://github.com/Brian910cpr/910cpr-class-landers/pull/372.
Branch: codex/issue371-checkpoint-20261012; also advancing existing feat/customer-learning-studio-20261010 by fast-forward only.
Substantive commit: 5078a86e0c540550f869c2096952f8cdf5f40901.
State: IN_PROGRESS / PR_OPEN. Evidence: BUILT, validated locally. Not deployed, merged, CONNECTED to production, PROVEN end to end, MONITORED or HEALTHY.

## Execution and scope

Read full issue body/comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard before implementation; acknowledged actual execution on originating issue (comment 6131514398). Followed owner Path A superseding Docker/WSL/Synology prerequisites. Reused PR372 tip 7b9512d1813e062b672b391ab16748cbb1e2d7ec in isolated named worktree E:/GitHub/910cpr-issue371-checkpoint-20261012. Existing E: checkout dirty files/caches/receipts and D: Earl/Jackson edits remain untouched. New Windows worktree also reports tracked Earl/Jackson case-collision differences; explicitly excluded from staging. No reset, cleanup, broad build, installation, job/assignment/monitor changes, production write, deployment, origin expansion or merge.

Queue sweep found other open assignments; no unrelated work was claimed or displaced. Existing canonical launcher signal at 2026-10-12T19:52:22.6758835Z reported current_task=371, execution_process_alive=true, manual_hold=false. Single implementation stream preserved. Existing blocked #214/#297 input dependencies were not retried.

## Finding and substantive change

A successful older checkpoint must not mark newly typed notes saved. A lost response must not cause a new request ID for the same uncertain write. Added a prepared, unloaded checkpoint coordinator that retains immutable pending requests, protects newer draft edits, advances expected_version only from matching confirmed receipts, and guards navigation/reload while dirty or uncertain. Conflicts preserve drafts and allow explicit same-identity server-version reconciliation; this is an owner-reviewed merge boundary, not automatic overwrite. Uncertain transport failures cannot bypass retry via reconcile. No production flags, endpoint allowlisting or page imports changed.

Exact intended files:
- docs/admin/customer-interaction-checkpoint.mjs — prepared coordinator.
- tests/customer_interaction_checkpoint.test.mjs — six behavioral tests with real prepared transport.
- docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md — appended precise scope/proof limits/next integration.
- Codex_Reply_Issue371_PathA_Checkpoint_20261012_R1.md — this immutable receipt.

## Validation and exact results

Local existing cached PGlite 0.3.14 reused; no dependency added. Command:

```powershell
$env:PGLITE_MODULE='file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js'
node --experimental-strip-types --test tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs tests/customer_interruptions_sql.test.mjs tests/customer_interaction_pagination.test.mjs tests/customer_interaction_restart.test.mjs tests/customer_interaction_grants.test.mjs tests/admin_auth.test.mjs tests/customer_interaction_cors.test.mjs tests/customer_interaction_client.test.mjs tests/customer_interaction_checkpoint.test.mjs
node --check docs/admin/customer-interaction-checkpoint.mjs
node --check tests/customer_interaction_checkpoint.test.mjs
git diff --check
```

Output: tests 55; suites 0; pass 55; fail 0; cancelled 0; skipped 0; todo 0. Duration 10318.2144ms. Syntax/diff checks exit 0. No known unrelated test failure. These tests include injected transport/handler and synthetic database tests, not real owner browser/Edge Runtime/PostgREST integration.

## Remaining gates and recommended next action

Production remains NO-GO: actual recoverable backup/restore evidence, durable feature-gated Studio wiring and real owner-session browser/API/database reload/resume/conflict/failure proof remain absent. Separate explicit production migration/function/UI exposure approval is still required after safety gates pass. No approval of incomplete gates requested. No owner action needed for safe local continuation.

Continue same PR372: wire Studio edit/save/view behind default-off owner gate, display retained draft/loading/error/retry/conflict states, use save-confirmed navigation/NEXT, integrate atomic interruption/resume and server-loaded recovery. Reconciliation must first fetch and show current server work; callers must not present it as an automatic merge. Malformed server receipts remain unconfirmed and need diagnosis, never silent abandonment of the pending request. Prepare versioned assets only when page wiring is ready. Do not merge or deploy.

Operational proof: expected useful result is server-confirmed notes/tasks surviving browser closure. Cadence on demand. Last real end-to-end proof: none. Last successful component evidence: this local 55-test run. Failure condition: missing/invalid save receipt, dirty draft, inaccessible server state or conflict. Recovery: preserve draft/request; exact retry for uncertain failures; explicit fetched-version reconciliation for conflict. CRM outcome observer and observer health remain unimplemented; Brian must not become the routine monitoring layer. Existing launcher/observers retained unchanged.

Receipt push and GitHub presence are verified by this dispatch after commit; final pushed tip is reported on #371 and in the final response (avoids self-referential SHA).
