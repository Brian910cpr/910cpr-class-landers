"""Render static 910CPR industry pages; no schedule, checkout, or booking writes."""
from __future__ import annotations

import argparse
from html import escape as e
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.ensure_analytics_tags import (  # noqa: E402
    ATTRIBUTION_SCRIPT_SNIPPET, GTM_HEAD_SNIPPET, GTM_NOSCRIPT_SNIPPET,
)

DOCS = ROOT / "docs"
ASSETS = DOCS / "assets" / "industry-landers"
BASE = "https://www.910cpr.com"
DIRECTORY = "/group-training/industries/"
CTA = "/group-training.html#request-form"
REVIEW = "https://www.google.com/maps/search/?api=1&query=910CPR%204018%20Shipyard%20Blvd%20Wilmington%20NC%2028403"
BADGES = {
    "aha": ("American Heart Association", "/images/0aha.png"),
    "arc": ("American Red Cross", "/images/0arc.png"),
    "hsi": ("Health & Safety Institute", "/images/0hsi.png"),
}
# Original vector illustrations. The path coordinates use a 32-unit grid.
ICONS = {
 "office": "M5 27V9h22v18M9 13h3m4 0h3m4 0h1M9 17h3m4 0h3m4 0h1M9 21h3m4 0h3m4 0h1M3 27h26",
 "factory": "M3 26V15l8-5v6l8-6v6l7-4 2 14H3Zm4-6h2m5 0h2m5 0h2M22 12l2-7h3l1 9",
 "build": "M5 27h22M9 27V5h14v22M9 9h14M9 13h14M9 17h14M9 21h14M9 25h14M9 5l14 4M23 9 9 13",
 "water": "M3 23q3-4 6 0t6 0t6 0t7 0M4 27q3-4 6 0t6 0t6 0t6 0M6 18l3-7h14l3 7H6Zm7-7V6h6v5m-3-5V3",
 "care": "M16 27 5 16C-1 9 9 3 16 10 23 3 33 9 27 16L16 27Z M10 16h4l2-4 3 7 2-3h2",
 "clinical": "M13 5h6v8h8v6h-8v8h-6v-8H5v-6h8z",
 "hospitality": "M5 27h22M6 22h20v-4a10 10 0 0 0-20 0v4Zm10-13V5m-3 0h6M10 22v5m12-5v5",
 "calendar": "M5 8h22v18H5zM10 4v8m12-8v8M5 15h22m-16 5h2m6 0h2",
 "hybrid": "M4 7h24v15H4zM11 27h10m-5-5v5M13 11l7 4-7 4z",
 "team": "M12 10a4 4 0 1 0-8 0 4 4 0 0 0 8 0zm16 0a4 4 0 1 0-8 0 4 4 0 0 0 8 0zM2 26v-3a6 6 0 0 1 12 0v3zm16 0v-3a6 6 0 0 1 12 0v3z",
}
PALETTES = {
 "office": ("#173757", "#076a80"), "factory": ("#183250", "#8b4837"),
 "build": ("#312e50", "#945126"), "water": ("#0b3056", "#086984"),
 "care": ("#31415e", "#8a4f58"), "clinical": ("#183959", "#16665e"),
 "hospitality": ("#313348", "#805628"),
}
PROGRAMS = {
 "clinical": ("Clinical life support","clinical",("aha", "arc")),
 "care": ("CPR, AED & pediatric / general first aid","care",("aha", "hsi", "arc")),
 "water": ("Maritime and workplace first aid","water",("hsi", "aha", "arc")),
 "default": ("Workplace First Aid, CPR & AED","care",("hsi", "aha", "arc")),
}
DELIVERY_NOTES = {
 "childcare": "For licensed NC child care centers, we verify the exact approved course, any delivery restrictions and instructor evaluation before quoting a blended option. A self-paced online-only course is not a substitute.",
 "dental-offices": "For NC dental licensure, an instructor must be physically present during the manikin test. We check the exact course and skills format before quoting.",
 "logging": "For logging crews covered by OSHA’s rule, we verify the proposed course against Appendix B before quoting a format. A generic online course is not a substitute.",
}


