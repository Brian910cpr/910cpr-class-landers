# PR353 matching public page refresh

Existing admin refresh now uses existing write_page_outputs for configured selector customer pages, aliases and legacy redirects together with existing feeds. Explicit configured page paths staged; no sitewide generation. Expected scope8 feeds,17 public HTML,16 existing audit reports (audit reports not added to publication staging). This fixes stale customer star semantics after feed-only activation.

YAML and edited embedded Python syntax parsed.5 customer-render pipeline/probe tests passed. Latest active-policy real-source probe37628457691 still running when checked. Public merge/deployment not yet performed; only release wiring changed. Owner authorization retained. Two unrelated dirty generated pages remain untouched.
