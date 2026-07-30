# ChatGPT handoff: certification-history importer

Branch: `codex/certification-history-importer`

Status: implemented and validated locally; representative dry run completed;
no Drive files modified; no Supabase writes; migration generated but not
applied; not deployed.

## Primary audit

The full source-format discovery report is:

`data/audit/assigned_ecards_source_discovery.md`

Key conclusions:

- `maxim_certification_history` remains the authoritative certification
  repository and already supports multiple credentials/history.
- The only proposed table is the lightweight private file-inspection ledger
  `certification_import_files`.
- Corporate customer and course are not reliable across all source rows.
- Filenames are recorded as provenance but are never authoritative matching
  evidence.
- Exact matching is deterministic. Fuzzy matching is review-only.

## Representative dry run

Command:

```powershell
python -m scripts.import_assigned_ecards `
  --folder-id 1mAKk554dqD3l-ufLSMp07dh_T07Ih_8o `
  --customer MAXIM `
  --dry-run `
  --manifest <representative-local-manifest.json> `
  --snapshot <empty-read-only-snapshot.json> `
  --output-report <local-output-path>
```

Exact summary:

```json
{
  "total_drive_files_discovered": 14,
  "files_inspected": 14,
  "supported_files": 14,
  "unsupported_files": 0,
  "files_skipped_as_unchanged": 0,
  "rows_parsed": 724,
  "duplicate_rows": 268,
  "duplicate_status_rows": 268,
  "exact_matches": 0,
  "probable_matches": 0,
  "ambiguous_matches": 0,
  "unmatched_rows": 184,
  "invalid_rows": 272,
  "non_maxim_rows": 0,
  "proposed_file_ledger_upserts": 14,
  "proposed_certification_history_inserts": 0,
  "proposed_employee_profile_updates": 0,
  "skipped_older_ecards": 0,
  "skipped_earlier_expiration_dates": 0,
  "parsing_errors": 0
}
```

This sample intentionally used an empty Supabase matching snapshot because no
local Supabase service credential was available. It validates parsing,
normalization, duplicate classification, error preservation, and all three
report formats. It does **not** establish production match counts. A complete
read-only dry run needs `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.

The authenticated Drive connector confirmed that the folder exceeds the
1,000-file first page and supplies a continuation token. The command-line
Drive client implements full `nextPageToken` pagination, but a Drive
read-only token/service-account credential is required to run that listing
outside the connector session.

## Complete production-backed read-only dry run

The complete follow-up run is summarized in:

`data/audit/certification_history_production_readonly_summary.md`

It used three authenticated Drive metadata pages (1,069 files), a SELECT-only
production snapshot (339 active profiles and 15 history rows), and a private
local download cache. It produced 25 deterministic exact matches, 74
ambiguous matches, 2,535 unmatched rows, 16 invalid rows, 24 proposed history
inserts, 15 proposed occurrence reconciliations, and 19 proposed legacy profile
projections. No production writes occurred.

The importer is not ready for `--apply`: all proposed history inserts are
currently labeled `current`, including records as old as 2022, while none has
a source expiration date. Status/expiration policy needs review first.

## Important files

- `scripts/import_assigned_ecards.py` — CLI and safety gate.
- `scripts/certification_import/README.md` — operation, credentials, matching,
  duplicate, and deployment behavior.
- `scripts/certification_import/drive.py` — read-only paginated Drive access.
- `scripts/certification_import/parsers.py` — CSV/XLS/XLSX/XLSB/ODS parser.
- `scripts/certification_import/normalize.py` — aliases and normalization.
- `scripts/certification_import/matching.py` — deterministic matching and
  review-only fuzzy suggestions.
- `scripts/certification_import/reconcile.py` — history proposals and guarded
  legacy profile projections.
- `scripts/certification_import/reporting.py` — JSON, Markdown, HTML dashboard.
- `supabase/migrations/20260730194932_certification_import_file_ledger.sql` —
  review-only migration; not applied.
- `tests/test_certification_history_importer.py` — invented fixtures only.
- `data/audit/assigned_ecards_source_discovery.md` — primary discovery report.

## Validation

Syntax:

```text
python -m compileall -q scripts/certification_import \
  scripts/import_assigned_ecards.py \
  tests/test_certification_history_importer.py
Exit code: 0
```

Tests:

```text
..................
----------------------------------------------------------------------
Ran 18 tests in 0.054s

OK
```

`git diff --check` exited 0.

## Review focus

1. Approve or revise the course alias/compatibility policy before real
   matching.
2. Decide how `UNKNOWN` course rows can be resolved from an authoritative
   source; they intentionally cannot auto-match now.
3. Review the guarded `maxim_employee_profiles` legacy projection. History
   inserts and profile projection should remain separable at apply time.
4. Review RLS/grants and the file-ledger fields before applying the migration.
5. Provide scoped read-only Drive access and the Supabase service-role
   credential in environment variables, then review a full dry run.
6. Only after explicit approval should the production apply implementation be
   added/enabled.

## Intentionally absent

- No migration execution.
- No production database writes.
- No Edge Function deployment.
- No site build/publish.
- No real participant fixtures in the repository.
- No credentials or secret values in source or reports.
