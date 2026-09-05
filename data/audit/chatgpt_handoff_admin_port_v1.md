# ChatGPT handoff: Admin Port v1

## Outcome

Issue #138 adds one read-only operational screen at `docs/admin/admin-port.html`. It consumes the exact Session Bundle contract merged in PR #137 through the authenticated `schedule.910cpr.com/admin/session-bundles/<date>` endpoint; it does not define or mutate a parallel record model.

Canonical bundles are stored under the existing private R2 binding at `private/session-bundles/<date>.json`. Authentication is verified before storage access, and successful responses use `Cache-Control: private, no-store`. No bundle is shipped under `docs/data/`.

## September 19 behavior

- 09:00 Hendersonville Family Dental and 11:00 Little Leaps are visibly scheduled and reserve customer availability.
- The 14:00 Accelerated Academy/Hendersonville record is visibly cancelled, remains in history, and has no blocking resources.
- Participant evidence renders as `Unknown — source evidence absent`, based on the `registrations_not_present` dependency. It never converts the empty export array into a confirmed zero.
- Each card exposes its canonical session ID and exact source-system/source-ID pair.
- Bundle-level provenance, conflicts and all missing dependencies remain visible beside the day.

## Files

- `docs/admin/admin-port.html`
- `docs/admin/admin-port.css`
- `docs/admin/admin-port.js`
- `docs/admin/admin-nav.js`
- `worker/admin-api.js`
- `tests/test_admin_port.py`
- `data/audit/chatgpt_handoff_admin_port_v1.md`

## Validation

```text
python -m unittest tests.test_admin_port tests.test_session_bundle tests.test_canonical_schedule_hot_sync
............
Ran 12 tests in 0.600s

node --test tests/admin_api.test.mjs
17 tests passed, including unauthenticated denial before storage access and authenticated private read.
OK

git diff --check
```

The page was served locally and visually inspected. Its accessibility tree exposed all three sessions, both blocking decisions, the cancelled/non-blocking decision, unknown participant evidence, all three missing dependencies, empty conflict state, and bundle provenance.

## Scope and open questions

- Persisted locally and dry-run/visual validated only; endpoint and private object not deployed.
- The date picker intentionally fails clearly for dates without a published bundle. A future slice should add a generated bundle index/API after more dates exist.
- Admin Port v1 is read-only and has no production writer endpoint.
- Current Windows checkout still exposes five unrelated case-colliding generated HTML modifications; they must remain unstaged.
