# Codex Reply: #157 public delivery and scheduled-refresh boundary

Timestamp: 2026-09-27T05:00:00Z / 01:00 EDT.
Repository: Brian910cpr/910cpr-class-landers.
Receipt branch: codex/issue-297-delivery-proof, based on main 08faa58dc23da6bd7c7b99650d3d69c144b3443e.
Observable runtime configuration: gpt-6-astra / xhigh. Existing work was coordinated before edits; unrelated dirty checkouts were preserved.
Work-item state: MERGED / DEPLOYED / LIVE-VERIFIED for the incident repair; subsequent scheduled-refresh proof remains pending. This is not a claim that the whole persistent system is HEALTHY.

## Approval, substantive changes and delivery

Brian explicitly accepted the immutable R3 receipt and approved normal publication, including the declared full publisher scope. R3 and R4 receipts remain intact. No Codex_Read acknowledgement was manufactured.

Existing PR197 merged normally at 04:31:28 UTC, merge b9297d128143b99b62d273770e0a7304a4d17b98. It includes substantive R3 3edaf2ef037ec491f8b7768c7bec264b2401d08c, #297 reconciliation 3d5f4e0f95ca961f9f90b2331dcaf47f8c78b745 and runtime freshness/proof 1cd4e16bf43c2a5102db1460d2d13c5306beedde. The approved normal public build 36294558652 succeeded and published 3830fd61cbfa595925dba3de6535c5de2b998227. Its 59 changed files were within the approved docs/hash scope.

Actual browser verification found a remaining presentation defect: an Anchor rewrite stored `1:00 PM` in the machine `startTime` field, so the selector grouped afternoon classes under AM. Narrow follow-up PR299 changed only scripts/apply_anchor_policy.py and tests/test_apply_anchor_policy.py. Substantive commit b3114af62da97823d3cb5487fedbec32b2885b12 preserves machine clocks `13:00` / `18:30` and formats display fields separately. The existing policy, ranking and asset code did not change. PR299 merged normally at 04:42:34 UTC, merge 781ed158d758b218eb2aadb58ceb8dce9e48755e.

Normal admin publisher 36295093741 succeeded; deployed publication revision is 08faa58dc23da6bd7c7b99650d3d69c144b3443e. Pages run 36295279074 completed at 04:47:21 UTC. Earlier queued admin run 36294558713 failed because main advanced during its build and generated JSON conflicted during rebase. The safety check prevented overwrite; the later fresh-main publication succeeded without reset, force push or bypass.

## Exact tests and production proof

CI run 36295036810 passed syntax compilation and:

```text
python -m unittest tests.test_anchor_state tests.test_apply_anchor_policy tests.test_canonical_scheduling_demand tests.test_fetch_canonical_scheduling_demand tests.test_demand_publication tests.test_selector_clock tests.test_enrollware_roster_reconciliation
Ran 52 tests in 14.549s — OK
node --test tests/canonical_demand_endpoint.test.cjs tests/enrollware_roster_proof.test.cjs
17 tests, 17 pass, 0 fail
node --test tests/reconciliation/reconcile.test.mjs
1 PostgreSQL lifecycle scenario, 1 pass, 0 fail
```

The isolated lifecycle proofs cover empty uncommitted occurrence -> one active registration -> Anchor -> refresh -> removal -> refresh, plus valid independent commitment/manual exceptions, weekdays/Saturday/Sunday, exact external identities, source-owned reschedule/absence handling, and stale/missing/mismatched fail-closed behavior. The production location-authority trigger is included in the PostgreSQL fixture. The broader selector suite's pre-existing 14 failures/18 errors in 60 tests were reproduced on main/R3 and remain outside this changed path; see immutable R3 evidence.

At 04:47:43.738 UTC the live BLS HTML, all seven referenced first-party CSS/JS resources, schedule JSON, Anchor JSON and BLS selector JSON returned HTTP 200 and matched the exact deployed Git blobs. At 04:48:15.734 UTC actual browser interaction proved:

