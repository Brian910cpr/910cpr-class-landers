# PR353 explicit instructor coverage repair

Explicit-only availability calendars now establish bounded coverage for actual normalized available blocks, intersected with all successful configured-owner export bounds. They no longer require an inverse calendar. Empty explicit calendars, missing block times, failed/stale/partial exports still establish no free time. Existing qualifications and occupancy remain required.

46 coverage/readiness/publication/adapter tests passed. Syntax checked. Regression proves exactly9:00–12:00 coverage, not90-day free time, and failed/empty sources fail closed.

Prior real-source repairs: runs37623074577 (course-format distinction) and37623211507 (90+15 Heartsaver duration) completed successfully. Public deployment remains stopped under persisted PR353 acceptance hold; latest review has not cleared merge/activation. This repair is persisted/pushed; exact-head actual-source proof pending. Explicit sources had no current events in earlier proof, so no invented real additional availability claimed.
