# Codex Receipt — Durable Session Endpoint Deployment

## Outcome

The `session-workspace` Supabase Edge Function is deployed to the production LanderWare project (`wktwgcnwdvbebcobgyey`) and its anonymous boundary was verified live.

The older participant-linking UI commit was not replayed onto current `main`. Current `main` is 249 commits ahead of the original delivery branch and already contains a newer canonical participant model and dense dashboard. A trial cherry-pick produced conflicts in the dashboard, publisher, and publisher tests; it was aborted so newer production behavior would not be overwritten.

## Deployment performed

- Function: `session-workspace`
- Project: `wktwgcnwdvbebcobgyey` (`LanderWare`)
- Source commit already persisted on GitHub: `a8d44b79a7c`
- Final deployment mode: `--no-verify-jwt`
- Reason: public summary requests must reach the function, while sensitive detail remains protected by the function's `x-maxim-session` validation.

The initial default deployment was reachable but rejected anonymous requests with `401 UNAUTHORIZED_NO_AUTH_HEADER`. Redeploying with `--no-verify-jwt` corrected the platform configuration without weakening the function's internal authorization gate.

## Live verification

Production endpoint tested:

`https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/session-workspace`

Anonymous `POST /summaries` for Enrollware session `14011964` returned:

```json
{
  "ok": true,
  "summaries": [{
    "externalSessionId": "14011964",
    "session": null,
    "participant_count": null,
    "count_available": false,
    "roster_available": false,
    "count_source": "unavailable"
  }]
}
```

Anonymous `GET /resolve?externalSessionId=14011964` returned `authorized: false`, no participant detail, and an unknown count rather than a false zero.

## Repository and validation status

- Supabase deployed: yes.
- Live endpoint verified: yes.
- Public summary behavior verified: yes.
- Anonymous detail protection verified: yes.
- Generator run: no.
- Broad rebuild: no.
- Current-main UI modified: no; newer canonical behavior was preserved.
- Original dirty worktree modified: no; unrelated `docs/Earl/index.html`, cache, and heartbeat changes remain untouched.

## Remaining review decision

Current `main` already uses `canonical-session-workspace` for authenticated participant truth and routes its workspace control to `/admin/admin-port.html`. It still contains a fallback roster request to `session-workspace/resolve`, which is now live. Any future consolidation of these two endpoints should be treated as a separate targeted change with explicit compatibility tests.
