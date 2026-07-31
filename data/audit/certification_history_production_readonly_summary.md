# Certification-history production read-only dry run

Run date: 2026-07-30

Status: completed against a connector-derived read-only production Supabase
snapshot and the complete current Drive folder listing. No database or Drive
write occurred. No migration, deployment, merge, or `--apply` implementation
occurred.

## Inputs

- Drive folder ID: `1mAKk554dqD3l-ufLSMp07dh_T07Ih_8o`
- Drive pagination: 3 pages, 1,069 files
- Active production employee profiles: 339
- Existing production certification-history rows: 15

## Results

| Metric | Count |
|---|---:|
| Drive files discovered | 1,069 |
| Supported files | 1,068 |
| Unsupported files | 1 |
| Files skipped as byte-identical duplicates | 147 |
| Unique files inspected | 921 |
| Sheets inspected | 921 |
| Source rows | 3,019 |
| Valid certification rows | 2,634 |
| Invalid rows | 16 |
| Semantic/eCard duplicates | 369 |
| Exact matches | 25 |
| Ambiguous matches | 60 |
| Existing-eCard conflicts | 14 |
| Unmatched rows | 2,535 |
| Existing eCards | 15 |
| Proposed history inserts | 24 |
| Proposed history occurrence reconciliations | 1 |
| Proposed legacy profile projections | 1 |
| Proposed workflow-stage changes | 1 |
| Proposed current history inserts | 20 |
| Proposed expired history inserts | 4 |
| Proposed superseded history inserts | 0 |
| Proposed historical-unknown history inserts | 0 |
| Expiration from reviewed calculation | 24 |
| Expiration directly from source | 0 |
| Expiration from existing production | 0 |
| Unknown expiration | 0 |
| Parsing errors | 0 |

Exact-match methods:

- `exact_email_compatible_course`: 24
- `existing_exact_ecard`: 1
- Exact normalized name methods: 0
- Fuzzy review suggestions: 0

Ambiguous methods:

- `exact_email_incompatible_or_unknown_course`: 59
- `exact_email_multiple_profiles`: 1
- `existing_ecard_course_conflict`: 13 (review-only; no proposed write)
- `existing_ecard_identity_conflict`: 1 (review-only; no proposed write)

Invalid reasons (a row can have more than one reason):

- `missing_ecard_code`: 15
- `missing_participant_name`: 5
- `malformed_ecard_code`: 1

The current folder contains no row matching the
`historical_expiration_reference` rule. The earlier representative
`combined.ods` file is not present in the current 1,069-file manifest. The two
current “Combined” XLSX files are roster-style rows without eCard or expiration
values; their remaining unique rows are correctly invalid, not expiration
references.

## Safety assessment

The revised policy separates parsed source expiration from calculated
expiration. All 24 matched Heartsaver Total records use the reviewed AHA
two-years-through-end-of-issue-month policy: 20 calculate as current and 4 as
expired on the 2026-07-30 reconciliation date. The 4 expired records no longer
project to employee profiles. Of the 20 current records, only one passes the
newer-data and current-cycle projection gates.

Parser classification, deterministic matching, status planning, and
projection gating are suitable for migration review. Production apply remains
intentionally unimplemented.

The detailed JSON/Markdown/HTML reports contain participant PII and are kept
outside the repository under the task `outputs` directory. The Drive manifest,
Supabase snapshot, and downloaded spreadsheets are private runtime artifacts
under the task `work` directory and are not committed.
