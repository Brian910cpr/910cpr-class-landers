# Issue 338: refresh terminal checkpoint
Timestamp: 2026-10-02 10:24 UTC
Branch: fix/stale-feed-notice-20261002
Warning release: PR339 / fd28f7cf; live proof ee182ed47 recorded in R2, commit b74be1ea8; framed failure screenshot935cd04d1.
State: VERIFIED warning; PROVEN push-triggered admin and public refresh execution; new public deployment IN_PROGRESS.
Admin push36994082058 succeeded and Pages36994585614 succeeded. Public push36994082057 succeeded, jobduration6m49s, producing acf519234b4516c352df288c9cc785fb668dba04. Its Pages36995218843 remains in progress at this checkpoint. Last live byte/customer proof remains ee182ed47 with BLS/HS unexpired11:43/11:44UTC.
Both runs were event=push, not scheduled recovery. Public strict audit succeeded with existing reconciliation annotations; no denied bridge was retried. Original roster guard remains. Source integrity and Cloudflare preflight on evidence branch succeeded.
Next: confirm Pages36995218843 success, fetch all8 changed liveHTML +4feeds and bytecompare acf519234, rerun GET-only fresh/stale browser if HTML changed. Treat R2 failed-fetch calendar clearing as unresolved limitation. Reliability remedy and missing-trigger evidence remain as R2; no workflow modifications/new persistent access made.
Evidence level PROVEN for verified warning and these explicit push runs, not HEALTHY automatic scheduling. No owner action required for remaining read-only deployment/live checks; precise denied bridge approval remains separate.
