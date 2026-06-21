# Local Private Data Migration Plan

Created: 2026-06-20

This is a report-only plan. No files were moved, deleted, untracked, redacted, committed, deployed, or regenerated as part of this plan.

## 1. Current Dependency Map

The repo currently tracks several live/operational Enrollware exports. These files are useful locally, but they are not safe long-term source files because they may contain student/contact, registration, roster, or operational schedule data.

### `data/raw/students_raw_live.csv`

Current status: tracked by git.

Risk: high. This is a live student export path and is expected to contain student names, emails, phone numbers, registration records, and related enrollment data.

Current readers/references:

| File | Dependency |
| --- | --- |
| `scripts/build_sessions_current.py` | Default `--students-csv data/raw/students_raw_live.csv`; used to enrich current sessions with student/enrollment data. |
| `docs/STACK_ARCHITECTURE.md` | Documents it as live student/export data used for enrollment counts. |
| `docs/STACK_RUNBOOK.md` | Documents it as an input for current-session generation. |
| `docs/910cpr_lander_scheduler_punchlist.md` | Flags possible drift between this file, class exports, generated JSON, public feeds, and generated HTML. |

If removed from tracking before script changes: clean checkouts may still run `scripts/build_sessions_current.py`, but the script will look for a missing live CSV unless an operator supplies an alternate path.

### `data/raw/classes_raw_live.csv`

Current status: tracked by git.

Risk: high. This is a live class export path and may contain operational class/session metadata, Enrollware IDs, instructor/location details, and linked registration state.

Current readers/references:

| File | Dependency |
| --- | --- |
| `scripts/build_sessions_current.py` | Default `--classes-csv data/raw/classes_raw_live.csv`; used to patch/enrich sessions. |
| `docs/STACK_ARCHITECTURE.md` | Documents it as a live class export used to patch/enrich sessions. |
| `docs/STACK_RUNBOOK.md` | Documents it as an input for current-session generation. |
| `docs/910cpr_lander_scheduler_punchlist.md` | Flags possible drift between this file, student exports, generated JSON, public feeds, and generated HTML. |

If removed from tracking before script changes: session enrichment may degrade or fail depending on how the command is invoked.

### `data/Class Report.xlsx`

Current status: tracked by git.

Risk: high. This is the authoritative local Enrollware class report. It may contain live roster/session details and operational scheduling data.

Current readers/references:

| File | Dependency |
| --- | --- |
| `scripts/build_sessions_current.py` | Fallback candidate and default `--class-report data/Class Report.xlsx`. |
| `scripts/build_schedule_future.py` | Fallback candidate and default `--class-report data/Class Report.xlsx`; hard reconciliation source. |
| `scripts/audit_stale_sessions.py` | Fallback candidate and default `--class-report data/Class Report.xlsx`. |
| `scripts/check_schedule_integrity.py` | Fallback candidate for schedule integrity checks. |
| `scripts/prebuild_cleanup_validate.py` | Fallback candidate and default `--class-report data/Class Report.xlsx`; invokes session/schedule builders. |
| `scripts/hub_utils.py` | `RAW_REPORT = ROOT / "data" / "Class Report.xlsx"`. |
| `scripts/build_appointment_offer_inventory.py` | `CLASS_REPORT_PATH = ROOT / "data" / "Class Report.xlsx"`. |
| `scripts/build_all_v4.py` | Candidate class report file: `Class Report.xlsx`. |
| `scripts/build_schedule_json.py` | Requires `--class-report`; runbook examples pass `data/Class Report.xlsx`. |
| `docs/DATA_FLOW_MAP.md` | Documents it as authoritative session list and registration-link source. |
| `docs/STACK_ARCHITECTURE.md` | Documents it as authoritative session list. |
| `docs/STACK_RUNBOOK.md` | Documents it across build, stale-session, and scheduler workflows. |
| `docs/enrollware_sync.md` | Uses it as `--master data\Class Report.xlsx`. |
| `docs/910cpr_lander_scheduler_punchlist.md` | Flags drift risk. |
| `docs/data/schedule_future.json` | Contains a source metadata reference to the local path. |
| `docs/control-center/**` | Public/admin-facing static control center text references `data/Class Report.xlsx` as a source file. |
| `docs/courses/*.html` | Generated public pages mention “Live course hub built from Class Report.xlsx.” |

