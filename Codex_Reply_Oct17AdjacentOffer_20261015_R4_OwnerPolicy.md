# October17 owner-approved occupied interval contract

2026-10-15 UTC. Branch `fix/availability-turnaround-20261015`; updates existing draft PR408. This receipt supersedes R1's pending policy question; historical receipts remain immutable.

Owner answered yes in message `Sentinel_7a99f4491ab48191871b6c3b4c006224`: genuinely required extra time must already be part of a class's unavailable space, or the special cleanup veto must be dropped. Parent's accepted interpretation: no separate cleanup refusal after the recorded occupied end; explicit extensions still block. No further policy question is pending.

## Runtime diagnosis and implementation

The active V2 runtime already honors the approved model. Existing source consumption bounds are preserved; candidate total reservation is computed before conflict checks and publication; global added transition cleanup is0; half-open conflicts allow touching. Oct17 source10:00–12:00 therefore permits noon. An explicit source consumption end12:30 moves the boundary to12:30. The earlier assistant's inferred additional cleanup rejection was wrong; a stricter public availability change is unnecessary.

Do not erase existing candidate reservations120+30/45+15 or explicit travel/ADR/teaching blocks. They already participate before publication and are represented by the candidate's occupiedUntil, rather than appearing as a later surprise veto. RoomC flexibility does not override real same-instructor teaching overlap.

Added the exact owner rule/evidence to `data/config/layered_scheduling_policy.json`, the source-preservation explanation in `scripts/layered_selector_adapter.py`, and durable assistant/operator guidance in `docs/SCHEDULING_OCCUPIED_INTERVAL_CONTRACT.md`. These are policy documentation/provenance changes, not changed scheduling decisions. Expanded `tests/test_oct17_adjacent_offer_contract.py` from10 to14 tests. No production generator or output was run.

## Validation and its boundary

`python -m unittest tests.test_oct17_adjacent_offer_contract tests.test_layered_selector_adapter tests.test_layered_publication_adapter tests.test_layered_location_aliases`: **50 passed**,14 incident regressions. AST/JSON parse and git diff whitespace validation passed.

New tests take actual published offer date/start/occupiedUntil and apply the runtime's actual `interval_conflict` predicate to normalized canonical occupancy. They prove noon full/skills agreement; stale noon rejection after an explicit12:30 extension; rejection after a new same-instructor RoomC conflict; preservation of explicit extra reservation exactly once; and agreement across full/skills variants of BLS, Heartsaver, ARC, HSI, ACLS, PALS, USCG and FamilyCPR. Synthetic qualified instructors/course labels avoid fabricating clinical eligibility or live course mappings. Existing tests preserve Brian's ACLS/PALS exclusion, planted paid anchors, shared-room blocking, travel and occupied intervals.

This is local generation→public interval→collision-revalidation proof. It is NOT an integrated external checkout test, complete booking validator proof, or atomic reservation-race proof. The incident URL bypasses this repository's native checkout and goes to Enrollware; its validator cannot be changed here. Existing exact-page HTTP403 and CyberPC CUA initialization HRESULT0x80070003 remain the access/render gates. No registration was submitted and no access restriction was bypassed.

## Delivery and release

Existing implementation commit100b4aeb52d is confirmed on the remote branch and PR408. Local delivery receipts7e45e3048da and232787c7bd6 are preserved in the same branch. This round commits the new policy documentation/tests and updates that existing PR; exact resulting SHA and remote confirmation are reported in the final outcome.

No production behavior release is needed to make the current runtime allow touching at noon: it already does. PR408's provenance/guidance correction may be merged/published through normal review, but no merge/deploy is performed in this task. A complete claim of public→Enrollware checkout consistency still requires authorized access and actual read-only/end-to-end proof. The owner's policy decision is resolved; remaining blockers are proof/access, not another cleanup-policy approval.

Bookings, rosters, Sandra contact, payments, broad generated outputs, other open PRs and other worktrees are untouched. Earl/Jackson Windows case-collision changes remain unstaged and excluded. No separate cross-thread delivery was retried.
