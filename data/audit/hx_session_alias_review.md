# Hx-Builder Historical Session Alias Review

No aliases or historical records were applied to production. No application code was deployed.

## Dry-run effect

| Dimension | Before | After | Change |
| --- | ---: | ---: | ---: |
| Unresolved location rows | 4,266 | 4,258 | -8 |
| Unresolved instructor rows | 2,551 | 126 | -2,425 |
| Unresolved course rows | 235 | 17 | -218 |
| Unresolved timing rows | 85 | 85 | +0 |
| Fully canonicalized sessions | 1,765 | 2,063 | +298 |

## Determinism

- Hash: `bf2e98b67868ac910283471c0947ca59065778e5893782390e301c5af61cde26`
- Independent output identical: **true**
- Replay additional operations/assertions: **0 / 0**
- Unexplained mismatches: **0**
- Identity conflicts: **27**
- Duplicate candidates: **97**

## Alias proposal

- Locations: **2**
- Instructors: **55**
- Courses: **15**
- Timing corrections: **0**

The complete frequency-ranked inventories for all four dimensions are included in the redacted JSON artifact.

## Persistence design

The proposal reuses the three shared historical alias tables. It adds source scope, provenance, review status, reversible activation, and a scoped primary key. Plain inserts deliberately fail on collisions.

## Remaining blockers for import

- 4,258 location references remain unresolved because canonical location authority is absent or the source value is missing/ambiguous.
- 126 rows have no instructor value and remain review-required.
- 17 course rows remain intentionally unresolved across three ambiguous/generic course labels.
- 85 rows retain unknown, ranged, zero, or implausible duration evidence; no end time was synthesized.
- 27 participant identity conflicts remain outside this session-alias review.

NHCSO 2026 remains outside this export and was not reconstructed.
