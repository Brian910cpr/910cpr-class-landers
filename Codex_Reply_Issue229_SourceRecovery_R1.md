# Issue #229 source recovery receipt

- Assignment: #229 owner EXECUTE NOW dispatch, advanced sequentially while #214 remains blocked.
- Timestamp: 2026-09-14 11:48:16 UTC.
- State: **PR_OPEN / IN_PROGRESS** for the archive; bounded source recovery **VERIFIED locally**. Audit tool **BUILT**. No archive deployment or operational HEALTHY claim.
- Branch: `codex/issue-229-source-recovery-r1`.
- Worktree: `E:\GitHub\910cpr-class-landers_codex_issue229_recovery_r1`.
- Substantive commit: `beaed931f3352e50e0f13b12d083b55f61ff898d`, based on `abc7e9b1dd2d03039437721f80fe294190060c8a`. Receipt is a separate commit; pushed tip/PR are returned on #229.

## Concrete result

Recovered the specified Git sources and both SEO branches directly from existing local Git. No fallback filesystem hunt or cloud regeneration was required. Implemented a deterministic read-only inventory with workbook provenance, URL coverage, privacy gates and by-source/year/course counts. Full restoration remains the target; no numerical pilot cap was added.

- `f523c364ccbb29fffdf96fec1b4a915421f682bd`: `scripts/build_landers.py` embeds the historical template/passed notice/Upcoming Classes mechanism; `scripts/build_schedule.py`, `data/schedule.json`, `docs/data/public_schedule.json`. 1,812 numeric pages/source rows.
- `a7ff508d070ee7c23db0c955c04f05d03c4ef576`: `raw/Class Report.xlsx`, `data/schedule.json`, `scripts/build_landers.py`, `scripts/build_schedule.py`, `scripts/build_index_and_sitemap.py`. **26,171 historical HTML paths and 26,165 source rows**; the commit filtered compiled discovery, while its tree retained the class files.
- `seo/core-selector-local-pages` at `d02a7a6fe7a398112cf71595e62fa3cc1d351745` and `codex/seo-funnel-final` at `269e9fd7015128fd7652d57864623da1aaa2fd4a`: source/template lineage inspected and blob-pinned in the manifest.
- Current `data/schedule_all.json`: 19,708 records, including 19,655 registration identities shared with the historical corpus; 6,510 old registration identities are absent from that current archive. Existing retained-page rendering in `scripts/build_landers.py` should be extended, not overwritten with the old template.

At fixed `2026-09-14T00:00:00-04:00`, old-corpus exclusive buckets are **23,488 preliminary public candidates**, 409 invalid/ambiguous timing, 640 not elapsed, 724 client review, 641 non-public-location review, 263 workbook-provenance review. Candidate is not publication approval or proof a class was taught. Historical workbook enrollment: 4,603 positive / 21,562 zero; neither is converted into fabricated completion status.

Privacy finding: the old exporter dropped Client; 812 workbook rows have a client, including 67 at public-marker locations. All source IDs uniquely join the workbook, and all course/time/registration identities agree. All 268 location differences are literal JSON `nan` versus blank workbook cells; 263 survive the earlier timing exclusion. Do not invent their city.

URL preservation: **26,164 / 26,171 = 99.9733%** old paths match their same-snapshot source ID. Seven unmatched pages and one source row without a page need reconciliation. Zero exact old paths occur in the pinned current tree. Across six snapshots, 26,286 numeric paths and 26,274 distinct registration identities are found; overlapping snapshots and changing session-ID namespaces must not be double-counted as classes.

Year counts (all rows / candidates): 2020 1,529/1,093; 2021 8,040/7,691; 2022 1,438/1,198; 2023 3,695/3,254; 2024 4,957/4,687; 2025 4,385/4,142; 2026 2,121/1,423. Complete 75 historical course-label groups and all-source/year/course breakdowns are in `sources.*.by_course_label_sha256` in the JSON. Labels are hashed because raw titles can embed private details; controlled family buckets are explicitly non-authoritative summaries.

## Files and validation

Exactly five intended files, including this receipt:

1. `scripts/audit_historical_source_recovery.py`.
2. `tests/test_audit_historical_source_recovery.py`.
3. `data/audit/issue229_source_recovery_r1.json`.
4. `data/audit/issue229_source_recovery_r1.md` (full report, exact source paths, commands, counts and next steps).
5. `Codex_Reply_Issue229_SourceRecovery_R1.md`.

Validation: **8 unit tests passed**, zero failures/errors; 2 Python AST/in-memory syntax checks passed. All 6 source totals reconcile by exclusive reason/year/course. Registration-host/ID validation, duplicate aliases, private Client restoration, missing provenance, privacy-safe output, elapsed boundary and DST ambiguity are covered. Exact command and result are in the report. Only the announced JSON report was generated; no public file generator ran. Initial exploratory timing count was refined from 401 to 409 by the final positive-duration/DST-aware validation, without altering source data.

Git diff/whitespace and explicit staged-file scope checked. The original dirty LanderWare and ShiftCommander checkouts, unpublished ShiftCommander commits, old worktrees and receipts are preserved. No new untracked working files are intentionally left. No unrelated test failure occurred. Existing openpyxl read the workbook in memory; no dependency install, workbook edit or export.

## Remaining work and concrete continuation

Archive generation, editorial modules, privacy/content validation, deployment and GSC submission are not completed. Reconcile short historical URL IDs with existing Registration Link identities and actual class/status provenance; investigate orphan/missing pages and exceptions; build the allowlisted historical input into the current retained-page generator with an explicit dry-run scope. Avoid the current automatic elapsed-to-completed wording where completion is unverified.

Reuse #228's canonical current-inventory/conflict decision; preserve #140's fail-closed occupancy and #227's source-freshness hold for public release. These do not block local source recovery but do gate publishing current options. Before any sitewide generator, return exact command/output directories/full eligible file estimate for the AGENTS.md scope gate. Validate every eligible page before production and monitor GSC/HTTP/privacy outcomes after release; no arbitrary archive cap.

Next ChatGPT action: review the four substantive files at the exact commit, especially `workbook_provenance_unresolved`, dropped Client recovery, URL-ID overlap, `publication_authorized_count: null` and the no-completion-inference limitation. Continue the historical generator/canonical projection tranche with those findings. This audit requires no new account action; publication freshness, current canonical authority and GSC access retain their existing operator dependencies. No new authorization to weaken those gates is inferred.

Deployment: local source audit and tests only; intended files committed/pushed for draft review. No application merge/deployment, source mutation, registration/calendar write, member communication or GSC claim. As a one-time recovery audit, no recurring monitor is created; archive publication/refresh observer and last real end-to-end success remain unestablished.
