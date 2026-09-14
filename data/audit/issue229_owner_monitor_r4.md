# Issue #229 — protected checkpoint delivery and owner monitor

Assessment: September 14, 2026, America/New_York (UTC-04:00).
Branch: `codex/issue-229-owner-monitor-r4`, based on `d11824ee9e8b8301960f0be6af22890497920437` / draft PR #232.
State: **PR_OPEN / IN_PROGRESS**. Delivery and page are **BUILT**, validated locally. Production monitor is **not deployed or proven**.

## Result

The owner can review recovered records, preliminary candidates, generation/validation/sitemap/publication counters, unknown Google observations and a newest-first checkpoint history in the new `/admin/archive-rebuild.html` implementation. It uses the existing remembered owner session; no second password, owner grant, database table or alternate schedule feed is introduced.

The page fetches a new `archive-status` Edge Function every 20 seconds after the previous request completes. The function reads the existing `data/audit/issue229_archive_rebuild_status.json` from GitHub, with a 10-second shared source cache and one concurrent source fetch per function instance. A configured read token prevents the unauthenticated GitHub rate-limit problem that 20-second polling would create. No dashboard/mailbox/roster query is performed. Two existing owner-session lookup queries authorize each successful response, before and after the source read; session authority is never cached with checkpoint data.

This is the next integration of R3's checkpoint contract, not another archive catalog. R3 producer/feed and the R1/R2 historical source artifacts are unchanged. Existing review/publication restrictions remain visible: the current source says ELIGIBILITY_REVIEW / BLOCKED, with `eligible_pages=null`, zero build/publication counters and unknown Google values. The page never treats 23,488 preliminary candidates as an approved denominator or sitemap size as indexing evidence.

## Exact source/configuration contract

- Entry point: `supabase/functions/archive-status/index.ts`.
- Request: GET `/functions/v1/archive-status`, header `X-LanderWare-Owner-Session` containing the existing opaque owner token. Tokens are never included in URLs, logs, status JSON or diagnostic copies.
- Allowed browser origins: `https://www.910cpr.com`, `https://910cpr.com`; OPTIONS is a credential-free preflight. Other origins return 403 and writes return 405.
- Authentication: reuse `lookupOwnerSession()` from `_shared/owner-session.ts`, which checks both browser-session and grant expiry/revocation. Anonymous/malformed tokens and corporate/legacy credentials return 401 without a source fetch. Database outages return sanitized 503. Revocation during source retrieval prevents delivery.
- Platform configuration: deploy this function with `verify_jwt=false`, as it validates the existing opaque owner session rather than a Supabase browser JWT. This is not anonymous authorization: the application handler requires the owner session before accessing data.
- `GITHUB_TOKEN`: server-side Contents-read access to this repository. Existing deployed configuration has **not been verified** in this increment. Reuse an appropriate existing token if present; no secret was read, created or changed. Missing token fails closed. Never embed it in page assets.
- `ARCHIVE_STATUS_REF`: defaults to `main`. It may be set only server-side to an explicit `codex/` branch for controlled staging. HTTP parameters cannot choose a repository/ref/path. Repository and path are constants in `core.mjs`.
- **Current production-source blocker:** fetched `origin/main` at `abc7e9b1dd2d03039437721f80fe294190060c8a` does not contain `data/audit/issue229_archive_rebuild_status.json`. The source is currently in PR #232's draft stack. Default-main deployment cannot yet deliver the checkpoint. Coordinate reviewed source integration or explicitly configured staging; do not silently read an unrelated branch.
- GitHub content responses must be successful, bounded, base64 content with a blob ID; redirects/errors fail closed. Cached content expires after 10 seconds. An upstream outage after expiry produces 503, never a fresh-looking stale success.
- Every returned checkpoint field is validated against the existing schema-v1 Python contract: exact keys, enums, safe counters, timestamps, partitions, full eligible denominator, immutable evidence references, event snapshots and Google measurement windows. Unknown fields, including arbitrary private text, are rejected. This is structural validation, **not approval of the facts in an evidence reference**.
- Response fields: `checkpoint` (validated R3 contract), `source` (`ref`, Git blob ID, `fetched_at`), `observed_at` (delivery time), and `job_health` (`state`, `checkpoint_age_seconds`). Responses are private/no-store/no-referrer and vary by Origin.

