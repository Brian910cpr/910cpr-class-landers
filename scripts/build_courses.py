
from pathlib import Path
from collections import defaultdict
from scripts.build_status import BuildStatusReporter
from scripts.hub_utils import load_sessions, upcoming_public_sessions, render_page, session_rows, slugify
try:
    from tqdm import tqdm
except ModuleNotFoundError:
    def tqdm(iterable, **_kwargs):
        return iterable

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "courses"
OUTPUT.mkdir(parents=True, exist_ok=True)


def purge_stale_outputs(output_dir: Path) -> int:
    removed = 0
    for path in output_dir.glob("*.html"):
        path.unlink(missing_ok=True)
        removed += 1
    return removed

def build():
    reporter = BuildStatusReporter("build_courses")
    last_output = None
    try:
        sessions = load_sessions()
        removed = purge_stale_outputs(OUTPUT)
        if removed:
            print(f"Removed {removed} stale course hub pages from {OUTPUT}")
        families = sorted({s.course_family for s in sessions if s.course_family})
        reporter.waiting(total=len(families))
        reporter.start(total=len(families))
        print(f"Loaded {len(sessions)} sessions")
        print(f"Building {len(families)} course hub pages")
        for index, family in enumerate(tqdm(families, desc="Building course hubs", unit="page", miniters=1), start=1):
            rows = upcoming_public_sessions(sessions, family=family)
            blocks = [f"<h1>{family}</h1>", "<p class='muted'>Live course hub built from Class Report.xlsx. Use this page to jump into actual upcoming sessions instead of a generic article.</p>", session_rows(rows, limit=20)]
            html = render_page(f"{family} Classes | 910CPR", "".join(blocks), f"Upcoming {family} classes and registration options from 910CPR.")
            last_output = OUTPUT / f"{slugify(family)}.html"
            last_output.write_text(html, encoding='utf-8')
            reporter.update(current=index, total=len(families), last_output_file=last_output)
        reporter.done(current=len(families), total=len(families), last_output_file=last_output)
        print(f"Wrote {len(families)} course hub pages to {OUTPUT}")
    except Exception:
        reporter.error(last_output_file=last_output)
        raise

if __name__ == "__main__":
    build()
