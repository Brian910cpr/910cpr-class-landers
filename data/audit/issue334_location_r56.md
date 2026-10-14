# Issue 334: authenticated native venue proof and bounded repair

2026-10-14 UTC. Branch: `codex/issue334-location-proof-20261014-r56`.
State: locally validated; production release gated. No production mutation or deployment.

## Authoritative evidence

Authenticated Supabase connector, LanderWare project `wktwgcnwdvbebcobgyey`, SELECT-only reads:

```sql
select s.id, s.location_id, s.source_location_label, l.name as canonical_location_name
from public.class_sessions s left join public.locations l on l.id = s.location_id
where s.id = 'dfa08088-1266-4dd6-ad7d-14856b7f845a';
```

Result: location_id `fd44e20f-af86-4198-ab7c-fa13dad6a7fd`, source_location_label
`4018 Shipyard Blvd, Room B, 910CPR Office`, canonical_location_name
`910CPR Office - Shipyard Blvd`. A further exact-session SELECT established
`resource_id=null`, canonical location_key `910cpr-office-shipyard`, and the
`class_sessions_resource_id_fkey` references `resources.id`.

```sql
select id,location_id,resource_key,name,capacity,active from public.resources
where location_id='fd44e20f-af86-4198-ab7c-fa13dad6a7fd' order by resource_key;
```

Result: `[]`. This proves the venue relationship, not a Room B assignment.
No room is created or assigned. The source label and original occupied interval
remain intact. The existing owner policy reserves the primary room for venue-only
occupancy and prohibits automatic relocation.

## Smallest repair and safety

- Add the exact proven native label as a **venue alias**, not an internal room alias,
  in `data/config/location_resource_map.json`.
- In `scripts/layered_publication_adapter.py`, apply the existing primary-room
  fallback before relevance filtering. Previously another instructor's venue-only
  occupancy could be discarded before `build_shadow` applied that same fallback.
  Explicit known Room A/C resources retain their identity. Unknown offsite travel
  still fails closed; no travel rule or duration is invented.
- Tests traverse `build_occupancy`, calculation, selector JSON and HTML rendering;
  check both same-instructor and other-instructor conflicts; preserve explicit Room A.

This promotes canonical LanderWare Location identity rather than relying on label
similarity or Enrollware IDs. Existing scheduling objects/policy are reused.

## Bounded local evidence

`data/audit/issue334_location_r56_proof.json` retains authenticated facts and a
synthetic October 11 regression using the proven label (not actual November 3
capacity). Before: one input source/window, zero evaluated, one failed window,
zero offers; exact missing directional travel rule retained. After: same source
and occupied 12:00-14:00 interval, one evaluated window, zero failures, six offers
at three starts (09:30, 11:00, 14:00), no overlap. These numbers do not predict
production offer counts. No public pages or source snapshots regenerated.

```text
python -B -m unittest tests.test_layered_location_aliases tests.test_layered_selector_adapter tests.test_layered_publication_adapter tests.test_layered_publication_pipeline tests.test_family_publication_coverage tests.test_layered_resource_readiness -q
Ran 55 tests in 6.692s
OK
```

AST parsing for changed Python sources, JSON parsing and `git diff --check` pass.
Earlier test-development failures (wrong offer field names and an expectation
that externalized URLs were embedded in HTML) were corrected; final suite passes.

## Current public evidence and remaining gates

Read-only live audit at `2026-10-14T08:23:45.304309+00:00` is retained in
`data/audit/issue334_location_r56_live.json`. All eight families have 191 input,
189 evaluated, two failed windows, including two November 3 failures.
BLS: 3,622 offers / 88 dates (3,612 dynamic, 10 seated); Heartsaver: 7,565 / 88.
Both are unexpired at the sample. Audit intentionally exits 1 for coverage alerts.
ACLS/PALS are seated-only with expired payload timestamps; do not infer dynamic
freshness from their retained seated choices. This is pre-repair production evidence.
No current browser interaction, checkout or payment proof claimed.

Latest sampled natural public observer `38514856448` failed; earlier scheduled
`38469671908` succeeded. Sustained five-minute observation remains unproven.
`AVAILABILITY_WATCHDOG_HEALTH_URL` GET returns HTTP404. Existing secure encrypted
repository-restricted Actions read/write credential gate remains unchanged.
No secret values read, activation retry, competing refresh or monitor.

Persistent classification: prior publication PROVEN; this repair BUILT and locally
validated; overall HEALTHY unestablished. Outcome: continuously legal selectable
bookings. Failure: expired feeds or failed/unevaluated windows. Observer: public
booking audit plus supervisor; multi-hour schedule gaps/absent cloud health prevent
reliable observer health. Local containment still requires CYBERPC awake/online/login.
Recovery: review/probe this patch, bounded approved release, customer/output proof;
then existing secure cloud provisioning and natural recovery/observer proof.

## Release scope and rollback (not executed)

No complete build chain is requested. Review this patch, then use the existing
`refresh-admin-availability.yml` read-only `v2_release_probe=true` path on this branch
to obtain current all-family proof before a release decision. That probe writes only
runner-local input/build diagnostics and `data/runtime/audit_previews/v2_release_probe/`;
it does not commit or publish. Preserve its artifact and verify zero failed windows,
occupied intervals and correct November 3 choices across all eight families.

Merging the config change triggers the existing main admin publisher. Its expected
write surface is 17 configured selector/alias/redirect HTML files; eight family JSON
feeds under `docs/data/block-selector-availability/`; matching canonical schedule,
admin availability/reference/landscape/anchor/ical data; current native anchor class
pages under `docs/classes/`; calendar snapshots and workflow-listed audit/status
files. Estimate 40-60 changed generated/state files, variable with current inventory
(prior approved comparable release changed 38). The exact allowlist is the commit
step of `.github/workflows/refresh-admin-availability.yml`, plus configured paths in
`data/config/block_schedule_pages.json`; no sitewide class/hub rebuild is proposed.
Obtain specific approval for this production write scope after current probe proof.
Stop for more than ten unexpected changed files. Do not count unrelated checkout
changes as intended generated output.

Rollback: revert only this PR's config/adapter changes through a reviewed commit;
let the existing approved publisher restore matching outputs. Do not reset dirty
work or weaken freshness/conflict/link audits. The old behavior can restore the two
known fail-closed windows; preserve live audit artifacts to assess that tradeoff.

After release: require zero failed windows across all eight live families, verify
actual November 3 BLS/Heartsaver rendered choices and linked assets/registration
handoff without submitting a booking, and observe successive renewals before expiry.
Keep #334 open until the operational evidence gates are satisfied.

## Work hygiene and queue

Original `E:/GitHub/910cpr-class-landers` remains untouched and dirty. Separate
worktree based on `47a10dc2d2c6853a9fe88e96f4fb7b485334b07e`. Windows case-collision
changes in `docs/Earl/index.html` and `docs/Jackson/index.html` excluded explicitly.
Open PRs/owner queue swept. #383 is a different ongoing scheduling change; #387
checkout, #389 documents, #388 finance and fleet preflight remain existing streams.
No matching open native venue repair PR exists. No unrelated safe unassigned
backend quick win selected; no competing deep stream. Draft #372 untouched.
No `ops/handoff/next_task.md` use. No participant PII in evidence.