def load():
    return json.loads((ROOT / "data/industry_landers.json").read_text(encoding="utf-8"))


def sitemap_paths():
    return [DIRECTORY] + [f"/group-training/{r[0]}/" for r in load()["industries"]]


def icon(key, css="feature-icon"):
    return f'<svg class="{css}" viewBox="0 0 32 32" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="{ICONS[key]}"/></svg>'


def delivery_block(slug):
    in_person = ("<li><strong>Fully in person</strong> is our usual recommendation. Your team can ask questions, "
                 "practice together and work through scenarios as a group. It’s often the more economical choice.</li>")
    if slug == "merchant-mariners":
        return (icon("calendar") + "<h2>Course type</h2><ul>" + in_person +
                "<li><strong>Blended:</strong> Don’t assume a general blended or online course counts "
                "toward the Coast Guard requirement.</li></ul>"
                "<p>We’ll quote the exact instructor-led HSINST-203 course if it matches your "
                "Merchant Mariner Credential checklist and the approved delivery conditions.</p>")
    blended = ("<li><strong>Blended, where allowed:</strong> Employees complete the online coursework "
               "on their own schedule, then rotate through the required instructor-led, hands-on skills "
               "in pairs or groups of four.</li>")
    note = f"<p>{e(DELIVERY_NOTES[slug])}</p>" if slug in DELIVERY_NOTES else ""
    quote = ("<p>We’re happy to quote either format or both so you can compare, as long as the program, "
             "employer and applicable authority allow them.</p>")
    return icon("calendar") + icon("hybrid") + "<h2>Course type</h2><ul>" + in_person + blended + "</ul>" + note + quote