Python remains authoritative for checkpoint production. The JS consumer validates that contract for its different runtime; changing schema versions requires coordinated producer/consumer changes. Tests use the actual R3 JSON to detect drift. No scheduling eligibility/filter rules changed.

## Page behavior

The static HTML shell contains labels, navigation, version metadata and no operational counts or credentials. Private containers begin hidden. After authorization, the script renders values using DOM text nodes, not source-controlled HTML. Direct links point to issue #229, PR #230 and the validated current PR/commit.

Displayed metrics: historical source rows and HTML URLs; preliminary candidates; private/ambiguous/review rows with additional not-elapsed rows; eligible total when approved; generated, validated, failed validation, sitemap and published counts; discovered/indexed/impressions/clicks plus measurement windows. Progress bars use the entire approved eligible denominator. Unresolved and zero denominators do not show invented percentages.

The job checkpoint time and its age remain distinct from successful browser polls and GitHub fetch time. RUNNING with an age over 300 seconds is STALLED; a future checkpoint is CLOCK_MISMATCH. BLOCKED remains BLOCKED, visibly retaining its age. The rail shows the R3 import events as recorded; they are not invented historical execution timestamps.

Requests have a 15-second timeout and never overlap. A changed session, sign-out or page-hide clears private details and prevents late responses from repopulating them. Visible-tab resume reloads. Failed polls hide the prior private counts, retain the last successful poll timestamp and retry in 20 seconds. No browser polling or private display is persisted when the tab is hidden. Existing auth helper continues to handle private-link redirect/session refresh.

Both changed/new scripts have versioned references on the new page (`20260914-archive4`). The existing helper change adds only the exact `archive-status` service to its credential destination allowlist. Old pages retain their existing behavior; no bulk HTML rewrite ran. Page diagnostics copy a URL without query/fragment, page/build identifier, asset version, last successful poll and checkpoint commit. Deployment timestamp is explicitly unverified/null until an actual release records it; no deployment date is fabricated.

## Validation

All implementation and testing were local. GitHub operations and official Supabase/OpenAI documentation retrieval were remote. No production auth attempt, database row read/write, provider configuration change or deployment was performed.

```powershell
node --test tests/archive_status.test.mjs tests/archive_rebuild_ui.test.mjs tests/admin_auth.test.mjs tests/owner_access.test.mjs tests/owner_access_ui.test.mjs
python -B -m unittest discover -s tests -p test_archive_rebuild_status.py -v
```

Final Node result:

```text
# tests 42
# pass 42
# fail 0
# cancelled 0
# skipped 0
```

Producer compatibility result:

```text
Ran 15 tests in 0.142s
OK
```

**57 passing local cases**. Seven changed JS/TS source/test files passed `node --check`. The production TypeScript entry point was imported under a synthetic Deno environment and its anonymous request rejected without database/source access; this is Node import/wiring evidence, not a real Deno Edge Runtime execution. No new dependency was installed. All functional tests passed first run; the final wiring test was added after entry-point review and passed with the combined 42-case Node run.

Coverage includes real baseline counts, privacy-field rejection at all object boundaries, malformed metrics/provenance, unknown Google/eligibility, auth revocation during fetch, sanitized outages, exact credential destination, concurrent source reads/cache expiry, stale-source failure, job heartbeat separation, actual page-shell asset/metadata checks, DOM rendering, full denominator, 20-second checkpoint changes, session races, non-overlapping polls, hidden tabs, timeouts and recovery. Existing owner access and R3 producer tests verify the reused interfaces. No operational source generator was run, so no page/counter output was regenerated.

**Visual browser verification blocker:** `mcp__cua_repl` inventory returned `{"apps":[],"browsers":[]}`. Chrome and Edge executable files exist, but no browser automation surface is exposed. DOM tests execute the actual new page script against elements identified from the actual HTML; they are not screenshot, layout, real browser-cookie, staging or public-output evidence. No browser test, normal operational localhost URL or watchable deployed monitor is claimed. No browser fixture/server was left running.

Read-only source check:

```text
git cat-file -e origin/main:data/audit/issue229_archive_rebuild_status.json
fatal: path 'data/audit/issue229_archive_rebuild_status.json' exists on disk, but not in 'origin/main'
Production main feed present: False
```

