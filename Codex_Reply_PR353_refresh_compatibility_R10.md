# Production V2 refresh compatibility repair

PR353 merged as23dbbf212 and Pages code deployment succeeded. Actual production refresh37629056654 stopped before commit/publication in write_page_outputs -> render_report: KeyError rejectedOfferCount, a legacy diagnostic count absent from V2. No booking mutations or failed-refresh publication occurred.

Narrow correction: existing refresh calls existing render_html and render_redirect_html directly for8 primary pages/aliases/redirects plus8 feeds. Removes legacy audit report invocation only, preserving live guards, feed serializer, customer renderer, staging and publication validation. No sitewide build requested.

YAML/embedded Python parsed.4 browser pipeline tests passed. Executed actual workflow Python using a V2 fixture lacking rejectedOfferCount in a temporary output directory; primary/alias/redirect/feed all produced, aliases identical and feed dates present. No unrelated repo output generated. Owner authorized deployment after checks; no repeated permission needed. Production rerun pending merge/checks. Existing Earl/Jackson dirty pages untouched.
