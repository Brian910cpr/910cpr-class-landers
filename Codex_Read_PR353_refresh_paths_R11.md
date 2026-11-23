# Production V2 refresh absolute path repair

Actual refresh37630493480 stopped before publication: render_redirect_html requires target_path under absolute ROOT/docs, while new workflow passed relative docs/bls.html. Resolve primary, alias and redirect paths before rendering. No source, booking, duration or guards changed.

New tests/test_v2_refresh_workflow_render.py executes the actual embedded production workflow Python with real V2 fixture counts and production-shaped relative paths in a temporary workspace. Asserts primary/alias/redirect/feed generation, identical alias HTML and correct redirect.24 discovered targeted tests passed including browser pipeline. Existing unrelated dirty generated pages remain unstaged. Fresh publication still pending correction merge and run.
