# Issue 219 dispatch: instructor rollout gate

Timestamp: 20261014T204428Z UTC.
Branch: codex/issue219-access-review-20261012. Existing review PR: #389.
Reviewed branch commit: 2ca2f9b0a6b10def779e5d67bbae902d23c7ee86. Receipt commit is the pushed branch tip, reported on #219 and in the dispatch response.
State: BLOCKED for instructor rollout; existing PR_OPEN backend test repair preserved.

## Findings and exact blocker
Read the full #219 body and all comments, checkout AGENTS.md, current GitHub root CODEX_HANDOFF_PROTOCOL.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Acknowledged actual execution on #219 before implementation: issuecomment-6178016072.
Current default-branch supabase/functions/instructor-workbench/index.ts still imports authorizedOwner and rejects non-owner requests before routing. No owner answer has supplied the authoritative verified auth-subject-to-Person binding, assistant permission rule, or historical access after revocation. Do not infer identity from names or corporate sessions. These decisions block safe instructor rollout. Authenticated production instructor UI proof is also absent. No authorization changes were made.

## Work and exact changed files
Only Codex_Reply_Issue219_Dispatch_20261014T204428Z.md changed intentionally in this dispatch. Reused PR #389 and its named branch; no competing deep stream. Revalidated existing backend work locally. Reviewed related #368 canonical document scope and #215 owner/corporate auth separation. Scanned open CODEX queue and open PRs: existing assignments remain preserved; no independent backend change was selected without sufficient scope/ownership evidence. #368 requires canonical references rather than duplicate documents and does not resolve instructor identity.

## Validation
- node --test tests/instructor_documents.test.cjs: 12 passed, 0 failed.
- node --check tests/instructor_documents.test.cjs: passed.
- node --check docs/assets/instructor-workbench.js: passed.
- Existing PR #389 checks: documents, preflight, truncation-guard and Cloudflare preview reported passing before this receipt push.
Tests are mocked endpoint checks, not live database or authenticated browser proof. No generator, migration, production write, merge or deployment was performed. PR #372 remains OPEN and draft; untouched.

## Isolation and unrelated failures
Original E:\GitHub\910cpr-class-landers dirty work and all untracked receipts preserved. Fetch failed with `fatal: bad object refs/remotes/origin/codex/group-training-experience`; no repair or cleanup attempted. Created isolated real-repository clone E:\GitHub\910cpr-issue219-20261014 on existing PR #389 branch. Windows case collisions leave docs/Earl/index.html and docs/Jackson/index.html modified after checkout; these are unrelated, unstaged and excluded from this commit. No retired ops/handoff file was used.

## Delivery and proof contract
Persisted locally; receipt committed and pushed to existing PR branch, with remote Contents API verification required before exit. Not merged or deployed. Existing owner controls are CONNECTED per September 13 #219 deployment evidence; instructor workflow remains BUILT at most and is not PROVEN. No fresh successful instructor end-to-end cycle exists.
Expected outcome: individually authenticated instructors view/remove only authorized class documents, preserving audit/recovery and other classes. Success evidence: assigned/unassigned/revoked identity tests plus authenticated UI view/remove/cancel/missing-file checks and durable audit evidence. Window: each document operation. Failure: unauthorized access or legitimate assigned access denied. Observer and observer-health evidence for instructor workflow are not established; no HEALTHY claim. Recovery: retain owner-only guard, establish identity and assignment policy, implement scoped backend checks, then prove authenticated customer-facing flow. Escalation: owner policy decisions and identity/account provisioning if needed; Brian is not assigned routine monitoring.

Next action for ChatGPT: obtain the authoritative verified identity-to-Person binding and assistant/revoked historical access decisions on #219; then resume the existing implementation stream and coordinate with #368 canonical document references. Do not close #219 from mocked tests or share owner credentials. User/account action is required for those unresolved policy/identity decisions, not for routine local testing.
