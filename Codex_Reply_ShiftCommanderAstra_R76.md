# ShiftCommander Astra R76 receipt

Assignment: [Brian910cpr/910cpr-class-landers#214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214).
Dispatch ID: `SHIFTCOMMANDER_ASTRA_20260913_R1`, continuing R75 as R76.
Timestamp: 2026-09-14T17:50:00-04:00 (America/New_York).
Work-item state: **PR_OPEN; production release BLOCKED**.
Persistent-system state: **BUILT with synthetic local HTTPS/client-routing proof**;
no complete real-world PROVEN, MONITORED or HEALTHY claim.

## Pushed implementation and exact scope

- Target repository: `Brian910cpr/shiftcommander_v2`.
- Target worktree: `E:\GitHub\shiftcommander_v2_codex_issue214_r76`.
- Target branch: `codex/issue-214-pilot-client-r76`.
- Substantive commit: [`8231421adec647fafa04d2c8ab5a58a115625854`](https://github.com/Brian910cpr/shiftcommander_v2/commit/8231421adec647fafa04d2c8ab5a58a115625854).
- Review: [draft PR #14](https://github.com/Brian910cpr/shiftcommander_v2/pull/14),
  stacked on PR #13 (`codex/issue-214-pilot-isolation-r75`) at
  `67062ff780aa0efe9d7f43cd7526d06425567008`.
- GitHub readback: OPEN/draft, exact head above, exactly three changed files,
  no CI results. Local checks are not GitHub CI evidence.

Exact files changed and important review material:

| File | Purpose | Verified committed bytes | Git blob |
| --- | --- | ---: | --- |
| `server.py` | Pilot-only client configuration, response policy and named supervisor form | 200964 | `2836c6df4958c855fa9351fa91f647d3d02ac334` |
| `tests/smoke/test_private_pilot_clients.py` | Four executable HTTPS/client regressions | 6842 | `8784a369b4b29c7cb197ee94879891513297e18f` |
| `docs/PRIVATE_PILOT_CLIENTS_ISSUE214_R76.md` | Full findings, commands, validation limits and continuation | 9352 | `143f7f704e29c26234d8f9974798381adef13116` |

All three complete GitHub contents matched `git show` bytes at the immutable
commit, and the remote branch tip matched. The primary report is
[docs/PRIVATE_PILOT_CLIENTS_ISSUE214_R76.md](https://github.com/Brian910cpr/shiftcommander_v2/blob/8231421adec647fafa04d2c8ab5a58a115625854/docs/PRIVATE_PILOT_CLIENTS_ISSUE214_R76.md).
Base-to-head scope is 3 files, 348 insertions and 2 deletions.

Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r76`.
Courier branch: `codex/issue-214-shiftcommander-receipt-r76`.
Courier base: `1f8ede6e38d22b66374adb3b567ab16d0b24084c`.
Only this unique repository-root `Codex_Reply_ShiftCommanderAstra_R76.md` is being
committed on the courier branch. Its containing commit is the receipt commit;
the exact pushed tip/readback is returned on #214 and in the dispatch response.
Both Reply/Read filename collisions were checked, including all fetched history.
No prior mailbox file was overwritten or acknowledged by Codex.

## Findings and work performed

The previous pilot successfully served HTML while its supervisor JavaScript
still defaulted to `https://sc-api.adr-fr.org`. A saved
`localStorage.sc_api_base_url` could also route the member, wallboard and admin
views to another backend. R75's response-status checks had not executed this
API selection. This is a concrete pilot defect, not an unchanged blocked audit.

The server now injects the actual loopback origin before each approved pilot
HTML client's API selector. Its explicit nonempty value wins over existing
`||` fallbacks without rewriting browser storage. Pilot HTML is always a full
uncached configured response; it cannot return the original file's ETag-based
304 or byte-range 206. No generated/public HTML or separate asset was edited.

Pilot responses also carry a same-origin CSP for script connections and form
targets, with local resource restrictions. MDN's
[connect-src documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/connect-src)
and [form-action documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/form-action)
were consulted. Existing inline scripts/styles remain allowed. This is not an
OS sandbox, complete XSS protection, or proof of graphical browser enforcement.

The existing `/login/supervisor` link was also unusable for the required named
accounts: it offered only the deliberately disabled shared password. In pilot
mode it now offers the member-ID/password form and retains the supervisor
destination. Existing roster authorization confers supervisor privileges;
ordinary members still receive 403 on supervisor pages.

Hosted static files, normal serving behavior, staffing rules, auth schema,
provider bindings and calendar authority were preserved. No sitewide or
operational generator ran, and no new dependency was installed.

## Validation evidence

Fresh final-tree combined run, locally on Windows:

```text
SYNTAX: 2 changed Python files passed
DISCOVERED: 191
Ran 191 tests in 195.308s
OK
FINAL: tests=191 failures=0 errors=0 skips=0
```

This includes four new client tests, R75's 12 pilot tests, R74's 15 auth-readiness
tests and R9's eight existing suites (160 tests). The report contains the exact
11-suite command. Focused command:

```powershell
python -B -m unittest discover -s tests/smoke -p test_private_pilot_clients.py -v
```

The initial four-case regression run before repair failed in three cases,
with 14 subtest failures, demonstrating the missing client/policy/named-form
boundary. The hosted-default preservation case passed. After correction the
focused run passed all four in 8.920s. The final combined run also includes the
final Range-header and minimal Node-environment checks.

New evidence: actual loopback HTTPS responses; real named form submission;
secure-session role denial; five served UI API selectors executed in Node's VM
with external/missing stored settings; eight HTML responses checked for complete
body, CSP and no-store behavior; shared JavaScript still served; complete inline
scripts syntax parsed. The computed schedule URL reaches the authenticated
local backend. No external destination is contacted by these fixtures.

Retained broader checks prove synthetic save/readback after process stop/start,
logout revocation, temporary-password restrictions, audited credential recovery,
fail-closed storage behavior and resolver hard filters. R75's synthetic legal
draft retains OPEN seats and its checkout data/mirror/audit hash comparison
passes. Remaining fixture-process count after the suite is **0**.

These are local synthetic checks, not a graphical browser click-through,
real-member consent, production publication, hosted recovery or real complete
release proof. CSP headers were inspected; browser-engine enforcement was not
independently exercised. Test fixtures verify their ephemeral TLS certificate;
TLS verification was not disabled. No operational service remains running.

Syntax, explicit staging, whitespace and three-file base-to-head checks passed.
Expected storage-failure messages belong to negative tests. No final test
failure or newly identified unrelated application failure remains in this run.

## Exact remaining blockers and next action

Safe preparation advanced despite the production hold. Real pilot activation
still lacks private runtime configuration:

```json
{
  "auth_path_present": false,
  "auth_preflight_passed": false,
  "signing_secret_configured": false,
  "auth_path_absolute_outside_checkout": false,
  "named_accounts_provisioned": false,
  "release_ready": false
}
```

`SC_AUTH_DB_PATH` is absent from this worker's environment. No real private
account store was inspected, seeded, upgraded or changed. The operator setup
must establish an outside-Git directory/service identity, restricted ACLs,
backup/retention, named schema-v2 accounts, independent persistent signing
material and trusted loopback TLS. Do not reuse the profile's LocalAppData path
unchanged: the profile is itself inside a Git checkout on this PC.

Next for ChatGPT: review draft PR #14's three-file increment, retaining PR #13's
pilot isolation and the existing draft-stack/production hold. Use the exact
layout and check/start/stop commands in
`docs/PRIVATE_PILOT_ISOLATION_ISSUE214_R75.md` after private setup. Default URL is
`https://127.0.0.1:5443`, with named supervisor entry `/login/supervisor`; stop
with Ctrl+C and restart against the same private root/signing key. These are
prepared launch instructions, not a currently running operational URL.

Owner/operator configuration action remains required for that real installation
and any needed certificate trust; do not ask Brian to paste credential values.
Use the accepted starter roster and approved supervisors 159, 186 and 188.
Roster completeness alone is not a demonstration gate. Preserve disputed
identities/qualifications and collect fresh availability in the app.

Production additionally requires private R37/R47 incident disposition,
coordinated bridge-credential replacement as applicable and superseded-key
rejection proof. The runbook is `docs/PRIVATE_PILOT_AUTH_ISSUE214_R74.md`;
connected R43 provider metadata access remains established. Do not revive the
retired blanket metadata-access blocker. No operational key was read, rotated,
used for an authentication probe or printed here.

Then complete approved staffing/consent/demand/calendar provenance and real
member/mobile/wallboard agreement, protected/partial/overnight/DST/OT/swap
scenarios, controlled publication, hosted recovery, communication integrations
and observation. ADR Calendar remains the published-staffing authority.
Keep #214 and the draft stack open; this is a repair checkpoint, not a release.

## Persistent proof and observer contract

Expected outcome: named availability save -> durable revision after restart ->
legal explained resolution -> supervisor review -> authorized publication ->
matching member/supervisor/mobile/wallboard views. This round proves synthetic
components of that path, not a full real cycle. Real last-success timestamp is
not established. The confirmed weekly publication boundary remains Wednesday
23:59; lost saves, stale revisions, illegal staffing and divergent views are
failure conditions. Whole-workflow observer and observer heartbeat are not yet
established, so MONITORED/HEALTHY cannot be claimed.

Recovery: stop the affected pilot, preserve state/evidence, validate the private
backup, recover without reviving revoked sessions and repeat the loopback proof.
Do not fall back to operational files or restore a compromised bridge key.
Routine monitoring must not depend on Brian remembering to check the process.
Private identity/TLS/incident decisions are the current escalation boundary;
deterministic local code repairs remain eligible independently.

## Runtime, concurrency, preservation and transport

The active session's matching local `session_meta`/`turn_context` records report:

```json
{"session":{"cli_version":"0.153.4","id_matches":true},"turn":{"model":"gpt-6-astra","timestamp":"2026-09-14T21:35:05.229Z"}}
```

Only those allowlisted fields were emitted. This is local runtime evidence,
not a provider attestation or inference from a model-setting edit. Official
[Codex command documentation](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
was consulted. The existing project launcher
`E:\GitHub\shiftcommander_v2_codex_issue214_r2\scripts\Start-AstraReview.ps1`
was read and run with `-RepoPath E:/GitHub/shiftcommander_v2_codex_issue214_r76 -CheckOnly`.
At 17:42:54-04:00 it reported `can_launch=false` because the dispatcher lock was
held/inaccessible. No second worker, lease/lock change, or machine-default edit.

Final HEAD/branch/status and dirty tracked-file hashes matched captured baselines
for both original checkouts and the unchanged R75 target worktree. The original
ShiftCommander consolidation branch remains four commits ahead, with its dirty
calendar mirror and untracked code/data intact. LanderWare's unrelated Earl HTML,
tracked/untracked caches, heartbeat and Supabase temp directory remain intact.
No stash, reset, cleanup, rebase, force-push or existing worktree modification.
The newly created courier's root-only index was explicitly materialized before
use and checked clean; no apparent checkout deletions were staged.

The independent queue sweep reviewed open dispatches and latest #215/#219/#216/
#223/#227 evidence. Owner access and document controls/reconciliation already have
delivered implementations; instructor roles, financial inputs, auth/source parity
and stabilization have distinct unfinished gates. No new unclaimed narrow backend
defect was established there. The concrete ShiftCommander client repair above
advanced safely instead of duplicating those workstreams or retrying failed auth.

Tooling limitations: the GitHub connector returned 403 `Resource not accessible
by integration` for target PR creation. The already-authorized local `gh` route
successfully created draft PR #14 and read it back; no connector retry or new
account permission was needed. A read-only unpublished-count query initially
used the courier repo; it was corrected in the target repo and returned four.

Persisted locally and pushed: three intended target files plus this separate
root-only receipt. Intentionally ignored/uncommitted target artifacts are test
resolver output under `debug/` and the non-secret PR body at
`debug/issue214_r76/pr_body.md`. No private fixture or credential is committed.
No merge, deployment, account activation, production write, routing/calendar
cutover or member communication occurred. The retired mutable handoff path was
not used. The pushed receipt and follow-up on #214 are the return handshake;
later ChatGPT acknowledgement is not claimed by this dispatch.
