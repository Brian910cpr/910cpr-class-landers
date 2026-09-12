# Codex Reply — Issue #140 Round 2

- Assignment: GitHub issue `#140`, HOT/P0 HOT_SYNC credential parity verification
- Timestamp: `2026-09-12T07:21:58-04:00`
- Branch: `codex/issue-140-r2-verification`
- Base/current production commit inspected: `bfa152008163a93b6c49315f932fc0417790c8a6`
- Work-item state: `BLOCKED`
- Persistent-system evidence state: `CONNECTED` historically; currently failing authentication and therefore not `PROVEN`, `MONITORED`, or `HEALTHY`

## Executive result

Round 2 confirms that the single account-level blocker recorded in Round 1 remains unchanged. The GitHub Actions repository secret `HOT_SYNC_ADMIN_KEY` still has update timestamp `2026-09-11T19:00:48Z`, the timestamp of the known GitHub-only replacement. Both current production publishers continue to receive HTTP 401 from the protected HOT_SYNC endpoint. No repository-side credential name, endpoint, header, or fail-closed defect was found, so no application or workflow code change is safe or warranted.

The required owner action has not yet occurred. Production workflows were not manually rerun because the credential metadata is unchanged and a newer scheduled run already provides fresh, deterministic failure evidence.

## Root cause and authentication path

Facts retained and reverified from current `main`:

- `scripts/fetch_hot_sync_snapshot.py` reads `HOT_SYNC_ADMIN_KEY`, sends it as `X-Hot-Sync-Admin-Key`, and calls `https://schedule.910cpr.com/admin/hot-sync`.
- `.github/workflows/refresh-admin-availability.yml` and `.github/workflows/refresh-public-site.yml` both inject the same repository secret into that client.
- `.github/workflows/verify-canonical-participants.yml` injects the same secret and sends the same header to the protected Supabase `canonical-session-workspace` function.
- `worker/admin-api.js` requires the Worker-side `HOT_SYNC_ADMIN_KEY`; an absent service secret returns 503 and a nonmatching supplied value returns 401.
- The deployed route/service identified in Round 1 is Cloudflare Worker `free-time-offer-worker`, routed by `wrangler.toml` for `schedule.910cpr.com`, with `/admin/hot-sync` implemented by `worker/admin-api.js` through `worker/free-time-offer-worker.js` and backed by D1 `landerware-hot-sync` (`755bbe0b-300d-4c71-b3e3-f686f3b3d966`).

The current 401 responses prove the GitHub-supplied value is present but disagrees with the deployed service secret. GitHub secret metadata still shows `HOT_SYNC_ADMIN_KEY` last updated at `2026-09-11T19:00:48Z`; it has not changed since the proven bad replacement. The last known-good end-to-end admin refresh was run `34634928476`, job `103380389587`, completed at `2026-09-11T18:47:12Z`, immediately before that GitHub secret update.

## Current production evidence

### Refresh admin availability

- Failed run: `34685293951`, job `103531133442`
- Trigger/commit: scheduled, `main` @ `bfa152008163a93b6c49315f932fc0417790c8a6`
- Result: Enrollware seated/committed refresh succeeded. Step 6, **Fetch committed HOT_SYNC classes**, received `HTTP Error 401: Unauthorized` at `2026-09-12T09:15:57Z`.
- Fail-closed result: steps 7-21 were skipped, including future schedule, seat counts, canonical/public projection, iCal, availability, selector feeds, diagnostics, durable pages, source health, and commit. No incomplete publication occurred.

### Refresh public site from Enrollware iCal

- Newer failed run: `34690541250`, job `103544880660`
- Trigger/commit: scheduled, `main` @ `bfa152008163a93b6c49315f932fc0417790c8a6`
- Result: the full validated public build succeeded. Step 10, **Reconcile admin occupancy from current canonical sources**, received `HTTP Error 401: Unauthorized` at `2026-09-12T11:18:49Z`.
- Fail-closed result: strict link audit, refreshed inventory validation, stored iCal hash update, and approved output commit were skipped. No incomplete publication occurred.

