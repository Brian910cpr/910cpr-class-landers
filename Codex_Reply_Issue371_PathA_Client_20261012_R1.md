# Issue 371 — Path A prepared client transport

- Timestamp: 2026-10-12T13:39:34-04:00 (America/New_York).
- State: IN_PROGRESS / PR_OPEN; production NO-GO. Evidence: BUILT, locally validated only.
- Review branch: codex/issue371-client-20261012. Existing draft PR372 branch: feat/customer-learning-studio-20261010.
- Substantive commit: 665f3f1d58ad3688db73fdf3c3037f631e3de2d2. Receipt is a subsequent commit; pushed tip is recorded on issue371 and in final response.
- PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/372 . Keep draft, unmerged, undeployed.

## Execution and findings

Read full issue body/comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Acknowledged actual execution before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6129391603 . Latest controlling owner instruction is Path A; installation/staging prerequisites are superseded. No third-party instruction was treated as authorization. Existing launcher signal read at this dispatch showed current_task371, execution_process_alive true, no manual hold; assignments, launcher and observers unchanged.

Started isolated named worktree E:/GitHub/910cpr-issue371-client-20261012 at PR tip f7342ab89e1b1f93f47f723d26c39162c13ef71e using healthy repository. E:/GitHub/910cpr-class-landers unrelated tracked/untracked content and broken-ref condition from prior audit were preserved; no cleanup/reset/rebase/merge. Earl/Jackson tracked modifications appeared in the new worktree and remain unstaged; they are not part of this increment. No generator ran.

The Studio still uses tab-local operational state; admin-auth does not allow the CRM endpoint. This increment prepares the safe transport boundary without exposing UI or changing that allowlist. It does not claim to finish UI integration.

## Exact intended files

1. docs/admin/customer-interaction-client.mjs — default-disabled, unloaded transport for the existing manual saves, task mutations, interrupt/resume and paginated reads. Immutable request/payload/session snapshot; explicit identical retries; coalesced overlapping writes; copied confirmed receipts; terminal 4xx/conflict; replacement-session and late-response protection. No browser-storage draft queue, service credentials, new SDK or automatic retry loop.
2. tests/customer_interaction_client.test.mjs — seven local tests including actual handler with synthetic storage, lost response after commit, idempotent retry and stale-version 409. Auth/storage are injected in this harness: not real owner-session or database integration proof.
3. docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md — appended exact transport evidence, limitations and next UI/security gates. This is the primary review report; earlier live read-only audit remains data/audit/issue371_patha_metadata_20261012.json, unchanged.
4. Codex_Reply_Issue371_PathA_Client_20261012_R1.md — this unique root receipt.

## Validation

Local PGlite module reused at file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js. No production dependency installed.

Commands:

```powershell
$env:PGLITE_MODULE='file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js'
node --experimental-strip-types --test tests/customer_interaction_client.test.mjs tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs tests/customer_interruptions_sql.test.mjs tests/customer_interaction_pagination.test.mjs tests/customer_interaction_restart.test.mjs tests/customer_interaction_grants.test.mjs tests/customer_interaction_cors.test.mjs tests/admin_auth.test.mjs
node --experimental-strip-types --test tests/customer_interaction_client.test.mjs
node --check docs/admin/customer-interaction-client.mjs
node --check tests/customer_interaction_client.test.mjs
git diff --check
```

Exact results: initial combined suite tests48/pass48/fail0; final client suite tests7/pass7/fail0 after adding handler integration test and receipt-copy isolation. 49 distinct tests overall; syntax/diff checks exit0. No known related test failure. Existing SQL suite covers disk reopen, transactional rollback, interruption, grants, pagination and auth/privacy separately. Current Supabase changelog and CORS docs read; no SDK change required. Web tool could not fetch markdown content-type; PowerShell fetched changelog successfully. No remote customer API test performed.

## Remaining release gates / proof contract

Exact production blockers: recoverable production backup/restore evidence has not been established; durable feature-gated UI is not connected; real owner-session browser -> Edge Runtime -> PostgREST -> database save/reload/resume/conflict proof is absent. Production execution remains subject to separate explicit GO after review. No migration, function deployment, origin expansion, production UI exposure, merge, customer-data write, install or reboot occurred. No GO requested for incomplete gates.

Expected outcome: owner saves interaction notes and follow-ups that survive browser closure and can resume interrupted work. Cadence: on demand; no background process added. Last real owner end-to-end proof: none. Latest evidence is local synthetic tests in this dispatch. Failure: unconfirmed receipt, save/load error, session replacement or version conflict. Recovery: retain in-memory prepared envelope/draft, explicit identical retry after transient failure, reload/reconcile conflicts before new writes. Crash recovery still requires server checkpoints; in-memory prepared writes do not survive closing the browser. No active CRM outcome observer or observer-health proof exists; not MONITORED/HEALTHY, and Brian must not become the routine monitoring layer.

Next concrete action for ChatGPT/Codex: review the three exact implementation/report paths above, then continue same PR/workstream integrating existing Studio with default-off feature gate and owner auth allowlist, versioned asset references, server checkpoints and save-confirmed NEXT. Validate rendered browser recovery and actual backup evidence before separate production GO. Keep Production Board read-only. No new Brian action required for safe code/test continuation; production approval will be required only when complete safety findings are reviewable.

Receipt and intended implementation will be pushed to review branch and existing PR branch without force. GitHub receipt presence must be verified before final response. No ops/handoff/next_task.md use; no Codex_Read file created or renamed. No unrelated files intentionally added; existing unrelated files remain uncommitted.
