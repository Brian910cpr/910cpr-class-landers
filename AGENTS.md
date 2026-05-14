\# 910CPR Lander System Rules



\## Authoritative Inputs



Primary schedule source:



\* data/Class Report.xlsx



Primary runtime data contract:



\* docs/data/schedule\_future.json



Current-session intermediate:



\* data/sessions\_current.json



\## Generated Outputs



These are GENERATED and may be safely rebuilt:



\* docs/classes/\*.html

\* docs/courses/\*.html

\* docs/locations/\*.html

\* docs/index.html

\* docs/sitemap.xml



Do NOT manually edit generated outputs unless explicitly requested.



Prefer modifying generators over manually patching generated outputs.



\## Preferred Build Order



1\. build\_sessions\_current.py

2\. build\_schedule\_future.py

3\. build\_slug\_hubs.py

4\. build\_courses.py

5\. build\_locations.py

6\. build\_index\_and\_sitemap.py



\## Debug / Audit Artifacts



Debug outputs are authoritative for audits:



\* debug/latest\_build\_health.json

\* debug/stale\_sessions\_audit.json

\* debug/event\_schema\_audit.json



\## Important Operational Rules



\* schedule\_future.json is the authoritative public inventory contract.

\* Only real Enrollware sessions should become session landers.

\* Appointment availability is NOT pre-generated into landers.

\* Preserve existing working schema behavior unless explicitly modifying schema logic.

\* Avoid full-stack rebuilds unless required.

\* Prefer targeted builders for isolated fixes.

\* Prefer surgical modifications to authoritative source files.

\* Preserve compatibility with existing lander URLs whenever possible.

\* Preserve current JSON contracts unless explicitly changing them.



\## Dangerous Areas



Avoid mass rebuilds when only:



\* UI text

\* CSS

\* small JS logic

&#x20; changes are required.



Do not regenerate tens of thousands of landers unnecessarily.



Avoid broad refactors unless specifically requested.



\## Known Good / Stable



The following systems are considered operationally stable unless explicitly targeted for modification:



\* hub-ui.js routing stable as of 2026-05

\* JSON-LD event generation stable

\* schedule\_future.json contract stable

\* Cloudflare shortlink integration stable

\* Existing Enrollware enroll?id= link structures stable

\* Existing hub anchor structures stable (#provider, #renewal, #heartcode)

\* Existing sitemap generation stable



Do not rewrite stable systems solely for architectural elegance.



\## Preferred Engineering Style



\* Prefer surgical fixes over architectural rewrites.

\* Preserve operational quirks if they are relied upon.

\* Avoid replacing working systems simply because they are imperfect.

\* Minimize collateral rebuilds.

\* Assume uptime and continuity are more important than elegance.

\* When possible, identify the smallest authoritative file that can solve the issue.

\* Prefer deterministic and reproducible builds.

\* Preserve debug/audit visibility.

\* Avoid introducing unnecessary frameworks or dependencies.

\* Favor maintainability and operational reliability over abstraction.



\## Build / Validation Expectations



Before major rebuilds:



\* determine whether targeted rebuilds are sufficient

\* validate whether generated outputs are actually stale

\* avoid unnecessary regeneration loops



Before completion:



\* run syntax validation where practical

\* run lightweight behavioral validation where practical

\* clearly distinguish:



&#x20; \* locally validated

&#x20; \* dry-run validated

&#x20; \* deployed

&#x20; \* sandbox-only



\## Repository Philosophy



This repository is a production operational system, not merely a code experiment.



Priorities:



1\. Operational continuity

2\. Stable public URLs

3\. Search indexing continuity

4\. Conversion reliability

5\. Maintainable generation pipelines

6\. Low-friction updates

7\. Minimal unnecessary rebuilds



Prefer practical operational improvements over theoretical perfection.



