# Issue 334 — location provenance and cloud gate, R50

Timestamp: 2026-10-14T01:10:02.9736073Z
Branch: codex/issue334-provenance-20261014-r50
Inspected substantive commit: 47a10dc2d2c6853a9fe88e96f4fb7b485334b07e
State: BLOCKED (engineering trace completed; no production repair claimed)
Persistent evidence: prior publication PROVEN; overall HEALTHY not established.

## Findings and exact evidence

The latest owner issue history reports eight families with 189 input / 187 evaluated / 2 failed windows. Local committed docs/data/admin/scheduling_landscape.json reconciliationIssues[0:2] retain the missing directional rule:
4018 Shipyard Blvd, Room B, 910CPR Office->:: Wilmington; Shipyard Blvd - B
Both windows are November 3: 07:45–15:00 and 17:30–00:00 America/New_York. This does not explain October 14 omissions.

New source trace: docs/data/schedule_future.json sessions contains session_id lw-dfa08088-1266-4dd6-ad7d-14856b7f845a, canonical_session_id dfa08088-1266-4dd6-ad7d-14856b7f845a, course_id 359474, source landerware_event, location_name exactly the unresolved label above. No participant data retained here.

Authoritative data/config/location_resource_map.json declares Room B alias NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office, but not the native label. scripts/block_start_time_selector.py canonical occupancy consumes location_name and only marks location_resolution after normalize_location_resource succeeds. scripts/layered_selector_adapter.py preserves unresolved locations as offsite and requires explicit directional travel. The textual similarity alone is not authoritative canonical-location provenance. No guessed alias or travel duration was added.

Exact blocker: authoritative native Location/room relationship or approved alias evidence for this session is not present in the inspected committed map/source. Trace the canonical session's Location relationship in the existing #297 schedule-truth stream, then reuse that evidence for a narrow alias repair with conflict-preservation regression tests. Do not solve this with a guessed zero-minute travel rule.

Independent cloud recovery remains BLOCKED: GitHub GET actions/variables/AVAILABILITY_WATCHDOG_HEALTH_URL returns HTTP 404. Existing owner gate is secure provisioning of repository-restricted Actions read/write credential as encrypted GITHUB_ACTIONS_TOKEN; do not paste credentials in chat/issues. No activation retry made.

Latest natural canonical observer: run 38490975726, created 2026-10-14T00:34:46Z, completed failure. reconciliation-health failed at Notify existing issue 297 only when the condition changes; verify-demand, verify-production and verify-publication-watchdog skipped. This is new observer evidence, not sustained five-minute cadence proof. Investigate that failed notification step in #297 without weakening reconciliation gates. Last successful bounded public proof remains R49 at 2026-10-13T23:54:43Z; this dispatch made no new live-page claim.

## Work, validation, and preservation

Acknowledged execution on issue before implementation: issuecomment-6158593226.
Read repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard. Reviewed issue body/history and existing PRs. Queue sweep found existing backend streams assigned/gated; no independent safe quick win selected or competing stream started.

Local test command: python -m unittest tests.test_layered_location_aliases tests.test_layered_selector_adapter -q
Result: Ran 14 tests in 0.017s; OK. These validate existing behavior, not a deployed fix.
Only intended changed file: this repository-root receipt. No generator, application changes, merge or deployment. Draft PR #372 remains OPEN/draft and untouched. No new PR duplicates an existing implementation PR.

Original E:/GitHub/910cpr-class-landers dirty files/untracked receipts preserved. Fetch reports missing object 6e61cabca5981d1389e52c60d95424d9893bb50f and bad refs/remotes/origin/codex/group-training-experience. No cleanup/reset attempted. Isolated worktree E:/GitHub/910cpr-issue334-r50 created from available origin/main. Its checkout produced unrelated docs/Earl/index.html and docs/Jackson/index.html modifications; neither staged. Existing assignments preserved.

Push status: receipt committed and pushed on named branch; final pushed SHA recorded on originating issue and final response (avoids self-referential receipt hash).

## Recommended next action

Keep #334 open. Advance canonical Location provenance in existing #297 workstream; inspect latest observer notification failure. After authoritative relationship proof, implement the smallest alias/source normalization repair and verify final customer inventory. Cloud timer activation remains gated on secure account credential provisioning and authenticated health endpoint configuration. Local containment still requires CYBERPC awake/online/logged in; owner must not become routine monitoring layer.
