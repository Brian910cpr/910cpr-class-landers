# Brian's NOW monitor

Work item: https://github.com/Brian910cpr/910cpr-class-landers/issues/216
Page: https://www.910cpr.com/admin/now.html

## September 23 repair and report projection

NOW uses the private owner session established at `/admin/access.html`. The obsolete hidden admin-key dialog and its incompatible `set()` call were removed. A signed-out visitor is redirected to the private access-link flow by `admin-auth.js`.

The first screen shows four facts: permanent classes in the next seven days, classes with recorded completions missing linked eCard evidence, people in the recorded eProduct queue, and unread root handoff files. Each count opens its source or a detail view. A missing source renders `—`, never zero. The short "Do this, Brian" list accepts only a structured `context_manifest.owner_action` with action, where, look_for, reply_with, do_not_touch, and why fields. Production Manager can supply that translation; a decision lane or blocked issue alone does not become Brian's task. Identical `root_action_id` values collapse to one card. Verified cash prompts retain their existing strict finance gate.

The endpoint reads a bounded catalog of existing repository reports on its own five-minute cache: public build audit, stale session audit, event schema audit, local supervisor record, and future schedule build. It returns only path, label, time, freshness and source link, not whole files. Older green files remain visibly **stale**. Report files are diagnostics, not end-to-end health proof. Adding a report to the catalog requires a known timestamp field and a review window; arbitrary repository files are not fetched or presented as current truth.

The financial snapshot remains disconnected until a trusted ingester supplies verified balances and complete obligations. The money panel stays collapsed and unverified until then. The monitor still needs an authenticated owner-session browser round trip and an independent observer before it can be classified beyond BUILT/CONNECTED.

## Behavior and source boundaries

- Read-only owner dashboard: prominent Brian decisions and fulfillment queues; one-hour browser-local snooze, full screen, Eastern time, minute refresh and stale banner.
- Uses the same `hotSyncAdminKey` tab storage and authoritative Worker check as Operations. The new endpoint does not accept corporate portal sessions.
- `owner_dashboard_snapshot()` is SECURITY INVOKER, denied to PUBLIC/anon/authenticated and executable by service_role. Financial input table is RLS enabled and denied to anon/authenticated. No private payload is emitted into static assets.
- Counts use existing canonical registration/session, completion, credential and order records. eCard queue means recorded completions missing linked eCard evidence, not proof a card was never issued. Historical imported eCard codes count as evidence. The total includes all qualifying records; details cap at 100 recent classes.
- The next-seven-days list is permanent operational class records only, not a claim that all external calendars have been reconciled.
- eProducts join order items -> orders -> registrations -> people and products. People are distinct; pending payment status remains visible at drill-through. No inventory secret values are queried or returned.
- Exchange reads public GitHub root Codex_Reply/Read receipts and open [CODEX] issues, with source links. Picked-up filenames are acknowledgements, not worker-heartbeat proof. Cache: five minutes per Edge isolate. Anonymous GitHub rate limiting is handled as unavailable/stale. No fabricated conversation, autonomous wake or message sending.
- Board ownership defaults to Brian on development work. Only decision-lane items or an explicit next_actor=Brian become Brian prompts. Existing dated records carry their timestamps and stale-source note.
- Internal drill-through opens a same-origin child tab with `rel=opener` so existing sessionStorage is copied by the browser and the monitor stays open. External links use noopener. No credentials travel in URLs.

## Financial input contract and remaining connection

No verified finance snapshot exists at initial deployment. This source is explicitly disconnected. Bank balances cannot be inferred from Stripe open invoices, receivables or old chats. No recommendation to pay was produced.

A trusted existing finance ingester can insert a snapshot in `owner_dashboard_finance_snapshots` using its service-side identity. No new public writer, credential or banking service was created. The source should remain recoverable in Google Workspace under the standing architecture directive.

Fields: observed_at, expires_at, obligations_through, source, payload. payload:

```json
{
  "obligations_complete": true,
  "accounts": [{"id": "personal", "currency": "USD", "available_cents": 0, "reserve_cents": 0}],
  "bills": [{"id": "source-bill-id", "account_id": "personal", "name": "Storage", "amount_cents": 0, "due_at": "2026-09-20T12:00:00Z", "status": "unpaid", "payment_url": "https://vendor.example/bills"}]
}
```

Illustrative zero-value schema only; never seed these as real facts. Cash evidence must be no older than 12 hours, unexpired, with explicitly complete obligations extending at least seven days. Every bill through that coverage boundary plus the account reserve is protected. Funds are not silently moved between personal and business accounts, and uncollected income never counts. Negative, duplicate, unknown-account and malformed values fail closed. Unknown or incomplete obligations produce no payment prompts. No payment execution exists.

Next integration action: connect the verified bank-available-balance plus upcoming obligation source used by the AM/PM cash process to this private contract. Preserve personal/business ownership, bill IDs, paid state, posted versus pending funds, and source timestamps. Do not invent reserves or assume missing bills are zero.

## Deployment and proof

Initial database check: 2 classes / 13 recorded completions lacking linked eCard evidence; 1 person / 1 eProduct item; 4 upcoming permanent class records. This is a point-in-time database observation, not final business reconciliation.

Production Board live version 3 had an attention route absent from the checkout. The source was reconciled with that deployed version before adding only the canonical owner-key check; existing attention behavior was preserved. The frontend accepts that key and opens `?card=` links directly.

Evidence level: BUILT / partial CONNECTED. SQL executed against production; privileged RPC grants verified; unauthenticated endpoint returns 401; JS syntax and 5 finance/priority behavioral tests pass. Actual page script verified in a DOM harness: count rendering, product drill-through, snooze/restore, filters, escaping untrusted source text, and ignoring late responses after locking. Browser localhost preview was unavailable. No current accepted Operations admin key was available for authenticated browser proof; the old chat code was rejected without changing credentials.

Expected outcome: unlock -> current source reads -> prompt -> exact roster/order/decision. Cadence: operations 60s while visible; GitHub 5m cached. Last successful proof: production SQL snapshot 2026-09-13, not yet an authenticated browser round trip. UI detects refresh failures and stale reads after two minutes; cash expires independently. Observer: open monitor tab. Observer health: browser clock and last-success stamp. No independent supervisor heartbeat is configured for this new monitor; do not classify MONITORED/HEALTHY. Existing handoff supervisors remain separate and their presence is not inferred from a receipt.

Recovery: retry bounded reads, inspect source state, preserve data; escalate only canonical credential/account configuration or missing financial authorization. Revert frontend commit and remove the new endpoint to roll back; private finance table can be retained empty. Production Board rollback must preserve the pre-existing version-3 attention route.
