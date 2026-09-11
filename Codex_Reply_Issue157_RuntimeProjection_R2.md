# Codex Reply — GitHub Issue #157 Runtime Projection Round 2

- Assignment: `Brian910cpr/910cpr-class-landers#157`
- Timestamp: `2026-09-11T19:08:32-04:00`
- Branch: `codex/issue-157-runtime-projection`
- Pull request: `https://github.com/Brian910cpr/910cpr-class-landers/pull/197`
- Reconciled Stage 1–5 commit: `ed3d62e5dc5e752611c4c1f0bdb920dcac1dcbb7`
- Runtime-projection implementation commit: `6ad1fdf8619a22bd435c5c2150b64b6f0bc61fc7`
- Receipt commit: recorded by the pushed branch tip containing this file
- Work-item state: `PR_OPEN` and `BLOCKED` for live proof/deployment
- Persistent-system evidence state: `BUILT`

## Facts and findings

1. Stage 1–5 commit `d76e714d2b4` reconciled cleanly onto current `origin/main` as `ed3d62e5dc5`; no conflict resolution or broad regeneration was required.
2. The Stage 1–5 review's repository connection gap was real: the scheduled public refresh had no producer for `data/runtime/canonical_scheduling_demand.json`.
3. Merely fetching during an Enrollware-triggered rebuild would still miss registration-only changes. The refresh workflow now fetches canonical demand on every scheduled run, compares a stable content hash that excludes `generated_at`, and triggers the existing validated build when either Enrollware inventory or canonical demand changes.
4. The new producer requires `HOT_SYNC_ADMIN_KEY`, validates the exact schema, timestamp freshness, session counts, and absence of PII-like fields, then atomically replaces the runtime snapshot. Fetch or validation failure preserves the last good snapshot and fails the build closed.
5. The anchor consumer independently rejects stale/invalid runtime snapshots, preventing direct/local builds from silently consuming old demand.
6. A status JSON is written on success and failure and uploaded by the scheduled GitHub workflow even when fetching fails. The scheduled workflow is the observer; GitHub Actions run history plus the retained status artifact is its observable heartbeat/evidence.
7. No generator or public-site build was run. Stage 6 corporate availability was not started because live Stage 1–5 deployment and end-to-end proof remain incomplete.

## Work performed

- Read the full issue and comment history, repository `AGENTS.md`, `CODEX_HANDOFF_PROTOCOL.md`, `docs/CODEX_INSTRUCTIONS.md`, and `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md`.
- Preserved the unrelated dirty checkout and created a separate worktree on `codex/issue-157-runtime-projection` from current `origin/main`.
- Reconciled the reviewed Stage 1–5 implementation.
- Added the authenticated, PII-free, fresh-schema-validated, atomic endpoint-to-runtime producer.
- Connected canonical-demand hash changes to the existing scheduled validated public build.
- Added failure/status evidence and stale-consumer enforcement.
- Opened PR #197.

## Exact files changed

Reconciled Stage 1–5 files:

- `scripts/anchor_state.py`
- `scripts/apply_anchor_policy.py`
- `scripts/canonical_scheduling_demand.py`
- `supabase/functions/canonical-scheduling-demand/index.ts`
- `tests/test_anchor_state.py`
- `tests/test_apply_anchor_policy.py`
- `tests/test_canonical_scheduling_demand.py`

Round 2 connection files:

- `.github/workflows/refresh-public-site.yml`
- `scripts/apply_anchor_policy.py`
- `scripts/fetch_canonical_scheduling_demand.py`
- `tests/test_fetch_canonical_scheduling_demand.py`
- `Codex_Reply_Issue157_RuntimeProjection_R2.md`

## Tests and checks

Command:

```text
python -m unittest tests.test_fetch_canonical_scheduling_demand tests.test_anchor_state tests.test_apply_anchor_policy tests.test_canonical_scheduling_demand -v
```

Result: `34 tests passed`.

Command:

```text
python -m py_compile scripts/anchor_state.py scripts/apply_anchor_policy.py scripts/canonical_scheduling_demand.py scripts/fetch_canonical_scheduling_demand.py
```

Result: passed with no errors.

Additional checks:

- `.github/workflows/refresh-public-site.yml` parsed successfully with PyYAML.
- `git diff --check` passed.
- `actionlint` was not installed, so actionlint validation was not available.

## Known unrelated worktree state

- `docs/Earl/index.html` appears modified in both the original checkout and the fresh Windows worktree because the repository intentionally tracks case-colliding aliases that Windows cannot faithfully represent. It was not staged or committed.
- Test-created `scripts/__pycache__/` and `tests/__pycache__/` files remain untracked and were not staged or committed.
- The original checkout's unrelated branch, modifications, heartbeat file, and caches were not altered.

## Deployment and proof status

- Local validation: passed.
- Push: substantive commits and this receipt are pushed on the named branch.
- Pull request: #197 open.
- Merge: not performed.
- Supabase function deployment: not performed.
- Production workflow deployment: not performed.
- Live endpoint verification: not performed.
- End-to-end canonical registration -> projection -> runtime snapshot -> anchor output proof: not performed.
- Last successful end-to-end proof: none available.

Persistent proof contract:

- Expected outcome: active canonical registrations deterministically promote the matching public occurrence to an Anchor, including when only registration demand changes.
- Success evidence: a real registration change produces a fresh endpoint projection, changed runtime hash, successful scheduled build, matched-demand audit, and corresponding rendered anchor output.
- Expected cadence: scheduled refresh at minutes 13 and 43 each hour.
- Failure/staleness condition: missing credentials, failed HTTP/schema/PII/freshness validation, or a source timestamp older than 15 minutes fails closed and emits a status artifact.
- Observer: the scheduled `refresh-public-site.yml` GitHub Actions run and its `canonical-demand-fetch-*` artifact.
- Observer health: current run history/cadence after merge; not yet proven because the branch is not merged.
- Recovery path: inspect the failed run's canonical-demand status artifact, correct deployment/secret/schema/source failure, then rerun the workflow.
- Escalation boundary: repository logic is implemented; Supabase deployment/authentication requires account-level authority.

## Exact blocker and remaining risk

`HOT_SYNC_ADMIN_KEY`, `SUPABASE_ACCESS_TOKEN`, and a usable Supabase deployment context are unavailable locally. Consequently the new edge function cannot be deployed or verified against live canonical data from this environment. Until an authorized deployment occurs and PR #197 is merged, the endpoint and scheduled producer cannot exchange real state. The result must remain `BUILT`, not `CONNECTED`, `PROVEN`, `MONITORED`, or `HEALTHY`.

Stage 6 corporate availability remains gated until the live Stage 1–5 path is connected and proven.

## Exact recommended next action for ChatGPT

Review PR #197, deploy `supabase/functions/canonical-scheduling-demand` with the existing authorized Supabase context, verify one protected PII-free response, merge the PR, manually dispatch `refresh-public-site.yml`, and confirm the runtime hash, demand-match audit, anchor feed, rendered public output, and retained status artifact. Only then authorize Stage 6.

## Human/account action required

Yes. An authorized operator must deploy the Supabase function and make the existing `HOT_SYNC_ADMIN_KEY` available to the production GitHub Actions workflow without exposing it in repository files or logs.
