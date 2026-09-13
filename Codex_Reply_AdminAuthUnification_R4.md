# Owner sign-in failure verified; Cloudflare account access required

- Assignment: #215 owner access; related credential incident #140 and document controls #219.
- Timestamp: 2026-09-13T19:53:36Z.
- Branch: `codex/owner-access-failed-signin`.
- Inspected main commit: `612030fbdc3b8654bf509bd4ec73a5f7af3308b1`. This receipt is the only change; its commit is the branch tip.
- Work-item state: BLOCKED.
- Persistent-system evidence: BUILT, not PROVEN or HEALTHY for accepted-key owner access.

## User report and exact credential contract

Brian reported that none of the owner pages work and asked whether the expected password is the HOT_SYNC one.

Yes: owner APIs forward `X-Hot-Sync-Admin-Key` to the production authority at `https://schedule.910cpr.com/admin/hot-sync`. Repository routing identifies the Cloudflare Worker as `free-time-offer-worker`, whose secret name is `HOT_SYNC_ADMIN_KEY`. The browser supplies the VALUE of that secret. The name itself is not the password.

The GitHub Actions secret with the same name is an independently stored automation credential. Updating GitHub does not rotate the deployed Worker secret. Finance uses the separately configured `landerware-financial-worker`, which also needs the same intended value. Corporate access remains separate.

## Fresh evidence and limitations

- Production Class History rendered the owner-key form.
- One secure browserAuth submission was completed. Credential values were neither returned to the model nor read from inputs, browser storage, logs, or files.
- Fresh rendered UI after submission: “Class history could not load right now. Please try again.” No classes loaded. This is FAILED end-to-end proof, not successful authentication.
- The generic message alone does not establish whether the supplied credential was incorrect, the authority was unavailable, or another request failed. No second credential attempt was made.
- Source confirms that Class History catches shared-auth errors and replaces them with that generic message. The shared server authority also treats both upstream 401 and 403 as a rejected credential, although an infrastructure denial can return 403.
- Anonymous and deliberately invalid read-only diagnostics returned 401 from the Supabase workbench. Separate terminal requests to the Worker returned Cloudflare 403 / error 1010. That terminal-specific result does not establish that the browser or Supabase edge traffic received the same denial. No block bypass was attempted.
- Existing #140 evidence after the owner's September 13 GitHub secret update reports that both production publisher reruns still received HTTP 401 with the secret present. That is historical account-parity evidence; it does not reveal or validate the value submitted in today's browser test.
- Current main has no changes to the inspected auth, Worker, or workbench logic compared with the inspected document-controls revision.
- No Cloudflare plugin was returned by provider discovery. Wrangler whoami explicitly reports no authentication. No Cloudflare secret mutation capability is available in this session.
- Document removal already completed in the preceding work remains recorded under #219. This diagnostic made no database or application changes.

## Work, checks, and deployment

Only this new receipt is added. No password was reset, no service was redeployed, and no authentication fallback or bypass was introduced. Read-only checks included live UI, current source, the #140 incident history, repository routing, and Cloudflare CLI authentication state. No new tests were needed for a documentation-only diagnostic.

## Required recovery and proof

An account holder must reconcile the intended owner-key value with `HOT_SYNC_ADMIN_KEY` on `free-time-offer-worker`, the separate Finance Worker, and the GitHub Actions repository secret. Keep the value out of chat, issues, and logs.

After reconciliation, use secure sign-in to prove one owner page loads private data, same-tab navigation loads the other owner pages without another prompt, and locking clears protected content. Verify Class History document viewing/removal separately; instructor-specific access remains unresolved under #219.

Run the canonical participant verifier and the two publishers identified in #140, then observe a later scheduled cycle before claiming operational health. Improve error propagation so rejected credentials and service failures can be distinguished without inspecting secrets.

- Last successful accepted-key end-to-end proof: none established in this session.
- Failure condition: owner login cannot load protected data, or scheduled publishers reject their configured key.
- Observer: existing publisher workflows and issue #140; routine owner-page sign-in monitoring is not proven.
- Observer health: not newly verified in this diagnostic.
- Account-level action required: yes, Cloudflare-side credential reconciliation. Repository-only changes cannot establish secret parity.
- Exact next supervisory action: keep #215/#140 open, complete account reconciliation, then perform the accepted-key proof above. Do not describe deployment alone as restored access.
