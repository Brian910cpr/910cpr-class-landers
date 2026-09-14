# Issue 235: Overnight appointment hours and same-day eCards

- Timestamp: 2026-09-14 16:47 UTC
- Branch: `codex/overnight-hours-same-day-ecards`
- Substantive commit: `5145b9bd41c`
- Work-item state: `IN_PROGRESS`, locally validated and awaiting push, PR checks, merge, production generation, deployment, and live verification.
- Persistent-system evidence level: `BUILT`.

## Owner instruction

Widen Brian's public appointment hours to include overnight starts without changing any underlying blocking or availability rules. Publish the truthful same-day eCard advantage on the four core AHA funnels.

## Work performed

- Changed only the dynamic public start-time boundary from `08:00`–`19:00` to `00:00`–`23:45` in `data/config/public_offer_policy.json`.
- Preserved quarter-hour increments, 24-hour lead time, maximum horizon, course visibility, caps, real class occupancy, school/calendar blocking, ADR/travel buffers, duration fit, and fail-closed requirements.
- Added a same-day eCard and flexible skills-check service block immediately above the existing calendar on BLS, ACLS, PALS, and Heartsaver.
- Updated the generator and all eight tracked lowercase/uppercase page outputs without changing titles, descriptions, schema, selectors, registration URLs, or adding a click.

## Files changed

- `data/config/public_offer_policy.json`
- `scripts/build_bls_block_schedule_pilot.py`
- `tests/test_block_start_time_selector.py`
- `tests/test_filter_public_sellable_offers.py`
- `docs/bls.html`, `docs/BLS.html`
- `docs/acls.html`, `docs/ACLS.html`
- `docs/pals.html`, `docs/PALS.html`
- `docs/heartsaver.html`, `docs/HEARTSAVER.html`

## Validation

- Four focused unit tests passed, covering midnight, 02:15, 23:45, quarter-hour rules, and rendered service copy.
- Public-offer policy JSON parsed successfully.
- Modified Python generator compiled successfully.
- Strict site link scan: 992 public files, 41,869 links/buttons, 0 broken, 0 suspicious, 3 low-confidence review items.
- All eight page outputs contain the service promise and retain the selector shell.
- `git diff --check` passed.

## Proof contract and limitations

- Expected outcome: eligible overnight appointment starts appear only when the canonical availability pipeline finds an unblocked, duration-fitting window.
- Success evidence: a successful availability refresh produces a current selector artifact with an otherwise-eligible overnight start, and the live selector exposes its unchanged Enrollware registration handoff.
- Expected cadence: the existing public availability refresh cadence.
- Failure/staleness condition: policy is merged but selector artifacts remain stale, or a known blocked overnight interval is offered.
- Observer: existing refresh workflow diagnostics and recurring growth/site audits.
- Recovery path: repair the availability refresh, regenerate current selector artifacts, then inspect rejection reasons and the live selector.
- Escalation boundary: HOT_SYNC credential mismatch remains an account-level blocker if still unresolved.
- Current limitation: this clean clone lacks private `data/sessions_current.json` and the runtime dynamic-offer preview. The policy and rendering behavior are locally proven, but no claim is made that a real overnight slot is currently available.

## Next action

Push and merge the PR after checks, wait for GitHub Pages, verify the service message on all four live funnels, then run/observe a fresh availability cycle and confirm that an actually free overnight window can survive the unchanged blockers into the public selector.
