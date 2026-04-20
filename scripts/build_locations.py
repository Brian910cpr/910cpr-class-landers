import os
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
    sessions = load_sessions()
    future_public = upcoming_public_sessions(
        [s for s in sessions if getattr(s, "is_public", False)]
    )

    location_map = {}

    for s in future_public:
        city = str(getattr(s, "city", "")).strip()

        if not valid_city(city):
            continue

        location_map.setdefault(city, []).append(s)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    count = 0

    for city, city_sessions in location_map.items():
        html = render_page(
            title=f"CPR Classes in {city}",
            body=f"""
<h1>CPR Classes in {city}</h1>
{session_rows(city_sessions)}
""",
            description=f"Upcoming CPR classes in {city}.",
        )

        filename = os.path.join(OUTPUT_DIR, f"{slugify(city)}.html")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        count += 1

    print(f"Wrote {count} filtered location hub pages to {OUTPUT_DIR}")


if __name__ == "__main__":
    build_locations()