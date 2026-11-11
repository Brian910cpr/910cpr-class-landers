# Bounded first-party publication

Implementation state: **BUILT**, default off. **Skills activation is blocked:** context-safe native remaining-seat admission is not implemented. A first held skills seat remains correctly occupied, but its second seat is not yet publicly selectable. This change neither activates native publication nor proves the live registration path.

## Source and output contract

- Read fresh canonical demand from the existing first-party endpoint and current configured Google calendars. Never invoke the external session fetcher, external class-page confirmation, historical container bounds, full-site rebuild, or HOT_SYNC export.
- Preserve every retained public occurrence as conservative geometry. Reconcile participant counts from canonical demand; unmatched counts remain unknown. New native public sessions come from canonical demand. The existing layered engine also reads the full canonical demand, including private/offsite commitments, holds, and reserved seats.
- Reuse the existing scheduler and strict native selector validation. No new business-hours rule is introduced.
- With skills disabled, only six public paths are staged: the retained/reconciled schedule, BLS HTML and its two existing aliases, the BLS selector JSON, and its versioned shared availability reader. Private calendar exports, runtime inputs, audit detail and participant data never enter the commit or preview artifact.
- Only full-course BLS 209806/359474 dynamic native-v2 choices are admitted in this baseline. Retained sessions keep geometry/counts. Existing BLS seats are admitted only with a fresh exact-identity STABLE snapshot of native authority, active scheduled-session profile/catalog, and positive known remaining capacity. The separate `skillsEnabled: false` gate retains this BLS-only baseline. When explicitly activated after the independent backend/qualification gates, it adds only course 509474 on Heartsaver (cpr-aed, first-aid-cpr-aed), ARC (arc-blended), and HSI (hsi-blended). Skills uses its existing 45-minute instruction, 15-minute cleanup, capacity-two policy. Bundle 210549 and other full-course mappings remain excluded.

## Modes

`python -m scripts.run_native_publication build --preview` temporarily enables the local native scope, restores the exact original configuration even on failure, and emits a non-publishable preview manifest. It requires already-fetched fresh first-party inputs.

`python -m scripts.run_native_publication build` requires native mode already enabled. The manual workflow defaults to preview. Publication additionally requires `publish=true`, a main dispatch, unchanged source files and source commit, and unchanged remote main. A preview manifest cannot be published.

The retired public refresh and admin availability/probe workflows have a prerequisite source-mode job. Native mode skips their entire legacy jobs before any feed or page fetch. Invalid configuration fails closed rather than choosing the legacy route.

## Freshness and race behavior

The original calendar observation remains the proof. It expires at most 15 minutes later. A build timestamp, unchanged source hash, retry, deploy delay or new commit never extends it. Demand is revalidated at consumption and publication. The publisher requires at least five minutes of source-proof lifetime immediately before staging; the visible verifier requires at least one minute after seeing the exact output.

All publishers use `schedule-publish-main` with no in-progress cancellation. A changed main fails the run rather than rebasing old generated output. The next attempt must fetch fresh inputs and rebuild. Normal fast-forward push provides the final race guard. The script stages exact paths, never a directory or `git add -A`.

After pushing, the workflow explicitly requests the existing branch-based Pages build. It does not change Pages settings. A green commit or deployment is insufficient: the verifier polls the real site and requires SHA-256 matches for every gate-selected output file while the original proof is still valid. Only that observation advances the private run artifact from `BUILT` / `PUSHED_NOT_PROVEN` to `PROVEN`. Failure or expiry writes a sanitized failure artifact and leaves existing browser expiry behavior in place. No stale proof is restamped and no external publisher fallback is invoked.

## Activation gates

1. Verify the existing Pages source is branch-based and the workflow token can request its build. If the site uses Actions deployment instead, provide the reviewed deployment adapter before activating. No hosting/settings change is included here.
2. Run the native preview from the exact intended commit with fresh first-party inputs. Check output counts, retained sessions, unknown occupancy, qualification/commitment exclusions, and the actual BLS page and native registration path. Local fixtures do not replace that proof.
3. Enable the native scope only after the source, canonical checkout/confirmation, and supported-course activation gates are independently satisfied. Unadmitted seated CTAs remain suppressed without changing their occupied intervals or counts. Admitted native seats use the owned canonical session URL and require the new snapshot booking-admission DTO.
4. Execute an authorized real publication and prove all visible file hashes before expiry. Measure fetch/build/queue/deploy timing across repeated cycles.
5. Enable a five-minute schedule only after an independent observer is active. The observer must check the actual visible original proof and registration read path, alert on missed or stale cycles, and have its own heartbeat checked by another existing operational observer. GitHub cron can be delayed or dropped; a five-minute cron expression is not an availability guarantee. If observed delays cannot fit the 15-minute proof, use a reliable publication service rather than enlarging or restamping the lease.
6. Add an explicit scheduled-event condition when activating the commented cadence: scheduled runs must publish on main, not take the manual preview default. Review any other writer that can overwrite the same selectors.

