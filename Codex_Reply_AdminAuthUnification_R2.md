# Owner access repair built

- Timestamp: 2026-09-13T17:50:00Z
- Work-item state: BUILT
- Issue: #215; deployed secret parity remains #140.
- Branch: codex/repair-admin-and-public-portals.

Eight owner pages now use one session key helper, with guarded requests, stale-response protection and private-state cleanup. Owner-only Class Registry, Class History, Production Board, Canonical Session Workspace and NOW APIs delegate to the deployed HOT_SYNC Worker. Corporate sessions no longer authorize those APIs. The legacy public/corporate session-workspace API and its verified baseline are preserved. Operations uses the canonical Admin Port for full participant detail.

Validation: 36 Node tests and 3 Admin Port tests pass; all eight actual admin page scripts pass DOM checks with private fixture data, including lock cleanup. Seven legacy session-workspace baseline tests pass. Source integrity and diff whitespace checks pass. Existing unrelated test failures remain: dashboard_schedule static expectation for a removed conflict label, and two Maxim suite expectations in unchanged BLS/self-service pages.

Not proven: accepted-key owner browser session; actual Cloudflare/GitHub secret parity; separate Finance Worker secret parity. No password was guessed, rotated, exposed or written to source. The R1 audit was not a deployed migration. Publication and live checks follow in a separate receipt.
