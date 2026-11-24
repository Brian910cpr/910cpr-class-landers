# Codex Read — Issue 380 R36 canonical GitHub bridge

Reviewed at: 2026-10-14T14:10Z
Source handoff: `Codex_Reply_Issue380_20261014_R36.md`
Substantive commit: `b75386397118ce18468fd11a22c788567316226d`
Draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/381

## Review

Reviewed the new operator bridge, focused tests, and retained report.

The implementation is consistent with the existing fail-closed design:

- requires an explicit allowlisted libpq service name and valid UUID;
- invokes bounded noninteractive `psql` with startup scripts disabled, no password prompt, `ON_ERROR_STOP`, read-only transaction, and the restricted collector role;
- obtains the canonical binding before the bounded authenticated GitHub read and reacquires it afterward;
- suppresses the source observation if the card resolves or identity/version/source binding drifts;
- suppresses database/source diagnostics and returns no execution authority;
- performs no publication, resolution, reopen, task launch, or external mutation.

The 44/44 targeted Node result covers invalid inputs, subprocess boundaries, malformed responses, resolution races, and canonical drift. It is fixture proof only: no libpq service was provisioned, no operational database was contacted, and lifecycle metadata is still not typed operational evidence.

## Decision

Acknowledged as reviewed. Keep PR #381 draft and all SQL unapplied. No merge, migration, production integration, or task execution is authorized.

Next engineering step is a disposable authenticated PostgreSQL/libpq integration proof, followed by typed operational attestation enforced through the exclusive publisher. Production privileges, trusted first binding, installed no-launch consumer, and the external atomic side-effect fence remain open. No Brian action is required.
