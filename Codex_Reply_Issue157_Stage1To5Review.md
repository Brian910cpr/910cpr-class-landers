# Codex Reply — GitHub Issue #157 Stage 1–5 Review

- Assignment: `Brian910cpr/910cpr-class-landers#157`
- Timestamp: `2026-09-11T18:47:29-04:00`
- Branch: `codex/issue-157-stage1-5-review`
- Substantive implementation reviewed: `d76e714d2b4d26753bcc60583d28fe50e1e9170e`
- Receipt commit: recorded by the pushed branch tip containing this file
- Work-item state: `BLOCKED`
- Persistent-system evidence state: `BUILT`

## Facts and findings

1. The Stage 1–5 implementation exists on `origin/codex/demand-led-canonical-anchor-truth` at `d76e714d2b4`.
2. The targeted Python behavior is locally reproducible: 27 focused tests passed for anchor state, anchor policy, canonical demand matching, the Sep. 14 regression, and cross-course barnacles.
3. Python syntax validation passed for all three changed Python modules.
4. The protected Supabase function exists, but this repository has no producer that calls `canonical-scheduling-demand` and persists its response to `data/runtime/canonical_scheduling_demand.json`. Repository-wide call-site search found only the function source and a source-inspection test. `scripts/apply_anchor_policy.py` only consumes the file when it already exists.
5. Therefore canonical registration demand is not connected to the anchor-policy runtime by the reviewed branch. No end-to-end cycle has been proven.
6. Live Supabase verification/deployment remains unavailable because `HOT_SYNC_ADMIN_KEY` and `SUPABASE_ACCESS_TOKEN` are absent and the Supabase CLI was not found on `PATH` or in the checked common installation locations.
7. The implementation branch is 106 commits behind `origin/main` and one commit ahead. It requires reconciliation/review before merge.
8. Stage 6 corporate availability remains explicitly gated by the issue's required Stage 1–5 report/review checkpoint and was not started.

## Work performed

- Read the complete GitHub issue, repository `AGENTS.md`, `CODEX_HANDOFF_PROTOCOL.md`, `docs/CODEX_INSTRUCTIONS.md`, and `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md`.
- Created a separate named review worktree/branch from the issue implementation commit.
- Inspected the complete implementation diff and repository call sites.
- Ran focused tests and syntax validation.
- Checked required credentials and Supabase CLI availability.
- Did not run any generator, rebuild public pages, deploy, merge, or begin Stage 6.

## Exact files changed by this review

- `Codex_Reply_Issue157_Stage1To5Review.md`

The pre-existing/unrelated worktree modifications in `docs/Earl/index.html` and `docs/PALS.html` were preserved and are not included in the receipt commit.

## Tests and checks

Command:

```text
python -m unittest tests.test_anchor_state tests.test_apply_anchor_policy tests.test_canonical_scheduling_demand -v
```

Result: `27 tests passed`.

Command:

```text
python -m py_compile scripts/anchor_state.py scripts/apply_anchor_policy.py scripts/canonical_scheduling_demand.py
```

Result: passed with no output.

Repository integration search:

```text
rg -n "canonical_scheduling_demand\.json|canonical-scheduling-demand" . -g '!docs/**' -g '!**/__pycache__/**' -g '!Codex_*'
```

Result: no runtime producer found; only the consumer constant, Supabase function, and source-inspection test were present.

## Known unrelated/stale-snapshot failures

`python -m unittest discover -s tests -p 'test_*anchor*.py' -v` ran 27 tests and reported 3 failures plus 1 error in `tests/test_anchor_calendar_and_landers.py`. The failures concern stale generated selector/anchor artifacts, including a missing `docs/classes/13833211.html`, a current five-anchor feed where the older test expects three, and older rendered selector expectations. No generator was run because the narrow-change gate requires advance scope review and the branch is 106 commits behind `origin/main`.

## Deployment and proof status

- Local validation: targeted code behavior validated.
- Push: this receipt branch is pushed; see branch tip.
- Merge: not performed.
- Supabase deployment: not performed.
- Production deployment: not performed.
- Live verification: not performed.
- Last successful end-to-end proof: none available for canonical demand -> runtime JSON -> anchor policy -> rendered public offer.
- Failure/staleness condition: missing or stale `data/runtime/canonical_scheduling_demand.json` leaves canonical demand disconnected and can yield no canonical-demand anchors.
- Observer health: no producer/observer for this new demand projection was found, so observer health is unproven.

## Blockers and remaining risk

- A repository or operational producer must securely fetch the PII-free endpoint and atomically persist the validated runtime contract before the feature can be classified `CONNECTED`.
- Supabase credentials/account authority are required to deploy and live-test the function.
- The 106-commit divergence must be reconciled without mixing unrelated generated-page changes.
- Stage 6 must remain gated until Stage 1–5 is connected, deployed, and reviewed with real evidence.

## Exact recommended next action for ChatGPT

Review this checkpoint and dispatch a new round that first reconciles `d76e714d2b4` onto current `origin/main`, adds or identifies the durable authenticated endpoint-to-runtime producer plus stale/failure observation, and validates a real canonical registration through final anchor output. Only after that proof should Stage 6 corporate availability be authorized.

## Human/account action required

Yes. An authorized operator must provide the existing Supabase deployment/authentication context (without committing secrets) or perform the account-level deployment. Repository-side producer and test work can proceed in a follow-up without exposing credentials.
