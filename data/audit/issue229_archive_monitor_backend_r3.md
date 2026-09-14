# Issue #229 — archive monitor checkpoint backend

Assessment: September 14, 2026, America/New_York (UTC-04:00).
Branch: `codex/issue-229-monitor-feed-r3`, based on `af1b2b498fc110357becf2078124cdc6c2091baf` / draft PR #231.
State: **IN_PROGRESS** for #229. Checkpoint producer **BUILT**, validated locally. Owner-facing monitor is not deployed, connected, or proven by this increment.

## Result

The September 14 12:38:31Z owner comment requires a watchable archive rebuild. This bounded backend increment adds `scripts/archive_rebuild_status.py` and its aggregate status contract, reusing the R1 recovery and R2 identity artifacts. It introduces no second archive catalog or scheduling source. It runs locally using Python standard libraries and Git; it performs no network request, page generation, publication, account operation or GSC submission.

The initial feed is `data/audit/issue229_archive_rebuild_status.json`. It deliberately stays outside the public `docs/` tree because it contains operational branch/validation provenance. The CLI rejects output outside repository `data/audit`. Publishing this internal file directly as static JSON is not an acceptable owner-access implementation. The separate root receipt supplies exact code/feed commits and PR links.

## Baseline and metric meaning

Source audit inputs are read from immutable Git commits, not possibly dirty working copies:

- `data/audit/issue229_source_recovery_r1.json`, `sources.historical_corpus`.
- `data/audit/issue229_identity_reconciliation_r2.json`, historical row/disposition/orphan totals.

The initial feed preserves these known facts:

| Field | Value / interpretation |
|---|---|
| `baseline.source_rows_recovered` | 26,165 |
| `baseline.html_urls_recovered` | 26,171 |
| `baseline.preliminary_candidates` | 23,488 elapsed preliminary candidates; **not approved public-safe pages** |
| `baseline.non_candidate_rows` | 2,677, including 640 not elapsed |
| `baseline.excluded_private_ambiguous_rows` | 2,037: 724 Client review + 409 timing + 641 location review + 263 provenance review |
| `baseline.identity_rows_reconciled` | 26,165; reconciliation does not approve historical facts/publication |
| `baseline.orphan_html_unresolved` | 7 |
| `metrics.eligible_pages` | `null`, full eligible denominator unresolved, not zero and not 23,488 |
| `metrics.pages_generated`, `pages_validated`, `pages_failed_validation`, `sitemap_urls_generated`, `pages_published` | 0 for this new archive run; not a count of all existing public site pages |
| `gsc.discovered`, `indexed`, `class_impressions`, `class_clicks` | `null`; no current Google observation imported |

No raw source row, participant, course label, Client, address, credential, arbitrary event message or exception contents are emitted. Classification is copied only through an exact allowlist. Source/reconciliation partitions must agree. The initial event rail imports SOURCE_RECOVERY and IDENTITY_RECONCILIATION evidence and marks ELIGIBILITY_REVIEW blocked at the current observation time. These timestamps describe this evidence import, not invented historical job execution times. Source recovery counts are in `baseline`; each rail item snapshots subsequent build counters in `metrics`.

## Contract and checkpoint behavior

Schema version 1 is enforced by `validate()` with exact allowed keys, enums, nonnegative safe integer counters and offset-bearing timestamps. `phase` supports SOURCE_RECOVERY, IDENTITY_RECONCILIATION, ELIGIBILITY_REVIEW, GENERATION, VALIDATION, SITEMAP, DEPLOY and GOOGLE_DISCOVERY. `state` is RUNNING, BLOCKED or CHECKPOINT_COMPLETE. BLOCKED requires enum blocker codes; a complete checkpoint is not a completed production release.

`provenance` contains the fixed repository, actual local branch/commit, optional PR number and immutable audit references. `evidence` has nullable `eligibility`, `validation`, `deployment`, `gsc` references shaped as `{commit, path}`. Paths must be aggregate JSON/Markdown artifacts under `data/audit`; CLI writes also verify that every referenced Git object exists. A syntactically valid reference is **not independent proof of its claims or approval**: the authorized upstream validator/operator must produce and review the actual artifact before reporting progress.

Generation phases require resolved eligibility evidence. Generated pages cannot exceed the full approved denominator or recovered corpus. Validation pass/fail partitions cannot exceed generated pages. Sitemaps/publication cannot exceed validated pages; validated and published counts require corresponding evidence. Eligibility is fixed after resolution; changed corpus/evidence or decreasing counters require a distinct run/output. Counters are cumulative unique-page results for an immutable run, not retries or totals summed across overlapping audit sources. Failed-page corrections/revalidation must begin a new run if those cumulative dispositions change.

Google values remain null until backed by an evidence reference, observed timestamp and explicit measurement window. Google values are not inferred from sitemap size, generated pages, historical impressions, or Git pushes. A UI must distinguish these measurement windows and dates.

