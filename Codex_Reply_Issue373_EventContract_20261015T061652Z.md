# Issue #373 — Activity Monitor preparation

Timestamp: 2026-10-15T06:16:52Z
Branch: codex/issue373-event-contract-20261015
Substantive commit: 14f9657181a4d074a7ae8bf0c3245d8f40847c68
State: PR_OPEN (partial phase 1); https://github.com/Brian910cpr/910cpr-class-landers/pull/407
Persistent evidence: BUILT only, locally validated. No live end-to-end proof.

## Findings and work
Read full #373 including comments (none at pickup), repository AGENTS.md,
CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md,
LANDERWARE_PROOF_AND_HEALTH_STANDARD.md and docs/CODEX_INSTRUCTIONS.md.
Acknowledged execution before implementation on issue comment 6185777653.
Reviewed #371 dependencies and draft #372; neither changed, merged nor deployed.
Scanned open CODEX queue and existing PRs; preserved their assignments and the
single deep P1 stream. No existing Activity Monitor PR was present; created #407.

Prepared an independent backend contract: trusted operation registry, opaque IDs,
observed lifecycle statuses, canonical UTC timestamp, bounded fixed summaries,
owner/staff scope constraints and duration validation. Rejects arbitrary fields;
never serializes customer content or exception messages. No runtime integration.

## Exact intended files
- scripts/activity_event_contract.mjs
- tests/activity_event_contract.test.mjs
- docs/ACTIVITY_MONITOR_CONTRACT.md (primary design/review report and remaining gates)
- Codex_Reply_Issue373_EventContract_20261015T061652Z.md (this receipt)

## Validation evidence
node --check scripts/activity_event_contract.mjs: exit 0.
node --test tests/activity_event_contract.test.mjs: tests 8, pass 8, fail 0.
git diff --check: exit 0, no output before committing.
No generators, migrations, deployment commands or public builds run.
Substantive commit pushed successfully to origin before this receipt.
Receipt will be committed separately; its containing pushed SHA is reported on #373
and in final dispatch response (avoids a self-referential commit identifier).

## Preserved unrelated work
Original E:/GitHub/910cpr-class-landers remained on its existing branch with all dirty
files and untracked receipts/caches intact. Work isolated at
E:/GitHub/910cpr-issue373-event-contract. That new checkout reports modifications
in docs/Earl/index.html and docs/Jackson/index.html without this assignment editing
them, consistent with existing Windows checkout/case-collision behavior. Those
files remain unstaged/uncommitted; no reset/restore/cleanup attempted.
No intentional temporary/untracked deliverables remain in this worktree.

## Exact remaining blockers / limits
This does not satisfy the full Activity Monitor acceptance criteria. P1 #371
foundation gates remain outstanding; #372 remains draft, unmerged, undeployed.
This bounded preparation adds no competing deep implementation stream. No
instrumented owner producer, authenticated event transport, persistent store,
retention cleanup or UI exists for this feature. No source may be represented as
connected based on these tests. Real-request-to-light acceptance is unproven.
Actionable error catalog still needs reviewed fixed codes, not exception text.

Last successful end-to-end proof: none. Failure/staleness observer and observer
health: not installed. Proposed 60-second active polling freshness and bounded
24-hour/1,000-event retention are documented proposals, not operational facts.
Recovery: keep feature disabled; implement one authorized read-only producer and
bounded sink, prove auth/privacy/retention/failure behavior before UI integration.
Owner is not assigned routine monitoring; no monitoring capability claimed.

## Next action for ChatGPT
Review #407 and the exact three substantive files above. Keep #372 and #407 draft;
do not deploy. Continue the P1 primary stream. Once its foundation is proven,
coordinate the smallest real owner read-only producer/transport slice, followed by
feature-flagged accessible lights and real end-to-end proof. Account-level action
is not required for this local contract; future transport authorization must be
verified at integration time. No owner permission request is pending.

Deployment: persisted locally and pushed for review; not merged, deployed,
CONNECTED, PROVEN, MONITORED or HEALTHY.
