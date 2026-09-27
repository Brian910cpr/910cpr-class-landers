# Codex Reply: #297 complete instructional coverage and reviewed deadline

Timestamp: 2026-09-27T05:23:00Z / 01:23 EDT.
Repository: Brian910cpr/910cpr-class-landers.
Receipt branch: codex/issue-297-classification-receipt, based on main 0a19a51dd41d1d914316c76c85fe59484a94a5e7.
Substantive commits: bd1e396b6cd98d15ec3306e08c3f190cc25386b9 and ee8d4abd6731e1a58ff828c807137e8c09ff3d4d.
PR301 merged normally at 05:20:50 UTC as 0a19a51dd41d1d914316c76c85fe59484a94a5e7 after all checks passed.
Work-item state: MERGED / database DEPLOYED / production projection VERIFIED. Continuous source ingestion and an actual subsequent scheduled publication remain unproven.

## Owner decisions resolved the remaining class classification

Brian approved 4018 Shipyard Blvd, Wilmington, NC and explicitly answered `Renewal deadline / placeholder` for external class 11341058. It is not a December 1 midnight instructional class. The prior R2 receipt's unanswered TBD business decision is therefore resolved, not silently ignored.

The existing private ingest review queue now records this owner decision, exact source identity and approved canonical location key 910cpr-office-shipyard. The importer preserves the full private source evidence and its two renewal registrations without fabricating an operational class_session or instructional Registration relationship. The health projection labels this source classified_non_session / renewal_deadline; its counts are not represented as zero students. No Enrollware booking was moved, canceled or edited by this task.

The final authenticated read-only refresh observed all 38 source rosters from 05:14:50.570 through 05:15:29.871 UTC and all 20 individual statuses by 05:17:41.245 UTC. Membership and statuses were unchanged. One real source field changed: the deadline's Enrollware location became 247652, Shipyard Room A, replacing 109182 ___TBD___. This task performed no Enrollware write. The change matches Brian's approved Shipyard location and unchanged renewal-deadline classification.

A focused edge-case repair ensures that a changed previously classified deadline is quarantined before operational promotion even when its new location is active. The actual new source initially returned non_session_source_changed_requires_review. Its prior review decisions were retained as superseded, and the new exact source identity was reviewed using Brian's current instructions; decision id 7d41cbb5-8e3b-47a3-a0de-653c07a2864f, decided 05:18:58.507848 UTC. Reconciliation then completed with 37 instructional sessions, one classified deadline and zero quarantines. The deadline has zero canonical instructional sessions and two records retained as private source evidence. This is an explicit non-session classification, not a missing instructional class.

## Final authoritative proof

- Source SHA256: 60221a2674d5b1eb6da5ee35ef69189ef138435b57eb7393193acfc6ebdc6fd6.
- Ingest job: 99f1b358-2ecf-401c-bb5c-025216919d8c.
- Conservative source watermark: 05:14:50.570 UTC; expires 06:14:50.570 UTC / 02:14:50 EDT. The actual source was reread; no database-fetch timestamp was substituted.
- All 37 actual instructional classes are reconciled: three September 26 classes plus all 34 future instructional classes. The 35th future Enrollware source row is the separately classified renewal deadline.
- September 26 source/canonical counts remain 14186375=3, 14145607=0, 14184955=2. September 27 14361098/51485 and 14421081/51495 remain 1/1 each.
- At 05:20:13.615617 UTC, all 18 instructional registration relationships matched exact external class and registration IDs, and all source customer identity fields matched canonical records. No participant PII appears in the audit or public JSON.
- Protected health run 36296861999 passed at 05:19:37.644736 UTC: 37 canonical external sessions, explicit deadline classification, zero gaps. This is a current successful component observation, not a claim of persistent overall HEALTHY operation.
- Protected demand run 36296862999 passed at 05:19:44.042 UTC: 38 known rows including native/manual records, zero unknown rows, repeated content equal, OPTIONS 204 and unauthenticated 401. The deadline is not a demand session.
- Reapplying this actual protected projection to scratch copies of all eight public selectors and schedule/admin projections preserves all 12 Anchors on repeat. Both September 27 classes remain canonical_active_registration with count 1. Deadline Anchor absent. 31 public occurrences match; seven unmatched rows are the three private Brunswick classes plus four native/manual rows, not missing canonical public demand. Zero public occurrences have unknown demand.

