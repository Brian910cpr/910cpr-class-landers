# Issue 334 — native Location proof and guarded repair R56

Timestamp: 2026-10-14T08:30:00Z (UTC).
Branch: `codex/issue334-location-proof-20261014-r56`.
Substantive pushed commit: `7abecacd9da7976493b4326641c92f203e46e412`.
Receipt commit: branch tip recorded on originating issue and final response after push.
State: PR_OPEN; production release BLOCKED on current probe/review and specific output-scope approval.
PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/393 (draft).
Execution acknowledgement: https://github.com/Brian910cpr/910cpr-class-landers/issues/334#issuecomment-6164055770

## Material progress

Authenticated SELECT-only Supabase access was available in this dispatch. It resolves
the previous provenance uncertainty: native session `dfa08088-1266-4dd6-ad7d-14856b7f845a`
has Location FK `fd44e20f-af86-4198-ab7c-fa13dad6a7fd`, joined canonical name
`910CPR Office - Shipyard Blvd`, key `910cpr-office-shipyard`. Its source label is
`4018 Shipyard Blvd, Room B, 910CPR Office`. `resource_id` is null; Location resource
SELECT returns `[]`. Venue proof is now acquired; Room B identity is not proven.

The patch adds only a venue alias, preserving raw label/occupied interval. A related
publication relevance-filter bug was found and fixed: venue-only reservations from
another instructor must receive the existing conservative primary-room fallback
before filtering, as they already do in build_shadow. Explicit known Room A/C
assignments remain distinct; unknown offsite travel fails closed. No DB write,
room creation, new travel rule, source freshness extension or appointment invention.

## Exact review files and validation

Primary report (full authenticated query, findings, release scope and rollback):
`data/audit/issue334_location_r56.md`.
Structured authenticated facts and pinned before/after:
`data/audit/issue334_location_r56_proof.json`.
Read-only current public audit:
`data/audit/issue334_location_r56_live.json`.
Important source/config/tests:
`data/config/location_resource_map.json`, `scripts/layered_publication_adapter.py`,
`tests/test_layered_publication_adapter.py`, `tests/test_layered_selector_adapter.py`.
These seven files plus this root receipt are the complete intended commit scope.

```text
python -B -m unittest tests.test_layered_location_aliases tests.test_layered_selector_adapter tests.test_layered_publication_adapter tests.test_layered_publication_pipeline tests.test_family_publication_coverage tests.test_layered_resource_readiness -q
Ran 55 tests in 6.692s
OK
```

Python AST, JSON and whitespace validation pass. Pinned synthetic fixture:
one source/window, before evaluated0/failed1/offers0; after evaluated1/failed0/offers6
at three starts, occupied12:00-14:00 preserved. Calculation -> public selector JSON
and HTML reference verified locally. Same/other-instructor blocking and explicit
Room A negative regression pass. No current-source regenerated page or production
after-count claimed. Test-development assertion errors were corrected before final
passing suite; full context in report.

Read-only live audit at08:23:45Z intentionally fails coverage: all8 families
191input/189evaluated/2failed windows; two November3 failures. BLS3622offers/88dates
(3612dynamic/10seated); HS7565/88; both unexpired in sample. ACLS/PALS seated-only
payload timestamps expired; retained seats do not prove dynamic freshness.
No current browser/booking/payment test performed. No participant PII committed.

## Status, blockers and exact next action

This repair is BUILT and validated locally; prior publication PROVEN; overall
HEALTHY unestablished. Last prior accepted full customer proof is the direct P0
release report at `05f04ad67a20484be3d0556bb1d39f467361c5f9`,
`data/audit/issue334_direct_p0_release_20261012.md`; this dispatch adds pre-repair
live evidence and local proof only.

Next ChatGPT action: review draft #393 and exact evidence, obtain a current
authenticated all-family read-only `v2_release_probe=true` on this branch, verify
zero failed windows and preserved actual November3 occupied interval, then obtain
the smallest specific production release approval. Report gives existing normal
publisher scope:17HTML +8familyfeeds plus workflow-listed schedule/admin/ical/
native-anchor/snapshot/audit/status outputs, estimated40-60changed generated/state
files. No complete build chain proposed. Stop for >10unexpected files. Following
approved release, verify live family JSON, affected rendered choices and changed
assets/registration targets, and consecutive renewals before expiry. No merge or
deployment performed by this dispatch. #334 must remain open.

Independent cloud recovery remains BLOCKED: health URL variable GET HTTP404;
existing owner-level repository-restricted Actions read/write credential must be
stored only in encrypted Cloudflare `GITHUB_ACTIONS_TOKEN`, then configure/verify
health and natural recovery. No secret contents read or unchanged activation retry.
Latest sampled natural observer38514856448 failed; sustained five-minute cadence
unproven. Expected outcome: continuously legal public bookings; cadence local5min,
effective source lease may15min. Failure: stale feed, failed/unevaluated windows or
stale observer. Observer: scheduled public-booking audit/supervisor; its multi-hour
gaps and absent cloud health remain unresolved. CYBERPC awake/online/login remains
an operational dependency; Brian must not become routine monitoring.

## Preservation and persistence

Persisted locally, changed in isolated repo worktree, substantive commit pushed.
Receipt committed/pushed and GitHub Contents verification required before exit.
Base: `47a10dc2d2c6853a9fe88e96f4fb7b485334b07e`.
Original dirty checkout preserved. Inherited case-collision modifications to
`docs/Earl/index.html` and `docs/Jackson/index.html` remain unstaged and excluded.
No generators affecting public output, broad rebuild, competing refresh, task
mutation, infrastructure change, merge or deployment. Draft #372 untouched.

Queue/open-PR sweep: existing #383 scheduling, #387 checkout, #389 documents,
#388finance and fleet/preflight streams preserved. No existing open exact venue
repair PR to reuse, so one narrowly scoped draft #393 created; no competing deep
refactor. No safe independent unassigned backend quick win established. Do not
restart #297's unchanged authoritative roster acquisition path. Never used
`ops/handoff/next_task.md`; no Codex_Read files created or renamed. No intentionally
untracked assignment files; outside-repo PR body is temporary CLI input only.
