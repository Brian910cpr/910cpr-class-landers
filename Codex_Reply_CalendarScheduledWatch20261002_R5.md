# Issue338 automatic refresh checkpoint R5
Timestamp:2026-10-02T05:44:23.253576+00:00
Branch:fix/calendar-open-shifts-20261002
Previous commit:8828ce351
State:IN_PROGRESS scheduling recovery; BLOCKED public bridge awaiting owneranswer. Evidence:manual projection recovery PROVEN; scheduled cadence NOT PROVEN/HEALTHY.

Eight bounded read-only polls 2026-10-02T05:38:14.862332+00:00 through 2026-10-02T05:43:35.410842+00:00 found zero scheduled runs after manual36968821283 and no live feed timestamp advancement. Live BLS generatedAt remains2026-10-02T01:26:42.312667 (Eastern,05:26UTC); validUntil2026-10-02T06:57:01.780686+00:00; unexpired at everycheck. Missed05:37cron window observed through05:43; nextexpected05:47 then05:57. Scheduler may delay; no exact cause proved.

Read-only diagnosis:repository notarchived/disabled; defaultbranchmain; Actions enabled/allowedall; workflow315399794 active; production cron7,17,27,37,47,57. Last scheduled36948145959 at00:52UTC succeeded,actorBrian910cpr/main. Manualdispatch and productionPages deployment succeeded. Recent workflow changes034e76d23/47053dcee correctedcheckoutcurrentmain/buildinputs/tests,notcron. No queued refresh or failing invokedjob found. GitHub official status API reports AllSystemsOperational/no unresolvedincidents. These facts rule out observed disabledworkflow/defaultbranch/jobfailure,not unseen GitHub scheduler/account failures.

API caution:event=schedule filtered query inconsistently returns onlySeptember11andolder,despite exactrun36948145959/unfilteredworkflowhistory showingOct2schedule. HeaderDate iscurrent05:39UTC andcachemaxage60. Boundedwatch therefore used exactworkflowID/unfilteredhistory; additional no-cache created>=Oct2query returnedmanual05:24+scheduled00:52 only. Do not use filteredquery's Septdate as lastactualscheduledrun.

No second manualrefresh,cron/accesschange,securitychange,pendingproductionedit,source/bookingmutation or denialworkaround occurred. Do not blindly refresh manually and callpermanentfix. Safe next:continue boundedwatch through05:47plusnormalqueue window and verifyanygenuineevent=schedule producesnewlivefeeds before06:57expiry. If trigger remains absent, collectrequestIDs/timewindow forGitHubsupport or obtainapprovalforindependent observed scheduler strategy; avoidspeculativeworkflowreset. This localwatch isephemeral diagnostic,notroutineproductionmonitor; ownerisnotclaimedrelievedofmonitoring.

PriorreceiptR3 has exactautomatic-reviewdenials; bridge remainspaused whileparent awaitsowneranswer. AllunrelatedEarl/Jacksonchangespreserved. Fulltask remainsopen.
