# Issue 380 R34: bounded GitHub lifecycle source reader

PR_OPEN / BUILT only. Existing draft PR #381; baseline 6678c36e7c8b55ca8d6a7cefe6be239a337811f6. Local branch codex/issue380-r34-20261014.

## Change and evidence boundary

Added ops/operator/read-github-source.mjs alongside existing operator tooling. It performs a real authenticated gh api GET against the fixed repository/host, with five-second timeout, 256 KiB stdout/stderr limit and hidden Windows subprocess. It uses existing gh authentication, never requests or prints credentials. Existing canonical card UUID/version/issue/source URL must be supplied by the caller; unsupported refs fail before network access. The exact response number, repository API URL, browser URL, non-PR identity, stable source IDs, lifecycle state and update timestamp are validated. Binding drift during acquisition invalidates output. Only allowlisted lifecycle metadata is returned; issue title/body/comments/user content and CLI diagnostics are suppressed.

This is actual source acquisition, not a canonical database reader or source attestation service. A JavaScript object cannot prove authenticated canonical mapping. Existing publisher accepts a separate collector login; this reader is intentionally NOT connected to it. In particular, an issue being open does not prove action_required, and being closed does not prove already_corrected. Both return review/source_state=unknown/worker_safe=false/can_execute=false. Closed issues explicitly request reconciliation. Prose and arbitrary third-party comments never supply opt-in, priority, resolution, or blocked-state authority. No automatic resolve/reopen or writes.

## Validation

- node --check ops/operator/read-github-source.mjs: pass.
- node --check tests/github_source_reader.test.mjs: pass.
- node --test tests/github_source_reader.test.mjs tests/dispatch_reconciliation.test.mjs tests/live_dispatch_check.test.mjs: 38/38 pass, zero failed/skipped. Six new tests include nine invalid binding cases, eight response attacks, auth/JSON failure suppression, and four asynchronous binding drifts.
- git diff --check: pass.
- Read-only live acquisition at 2026-10-14T11:23:14.303Z returned issue #380 open, source ID 5804694193, node ID I_kwDOPDfdZc8AAAABWfyasQ, source updated_at 2026-10-14T11:21:05Z. The UUID/version used were explicitly synthetic fixtures, NOT a live Production Board binding. Output remained review/unknown/non-executable. This proves gh connectivity and source identity only.
- SQL unchanged; prior PostgreSQL suite not repeated. No SQL, HTTP routes or public pages changed. No generator run.

## Exact live probe output

```json
{"decision":"review","reason":"underlying_source_check_required","can_execute":false,"card_id":"12345678-1234-1234-1234-123456789abc","issue_id":380,"expected_version":"2","source_kind":"github_issue_lifecycle","source_ref":"https://github.com/Brian910cpr/910cpr-class-landers/issues/380","source_id":5804694193,"source_node_id":"I_kwDOPDfdZc8AAAABWfyasQ","issue_state":"open","source_updated_at":"2026-10-14T11:21:05Z","checked_at":"2026-10-14T11:23:14.303Z","source_state":"unknown","worker_safe":false}
```

## Remaining gates / next engineering

All six issue acceptance criteria remain OPEN. Next implement an authenticated database reader for an existing canonical intake/card relation; use its immutable issue identity/version, acquire this limited source observation, and revalidate the version inside the restricted publisher transaction. Review a typed distinction between lifecycle evidence and underlying operational evidence before allowing publication as authoritative_observation. Do not map open/closed directly onto action_required/already_corrected. First-publication card-to-issue binding and actual underlying schedule/payment/deployment readers still require design/proof. Production privilege verification, installed no-launch consumer/external atomic side-effect fence, private evidence intake, UI/history/counts/reopen and browser proof remain unfinished. These are engineering gates, not a request for Brian credentials or action. No production migration or runtime integration authorized here. Keep all SQL outside migrations/unapplied and PR #381 draft.

The expected outcome remains duplicate suppression before launch/mutation. No real end-to-end card/read/publish/dispatch proof exists. No operational cadence/observer/observer-health proof is established by this reader. Failure/staleness: failed read, mismatched identity, stale canonical version, unsupported source or ambiguous operational state must fail closed. Recovery: reacquire authenticated binding/source and recheck through the locked publisher; never retry mutation from cached lifecycle evidence. Brian is not the routine monitor. Escalate only real account/business decisions.

This extends native canonical evidence acquisition without adding Enrollware dependency. It follows the existing immutable audit/versioned publisher pattern rather than copying mutable issue prose into execution authority. Existing request/audit history survives unchanged. Production proof remains mandatory.

## Preservation / scope

Original E:/GitHub/910cpr-class-landers dirty checkout unchanged. Isolated worktree E:/GitHub/910cpr-issue380-r34. Existing Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded from commits. #371 primary, #372 draft, and other assignments untouched. Open [CODEX] queue scanned; no competing deep workstream or independently safe unassigned quick win selected. No installed runtime/state/process/task changes, production write, merge, deployment or cleanup. Known unrelated historical test failures not rerun or claimed repaired.

Changed files: ops/operator/read-github-source.mjs; tests/github_source_reader.test.mjs; data/audit/issue380_github_source_reader_20261014.md; unique root R34 receipt.
