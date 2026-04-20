import os
from scripts.hub_utils import (
    load_sessions,
    upcoming_public_sessions,
    render_page,
    session_rows,
    slugify,
)

OUTPUT_DIR = os.path.join("docs", "course-at-city")


def valid_city(city: str) -> bool:
    value = str(city or "").strip()
    if not value:
        return False
    if value.lower() in {"nan", "none", "unknown"}:
        return False
    if value.isdigit():
        return False
    return True


def valid_family(family: str) -> bool:
    value = str(family or "").strip()
    return value in {
        "BLS",
        "ACLS",
        "PALS",
        "Heartsaver",
        "USCG Elementary First Aid | CPR",
    }


def build_course_at_city():
    sessions = load_sessions()
    future_public = upcoming_public_sessions(
        [s for s in sessions if getattr(s, "is_public", False)]
    )

    combo_map = {}

    for s in future_public:
        city = str(getattr(s, "city", "")).strip()
        family = str(getattr(s, "course_family", "")).strip()

        if not valid_city(city):
            continue

        if not valid_family(family):
            continue

        key = (family, city)
        combo_map.setdefault(key, []).append(s)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    count = 0

    for (family, city), group_sessions in combo_map.items():
        html = render_page(
            title=f"{family} Classes in {city}",
            body=f"""
<h1>{family} Classes in {city}</h1>
{session_rows(group_sessions)}
""",
            description=f"Upcoming {family} classes in {city}.",
        )

        filename = os.path.join(
            OUTPUT_DIR,
            f"{slugify(family)}-{slugify(city)}.html"
        )

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        count += 1

    print(f"Wrote {count} filtered course-at-city pages to {OUTPUT_DIR}")


if __name__ == "__main__":
    build_course_at_city()