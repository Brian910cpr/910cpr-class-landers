# October 17 adjacent-offer mismatch — diagnostic and provenance correction

Timestamp: 2026-10-15 UTC. Branch: `fix/availability-turnaround-20261015`.
Base: `a06d53897dd` (fresh origin/main). State: BLOCKED on policy/checkout proof; local provenance correction BUILT. Implementation commit: the commit adding this receipt (resolve with `git log -1 --format=%H -- scripts/build_bls_block_schedule_pilot.py`). No merge or deployment.

## Finding

The public offer is real and reproducible. A read-only HTTPS fetch returned 200 for `/data/block-selector-availability/heartsaver.json`, generated `2026-10-15T07:25:32.865218-04:00`. SHA-256 and sanitized exact records are in `data/audit/oct17_adjacent_offer_20261015.json`. On October 17 the feed has nine offers: three skills offers at 09:00 and six full/skills alternatives at 12:00. Heartsaver 209809 advertises 120 teaching minutes, reserves 150 minutes through 14:30, uses appointmentDayId 260788, and attaches to canonical source `3b2731a3-19bb-4d10-9757-08a8e81e336f`.

Public schedule session 14377157, BLS Renewal 359474, Brian, Room B, has 10:00–12:00 teaching and consumption bounds. Its zero-duration external iCal end was inferred using the 120-minute consumption rule. The public snapshot reports count unknown/stale reconciliation; the two-student count and native cleanup=0 come from the parent handoff and were NOT independently re-queried here. Unknown counts must not be rewritten as zero or used to erase occupancy.

There is no demonstrated native-checkout rejection in this evidence. The earlier refusal was the parent assistant's interpretation of 120+30 cleanup. Treating that refusal as an observed backend validation failure would be false.

## Provenance and root cause

1. `block_start_time_selector.build_block_schedule_page` selects the active `layered_scheduling_policy.json` path (`active_local_v2`). It does not use the legacy dynamic generator's default buffers for these final offers.
2. `build_occupancy` prefers canonical consumption bounds. `layered_selector_adapter.build_shadow` preserves actual existing occupied intervals. It gives NEW full candidates 120+30 minutes and skills candidates 45+15, with the evidenced 344085 exception 90+15.
3. The adapter passes global transition cleanup=0, because candidate consumption already includes cleanup. `layered_scheduling_engine` uses half-open conflicts: a right-edge candidate may touch the stored occupied end. Thus the source ending at noon yields a noon candidate; cleanup is not appended retroactively to the existing source.
4. `matching_container` validates the owned continuous Brian/Shipyard range. June 21 ID260670 +118 days = October17 ID260788. It constructs the course-specific URL; it does not query actual appointment-day inventory. The container interval is June21–April30 and ends at ID260983. It is venue-level `Shipyard Office`, not proof of a fresh Room B assignment in Enrollware.
5. `layered_publication_adapter.publish` → `public_selector_availability_payload` → rendered selector passes `appointmentUrl` directly to Register. The browser consumes the feed; it has no second collision engine. The exact path goes to Enrollware, bypassing this repository's native `/register` APIs and experimental Worker recheck scaffold. Source containers and a generated URL are not final checkout proof. No Enrollware registration was submitted.

Root mismatch: the assistant appended an inferred cleanup interval to a commitment whose stored consumption ended at noon, while active publication preserves that source boundary. A contributing, now corrected, code defect was misleading provenance: the V2 public feed still described legacy Work Order1B rules and omitted its active policy path. No hard instructor collision at noon is established by the supplied source bounds. Actual instruction overlap would remain a hard conflict regardless of room.

## Existing work and unresolved policy

Reviewed existing #351 owner doctrine, #338 Heartsaver duration ambiguity, #342 V2 architecture, #131 occupancy repair, #197 demand projection, and open #393 venue/resource normalization. This change does not duplicate, merge, or deploy those repairs; #372 remains untouched.

Current config: rooms24/7; one simultaneous class per room; primary B; C manual overlap resources; automatic_relocation=false; Brian excludes ACLS/PALS; course-level full-class consolidation; exact existing boundary edges. The owner's latest flexibility direction conflicts with interpreting every cleanup minute as universal instructor unavailability, and automatic C relocation is still explicitly disabled in config. No new relocation rule, overlap tolerance, buffer erasure or policy override has been encoded.

One focused owner question: **May a new class start at Brian's recorded class end (noon here), treating cleanup as flexible room turnaround unless an explicit instructor reservation extends later, while still blocking actual instructor teaching overlaps?** If yes, formalize that resource distinction consistently for source occupancy, offers and checkout; if no, store an explicit instructor consumption end and use it across all paths. Do not suppress all adjacent classes or retroactively modify bookings.

## Changed files and validation

- `scripts/build_bls_block_schedule_pilot.py`: correct V2 authority metadata and identify active policy; explicitly distinguish feed calculation from Enrollware checkout validation. Legacy metadata remains unchanged. No scheduling decisions changed.
- `tests/test_oct17_adjacent_offer_contract.py`: 10 new incident regressions covering noon full/skills, left-edge cleanup, explicit 12:30 occupied end, same instructor in C, another instructor in B, later blocker during candidate cleanup, paid anchor preservation, BLS/ARC/HSI adjacency and Brian ACLS/PALS exclusion, active versus legacy provenance, exact appointment date/URL.
- `data/audit/oct17_adjacent_offer_20261015.json`: bounded public evidence, source/verification limits and all eight local family feed counts.
- This immutable root receipt.

`python -m unittest tests.test_oct17_adjacent_offer_contract tests.test_layered_selector_adapter tests.test_layered_publication_adapter tests.test_layered_location_aliases`: **46 passed**, including the10 new tests. Synthetic ARC/HSI identifiers test engine family behavior, not live course mapping or eligibility. Python compilation and `git diff --check` passed. An optional broader run adding `tests.test_layered_day_cache` stopped making progress after these46 checks and was interrupted; no cache-suite pass is claimed. No unrelated suite repair.

Actual live feed overall: 7314 offers,87 dates,1345 start cells;453 input/normalized occupancy sources;191 windows;189 evaluated;2 failed windows/uncertainty issues. These are captured publisher counts, not a new generation. No generators or public artifacts were rebuilt; there is no new rejection-reason histogram to claim. Regression cases explicitly exercise conflict and cleanup blocking. Earl/Jackson case-collision changes and generated bytecode are excluded from staging; other worktrees remain untouched.

## Remaining release gates and next action

1. Answer the single policy question above; this is a business semantic choice, not a request to repeat existing code authorization.
2. Read actual Enrollware appointment inventory and checkout validation without enrolling. The exact public page GET failed `SSL CERTIFICATE_VERIFY_FAILED: certificate has expired`; verification was retained. No access restriction was bypassed.
3. Verify rendered public selector and link in **CyberPC's browser**. CUA initialization twice failed: `MXC launcher: cannot locate required Windows platform directory: HRESULT 0x80070003`. No rendered-browser success is claimed.
4. Independently confirm current native source consumption/counts and instructor/resource truth, then align both publication and booking enforcement with the approved semantics and test the composed source→selector→checkout path. Existing #393 also retains independent venue normalization proof gates.
5. Review the small draft, then authorize the appropriate targeted publication scope; no broad builder, deployment, emails, charges, roster changes, session mutation or enrollment occurred. This is NOT a completed public availability repair.

Supervising assistant: explain that noon was not proven impossible, retain the exact offer/source evidence, obtain the one policy answer, and resume here rather than starting another scheduler fix. Public HTTP proof is a snapshot and expires; refresh read-only evidence before release.
