# Codex read — Issue #380 R37

- Reviewed at: 2026-10-14T14:56Z
- Reply: `Codex_Reply_Issue380_20261014_R37.md`
- Substantive commit: `4019f8dfc69ef71afdd2d817e934fc7291d2e811`
- Draft PR: #381
- Disposition: ACKNOWLEDGED; guarded bridge harness is a safe test-only increment, but its four real-transport cases remain unproved.

The harness and report were reviewed. It fails before SQL fixture initialization when `psql` is unavailable, uses a temporary explicit loopback service under a separate collector identity, fixtures only the GitHub boundary, asserts fail-closed behavior, and changes no application, migration, production, installed runtime, or assignment state. Existing workflow evidence on the current PR tip is green.

Do not count the blocked harness as integration proof. Keep #381 draft/unmerged/unapplied. Next Codex work is to provision a verified local PostgreSQL client in the same guarded disposable environment, rerun and fix the four bridge cases, then continue the typed attestation/source-enforcement, privilege, installed-consumer atomic-fence, and private evidence/UI/history/count/reopen proof. No Brian/account action is required.
