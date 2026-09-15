# Issue #229: historical source recovery

Assessment: September 14, 2026, America/New_York. Fixed cutoff: `2026-09-14T00:00:00-04:00`.
State: source recovery **VERIFIED locally**; archive implementation **IN_PROGRESS**, not generated/deployed.
Branch: `codex/issue-229-source-recovery-r1`, based on `abc7e9b1dd2d03039437721f80fe294190060c8a`.

## Recovered machinery and data

The requested recovery points and both SEO branches are present in existing local Git. No extra CyberPC filesystem search, cloud regeneration or source reconstruction was necessary. The audit reads exact immutable blobs in memory; it does not copy private workbooks or historical records into a new public artifact.

| Recovery point | Exact reusable files and finding |
|---|---|
| `f523c364ccbb29fffdf96fec1b4a915421f682bd` | `scripts/build_landers.py` contains the embedded HTML template, explicit passed-session notice and Upcoming Classes recovery. `scripts/build_schedule.py`, `data/schedule.json`, and `docs/data/public_schedule.json` preserve its inputs. There are 1,812 numeric class URLs, all matched to that snapshot's 1,812 source IDs. |
| `a7ff508d070ee7c23db0c955c04f05d03c4ef576` | `raw/Class Report.xlsx` has 26,165 rows. `scripts/build_schedule.py` exports them to `data/schedule.json`. `scripts/build_landers.py` and `scripts/build_index_and_sitemap.py` preserve generation/discovery machinery. The commit added `is_future_session()` to compiled course/location/sitemap surfaces; its tree still contains 26,171 class HTML files. This removal from discovery was not deletion of the entire historical corpus in that commit. |
| `seo/core-selector-local-pages` at `d02a7a6fe7a398112cf71595e62fa3cc1d351745` | Inspected source tree and `docs/data/schedule_future.json` (35 rows); generator paths and blob IDs are in the JSON manifest. 99 numeric class files plus index. |
| `codex/seo-funnel-final` at `269e9fd7015128fd7652d57864623da1aaa2fd4a` | Same generator lineage and `docs/data/schedule_future.json` (23 rows); 103 numeric class files plus index. |
| Current pinned main `abc7e9b1dd2d03039437721f80fe294190060c8a` | `data/schedule_all.json` retains 19,708 mapped records; `docs/data/schedule_future.json` has 25 rows. Current `scripts/build_landers.py` already has `render_past_current_inventory_html`, retained-page rendering and lifecycle presentation. Reuse those entry points; do not install the old generator over them. `scripts/public_class_eligibility.py` is the existing exact `::` location-marker rule reused by this audit. |

The old template's course-substring browser filter and repository-prefixed `public_schedule.json` URL are historical mechanisms, not an acceptable replacement for #228's canonical projection. The current builder also scans/retire-processes existing output files; a full invocation is not a narrow dry run. No old or current public builder was executed.

## Source and URL counts

| Source | Rows | Preliminary elapsed public candidates | Other disposition |
|---|---:|---:|---|
| Original passed-page pattern | 1,812 | 0 under today's exact public marker | Its location strings lack `::`; this is a provenance difference requiring mapping, not proof all those sessions were private. 640 are future at cutoff; 9 invalid timing. |
| Historical workbook/JSON corpus | 26,165 | 23,488 | 409 invalid/ambiguous timing; 640 not elapsed; 724 client review; 641 non-public-location review; 263 workbook provenance unresolved. These buckets are exclusive and sum exactly. |
| Current archive JSON | 19,708 | 17,924 | 225 timing; 640 not elapsed; 244 client; 675 location. JSON-only provenance; no independent workbook reconciliation claimed. |
| SEO core public snapshot | 35 | 10 | 25 not elapsed; historical snapshot is not current booking authority. |
| SEO final public snapshot | 23 | 6 | 17 not elapsed. |
| Current public snapshot | 25 | 3 | 22 not elapsed. Snapshot is not fresh eligibility proof while #140 is unresolved. |

Snapshots overlap. Across them there are **26,274 distinct Enrollware registration IDs**, not 45,929 classes: 45,929 is the union of differently shaped `session_id` values. The current archive shares 19,655 registration IDs with the old corpus, adds 53, and lacks 6,510 old registration IDs. This is recovery inventory, not final reconciliation to live canonical class records.

Old URL preservation: 26,164 of 26,171 historical numeric HTML paths match their same-snapshot short source ID (**99.9733% identity coverage**). Seven files lack a matching source row; one source ID lacks its expected file. Those require investigation, not fabricated 200 pages. None of those 26,171 exact old paths is present in current main's 115 numeric class paths. This is Git-tree coverage, not live HTTP/indexing measurement. Across all inspected trees, 26,286 numeric paths are recoverable; 26,220 match at least one inspected source ID and 66 remain unmatched across those sources.

Preserve short historical `/classes/<Class Report ID>.html` aliases while reconciling through the source Registration Link ID. Do not rename every old URL to a newer ID or mass redirect it to a course page. Registration identities were parsed from existing Enrollware links, never guessed.

## Historical year and course breakdown

