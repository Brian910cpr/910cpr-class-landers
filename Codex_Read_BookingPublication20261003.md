# Booking publication outage — 2026-10-03

- Timestamp: 2026-10-03T12:02:00Z.
- Branch: `codex/booking-reliability-20261003` (pushed).
- Implementation commit: `840d6162e3931ed7d007d6a8e787b9fc0c4dd588`.
- PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/343
- Manual production recovery: VERIFIED / PROVEN.
- Durable timer: PR_OPEN / BUILT; credential activation and scheduled-cycle proof pending.

## Exact failure

The live browser gate `datesForPublication()` removed 7,612 dynamic course offers
because the feed-wide `validUntil` had expired. Seven real classes survived. BLS
Initial went from 2,425 starts to one. The feed itself still contained the offers.
GitHub's ten-minute configured Cron actually ran hours apart, so another manual
refresh alone does not permanently repair this recurring failure.

## Recovery already deployed

Dispatched existing bounded refresh run 37120275947, completed successfully at
11:45:40 UTC. Production GitHub Pages deployed
`7150450b1c1b5902581a36a61e5174f4e4ee09cd` at 11:46:28 UTC. Browser reloaded the
real `https://www.910cpr.com/bls`, rendered Initial appointment dates and October 5
starts 07:45, 08:15, 08:45, 09:15, 09:45, 10:15, with an Enrollware appointment link.
The 11:55 UTC public feed contained 7,643 course offers / 2,779 date/start pairs /
80 dates, valid until 09:11 Eastern. October 12 retained 09:00 Renewal, 12:00
HeartCode and 17:00 Initial; unrelated overnight and 12:45 offers were absent.
Initial and Renewal were individually checked in the rendered browser.

## Review files

- `worker/availability-refresh-watchdog.mjs`: independent Cron invokes the existing
  publisher before expiry; no scheduling rules or leases changed.
- `worker/wrangler.availability-refresh.jsonc`: dedicated new Worker, no existing
  free-time Worker route/binding/config changes.
- `tests/availability_refresh_watchdog.test.mjs`: 12 tests for early recovery,
  expired/public-feed failure, deduplication, credential errors, bounded bodies,
  timer staleness, hung jobs, and read-only public health.
- `.github/workflows/verify-canonical-participants.yml`: independent health check.
- `docs/availability-refresh-watchdog.md`: primary incident report and operating contract.
- `data/audit/booking_publication_dropout_20261003.json`: exact before/after counts.
- This reply.

## Validation and deployment boundary

Node syntax validation, 12 Node tests, workflow YAML parse and Wrangler 4.60.0
deployment dry-run passed. PR preflight, truncation guard and Cloudflare Pages
preview checks passed on implementation commit. No sitewide generator ran.
The emergency refresh produced its existing bounded generated-data output.

Created dedicated KV namespace `53b5ac2432a946efaf2c094c07142ba7`. The new Worker
has not been activated. It requires `GITHUB_ACTIONS_TOKEN`; the existing local
GitHub OAuth credential has broad `repo` and `workflow` access. Owner approval
was requested before moving that credential into persistent cloud storage. A
repository-restricted Actions token is the narrower alternative. No credential
has been copied or exposed. Local Wrangler auth is location-blocked (9109);
the authenticated Cloudflare connector works and is the deployment route.

## Remaining work

After the credential choice: provision the approved encrypted secret, merge PR,
deploy the dedicated Worker, enable its five-minute Cron, and observe an actual
scheduled dispatch -> successful publisher -> newly published feed -> rendered
booking calendar. Observe a later timer cycle before calling cadence healthy.
The health endpoint reports expired feed or >12-minute missing heartbeat as 503;
the existing GitHub health workflow is a delayed independent observer, with no
five-minute alert guarantee. See the primary report for recovery/escalation limits.

Unrelated Windows case-collision modifications `docs/Earl/index.html` and
`docs/Jackson/index.html` remain unstaged. No cleanup was attempted. No new
temporary runtime files were staged. No production schedule/roster policy was
weakened. The separate absent unattended Enrollware roster collector is unresolved.

ChatGPT next action: retain the exact expiry/cadence finding; do not rediscover or
replace it with another scheduling-rule rewrite. Resume credential activation
and record real automatic recovery proof. Do not describe the timer as healthy
from the manual recovery or green PR checks alone.