`checkpoint` accepts exactly `expected_revision`, `phase`, `state`, `blockers`, `metrics`, `evidence` and `gsc`. Pass a full snapshot of those fields. Revisions reject stale/concurrent updates; phase/time/count regression is rejected. The last 100 checkpoint events are retained newest first. Long-term execution artifacts remain referenced in Git; this bounded rail is not an unlimited audit journal. Only an explicit checkpoint changes `last_checkpoint_at`; reads/polls cannot refresh it.

The exclusive sibling `.lock` prevents competing writers. JSON is flushed/fsynced to a same-directory temporary file and atomically replaced; failed replacement preserves the prior feed and removes the temporary file. No lock is automatically stolen. If a producer crashes leaving a lock, preserve the feed, check the PID/actual process and its owning job, and remove only that explicit stale lock after establishing no live writer. A scheduler/monitor must surface that failure. No such lock existed or needed recovery in this increment.

## Local commands

The initial producer writes **one** audit JSON; it does not invoke a public builder. After the script is committed, initialize once from R2's immutable audit commit:

```powershell
python -B scripts/archive_rebuild_status.py init --source-ref af1b2b498fc110357becf2078124cdc6c2091baf --run-id issue229-r3 --output data/audit/issue229_archive_rebuild_status.json
python -B scripts/archive_rebuild_status.py check --output data/audit/issue229_archive_rebuild_status.json
python -B -m unittest discover -s tests -p test_archive_rebuild_status.py -v
```

Use `--pr <number>` at initialization once the review PR exists. Initialization refuses to overwrite an existing feed. `--at <ISO timestamp with offset>` is available for deterministic local validation; normal producers omit it to record the actual UTC checkpoint time.

An approved future builder writes a local checkpoint envelope once per batch/phase, then invokes:

```powershell
python -B scripts/archive_rebuild_status.py checkpoint --output data/audit/issue229_archive_rebuild_status.json --update <local-checkpoint.json>
```

The update envelope is the seven-field contract above; reviewed evidence fields must be retained. Use the existing `advance()` function for in-process integration, and retain `writer_lock()` plus `write_atomic()` around the read/update/write transaction. No per-page network calls or expensive live database loop are needed.

## Validation and evidence limits

Fifteen focused unit tests cover actual audit baseline counts, cross-source mismatch, private-field exclusion, unknown-field rejection, approval/provenance requirements, numeric/partition bounds, full eligible denominator, Google evidence/window checks, immutable revisions/counters, stalled/future clocks, bounded event history, competing locks, atomic failure recovery and public-output rejection. AST/in-memory compilation checks the producer and tests without writing bytecode. The separate receipt records final test outputs, CLI integration checks, initial JSON count checks and exact commit/file scope.

The source audit itself is unchanged; its prior 19 passing tests were not rerun merely to repeat unchanged evidence. No full site build, archive HTML generation, frontend build, deployment, rendered owner monitor check or public availability test is claimed here. #228's canonical current-options projection and #140's credential-parity/occupancy/freshness publication gates remain intact. Nothing in this counter writer approves publication or resolves R1/R2 historical identity/privacy/course/status exceptions.

## Next integration and persistent-system proof

This is the backend prerequisite, not the watchable owner UI. Existing `docs/admin/admin-auth.js` / `owner-access.js` and `supabase/functions/_shared/owner-auth.ts` provide the remembered owner session pattern. Add an owner-authenticated read-only status route that reads this small checkpoint object without the broader dashboard's database/mailbox workload. Serve private/no-store responses; anonymous users receive no operational feed. Then wire `/admin/archive-rebuild.html` or a shared owner panel to that route, polling about every 20 seconds without overlapping requests; clear sensitive display on logout/auth failure. Include links to #229/#230 and the current PR, phase/event counts, observation age and full-corpus progress bars only after `eligible_pages` is known.

Connect actual approved archive builders/validation/sitemap/deploy/GSC workflows to checkpoint writes at meaningful batches. Do not pretend a scheduled writer exists merely because this utility exists. Backend auth/endpoint, rendered owner UI, workflow publishing of the feed and GSC observation remain outstanding. No additional permission prompt is needed for routine reversible integration already requested by the owner; existing source/publishing gates still apply to archive release.

Expected useful outcome: a real archive job advances a durable checkpoint and the authenticated owner page displays its matching counts within 30 seconds. Last successful complete end-to-end proof: **none**. While RUNNING, producers should checkpoint within 300 seconds; `health()` reports STALLED after that interval and CLOCK_MISMATCH for future timestamps. BLOCKED checkpoints stay BLOCKED and retain their age; polling must not make them look active. The UI should show observation age even for completed/blocked phases.

Observer and observer health: **not connected/proven**. The eventual monitor needs last successful poll/error state and the job needs an independently observed missing-checkpoint/failure signal; a closed browser or dead writer cannot be covered by Brian remembering to refresh. Validate writer stop/stall, endpoint failure, owner-session expiry, resumed checkpoint and atomic recovery before calling the monitor PROVEN/MONITORED. Account/private-source decisions still go through the existing issues; this utility never repairs credentials or changes publication policy.
