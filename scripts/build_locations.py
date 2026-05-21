import os
from pathlib import Path
from scripts.build_status import BuildStatusReporter
try:
    from tqdm import tqdm
except ModuleNotFoundError:
    def tqdm(iterable, **_kwargs):
        return iterable
from scripts.hub_utils import (
    load_sessions,
    upcoming_public_sessions,
    render_page,
    session_rows,
    slugify,
)

OUTPUT_DIR = os.path.join("docs", "locations")
ROOT = Path(__file__).resolve().parents[1]
SESSIONS_INPUT = ROOT / "data" / "sessions_current.json"


def valid_city(city: str) -> bool:
    value = str(city or "").strip()
    if not value:
        return False
    if value.lower() in {"nan", "none", "unknown"}:
        return False
    if value.isdigit():
        return False
    return True


def purge_stale_outputs(output_dir: str) -> int:
    removed = 0
    for name in os.listdir(output_dir):
        if not name.lower().endswith(".html"):
            continue
        path = os.path.join(output_dir, name)
        if os.path.isfile(path):
            os.remove(path)
            removed += 1
    return removed


def build_locations():
    reporter = BuildStatusReporter("build_locations")
    reporter.set_context(inputs=[SESSIONS_INPUT], outputs=[ROOT / OUTPUT_DIR])
    count = 0
    last_output = None
    try:
        sessions = load_sessions()
        future_public = upcoming_public_sessions(
            [s for s in sessions if getattr(s, "is_public", False)]
        )
        print(f"Loaded {len(sessions)} sessions")
        print(f"Found {len(future_public)} upcoming public sessions")

        location_map = {}

        for s in future_public:
            city = str(getattr(s, "city", "")).strip()

            if not valid_city(city):
                continue

            location_map.setdefault(city, []).append(s)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        removed = purge_stale_outputs(OUTPUT_DIR)
        if removed:
            print(f"Removed {removed} stale location pages from {OUTPUT_DIR}")

        cities = sorted(location_map.items())
        reporter.waiting(total=len(cities))
        reporter.start(total=len(cities))
        print(f"Building {len(cities)} location pages")

        for city, city_sessions in tqdm(cities, desc="Building location pages", unit="page", miniters=1):
            filename = os.path.join(OUTPUT_DIR, f"{slugify(city)}.html")
            html = render_page(
                title=f"CPR Classes in {city}",
                body=f"""
<h1>CPR Classes in {city}</h1>
{session_rows(city_sessions)}
""",
                description=f"Upcoming CPR classes in {city}.",
                canonical_path="/" + filename.replace(os.sep, "/"),
            )

            last_output = filename

            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)

            count += 1
            reporter.update(current=count, total=len(cities), last_output_file=last_output)

        reporter.done(
            current=count,
            total=len(cities),
            last_output_file=last_output,
            pages_generated=count,
            counts={
                "sessions_loaded": len(sessions),
                "future_public_sessions": len(future_public),
                "location_pages": count,
            },
        )
        print(f"Wrote {count} filtered location hub pages to {OUTPUT_DIR}")
    except Exception:
        reporter.error(current=count, last_output_file=last_output)
        raise


if __name__ == "__main__":
    build_locations()
