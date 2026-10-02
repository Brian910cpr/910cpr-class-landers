# Issue338 scheduled public refresh proof R6
Timestamp:2026-10-02T05:56UTC
Branch:fix/calendar-open-shifts-20261002
Previous local commit:2af429268
State:scheduled public projection recovery VERIFIED once; public block-edge replacement BLOCKED awaiting owner approval. Evidence level PROVEN for observed publication outcome, not HEALTHY.

Three spaced checks at05:48,05:51,05:54:45UTC found no new admin-workflow run. The05:51 check detected live timestamp advancement and triggered trace investigation rather than another manual refresh.

Actual producing run36970091836 was event=schedule on .github/workflows/refresh-public-site.yml, ID301038681, created05:41:46UTC, SUCCESS. Its configured cron is13,43 * * * *. It published adf0b6a3d7726b6c05d2b8189653f7b2a8b8b97e (52 incumbent output changes). Pages36970625997 succeeded for that exact SHA.

At05:54UTC live schedule/admin availability/BLS/Heartsaver bytes matched that commit exactly. Schedule advanced05:48UTC; public selectors generated05:44UTC, unexpired until07:15:56UTC BLS and07:16:40UTC Heartsaver. GET-only actual BLS/Heartsaver calendars renderedOct5 starts and established booking links with zero errors/no refresh-warning. ExistingOct2 12:45PM BLS class andOct3 13:00 F&F projection persist. F&F canonical/source mismatch remains protected. No registrations or source classes edited.

Important limitation:admin_availability remains05:26:42UTC. Public workflow exports/builds fresh calendar snapshots under changed-hash conditions and publishes admin_schedule, but does not publish_admin_availability. The ten-minute admin cron remains silent through05:54:45. Automatic public refresh is therefore proved once; all admin freshness/cadence recovery is not proved.

Safe concrete remedy proposal:review a success-gated workflow_run trigger on existing admin refresh after existing public refresh completes, retaining all current validators and avoiding trigger loops. This is independent of the denied selector replacement and does not require new access or weaker roster safety. A simpler conditional availability-publisher addition alone would not guarantee refresh when public hash/build conditions are false. No trigger/security/settings changes were performed. GitHub Support bundle includes current configuration/run/request-ID evidence; no support message sent. Exact admin scheduler cause remains unproved; GitHub documentation allows delay/drop, which is a possibility, not a diagnosis.

Files:scheduled-public-refresh-verification.json; scheduled-refresh-spaced-watch.json; github-scheduler-investigation.md. No new tests needed for read-only diagnostics; eight offline planner/final local calendar tests remain prior evidence only. No denied edits retried. No additional manual dispatch. Earl/Jackson unrelated changes preserved. Parent next:relay genuine scheduled-public proof, consider the narrowly scoped trigger remedy separately, and await the owner's precise bridge approval. Full requested block-edge task remains open.
