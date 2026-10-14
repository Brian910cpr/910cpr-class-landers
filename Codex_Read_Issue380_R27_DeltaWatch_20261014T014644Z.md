# Delta Watch acknowledgment — Issue 380 R27

Reviewed at 2026-10-14T01:46:44.243Z UTC.

Reviewed `Codex_Reply_Issue380_20261014_R27.md`, substantive commit `0661145b95512d28c0a6d61f1fc83b10e1ca2062`, its two new PostgreSQL negative controls, and green PR checks. The diagnostic genuinely proves two additional provenance-forgery paths: first-row INSERT without publication/audit and stale authoritative observation revival by refreshing timestamp/reference without provenance assignment. Both remain fail-closed at execution, but show that column-only protection is insufficient.

Accepted as diagnostic BUILT evidence only. No SQL behavior fix or acceptance criterion is complete. The next safe implementation boundary is an independently authenticated restricted collector/write protocol covering INSERT and every observation identity/outcome/freshness field, with forgery controls converted to denial/downgrade tests before installed consumer, external fence, and private UI evidence. Keep PR 381 draft and unapplied. No Brian/account action.
