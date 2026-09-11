# Codex Reply — Issue #140

- Assignment: GitHub issue `#140`, P0 HOT_SYNC admin credential parity
- Timestamp: `2026-09-11T15:57:38-04:00` (`2026-09-11T19:57:38Z`)
- Branch: `codex/issue-140-hot-sync-parity`
- Commit SHA: recorded in the follow-up receipt commit after this file's foundation commit
- Work-item state: `BLOCKED`
- Persistent-system evidence state: `CONNECTED` historically, currently failing authentication and therefore not `PROVEN`, `MONITORED`, or `HEALTHY`

## Root cause and exact service

Fact: `schedule.910cpr.com/*` is routed by repository `wrangler.toml` to the Cloudflare Worker named `free-time-offer-worker`, backed by D1 database `landerware-hot-sync` (`755bbe0b-300d-4c71-b3e3-f686f3b3d966`). The `/admin/hot-sync` route is implemented by `worker/admin-api.js` through `worker/free-time-offer-worker.js`.

Fact: the exact authentication contract is a nonempty request header named `X-Hot-Sync-Admin-Key`, compared in constant-time after SHA-256 hashing against the Worker's `HOT_SYNC_ADMIN_KEY` secret. A missing Worker secret returns HTTP 503; a nonmatching supplied value returns HTTP 401. `scripts/fetch_hot_sync_snapshot.py` still implements that exact header contract.

Fact: GitHub Actions repository secret `HOT_SYNC_ADMIN_KEY` reports `updated_at=2026-09-11T19:00:48Z`. Immediately before that update, scheduled admin-refresh run `34634928476` (job `103380389587`) successfully fetched HOT_SYNC data and completed the entire refresh at `2026-09-11T18:47:12Z`. After the update, rerun job `103397319511` in run `34634002292` received HTTP 401 from the Worker.

Finding: the GitHub Actions secret was replaced at 19:00:48 UTC with a value that does not match the already-deployed backend secrets. This is GitHub-side credential replacement/staleness, not a missing secret, client regression, header-contract change, or absent Worker secret. No relevant client, Worker auth, workflow, or Wrangler configuration commit occurred in the interval.

Additional fact: the same GitHub secret is used by three workflows:

1. `.github/workflows/refresh-admin-availability.yml` against the Cloudflare Worker.
2. `.github/workflows/refresh-public-site.yml` against the Cloudflare Worker.
3. `.github/workflows/verify-canonical-participants.yml` against the Supabase `canonical-session-workspace` function.

The fresh Supabase verification below also returned 401, independently confirming that the replacement GitHub value disagrees with both deployed backends.

## Work performed

- Read the full issue body, recurrence comment, repository `AGENTS.md`, `CODEX_HANDOFF_PROTOCOL.md`, and `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md` before acting.
- Preserved the unrelated dirty checkout and created isolated worktree `E:\GitHub\910cpr-issue140` on branch `codex/issue-140-hot-sync-parity` from `origin/main` (`5392e74e2c774be00e784dc9fb6394a3d5ab452b`).
- Inspected the Worker routing, backend implementation, constant-time auth code, client, and all workflow consumers.
- Inspected GitHub secret metadata without attempting to reveal any secret value.
- Attempted authorized Cloudflare metadata access with Wrangler. The configured Cloudflare API token was rejected by account IP-location policy (`code 9109`) and secret access was rejected with authentication error (`code 10000`). No Cloudflare state was changed.
- Triggered narrow, fail-closed production checks on current `main`; no generator was run locally and no incomplete output was published.

## Verification results

- Historical end-to-end success: run `34634928476`, job `103380389587`, completed all 21 workflow steps successfully at `2026-09-11T18:47:12Z`, including HOT_SYNC fetch, admin schedule publication, calendar/availability feeds, diagnostics, and commit.
- Affected full public refresh: run `34634002292`, rerun job `103397319511`, checked out current `main` `5392e74`, completed the full public build, then failed closed with Worker HTTP 401 at HOT_SYNC reconciliation. No incomplete public output was committed.
- Fresh admin refresh check: run `34641338744`, job `103401487647`, on current `main`; Enrollware refresh succeeded, then `fetch_hot_sync_snapshot` failed at `2026-09-11T19:57:18Z` with HTTP 401. Every downstream publication and commit step was skipped. Fail-closed behavior is intact.
- Fresh second-service check: run `34641340641`, job `103401492898`; the masked GitHub secret was nonempty, but the protected Supabase canonical-session endpoint returned HTTP 401. Participant proof was skipped.
- Local environment has no recoverable `HOT_SYNC_ADMIN_KEY` value at process, user, or machine scope. No secret value was printed or stored.

## Exact blocker and single Brian action

Account-level action is required because deployed secrets are write-only and the available Cloudflare token cannot read or mutate the Worker secret.

**Single exact action for Brian:** restore the GitHub Actions repository secret `HOT_SYNC_ADMIN_KEY` to the immediately previous canonical value that remains configured in both the Cloudflare `free-time-offer-worker` and the Supabase canonical-session service.

Do not send or paste the value into chat or this repository. Perform the restoration directly in GitHub repository Settings → Secrets and variables → Actions. This is preferable to rotating three locations because both independent backends demonstrably accepted the previous value minutes before the GitHub-only update.

## Remaining validation after Brian's action

1. Rerun `Verify canonical participant workspace` and require success.
2. Rerun `Refresh admin availability` and require HOT_SYNC fetch plus complete admin schedule publication and commit success.
3. Rerun `Refresh public site from Enrollware iCal` on current `main` and require the entire workflow to pass.
4. Confirm the HOT_SYNC snapshot reports the expected records without exposing record details unnecessarily.

## Files changed

- `Codex_Reply_Issue140.md` only.

Unrelated `docs/Earl/index.html` work appeared modified in the isolated worktree and was deliberately left unstaged and uncommitted. No application code, generated inventory, secrets, Worker configuration, or deployment was changed.

## Deployment and risk

- Local validation: diagnostic/read-only checks completed.
- Push: pending at the time of the foundation commit; this receipt will be pushed before exit.
- Merge: not performed.
- Deployment: not performed.
- Current operational risk: both HOT_SYNC-dependent refresh workflows remain fail-closed, and the canonical participant verification also fails. Public/admin schedule refreshes cannot advance until credential parity is restored.
- Recommended next action for ChatGPT: route the one account-level GitHub secret restoration to Brian, then dispatch a verification round using the four checks above.
