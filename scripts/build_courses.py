
from pathlib import Path
from collections import defaultdict
from scripts.hub_utils import load_sessions, upcoming_public_sessions, render_page, session_rows, slugify

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "courses"
OUTPUT.mkdir(parents=True, exist_ok=True)

def build():
    sessions = load_sessions()
    families = sorted({s.course_family for s in sessions if s.course_family})
    for family in families:
        rows = upcoming_public_sessions(sessions, family=family)
        blocks = [f"<h1>{family}</h1>", "<p class='muted'>Live course hub built from Class Report.xlsx. Use this page to jump into actual upcoming sessions instead of a generic article.</p>", session_rows(rows, limit=20)]
        html = render_page(f"{family} Classes | 910CPR", "".join(blocks), f"Upcoming {family} classes and registration options from 910CPR.")
        (OUTPUT / f"{slugify(family)}.html").write_text(html, encoding='utf-8')
    print(f"Wrote {len(families)} course hub pages to {OUTPUT}")

if __name__ == "__main__":
    build()
