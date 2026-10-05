# Layered scheduling production readiness — 2026-10-05

State: BLOCKED. The new production scheduling model has not been integrated or deployed.

## Current evidence

Audited origin/main 529b5eb20 in an isolated worktree on branch
`feat/layered-production-20261005`; the previous local lab and legacy repair branches
were not copied over current main. Main has additional roster/publication safeguards.

Read-only canonical Supabase query at approximately 02:35 UTC found 222 locations
and **zero resource rows**. The query inspected only resource metadata/counts; no
registration, roster, payment or calendar records were changed. Public schema
contains a `resources` table but no table whose name includes availability,
calendar, commitment or schedule. This table-name check is not proof that no
alternate application can own such a ledger.

`data/config/calendar_sources.json` declares instructor inputs: Amy/Nick explicit
availability and Brian's dedicated DoNotSchedule inverse blocking source. It does
not declare room free intervals. Brian's personal public calendar is not a substitute.
`data/config/location_resource_map.json` confirms the Shipyard Office appointment
container label, explicitly leaves A/B/C containers unconfirmed, and normalizes
venue aliases. It does not declare room hours or concurrent-class capacity.
An appointment container provides a booking target, not room capacity evidence.

Therefore the required room availability ∩ qualified instructor availability
cannot yet be constructed from the inspected authoritative inputs. Using the lab's
08:00–20:00 room fixture, inferring that rooms are always free, or treating student
seat capacity as concurrent-class capacity would invent production truth.

## Independent implementation

`scripts/layered_resource_readiness.py` is a read-only preflight with explicit
timezone, freshness, resource identity, single-room concurrency and complete
commitment coverage requirements. It retains room/instructor source identities in
intersection diagnostics, supports midnight intervals, and cannot publish offers.
It is deliberately not enabled in the production refresh pipeline: doing that
before supplying room truth could remove otherwise valid inventory.

Run `python -B -m unittest tests.test_layered_resource_readiness`.
For a separately prepared explicit coverage snapshot, run
`python -B -m scripts.layered_resource_readiness SNAPSHOT.json`; JSON goes to stdout,
exit 2 means blocked. No files or services are mutated by this command.

The snapshot contract has:

- `resources`: id, active, location. No default resource or capacity is inferred.
- `room_availability`: id, resource_id, location, simultaneous_classes=1.
- `instructor_availability`: id, instructor_id, locations.
- `commitment_coverage`: id, instructor_id, location.
- Every interval row: start/end with timezone, observed_at, freshness_minutes,
  source, status=`known_complete`. This assertion must come from an authoritative
  adapter, not a model-generated fixture.

`RESOURCE_INPUTS_READY` only means these inputs intersect; it does not prove course
qualification, occupancy, duration, travel, roster reconciliation, booking URLs or
public output. The legacy selector/publication path remains unchanged.

## Exact next integration prerequisites

1. Identify the authoritative room ledger and its coverage horizon. If no ledger
   exists, obtain an explicit owner decision defining Shipyard resource identities,
   available intervals and simultaneous-class capacity. Confirm whether physical
   A/B/C rooms or the Office container are the scheduling unit. This assignment
   does not create those persistent records or expand booking containers.
2. Export resource/instructor coverage with independent source timestamps, canonical
   instructor identities, actual commitments, course metadata and directional travel.
   Implement read-only adapters; retain current roster reconciliation gates.
3. Promote the existing pure layered engine rather than inventing a second engine.
   Brian's owner eligibility is all families/bodies/variants except ACLS/PALS,
   including skills; other instructor qualifications remain explicit. Catalog identity
   is not booking-link proof, especially for extra ARC variants.
4. Shadow-run current source days through source → occupied intervals → merged
   blocks → edges → both skills families → constraints → public offers. Paid growth
   moves the edge; independent free windows remain available. Preserve actual enrolled
   classes and their 24-hour exception. Trace every accepted/rejected candidate.
5. Resolve Oct7/8/17/24 records through separately approved source reconciliation
   when required. Their earlier proof issues are historical evidence, not revalidated
   current counts in this checkpoint. No stale-roster override or canonical edits.
6. Only after shadow parity/positive coverage, add a guarded publication adapter,
   run required CI, merge, execute the established refresh and verify rendered
   Oct10 13:00/16:30 skills plus representative free/paid/overnight days. Rollback is
   reverting that future integration commit; no cutover has occurred here.

This moves toward Enrollware independence by separating resource truth from
appointment-link containers, while keeping those existing links operational.
Repeated skills growth conflicts with daily compaction/course suppression in the
legacy selector; retaining that path is a temporary release state, not acceptance
of those rules as the new model. Detailed historical comparisons and regression
fixtures remain in the local scheduling lab.

## Verification limits and operational proof

Seven focused preflight regressions pass. No generator, full rebuild, external
mutation, deployment, rendered-page repair verification or broader production CI
was run for this checkpoint. Existing unrelated Earl/Jackson HTML changes were
observed and excluded. The pure preflight is BUILT, not a persistent operational
monitor. There is no new observer, cadence or recovery service to report healthy.
