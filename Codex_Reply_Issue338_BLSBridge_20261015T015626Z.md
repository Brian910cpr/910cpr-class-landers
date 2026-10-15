# Issue 338 BLS bridge dispatch receipt

Timestamp: 2026-10-15T01:56:26.7877559Z
Branch: codex/issue338-bls-bridge-20261014
Substantive commit: a0f5a0d487b2153b357872c9f82b001c47f1b108
Starting checkpoint: 4495474029c21f7c6f9c741f38e80cd19beaeb0d
Work-item state: BLOCKED for release; backend narrowing and controlled-source proof completed.
Persistent-system evidence: BUILT, locally validated. No current production end-to-end proof, monitoring or health claim.
Origin: https://github.com/Brian910cpr/910cpr-class-landers/issues/338
Execution acknowledgment: https://github.com/Brian910cpr/910cpr-class-landers/issues/338#issuecomment-6182480179

## Findings and work performed

Read the full issue body/comments and repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard. The latest owner disposition prohibits releasing the old broad branch. Preserved its checkpoint and all other assignments. Existing issue338 implementation PR search returned none; no duplicate PR created. Draft PR372 remains untouched, unmerged and undeployed.

Created isolated worktree E:/GitHub/910cpr-class-landers-issue338. Restored all non-BLS catalog/rule objects from exact GitHub main 8b6c598000410afb67c7915b3b7f0d321d7ae292. Only 209806, 359474 and 210549 retain approved changed definitions. Course209809 definition is unchanged from main. The apparent large catalog diff is incorporation of main's subsequent catalog additions into the October2 checkpoint, not new course invention. The JSON report records byte equality after canonical serialization for all 69 non-BLS catalog entries and 21 non-BLS consumption entries; this is object/serialized-entry equality, not a claim of whole-file byte equality.

Fixed occupancy's nested timing.inferred_scheduler_consumption_minutes handling; canonical consumption ends are not treated as teaching ends. Updated only three approved full-BLS fixture expectations (120 to150); did not rewrite unrelated fixtures. Kept source teaching timestamps unchanged.

Restricted the edge bridge to three approved BLS IDs and the exact existing public anchor lw-b48b53c7-df11-409f-a8f0-61b72a7f17e9. Its teaching end16:30 receives the reviewed occupied edge17:00 exactly once. This deliberately does not generalize compatibility to other Heartsaver sessions. Other courses and clear-day candidates use the incumbent grid/policy; no clinical free-day expansion. Finalizer runs incumbent policy for legacy candidates and independently revalidates attached edge identity, resource and current anchor geometry before the unchanged reconciliation/final publication gates. Offsite edges still reject. No roster/freshness/lead/URL/collision guard relaxation.

Preserved attached_to_session_id, blockEdge, schedulerConsumptionMinutes, setup/cleanup and duration/buffer provenance through compact publication. Public validator rejects missing/stale attachments and invalid geometry/provenance. Malformed edge timing fails closed. Approved BLS durations/buffers are checked exactly.

## Files changed intentionally

- data/config/course_catalog.json
- data/inventory/course_consumption_rules.json
- scripts/apply_anchor_policy.py
- scripts/block_start_time_selector.py
- scripts/build_bls_block_schedule_pilot.py
- scripts/public_block_edges.py
- scripts/validate_public_refresh_output.py
- tests/fixtures/enrollware_zero_duration_20260929.json
- tests/test_zero_duration_pipeline.py
- tests/test_issue338_bls_bridge.py
- data/audit/issue338_bls_bridge_20261014.json
- Codex_Reply_Issue338_BLSBridge_20261015T015626Z.md

## Controlled-source output and proof

Primary exact report: data/audit/issue338_bls_bridge_20261014.json. candidate_offers and final_offers contain exact course IDs, starts, consumption and attachments. This is synthetic/local dry-run evidence, not current public inventory.

One explicit availability block07:00-nextmidnight, existing HS209809 teaching14:00-16:30, occupancy through17:00. Six candidates:209806 and359474 each11:30/17:00 (150min);210549 at13:00/17:00 (60min). Family limit removes two later full-course alternatives. Final four dynamic offers:20980611:30,35947411:30,21054913:00,21054917:00. Separate combined-family finalizer/compact/validator fixture retains exactly one real HS occurrence at14:00 with its identical real booking URL. No booking submitted.

The real builder is invoked with controlled source adapters and actual conflict/qualification/lead-time/finalizer logic. Its URL lookup is a fixture stub, so this does not prove actual appointment container availability or live URL reachability. Tests separately cover missing attachment, changed edge, wrong course, missing block and blocked reconciliation dates. Geometry tests retain offsite, midnight, merged growth and holds. Zero-duration tests cover inferred versus explicit ends and occupied-window collision behavior.

