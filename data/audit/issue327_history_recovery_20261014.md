# Issue 327 — NHCSO history recovery

Timestamp: 2026-10-14 America/New_York. Branch: codex/issue327-history-20261014.
Baseline: 8e08de5ca5eb2525bf578bd7ace77971d39efd5b.
State: BUILT; production rollout BLOCKED pending backend validation and authenticated end-to-end proof.

## Root cause and source

The pre-lockdown portal at commit 1b949ba8df3d2607820c6bbb9763595e5c9f6fb6 scraped `/admin/nhcso-training-workspace-v6.html`, matched `const history=[...]`, and evaluated its contents with `new Function`. Aggregate extraction with Python `ast.literal_eval` found 69 six-field summaries, date range 2022-09-12 through 2026-08-12, zero duplicate IDs. No historical record values were persisted or republished.

Security commit ea88f2ec46f9d9b5e5825118afaa054a366db595 at 2026-09-29T22:58:16Z removed public training data. Current prototype paths contain restricted placeholders. The restored authenticated portal deliberately made `loadHistory()` empty; `refresh()` only uses `list_classes`. This was a lost feed during security remediation, not a lack of historical inventory. PR #326 is merged; its lifecycle semantics are preserved. Open PR #324 owns additional lifecycle/unlock changes and its stale test repair; this branch does not change those functions.

Authoritative replacement: existing `class_sessions`, joined through `organization_id` to `organizations.organization_key=hist_org_9c5e13364df2bf5e339e75f0`, `source=enrollware_history`, `record_scope=historical`, and the existing course FK. The key was verified against the NHCSO organization in a read-only authenticated query. No broad label matching is used in the implementation.

Production read-only aggregate query result:
```json
{"historical_count":80,"distinct_external_ids":80,"live_overlap":0,"missing_timezone":0,"first_local_date":"2022-02-16","last_local_date":"2026-08-19"}
```
Seven `nhcso_classes` records exist, dates 2026-08-26 through 2026-10-07. Historical inventory has course and organization relationships for all 80 records. This removes the public prototype dependency and promotes the already ingested canonical session truth; it does not add another catalog or import pipeline.

## Implementation

- `supabase/functions/nhcso-workspace/history.js`: exact organization/source/scope filters, 40-record pages, stable date/ID ordering, summary-only projection, timezone-aware local date/time, explicit errors and next offset.
- `supabase/functions/nhcso-workspace/index.ts`: new `list_history` action AFTER existing authorization, offset validation, existing no-store response; no changes to live list or lifecycle logic.
- `docs/corp/nhcso/index.html`: authenticated-only loading concurrent with live list, older-page button, explicit count/error/retry, existing scroll container, separate gray legacy records, duplicate suppression against live class numbers. History selection opens a read-only summary and never clears or populates the editable class form. No per-class fetch, roster, credential, document, enrollment link, or new public history asset.
- `tests/nhcso_history.test.cjs`: six targeted tests.
- `tests/nhcso_history_browser.py`: reproducible synthetic-only Chromium proof; all requests intercepted, no production sign-in or writes.

No generator, migration, ingestion, database write, merge, deployment, or asset change. HTML changes are inline; existing CSS/JS URLs are unchanged and no changed external asset needs cache versioning.

## Validation and limitations

`node --test tests/nhcso_history.test.cjs`: tests 6, pass 6, fail 0. All inline scripts parse.

`python -B tests/nhcso_history_browser.py`:
```text
{'result': 'PASS', 'historical_cards': 80, 'pagination_offsets': [0, 40], 'scroll_metrics': {'height': 396, 'scroll': 8508, 'overflow': 'auto'}, 'page_errors': [], 'writes': 0}
```

`npx --yes deno check --check-js supabase/functions/nhcso-workspace/history.js`: PASS.
`git diff --check`: PASS.

`python -B -m unittest discover -s tests -p test_nhcso_roster_workflow.py`: 8 tests, 7 pass, 1 existing failure. `test_finalization_is_confirmed_and_enforced_by_the_backend` expects `Type the complete class number to continue`; that phrase is also absent at baseline. The repair already exists in PR #324; it was not duplicated here.

`npx --yes deno check supabase/functions/nhcso-workspace/index.ts`: FAIL, five existing errors. The unmodified baseline extracted to a local temporary `.ts` file gives the same five errors:
- baseline lines 454 and 612 (branch 455 and 613): TS2551, `.catch` on a Postgrest builder; this is also a possible runtime issue in existing audit writes.
- baseline line 692 (branch 693): TS2339, `person.active` on inferred instructor array.
- baseline line 693 (branch 694), twice: TS2339, `display_name` on inferred instructor array.

No authenticated production/browser restoration proof has occurred. Supabase project inventory and aggregate SQL were remotely read only. All code and rendered behavior validation was local with synthetic data. Supabase project branch inventory currently returns `[]`; no isolated branch was provisioned and no cost was incurred. Do not describe this restoration as PROVEN, MONITORED, or HEALTHY.

## Rollout/proof contract

Expected outcome: authorized NHCSO user can browse all canonical historical summaries without granting edit operations on them. Success evidence: authenticated endpoint returns two stable pages totaling 80 unique IDs and browser scrolls through the final record; unsigned and unrelated-role requests are rejected; live lifecycle behavior remains intact.
Cadence: on sign-in, then explicit load-older action. Last successful real end-to-end proof: none for this restoration. Last local synthetic proof: this dispatch.
Failure condition: non-2xx history response, missing/wrong organization, duplicate/missing pages, UI inaccessible history. Immediate observer: visible history count/status/retry; automated regression tests provide local proof only. Observer health: no deployed automated end-to-end observer was added or proven. Brian must not be considered the routine monitor; operational monitoring remains unresolved until rollout proof is integrated into the workspace health boundary.
Recovery: inspect existing authorized endpoint errors and canonical session counts, then redeploy only this function after baseline errors are resolved; do not restore public embedded history. Escalate only account/session or staging provisioning decisions that cannot be handled within existing access.

Next concrete action: coordinate the five existing backend validation errors with their owning stream, validate this endpoint using an authorized isolated environment/session, then deploy the NHCSO function before publishing the HTML and verify production HTML plus authenticated browsing. Do not merge/deploy PR #372. No account-level action was requested during this dispatch.

## Hygiene and queue

Primary E:/GitHub/910cpr-class-landers dirty work was preserved. An isolated named branch/worktree was used. Unrelated `docs/Earl/index.html` and `docs/Jackson/index.html` became dirty in this worktree without being edited by this task; they are not staged. No cleanup/reset/rebase occurred. All open [CODEX] issues were swept; existing assignments and the primary Studio stream were preserved. No independent unassigned, low-risk backend item was selected to avoid duplicating the many active issue branches. Backend history work continued independently of the lifecycle UI stream. No preexisting #327 PR was found; #324 concerns #325 and is preserved separately.
