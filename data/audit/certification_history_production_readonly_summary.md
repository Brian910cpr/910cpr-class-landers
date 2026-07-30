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
| Ambiguous matches | 74 |
| Unmatched rows | 2,535 |
| Existing eCards | 15 |
| Proposed history inserts | 24 |
| Proposed history occurrence reconciliations | 15 |
| Proposed legacy profile projections | 19 |
| Proposed workflow-stage changes | 1 |
| Skips due to older/unproven profile data | 5 |
| Backward expiration skips | 0 |
| Parsing errors | 0 |

Exact-match methods:

- `exact_email_compatible_course`: 24
- `existing_exact_ecard`: 1
- Exact normalized name methods: 0
- Fuzzy review suggestions: 0

Ambiguous methods:

- `exact_email_incompatible_or_unknown_course`: 59
- `exact_email_multiple_profiles`: 1
- `existing_ecard_course_conflict`: 14

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

Parser classification and deterministic matching are suitable for continued
migration review. Production apply is **not** ready:

- all 24 proposed history inserts currently label
  `certification_status = 'current'`;
- their class dates range from 2022-09-07 through 2026-07-25;
- none has a source expiration date.

Before any apply implementation, certification status/expiration policy must
be reviewed so an older credential is not labeled current merely because it
is newly discovered. History inserts must also remain separable from legacy
profile projections.

The detailed JSON/Markdown/HTML reports contain participant PII and are kept
outside the repository under the task `outputs` directory. The Drive manifest,
Supabase snapshot, and downloaded spreadsheets are private runtime artifacts
under the task `work` directory and are not committed.

