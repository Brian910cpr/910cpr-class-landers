# GitHub scheduled refresh investigation

Repository: Brian910cpr/910cpr-class-landers
Workflow: `.github/workflows/refresh-admin-availability.yml` (ID315399794)
Production cron: `7,17,27,37,47,57 * * * *`, UTC, on default branch `main`.

The observed failure is missing schedule-trigger delivery, not a failed invoked generator. The last observed scheduled run36948145959 began2026-10-02 at00:52:13UTC and succeeded. The preceding scheduled run36927521781 also succeeded. Manual run36968821283 at05:24:54UTC succeeded, producing commita87a4d5d5a3b72eaabf143d8696e95b82b324625; Pages run36969265705 succeeded. The live feeds matched that commit exactly.

Repository checks show Actions enabled, workflow active, repository neither archived nor disabled, default branchmain, and scheduled actorBrian910cpr. Recent changes034e76d23 and47053dcee corrected checkout/build inputs/tests without changing cron. Official GitHub status reported no unresolved incident. These observations do not prove a provider or account root cause.

The REST event filter is inconsistent. `event=schedule` omitted known recent runs and returned September11 or older, while exact run36948145959 and the unfiltered workflow history identify it as an October2 scheduled run. At05:39UTC, the filtered response had request IDCAEA:10CF44:1F5DE0:68915D:6ABF4378; unfiltered response IDCAEE:1A618E:20A2B4:6C8CBC:6ABF4379. Both response dates were current, with cache age limit60seconds. A no-cache query restricted to October2 returned the00:52 scheduled and05:24 manual runs only. The watch uses unfiltered exact workflow history.

GitHub documents that scheduled events can be delayed or dropped under load. This cron already avoids minute zero. Documentation does not establish that load caused this particular gap.

If the05:47 window remains silent, give GitHub Support this workflow/run/request-ID evidence and ask why active schedule events were not delivered and why the event filter omits known runs. No support message has been sent. Avoid speculative disable/enable or security changes. Use the existing manual dispatch only as an explicitly approved emergency recovery, not as a permanent fix.

A later independent freshness watchdog would need explicit persistent-system scope, an observer and observer-health proof, a bounded recovery path and an escalation boundary. It must not depend on Brian remembering routine checks. No watchdog or new access was created here.

Recovery requires a genuinely scheduled run, successful refresh and deployment, advanced live source timestamps and rendered public offers before BLS expiry06:57:01UTC. One observed recovery would prove that process once, not justify HEALTHY.

Reference: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
Evidence: `public-calendar-refresh-verification.json`, `scheduled-refresh-watch.json`, and the subsequent spaced-watch artifact.

## Subsequent evidence,05:54UTC
A different existing workflow, Refresh public site from Enrollware iCal (ID301038681), ran with event=schedule at05:41:46UTC:run36970091836 SUCCESS. It produced adf0b6a3d7726b6c05d2b8189653f7b2a8b8b97e; Pages36970625997 SUCCESS. Public BLS/Heartsaver feeds advanced to05:44UTC and matched that commit; expiry07:15/07:16UTC. Thus automatic public publication is proved once; the earlier missing-run concern is specific to the admin workflow, not all repository schedules.

The public workflow refreshes calendar snapshots only under its existing changed-hash/build condition and publishes admin_schedule, but does not invoke publish_admin_availability. Accordingly live admin_availability still shows05:26UTC, despite fresh public selectors. Merely adding a publisher under a conditional build may not guarantee cadence.

Concrete bounded resilience proposal: add a success-gated workflow_run trigger to the existing admin refresh after completion of the existing public refresh, retaining the admin workflow's full current validation and avoiding a loop. This needs explicit review as a persistent trigger change; no code or settings were changed here. It adds a second existing trigger path without new access or roster relaxation. Alternatively investigate/re-register the existing admin cron through GitHub Support; there is no proved syntax/configuration error to fix. Neither proposal justifies HEALTHY without repeated outcome and observer-health proof.
