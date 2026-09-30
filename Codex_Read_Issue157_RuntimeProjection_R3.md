# Codex Reply: Issue 157 Runtime Projection R3

Timestamp: 2026-09-27T03:10:00Z (America/New_York: 2026-09-26 11:10 PM EDT)
Assignment: existing #157 R3 / PR #197; direct prerequisite #297
Branch: codex/issue-157-runtime-projection
Substantive commit: 3edaf2ef037ec491f8b7768c7bec264b2401d08c
Main reconciliation commit: 2db7c48f273
Work-item state: BLOCKED / PR_OPEN — implementation and backend verification complete to the boundary below; production scheduling repair is not complete.

## Delivery state

- BUILT: yes, persisted in the actual isolated repository worktree and pushed to the existing PR branch.
- MERGED: no. PR #197 is mergeable/CLEAN but has no review approval. The existing issue expressly requires R3 receipt review before merge.
- DEPLOYED: protected read-only canonical-scheduling-demand endpoint only, version 1. Public scheduling changes are not deployed.
- LIVE-VERIFIED: endpoint authentication/CORS/data fetch/repeated fetch yes. Repaired production Anchor/public-selector behavior no.
- Persistent-system classification: BUILT; endpoint transport verified. Do not claim the entire demand-led scheduler CONNECTED, PROVEN, MONITORED or HEALTHY. Isolated lifecycle proof is recorded separately from production proof.
- Stage 6 corporate availability remains gated.
- No real student booking was created, modified, moved, canceled, or invented. Real customer verification was read-only.

## Findings and completed work

The actual incident is Sunday September 27, 2026. Renewal external class 14361098 (appointment class 51485, course 359474) at 1 PM was registered September 24 at 7:26 PM Eastern. HeartCode class 14421081 (appointment class 51495, course 210549) at 6:30 PM was registered September 26 at 3:59 PM Eastern. Authenticated Enrollware rosters currently show one each; notices corroborate the order. Customer navigation/referral channels are unknown. Neither booking is assumed to have traversed LanderWare.

Before HeartCode was booked, main af4befbd61699b65fc5603ff60292558665a40dd already labeled 6:30 PM as a Barnacle attached to the 1 PM Renewal. The 18:02 UTC build clock was incorrectly used as Eastern wall time, shifting the 24-hour lead-time cutoff four hours late. The regression demonstrates that 3 PM the next day passes at the correct 14:02 Eastern reference but fails at the erroneous 18:02 reference. This is a demonstrated filtering defect, not proof of either customer's navigation route or every historical constraint.

Implemented: DST-correct New York endpoint date boundaries, CORS OPTIONS, stable paginated PII-free reads, explicit unknown external counts, validated atomic runtime projection in both publishers, canonical input to candidate consolidation and final promotion, stale/ambiguous projection clearing, explicit commitment/manual override preservation, correct Anchor checkout URL reuse, per-occurrence audit reasons, and Eastern build clock conversion. An AST comparison confirms daily_anchor_stack_v1 implementation is unchanged; policy configuration, lead time, duration/conflict/availability/compatibility/repeat rules are unchanged. No weekend exceptions or alternative catalog/scheduling architecture were added.

## Exact production prerequisite / stopping boundary

Fresh production SQL across all record scopes returns zero class_sessions for September 26–27. The existing #297 examples and both Sunday incident classes are missing, so their canonical registrations cannot be joined. A live read of old imported rows cannot establish current external-roster completeness. Historical promotion/report-only import code does not supply a current complete-roster watermark or cancellation/reschedule/empty-roster coverage.

The read-only publication dry-run used the real freshly fetched endpoint artifact and copies of main schedule/BLS selector files. Result:

```json
{
  "canonical_endpoint_sessions": 7,
  "known_counts": 4,
  "unknown_counts": 3,
  "repeat_content_equal": true,
  "anchors_promoted": 0,
  "canonical_demand_rows_matched": 0,
  "canonical_demand_rows_failed_closed": 7,
  "occurrences_with_unknown_demand": 31,
  "incident_14361098": "missing_canonical_session",
  "incident_14421081": "missing_canonical_session"
}
```

The four known native/manual canonical sessions do not match this public Enrollware occurrence inventory; the other three backend rows are explicitly unknown. All 31 public occurrences remain unknown. This is NOT a claim of zero students. No production public files were changed by this dry-run. It applies policy to copied published inputs; it is not a full production candidate rebuild.

Required owner/reconciliation action under existing #297: establish canonical committed session identity and current complete registrations from an authoritative source, with explicit completeness/freshness and cancellation/reschedule semantics. R3 currently keeps every external-backend count unknown until that proof exists. No missing Supabase credential is claimed: authenticated reads and deployment worked. The obstacle is missing authoritative canonical data and the outstanding review gate, not unrelated maintenance.

## Tests and checks

1. `python -m unittest tests.test_anchor_state tests.test_apply_anchor_policy tests.test_canonical_scheduling_demand tests.test_fetch_canonical_scheduling_demand tests.test_demand_publication tests.test_selector_clock`: 43 tests passed locally and in GitHub CI.
2. `node --test tests/canonical_demand_endpoint.test.cjs`: 12 passed, 0 failed locally and in CI; actual TypeScript handler, isolated database/auth fixtures, 501-row pagination, active/unknown counts, invalid ranges, CORS/auth, winter/summer and 23/25-hour DST days.
3. Five changed Python modules compiled; four workflow YAML documents parsed; `git diff --check` passed.
4. Existing broader selector suite: 60 tests, 14 failures and 18 errors on both current main and this repair, with no newly failing test IDs. Missing ignored data/sessions_current.json and stale checked-in generated-output assertions remain. Exact comparison is in data/audit/issue157_r3_proof.json under selector_regression_comparison. This suite is not claimed green.
5. Isolated endpoint → HTTP fetch → runtime → schedule/Anchor → selector publication: 0→1→1→0→0 on a weekday, Saturday and Sunday. Explicit commitment/manual overrides and legacy explicit commitment metadata survive demand removal. Missing/ambiguous input clears prior demand; absent runtime stops publication.
6. Actual repository BLS HTML and CSS/JavaScript, served locally with only a fixture JSON route: count 1 renders noon/3 PM HeartCode `is-barnacle` buttons around a 1–3 PM Renewal Anchor; refresh preserves them. Count 0 renders four ordinary `is-available` slots and no Anchor. Register targets are example.test fixture URLs; no real checkout occurred.

