# Issue #238 — overnight selector

- Timestamp: 2026-10-14T21:41:00Z (UTC).
- Branch: codex/issue238-overnight-20261014.
- Implementation commit: e280182c971 (full identity available in branch history).
- Validated source tip before receipt: 85c1ffd4faa7373c5ab0512f89a165638c25d100.
- State: PR_OPEN; release BLOCKED. Draft PR https://github.com/Brian910cpr/910cpr-class-landers/pull/396.
- Evidence level: BUILT. No end-to-end production proof; not PROVEN, MONITORED or HEALTHY.

## Findings and work

Read full #238 (no original comments), checkout AGENTS.md, current main AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Acknowledged actual execution on originating issue before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/238#issuecomment-6179056260.

Inverse availability expansion constructs separate daily intervals and subtracts blockers from them independently. This makes midnight an artificial duration boundary even across adjacent covered days. Targeted change joins only exactly adjacent open intervals before subtracting real blocking events. Daily clock closures, unavailable container dates and horizon ends remain boundaries. No clock policy, lead-time rule, qualifications, course IDs, travel rules, resource conflicts or publication guards changed. Existing downstream explicit cross-midnight datetime regression already exists in tests/test_generate_dynamic_offers.py.

Regression demonstrates real blocking events leaving July 1 23:30 through July 2 01:30: the continuous gap now survives a 90-minute minimum. Separate regression preserves 08:00–19:00 daily closure. This is synthetic local evidence, not a real public booking proof.

Files intentionally changed:
- scripts/build_live_availability_snapshot.py
- tests/test_build_live_availability_snapshot.py
- Codex_Reply_Issue238_Overnight_20261014T214100Z.md

No generator ran; input/offer/rejection totals from a production rebuild therefore do not exist. No generated public artifacts were staged.

## Validation and live evidence

Local command: python -m unittest tests.test_build_live_availability_snapshot tests.test_layered_selector_adapter -q
Result: Ran 33 tests in 0.030s; OK.
Syntax: python -m py_compile scripts/build_live_availability_snapshot.py tests/test_build_live_availability_snapshot.py passed.
Diff whitespace warning was corrected in 85c1ffd4faa7373c5ab0512f89a165638c25d100.

Broader initial command included tests.test_generate_dynamic_offers and tests.test_block_start_time_selector: 105 executions, 27 failures and 21 errors. One error was a new test calling the wrong entry point; corrected before focused passing validation. Remaining broad failures are not resolved or claimed all baseline-proven. Concrete selector blocker: Required real input is missing: E:\GitHub\910cpr-issue238-20261014\data\sessions_current.json. Other failures include empty dynamic-offer expectations and renderer assertions. Do not interpret focused green tests as whole-selector release readiness.

Read-only public HTTP fetches verified BLS, Heartsaver, ACLS and PALS HTML plus their referenced /data/block-selector-availability/<family>.json endpoints. Observed 2026-10-14T21:39:54.840572Z:
- BLS: 3577 course offers; 0 with start clock plus schedulerConsumptionMinutes >1440.
- Heartsaver: 7470 offers; 0 cross-midnight.
- ACLS: 3 offers; 0 cross-midnight.
- PALS: 2 offers; 0 cross-midnight.

Feeds use selector-resolved-availability.v1. Earlier same-session fetch: BLS generatedAt 2026-10-14T17:35:32.825228-04:00; validUntil 2026-10-14T17:50:31.699213-04:00. Heartsaver generatedAt 17:35:38.958128-04:00 with same validUntil. Clinical feeds contain direct seated classes; their immediate validUntil is not evidence that those direct classes expire.
Latest inspected Refresh admin availability run 38640850718 succeeded; Pages build/deployment 38641526020 succeeded. No account-level HOT_SYNC failure established by these checks. No registrations clicked or submitted. JSON and HTML fetched, but interactive browser overnight behavior remains unproven.

## Safety, dependencies and exact blocker

Original E:\GitHub\910cpr-class-landers dirty work remains untouched. Used isolated named worktree E:\GitHub\910cpr-issue238-20261014 from origin/main 47a10dc2d2c6853a9fe88e96f4fb7b485334b07e. Initial shared-repository fetch reported unreadable object 6e61cabca5981d1389e52c60d95424d9893bb50f; branch checkout and push succeeded. No repair/reset/cleanup attempted.

Checkout/test side effects and existing work remain unstaged: docs/Earl/index.html, docs/Jackson/index.html and tracked Python cache changes. No blanket staging. Do not delete those as part of this task.

Reviewed queue and existing scheduling PRs. Reused current implementation patterns; no competing scheduler rewrite. #351 and #342 document later doctrine and active V2 work. Existing PR #383 remains the V2 implementation stream; its body limits it to review/validation and its prior source validation documents clinical suppression gates. No changes to it, draft #372, or existing assignments. No unrelated backend change was selected: current items require their own dependency/context validation and were not demonstrably safe quick wins in this dispatch.

Exact release blocker: isolated checkout lacks data/sessions_current.json needed by build_block_schedule_page, and no authenticated real-source generated selector plus actual live overnight example has been proven. Do not merge a scheduling change on synthetic gap tests alone. Missing local input is a runtime-data prerequisite, not established credential denial or an owner decision. No production write attempted.

## Next action / proof contract

Continue #238 using PR #396, do not create another competing implementation. Obtain current canonical runtime inputs through the existing authorized read-only freshness pipeline; reproduce a real cross-midnight free interval with the complete next real blocker, instructor and room coverage, course consumption, appointmentDayId/course/start URL and 24-hour lead evidence. Trace the interval through inverse snapshot, generated offers and rendered selector. Check whether contiguous explicit windows also need provenance-safe combination; this patch covers inverse expansion only. Before any targeted generator, report exact command/output scope and get approval if sitewide; retain input/block/offer/rejection counts. Resolve broader failures proportionately before release. Then merge/deploy only within applicable release gates and verify actual customer choices and matching assets. Do not merge/deploy PR #372.

Success evidence: real current source availability -> legal cross-midnight offer -> rendered usable choice with correct registration URL; next actual blocker rejects conflicts. Last successful end-to-end overnight proof: none in this dispatch. Cadence: existing publication 15-minute validity window; observer: existing refresh and deployment workflows, inspected once. Observer health beyond those successful runs is unproven. Recovery: restore authorized runtime inputs, validate exact PR head, then use existing release path. Escalation: only if pipeline reports an actual account/permission failure; no owner-level action currently established. Brian is not assigned routine monitoring in this receipt.

Locally persisted and pushed source; draft PR open. Not merged, not deployed. Receipt is a separate communication commit; its pushed tip SHA is reported in the originating issue and final response.
