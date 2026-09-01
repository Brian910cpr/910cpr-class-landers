# Hx-Builder Session-Alias Migration Validation

The proposal from `8e3d48d2ae882135449baec9db86660d3fca150b` was corrected during migration review. The migration remains unapplied.

## Corrections made

- Revokes every `anon` and `authenticated` table grant on the three shared alias tables.
- Backfills existing aliases as `legacy_unscoped` / `approved_legacy`, then defaults new aliases to `unreviewed` and inactive.
- Requires review time and reviewer identity before activation.
- Makes source identity, canonical target, and provenance immutable.
- Allows reversible activation and timestamps deactivation without deleting evidence.
- Adds scoped `(source_system, source_label)` primary keys and canonical-target indexes.
- Updates Hx-Builder to ignore inactive, rejected, or unreviewed aliases.

## Production transaction validation

The exact corrected migration ran twice in independent production transactions ending in `ROLLBACK`.

Both runs verified:

- location / instructor / course aliases: `2 / 55 / 15`
- browser grants after migration: `0`
- active unreviewed aliases: `0`
- orphan canonical targets: `0`
- duplicate scoped labels fail with a unique violation
- canonical target deletion fails through the existing foreign key
- alias identity, target, and provenance cannot be updated

After both rollbacks, production retained its original `22 / 27 / 22` course/location/instructor alias rows. No proposed row, new column, trigger function, or index remained.

## Compatibility and behavior boundary

Production has no database view or function dependency on these alias tables, and repository search found no public schedule or registration consumer. The tables are not joined to `class_sessions`; inserting an alias cannot mutate a session or public offer. Hx-Builder is the only reviewed consumer and now requires `active=true` plus `reviewed`/`approved_legacy`. Existing reference fixtures without the new fields retain legacy-compatible behavior.

Foreign keys retain PostgreSQL `NO ACTION` delete behavior. Therefore a canonical course, location, or person cannot disappear while referenced. Explicit IDs plus scoped uniqueness ensure one target per alias; if an alias and exact-name lookup disagree, Hx-Builder returns multiple candidate IDs and routes the fact to review.

## Full dry-run gate

- records: `8,199`
- deterministic hash: `bf2e98b67868ac910283471c0947ca59065778e5893782390e301c5af61cde26`
- independent output identical: `true`
- replay additional operations: `0`
- replay additional assertions: `0`
- unexplained mismatches: `0`
- tests: `25 passed`

No historical import occurred and no application code was deployed.

**SAFE TO APPLY SESSION-ALIAS MIGRATION**
