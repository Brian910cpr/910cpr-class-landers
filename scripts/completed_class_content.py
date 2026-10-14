"""Completed-class presentation, independent of availability and payment routing.

The shared selector supplies calendar_html after its routing release gates pass.
This module must never infer course identity from a marketing title.
"""
from html import escape
from pathlib import PurePosixPath


def calendar_context(course_id: str, pages: dict) -> dict | None:
    """Resolve an exact legacy course ID using the existing selector catalog.

    Unknown and ambiguous IDs fail closed; family membership alone does not
    establish equivalent delivery, eligibility, or payment requirements.
    """
    course_id = str(course_id or "").strip()
    if not course_id:
        return None
    matches = []
    for key, page in pages.get("pages", {}).items():
        options = [option for option in page.get("course_options", [])
                   if str(option.get("course_id", "")) == course_id]
        if not options:
            continue
        output = PurePosixPath(page.get("output_path", ""))
        if output.parts[:1] != ("docs",) or ".." in output.parts or output.suffix != ".html":
            return None
        matches.append({
            "page_key": key,
            "course_id": course_id,
            "family": page.get("family", ""),
            "course_page_url": "/" + str(output.relative_to("docs")),
            "availability_url": f"/data/block-selector-availability/{key}.json",
        })
    return matches[0] if len(matches) == 1 else None


def render_completed_content(*, course_name: str, date_label: str,
                             location: str, calendar_html: str,
                             fallback_html: str) -> str:
    """Render the compact body; caller retains canonical head and diagnostics.

    calendar_html and fallback_html must be trusted renderer output, never
    registrant input. Keeping them separate guarantees crawlable links follow
    the calendar. No old-session registration action belongs in this body.
    """
    return f'''<main class="completed-class">
  <div class="notice" role="status">This class has passed.</div>
  <h1>{escape(course_name)} — choose a new date</h1>
  <section aria-label="Current matching dates">{calendar_html}</section>
  {fallback_html}
  <section class="section-box" aria-label="Original class details">
    <h2>Original class</h2>
    <p>{escape(course_name)} · {escape(date_label)} · {escape(location)}</p>
  </section>
</main>'''

