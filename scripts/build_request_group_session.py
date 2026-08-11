from pathlib import Path

from scripts.build_status import BuildStatusReporter
from scripts.hub_utils import render_page


OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "request_group_session.html"


def build() -> None:
    reporter = BuildStatusReporter("build_request_group_session")
    reporter.set_context(outputs=[OUTPUT])
    reporter.waiting(total=1)
    reporter.start(total=1)
    body = """
<main class='card request-adapter-shell'>
  <header class='site-brand-bar'>
    <a class='site-brand-link' href='/index.html' aria-label='910CPR home'><img class='site-brand-logo' src='/images/logo.png' alt='910CPR logo'><span class='site-brand-wordmark'>910CPR</span></a>
    <a class='site-header-phone' href='tel:+19103955193'>910-395-5193</a>
  </header>
  <section class='request-adapter-message'>
    <div class='eyebrow'>Group Training Request</div>
    <h1>Continue to Build Your Training Day</h1>
    <p>Your program, timing, and location details will carry into the combined corporate training builder.</p>
    <a class='button primary' data-builder-link href='/group-training.html'>Continue</a>
  </section>
</main>
<script>
(function () {
  var target = "/group-training.html" + window.location.search + window.location.hash;
  var link = document.querySelector("[data-builder-link]");
  if (link) link.href = target;
  window.location.replace(target);
})();
</script>
"""
    html = render_page(
        "Group Training Request | 910CPR",
        body,
        "Continue an existing group-training request in the 910CPR Build Your Training Day planner.",
        "/group-training.html",
    )
    OUTPUT.write_text(html, encoding="utf-8")
    reporter.done(
        current=1,
        total=1,
        last_output_file=OUTPUT,
        pages_generated=1,
        counts={"compatibility_adapters": 1},
    )
    print(f"Wrote compatibility adapter {OUTPUT}")


if __name__ == "__main__":
    build()
