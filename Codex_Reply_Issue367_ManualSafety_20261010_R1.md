# Issue 367 — manual safety slice and deep-stream gate

- Assignment: Brian910cpr/910cpr-class-landers#367.
- Timestamp: 2026-10-10, America/New_York (UTC-04:00).
- Branch: codex/issue367-preflight-20261010.
- Substantive commit: f3ab6ebb95d67bb366a3587f136cc24ffa4fc281.
- State: PR_OPEN; broader implementation BLOCKED by workstream allocation pending explicit handoff.
- PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/379 (draft, partial; does not close #367).
- Evidence: BUILT for this narrow manual UI change only. No end-to-end proof for issue 367.

## Authority and execution

Read the complete #367 body and comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md, LANDERWARE_PROOF_AND_HEALTH_STANDARD.md and docs/CODEX_INSTRUCTIONS.md. Read #354 pricing/session constraints and owner issue #116. Acknowledged execution before editing at https://github.com/Brian910cpr/910cpr-class-landers/issues/367#issuecomment-6104921472 .

The current dispatch explicitly says preserve one deep stream and all existing assignments. PR #372's current body identifies #371 as the continuing deep stream and says it must remain draft/unmerged/undeployed. Owner #116 says maximum active implementation streams is one. This run therefore advances a narrow independent safety slice, not a second complete checkout/database/scheduling implementation. The workstream allocation is an interpretation of these instructions, not a proven runtime worker lock. No arbitrary third-party comment was treated as owner authorization.

## Findings and work performed

Existing public-registration code validates public_direct_booking=true and registration_status=open against schedule_future.json; preserve this fail-closed gate. Existing native order SQL validates add-ons against the active server-side catalog and preserves per-student selections. Existing paidEmails queues manual add-on fulfillment rather than automatically releasing codes/materials.

The BLS manual UI previously offered a selectable Physical BLS Manual — $0 option. Changed it to a disabled radio, visibly marked Out of stock and styled unavailable; the direct-AHA link remains enabled and opens a new tab with noopener/noreferrer. Clarified the current 2025 BLS manual wording for own-copy and eBook choices. No catalog prices or IDs changed. The test executes the actual JavaScript productOptions renderer with Node and parses its emitted HTML.

This is a partial first slice. It does NOT implement the full BLS/ACLS/PALS/Heartsaver families, required per-course/cross-sell manual trees, program provenance, generalized native skills-session registration, or all eCode fulfillment records. It does not prove issue #367 complete or Enrollware independence.

## Exact files intentionally changed

1. docs/register/index.html
2. tests/test_public_registration_manual_availability.py
3. Codex_Reply_Issue367_ManualSafety_20261010_R1.md

Important review references: supabase/functions/public-registration/index.ts; supabase/migrations/20260909220000_native_public_checkout.sql; supabase/migrations/20260930030000_bls_public_registration_addons.sql; supabase/migrations/20260930050000_per_student_public_billing_codes.sql; tests/test_public_registration.py. These references were inspected, not changed.

## Validation and exact results

Command: python -B -m unittest discover -s tests -p test_public_registration_manual_availability.py -v
Result: Ran 1 test; OK. Checks disabled/unselected physical option, available eBook, own-copy default, out-of-stock wording, official AHA URL, new tab and noopener.

Node --check against each inline JavaScript block (via Python subprocess with encoding='utf-8'):
PASS: 2 inline JavaScript block(s) syntax checked
Python ast.parse against the new test:
PASS: Python test syntax

git diff --check -- docs/register/index.html tests/test_public_registration_manual_availability.py: pass, no output.

Baseline command: python -B -m unittest discover -s tests -p test_public_registration.py -v
Ran 11 tests; FAILED (failures=1); 10 passed.
Failure: test_only_real_bls_initial_sessions_route_to_native_registration.
AssertionError: "String(course.courseId) === '209806'" not found in BLS_PAGE.
This failure was observed before edits. It remains unresolved; neither fixture expectations nor public routing were changed to hide it.

First syntax-check attempt failed because Windows cp1252 could not encode U+25CF. Re-ran with explicit UTF-8 and both blocks passed. No source change was needed for that tooling error.

No desktop/mobile browser render proof, payment, webhook, production migration, function deployment, production build, or live checkout was performed. Rendered-template assertions are not browser visual QA.

## Workspace preservation and known unrelated failures

Original checkout: E:/GitHub/910cpr-class-landers, branch codex/durable-session-participant-linking. Preserved its dirty files, caches, runtime artifacts and assignments. Fetch failed with:
fatal: bad object refs/remotes/origin/codex/group-training-experience
error: https://github.com/Brian910cpr/910cpr-class-landers.git did not send all necessary objects

Did not delete references, reset, clean, rebase or repair that checkout. Used a separate real clone of the same repository at E:/GitHub/910cpr-issue367-20261010 based on main fd8514f8e01e6cbe42e90514119d2e33e67e39a2. Windows checkout reported case collisions; docs/Earl/index.html and docs/Jackson/index.html appear dirty solely after checkout and remain intentionally unstaged. No generated pages, caches or unrelated files were committed. No site generator ran.

## Delivery and remaining gates

Persisted locally, committed and pushed the narrow slice. PR #379 is draft. No merge or deployment. PR #372 was read only and remains untouched. No existing PR for #367 was found (open list and all-state search), so created this partial draft instead of duplicating an existing implementation PR. Swept the open queue; existing #374/#375 backend PRs already cover their respective fleet work, so did not create duplicate backend implementations or start another deep stream.

Next concrete action: explicitly hand off the single deep implementation allocation from #371 to #367 (or confirm #367 is now the primary), then reuse PR #379 and the established public-registration/order/catalog architecture. Absorb #354: scheduling course 210549, skills-only $55, online eProduct $41, total $96, one physical session/shared capacity, manual owner fulfillment. Extend verified catalogs/manual rules for other families without guessing IDs/prices, implement the complete acceptance matrix, resolve the baseline routing failure, run desktop/mobile browser checks and payment/webhook integration proof. Only then use the owner's #367 merge/deploy authority; never merge/deploy #372.

No credentials/account action was required to push this receipt. No repository-corruption repair is needed to continue in the clean clone. Supervisor workstream allocation is required to remove the interpreted deep-stream gate; no further payment or deployment permission is requested.

## Persistent-process proof limits

Last successful end-to-end proof for the requested family checkout: not established by this run. Expected proof is selected family/program/session -> correct Stripe amount -> durable paid registration/seat -> manual fulfillment requirement. Failure conditions include unavailable canonical session, incorrect pricing/manual program, duplicate registration/session, missed fulfillment and webhook failure. Existing observers/observer health and their cadence were not validated; do not classify this checkout as MONITORED or HEALTHY. Recovery: resume the scoped acceptance matrix on this branch after allocation; retain fail-closed session eligibility. Brian's manually authorized fulfillment remains an explicit operating dependency, not automated eCode delivery.