If removed from tracking before script changes: most schedule-generation, stale-session auditing, integrity checking, and appointment-offer inventory workflows may fail on clean checkout unless the operator passes a local file path.

### `data/enrollware_export.xlsx`

Current status: tracked by git.

Risk: high. This is an Enrollware export path used for sync/diff workflows and may contain live operational data.

Current readers/references:

| File | Dependency |
| --- | --- |
| `scripts/enrollware_sync.py` | Default `DEFAULT_EXPORT_PATH = Path("data/enrollware_export.xlsx")`; used by dry-run/reconcile flows. |
| `scripts/build_all_v4.py` | Course-export candidate: `enrollware_export.xlsx`. |
| `docs/enrollware_sync.md` | Uses it as `--enrollware-export data\enrollware_export.xlsx`. |
| `docs/STACK_ARCHITECTURE.md` | Lists it in the Enrollware/export data area. |
| `docs/STACK_RUNBOOK.md` | Documents it as an expected candidate/source. |

If removed from tracking before script changes: Enrollware sync dry-run/reconcile workflows may fail unless the operator supplies a private export path.

### `data/runtime/enrollware_sync/**`

Current status: tracked by git.

Tracked files currently include:

| File |
| --- |
| `data/runtime/enrollware_sync/20260427-074805/desired_sessions.json` |
| `data/runtime/enrollware_sync/20260427-074805/sync_report.json` |
| `data/runtime/enrollware_sync/20260427-074805/sync_report.md` |
| `data/runtime/enrollware_sync/playwright_scaffold_20260427-074844.json` |
| `data/runtime/enrollware_sync/reconciliation_20260427-074902.json` |
| `data/runtime/enrollware_sync/reconciliation_20260427-074950.json` |

Risk: high. This is runtime output from sync/reconcile workflows. It may include desired-session plans, reconciliation state, operational class IDs, and source-derived data.

Current readers/references:

| File | Dependency |
| --- | --- |
| `scripts/enrollware_sync.py` | Default `DEFAULT_OUTPUT_DIR = Path("data/runtime/enrollware_sync")`; writes dry-run, scaffold, and reconciliation outputs. |
| `docs/enrollware_sync.md` | Documents runtime output and follow-up commands using `data/runtime/enrollware_sync/<timestamp>/`. |
| `docs/910cpr_lander_scheduler_punchlist.md` | Lists it as hot-sync output area. |

If removed from tracking before script changes: existing commands still write to this path locally. The main risk is not runtime breakage; the main risk is future accidental commits of fresh sync outputs.

## 2. Proposed Private Local Paths

Use local-only private paths for live data. These paths should be ignored by git and never required from a clean checkout.

| Current tracked path | Proposed private path |
| --- | --- |
| `data/raw/students_raw_live.csv` | `data/private/raw/students_raw_live.csv` |
| `data/raw/classes_raw_live.csv` | `data/private/raw/classes_raw_live.csv` |
| `data/Class Report.xlsx` | `data/private/enrollware/Class Report.xlsx` |
| `data/enrollware_export.xlsx` | `data/private/enrollware/enrollware_export.xlsx` |
| `data/runtime/enrollware_sync/**` | `data/private/runtime/enrollware_sync/` |

Recommended path precedence for future script changes:

1. Explicit CLI path, for example `--class-report`, `--students-csv`, `--classes-csv`, or `--enrollware-export`.
2. Explicit environment variable, for example `LANDER_CLASS_REPORT_PATH`, `LANDER_STUDENTS_CSV_PATH`, `LANDER_CLASSES_CSV_PATH`, or `LANDER_ENROLLWARE_EXPORT_PATH`.
3. Private local default under `data/private/...`.
4. Legacy tracked path during migration only.
5. Sanitized fixture only when the command is clearly running in test/demo/report-only mode.

## 3. Proposed Tracked Placeholders

Add safe tracked placeholders after private-path support exists:

| Placeholder | Purpose |
| --- | --- |
| `data/README_PRIVATE_DATA.md` | Explains where operators should place local Enrollware exports and why real files are not tracked. |
| `data/raw/README.md` | Explains that `data/raw/` contains only sanitized examples in git; live exports belong under `data/private/raw/`. |
| `data/raw/sample_students_synthetic.csv` | Synthetic student export fixture with fake names, fake emails, fake phones, fake IDs, and no real registration data. |
| `data/raw/sample_classes_synthetic.csv` | Synthetic class export fixture with fake or public-safe class examples and no live roster data. |

