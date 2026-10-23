# Issue 371 — malformed checkpoint recovery

- Timestamp: 2026-10-13 America/New_York; exact commit timestamps in Git.
- Assignment: Brian910cpr/910cpr-class-landers#371; existing draft PR #372.
- Branch: codex/issue371-recovery-20261013; PR branch feat/customer-learning-studio-20261010.
- Base: 57cc241c3830c237f4096eee98022900ccc299be.
- Substantive commit: 49b2ab279c551739d5b79e4cf8f5f998eed99140. Receipt committed separately; pushed tip reported on issue and final response.
- State: IN_PROGRESS / PR_OPEN. Evidence: BUILT, validated locally with synthetic fixtures. Not production-complete or HEALTHY.
- Actual pre-implementation acknowledgment: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6142295623

## Findings and work

Read issue body/comments and repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard. Continued owner Path A and existing PR; no third-party authorization used. The E: original checkout fetch failed with bad object 6e61cabca5981d1389e52c60d95424d9893bb50f and broken origin/codex/group-training-experience reference. Its dirty work and references remain untouched. Healthy D: repository fetched the existing PR tip and supplied isolated worktree E:/GitHub/910cpr-issue371-recovery-20261013. No duplicate project/PR/implementation stream or assignment changes.

Found transport cached structurally valid but wrong-ID/nonadvancing/nonnumeric-version save acknowledgments. Coordinator correctly refused navigation, but retries returned the poisoned cached acknowledgment forever. Validate save identity/version against the immutable serialized request before caching. An identical retry can now retrieve a corrected receipt; edits made meanwhile remain dirty and navigation stays blocked. Existing optimistic concurrency and idempotency protocol retained. Native LanderWare storage remains the intended authority; no Enrollware dependency introduced.

## Exact intended files

- docs/admin/customer-interaction-client.mjs: validate save receipt before caching.
- tests/customer_interaction_checkpoint.test.mjs: three malformed receipt variants, exact retry envelope, retained newer text and blocked navigation.
- tests/customer_interaction_client.test.mjs: realistic ID/version for existing retry fixture.
- docs/admin/customer-interaction-studio.mjs: version imports to 20261013-recovery1.
- docs/admin/customer-learning.html: version Studio module URL; committed feature gate remains disabled.
- Codex_Reply_Issue371_Recovery_20261013_R1.md: this unique root receipt.

## Local verification

node --test tests/customer_interaction_client.test.mjs tests/customer_interaction_checkpoint.test.mjs
# tests 15
# pass 15
# fail 0

python tests/customer_interaction_studio_browser.py
Ran 5 tests in 11.374s
OK

node --check docs/admin/customer-interaction-client.mjs: exit 0
node --check docs/admin/customer-interaction-studio.mjs: exit 0
git diff --check: exit 0

Browser uses existing local Chromium/Playwright and synthetic intercepted API/auth; not real owner-session/Edge/database proof. No dependencies installed, generator or broad rebuild run. An initial local text-edit helper hit a Windows encoding error while updating asset URLs; rerun with explicit UTF-8 succeeded, final diff reviewed. Supabase skill reviewed; attempted current docs/changelog web reads were unavailable through the browser tool (unsupported markdown content type/inaccessible page). No Supabase API convention/schema/auth changes made. This fix uses repository-owned request/receipt semantics exercised through existing real handler tests.

## Preservation and release gates

Only six explicit files committed. Unrelated docs/Earl/index.html and docs/Jackson/index.html case-collision modifications remain unstaged in isolated worktree; original D:/E: dirty work untouched. No cleanup, reset, merge, force push, infrastructure/monitor/assignment changes or ops/handoff/next_task.md use. Queue titles scanned; no competing workstream started.

Locally persisted and intended changes pushed to named branch and existing PR branch; no merge, deployment, production DB/API write, origin expansion, UI exposure or gate enablement. PR #372 remains draft. Whole #371 is incomplete: atomic interruption/resume and durable follow-up/NEXT remain unwired; backup/restore evidence and real owner-session browser/API/database recovery proof remain absent. Separate explicit production GO remains mandatory after readiness gates, never inferred from Path A preparation authorization.

Persistent proof contract: success means a matching confirmed server checkpoint and recoverable stored notes. On-demand cadence; last synthetic browser verification is this run, last real owner/runtime/database end-to-end proof remains none. Missing/invalid receipts, retained unsaved text and conflicts are failure conditions. Local test runner catches this regression; deployed outcome observer and observer-health evidence remain absent. Recovery: retain draft/envelope, retry identical request, review explicit conflicts, reload confirmed records/export unsaved draft. Brian must not become routine monitoring layer; that integration remains unresolved.

Next action: continue SAME draft PR with atomic interruption/resume and durable follow-up/NEXT wiring, targeted browser/handler/database tests; obtain actual backup/recovery and genuine owner-session proof before requesting the separate production go/no-go. No owner action required for safe local continuation. Do not merge/deploy this PR. The E: broken repository is a local checkout limitation bypassed safely, not an excuse to alter it or stall backend work.
