# Codex Read — Issue 380 R35 canonical binding reader

Reviewed at: 2026-10-14T13:08Z
Source handoff: `Codex_Reply_Issue380_20261014_R35.md`
Substantive commit: `163bb42db000aba6bf6470e9ba652aa0c534aac3`
Draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/381

## Review

Reviewed the new SQL reader, focused PostgreSQL regression suite, and retained proof report.

The increment is internally consistent with the fail-closed design:

- the reader is `SECURITY INVOKER`, schema-qualified, and restricted to the collector role;
- canonical card/version/resolution and intake issue identity are read together;
- the GitHub issue URL is constructed for the fixed repository rather than accepted from caller input;
- missing, RLS-invisible, unsupported, or unresolved source state cannot authorize execution;
- resolved cards return skip;
- the reader is not treated as a lease, and the publisher still rejects a stale version;
- routine API roles remain denied and private card text is not returned.

The 47/47 disposable PostgreSQL result covers the four new reader cases plus inherited publication, privilege, rollback, contention, and audit checks. The proof remains local/synthetic and does not establish production privileges, installed integration, source attestation, or end-to-end safety.

## Decision

Acknowledged as reviewed. Preserve PR #381 as draft and unapplied. No merge, migration, production write, or task-launch authority is granted.

Next engineering work remains the authenticated DB-to-GitHub bridge and typed operational attestation feeding the exclusive publisher, followed by trusted first-binding authority, production effective-privilege proof, and the installed no-launch/external-side-effect fence. Lifecycle state alone must not become operational truth.

No Brian action is required for this increment.
