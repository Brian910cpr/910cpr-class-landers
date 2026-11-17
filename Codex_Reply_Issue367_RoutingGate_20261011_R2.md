# Issue #367 — routing diagnosis and allocation gate

- Timestamp: 2026-10-11 UTC.
- Assignment: Brian910cpr/910cpr-class-landers#367.
- State: BLOCKED for full checkout-family implementation; bounded local diagnosis completed.
- Local branch: codex/issue367-validation-20261011-r2.
- Published branch / existing PR: codex/issue367-preflight-20261010 / #379 (draft).
- Reviewed base commit: 9a8ceb5b7d841a601d10f1c406fbf7e317f095ce. This communication-only commit is discoverable as the published branch tip; its SHA will be posted on #367 and returned by the launcher response.

## Exact blocker and next action

The latest owner handoff on #367 (20261011T032638Z-I367-MANUAL-SAFETY-READ-R1) explicitly preserves #371/#372 as the active deep stream and says to begin the remaining family implementation when the single-stream allocation is explicitly handed to #367. Issue #116 caps implementation at one stream. The latest #371 owner decision explicitly continues that existing assignment with local isolated staging. This dispatch also requires preserving one deep stream and existing assignments. No explicit allocation transfer was found. Do not infer one from third-party comments or the fact of dispatch.

Next supervisory action: explicitly hand off the single deep-stream allocation to #367, preserving #371's durable state, then resume existing PR #379. No account credentials or payment from Brian are required for this diagnostic slice. Do not merge or deploy #372.

## Work performed and findings

Read full #367 body and all comments, repository AGENTS.md, current CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md, LANDERWARE_PROOF_AND_HEALTH_STANDARD.md; inspected #116, #371 latest owner decisions, and #372/#379 current draft state. Acknowledged execution before implementation on originating issue:
https://github.com/Brian910cpr/910cpr-class-landers/issues/367#issuecomment-6105301040

Preserved unrelated dirty work in E:/GitHub/910cpr-class-landers and E:/GitHub/910cpr-issue367-20261010. Created isolated named branch/worktree at E:/GitHub/910cpr-issue367-validation-20261011, fetched current #379 head, and based this receipt on that head. Original checkout's two tracked changes plus caches/runtime artifacts were not staged. The prior #367 checkout has docs/Earl/index.html and docs/Jackson/index.html changes; these also appear as dirty tracked files in the newly materialized Windows worktree and remain excluded. No cleanup performed.

The baseline failing test is not safely dismissed as stale: tests/test_public_registration.py:105 expects native BLS routing, but docs/bls.html:1671 uses `link.href = course.appointmentUrl;`, matching scripts/build_bls_block_schedule_pilot.py:2223. Neither source contains nativeSessionId. This identifies the smallest source/output boundary for subsequent investigation, rather than proving the backend route or all live destinations fail. Do not remove the test assertion or relax fail-closed canonical eligibility just to make checks green. Before changing routing, validate current canonical eligibility, source identifiers and resolved inventory; then update only the necessary generator/output under the narrow-change gate.

Swept open issue titles for eligible independent backend work. The overlapping checkout/catalog/shared-session issues require their own source/dependency review and are not established low-risk independent quick wins. No unrelated backend implementation or second deep stream was started. This assignment makes no further progress toward Enrollware independence beyond preserving the prior manual-safety slice; full native replacement remains pending.

## Exact changed files

- Codex_Reply_Issue367_RoutingGate_20261011_R2.md (this receipt only).

No application source, generated page, migration, runtime configuration, or tests changed. No generator or broad build ran. Reuse #379; no duplicate PR.

## Local validation

- `python -B -m unittest discover -s tests -p test_public_registration_manual_availability.py`: 1 test passed; executes actual productOptions renderer with Node, inspects disabled physical radio, own-copy default, enabled eBook, out-of-stock text and direct AHA new-tab link.
- Public registration suite through unittest TestResult: 11 tests run; 10 passed, 1 failed, 0 errors. Failure: test_public_registration.PublicRegistrationTests.test_only_real_bls_initial_sessions_route_to_native_registration, expected native BLS routing expression absent in docs/bls.html. Pre-existing on reviewed base, unchanged.
- Python AST syntax: tests/test_public_registration.py, tests/test_public_registration_manual_availability.py, scripts/build_bls_block_schedule_pilot.py all pass (3 files).
- Node `--check` on actual registration inline scripts: 2 blocks pass. Initial local validation wrapper hit Windows cp1252 encoding; reran successfully with explicit UTF-8, without changing application files.
- `git diff --check`: passed before receipt; repeated for receipt before commit.

## Delivery and persistent proof limits

Persisted locally and pushed to existing #379 branch. Not merged, not deployed, no browser desktop/mobile proof, no payment/webhook execution or live checkout proof this dispatch. #372 untouched.

Prior manual-safety slice is BUILT with focused local renderer evidence, not PROVEN end to end. Full #367 implementation is incomplete. Last successful end-to-end proof: none established for the requested family matrix. Success must include correct family options -> eligible canonical session -> Stripe payment -> webhook -> durable registration/order -> manual/eCode fulfillment requirements, without duplicate Enrollware registration. Cadence is each checkout; failure is missing/mispriced products, invalid session eligibility, lost metadata or webhook/order mismatch. Observer and observer health for this expanded path are unverified; do not claim MONITORED or HEALTHY. Recovery: trace exact order/session/payment and webhook evidence, preserve fail-closed gates, fix the narrow failing component. Escalate only genuine account/auth or owner business decisions.

Remaining acceptance: four BLS/ACLS/PALS paths, three Heartsaver program pairs with preserved program/checkoff, native skills/bundle products and pricing, per-course manual subtrees including renewal cross-sells, physical-manual server/cart rejection, eManual/eCode fulfillment metadata, Stripe/webhook integrity, desktop/mobile rendering, and production verification after authorized green merge/deploy. Manual eCode fulfillment remains accepted; automation is not a launch gate.
