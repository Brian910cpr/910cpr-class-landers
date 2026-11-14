# Issue 371 — concurrency runner safety

Timestamp: 2026-10-15T23:33:55.7752858Z (UTC)
Assignment: #371; existing draft PR https://github.com/Brian910cpr/910cpr-class-landers/pull/372
Branch: codex/issue371-runner-safety-20261015
Substantive commit: 4ffae179e260483572b2489e336659da4c280d0a
State: PR_OPEN; BLOCKED for remaining operational proof. Evidence: BUILT / validated locally only.
Receipt commit is the pushed branch tip (separate commit avoids self-referential SHA).

## Findings and change

The existing opt-in independent-session runner validated only DSN hostaddr/service, leaving inherited libpq PGHOSTADDR/PGSERVICE able to redirect a nominal loopback connection. Python -O/-OO also disabled its empty-public-schema and proof assertions. These were code-review findings; no real redirected connection or database write was attempted.

Now reject PGHOSTADDR, PGSERVICE, PGSERVICEFILE, PGOPTIONS and DSN hostaddr/service/options before connect. Reject optimized Python before driver import and at run entry. Empty schema/function checks raise unconditional exceptions. Error messages do not echo connection values. Seven no-network tests cover numeric loopback acceptance, remote/multihost/wrong-database refusal, DSN/environment overrides, refusal before run without secret echo, nonempty-schema/function no-write behavior, -O/-OO subprocess refusal and missing consent. Docs describe these safeguards.

Exact intentional files:
- tests/customer_interaction_concurrency.py
- tests/test_customer_interaction_concurrency_safety.py
- docs/CUSTOMER_INTERACTION_CONCURRENCY.md
- Codex_Reply_Issue371_RunnerSafety_20261015T233355Z_R1.md

Read full #371 body/comments, AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Execution acknowledged before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6204463098
Applied Supabase skill; changelog and relevant PostgreSQL libpq environment documentation checked read-only. No Supabase API/schema change.

## Validation / exact blocker

Command: python -B -m unittest discover -s tests -p test_customer_interaction_concurrency_safety.py -v
Output: Ran 7 tests in 1.037s; OK. Zero failures. Mocks and refusal subprocesses only; no database contacted.
Python AST parse: AST PASS for both changed Python files.
Targeted git diff --check: PASS.
Actual opt-in runner: python -B tests/customer_interaction_concurrency.py --apply-to-empty-local
Output: customer_interaction_concurrency.py: error: psycopg 3 missing; no database contacted or dependency installed
Module check: psycopg3_available=False. No authorized empty loopback issue371_* PostgreSQL database established. Existing prior executable-location findings reused; no new claim that PostgreSQL is absent everywhere. No dependency installed. This increment makes later proof execution safer; it does not constitute that proof.

Remaining gates: actual independent READ COMMITTED sessions with all five observed blocking/receipt/invariant scenarios, genuine owner-session UI/Edge/PostgREST/database save/reload/resume/conflict/recovery, usable production backup/restore evidence, then separate explicit rollout GO. Path A supersedes Docker/WSL/Synology prerequisite requests. No incomplete rollout approval requested.

## Preservation and deployment

Used isolated E:/GitHub/910cpr-issue371-runner-safety from PR372 tip fa5b594937099b2f99ba0776f9fa2a908bf705ac. Explicit files only staged. Unrelated shared checkout dirt, all assignments, monitors and existing worktrees preserved. Local Windows case-collision docs/Earl/index.html and docs/Jackson/index.html remain unstaged, intentionally excluded. No cleanup, generator, installation, production database/API write, origin expansion, customer action, merge or deploy. Gate OFF; PR372 remains draft/unmerged/undeployed. Existing PR reused, no competing deep stream.

Open CODEX queue scanned; no separate safe quick win established that justified disturbing active assignments. Continued eligible backend runner work while operational proof remains gated.

Latest observer issue update at 2026-10-15T23:04:13Z reports existing Delta task enabled/recovered; read-only canonical comment 6102801791 still contains scheduled checked_at=2026-10-15T22:42:49.321Z, status FRESH at its observation. No observer receipt/task/monitor mutation or forced run. Earlier lifecycle cause remains unexplained; do not repeat superseded incident escalation absent new stale evidence. No sustained current-health claim made here.

## Proof contract / next action

Expected outcome: owner capture/disposition/recovery preserves notes, obligations and immutable retries. Genuine operational E2E timestamp absent; BUILT only. This runner is on-demand, with no expected unattended cadence: success requires five actual independent-session PASS records and invariants. Missing scenario, wrong conflict, timeout, duplicate receipt or resolved interaction with outstanding work fails proof. Local tests observe guard regressions only; no deployed CRM observer/observer-health proof exists. Recovery: preserve synthetic failed database, inspect private lock/session diagnostics and repeat on a fresh authorized empty local database. CRM uncertain writes retry identically; conflicts retain/export intent for fresh server review. Brian must not become routine monitoring.

ChatGPT next: review substantive commit and these exact three source/test/doc paths; retain all existing Path A gates. Engineering should establish an authorized empty numeric-loopback PostgreSQL/psycopg3 environment before running existing proof, without production access or reviving superseded infrastructure requirements. Genuine owner-session and backup evidence must follow before preparing final rollout GO. No owner action required for this local safety increment; production GO remains separate. Broader email/customer discovery, supervised learning, integrations and asynchronous reminder milestones are unfinished.

Persisted locally, committed and pushed; GitHub receipt verification is performed before final response. Not deployed.