Recovery: retain source and failure evidence, fix the failed first-party component, fetch again and rebuild from current main. Token/hosting access changes and new course activation require appropriate authorization. Routine stale detection must not depend on a person remembering to check.

## Existing native seat continuation

A newly materialized native class remains its existing physical class on subsequent publications. One held seat in a proven capacity-six class produces a seated choice with five remaining seats via `/register/?session=lw-...`. The layered scheduler retains the occupied interval and does not materialize a duplicate dynamic choice. The public DTO exports only bounded admission/capacity fields, not private IDs, profile internals, or student data. Profile or catalog deactivation removes the CTA while preserving all occupancy. Browser admission expires against the original canonical observation even if a global publication timestamp changes; legacy seated-class compatibility is unchanged. Checkout rechecks current canonical seats and profile before reserving.

## Abandoned-hold maintenance

There was no repository-defined scheduled cleanup caller. The old on-demand release occurred only after a selectable offer was resolved. An expired, zero-registration native class could therefore remain an occupied/day-anchor source while its seated choice was hidden. Even a later database cancellation alone was insufficient because retained public geometry is deliberately not removed based on absence.

The production publisher now calls a bounded owner-authenticated maintenance POST before fetching canonical demand. Preview and GET remain read-only. The separate database maintenance policy defaults to disabled and requires an authorized activation. The transition uses existing lifecycle emptiness/witness rules and matching locks, with at most 32 exact classes per call, within the next 90 days. Paid/unknown evidence, fresh holds, any registration history, staff edits, and missing lifecycle witnesses prevent release. No class, order, registration or witness is deleted.

Fresh canonical source reads request release proofs only for retained native IDs, in complete read-only batches of at most 64. The base GET does not scan cumulative release history. A fetch checks every requested batch before replacing its snapshot, retains the earliest original observation time, rejects active/released conflicts, and never silently truncates. Its fixed 64-batch work budget is separate from the unbounded historical witness count. Exact owner-authenticated proof responses contain tombstones for unchanged, canceled, still-empty witnessed native classes. The projection retires only an exact canonical/external identity and instruction/consumption interval match. Missing rows, legacy identifiers and unproven cancellations cannot clear geometry. A bounded last-verified native identity/interval DTO survives missing reads solely as release-matching provenance. It never supplies current demand, seats, or booking admission. A later fresh tombstone must match both that original identity and all retained instruction/consumption bounds. Older rows with no recoverable canonical provenance remain unknown blockers instead of being removed by external ID alone or aborting unrelated safe publication. The actual occupied records and lifecycle history remain in the database. Repeated production runs progress a larger backlog in bounded batches; the existing session-reuse validator still rechecks qualifications and competing commitments before reopening a released identity.

Activation additionally requires applying the reviewed maintenance migration and endpoint update, explicitly enabling its default-off policy, and proving the authorized production prefetch path. Until that happens, no active cleanup cadence is claimed. The route uses existing private owner-app authentication only; it adds no authority to public checkout clients or confirmation callback tokens.

## Bounded skills publication

The skills gate adds exactly nine public outputs from the existing page generator: `docs/heartsaver.html`, `docs/HEARTSAVER.html`, `docs/heartsaver-schedule.html`, `docs/data/block-selector-availability/heartsaver.json`, `docs/arc.html`, `docs/data/block-selector-availability/arc.json`, `docs/hsi.html`, `docs/hsi-schedule.html`, and `docs/data/block-selector-availability/hsi.json`. The three pages expose only the skills-only option and existing context choices, without granting certification/qualification or activating a course profile. BLS remains unchanged and retains canonical remaining seats.

The runner checks each configured output and audit path before invoking a page generator. The manifest, staging, preview artifact and live observer use the same six-or-fifteen-path allowlist. An unexpected alias, missing or extra path, modified file, changed gate, stale proof or unsupported course aborts publication. Every enabled selector is strictly validated, including exact native destinations, context, duration, capacity, source trace and original-proof expiry. The manifest expiry cannot outlive its earliest selected offer.

Preview temporarily enables only the existing master gate, never skills. Skills publication, backend runtime admission, verified qualifications, catalog/profile activation and the maintenance policy remain separate gates. This local implementation supplies no hosted activation or production proof. Before any skills activation, add and prove context-safe seated admission for the existing physical class without duplicating its capacity pool. Activation also requires a current first-party preview and observed customer path within the original 15-minute proof, followed by an independent stale-cycle observer.
