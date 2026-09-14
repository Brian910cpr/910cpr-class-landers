# Issue #229 — Archive monitor backend R3

- Assignment: #229 LIVE MONITOR REQUIREMENT, September 14 12:38:31Z; independent backend continuation after #214 R56.
- Timestamp: 2026-09-14T08:56:00-04:00, America/New_York.
- State: **PR_OPEN** for this backend increment; broader archive/monitor **IN_PROGRESS**, archive publication gated.
- Evidence state: **BUILT**, validated locally. No owner-facing monitor connection, deployment or complete operational proof.
- Branch: `codex/issue-229-monitor-feed-r3`.
- Worktree: `E:\GitHub\910cpr-class-landers_codex_issue229_monitor_r3`.
- Base: `af1b2b498fc110357becf2078124cdc6c2091baf`, draft PR #231.
- Implementation commit: `9e9251f5c9678473bbc1e696584739a33731b4aa`.
- Draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/232 (stacked on #231, which is stacked on #230).
- This receipt and initial feed are the follow-up commit; exact pushed tip is returned on #229 after complete remote verification.

## Work and findings

Read the full #229 body/comments, #228 source contract, #140 gate and governing repository instructions before this increment. Added a local checkpoint/status-feed producer for the requested monitor, reusing existing R1 recovery and R2 identity audits. It has strict aggregate fields, immutable audit/code provenance, full eligible-corpus denominator, revision conflict protection, consistent progress/evidence checks, newest-first bounded events, stale-running heartbeat detection, exclusive writer lock and atomic persistence. It makes no network requests or scheduling/publication changes.

Initial feed at `data/audit/issue229_archive_rebuild_status.json` records 26,165 recovered rows, 26,171 old HTML URLs, 23,488 **preliminary** candidates, 2,677 non-candidates (2,037 private/ambiguous/review plus 640 not elapsed), 26,165 reconciled identity rows and seven unresolved orphan HTML pages. Approved `metrics.eligible_pages` and all GSC fields remain **null**. Generated/validated/failed/sitemap/published counts are zero for this new archive run. These are not whole-site totals or approval to publish. Source observations are imported at the actual checkpoint time; no historical job/heartbeat timestamp is invented.

Initial phase/state: ELIGIBILITY_REVIEW / BLOCKED; blockers ELIGIBILITY_REVIEW and CURRENT_INVENTORY_GATE. Checkpoint timestamp: `2026-09-14T12:55:17.821634+00:00`. Provenance names PR #232, implementation commit above and the immutable R2 audit-source commit. The initial file is 3,104 UTF-8 bytes.

Operational branch/validation details remain outside `docs/`. The CLI rejects public output paths and excludes raw/private source fields and free-text event payloads. The initial feed is **not an HTTP endpoint**; do not expose it publicly to approximate owner access. Reuse the existing remembered owner session when adding private delivery and the UI.

## Exact files and review references

1. `scripts/archive_rebuild_status.py` — strict status contract, `initial`, `advance`, `health`, CLI and atomic writer.
2. `tests/test_archive_rebuild_status.py` — focused behavior/privacy/persistence tests.
3. `data/audit/issue229_archive_monitor_backend_r3.md` — complete implementation report, exact contract/commands, semantics, recovery and integration limits.
4. `data/audit/issue229_archive_rebuild_status.json` — initial aggregate checkpoint.
5. `Codex_Reply_Issue229_ArchiveMonitorBackend_R3.md` — this unique repository-root receipt.

Unchanged authoritative audit inputs at `af1b2b498fc110357becf2078124cdc6c2091baf`: `data/audit/issue229_source_recovery_r1.json` (`sources.historical_corpus`), `data/audit/issue229_identity_reconciliation_r2.json` (`historical_rows`, `exclusive_historical_dispositions`, `orphan_html_count`). Existing source recovery code and all raw historical records remain intact. Feed JSON review paths: `baseline`, `metrics`, `gsc`, `provenance.sources`, `evidence`, `events`, `last_checkpoint_at`.

## Validation

```text
python -B -m unittest discover -s tests -p test_archive_rebuild_status.py -v
Ran 15 tests in 0.143s
OK
SYNTAX: 2 Python files passed
```

Tests include actual source-count reconciliation, explicit unknown eligibility/GSC, private-field rejection, immutable approval/evidence constraints, numeric partitions, stale/future clocks, revision/count/phase regression, bounded events, lock exclusion, failed atomic-replace recovery and prevention of public-file output. AST/in-memory compilation generated no bytecode. The final run followed the fixed-denominator safeguard; both runs passed. Prior unchanged 19-case recovery/identity tests were not rerun.

Exact one-file producer scope was reported before running:

```text
python -B scripts/archive_rebuild_status.py init --source-ref af1b2b498fc110357becf2078124cdc6c2091baf --run-id issue229-r3 --pr 232 --output data/audit/issue229_archive_rebuild_status.json
python -B scripts/archive_rebuild_status.py check --output data/audit/issue229_archive_rebuild_status.json
{"issue": 229, "run_id": "issue229-r3", "revision": 0, "health": "BLOCKED", "phase": "ELIGIBILITY_REVIEW"}
FEED: counts, unknown eligibility/GSC, zero generated/published, provenance passed
```

Both CLI commands succeeded; Git scope showed exactly the expected JSON output. No public generator ran. Staged/base-to-head whitespace and explicit-file checks passed before the code commit; final receipt/feed checks precede their commit. Four GitHub preflight/source-integrity checks at the implementation commit reported SUCCESS. These do not establish production monitor/archive health; final-head check status is reported separately on #229.

## Remaining work, proof and next action

Next eligible #229 implementation: expose this small feed through an owner-authenticated read-only route, add the requested owner monitor using existing remembered access and roughly 20-second polling, then wire actual archive jobs to checkpoint writes at meaningful batches. Avoid the broader dashboard's database/mailbox workload per poll. The monitor must clear operational data on auth failure, display observation age and distinguish BLOCKED from STALLED. Full-corpus bars use approved eligibility only; Google data requires actual observation/window/evidence. No new password or public admin feed.

Connect generation/validation/sitemap/deployment/GSC checkpoints only to their real results. R1/R2 Client/identity/timing/location/course/status exceptions and #228 canonical current inventory/#140 occupancy/freshness remain release gates. Full eligible archive, editorial library, sitemap architecture, deployment and indexing proof remain outstanding. No arbitrary pilot cap, public-page generation, merge, deployment, GSC submission, auth retry, operational-data mutation or member communication occurred here.

Expected end-to-end proof: a real job persists a checkpoint and an authorized owner page shows matching counts within 30 seconds; last such success is **not established**. While RUNNING, a missing checkpoint for over 300 seconds returns STALLED; future clocks return CLOCK_MISMATCH. BLOCKED remains blocked with the original age. Reads never update heartbeat. Writer/endpoint/UI observer and observer heartbeat are **not connected or proven**; no background service was installed. Retain prior feed on failure, preserve evidence and verify the writer is stopped before recovering a stale lock. Brian must not be the routine failure detector.

Reviewer: inspect the report, code and tests in PR #232, then continue authorized monitor/endpoint integration. The JSON/code do not themselves prove access control, remote delivery, legal public eligibility or production publication. Account/operator input remains necessary for existing private-source/credential gates; routine reversible monitor integration is already owner-authorized.

## Preservation and related #214 state

Both original dirty checkouts, four unpublished ShiftCommander commits, prior worktrees/receipts and active #226 work are preserved. Only the five intended files belong to this PR increment. Temporary unit-test files were removed by their fixtures; no new runtime/cache artifacts are intentionally retained. One worker; no additional launch, lock/lease or machine-default changes. Matching local session turn_context reports gpt-6-astra at `2026-09-14T12:39:56.729Z`, CLI `0.153.4`; runtime-local evidence, not provider attestation.

#214 remains BLOCKED at its independent approved persistent-auth/current ADR/private R37-R47 incident prerequisites. Its required unique receipt is already pushed and verified: `Codex_Reply_ShiftCommanderAstra_R56.md`, branch `codex/issue-214-shiftcommander-receipt-r56`, commit `b578bd9947235f424c735c270364dd4ab10dd365`. No ShiftCommander implementation/merge/deployment/cutover. Keep both work items open; this backend increment is not either production release.
