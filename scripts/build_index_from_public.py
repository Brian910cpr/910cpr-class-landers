import json
import os

INPUT = "docs/data/public_schedule.json"
OUTPUT = "docs/schedule.html"


PATHWAYS = [
    {
        "title": "Healthcare Provider",
        "body": "For healthcare workers, nursing students, dental offices, hospital staff, EMS, and clinical requirements.",
        "courses": ["BLS", "ACLS", "PALS"],
        "links": [("BLS dates", "/bls.html"), ("ACLS dates", "/acls.html"), ("PALS dates", "/pals.html")],
    },
    {
        "title": "Workplace, Daycare, School, or Coach",
        "body": "For workplace safety, childcare, schools, coaches, foster care, camps, and general CPR / first aid needs.",
        "courses": ["Heartsaver First Aid CPR AED", "Heartsaver CPR AED", "Pediatric First Aid CPR AED", "Family & Friends CPR"],
        "links": [("Heartsaver dates", "/heartsaver.html"), ("Pediatric dates", "/heartsaver.html?program=Pediatric%20First%20Aid%20CPR%20AED%20Blended")],
    },
    {
        "title": "American Red Cross Required",
        "body": "For students, employers, schools, or programs that specifically require Red Cross certification.",
        "courses": ["ARC BLS", "ARC First Aid CPR AED", "ARC blended options where available"],
        "links": [("Red Cross options", "/arc.html")],
    },
    {
        "title": "HSI Required",
        "body": "For employers, schools, or organizations that specifically accept or request HSI certification.",
        "courses": ["HSI CPR AED", "HSI First Aid CPR AED", "HSI blended options where available"],
        "links": [("HSI options", "/hsi.html")],
    },
    {
        "title": "USCG / Maritime",
        "body": "For mariners, captains, crews, and maritime employers who need USCG-aligned first aid and CPR.",
        "courses": ["USCG Elementary First Aid CPR AED"],
        "links": [("USCG / maritime dates", "/uscg-elementary-first-aid-cpr.html")],
    },
    {
        "title": "Not Sure What I Need",
        "body": "If your requirement is unclear, contact 910CPR before choosing a class date.",
        "courses": ["Match your employer, school, agency, or licensing wording first"],
        "links": [("Call 910-395-5193", "tel:9103955193"), ("Ask about a class", "/request_group_session.html")],
    },
]


def load_sessions():
    with open(INPUT, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload if isinstance(payload, list) else payload.get("sessions", [])


def esc(value):
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_pathway(pathway):
    courses = "".join(f"<li>{esc(course)}</li>" for course in pathway["courses"])
    links = "".join(f'<a class="button" href="{esc(href)}">{esc(label)}</a>' for label, href in pathway["links"])
    return f"""
<article class="schedule-route-card">
  <h2>{esc(pathway["title"])}</h2>
  <p>{esc(pathway["body"])}</p>
  <strong>Common course names</strong>
  <ul>{courses}</ul>
  <div class="actions">{links}</div>
</article>
"""


def build_html(sessions):
    count = len(sessions)
    cards = "".join(render_pathway(pathway) for pathway in PATHWAYS)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Choose a CPR Class Before Viewing Dates | 910CPR</title>
<meta name="description" content="Choose the right CPR, BLS, ACLS, PALS, Heartsaver, Red Cross, HSI, or USCG training path before viewing matching 910CPR class dates.">
<link rel="canonical" href="https://www.910cpr.com/schedule.html">
<link rel="stylesheet" href="/css/lander.css">
<style>
body {{ margin: 0; font-family: Arial, sans-serif; color: #17324a; background: #eef8ff; }}
.schedule-route-shell {{ max-width: 1060px; margin: 0 auto; padding: 28px 16px 54px; }}
.schedule-route-hero, .schedule-route-card {{ background: #fff; border: 1px solid #d7e8ef; border-radius: 22px; box-shadow: 0 10px 22px rgba(18,58,87,.05); }}
.schedule-route-hero {{ padding: 26px; margin-bottom: 18px; }}
.schedule-route-hero h1 {{ margin: 0 0 10px; color: #123a57; font-size: clamp(2rem, 8vw, 3.2rem); line-height: 1.05; }}
.schedule-route-hero p {{ margin: 0; max-width: 760px; color: #5d7488; line-height: 1.65; }}
.schedule-route-grid {{ display: grid; grid-template-columns: 1fr; gap: 16px; }}
.schedule-route-card {{ padding: 22px; }}
.schedule-route-card h2 {{ margin: 0 0 8px; color: #123a57; }}
.schedule-route-card p, .schedule-route-card li {{ color: #5d7488; line-height: 1.55; }}
.actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 14px; }}
.button {{ display: inline-flex; align-items: center; justify-content: center; min-height: 42px; padding: 10px 14px; border-radius: 8px; background: #eb7b4d; color: #fff; font-weight: 800; text-decoration: none; }}
@media (min-width: 820px) {{ .schedule-route-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
</style>
</head>
<body>
<main class="schedule-route-shell">
  <section class="schedule-route-hero">
    <p><a href="/index.html">910CPR home</a></p>
    <h1>Choose a course before viewing dates</h1>
    <p>The old all-class schedule list has been replaced with course-specific paths. Start with the requirement you need, choose the delivery format on that course page, then pick a matching date. Current schedule source contains {count} records.</p>
  </section>
  <section class="schedule-route-grid" aria-label="Course selection paths">
{cards}
  </section>
</main>
</body>
</html>
"""


def main():
    print("Loading public schedule...")
    sessions = load_sessions()
    print(f"Sessions loaded: {len(sessions)}")

    html = build_html(sessions)

    os.makedirs("docs", exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote: {OUTPUT}")


if __name__ == "__main__":
    main()
