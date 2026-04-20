import os
from scripts.hub_utils import (
    load_sessions,
    upcoming_public_sessions,
    render_page,
    session_rows,
    slugify,
)

OUTPUT_DIR = os.path.join("docs", "locations")


def is_public_location(location_name: str) -> bool:
    return location_name.strip().startswith(":: ")


def clean_location_name(location_name: str) -> str:
    # ":: Wilmington; Shipyard Blvd" → "Wilmington"
    name = location_name.replace("::", "").strip()
    return name.split(";")[0].strip()


def build_locations():
    sessions = load_sessions()

    location_map = {}

    for s in sessions:
        location = s.get("Location", "")

        if not is_public_location(location):
            continue

        city = clean_location_name(location)

        location_map.setdefault(city, []).append(s)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    count = 0

    for city, city_sessions in location_map.items():
        public = upcoming_public_sessions(city_sessions)

        if not public:
            continue  # skip empty public locations for now

        html = render_page(
            title=f"CPR Classes in {city}",
            content=f"""
<h1>CPR Classes in {city}</h1>
{session_rows(public)}
""",
        )

        filename = os.path.join(OUTPUT_DIR, f"{slugify(city)}.html")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        count += 1

    print(f"Wrote {count} filtered location hub pages to {OUTPUT_DIR}")


if __name__ == "__main__":
    build_locations()