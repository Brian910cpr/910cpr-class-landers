# Issue 367 — bounded backend contract validation, round 3

- Assignment: Brian910cpr/910cpr-class-landers#367.
- Timestamp: 2026-10-11 (UTC); exact commit time is recorded in Git.
- State: BLOCKED for complete checkout-family implementation; existing PR #379 stays draft.
- Review branch: codex/issue367-backend-proof-20261011-r3.
- Existing PR branch reused for delivery: codex/issue367-preflight-20261010.
- Baseline commit SHA: a85e09a34d5df72fa8c874f5b2d8d3637679758f. Receipt commit is the pushed branch tip reported in the issue checkpoint and launcher response (avoids a self-referential SHA).

## Exact blocker and authority

The latest #367 owner disposition says: "After the single deep-stream allocation is explicitly transferred from #371/#372 to #367, reuse #379". No subsequent transfer appears in the full issue conversation read for this dispatch. #371's latest owner decision explicitly continues its existing assignment/PR372 with local CyberPC staging and says not to create another deep workstream. #116 caps active implementation streams at one. The dispatch likewise preserves one deep stream/all assignments and prohibits merging/deploying #372. Therefore this dispatch does not implement the checkout-family overhaul or the gated native-routing repair. This is an allocation/authorization gate, not a missing credential.

Execution was acknowledged before implementation at:
https://github.com/Brian910cpr/910cpr-class-landers/issues/367#issuecomment-6105804260

## Work performed

Read full #367 body/comments; repository AGENTS.md; current CODEX_HANDOFF_PROTOCOL.md; LANDERWARE_DESIGN_ETHOS.md; LANDERWARE_PROOF_AND_HEALTH_STANDARD.md; #116 and #371 owner decisions; current #372/#379 state. Swept open CODEX issue titles for eligible independent work. No additional deep/backend implementation was selected because it would require further scope/dependency discovery and risk competing with existing assignments. Continued safe local backend validation within this assignment instead.

Created a named isolated review worktree from current #379 head at E:/GitHub/910cpr-issue367-backend-proof-20261011-r3. Did not alter original checkout, clean/reset/rebase, regenerate pages, install dependencies, change assignments or touch the retired mailbox.

Ran the existing Heartsaver registration backend contract suite not reported in the prior routing receipt. These assertions check shared registration profiles, requirement/document linkage, payer modes, RPC signatures, structured selected options, lifecycle linkage and HTTP replay safeguards. They read existing source; they do not execute a database, Stripe payment or webhook.

## Exact checks and outputs

Command: python -B -m unittest discover -s tests -p test_heartsaver_skills_registration.py -v

Result:
    Ran 13 tests in 0.001s
    OK

Command: python -B -c "import ast,pathlib; p=pathlib.Path('tests/test_heartsaver_skills_registration.py'); ast.parse(p.read_text(encoding='utf-8')); print('Python syntax: PASS')"

Result: Python syntax: PASS

Command: git diff --check
Result: exit 0, no output before receipt creation. Repeated for staged receipt before commit.

Relevant exact source/test paths:
- tests/test_heartsaver_skills_registration.py
- supabase/migrations/20260827220000_landerware_unified_registration.sql
- supabase/functions/landerware-registration/index.ts
- supabase/functions/maxim-portal/index.ts
- docs/register/heartsaver-skills/index.html

## Existing failure and evidence limits

Reused prior owner-accepted routing diagnosis instead of rerunning unchanged checks:
- tests/test_public_registration.py: prior 10 pass / 1 failing BLS native-routing assertion.
- docs/bls.html:1671 and scripts/build_bls_block_schedule_pilot.py:2223 route directly to course.appointmentUrl without the expected conditional native session registration URL.
- Historical exact receipt: Codex_Read_Issue367_RoutingGate_R2_20261011T042737Z_R1.md on PR379 baseline.

The failing assertion was not weakened. Canonical eligibility was not bypassed. No assumption is made about current canonical BLS session identities.

Persistent-system evidence: existing narrow implementation is BUILT only for purposes of this dispatch; full #367 is incomplete. No new CONNECTED/PROVEN/MONITORED/HEALTHY claim. Last successful complete #367 end-to-end proof: none established. Expected proof remains family selection -> canonical eligible session -> native order/Stripe payment -> webhook -> correct session/person/product/fulfillment records. Observer health and live failure/staleness coverage were not evaluated; contract tests are not an operational monitor.

## Files, preservation and delivery

Only intended changed file: Codex_Reply_Issue367_BackendProof_20261011_R3.md.

Original E:/GitHub/910cpr-class-landers dirty work preserved: docs/Earl/index.html; docs/data/admin/scheduling_landscape.json; tracked scripts/__pycache__ files; untracked ops/handoff/codex_heartbeat.json, additional scripts/tests bytecode and supabase/.temp/. No secret contents read or copied.

The earlier validation checkout has unrelated docs/Earl/index.html and docs/Jackson/index.html modifications. The new isolated worktree also showed these two unrelated files modified after checkout/checks; neither was edited by this dispatch or staged. They remain uncommitted and untouched. Explicit-file staging only.

Local validation: 13 backend source-contract tests and Python syntax passed. Push: receipt committed and pushed to existing PR379 branch, GitHub Contents API verification required before exit. Merge: none. Deployment: none. PR372 untouched. No browser/render/payment/webhook proof. No production database, auth, origin or scheduling changes.

## Next action

Supervisor/owner must explicitly transfer the single deep-stream allocation to #367 before implementation resumes. Then continue existing PR379, verify canonical BLS session eligibility/identities, repair the generator and smallest affected output, preserve fail-closed tests, and complete the entire issue family/manual/cross-sell/fulfillment acceptance matrix plus desktop/mobile and payment/webhook proof before considering authorized production delivery. Preserve manual eCode fulfillment metadata. No Brian credential action required for this local validation slice.
