# #297 canonical reconciliation continuation / #157 PR #197

Repository: Brian910cpr/910cpr-class-landers. Branch: codex/issue-157-runtime-projection. Observable task model: gpt-6-astra, xhigh. No other active coding owner found. Main baseline: 616832dec7cef34b0e4928d90fe74a7d480259ab. Prior R3 receipt at 20dc2b1684c832eb6a51d4cbbee59286a7aff57a remains immutable.

## Actual source and repair

The existing historical importer deliberately produces historical Sessions; the CSV registration-event importer was report-only. Neither established complete current roster coverage. The operational mode now extends that importer into the same class_sessions, customers, registrations, ingest_jobs, ingest_facts and ingest_review_queue. It does not create a second schedule database or change Enrollware bookings.

The service-only, SECURITY INVOKER RPC resolves exact external class and registration IDs, uses existing canonical entity keys, preserves native authority, records prior relationships, reconciles reschedules and complete-roster absence, and quarantines failed classes atomically. Historical mode remains intact. Existing gmail_enrollware/enrollware_owner_reconciliation relationships are accepted only when their exact IDs are reverified against the current roster, not because an old notice exists. Their existing provenance is retained.

The shared owner/demand projection checks complete roster evidence, source timestamp (60 minutes maximum), exact active external registration-ID membership, and canonical active statuses. Missing, partial, failed, stale and mismatched reconciliation yield null/unknown; a fresh database GET cannot renew source time. Owner rosters are withheld when stale. Newer incomplete imports invalidate old proof. Source replay does not renew its watermark. The endpoint projection includes no participant PII or registration identities.

## Production source comparison

Authenticated source observed 2026-09-27 03:46:19–03:47:32 UTC. All displayed roster entries were captured and matched to independent class-list totals; every displayed registration's status was inspected. Browser Student Export download and tab export were unavailable; authenticated live class/registration pages supplied the authority. Private evidence is retained outside Git in the task work directory. No export or PII was committed.

| Date ET | External class | Class number | Current source / canonical count |
| --- | --- | --- | --- |
| Sep 26, 09:00 | 14186375 | 51479 | 3 / 3 |
| Sep 26, 10:00 | 14145607 | 51468 | 0 / 0 |
| Sep 26, 17:00 | 14184955 | 51476 | 2 / 2 |
| Sep 27, 13:00 | 14361098 | 51485 | 1 / 1 |
| Sep 27, 18:30 | 14421081 | 51495 | 1 / 1 |

The live September 26 identities differ from historical notices: a registration formerly reported at 10 AM is now on the 9 AM roster, and an older notified identity is absent. Current relationships, not notice totals, were reconciled. Exact IDs and customer name/email comparisons passed for all 18 source registrations in the 34 reconciled classes. Two registrations in the quarantined TBD class remain unpromoted, explicitly unknown.

The future audit covers all 35 classes shown by Enrollware's unfiltered Upcoming Classes list. 31 now reconcile to canonical Sessions. Four remain quarantined: 13895152/13895154/13895155 use an existing inactive Brunswick Oral location; 11341058 uses inactive ___TBD___, midnight, and no explicit end time. No location authority was weakened to admit them. Their evidence and review requests are durable in the existing ingest tables and returned by the protected owner response. The September 29 class 13963994 retained both original canonical registration IDs after exact source verification.

Source zero/equal start/end times do not establish duration. Effective windows use the existing explicit course consumption rules (120-minute Renewal, 60-minute HeartCode, 150-minute Heartsaver First Aid, 120-minute CPR AED), with the raw source end/hour values and duration basis preserved. Valid explicit source end times are retained; consumption remains at least the existing course reservation minimum. This does not promote a new Course Master or alter ranking, conflicts, lead time or availability.

## Verification and deployment

51 focused Python tests pass (43 original Anchor/runtime/publication/clock + 5 complete-roster/alarm contract tests + 3 consumption-time watermark tests). 17 actual TypeScript endpoint/projection tests pass. An isolated real PostgreSQL (PGlite 0.5.8, pinned test-only dependency) lifecycle test verifies empty→registered→replay→reschedule→absence, identity preservation, legacy-source evidence, partial/stale/status rejection, quarantine and service-only access. Production state-changing reconciliation used only the current authoritative source; synthetic lifecycle changes were isolated locally.

