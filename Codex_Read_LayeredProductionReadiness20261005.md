# Layered production scheduling — blocked checkpoint

- Assignment: Brian's layered-model production integration, continuing issue #342.
- Timestamp: 2026-10-05 02:40 UTC.
- Branch: feat/layered-production-20261005.
- Base: origin/main 529b5eb20.
- Substantive commit: e921ff5bf5408fef4dcbf6793993010d6f5b116f.
- State: BLOCKED for production integration; independent preflight BUILT.

Read-only canonical database inspection found 222 locations and zero resource
rows. The repository declares instructor calendar sources and booking-container
labels, but no room free-interval/concurrency contract. Those inputs cannot prove
the required room ∩ instructor windows. The lab's synthetic room hours are not a
production adapter. An alternate authoritative room ledger has not been identified.

Added a read-only resource coverage/freshness preflight and seven regression tests.
It reports missing/stale/unsupported resource coverage without mutating inputs or
services. It is not enabled in the public refresh, so this checkpoint does not
remove or change public inventory. It deliberately makes no scheduling-health claim.

Changed files:

- scripts/layered_resource_readiness.py
- tests/test_layered_resource_readiness.py
- docs/LAYERED_PRODUCTION_READINESS_20261005.md
- this reply

Validation: `python -B -m unittest tests.test_layered_resource_readiness` — 7 pass.
`git diff --check` passed. No generators, broad suites or production refresh ran.
No full layered adapter, live rendered offer proof or new persistent monitor exists.
Unrelated Earl/Jackson HTML modifications were excluded from explicit staging.

Release: branch-only handoff; no merge, deployment, calendar/roster/payment mutation
or production cutover. Push completion is reported separately from this committed
receipt; do not infer deployed status from a GitHub branch.

Exact next action for parent: identify the authoritative room ledger, or obtain
Brian's explicit resource policy for physical rooms vs Office container, open
intervals and simultaneous-class capacity. Do not substitute student seat capacity.
Then supply source-stamped coverage to a read-only adapter, reuse the existing pure
layered engine, shadow-run real days and preserve current roster gates before a
guarded release. Oct7/8/17/24 source repairs remain outside this checkpoint; previous
counts were not revalidated here and no record writes were made. No routine
monitoring responsibility has been shifted to Brian: integration is blocked rather
than described as healthy.

Existing runnable local lab remains at
`C:\Users\ten77\AppData\Local\Temp\landerware-scheduling-lab`, branch
`lab/layered-windows-20261004`, commit 06c73d69d536386e5d98c54092dd3e43d7474c76.
Its existing 94-test/browser evidence is historical, not a new production pass.

Readiness integration worktree:
`C:\Users\ten77\AppData\Local\Temp\landerware-layered-production-20261005`.
Rollback: no public change to revert. The independent preflight commit can be
reverted without affecting the existing selector.
