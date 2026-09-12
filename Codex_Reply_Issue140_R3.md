# Codex Reply — Issue #140 Round 3

- Assignment: GitHub issue `#140`, HOT/P0 HOT_SYNC credential parity verification
- Timestamp: `2026-09-12T07:39:24-04:00`
- Branch: `codex/issue-140-r3-verification`
- Production commit inspected: `bfa152008163a93b6c49315f932fc0417790c8a6`
- Work-item state: `BLOCKED`
- Persistent-system evidence state: historically `CONNECTED`; currently failing authentication and therefore not `PROVEN`, `MONITORED`, or `HEALTHY`

## Result

The Round 2 account-level blocker remains unchanged. GitHub reports repository secret `HOT_SYNC_ADMIN_KEY` was last updated at `2026-09-11T19:00:48Z`, the known bad GitHub-only replacement timestamp. No subsequent secret change or successful production occupancy cycle exists. The latest scheduled admin and public publishers both still fail closed with HTTP 401.

No repository-side credential name, endpoint, header, or authentication defect was found. No code change, workflow rerun, generator run, backend mutation, authentication weakening, or stale-data publication was performed.

## Root cause and exact service

- `scripts/fetch_hot_sync_snapshot.py` reads `HOT_SYNC_ADMIN_KEY`, sends `X-Hot-Sync-Admin-Key`, and calls `https://schedule.910cpr.com/admin/hot-sync`.
- Both `.github/workflows/refresh-admin-availability.yml` and `.github/workflows/refresh-public-site.yml` inject the same repository secret into that client.
- `.github/workflows/verify-canonical-participants.yml` injects the same secret and header into the protected Supabase `canonical-session-workspace` function.
- The deployed HOT_SYNC route is Cloudflare Worker `free-time-offer-worker`, routed by `wrangler.toml`, implemented by `worker/free-time-offer-worker.js` and `worker/admin-api.js`, and backed by D1 `landerware-hot-sync` (`755bbe0b-300d-4c71-b3e3-f686f3b3d966`).
- `worker/admin-api.js` returns 503 when its service secret is absent and 401 when a supplied value does not match. Current 401 responses therefore prove that the GitHub-provided value is present but disagrees with the deployed service secret.

## Current workflow evidence

- Last known-good end-to-end admin refresh: run `34634928476`, job `103380389587`, completed `2026-09-11T18:47:12Z`, before the GitHub secret replacement.
- Latest admin failure: run `34685293951`, job `103531133442`, scheduled on `main` @ `bfa152008163a93b6c49315f932fc0417790c8a6`; **Fetch committed HOT_SYNC classes** returned HTTP 401 and all downstream publication steps were skipped.
- Latest public failure: run `34690541250`, job `103544880660`, scheduled on the same commit; the validated public build passed, then **Reconcile admin occupancy from current canonical sources** returned HTTP 401. Strict link audit, inventory validation/hash handling, and approved publication were skipped.
- Fail-closed behavior is intact: neither run published incomplete output.

## Issue #205 relationship

Issue #205 is downstream of the same credential mismatch, not an independent verifier defect. Its run `34641340641`, job `103401492898`, failed at **Query protected canonical workspace** while using the same GitHub secret/header. Keep #205 open and rerun it after credential parity is restored.

## Work performed and validation

- Read the complete issue body/comments, `AGENTS.md`, `CODEX_HANDOFF_PROTOCOL.md`, and `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md`.
- Preserved the unrelated dirty primary checkout and used isolated worktree `E:\GitHub\910cpr-issue140-r3`.
- Added pickup checkpoint issue comment `5645649629`.
- Rechecked GitHub secret metadata without reading or exposing any secret value.
- Reverified all three workflow consumers and the Worker/client authentication contract on current `main`.
- `python -m unittest tests.test_publish_admin_schedule tests.test_canonical_schedule_hot_sync tests.test_validate_public_refresh_output -v` — 10 passed.
- `node --test tests/admin_api.test.mjs` — 17 passed.
- `python -m py_compile scripts/fetch_hot_sync_snapshot.py scripts/publish_admin_schedule.py` — passed.

## Files and deployment status

- Intended file changed: `Codex_Reply_Issue140_R3.md` only.
- Local validation: completed as listed above.
- Application code/config: unchanged.
- Merge: not performed.
- Deployment/config mutation: not performed.
- Production remains blocked and safely fail-closed.

## Exact blocker and single owner action

Account-level action is required. The deployed secrets are write-only, the prior canonical value is unavailable to this environment, and current authorization cannot safely recover or mutate the deployed Worker secret.

**Single exact Brian action:** in GitHub repository **Settings → Secrets and variables → Actions**, restore `HOT_SYNC_ADMIN_KEY` to the immediately previous canonical value that remains configured in both the Cloudflare `free-time-offer-worker` and the Supabase canonical-session service. Do not paste, send, log, or commit the value.

## Required verification after owner action

1. Run **Verify canonical participant workspace** and require its protected query and count/integrity proof to pass.
2. Run **Refresh admin availability** and require every downstream occupancy, availability, publication, and source-health step to pass.
3. Run **Refresh public site from Enrollware iCal** and require reconciliation, strict link audit, inventory validation/hash handling, and approved publication to pass.
4. Observe at least one later scheduled cycle for each production publisher before classifying the system `HEALTHY`.

Recommended next action for ChatGPT: route only the single owner action above to Brian, then dispatch a verification-only Round 4. No repository auth bypass or stale occupancy fallback is authorized.
