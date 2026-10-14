# Issue 334 — provenance dispatch R55

Timestamp: 2026-10-14T06:40:00Z (UTC)
Branch: codex/issue334-provenance-20261014-r55
Inspected base commit: 2751c1046f44d736aa1082e965d6482f0a776b52 (previous isolated R54; not current main).
Commit: communication-only receipt commit; full pushed tip recorded on issue and in final response (avoids self-reference).
State: BLOCKED. Diagnostic work validated locally; no application change or deployment.
Execution acknowledgement: https://github.com/Brian910cpr/910cpr-class-landers/issues/334#issuecomment-6162504359

## Findings and exact next diagnostic

Prior accepted link/native-page repairs preserved. Known two failed November 3 windows remain dependent on authoritative location provenance for canonical session dfa08088-1266-4dd6-ad7d-14856b7f845a / course 359474. No location alias or directional travel duration inferred from similar text.

New bounded source trace:
- supabase/functions/canonical-scheduling-demand/index.ts:57 projects location_id from the session row.
- Line 58 projects location_name as row.source_location_label || row.locations?.name || null. A source label therefore takes precedence over the joined canonical Location name.
- loadDemand selects location_id, source_location_label and locations!class_sessions_location_id_fkey(name), lines 81–84.
- scripts/canonical_scheduling_demand.py:132 carries location_name into the added native public occurrence; that object does not carry location_id.

FACT: a public occurrence lacking location_id does not prove the canonical session has no Location foreign key. LIMITATION: this source review does not establish the affected row's actual location_id, joined name, room/resource relationship, or the currently deployed endpoint version. Do not change label precedence globally or add a guessed alias based on this finding.

Exact next action in existing #297 schedule-truth stream: obtain an authenticated, read-only result for the exact session's location_id, source_location_label, joined Location name, and authoritative room/resource relationship. Compare those fields with canonical-demand output and the existing resource map; normalize only the proven identity, then run occupied-window/directional-conflict tests and verify the affected rendered inventory. Preserve raw source provenance.

Local data/config/location_resource_map.json has no exact native label '4018 Shipyard Blvd, Room B, 910CPR Office'. rg -l --fixed-strings over data/config, scripts and tests found no match. Current GitHub map blob SHA: 61d3ce54f297aef33eb6148742090445edac91b9. No authenticated row/room proof acquired in this dispatch; canonical relationship remains the blocker.

## Current remote component evidence

GET actions/variables/AVAILABILITY_WATCHDOG_HEALTH_URL returned HTTP404 / Not Found. Existing owner-directed provisioning boundary remains: repository-restricted Actions read/write credential stored only as encrypted Cloudflare GITHUB_ACTIONS_TOKEN, then authenticated health URL configuration and independent recovery proof. No secret read, activation retry or new monitor.

Natural public-booking observer history sampled:
- 38514856448, schedule, 2026-10-14T05:06:20Z, failure.
- 38489856064, schedule, 2026-10-14T00:23:01Z, failure.
- 38469671908, schedule, 2026-10-13T21:19:05Z, success.

Prior original failed observation retained at data/audit/issue334_observer_r54.json. No new live/customer-browser proof claimed. Component sample: admin38522655744 (06:30:54Z) and Pages38523094642 (06:35:22Z) succeeded; admin38523145959 running. These do not prove continuous public validity. GitHub main sampled f5c35d2c6869a5f410bacfdea0f922357c254980.

Persistent evidence: prior publication PROVEN; overall HEALTHY unestablished. Expected outcome: continuously legal selectable public bookings; local timer five-minute cadence, effective source lease can be15minutes. Failure: expired feed, failed/unevaluated windows or stale observer. Observer: scheduled public-booking audit; multi-hour gaps and current failure prevent trustworthy coverage. Independent cloud observer blocked by missing health URL/secure credential gate. Local containment still requires CYBERPC awake/online/logged in; Brian must not become routine monitoring. Recovery: proven identity normalization plus bounded conflict/render proof, secure independent provisioning, then natural independent timer/publication/recovery observation. No duplicate alert while unchanged gates persist.

## Validation and scope

python -B -m unittest tests.test_layered_location_aliases tests.test_layered_selector_adapter -q
Ran 14 tests in 0.022s; OK.
No source syntax changes; receipt whitespace checked with git diff --cached --check before commit.
Known unrelated state: original E:/GitHub/910cpr-class-landers remains dirty and on its existing assignment branch. Prior Git object corruption not repaired. This separate worktree inherits existing Windows case-collision modifications to docs/Earl/index.html and docs/Jackson/index.html; neither staged. No generator ran.

Queue and open-PR sweep performed. #297 remains acquisition/reconciliation gated; #383 scheduling, #387 checkout, #389 document validation, #388 finance and #381/#375 preflight are existing assigned streams. Broader catalog/fleet/archive work is not an independent narrow safe quick win for this blocked dispatch; no competing implementation or duplicate PR started. Draft #372 confirmed OPEN/isDraft=true, untouched. No merge, deployment, booking/payment mutation, infrastructure change or ops/handoff/next_task.md use.

Exact changed file: Codex_Reply_Issue334_Provenance_20261014_R55.md only. Persisted locally, committed, pushed, and GitHub Contents verification required before exit. No temporary evidence or unrelated files committed.

ChatGPT next action: keep #334 open, use the exact canonical Location/room read above in the existing truth stream, preserve fail-closed travel/conflict gates, then prove normalization at affected customer output. Existing account-level secure cloud provisioning action remains unchanged; no new approval request or duplicate owner notification.
