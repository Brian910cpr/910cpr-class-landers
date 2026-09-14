# Issue #229 — historical identity reconciliation

Assessment: September 14, 2026, America/New_York (UTC-04:00). Fixed source cutoff: `2026-09-14T00:00:00-04:00`.
State: bounded backend audit **validated locally**; full historical archive **IN_PROGRESS**, publication gated.
Branch: `codex/issue-229-identity-reconciliation-r2`, based on source-recovery PR #230 at `844218802483e75c177916ea7165577e8a01ce58`.

## What changed and why

The first recovery audit established 19,655 shared Registration Link identities but did not compare their historical/current class facts or inspect the seven unmatched historical HTML files. A shared identity alone is insufficient to copy newer class details onto an old URL or treat an elapsed class as completed.

Extended the existing `scripts/audit_historical_source_recovery.py` with `--identity-only`. It joins the two immutable source snapshots through validated Enrollware Registration Link IDs, distinguishes missing/ambiguous identities and invalid timing, compares exact course label/start/end/location values, inventories source status labels, and inspects actual enrollment anchors in the seven orphan pages. It emits aggregates and SHA-256 exception keys rather than private records. It neither creates public aliases nor changes canonical schedule truth.

The new mode is additive; the original six-source audit and its R1 artifacts remain intact. The original eight tests plus eleven new identity/privacy/ambiguity tests pass. No dependency, public builder, operational import, auth, course mapping or policy changed.

## Immutable inputs

| Source | Commit | Path | Blob |
|---|---|---|---|
| Historical corpus | `a7ff508d070ee7c23db0c955c04f05d03c4ef576` | `data/schedule.json` | `c5465df12ffcdad43b7930e12fb5b99a608f9fed` |
| Current archive snapshot | `abc7e9b1dd2d03039437721f80fe294190060c8a` | `data/schedule_all.json` | `ef77fd21e1db6becdb19b7f28abcdaf44eb08aaf` |
| Orphan HTML | historical commit above | Seven numeric `docs/classes/*.html` paths absent from that source's short IDs | Reproducible path/content digests in the JSON |

The current archive snapshot is a recovery source, not live canonical registry or current public availability proof. No live database/calendar was read. No spreadsheet was re-extracted; R1's workbook/Client provenance gates remain mandatory. Original source data remains in Git.

## Results

All 26,165 historical records receive one exclusive disposition:

| Disposition | Count |
|---|---:|
| Registration identity absent from current archive | 6,510 |
| Shared identity, valid timing, one or more exact source facts differ | 19,438 |
| Shared identity with invalid timing | 217 |
| Total | 26,165 |

There are 19,655 unique shared registration pairs and no ambiguous identities in these two actual snapshots. The current archive has 19,708 rows and adds 53 registration identities. Synthetic tests nevertheless require ambiguity to fail closed rather than selecting a first match.

Exact value differences across the 19,655 pairs overlap:

- Course label: **19,655**. This compares exact source strings. It is **not evidence that all courses changed** and does not establish semantic Course Master equivalence. Historical labels often contain HTML; no label content was exported. A separate diagnostic found that stripping HTML/normalizing display text also did not make these two snapshots' course labels equal. Course mapping still requires authoritative reconciliation.
- Start: **21**; end: **14**. The union is **22** pairs: eight start-only, one end-only and thirteen start-and-end changes.
- Location: **382** pairs; none overlaps the 22 timing-change pairs in this snapshot.
- Both historical and current timing are invalid in **217** shared pairs. Their identity match does not repair the invalid interval.

Exclusive exact-difference sets: `course=19,251`, `course+location=382`, `course+start=8`, `course+end=1`, `course+start+end=13`. These sum to 19,655 and include the invalid-timing pairs; valid label-only pairs number 19,034. Preserve the historical source facts pending adjudication instead of silently replacing them with the newer snapshot.

All **19,708** current source rows say `session_status=active`. That label does not establish cancellation or completion history. The audit does not infer that a historical class was taught, cancelled, or still bookable from `active`, elapsed time, or enrollment. `publication_authorized_count` remains **null**.

Each of the **seven** orphan HTML pages contains exactly one distinct validated Enrollware registration anchor. Every one of those identities is absent from **both** inspected source snapshots. Their HTML enrollment links therefore do not resolve the provenance gap. Keep these seven as exceptions pending another authoritative source; do not manufacture source records or 200 historical shells from HTML alone.

## Exact JSON review paths

