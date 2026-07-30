# Certification-history reconciliation importer

This package parses certification exports from Google Drive and reconciles
them against `maxim_certification_history` and active
`maxim_employee_profiles`. It is dry-run by default. Fuzzy names can produce
review suggestions but can never produce writes.

## Normal dry run

```powershell
python -m scripts.import_assigned_ecards `
  --folder-id 1mAKk554dqD3l-ufLSMp07dh_T07Ih_8o `
  --customer MAXIM `
  --dry-run `
  --output-report data/private/certification-import/certification_history_import
```

The command always emits `.json`, `.md`, and `.html` reports. The HTML file is
the human-readable audit dashboard. Reports contain participant names, email
addresses, profile IDs, and certification details. Keep them under
`data/private/` (already Git-ignored) or another access-controlled directory.

Useful filters:

```text
--limit N
--file-id DRIVE_FILE_ID
--since ISO_TIMESTAMP
--manifest PATH
--snapshot PATH
--output-report PATH
```

`--manifest` and `--snapshot` make a fully local/repeatable dry run possible.
The Drive code lists with page size 1,000, follows every continuation token,
caches downloaded files by immutable file ID, and never modifies Drive.

## Credentials

- Drive listing: `GOOGLE_DRIVE_ACCESS_TOKEN`, or
  `GOOGLE_APPLICATION_CREDENTIALS` pointing to credentials with
  `drive.readonly` access.
- Supabase matching snapshot: `SUPABASE_URL` and
  `SUPABASE_SERVICE_ROLE_KEY`.

Do not print, commit, or include those values in reports. The service-role key
is required because the matching tables and proposed ledger are private.

## Safety gates

- No flag means dry-run behavior.
- `--apply` additionally requires
  `--confirm-apply CERTIFICATION-HISTORY`.
- Production apply intentionally remains unimplemented until the migration,
  dry-run, and data-quality report are approved.
- The migration is not run by this command.
- No Edge Function redeployment is required; this is a standalone importer.
- `/corp/maxim.html` reads Supabase at runtime, so approved database updates
  would be visible without a site build or publish step.

## Deterministic matching

Automatic exact matches are considered in this order:

1. Existing exact eCard with compatible required course.
2. Unique exact normalized email with compatible required course.
3. Unique exact normalized name, explicit compatible customer, and compatible
   course.
4. Unique exact normalized name with compatible course and exact
   scheduled/prior class date.

Duplicate or conflicting candidates are ambiguous. Fuzzy normalized-name
similarity is evaluated only when course and date are compatible, and it is
always labeled `probable_match` for human review. Fuzzy matching never
proposes a certification insert or employee-profile update.

## Duplicate protection

- File IDs and modification metadata support incremental inspection.
- SHA-256 detects byte-identical renamed uploads.
- Semantic row fingerprints detect duplicate rows/files without relying on a
  filename.
- eCard codes are unique in `maxim_certification_history`; a second occurrence
  in one batch is classified `duplicate`.
- Existing history eCards are skipped on rerun.
- A different, newer eCard may be preserved as a new history credential.
- Older/equal expirations, older class dates, incompatible courses, and
  unproven replacement cards never overwrite the profile projection.
