import os
from scripts.build_status import BuildStatusReporter
from tqdm import tqdm
from scripts.hub_utils import (
    load_sessions,
    upcoming_public_sessions,
    render_page,
    session_rows,
    slugify,
)

OUTPUT_DIR = os.path.join("docs", "locations")


def valid_city(city: str) -> bool:
    value = str(city or "").strip()
    if not value:
        return False
    if value.lower() in {"nan", "none", "unknown"}:
        return False
    if value.isdigit():
        return False
    return True


def build_locations():
    reporter = BuildStatusReporter("build_locations")
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

        cities = sorted(location_map.items())
        reporter.waiting(total=len(cities))
        reporter.start(total=len(cities))
        print(f"Building {len(cities)} location pages")

        for city, city_sessions in tqdm(cities, desc="Building location pages", unit="page", miniters=1):
            html = render_page(
                title=f"CPR Classes in {city}",
                body=f"""
<h1>CPR Classes in {city}</h1>
{session_rows(city_sessions)}
""",
                description=f"Upcoming CPR classes in {city}.",
            )

            filename = os.path.join(OUTPUT_DIR, f"{slugify(city)}.html")
            last_output = filename

            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)

            count += 1
            reporter.update(current=count, total=len(cities), last_output_file=last_output)

        reporter.done(current=count, total=len(cities), last_output_file=last_output)
        print(f"Wrote {count} filtered location hub pages to {OUTPUT_DIR}")
    except Exception:
        reporter.error(current=count, last_output_file=last_output)
        raise


if __name__ == "__main__":
    build_locations()