File: `data/audit/issue229_identity_reconciliation_r2.json`.

- `sources[]`: exact commits, source paths and Git blob IDs.
- `exclusive_historical_dispositions`: mutually exclusive 26,165-row partition.
- `overlapping_changed_fields_in_unique_pairs`, `overlapping_unique_pair_flags`, `unique_pair_difference_sets`: exact comparison definitions/counts above.
- `current_source_status_labels`: source values from an explicit safe label allowlist; unknown raw labels become `unrecognized`.
- `orphan_dispositions`, `orphans_by_path_sha256`: all seven exception digests, HTML content digests, link counts and match counts. Keys hash the exact repository-relative path as UTF-8. HTML digests hash UTF-8 text after decoding the source with `utf-8-sig`; they are not Git blob IDs.
- `publication_authorized_count`: null, deliberately not a candidate count or numerical pilot cap.

Raw labels, client/location/instructor fields, registration URLs, participant details and orphan page contents are omitted. Re-running the audit against these immutable sources reproduces the joins without copying private rows into reports.

## Commands and validation

Only one generated audit output was authorized/reported before each execution; no public directory was written:

```powershell
python -B scripts/audit_historical_source_recovery.py --identity-only --current-ref abc7e9b1dd2d03039437721f80fe294190060c8a --as-of 2026-09-14T00:00:00-04:00 --output data/audit/issue229_identity_reconciliation_r2.json
python -B -m unittest discover -s tests -p test_audit_historical_source_recovery.py -v
```

Final results:

```text
Ran 19 tests in 0.004s
OK
SYNTAX: 2 Python files passed
JSON: totals, pair partitions, orphan keys and null publication gate passed
```

AST/in-memory compile checked the audit and test files without bytecode. Tests cover cross-namespace identity/equivalent instants, changed facts, duplicate links/IDs, invalid timing, missing identities, orphan matches/multiple links/unmatched sources, privacy and status non-authorization. JSON checks reconcile all historical/current/pair/orphan partitions. `git diff --check` passed. The initial run had 18 passing cases; the final 19-case run includes the added duplicate-source-ID orphan safeguard. The second audit execution updated the same single JSON after additional difference-set diagnostics; no unexpected generated files appeared.

Two exploratory commands needed correction: PowerShell literal wildcard arguments to `rg` were replaced with its `-g` option; an exploratory JSON reader assumed a list before selecting the snapshot's `sessions` member. The production audit mode already supports both forms and both full audit runs succeeded. These were diagnostic command errors, not altered source data or failed tests.

Exact intended files: the existing audit, its existing test file, this report and its sibling JSON. The separate unique root receipt records substantive commit/PR/push evidence. Original dirty checkouts, PR #230, prior receipts and active #226 work remain preserved. New sparse worktree initialization was inspected while `.git`-only/empty-index, then initialized from its pinned base; 700 intended root/scripts/tests/audit paths were populated without altering another worktree.

## Remaining implementation and release gates

1. Resolve the 22 changed-time pairs, 382 changed-location pairs, invalid intervals and seven orphan identities using private source evidence; retain exact historical facts and appropriate exceptions. Reconcile course labels through existing authoritative mappings. Neither enrollment nor the blanket `active` label is completion/cancellation evidence.
2. Build an allowlisted historical record projection using R1's restored Client provenance and public-location review, then extend the existing retained-page generator. Historical URLs should remain self-canonical when genuine records; invalid/unresolved records must not become fabricated shells.
3. Current options must reuse #228's canonical public/conflict decision. #140's credential-parity and occupancy/freshness proof still gates publication; no separate SEO feed or stale options. No current-offer count is claimed by this audit.
4. Report the exact full eligible builder command, directories and estimated file count for scope approval before sitewide generation. Full-corpus restoration remains the target, with privacy/canonical/schema/link/expired-booking validation and the editorial module library. No arbitrary cap is introduced.
5. Public HTML generation, merge, production deployment, archive sitemaps, Search Console submission and monitored indexing remain outstanding. This audit is reproducible local evidence, not a persistent archive proof. No real end-to-end archive generation/publication/refresh success timestamp, operational observer heartbeat or indexing-health proof exists from this tranche.

Next reviewer action: review this four-file increment against PR #230, use the exact JSON fields to select private source exceptions, and retain #228/#140 publication gates. Backend identity assessment is complete; the broader #229 work remains IN_PROGRESS. This does not clear ShiftCommander #214's independent release prerequisites.
