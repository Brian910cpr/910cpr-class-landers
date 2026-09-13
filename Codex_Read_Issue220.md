# Group Training and Maxim repairs built

- Timestamp: 2026-09-13T17:50:00Z
- Work-item state: BUILT
- Issue: #220; related paused redesign #148 is not being restarted.
- Branch: codex/repair-admin-and-public-portals.

The group form posted to a static page and had no submission handler. Request course tabs were incorrectly pruned as empty schedule inventory. A temporary diagnostic in shared interaction-motion.js hid Maxim's login gate regardless of authentication.

Repairs: persist a group inquiry and an owner-only Production Board action card before returning a receipt; retry with stable server-derived IDs; retain entered details on failures; keep every request course tab selectable; remove the diagnostic gate suppression; make Maxim sign-in and expired-session recovery explicit. Group requests also appear as short NOW prompts. No email delivery is claimed and the endpoint does not send messages. Prices and existing class creation workflows are preserved.

Validation: request validation, saved receipt/queue pairing, idempotent retry, queue-failure recovery and blocked-origin tests pass. Actual request-page DOM test proves course-tab selection stays usable. Actual Maxim DOM test including shared motion code proves the gate stays visible with no employee request before authentication. Public production deployment and a synthetic saved-request check follow in a separate receipt. No authenticated corporate scheduling or employee mutation was performed.
