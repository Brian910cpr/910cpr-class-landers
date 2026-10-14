# Issue 392 first milestone — 2026-10-14

## Scope and evidence
This is a read-only engineering checkpoint, not Enrollware exit completion. No source ZIP bytes were read. The owner reports 26 current Drive ZIPs (~13.59 GB); ZIP integrity, document totals, checksums, duplicates and date coverage remain UNKNOWN. The replacement Class Report (66)(1).xlsx was not found under the primary checkout data directory. No older archive inventory is promoted as current evidence.

## Historical path gaps at baseline 47a10dc2d2c6853a9fe88e96f4fb7b485334b07e
- `supabase/functions/class-registry/index.ts:13`: operational sessions only, start_at >= now minus one day, limit 500 without pagination. Therefore this registry cannot search the historical corpus, even if imports exist.
- `docs/assets/class-registry.js:19`: canonical enrichment is now minus two days through plus 400 days. Search is local over loaded records (`filtered`), including participant names/email only when enriched. Historic student search cannot find records excluded upstream.
- `supabase/functions/canonical-session-workspace/index.ts:97`: canonical listing uses class_sessions -> registrations -> customers, paginates by 500, but filters record_scope=operational and operational statuses. Detail lookup at line 124 also requires operational scope. Historical import scopes must be inspected before changing either filter. The older session-workspace implementation uses a different landerware_* model; do not mistake it for the canonical customer path.
- `docs/assets/class-registry.js:15`: stable detail links target `/admin/all-classes.html?session=<canonical id>`. End-to-end historical authorization, roster, documents, student, instructor and organization navigation have NOT been production-proven in this dispatch.
- `supabase/functions/nhcso-workspace/index.ts:726`: list_classes reads nhcso_classes, caps 250, reads separate nhcso_students/documents; no archive feed is returned in this action. It calls settleEligibleClasses, so do NOT invoke it as a mutation-free diagnostic.
- Missing database rows versus missing projection cannot be counted from source code. Source classes/canonical sessions/matches/unknown rosters/orphans/participants/evidence counts remain UNKNOWN, not zero.

## Existing work and dependencies
- #141 is QUEUED behind #157 R3 (latest owner instruction); #140 is cleared. Do not repeat the obsolete credential blocker. Preserve #193 -> #194 -> #195 -> #196; isolated PostgreSQL safety proof does not authorize production migration.
- #327 owns NHCSO history rail restoration; preserve lifecycle #325/#326 and latency PR #324.
- #297 owns current roster reconciliation; #150 specifies customers as students, people as staff. #209/PR #210 owns registry UI. Preserve these implementations rather than opening a second deep rewrite.
- Existing archive source/identity/monitor PRs #230/#231/#232/#233 remain the integration/review candidates; their old source counts are not evidence about the superseding Drive folder.
- Draft #372 was neither merged nor deployed.
- Queue sweep inspected open issues; higher-priority #334/#367/#380 have existing draft workstreams. No competing backend implementation was started.

## Sitemap observation
`python -B -m scripts.audit_public_sitemap --live`:
- Local and live: 60 URLs, 60 unique, duplicates 0; classes 20, courses 32, other public 8.
- Private-path, foreign/insecure, parameterized entries detected: 0 (absent category keys represent no detections).
- Live HTTP 200; Last-Modified Wed, 14 Oct 2026 17:13:16 GMT. robots declares the sitemap.
- lastmod elements 0; local-only 1 and live-only 1 at this baseline. Production moved during investigation; this is a baseline difference, not proof of publication failure.
- URL target reachability/canonical consistency and Google last fetch/submission UNKNOWN. No indexing claim.
- Pages API: legacy GitHub Pages, custom domain https://www.910cpr.com/, status built. Recent successful Pages run 38604625370; another run 38605516242 was in flight.
- `scripts/build_all.py:18` invokes build_index_and_sitemap. That generator writes homepage, class/course indexes, bridge courses, locations, stale-link containment, sitemap and robots: it is NOT a sitemap-only command. Do not execute it for this diagnostic.
- `scripts/generate_sitemap.py` is another sitemap writer. `.github/workflows/retire-expired-public-pages.yml` also updates sitemap. Consolidation and publish coverage require follow-up against current main; no broad rebuild authorized here.

## Validation and next repair
Added aggregate-only read-only sitemap inspection plus tests for duplicates/privacy boundaries, missing dates and wrong-document rejection. It never writes source files and does not emit private records/URLs in its JSON report. Three tests pass. No production DB credential inspection, writes, schema migration, source import, customer send or deployment occurred.

Next: review this checkpoint alongside existing #230/#231 and registry PR #210, obtain the current replacement report and authorized current archive bytes privately, and resume the canonical backfill only when the existing deep-workstream gate opens. Add a bounded authorized historical read/search route over verified scopes with stable detail resolution and private integration fixtures; do not simply remove operational-scope protections. Separately choose the authoritative sitemap writer and add publish-time validation before any generator run.
