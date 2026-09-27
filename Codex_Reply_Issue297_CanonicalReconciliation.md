# Codex Reply: #297 canonical reconciliation; #157 direct prerequisite

Timestamp: 2026-09-27T04:29:00Z / 00:29 EDT.
Branch: codex/issue-157-runtime-projection. Existing PR: #197.
Substantive commits: 3d5f4e0f95ca961f9f90b2331dcaf47f8c78b745 and 1cd4e16bf43c2a5102db1460d2d13c5306beedde.
Work-item state: PR_OPEN / rollout in progress. Prior receipts preserved.

## Result and evidence levels

- BUILT: existing registration importer now supports complete operational roster reconciliation into canonical class_sessions/customers/registrations, with ingest provenance, exact external IDs, deduplication, reschedule/absence handling, and per-class atomic quarantine.
- CONNECTED: real authenticated Enrollware source -> canonical database -> protected endpoint -> runtime -> Anchor/selector dry-run is connected for every incident class and all 31 current public occurrences.
- PROVEN: authoritative source comparisons and real backend reads pass for 34/38 source classes (31/35 future). Isolated PostgreSQL and weekday/Saturday/Sunday lifecycle proofs pass. Whole persistent system is not yet PROVEN or HEALTHY: four location-policy gaps and the unattended current-roster source dependency remain.
- MERGED: not yet at this immutable receipt timestamp.
- DEPLOYED: five database migrations; canonical-scheduling-demand v2, canonical-session-workspace v7. Public repair not yet deployed.
- LIVE-VERIFIED: protected backend yes; public repair awaits merge, publication, browser verification and a later scheduled refresh.

## Actual source and identity proof

Authenticated Enrollware complete class rosters plus each registration's current status supplied authority. Notices were not used to infer counts. September 26 classes 14186375/14145607/14184955 compare 3/0/2 source and canonical; September 27 Renewal 14361098/51485 and HeartCode 14421081/51495 compare 1/1 each. All 18 reconciled registration identities match exact external class and registration IDs and source customer name/email. Two registrations on the quarantined TBD class remain explicitly unpromoted/unknown.

First observations: 03:46:19–03:47:32 UTC. All 38 rosters were re-read 04:25:29.547–04:26:07.011 UTC, unchanged. All 20 source registration statuses were re-read by 04:26:46 UTC, unchanged. The conservative common refreshed watermark is 04:25:29.547 UTC, SHA256 22f7abab31d51343a7e6f84f936c10cf47b055f620d41ac9ced88520b7eb76cb, ingest job df4c3f85-cd02-4e2c-a425-2708d439a2aa. Canonical IDs survive refresh.

Exact evidence: data/audit/issue297_canonical_reconciliation_proof.json. Source and implementation report: data/audit/issue297_canonical_reconciliation.md. Private source snapshots remain outside Git in the task work directory. No participant PII or registration IDs were added to public JSON or receipts. No Enrollware booking was modified; synthetic changes occurred only in isolated tests.

## Tests and real publication dry-run

`python -m unittest tests.test_anchor_state tests.test_apply_anchor_policy tests.test_canonical_scheduling_demand tests.test_fetch_canonical_scheduling_demand tests.test_demand_publication tests.test_selector_clock tests.test_enrollware_roster_reconciliation`: 51 passed.

`node --test tests/canonical_demand_endpoint.test.cjs tests/enrollware_roster_proof.test.cjs`: 17 passed against actual TypeScript source. `node --test tests/reconciliation/reconcile.test.mjs`: 1 real PostgreSQL lifecycle scenario with multiple assertions passed, including the production location-authority trigger. Syntax checks and git diff --check passed. Security advisor findings unchanged (observation timestamps excluded).

Protected runs: 36293682090 demand PASS (35 known rows, repeated content equal, OPTIONS 204, anonymous 401); 36293683574 owner PASS; 36293684917 observer correctly FAIL and posts only to existing #297 for four gaps. An observer failure is not described as overall green.

