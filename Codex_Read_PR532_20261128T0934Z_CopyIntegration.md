# P0/migration adjacent — BLS Renewal copy integration

2026-11-28 09:34 UTC, PR_OPEN (draft), branch `dot/bls-renewal-current-card-copy-20261128`, substantive integration commit `8401286d548670fb74aaf7e9b8581223e6f2497a`.

Imported current main into the draft and resolved only the two BLS page alias conflicts. The generated pages are exact copies; reversing the five copy substitutions produces the exact current-main bytes, preserving all newer schedule, hero, checkout and route changes. The two source records and focused regression test remain scoped to current-card guidance. 18 local family-publication tests pass, including regeneration of the exact Renewal option and deep link. New draft head still needs exact-host mobile selector QA; no production publish, enrollment or payment. This is the existing 910CPR wording, not a new AHA rule or a change to any existing student.