def sector_art(slug, key):
    a, b = PALETTES[key]
    n = sum(ord(c) for c in slug)
    lines = "".join(f'<path d="M{x} 360 {x+260} 0"/>' for x in range(-330+(n%30), 690, 29))
    circles = "".join(f'<circle cx="{410 + (i%4)*36}" cy="{50 + (i//4)*39}" r="{2+i%3}"/>' for i in range(16))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 360"><defs><linearGradient id="sea"><stop stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs><rect width="640" height="360" fill="url(#sea)"/><g stroke="#c8edf1" stroke-opacity=".18">{lines}</g><g fill="#c8edf1" fill-opacity=".48">{circles}</g><circle cx="346" cy="187" r="115" fill="#0c2137" fill-opacity=".46"/><circle cx="346" cy="187" r="102" fill="none" stroke="#c8edf1" stroke-opacity=".4"/><path transform="translate(274 113) scale(4.6)" d="{ICONS[key]}" stroke="#e9f9f8" fill="none" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M0 308h115l14-11 13 18 15-33 18 26h465" fill="none" stroke="#a8e6d8" stroke-width="2" stroke-opacity=".68"/></svg>\n'


def shell(title, desc, path, main, structured, industry=""):
    val = e
    layer = json.dumps({"event":"industry_lander_view","industry":industry,"source_page_type":"industry_lander"}, ensure_ascii=True)
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{val(title)} | 910CPR</title>
<meta name="description" content="{val(desc)}"><meta name="robots" content="index,follow">
<link rel="canonical" href="{BASE}{path}">
<meta name="910cpr-page-id" content="{val(industry or "industry-directory")}">
<meta property="og:title" content="{val(title)} | 910CPR"><meta property="og:description" content="{val(desc)}"><meta property="og:url" content="{BASE}{path}">
<link rel="stylesheet" href="/assets/industry-landers/industry.css?v=6">
<script type="application/ld+json">{json.dumps(structured,ensure_ascii=True).replace("<", chr(92)+"u003c")}</script>
{GTM_HEAD_SNIPPET}
{ATTRIBUTION_SCRIPT_SNIPPET}
{"<script>window.dataLayer=window.dataLayer||[];window.dataLayer.push("+layer+");</script>" if industry else ""}
</head><body>
{GTM_NOSCRIPT_SNIPPET}
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap top-inner"><a class="wordmark" href="/">910<span>CPR</span></a><nav aria-label="Main navigation"><a href="/group-training.html">Group training</a><a href="{DIRECTORY}">Industries</a><a href="tel:+19103955193">910-395-5193</a></nav></div></header>
<main id="main" class="wrap">{main}</main>
<footer class="wrap footer"><strong>910CPR LLC</strong> · Based in Wilmington, North Carolina · <a href="{REVIEW}">Read public 910CPR reviews</a> · <a href="mailto:info@910cpr.com">Email 910CPR</a></footer>
</body></html>
'''


def crumbs(name, path):
    links = [("910CPR", "/"), ("Group training", "/group-training.html")]
    if path != DIRECTORY:
        links.append(("Industries", DIRECTORY))
    links.append((name, path))
    schema = {"@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":i,"name":label,"item":BASE+url}
        for i, (label, url) in enumerate(links,1)
    ]}
    body = '<nav class="crumbs" aria-label="Breadcrumb"><ol>' + ''.join(
        f'<li><a href="{url}">{e(label)}</a></li>' for label,url in links[:-1]
    ) + f'<li aria-current="page">{e(name)}</li></ol></nav>'
    return body,schema


def photo_markup(slug):
    asset = f"/assets/industry-landers/{slug}"
    source = f'<source srcset="{asset}.webp" type="image/webp">' if (ASSETS / f"{slug}.webp").exists() else ""
    return f'<picture class="scene" aria-hidden="true">{source}<img src="{asset}.svg" alt="" width="640" height="360" fetchpriority="high"></picture>'


def issuer_options(slug, art):
    if slug == "merchant-mariners":
        return {
            "aha": "Need an AHA card? Contact us with your Coast Guard checklist. We do not present a separate AHA option here for this endorsement.",
            "hsi": "Ask about instructor-led HSINST-203, the exact HSI First Aid/CPR/AED course listed for specified National Maritime Center first-aid and CPR requirements. It does not satisfy STCW endorsements.",
            "arc": "Need a Red Cross card? Send us your Coast Guard checklist. We do not present a separate Red Cross option here for this endorsement.",
        }
    if slug == "childcare":
        return {
            "aha": "Heartsaver Pediatric First Aid CPR AED. Confirm the exact issuer, ages and delivery format your center is allowed to use.",
            "hsi": "NC DCDEE lists specific HSI pediatric courses. Ask us to confirm that the exact approved program, delivery and age coverage are available before you choose.",
            "arc": "Adult and Pediatric First Aid/CPR/AED classroom. Check your center’s accepted course title, age coverage and delivery rules before booking.",
        }
    if slug == "dental-offices":
        return {
            "aha": "BLS Provider with a physically present instructor for manikin testing. Confirm the course against your practice and licensing requirements.",
            "hsi": "BLS Challenge or BLS with Adult First Aid are options for other roles. Ask before selecting HSI for NC dental licensure; we do not assume the course or format meets that rule.",
            "arc": "BLS classroom. Confirm all required topics and that an instructor is physically present during manikin testing for NC dental licensure.",
        }
    if art == "clinical":
        return {
            "aha": "BLS Provider initial, renewal or HeartCode skills when accepted. Ask about ACLS or PALS initial or renewal for roles that require advanced care.",
            "hsi": "BLS Challenge or blended BLS with Adult First Aid, only if your employer accepts the exact program and format.",
            "arc": "BLS classroom if accepted by your employer. Ask if you need a different course; ARC BLS does not replace ACLS or PALS.",
        }
    if slug in {"schools","aquatics","churches","fitness"}:
        return {
            "aha": "Heartsaver First Aid CPR AED or Heartsaver Pediatric First Aid CPR AED. Tell us the ages and job roles your policy covers.",
            "hsi": "Ask about First Aid/CPR/AED. If your policy requires a pediatric or role-specific HSI course, we’ll first confirm the exact option and acceptance.",
            "arc": "Adult and Pediatric First Aid/CPR/AED classroom. Choose the course your organization accepts; lifeguard and other job credentials are separate.",
        }
    hsi = "First Aid/CPR/AED in person. Tell us the exact program your employer accepts so we can match it."
    if slug=="logging":
        hsi="Ask about hands-on First Aid/CPR/AED. For covered logging crews, first verify the course and testing against OSHA’s Appendix B."
    return {
        "aha": "Heartsaver First Aid CPR AED or Heartsaver CPR AED. Choose First Aid as well if your role requires it.",
        "hsi": hsi,
        "arc": "Adult and Pediatric First Aid/CPR/AED classroom, or Adult CPR/AED online plus skills when a first-aid card isn’t required and your employer accepts blended.",
    }


def issuer_picker(slug, art):
    options = issuer_options(slug, art)
    items=[]
    for key, short in (("aha","AHA"),("hsi","HSI"),("arc","ARC")):
        title, asset=BADGES[key]
        option=e(options[key])
        items.append(f'<li class="brand-{key}"><details><summary aria-label="{e(title)} course options"><img src="{asset}" alt="" width="140" height="55" loading="lazy"><span>{short}</span></summary><p>{option}</p></details><p class="issuer-hover" aria-hidden="true">{option}</p></li>')
    return '<ul class="brand-picker">'+"".join(items)+'</ul>'


def authority_evidence(entry, sources):
    kind = e(entry["kind"])
    reference = e(entry["citation"])
    excerpt = entry["excerpt"]
    if len(excerpt.split()) > 25:
        raise ValueError("Authority excerpts must be short")
    details = (f'<p class="authority-from"><strong>{kind}:</strong> {reference}</p>'
               + (f'<blockquote class="authority-excerpt"><span>Short official excerpt</span><p>“{e(excerpt)}”</p></blockquote>' if excerpt
                  else '<p class="fine authority-paraphrase">Plain-English summary above.</p>'))
    links = "".join(
        f'<li><a href="{e(sources[key][1])}" target="_blank" rel="noopener noreferrer">{e(sources[key][0])}</a></li>'
        for key in entry["sources"]
    )
    return details, f'<div class="authority-references"><h3>References <span>(open in a new tab)</span></h3><ul>{links}</ul></div>'


def industry(row, sources, evidence):
    slug, name, title, kicker, who, fit, rule, prepare, question, answer, team, source_keys, art = row
    path = f"/group-training/{slug}/"
    crumb, crumb_schema = crumbs(name, path)
    schema = {"@context":"https://schema.org","@graph":[crumb_schema,{
        "@type":"Service","name":title,"url":BASE+path,"description":who,"serviceType":title,
        "provider":{"@type":"Organization","name":"910CPR LLC","url":BASE,"telephone":"+1-910-395-5193"},
        "areaServed":{"@type":"City","name":"Wilmington","containedInPlace":{"@type":"State","name":"North Carolina"}},
    }]}
    family,family_icon,body_ids = PROGRAMS.get(art,PROGRAMS["default"])
    if slug == "merchant-mariners":
        family,family_icon,body_ids = "HSI First Aid / CPR / AED (HSINST-203)","water",("hsi",)
    authority_details, authority_links = authority_evidence(evidence[slug], sources)
    badges = issuer_picker(slug, art)
    specialty = '<a href="/uscg-hsi/">Read about the HSINST-203 course</a>' if slug == "merchant-mariners" else ""
    main = f'''{crumb}
<section class="hero"><div class="hero-body"><p class="kicker">{e(kicker)}</p><h1>{e(title)}</h1><p class="lead">{e(who)}</p><div class="actions hero-actions"><a class="btn primary" href="{CTA}">Request group training</a><a class="btn secondary" href="mailto:info@910cpr.com">Email 910CPR</a><a class="btn secondary" href="tel:+19103955193">Call 910CPR</a></div><small>On the request form, replace the preset Program with the course your group needs, or write “help me choose.” We confirm the course, instructor and date before booking.</small></div>{photo_markup(slug)}</section>
<section class="quick" aria-label="Course information">
<div>{icon(family_icon)}<h2>Course family</h2><p>{e(family)}</p></div>
<div>{delivery_block(slug)}</div>
<div>{icon("team")}<h2>Who to train</h2><p>{e(team)}</p></div>
</section>
<div class="columns">
<section class="card"><p class="kicker label">Training fit</p><h2>Which class should we consider?</h2><p>{e(fit)}</p>{specialty}<h3>Plan a session</h3><p>{e(prepare)}</p><p>Tell us how many people need training and where you’d like to meet. We’ll help find a format and date that work for your team.</p></section>
<section class="card authority"><div class="authority-heading"><div><p class="kicker label">Primary sources</p><h2>What do the authorities say?</h2></div><img class="authority-photo" src="/assets/industry-landers/authority-glasses.webp" alt="" width="816" height="544" loading="lazy" decoding="async"></div><p>{e(rule)}</p>{authority_details}<p class="fine">If you have a written requirement, send it with your request. We’ll check the course and format with you before booking.</p>{authority_links}</section>
</div>
<section class="card brands"><p class="kicker label">Certifying bodies</p><h2>Which certification does your team need?</h2><p>910CPR offers qualifying training through the American Heart Association, Health &amp; Safety Institute, and American Red Cross. After you meet the course requirements, your card comes from the program you completed. If your organization names a specific issuer or program, tell us and we’ll help match it before you book.</p><p class="issuer-hint">Choose a logo to see relevant course options and limits.</p>{badges}</section>
<section class="card"><p class="kicker label">Common question</p><h2>{e(question)}</h2><p>{e(answer)}</p><div class="actions"><a class="btn" href="{CTA}">Share your group’s requirements</a><a href="{DIRECTORY}">Explore other industries</a></div></section>'''
    return shell(title,who,path,main,schema,slug)


def directory(rows):
    crumb,schema=crumbs("Industries",DIRECTORY)
    lines=''.join(f'<li><a href="/group-training/{r[0]}/">{icon(r[-1])}<span><strong>{e(r[1])}</strong><small>{e(r[2])}</small></span></a></li>' for r in rows)
    main=f'''{crumb}<section class="hero directory"><div class="hero-body"><p class="kicker">910CPR LLC · GROUP TRAINING</p><h1>CPR and First Aid by Industry</h1><p class="lead">Choose your work setting to compare course families, hands-on formats and the right authority to check.</p><a class="btn" href="{CTA}">Request group training</a></div></section>
<section class="card"><h2>Find your industry</h2><ul class="industry-grid">{lines}</ul></section>'''
    return shell("CPR and First Aid by Industry","Find onsite CPR, AED, First Aid and BLS training by industry in Wilmington and Coastal North Carolina.",DIRECTORY,main,{"@context":"https://schema.org",**schema})


def output_set():
    config=load()
    for row in config["industries"]:
        slug=row[0]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",slug):
            raise ValueError(f"Invalid public industry slug: {slug}")
        yield DOCS / "group-training" / slug / "index.html",industry(row,config["sources"],config["authority_evidence"])
        yield ASSETS / (slug+".svg"),sector_art(slug,row[-1])
    yield DOCS / DIRECTORY.strip("/") / "index.html",directory(config["industries"])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true",help="check outputs are current without writing")
    opts=parser.parse_args()
    diff=[]
    for path, body in output_set():
        if opts.check:
            if not path.is_file() or path.read_text(encoding="utf-8")!=body: diff.append(path)
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(body,encoding="utf-8",newline="\n")
    if diff:
        raise SystemExit("Missing or stale output: "+", ".join(str(p.relative_to(ROOT)) for p in diff))
    print(f"{len(sitemap_paths())} industry URLs")

if __name__ == "__main__":
    main()