Known diagnostic limits: earlier reads in R3's sparse worktree could not see excluded owner-auth files; Git object reads confirmed their real tracked locations, and this new worktree includes the needed subtrees. The web reader rejected Supabase's Markdown content type; direct HTTPS retrieval succeeded. Relevant changelog items did not change this reused custom-session auth pattern. Sources: [Supabase changelog](https://supabase.com/changelog.md), [Edge Function authentication](https://supabase.com/docs/guides/functions/auth).

## Changed files and preservation

1. `docs/admin/admin-auth.js` — one service allowlist entry.
2. `docs/admin/archive-rebuild.html` — owner monitor shell/styles/versioned references.
3. `docs/admin/archive-rebuild.js` — authorized rendering/polling lifecycle.
4. `supabase/functions/archive-status/core.mjs` — strict checkpoint consumer, GitHub reader/cache and job age.
5. `supabase/functions/archive-status/handler.mjs` — session-only read boundary.
6. `supabase/functions/archive-status/index.ts` — production runtime wiring.
7. `tests/archive_status.test.mjs` — endpoint/contract/source/auth regressions.
8. `tests/archive_rebuild_ui.test.mjs` — page/polling lifecycle checks.
9. `data/audit/issue229_owner_monitor_r4.md` — this report.
10. `Codex_Reply_Issue229_OwnerMonitor_R4.md` — separate required root receipt, committed after the implementation SHA is known.

Source/reconciliation/status JSON and public archive HTML/sitemaps are unchanged. Original dirty checkouts, unpublished ShiftCommander work, previous worktrees and PRs remain preserved. Only explicit files are staged; no cleanup, full generator, branch merge, deployment, auth rotation, schedule cutover or member communication occurred. Single worker under #116; no subagents or additional model launch. Runtime-local matching session reports `gpt-6-astra`, CLI `0.153.4`, at `2026-09-14T13:13:55.674Z`; no provider attestation claim.

## Next integration and operational proof

1. Review the source-recovery/reconciliation/feed stack #230/#231/#232 and this monitor PR. Keep historical eligibility/privacy/course/status and #228/#140 publication gates intact. Integrating monitor source does not approve public archive generation.
2. With a browser surface available, validate the page visually and on mobile with synthetic status and existing owner-session behavior. Confirm logout, expiry, stalled job, interrupted source, tab restore and a new checkpoint.
3. Verify the existing server GitHub read-token configuration privately; establish the intended committed status source. Deploy the new Edge Function with custom owner-session verification and the page/assets together. Record a real deployment timestamp/build reference and verify every changed live asset plus anonymous 401 and authenticated owner read. No new account or secret should be guessed/provisioned merely because this report names a configuration variable.
4. Connect approved archive builder/validator/sitemap/deploy/GSC workflows to R3 checkpoint writes and committed feed publication at meaningful batches (not per page). That source-update integration does not yet exist. The backend reads committed checkpoints, not an unpushed local file. Google observations require actual timestamped evidence.
5. Prove one real job update reaches the owner page within the 30-second target. A 20-second completion-to-next-poll cadence plus a 10-second source cache is the intended low-latency path, but slow network/authorization is not a strict 30-second SLA; measure it during staging. Establish an independent missing-heartbeat observer and its heartbeat/escalation. A browser left open by Brian is not the only monitor.

Expected outcome: actual archive job checkpoint -> committed status -> authenticated delivery -> matching owner view. Last complete real-world success: **none established**. Component state **BUILT** with synthetic tests; not PROVEN/MONITORED/HEALTHY. Producer checkpoints should occur within 300 seconds while RUNNING; source/authorization errors fail closed. Browser read age is shown, but independent observer/observer health remains unproven. Preserve last good source and Git history on failure; restore authorized access/source connection, then allow a fresh validated response. No automatic credential replacement or writer-lock stealing.

Full archive restoration/editorial/sitemaps/GSC acceptance remains IN_PROGRESS. This branch contributes protected delivery and owner-page code; it does not claim a production monitor or archive release. #214 remains independently blocked, with R57 receipt already pushed at `bb32cc7ad1ca0756a77f955660ba632ae9dc15a9`.
