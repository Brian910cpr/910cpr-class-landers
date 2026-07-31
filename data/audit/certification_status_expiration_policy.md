# Certification status and expiration policy

Status: review policy implemented in the dry-run planner. No migration or
production write has been performed.

Policy version: `1.0`

## Source-fact boundary

The spreadsheet parser preserves only source facts:

- `class_date`
- `issue_date`
- `source_expiration_date`

It does not calculate expiration, infer status from filenames, or use Drive
upload/modified timestamps as certification dates. Calculated expiration is a
separate reconciliation decision with explicit provenance.

## Certification statuses

### `current`

Allowed only when the effective expiration is on or after the reconciliation
date and comes from:

1. an explicit source expiration;
2. a reviewed course-specific calculation; or
3. independent existing production data for the identical eCard.

### `expired`

Used when an explicit source expiration or reviewed calculation is earlier
than the reconciliation date.

### `superseded`

Used only within the same normalized credential family when a newer compatible
credential exists for the matched employee profile. A proven-current new
credential may propose marking older same-family history rows superseded.

Family boundaries are strict:

- BLS supersedes only BLS.
- ACLS supersedes only ACLS.
- PALS supersedes only PALS.
- Heartsaver Total does not supersede BLS.
- Child/Infant CPR does not supersede Heartsaver Total.
- Unknown/unrecognized courses never supersede another credential.

### `historical_unknown`

Used when the eCard is valid and the participant match is deterministic, but
current versus expired cannot be proved. Missing evidence is preserved in
`status_evidence`.

These rows can be proposed for history only. They cannot project an eCard,
class date, expiration, completion status, or workflow change onto
`maxim_employee_profiles`.

## Expiration provenance

New planner values:

- `source`
- `calculated_policy`
- `existing_production`
- `unknown`

Calculated rows also record:

- `calculation_policy`
- `calculation_version`
- `calculated_from_date`
- `calculated_at`

The existing legacy values `imported` and `calculated` remain accepted by the
review migration so the 15 current production rows continue to satisfy the
constraint.

## Reviewed course-family rules

| Family | Repository evidence | Production evidence | Automatic rule |
|---|---|---|---|
| AHA BLS | Course descriptions say valid two years | Existing BLS history uses two years through end of issue month | Enabled: `aha_two_years_through_end_of_issue_month` v1.0 |
| AHA Heartsaver | Course descriptions say valid two years | Heartsaver Total and Child/Infant history use the AHA month-end rule | Enabled for Heartsaver Total, other identified Heartsaver, and Child/Infant CPR |
| AHA ACLS | Course descriptions say valid two years | No ACLS history rows, but production’s stored rule is expressed for AHA course-completion cards generally | Enabled under the same reviewed AHA rule |
| AHA PALS | Course descriptions say valid two years | No PALS history rows, but production’s stored rule is expressed for AHA course-completion cards generally | Enabled under the same reviewed AHA rule |
| HSI | Repository descriptions say two years for some HSI courses | No production certification-history rule | Disabled: precise boundary and reliable normalized provider/family mapping are not established |
| ARC / American Red Cross | Repository and Red Cross documentation describe two years from completion for represented CPR courses | No production certification-history rule | Disabled until the importer has reliable ARC provider/family normalization and a separately reviewed exact-date policy |
| Other/unknown | No reliable common rule | None | Disabled; expiration remains unknown |

The AHA calculation takes `issue_date` when present, otherwise `class_date`,
adds two years, and uses the last calendar day of that month. Leap-year month
ends are calculated using the target year/month rather than by adding a fixed
number of days.

Supporting repository sources:

- `data/content/course_descriptions.json`
- Production `maxim_certification_history.expiration_rule`

Supporting authoritative sources:

- https://cpr.heart.org/en/resources/faqs/course-faqs
- https://cpr.heart.org/en/courses/basic-life-support-course-options
- https://cpr.heart.org/en/courses/advanced-cardiovascular-life-support-course-options
- https://cpr.heart.org/en/cpr-courses-and-kits/heartsaver
- https://www.redcross.org/faq.html

## Portal projection gate

A certification can propose a legacy profile projection only when:

1. the participant match is deterministic;
2. the course matches the employee requirement;
3. status is proven `current`;
4. the effective expiration is known;
5. the certification is newer than the existing projected credential;
6. expiration does not move backward; and
7. a pending scheduled workflow cycle, when present, matches the source class
   date.

`expired`, `superseded`, and `historical_unknown` always produce no profile or
workflow projection.

## Existing-eCard conflicts

An identical eCard with a conflicting course or participant association is
classified `conflict`. It produces no insert, reconciliation, supersession,
profile projection, or workflow change.

## Review migration

`supabase/migrations/20260731024109_certification_history_status_policy.sql`:

- adds `historical_unknown` to the status constraint;
- adds the four new expiration-provenance values while retaining legacy values;
- adds calculation provenance columns and `status_evidence`;
- enforces that `historical_unknown` has no expiration and uses the `unknown`
  source, while `current`/`expired` require an expiration date;
- does not modify `certification_import_files`;
- does not create another certification table.

A read-only production preflight found zero existing rows that would violate
the proposed status constraint, expiration-source constraint, or
status/expiration consistency constraint.
