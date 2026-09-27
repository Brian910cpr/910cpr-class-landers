# Group request and Maxim gate repairs proven live

- Timestamp: 2026-09-13T17:59:00Z
- Work-item state: VERIFIED
- Proof level: PROVEN for public group submission and the unauthenticated Maxim gate.
- Issue: #220.
- PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/221
- Merge: 76ebb52aad9b292ad6c2be4a7a3e6399ef1674d2
- Production run: https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/34772936739 (success).

Live group-training.html, request_group_session.html and corp/maxim.html return the expected current content. All 21 changed HTML/JS files return 200 and byte-match the commit. The public group form exposes all six course tabs, displays the course matching the selection, and enables its real submission handler. Maxim's login remains visible after DOMContentLoaded and the background main is inert. The temporary diagnostic that hid its gate was removed from shared motion code.

Two temporary proof records were used, with no messages sent:

1. API submission returned HTTP 200 and one reference. A retry returned the same reference. SQL confirmed one inquiry, one Brian action card, and inclusion in the NOW snapshot. Exact-id/name cleanup removed both records.
2. Actual browser submission selected PALS, filled synthetic contact data and clicked Send Request. The browser displayed Request received with a reference and disabled repeat submission. SQL confirmed the PALS inquiry, one Brian action card, and inclusion in the NOW snapshot. Exact-id/name cleanup removed both records.

The group-request Edge Function is version 1 with platform JWT verification enabled. It saves both the inquiry and the action card before success, handles retries without duplicate cards, and does not depend on an email transport. No booking, customer message, payment, employee change or real class registration was made during verification.

The scope is not HEALTHY or MONITORED. Corporate authenticated roster/scheduling behavior remains unverified without an accepted Maxim code. Owner password parity remains #140/#215 and is not implied by these public-page proofs.