Optional later placeholder:

| Placeholder | Purpose |
| --- | --- |
| `data/private.example/README.md` | Shows the intended private directory shape without making `data/private/` itself tracked. |

Do not add real live rows to placeholders. If a fixture needs Enrollware course IDs for deterministic URL or mapping tests, use only non-personal public course IDs and synthetic person/contact values.

## 4. Proposed Script Behavior

Future script changes should preserve local operator usefulness while removing any requirement that Git contain live PII.

Recommended behavior:

- Scripts prefer private local files when present.
- CLI-provided paths always win over defaults.
- Environment variables provide a machine-local override without editing repo files.
- Legacy tracked paths remain temporarily readable during Phase A and Phase B only.
- Tests and demos use sanitized fixtures or temp files.
- Commands that require live data fail with a direct message when live data is missing.
- Report-only commands may continue with sanitized fixtures only if the operator explicitly opts into demo mode.
- Scripts should not silently treat missing live data as “empty schedule” unless that mode is explicitly named and safe.
- Scripts should not regenerate public pages from stale or synthetic data unless the command says it is a demo/test build.

Suggested helper behavior for later implementation:

```text
resolve_live_data_path(kind, cli_path=None, env_var=None, private_default=None, legacy_default=None, fixture_default=None, mode="live")

Resolution order:
1. cli_path if provided and exists
2. env_var value if set and exists
3. private_default if exists
4. legacy_default if exists and migration compatibility is enabled
5. fixture_default only for tests/demo/report-only
6. fail with a helpful error
```

Suggested helpful error example:

```text
Missing required live Class Report.
Expected one of:
- --class-report <path>
- LANDER_CLASS_REPORT_PATH
- data/private/enrollware/Class Report.xlsx

Real Enrollware exports are intentionally not tracked in git.
See data/README_PRIVATE_DATA.md.
```

## 5. Proposed `.gitignore` Rules

Add these only after confirming they do not conflict with intended safe fixtures:

```gitignore
# Private local Enrollware/student exports
data/private/

# Live Enrollware raw exports
data/raw/students_raw_live.csv
data/raw/classes_raw_live.csv
data/raw/*_raw_live.csv

# Live Enrollware workbooks
data/Class Report.xlsx
data/class-report.xlsx
data/enrollware_export.xlsx
data/*enrollware*export*.xlsx

# Enrollware sync runtime outputs
data/runtime/enrollware_sync/
```

If the repo needs to keep `data/runtime/` structure visible, track a non-sensitive README outside ignored runtime output, such as `data/runtime/README.md`, not the generated sync files.

## 6. Safe Migration Phases

### Phase A: Add Private Path Support

Goal: update scripts to work from private local paths without removing any tracked live files yet.

Proposed changes:

- Add a small shared path resolver or consistent local helper.
- Update `scripts/build_sessions_current.py`:
  - prefer `data/private/enrollware/Class Report.xlsx`
  - prefer `data/private/raw/classes_raw_live.csv`
  - prefer `data/private/raw/students_raw_live.csv`
  - preserve CLI overrides
  - keep legacy paths temporarily
- Update `scripts/build_schedule_future.py`, `scripts/audit_stale_sessions.py`, `scripts/check_schedule_integrity.py`, `scripts/prebuild_cleanup_validate.py`, `scripts/hub_utils.py`, and `scripts/build_appointment_offer_inventory.py` to prefer the private Class Report path.
- Update `scripts/enrollware_sync.py`:
  - prefer `data/private/enrollware/Class Report.xlsx`
  - prefer `data/private/enrollware/enrollware_export.xlsx`
  - write runtime outputs to `data/private/runtime/enrollware_sync/`
  - preserve explicit CLI `--output-dir`.
- Keep all current live files in place during this phase.

Validation:

- Run existing unit tests.
- Run report-only/syntax checks.
- Confirm commands still work with current legacy files.
- Copy local live files to private paths manually for a dry-run and confirm scripts prefer the private copies.

### Phase B: Add Sanitized Fixtures and Placeholders

Goal: make clean checkouts understandable and testable without live data.