CI at substantive commit:
- Anchor policy CI (PR): https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36290298497 — success (43 + 12 tests).
- Anchor policy CI (push): https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36290295060 — success.
- Source integrity: https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36290298416 — success.
- Cloudflare preflight: https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36290298557 — success.
- Session-workspace baseline parity: https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36290298435 — success.
- Cloudflare Pages PR check passed. A preview check is not deployment of the repaired production scheduling pipeline.

## Endpoint deployment and live verification

Supabase project: wktwgcnwdvbebcobgyey
Function: canonical-scheduling-demand
Version: 1
Function ID: d4fe35dc-9ccb-4043-9593-172cf629ef9f
Deployed bundle SHA-256: 58c3c86cb628430745016aa93176e6d2aa2eb3b2d3dca16e9a07ce1ef2bc8d6a
The deployed source was fetched back and exactly matches the local committed source after trimming terminal newlines.

Custom authentication uses the existing HOT_SYNC owner endpoint. JWT verification is disabled only because this function implements that existing custom authentication; no credential or service secret was exposed.

Live allowed-origin OPTIONS: 204, empty body, correct Allow-Origin/Allow-Headers. Missing key: 401. Deliberately invalid key: 401. Untrusted origin: 403.

Authenticated read-only workflow: https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36290293251 — success. It uses the existing GitHub HOT_SYNC secret, not a copied/local credential. Payload generated 2026-09-27T03:04:12.514Z; 7 sessions; 4 known and 3 unknown; two fetches have identical stable content hash 0124039a6f5062489cb9756cacbee4da33bf8a8def8e5595cee1ca07866dcc8a. Artifact: canonical-demand-production-proof (proof.json, runtime.json, fetch-status.json), all PII-free. Durable summary: data/audit/issue157_r3_live_endpoint.json.

Public main/deployment baseline remains 616832dec7cef34b0e4928d90fe74a7d480259ab, successful Pages run 36286584307. Live https://www.910cpr.com/bls.html and its seven same-site referenced JS/CSS files returned 200; hashes and pre-repair JSON are in the proof audit. Actual public browser inspection shows direct Enrollware registration URLs. This verifies the current surface, not the repaired result. Native Enrollware appointment checkout, saved/direct URLs, administrator adds, and other external channels still bypass LanderWare selector policy. The incident visitors' particular channels remain unknown.

## Files changed in the substantive repair

- .github/workflows/anchor-policy-ci.yml
- .github/workflows/refresh-admin-availability.yml
- .github/workflows/refresh-public-site.yml
- .github/workflows/verify-canonical-participants.yml
- scripts/anchor_state.py
- scripts/apply_anchor_policy.py
- scripts/block_start_time_selector.py
- scripts/canonical_scheduling_demand.py
- scripts/fetch_canonical_scheduling_demand.py
- supabase/functions/canonical-scheduling-demand/index.ts
- tests/test_block_start_time_selector.py
- tests/canonical_demand_endpoint.test.cjs
- tests/helpers/canonical_demand_endpoint.cjs
- tests/test_demand_publication.py
- tests/test_selector_clock.py
- data/audit/issue157_r3_demand_repair.md
- data/audit/issue157_r3_proof.json

This communication commit additionally contains data/audit/issue157_r3_live_endpoint.json and this immutable receipt. Prior Codex_Read_Issue157_RuntimeProjection_R2.md and every other prior receipt were preserved. No Codex_Read state was manufactured.

The substantive report is data/audit/issue157_r3_demand_repair.md; the exact JSON evidence is data/audit/issue157_r3_proof.json; authenticated backend and dry-run counts are data/audit/issue157_r3_live_endpoint.json. These three files plus the endpoint, both publishers, canonical matcher, selector clock and isolated tests are the primary review inputs. No private customer export, screenshot or credential is in the branch. Temporary browser fixtures, diagnostic logs and case-collision backups remain outside the repository under the task work directory; no unrelated untracked files are intended for commit.

## Existing issue evidence and exact next action

- #157 implementation evidence: https://github.com/Brian910cpr/910cpr-class-landers/issues/157#issuecomment-5852136374
- #297 direct prerequisite coordination: https://github.com/Brian910cpr/910cpr-class-landers/issues/297#issuecomment-5852136510

ChatGPT/owner should review this R3 receipt and substantive commit on existing PR #197, acknowledge according to the handoff protocol, and complete/assign the exact #297 canonical reconciliation prerequisite. Do not rename this receipt from Codex; only the supervising process may acknowledge it. The governing #157 instruction explicitly says not to merge before this review: https://github.com/Brian910cpr/910cpr-class-landers/issues/157#issuecomment-5760164604.

After the canonical data contract is proven and review permits rollout, merge the existing PR through the normal review/security process, use the normal production publishers, record the deployed commit, verify actual live schedule/Anchor/selector JSON plus referenced HTML/CSS/JavaScript, then prove persistence through a subsequent production refresh. Keep Stage 6 gated until that production proof exists. No branch protection, security check or review requirement was bypassed.
