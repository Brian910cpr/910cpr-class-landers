# Codex read: V2 release reconciliation

Reviewed 2026-10-07 against PR #353 at `d1225f7facc6674da2efddc828fa8ae9290db26c`.

Reviewed the original root receipt `Codex_Reply_v2_release_reconciliation.md`, the six-commit PR history and 31-file diff, the shadow-mode policy, the nonpublishing runner, the source projection/publication adapters, the test coverage described in the receipt, and the latest actual-data runner evidence.

## Result

The handoff is genuinely read and acknowledged, but PR #353 is **not accepted for merge or activation**.

The latest actual-data probe ([run 37617808899](https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/37617808899)) successfully read 25 canonical sessions, 161 calendar events, and one bounded calendar coverage proof. It then failed closed in `scripts.run_layered_release_probe`: each page received 205 input windows, evaluated zero, and reported 205 `unresolved_occupied_bounds` failures. Publication remained false, as required.

A successful Cloudflare branch preview proves only that static preview deployment works; it does not satisfy the source-to-V2 evaluation gate. Keep the policy in shadow and the PR draft. Do not merge, activate, publish, or weaken UNKNOWN/fail-closed behavior.

## Required repair

1. Trace why the 205 inverse-generated availability windows all intersect occupancy rows without resolvable `start`/`end` or bounded `uncertainty_scope`.
2. Preserve source identities and physical occupancy; do not drop malformed rows to manufacture availability.
3. Add an actual-shaped regression proving at least one current window is evaluated while malformed rows close only their real bounded scope.
4. Re-run the nonpublishing workflow and require: current sources read successfully, `evaluated_windows > 0`, no unbounded occupancy admitted, public output remains unpublished, and the result contains inspectable rejection/decision evidence.
5. Create the new immutable root receipt `Codex_Reply_PR353_20261007T121500Z_R1.md` with branch/commit, files changed, tests, run URL, before/after window counts, publication statement, and any remaining blocker. Preserve the original reply and this read receipt.

Owner-only action: none; engineering is handling this bounded repair.