### Related issue #205

- #205 is downstream of the same credential incident, not an independent verifier defect.
- Failed verifier run: `34641340641`, job `103401492898`, `main` @ `5392e74e2c774be00e784dc9fb6394a3d5ab452b`.
- **Query protected canonical workspace** failed; its integrity/count proof was skipped.
- The workflow uses the same GitHub secret/header against Supabase `canonical-session-workspace`, which then obtains the canonical HOT_SYNC source. #205 should remain open and be rerun after parity restoration.

## Work performed

- Read the full issue body and all comments, repository `AGENTS.md`, `CODEX_HANDOFF_PROTOCOL.md`, and `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md` before task work.
- Preserved the unrelated dirty primary checkout and created isolated worktree `E:\GitHub\910cpr-issue140-r2`.
- Left the requested durable pickup checkpoint on issue #140: issue comment `5645570266`.
- Inspected current secret metadata without reading or exposing any secret value.
- Reverified all three workflow consumers and the Worker/client authentication contract on current `main`.
- Inspected exact job/step results and failed logs for the two current production runs and the #205 verifier.
- Confirmed no `HOT_SYNC_ADMIN_KEY` is recoverable from local process, user, or machine environment scope; no value was printed.
- Did not run any generator, mutate any backend, weaken authentication, bypass occupancy, or publish stale/incomplete output.

## Local tests and checks

- `python -m unittest tests.test_publish_admin_schedule tests.test_canonical_schedule_hot_sync tests.test_validate_public_refresh_output -v` — **10 passed**.
- `node --test tests/admin_api.test.mjs` — **17 passed**.
- `python -m py_compile scripts/fetch_hot_sync_snapshot.py scripts/publish_admin_schedule.py` — **passed**.
- Initial `python -m pytest ...` attempt could not run because `pytest` is not installed in this local Python environment. Equivalent repository `unittest` modules were run successfully; this is a known local tooling limitation, not an application failure.

## Exact blocker and single owner action

Account-level action is required. The deployed secrets are write-only, the previous canonical value is not available locally, and Round 1 established that the available Cloudflare authorization cannot read or mutate the Worker secret.

**Single exact Brian action:** in GitHub repository **Settings → Secrets and variables → Actions**, restore the repository secret `HOT_SYNC_ADMIN_KEY` to the immediately previous canonical value that remains configured in both the Cloudflare `free-time-offer-worker` and the Supabase canonical-session service.

Do not send, paste, log, or commit the value. Restoring the GitHub copy is safer than rotating multiple deployed backends because both independently accepted the previous value immediately before the GitHub-only replacement.

## Required verification after the owner action

1. Run **Verify canonical participant workspace** and require the protected query and canonical count proof to pass.
2. Run **Refresh admin availability** and require all steps through source-health reporting and approved commit to pass.
3. Run **Refresh public site from Enrollware iCal** and require occupancy reconciliation, strict link audit, inventory validation/hash handling, and approved publication to pass.
4. Observe at least one subsequent scheduled cycle of each production publisher before classifying the persistent system `HEALTHY`; one manual green run is only end-to-end proof, not stability.

## Files and deployment status

- Intended file changed: `Codex_Reply_Issue140_R2.md` only.
- Known unrelated worktree change: `docs/Earl/index.html` appears modified and is deliberately unstaged/uncommitted.
- Local validation: completed as listed above.
- Push: this receipt will be committed and pushed before exit.
- Merge: not performed.
- Deployment/config mutation: not performed.
- Public state: blocked/fail-closed; no incomplete admin or public output was deployed.

## Remaining risk and recommended next action

Until the GitHub secret is restored, scheduled admin/public refreshes will continue to fail closed and #205 cannot prove canonical participant workspace integrity. ChatGPT should route only the single account-level action above to Brian, then dispatch a verification-only Round 3. No repository auth bypass or fallback to stale occupancy is authorized.
