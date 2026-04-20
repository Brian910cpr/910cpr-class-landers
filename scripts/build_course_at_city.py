import os
from scripts.hub_utils import (
    load_sessions,
    upcoming_public_sessions,
    render_page,
    session_rows,
    slugify,
)

OUTPUT_DIR = os.path.join("docs", "course-at-city")


def is_public_location(location_name: str) -> bool:
    return location_name.strip().startswith(":: ")


def clean_city(location_name: str) -> str:
    name = location_name.replace("::", "").strip()
    return name.split(";")[0].strip()


def get_course_family(course_name: str) -> str:
    course_name = course_name.lower()

    if "bls" in course_name:
        return "BLS"
    if "acls" in course_name:
        return "ACLS"
    if "pals" in course_name:
        return "PALS"
    if "heartsaver" in course_name or "first aid" in course_name:
        return "First Aid CPR AED"
    if "uscg" in course_name:
        return "USCG First Aid CPR"

    return None


def build_course_at_city():
    sessions = load_sessions()

    combo_map = {}

    for s in sessions:
        location = s.get("Location", "")
        course = s.get("Course", "")

        if not is_public_location(location):
            continue

        family = get_course_family(course)

        if not family:
            continue

        city = clean_city(location)

        key = (family, city)
        combo_map.setdefault(key, []).append(s)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    count = 0

    for (family, city), group_sessions in combo_map.items():
        public = upcoming_public_sessions(group_sessions)

        if not public:
            continue

        html = render_page(
            title=f"{family} Classes in {city}",
            content=f"""
<h1>{family} Classes in {city}</h1>
{session_rows(public)}
""",
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