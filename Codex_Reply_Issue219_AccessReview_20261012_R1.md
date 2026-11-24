# Issue 219 — access boundary review and local backend validation

Timestamp: 2026-10-12 America/New_York (UTC-04:00).
Branch: codex/issue219-access-review-20261012
Substantive commit: 332f8df96ce2eb9d5592f9fcc67583016d1be4ca
State: BLOCKED for instructor rollout; reviewable test repair committed.

## Findings and exact blocker
The full issue and both owner comments were read. PR #222 already delivered owner-only document controls. Current main still imports authorizedOwner in supabase/functions/instructor-workbench/index.ts, rejects unauthenticated requests before routing, and uses service-role queries. The client uses LanderWareAdminAuth. No verified instructor login-to-canonical-Person binding or instructor-scoped authorization is present in that endpoint. A frontend instructor filter is not an authorization boundary.

Enabling instructor access safely requires a verified identity binding and an explicit assignment rule: whether lead_instructor_id alone is sufficient, whether assistants receive access, and what revocation does to historical classes. These facts cannot be inferred from display names or corporate credentials. No access was broadened. Authenticated production instructor click-through remains unproven; no instructor session was available or used in this dispatch. Requested clarification is recorded on #219.

## Work performed and files changed
- tests/instructor_documents.test.cjs: corrected both import-stripping expressions to accept CRLF as well as LF. Windows checkout previously caused all 12 checks to fail before execution with `Cannot use import statement outside a module`.
- Codex_Reply_Issue219_AccessReview_20261012_R1.md: this unique receipt.

Validation processed locally, no cloud inference or generators. After the repair, `node --test tests/instructor_documents.test.cjs`: 12 tests, 12 passed, 0 failed. Covers denied/absent credentials, corporate denial, exact class/document lookup, private signing, wrong storage path, missing file, confirmation, atomic removal, evidence preservation, idempotency, invalid IDs, CORS. `node --check tests/instructor_documents.test.cjs` and `node --check docs/assets/instructor-workbench.js`: passed. These are mocked endpoint tests, not live database or browser proof. UI cancellation and authenticated production click-through were not retested.

## Isolation and unrelated work
E:\GitHub\910cpr-class-landers retained all dirty/untracked files and its original branch. Fetch failed with bad object 6e61cabca5981d1389e52c60d95424d9893bb50f and broken refs/remotes/origin/codex/group-training-experience. No cleanup or ref repair was attempted. Work persisted in the real repository sparse clone E:\GitHub\910cpr-issue219-review-20261012 on the named codex branch. A separate full clone was also initiated at E:\GitHub\910cpr-issue219-20261012; it is not the implementation checkout and may still be downloading. Neither clone overwrote existing work.

Read current AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md, and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Existing stale checkout lacked the protocol and its stale origin/main lacked the ethos; fresh main contains both. Scanned 100 open issues and 60 open PRs. Preserved existing deep streams and assignments, including PR #372 (draft/unmerged/undeployed). No independent backend feature was safely selected from titles alone; the concrete backend-validation repair above advances this assignment without competing with those streams. No third-party comment was used as authorization. No retired handoff file used.

## Delivery and evidence
Locally persisted and validated; branch will be pushed with receipt and its GitHub presence verified before final response. Not merged or deployed. No migration, production data mutation, public build, or asset change. Existing owner-only controls: CONNECTED according to September 13 owner evidence; current instructor end-to-end state is not PROVEN. Last reported owner deployment verification: #219 owner comment of 2026-09-13T18:05:27Z; not current instructor proof.

Expected outcome: individually authenticated instructors view/remove documents only for authorized classes, preserving recovery and audit. Success evidence must include assigned/unassigned/revoked instructor cases and authenticated rendered UI success/cancellation/missing-file checks. Cadence: per document operation. Failure condition: denied legitimate assigned access or access granted outside assignment. Observer and observer health for that future instructor workflow are not established. Recovery: preserve owner-only guard, implement and test identity/assignment scope in isolation, then validate an authorized account. Escalation: owner decision on assignment semantics and account-level identity provisioning if not already established elsewhere.

Next action: review the two-line test repair; identify the existing authoritative instructor identity provider and verified auth subject-to-Person binding, confirm assistant/historical assignment policy on #219, then implement a single scoped backend stream. Do not share owner credentials, close #219, merge/deploy #372, or claim instructor completion from these mocked tests. User/account action is required only for unresolved policy or identity provisioning; routine validation stays local.
