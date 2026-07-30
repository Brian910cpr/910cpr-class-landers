# Assigned eCards source-format discovery

Status: representative read-only discovery completed 2026-07-30. No Drive
file was modified, no migration was applied, and no Supabase write occurred.

## Source and sample

- Drive folder: `Assigned-ecards_`
- Folder ID: `1mAKk554dqD3l-ufLSMp07dh_T07Ih_8o`
- The authenticated Drive listing reached the 1,000-item page boundary and
  returned a continuation token. The importer uses Drive API v3 pagination
  until `nextPageToken` is absent.
- Fourteen representative files were downloaded read-only and inspected:
  recent XLSX exports, older XLS/XLSX exports, two byte-identical
  duplicate-looking XLSX files, CSV, ODS, a large older workbook, and files
  with customer/class hints in their names.
- The representative corpus contained 724 preserved rows. This is a format
  sample, not a claim that the folder contains only 14 files.

## Findings

1. Common structures: tabular exports with a header row followed by one
   participant per row. XLS/XLSX/CSV/ODS occur. Blank leading rows and
   unusually wide ODS used ranges occur.
2. Sheet names: exports most often use a single worksheet. No multi-sheet
   source was found in the representative sample; the parser nevertheless
   reads every sheet and tests that behavior.
3. Header variants include `eCard Code`, `eCard Number`, `Course Date`,
   `Class Date`, `First Name`, `Last Name`, `Name`, `Email`, and optional
   `Course Modules`.
4. Participant identifiers: first/last or full name are common; email is
   present in some layouts; eCard number is the strongest credential
   identifier. There is no universal employee/profile ID.
5. eCard numbers are normally 12 digits. The parser removes display hyphens
   and spaces, preserves alphanumeric codes, and flags unexpected lengths or
   malformed values.
6. Course values vary. Observed examples include `Heartsaver Total` and
   `Child CPR AED/Infant CPR`; many rows have no reliable course value. The
   parser maps only explicit aliases and leaves all other values `UNKNOWN`.
7. Course/class date is common. Issue date and expiration date are not
   consistently present and are never fabricated.
8. Corporate customer/account cannot be derived reliably from workbook
   content across the sample. Filenames may contain customer/class hints but
   are not treated as authoritative identity evidence.
9. Email addresses are available in some layouts but not all.
10. XLS, XLSX, CSV, and ODS are supported with `python-calamine` plus the
    standard CSV reader. Unsupported extensions are retained in the audit.
    One ODS file advertises a very wide used range and produces many
    preserved invalid rows with missing eCard values; it requires manual
    review rather than silent dropping.

## Schema assessment

The live `maxim_certification_history` table already represents multiple
credentials and historical/replacement eCards per employee profile. Its
credential rows include eCard number, course, issue/expiration dates,
certification status, employee-profile link, Drive provenance, source
occurrences, source payload, and match method. It is therefore the
authoritative certification repository.

`maxim_employee_profiles.prior_ecard_code` is a legacy portal projection, not
the certification system of record. A conservative projection may be
proposed only for an exact deterministic match and only when the source
credential is demonstrably newer and course-compatible.

The only proposed schema addition is the private file-level
`certification_import_files` ledger in
`supabase/migrations/20260730194932_certification_import_file_ledger.sql`.
The migration is generated for review and has not been applied.

## Open source-format questions

- Which upstream export field, if any, can authoritatively identify the
  corporate account?
- Are missing course values recoverable from an embedded sheet or a separate
  authoritative class roster?
- Is “Course Date” always the issue/completion date, or can those differ?
- Is expiration available in newer exports, or must it come from a separate
  authoritative rule/service?
- Are the unusually wide ODS rows meaningful records or formatting debris?