## Validation

Targeted command:
python -B -m unittest tests.test_issue338_bls_bridge tests.test_public_block_edges tests.test_zero_duration_pipeline tests.test_canonical_scheduling_demand tests.test_apply_anchor_policy tests.test_native_public_anchor tests.test_validate_public_refresh_output tests.test_public_refresh_renewal tests.test_demand_publication
Result:69 tests passed.

Existing production workflow gate:
python -B -m unittest tests.test_zero_duration_pipeline tests.test_enrollware_ical_import tests.test_scheduling_reconciliation tests.test_canonical_scheduling_demand tests.test_apply_anchor_policy tests.test_anchor_state tests.test_publish_scheduling_landscape tests.test_native_public_anchor
Result:65 tests passed.

node --test tests/resolved_selector_availability.test.mjs
Result:27 passed,0 failed.

AST parsing passed for all seven changed/new Python files. Scoped git diff --check passed. Non-BLS equality assertions passed against GitHub main identified above. No sitewide generator or public-output rebuild ran; tests use temporary fixtures.

Additional suites are NOT green: tests.test_block_start_time_selector ran60 tests with108 failed assertions/subcases and18 errors. Observed errors include absent data/sessions_current.json; observed saved-page failures include removed Back to All Courses text and historical artifact expectations. These were not all baseline-reproduced, so no blanket baseline-debt claim. tests.test_refresh_admin_workflow has one unchanged checkpoint failure: test expects cron */30 while both HEAD workflow and current working file use7,17,27,37,47,57. A mistyped test_public_refresh_workflow module initially caused an import error; rerun used actual existing modules above.

## Exact release blockers

1. No fresh source replay: data/sessions_current.json and data/runtime/canonical_scheduling_demand.json are absent in the isolated worktree. The tracked data/audit/live_availability_snapshot_preview.json generated_at is2026-10-02T10:13:12.407045+00:00. HOT_SYNC_ADMIN_KEY is not present in this process environment. No credential value was printed. Existing local source caches elsewhere were not substituted as current authoritative truth.
2. Broad real-input/saved-output selector checks remain unpassed as detailed above. Owner gate says all required checks must pass before opening a PR or generating public output. No PR opened.
3. Current-main integration not proved: GitHub main is newer than the checkpoint; broad git fetch failed with bad object6e61cabca5981d1389e52c60d95424d9893bb50f and did not send all necessary objects. Exact config comparison used read-only GitHub Contents API instead. No reset, cleanup, rebase or destructive repository repair performed. The old branch must not be merged as-is.
4. October10 is historical at dispatch time. Fixture correctness cannot prove useful current customer-facing availability. No generalized production bridge or replacement of active V2 work was inferred from this old narrow authorization.

No new automatic approval rejection occurred. These are source/test/integration gates, not a renewed permission request. No source calendars, Enrollware, sessions, registrations, payments, infrastructure, secrets or production data were written.

## Persistence, deployment and unrelated work

Implementation and this reply are committed to the named branch and are to be pushed together; final UI/issue receipt records exact pushed tip and GitHub receipt verification. No merge, deployment, live refresh or public output generation. No ops/handoff/next_task.md used. No Codex_Read file created or renamed.

Original E:/GitHub/910cpr-class-landers dirty files/caches/replies and all existing worktrees remain preserved. Isolated checkout reports docs/Earl/index.html and docs/Jackson/index.html dirty; neither was intentionally edited or staged for this dispatch. Their cause was not diagnosed. No cleanup attempted. No private runtime data committed.

## Next concrete action and proof contract

Continue this same backend workstream from the substantive commit. Obtain an authorized fresh canonical/HOT_SYNC snapshot through the existing read-only credential/workflow path, retain sanitized provenance, and replay the real input pipeline in an isolated checkout based on exact current main. Review current V2/issue351 integration before selecting a production target; do not deploy an obsolete October2 full branch. Reproduce/resolve relevant real-builder failures without rewriting unrelated page fixtures. Only after required gates pass reuse an applicable existing PR or open the one scoped issue338 PR; PR372 stays draft and excluded.

Expected useful outcome: a current qualified customer sees legal BLS options around a real HS commitment, and the real class/booking is preserved. Success evidence must be current sources -> candidate/rejection trace -> validated compact feed -> actual rendered customer page and booking links, after production release. Last successful end-to-end proof for THIS bridge: none. Failure/staleness: unresolved source identity, stale/unknown reconciliation, missing provenance, collisions or unavailable current inputs. Observer for this dispatch is bounded Codex execution plus originating issue/repository receipt; durable production observer and observer-health proof are not established. Recovery is fresh authoritative replay and current-main review; account-level escalation is needed only if existing source access cannot be supplied by the authorized execution environment. Brian is not asserted to be relieved of routine monitoring.