All eight copied public selectors plus main schedule/admin projections: 31/31 public occurrences match, 12 Anchors, zero unknown public occurrences, identical Anchor content on repeat; four unmatched native/manual canonical rows are distinct from the four missing external sessions. Both incident classes promote with canonical_active_registration. Actual iCal importer and BLS candidate generator: 269 source records, 234 unavailable for direct booking, 203 availability blocks, 8,588 candidates -> 8,102 final offers over 90 dates. Rejections overlap: 1,589 insufficient duration, 984 calendar blocks, 262 class collisions, 144 inside lead time, 15 already started. Eastern reference 2026-09-27T00:24:28. Existing incident classes remain bookable; no new dynamic offer inside 24 hours. Evidence: data/audit/issue297_anchor_connection_proof.json and data/audit/issue297_candidate_publication_proof.json. These are scratch dry-runs, not public deployment.

The prior broader selector suite's same 14 failures/18 errors in 60 tests on main and R3 are documented in the immutable R3 evidence. No unrelated selector repair was added.

## Remaining boundaries and recovery

Classes 13895152/13895154/13895155 resolve to inactive Brunswick Oral location; 11341058 to inactive ___TBD___ with a midnight source time. The exact-ID import still hits the existing database error `operational sessions require an active/schedulable location`. No location was activated and no trigger bypassed. The early guard was restored after this diagnostic; both applied migrations remain in history. Smallest owner action: approve the correct active canonical location mapping for Brunswick commitments and resolve the actual schedule/location of the TBD class. Current evidence remains in ingest_facts/review_queue and the owner projection as unknown.

Freshness is 60 minutes from authoritative source observation; fetching the database cannot renew it. Both endpoint and runtime consumer demote expired/missing external proof to null/unknown. Source replay cannot renew timestamps. The existing half-hourly workflow detects missing canonical sessions, unmatched registration evidence and stale proof, posts deduplicated condition changes on #297, and fails on protected-query failure. Cron activation and later observer health require merge/observation; a configuration is not proof that a monitor runs.

No unattended authorized complete-roster export/event-completeness feed was found. Current source access is the authenticated browser. The precise remaining infrastructure action is to supply/authorize a current complete source to the existing importer, not another scheduling architecture or notice-derived count. Without it, counts correctly become unknown when proof expires; Brian is not represented as an automatic collector.

Native Enrollware appointment checkout, direct/bookmarked links and administrator registration bypass LanderWare's selector policy. Incident navigation channels remain unproven. Renewal was first: Sep 24 19:26 ET; HeartCode later: Sep 26 15:59 ET.

## Review and next action

Brian explicitly answered `Accept R3; approve normal publication` in this task after the immutable R3 receipt, commit and actual demand proof were presented. Approval included the existing full publication command and possible 1,334 tracked docs files plus two state hashes. No Codex_Read acknowledgement was manufactured. Continue PR197 final checks, normal merge and production deployment, actual public HTML/assets/selector verification, then a subsequent scheduled refresh. Keep #297 and Stage 6 gated where the above source/identity requirements remain unresolved.

Important changed source/config/test paths: scripts/enrollware_roster_reconciliation.py; scripts/import_enrollware_registration_events.py; scripts/audit_enrollware_reconciliation.py; scripts/fetch_canonical_scheduling_demand.py; supabase/functions/_shared/external-roster-proof.ts; supabase/functions/_shared/scheduling-clock.ts; supabase/functions/canonical-scheduling-demand/index.ts; supabase/functions/canonical-session-workspace/index.ts; .github/workflows/verify-canonical-participants.yml; .github/workflows/anchor-policy-ci.yml; tests/enrollware_roster_proof.test.cjs; tests/helpers/canonical_demand_endpoint.cjs; tests/test_enrollware_roster_reconciliation.py; tests/test_fetch_canonical_scheduling_demand.py; tests/reconciliation/{schema.sql,reconcile.test.mjs,package.json,package-lock.json,.gitignore}; supabase/migrations/20260927034822_reconcile_operational_enrollware_rosters.sql; 20260927040638_reconcile_verified_enrollware_legacy_sources.sql; 20260927040949_invalidate_incomplete_roster_proof.sql; 20260927041952_preserve_committed_external_location_identity.sql; 20260927042118_retain_existing_operational_location_gate.sql (all under supabase/migrations).
