# Owner login retry still fails

- Assignment: user-requested retry of owner access; issue #215, related #140.
- Timestamp: 2026-09-14T00:01:01.491Z.
- Branch: `codex/owner-access-failed-signin`.
- Parent commit: `fef4fa84fc0ac45d1ab16733b22c1d19b30cc4ea`; this receipt is the only new file.
- Work-item state: BLOCKED. Persistent-system level remains BUILT, not PROVEN for accepted-key access.

The user explicitly requested another attempt. The browser opened the production Class History page, which displayed the owner-key form. One secure browserAuth request was submitted. Fresh visible DOM and the rendered page then showed: “Class history could not load right now. Please try again.” The owner form remained visible, summary counts remained blank, and no class records loaded.

The submitted request is not proof of successful authentication. The generic error does not distinguish a rejected key from a service failure or a browser-specific access restriction. No secret was read, captured, logged, or modified. No second automatic attempt was made after this failure.

Checks: live form inspection, one secure sign-in attempt, and fresh rendered-result inspection. Result: the owner access retry did not succeed. No application, database, deployment, or credential changes were performed; this receipt is documentation only. Other owner pages, document actions, publisher workflows, and secret parity were not retested in this narrow retry.

Last successful accepted-key proof: none established in this conversation. Failure condition: protected class records do not load after sign-in. Existing incident tracking: #215/#140. Observer health and ongoing sign-in monitoring are not established.

Next action: resolve the account/service gate documented in R4 and expose a clear distinction between rejected credentials and service failures. Then obtain secure accepted-key browser proof before calling access restored. Account-level configuration cannot be inferred from this generic UI message. Preserve the previous receipt; keep #215/#140 open.