- September 27 Renewal: PM / 1:00 PM, Register targets exact external class 14361098.
- September 27 HeartCode: PM / 6:30 PM, Register targets exact external class 14421081.
- Both source registrations are canonical count 1 and both Anchor reasons are canonical_active_registration.
- Tuesday September 29 BLS Initial presents 11:00 AM / 8:30 PM; the inspected 11:00 AM URL uses appointmentDayId 260770 and courseId 209806. Published offers attach to registered ACLS Anchor 13963994.
- Saturday October 3 BLS Initial presents 8:00 AM / 11:00 AM; the inspected 8:00 AM URL uses appointmentDayId 260774 and courseId 209806. Published offers attach to registered HeartCode Anchor 14186226.
- No browser errors. No actual Register checkout or booking mutation was used for proof.

All 12 Anchors survived two successive production publications. The corrected publication matched 31 public occurrences with zero unknown public occurrences. Four unmatched native/manual canonical rows are distinct from the former four external-session gaps. BLS final output contains 202 availability blocks, 8,111 offers, 2,963 starts and 90 dates. Earlier candidate/rejection counts and the Eastern lead-time proof remain in data/audit/issue297_candidate_publication_proof.json. daily_anchor_stack_v1, compatibility, durations, conflicts, lead time, spacing and instructor rules remain intact. Stage 6 stays gated.

Machine-readable delivery/browser evidence: data/audit/issue157_public_delivery_proof.json. Related prerequisite follow-up: Codex_Reply_Issue297_CanonicalReconciliation_R2.md and data/audit/issue297_brunswick_approved_reconciliation.json. Prior source/test inventory remains in Codex_Reply_Issue297_CanonicalReconciliation.md, Codex_Reply_Issue157_RuntimeProjection_R3.md and Codex_Reply_Issue157_RuntimeProjection_R4.md.

## Remaining exact boundary

BUILT: yes. CONNECTED: authoritative incident source through canonical database, endpoint, runtime, Anchor and public selector. PROVEN: incident end-to-end and repeated push publication. MERGED: PR197 and PR299. DEPLOYED: exact revision above. LIVE-VERIFIED: actual public HTML/assets/selector above. MONITORED/HEALTHY for the entire persistent loop: not established.

At 04:57:24 UTC, explicit-repository GitHub queries still showed the latest actual schedule events as public run 36286577970 at 01:47:03 and admin run 36286383604 at 01:43:10, both before the repair. Workflows are active, but no post-repair schedule event has started. A push-triggered run is not scheduled proof. GitHub scheduler delay is an external unresolved observation boundary; no workflow dispatch was relabeled and no duplicate scheduler was added to the repository.

A task heartbeat named Verify #157 scheduled refresh (automation id verify-157-scheduled-refresh) will check this boundary every 30 minutes, remain quiet on unchanged state, and record the first actual scheduled-run/public proof or a material blocker. Its configuration is follow-up coverage, not evidence that GitHub scheduling is healthy. It pauses when proof is recorded or an external owner blocker is reported.

The current authoritative roster watermark is 04:25:29.547 UTC and expires at 05:25:29.547 UTC. No unattended complete-roster source is connected. After expiry, the repaired endpoint/runtime must report unknown/null, never zero, until an actual fresh source is reconciled. Source staleness must not be mistaken for a code regression or hidden by renewing database-fetch timestamps.

Native Enrollware checkout, direct/bookmarked appointment links and administrator registration remain outside LanderWare selector controls. Actual source records show Renewal booked first (September 24 19:26 ET), then HeartCode (September 26 15:59 ET); the customers' navigation channels are unknown. No inference was made from the materials-option label MANUAL: OTHER SOURCE.

Next action: preserve this delivery, observe an actual later scheduled publisher, verify its deployed public selector, then append a new immutable proof. Resolve #297's remaining TBD commitment and authorized unattended source before claiming persistent health. Keep both existing issues open for those stated boundaries; do not open another scheduling issue.