Proposed changes:

- Add `data/README_PRIVATE_DATA.md`.
- Add `data/raw/README.md`.
- Add `data/raw/sample_students_synthetic.csv`.
- Add `data/raw/sample_classes_synthetic.csv`.
- Update tests to use synthetic fixtures or temp files only.
- Update docs/runbooks to describe private local data paths and the intentional absence of live exports from git.

Validation:

- Run unit tests on a checkout where live files are absent.
- Confirm scripts that require live data fail with helpful messages.
- Confirm demo/report-only commands use synthetic fixtures only when explicitly requested.

### Phase C: Stop Tracking Live Files

Goal: remove live/private exports from future commits while preserving local copies on disk.

Only after Phase A and Phase B are complete, run the approved untracking commands:

```powershell
git rm --cached -- data/raw/students_raw_live.csv
git rm --cached -- data/raw/classes_raw_live.csv
git rm --cached -- "data/Class Report.xlsx"
git rm --cached -- data/enrollware_export.xlsx
git rm --cached -r -- data/runtime/enrollware_sync
```

Then add/confirm `.gitignore` rules.

Important: `git rm --cached` removes files from git tracking, not from the local working directory. Operators should still copy or move their live files into `data/private/...` before relying on the new defaults.

Validation:

- `git status --short` should show the intended tracked removals plus `.gitignore`/placeholder/script updates only.
- `git ls-files` should no longer show the live export paths.
- Unit tests should pass without live files in tracked paths.
- Live local commands should work when private files exist.

### Phase D: Optional History Cleanup Decision Later

Goal: decide whether to rewrite repository history to purge previously committed PII.

This is intentionally separate from the first containment work.

Considerations:

- History rewriting is disruptive and requires coordination for all clones/remotes.
- If this repo has ever been public or broadly shared, assume historical exposure cannot be fully undone.
- If history cleanup is approved, use a deliberate tool/process such as `git filter-repo` or BFG Repo-Cleaner, then rotate any exposed secrets if any are found.
- Do not perform history cleanup as part of routine script migration.

## 7. Risk Notes

### Scripts likely to break if files are untracked too early

| Script | Risk |
| --- | --- |
| `scripts/build_sessions_current.py` | Defaults to current tracked live paths for Class Report, classes CSV, and students CSV. Clean checkout without private-path support may fail or lose enrichment. |
| `scripts/build_schedule_future.py` | Defaults to `data/Class Report.xlsx`; schedule future build may fail. |
| `scripts/audit_stale_sessions.py` | Defaults to `data/Class Report.xlsx`; stale-session audit may fail. |
| `scripts/check_schedule_integrity.py` | Searches current Class Report paths; integrity checks may fail or be incomplete. |
| `scripts/prebuild_cleanup_validate.py` | Defaults to `data/Class Report.xlsx` and invokes builders; prebuild validation may fail. |
| `scripts/hub_utils.py` | Hard-coded `RAW_REPORT` points to `data/Class Report.xlsx`; hub utility behavior may fail or use stale assumptions. |
| `scripts/build_appointment_offer_inventory.py` | Hard-coded Class Report path; appointment-offer inventory may fail. |
| `scripts/enrollware_sync.py` | Defaults to tracked master/export paths and writes to tracked runtime area; sync dry-run/reconcile may fail or keep creating commit-risk outputs. |
| `scripts/build_all_v4.py` | Looks for workbook candidate names in `data/`; full build may miss expected source workbooks. |

### Public-output risk

This plan does not modify public pages. Existing public docs/generated output currently reference `Class Report.xlsx` as a source label and include public session metadata. The major live PII containment risk is the tracked live/raw data files, not the source-label text itself. A separate public-output review should still be completed before deployment changes.

### Operational risk

Do not remove or untrack live files until private-path support is implemented and validated. The build/sync tooling currently assumes these files exist at their legacy paths. Removing them first would trade a privacy problem for brittle local operations.

## Recommended Next Action

Implement Phase A only:

1. Add private path resolution support to the dependent scripts.
2. Keep legacy paths readable during the transition.
3. Do not remove tracked live files yet.
4. Validate that scripts prefer `data/private/...` when private files exist.

After Phase A passes, add sanitized fixtures/placeholders in Phase B, then untrack live files in Phase C.