Five migrations applied successfully. The exact-location probe in migration 20260927041952 remained blocked by the existing database location-authority trigger and created no records; migration 20260927042118 restores the early importer guard. The isolated schema now includes that production trigger. No location was activated or policy bypassed. Demand endpoint version 2 and protected canonical-session-workspace version 7 deployed; the previous owner bundle exactly matched committed main before deployment. Security advisors are unchanged from the pre-change baseline. Public HTML has not yet been deployed by this continuation. Exact bundle hashes and PII-free SQL/source comparisons are in data/audit/issue297_canonical_reconciliation_proof.json.

The existing verify-canonical-participants workflow gains a half-hourly health check. It compares protected reconciliation health with public committed-class discovery, detects missing Sessions/relationships and stale evidence, and posts condition changes to existing issue #297. It creates no issue. A failed protected query fails the observer rather than returning green. Scheduled execution requires merge; an unrun cron definition is not MONITORED proof.

## Boundaries and remaining work

The current authoritative access is an authenticated Enrollware browser session. No unattended roster-export credential/event-completeness feed was found in the existing repository/GitHub secrets. This patch accepts such snapshots through the existing importer and automatically exposes staleness; it does not claim continuous Enrollware synchronization from iCal or Gmail. Without another verified snapshot, these source proofs expire after 60 minutes. Brian is not represented as a functioning automatic source collector.

The existing R3 receipt has been read with its source/tests and its former #297 coverage blocker is now cleared for every incident class. Its explicit review-before-merge instruction still applies; no Codex_Read acknowledgement is manufactured. Continue authenticated endpoint→runtime→Anchor publication proof, normal review/merge, production publication, actual public selector verification and a subsequent scheduled refresh. Stage 6 remains gated.

Enrollware's native appointment checkout, bookmarked/direct appointment URLs and administrator registration remain outside LanderWare's selector enforcement. The two September 27 customers' navigation channels remain unproven. Renewal was booked first (Sep 24 19:26 ET); HeartCode later (Sep 26 15:59 ET). Reconciliation observes those bookings without moving them.

## Continuation verification and accepted review

Protected production demand verification run 36293682090 passed: 35 returned canonical sessions, all counts known within the source watermark, OPTIONS 204, anonymous 401, repeated content identical. Protected owner verification 36293683574 passed. Observer 36293684917 correctly failed and notified existing #297 for the four inactive-location gaps.

The real runtime applied to all eight copied main selectors matches all 31 public occurrences, produces 12 Anchors and retains identical Anchor content on repeat. Both Sunday incident classes have one registration and promotion_reason canonical_active_registration. Actual iCal ingestion read 269 records, marked 234 unavailable for direct booking, and the BLS candidate path used 203 availability blocks. At 00:24 Eastern it generated 8,588 candidates and resolved 8,102 offers across 90 dates; top reasons: insufficient contiguous time 1,589, calendar block 984, class collision 262, lead time 144, already started 15 (reasons overlap). Today has the two already-committed incident classes and no new dynamic offer inside the 24-hour window. See issue297_anchor_connection_proof.json and issue297_candidate_publication_proof.json. These are isolated dry-runs, not public deployment.

All 38 source class rosters were re-read 04:25:29.547–04:26:07.011 UTC with unchanged fields/membership; all 20 registration statuses were re-read by 04:26:46 UTC and unchanged. Conservative common source watermark 04:25:29.547 UTC, source SHA256 22f7abab31d51343a7e6f84f936c10cf47b055f620d41ac9ced88520b7eb76cb, ingest job df4c3f85-cd02-4e2c-a425-2708d439a2aa: 34 reconciled, same 4 quarantined. No booking changes.

Brian explicitly accepted the immutable R3 receipt and approved normal merge/publication in this task: "Accept R3; approve normal publication". Approval included the existing full publisher's possible 1,334 tracked docs files plus two publication hashes, after final checks. No Codex_Read file was manufactured. The source freshness test additionally prevents a fresh database GET/cache from extending an external roster watermark during publication.
