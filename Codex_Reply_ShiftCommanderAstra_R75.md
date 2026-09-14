# ShiftCommander Astra R75: private pilot isolation and HTTPS launcher

- Assignment: [issue #214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214).
- Dispatch: `SHIFTCOMMANDER_ASTRA_20260913_R1`, continuing R74 as R75.
- Checkpoint timestamp: `2026-09-14T17:15:21-04:00` (America/New_York).
- Work-item state: **PR_OPEN** for the implementation; **BLOCKED** for real-member activation and production release.
- Evidence: **BUILT**, locally validated with a synthetic HTTPS/process cycle. No complete operational PROVEN/MONITORED/HEALTHY claim.
- Implementation branch: `codex/issue-214-pilot-isolation-r75`.
- Implementation commit: [`67062ff780aa0efe9d7f43cd7526d06425567008`](https://github.com/Brian910cpr/shiftcommander_v2/commit/67062ff780aa0efe9d7f43cd7526d06425567008).
- Target PR: [ShiftCommander draft PR #13](https://github.com/Brian910cpr/shiftcommander_v2/pull/13), stacked on PR #12, OPEN/unmerged with no GitHub CI results at readback.
- Target worktree: `E:\GitHub\shiftcommander_v2_codex_issue214_r75`.
- Courier branch: `codex/issue-214-shiftcommander-receipt-r75`.
- Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r75`.
- Courier base: `1f8ede6e38d22b66374adb3b567ab16d0b24084c`.
- Receipt commit: the commit adding this file; the final SHA/readback will be posted on #214 and returned in Codex. The substantive commit above is immutable and avoids a self-referential receipt SHA.

## Findings and completed work

The September 14 owner update and PR #11 approve the starter roster and three
initial supervisors. PR #12 prepared auth readiness and explicitly identified the
isolated launcher as the next implementation. R75 carries those changed inputs
forward; missing roster members alone are not a private-demonstration blocker.

Verified defect: `SC_STATE_DIR` redirects only part of the mutable state.
Members/settings/shifts, public mirror writes and resolver audits still targeted
the checkout. A pilot configured with that setting alone could overwrite unrelated
operational files.

Implemented an opt-in `SC_PRIVATE_PILOT_ROOT` that redirects server data, mirrors
and both resolver audit destinations into one existing directory outside Git.
Existing deployment paths remain unchanged when the setting is absent. The
launcher builds a small allowlisted environment and reuses R74's read-only named
auth preflight. It requires matching active roster identities and TLS material,
then runs the existing Flask application on loopback HTTPS. It never seeds real
accounts, silently copies a roster, or inherits operational bridge credentials.

Pilot requests reject non-loopback peers, unexpected Host/origin, external proxy
calls and publication, including supervisor publication. Direct `server.py`
execution refuses its normal public bind in pilot mode. Draft resolution and
local persistence remain usable. Existing durable auth, secure cookies, password
change, member ownership and private static-file boundaries remain in effect.

No staffing-policy rule, production credential, deployed configuration, calendar
authority, dependency, frontend asset or operational roster changed. No calendar
fetch/import or full operational generator ran.

## Exact review files

Full report/runbook:
[docs/PRIVATE_PILOT_ISOLATION_ISSUE214_R75.md](https://github.com/Brian910cpr/shiftcommander_v2/blob/67062ff780aa0efe9d7f43cd7526d06425567008/docs/PRIVATE_PILOT_ISOLATION_ISSUE214_R75.md).

The target commit contains exactly seven intended files:

1. `engine/runtime_paths.py` — opt-in roots and inherited-setting checks.
2. `server.py` — runtime paths, loopback/origin restrictions and proxy/publication hold.
3. `engine/rule_based_resolver.py` — active resolver audit destination only.
4. `engine/resolver.py` — existing resolver audit destination only.
5. `scripts/start_private_pilot.py` — private preflight and foreground HTTPS launcher.
6. `tests/smoke/test_private_pilot.py` — 12 focused path/process cases.
7. `docs/PRIVATE_PILOT_ISOLATION_ISSUE214_R75.md` — complete setup, proof, limits and recovery instructions.

All seven GitHub file contents were fetched at the exact commit and matched
complete committed bytes. The target worktree is clean. The courier changes only
this unique repository-root receipt. Both Reply and Read filename collisions were
checked in the fresh courier root, and the R75 remote branch did not already exist.

Supporting reviewed records: `docs/PRIVATE_PILOT_AUTH_ISSUE214_R74.md`,
`docs/OWNER_INPUTS_ISSUE214_20260914.md`,
`docs/RELEASE_VERIFICATION_ISSUE214_R9.md`,
`docs/RELEASE_CHECKLIST_ISSUE214_R8.md`, target `AGENTS.md`, confirmed scheduling
rules/project boundaries/RULES/DATA_CONTRACT, and migration history. Courier
`CODEX_HANDOFF_PROTOCOL.md` is absent on the original dirty branch; its fetched
`origin/main` version and `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md` governed this
receipt. The issue body, full 159-comment discussion and pinned dispatch were
retrieved; governing supervisor directions, owner inputs and latest returns were
reviewed. A pickup acknowledgement is on the original issue.

## Local validation

Six changed Python files passed AST syntax validation without bytecode generation.
The final combined test command used `python -B -` and this suite definition:

```python
import unittest
suite = unittest.TestSuite()
for directory, pattern in [
    ('tests/smoke', 'test_private_pilot.py'),
    ('tests/smoke', 'test_auth_readiness.py'),
    ('tests/smoke', 'test_private_serving_boundary.py'),
    ('tests/smoke', 'test_temporary_password_gate.py'),
    ('tests/smoke', 'test_durable_auth.py'),
    ('tests/smoke', 'test_auth_audit.py'),
    ('tests/smoke', 'test_serving_auth_safeguards.py'),
    ('tests/smoke', 'test_beta_session_safeguards.py'),
    ('tests/smoke', 'test_live_state_store.py'),
    ('tests/resolver', 'test_hard_filters.py'),
]:
    suite.addTests(unittest.TestLoader().discover(directory, pattern=pattern))
result = unittest.TextTestRunner(verbosity=1).run(suite)
print(f'FINAL: tests={result.testsRun} failures={len(result.failures)} errors={len(result.errors)} skips={len(result.skipped)}')
raise SystemExit(not result.wasSuccessful())
```

Exact final output:

```text
SYNTAX: 6 files passed
Ran 187 tests in 193.679s
OK
FINAL: tests=187 failures=0 errors=0 skips=0
REMOTE: 7 intended target files match complete committed bytes
```

This is 12 pilot tests + 15 R74 readiness cases + the existing 160 R9 regression
cases. Scope/whitespace checks passed before staging and after explicit-file
staging. Git's LF/CRLF notices were not failures.

The real subprocess test used a temporary synthetic SQLite store, roster/settings,
and a generated test certificate. The HTTPS client verified its certificate; TLS
verification was not disabled. It proved named login, Secure cookies, rendered
member/supervisor/wallboard HTML responses, raw-snapshot denial, own-versus-other
availability authorization, save/readback after stopping and restarting the OS
process, logout revocation, proxy/publication/origin/Host rejection, isolated
settings mirrors, and a legal two-seat draft remaining OPEN without qualified
members. Seven resolver audit files were created under the temporary pilot root.
Checkout data/public-mirror/debug inventories and hashes remained identical during
that case. All fixture processes were stopped and temporary pilot data cleaned up.

Initial fixture errors detected an actual parent Git checkout around the default
Windows temporary directory and an incorrectly sized synthetic hash salt. The
tests moved temporary state outside Git and corrected the fixture salt without
weakening validation. The final suite has no known failures/errors/skips. Existing
tests intentionally exercise sanitized auth-storage failures. Unselected broad
historical suites, hosted CI, visual browser/mobile interaction, real accounts and
production were not validated. No new dependency was installed; the TLS fixture
used the existing Git for Windows OpenSSL.

## Exact blocker and next step

**Private pilot activation:** the approved private service user, directory/ACL and
backup choice, schema-v2 real named-account provisioning, independent signing
material and trusted browser TLS are not yet established. This round prepares and
tests the launcher but does not activate real accounts. The default user profile
is itself inside a Git checkout on this PC, so R74's LocalAppData proposal must not
be used unchanged. An explicit outside-Git location such as
`E:/ShiftCommander/PrivatePilot` is a proposed installation, not created or approved.

The report specifies every required file and both exact commands. After a private
operator prepares that installation, run from the target worktree:

```powershell
python -B scripts/start_private_pilot.py --pilot-root E:/ShiftCommander/PrivatePilot --member-id 159 --member-id 186 --member-id 188 --check-only
python -B scripts/start_private_pilot.py --pilot-root E:/ShiftCommander/PrivatePilot --member-id 159 --member-id 186 --member-id 188
```

The intended URL is `https://127.0.0.1:5443`. Stop with Ctrl+C and restart against
the same private directory/signing material. No operational URL is currently
running. Check-only exit 0 does not prove browser certificate trust, ACLs, backup
durability or release readiness. Keep the shared supervisor credential unset and
use named accounts with the existing real role helper. Fresh availability must be
collected through the pilot; do not seed historical files as consent.

**Production release:** R37/R47 `SC_D1_BRIDGE_TOKEN` incident disposition remains
unknown. Inventory every Worker/Render consumer using established R43 metadata,
coordinate the private maintenance/change authority, replace the credential on
both sides and prove superseded credentials are rejected. R74 contains the exact
replacement/recovery sequence. No operational token was read, changed, replayed
or disclosed here. Connected Cloudflare metadata is established, not a renewed
access blocker. Preserve ADR Calendar publication authority.

Real consent/qualification/demand provenance, authenticated client agreement,
partial/overnight/DST/lock/OT/swap scenarios, reviewed publication, hosted recovery,
communications and observer proof remain release work. Missing starter-roster
members alone do not prevent the private demonstration.

Next ChatGPT action: review PR #13's seven-file change on PR #12/PR #11, then
coordinate the specific private installation and credential-maintenance actions
above. User/operator action is required for real private provisioning/TLS trust
and production maintenance authority; do not ask Brian to retrieve or paste keys.
Keep #214 and all draft release PRs open. No unchanged-auth retry or routing
cutover is justified by this local proof.

## Persistent proof and recovery

Expected operational outcome: a real member's authorized availability survives
restart, informs legal explained resolution, reaches supervisor review/publication,
and agrees across all clients at the same revision. No complete real last-success
timestamp is established. The local synthetic HTTPS cycle passed in this checkpoint;
it is not a recurring operational observer or live staffing proof.

Lost saves, unavailable/stale sources, illegal assignments, diverging revisions or
missing publication are failures. Wednesday 23:59 remains the confirmed publish
boundary. Whole-workflow observer and observer heartbeat/escalation remain unproven.
On storage trouble, stop the pilot, preserve evidence, validate protected backups,
recover credentials without resurrecting old sessions, and repeat local proof.
Do not switch to operational paths or restore an exposed bridge credential.

## Runtime, preservation and queue

Matching active-session local `turn_context`: `model=gpt-6-astra`,
`timestamp=2026-09-14T20:59:19.024Z`. Installed CLI: `codex-cli 0.153.4`.
These are allowlisted local runtime fields, not provider attestation. The existing
project-specific `scripts/Start-AstraReview.ps1` in the R2 worktree was read and
CheckOnly returned `can_launch=false` at `2026-09-14T17:03:54.6805386-04:00` because
the dispatcher lock was held/inaccessible. No second worker was started; no lock,
lease or machine model-default setting changed. Official
[Codex CLI controls](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
were fetched; documentation itself is not runtime evidence.

Original LanderWare checkout remains on `codex/durable-session-participant-linking`
at `f2f5dd06e936e9620e0db5edc2331a38a8517e6d`. Its Earl HTML, tracked bytecode and
untracked heartbeat/cache/Supabase temporary work retain the captured status.
Original ShiftCommander checkout remains on `codex/base44-worker-consolidation`
at `55d6a05b919c1661845902b35eda14c9d4935f02`; the modified calendar mirror and
untracked slot generator/data/tests/availability backup retain the captured status.
Four unpublished commits remain preserved. Neither original checkout was cleaned,
reset, restored, rebased, merged, or staged. Existing worktrees remain intact.

Queue sweep found existing delivered work/dependencies rather than another
unclaimed narrow repair: #215's owner access is already delivered; #140 still
requires real credential parity after the reported HTTP 401 recurrence; #229 has
its existing #230-#233 review/proof stack. No duplicate implementation or unchanged
failing credential retry was started. Eligible primary backend work advanced here
despite the production gates. Only this assignment's files are committed.

All application processing was local. GitHub retrieval/push/PR/receipt verification
and official documentation reads were remote. The target code is pushed and
reviewable; no merge, deployment, real auth activation, production write or calendar
cutover occurred. No ChatGPT Read marker or retired mutable mailbox was written.
