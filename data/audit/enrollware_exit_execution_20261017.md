# Enrollware exit execution checkpoint

2026-10-17 EDT. State: IN_PROGRESS. Diagnostic and dry-run evidence only; no production repair or cutover.

## Priority and boundaries

Brian authorized reliability, every-course Stripe/eOptions coverage, Enrollware replacement, then website AI before phone AI. Keep Google Voice. Do not pursue transfer of the Enrollware SMS number. Do not silence recurring errors as a substitute for repair.

## Booking failure: existing repair advanced

Production observation run 39074931969 failed because all eight family feeds retained two failed evaluation windows. Exact reason: missing directional travel rule from `:: Wilmington; Shipyard Blvd - B` to `4018 Shipyard Blvd, Room B, 910CPR Office`.

Existing draft PR #393 (`codex/issue334-location-proof-20261014-r56`) addresses the proven venue alias and primary-room filtering. It must be reviewed rather than independently reimplemented.

Executed the existing read-only release probe, run 39076409560, on that branch. The production refresh job was skipped. GitHub run and artifact both passed: `published=false`, `calculation_completed=true`, `release_passed=true`; all eight families have 441 input/normalized sources, 193 input windows, 193 evaluated windows, zero failed windows, zero uncertainty issues. BLS 3,566 offers; Heartsaver 7,438 offers. These are preview counts, not current live inventory guarantees.

Artifact: `v2-release-probe-39076409560/proof.json`, observed `2026-10-17T22:47:02.718209+00:00`. Eight matching HTML previews and JSON feeds preserved in the run artifact. Exact invocation: `gh workflow run refresh-admin-availability.yml --repo Brian910cpr/910cpr-class-landers --ref codex/issue334-location-proof-20261014-r56 -f v2_release_probe=true`.

The observer script's default diagnostic day is October 14, now in the past. Zero `dayOffers` is not itself the failing exit condition. Its actual exit condition includes nonzero failed windows and dynamic continuity checks. Do not mistake this diagnostic default for the root cause.

### Release boundary

PR #393 report `data/audit/issue334_location_r56.md` requires approval for its normal publisher scope after probe proof: approximately 40–60 generated/state files, including 17 configured selector/alias/redirect HTML files, eight family JSON feeds, canonical schedule/admin/reference/landscape/anchor/iCal data, current native anchor class pages, calendar snapshots and allowlisted audit/status files. No sitewide builder. Stop for more than ten unexpected files. This checkpoint does not grant or execute that publication. Review current branch versus current main before merging; the branch predates later production changes. After release verify live HTML, changed assets, legal offers and successive renewals.

## Participant reconciliation: concrete gaps

Run 39072065068 artifact `reconciliation-health` at `2026-10-17T21:42:36.667033+00:00` reports 46 gaps: 24 committed projections without canonical sessions, 14 stale reconciliations, eight requiring external reconciliation. Freshness window 60 minutes. These are classifications in the observer artifact, not proof that all students or classes are absent. Original source reconciliation timestamps include September 27 and October 10. Next work is tracing the existing ingestion/reconciliation recovery path and current authoritative records; do not fabricate fresh timestamps or merely relax the threshold.

## Course and payment baseline

Inspected current-main `data/config/course_master.json` and `data/config/course_options.json`. Master generated July 19, explicitly `authoritative=false`: 32 draft courses, 30 null base prices, all 32 backend fields set to Enrollware. Options file defines four BLS choices. This is a stale draft model still present on current main, not an exhaustive audit of live database pricing or checkout coverage.

`course_checkout_baseline_20261017.csv` preserves one draft-master row per course, option keys, missing fields and explicit UNVERIFIED values for option pricing, Stripe checkout and fulfillment. Promote existing canonical sources rather than creating a competing production catalog. Next: reconcile this list with live approved course/product/price records and active commercial-catalog workstreams; expand to one row per purchasable combination and prove payment, registration, occupied seat, confirmation, roster and fulfillment.

Existing PR #387 (`codex/native-registration-bls-renewal`) repairs native checkout routing and atomic paid registration. Its description records 37 regression tests and two real Stripe test-mode $75 guest payment proofs, including signed-webhook replay. Those are prior reported results, not rerun in this checkpoint. Production migration/function/page activation gates remain open. Do not claim all-course checkout is implemented or deploy it from this report.

## Local hygiene and validation

Original local checkout remains on `feat/customer-learning-studio-20261010`, commit `cda930cb2`, with existing changes to `docs/Earl/index.html`, `docs/Jackson/index.html` and untracked `supabase/.temp/`. No source edits, resets or cleanup. Fetch of current main was started separately; it is not evidence of a completed checkout update.

Locally parsed downloaded JSON and exported the 32-row CSV. Read-only remote evidence and one remote dry-run executed. No new application code to syntax-test. No registration, payment, SMS, email, production database, site publication or bot changes executed. Operational health is not established by this probe alone.

## Evidence

- https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/39076409560
- https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/39074931969
- https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/39072065068
- https://github.com/Brian910cpr/910cpr-class-landers/pull/393
- https://github.com/Brian910cpr/910cpr-class-landers/pull/387

Next action: review the passed PR #393 probe and publication scope, then release with live proof when approved. Independently investigate the 46 reconciliation classifications and live course/payment source ownership. Website AI and phone AI remain downstream.
