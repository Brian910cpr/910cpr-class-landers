# Issue 242 — acquisition inventory checkpoint

Timestamp: 2026-10-14 UTC. Work state: IN_PROGRESS. Persistent acquisition evidence: BUILT only; no complete acquisition cycle established.

## Reproducible evidence

Baseline: 47a10dc2d2c (origin/main at worktree creation). Run `python -B scripts/audit_growth_inventory.py` to reproduce the read-only inventory. Exact machine output: `data/audit/issue242_growth_inventory_20261014.json`.

- 1,089 HTML files, including private/admin surfaces; this is NOT an indexable-page count.
- 209 files in the classes family; 36 courses; 13 topics; 64 topics-year; several course/date families have 109–110 files each.
- Root sitemap: one urlset, 60 URLs, 5,194 bytes, no duplicate URLs or missing local targets. No root sitemap index detected. This does not establish intentional coverage or deployed correctness.
- Existing public inventory pipeline: `scripts/build_landers.py` consumes schedule_future/canonical Class Report inputs. `scripts/build_index_and_sitemap.py` owns root/archive indexes, locations and sitemap, and explicitly identifies stale archive index directories. `scripts/build_index.py` retains topics/year archive logic. `scripts/build_course_at_city.py` retains local-course generation. `scripts/build_date_availability_pages.py` owns date availability surfaces. Reuse these sources; do not create a competing catalog or generator.
- `.github/workflows/refresh-admin-availability.yml` invokes the existing lander builder with `--anchors-only`; `.github/workflows/retire-expired-public-pages.yml` can modify classes and sitemap. Restoration must reconcile retention policy with these writers before enabling bulk archive output.
- Initial checkout is shallow. Explicitly fetched recovery point `f523c364ccbb29fffdf96fec1b4a915421f682bd` from #229 successfully. `git ls-tree -r --name-only f523c364ccbb29fffdf96fec1b4a915421f682bd docs/classes | Measure-Object -Line` returns 1812 entries. This does not establish all entries are legitimate public class pages or recover the reported 24k corpus. No source privacy review performed.

## Tests and limitations

`python -B -m unittest tests.test_growth_inventory_audit`: 1 passed, proves counting, duplicate/missing target detection, and no input mutation.
`python -B -m unittest tests.test_growth_seo_surfaces`: 3 passed, 1 failed. Existing group-training rendering lacks the test's expected `href="#request-form"`; request form itself is rendered. No inference that public form submission is broken. Full traceback observed locally; assertion is at `tests/test_growth_seo_surfaces.py:45`.

No public builders ran. No site pages intentionally changed. New worktree has pre-existing checkout normalization differences in `docs/Earl/index.html` and `docs/Jackson/index.html`; neither is staged.

## Dependencies and next useful milestone

#229 owns historical recovery and editorial authority; existing PRs #230–233 cover recovery/privacy, identity and monitor work. #257 owns SEO intelligence/GSC/GA reconciliation. #392 owns archive reconciliation and sitemap integrity. Keep those assignments intact and reuse their work. #372 remains draft, unmerged and undeployed. Queue sweep also found P0 registration/schedule assignments; this audit does not claim to clear those higher-priority gates.

Next: reconcile #229/#392 source recovery and public-safe URL inventory with retirement/sitemap writers, then select an existing family for controlled rendered QA. Do not bulk restore or manufacture pages to meet a count. Report expected generator write scope and obtain the required bulk-run approval first. GSC/GA conversion/indexing evidence is not established in this dispatch; authenticated measurement must be obtained through the existing SEO workstream before claiming acquisition proof.

Monitoring contract remains unproven: useful success requires deployed differentiated pages → crawl/index evidence → attributed qualified visits/conversions. Cadence, last successful full cycle, stale detector, observer and observer health are not established here. Recovery path is the source/writer reconciliation above. Brian is not designated the routine monitor. No new Enrollware dependency introduced; independent acquisition restoration remains pending operational proof.