| Start year | Source rows | Preliminary public candidates |
|---|---:|---:|
| 2020 | 1,529 | 1,093 |
| 2021 | 8,040 | 7,691 |
| 2022 | 1,438 | 1,198 |
| 2023 | 3,695 | 3,254 |
| 2024 | 4,957 | 4,687 |
| 2025 | 4,385 | 4,142 |
| 2026 | 2,121 | 1,423 |
| Total | 26,165 | 23,488 |

There are 75 exact historical raw course-label groups. Complete source/year/course counts and rejection counts are in `issue229_source_recovery_r1.json`, path `sources.historical_corpus.by_course_label_sha256`. Keys are SHA-256 of the exact UTF-8 source label, so a private reviewer can reproduce the join without publishing possibly client-specific raw labels. The same breakdown exists for every source.

Coarse candidate family buckets: BLS 12,303; ACLS 3,781; Heartsaver 3,668; First Aid 1,519; CPR 1,094; PALS 804; Unclassified 319. These keyword buckets are audit summaries, not authoritative Course Master mappings. Exact course/certifying organization/delivery mapping still requires review before rendering.

## Privacy and accuracy findings

- The workbook has **812 populated Client cells**, including **67 at `::` locations**. The historical JSON exporter dropped Client entirely. A public-location check on that JSON alone can expose corporate history; the workbook join restores that review signal.
- All 26,165 source IDs join uniquely to workbook rows. Course, start, end and registration identity agree for every row. There are 268 exact location differences: **every one is JSON literal `nan` versus a blank workbook location**. Five hit the earlier timing gate; 263 appear in the exclusive provenance bucket. They need a known public location, not a guessed default city.
- Historical enrollment flags are 4,603 positive and 21,562 zero. Zero enrollment is not automatically deleted by this audit, and positive enrollment is not proof of completion. No source status here proves every occurrence was taught rather than cancelled or held as an available slot. Render neutral passed-session wording until actual completion/cancellation evidence is reconciled; do not turn all elapsed rows into an unsupported "class was held" claim.
- No participant names, client names, instructors, private locations, raw course labels, registration URLs, workbook rows or operational records are written to the report. Tests check representative private strings stay absent.
- `publication_authorized_count` is explicitly null, not 23,488 and not an arbitrary pilot cap. Public-safe approval awaits class/status/identity and content validation. Full legitimate restoration remains the target.

## Implementation and validation

New executable audit: `scripts/audit_historical_source_recovery.py`. It pins source commits, reads JSON/workbook data from Git, reuses the current location rule, refuses invalid/zero-length/DST-ambiguous timing, checks registration identity and duplicates, and emits aggregate provenance/URL/year/course counts. It neither imports the site generator nor changes schedule truth.

Exact final command (one report output, no public directory writes):

```powershell
python -B scripts/audit_historical_source_recovery.py --current-ref abc7e9b1dd2d03039437721f80fe294190060c8a --as-of 2026-09-14T00:00:00-04:00 --output data/audit/issue229_source_recovery_r1.json
```

Validation: `python -B -m unittest discover -s tests -p test_audit_historical_source_recovery.py -v`: **8 passed**, 0 failures/errors. Both new Python files passed AST/in-memory compilation. All six source totals reconcile by exclusive reason, year and course. Final output reports 6 sources and the union counts above. The initial exploratory elapsed count used `end >= start`; the final executable deliberately rejects zero-duration and ambiguous dates, so its 409 timing exceptions supersede the initial 401 exploratory count. Only intended source/test/report files changed after audit generation; no unexpected bulk output.

Existing openpyxl was used for read-only workbook extraction; no dependency was installed and no workbook was edited/exported. No external auth, cloud compute, source calendar fetch, participant read, generator, HTML validation, deployment, Search Console submission or live indexing claim occurred.

## Next implementation and release gates

1. Reconcile the historical short-ID/Registration-Link crosswalk to current class identity and status; resolve seven orphan HTML paths, the missing page, 268 missing-location provenance differences and timing exceptions. Keep exception lists private when they contain source records.
2. Extend the existing retained-page generator with an explicit historical input and dry-run scope; retain original URLs and neutral passed wording where completion is unknown. Use an allowlisted public record projection that excludes Client/instructor/student data. Add whole-corpus privacy, self-canonical/schema, expired-booking and internal-link validation before publishing any recovered corpus.
3. Reuse #228's exact current public/conflict decision, including #140 occupancy freshness. No separate SEO feed, old browser substring selector, stale future inventory or synthetic class URL. This remains a publication dependency, not a reason to stop the source audit.
4. Add the shared editorial module schema/library after course/status mapping is validated. Factual modules need primary-source review; no medical text or invented freshness was generated in this recovery tranche.
5. Report the exact full eligible generation command, output directories and file estimate for scope approval under AGENTS.md before a sitewide builder runs. Target all eligible records; no arbitrary 500/1,000-page cap. Then validate the entire output, commit/push/merge/deploy through production and verify HTML/assets/sitemaps. GSC submission and monitored indexing remain outstanding.

This bounded backend recovery is complete and reviewable; issue #229's full implementation remains IN_PROGRESS. No release approval or full-corpus deployment is claimed. Preserve active #226 work and original dirty checkouts. This report, its JSON, the audit and tests are the substantive four-file change; a separate unique root receipt supplies exact implementation commit/PR and push verification.