Exact evidence: data/audit/issue297_deadline_classification_proof.json. Previous source/Brunswick/public-delivery audits and every R3/R4/R5/#297 receipt remain unchanged.

## Implementation, deployment and validation

Existing review and reconciliation paths were extended; no new table, schedule database or architecture was introduced. Two additive SQL migrations are deployed:

- supabase/migrations/20260927050745_classify_confirmed_enrollware_deadlines.sql
- supabase/migrations/20260927051624_retain_review_for_changed_deadline_sources.sql

Other changed implementation files: scripts/audit_enrollware_reconciliation.py; tests/test_enrollware_roster_reconciliation.py; tests/reconciliation/reconcile.test.mjs; .github/workflows/anchor-policy-ci.yml. Existing protected Edge Functions read the updated RPC; no new credential, binding, public grant or function deployment was required. Existing ingest tables have RLS and no anon/authenticated SELECT. Security advisor findings before/after are identical excluding observation timestamps.

CI 36296758471 passed the existing focused suite: 53 Python tests, 17 actual TypeScript endpoint/projection tests and one PostgreSQL lifecycle scenario. Commands remain those recorded in the R5 public-delivery receipt, with the expanded deadline assertions. The new assertions cover retained private evidence, absent instructional session, replay, changed source at an active location reopening review, PII-free health and anonymous function privilege rejection. Python syntax and git diff --check passed. The pre-existing unrelated broad selector failures remain outside this repair.

The incident public repair remains the approved PR197/PR299 implementation recorded in Codex_Reply_Issue157_PublicDelivery_R5.md. Public BLS HTML, seven referenced assets and three relevant JSON resources were reread at 05:22:16.917 UTC and still match current main's unchanged public bytes. Actual browser interaction at 05:22:39.059 UTC again showed PM / 1:00 PM and PM / 6:30 PM with exact enroll?id=14361098 and enroll?id=14421081 Register targets and no errors. No new publication of scheduling data was performed for this classification-only follow-up. The previous successful production data revision is 08faa58dc23da6bd7c7b99650d3d69c144b3443e; Pages may redeploy unchanged public bytes for subsequent source/receipt commits.

## Persistent-system boundary and next action

BUILT: yes. CONNECTED: source -> existing ingest -> canonical instructional sessions/registrations -> protected demand -> runtime -> public Anchor path. PROVEN: complete current instructional coverage and actual incident public behavior. MERGED: PR197, PR299 and PR301. DEPLOYED: canonical backend and classification SQL; public incident repair. LIVE-VERIFIED: protected production projections and actual public selector. Full persistent loop: not yet HEALTHY.

Two boundaries remain: an authorized recurring complete-roster source has not been connected, and GitHub has not emitted a post-repair schedule-event publisher at the last check. Current proof expires at 06:14:50.570 UTC, after which unknown/null behavior must remain intact. The existing observer is proven by manual production runs and deduplicated condition-change alerts; cron configuration is not proof of observer cadence. The quiet task heartbeat verify-157-scheduled-refresh watches the actual scheduled-publication proof and preserves the latest receipts.

The legacy iCal discovery/admin JSON may still display the source deadline row; it is not an instructional session in canonical demand, and its registration evidence is not discarded. Building a native renewal workflow is outside this scheduling repair. Direct/native/bookmarked/admin Enrollware booking paths still bypass LanderWare selector controls. Stage 6 remains gated; daily_anchor_stack_v1 and existing compatibility/time/availability rules are unchanged.

Smallest next infrastructure action: connect an authorized current complete export or completeness-guaranteed source to the existing importer, then prove continuous freshness. Continue read-only observation until an actual scheduled publisher runs and verify its deployed public result. No further location/date business decision is required for the source proof set. Keep #297/#157 open for the documented persistent boundaries and post future evidence there; do not create another scheduling ticket.

Receipt additions: this root Codex_Reply file and data/audit/issue297_deadline_classification_proof.json. They are committed and pushed on the named receipt branch. Private source snapshots remain outside Git; supabase/.temp/cli-latest remains intentionally untracked. Unrelated checkouts and prior receipts are preserved.
