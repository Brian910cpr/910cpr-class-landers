import csv, os, re, sys
from pathlib import Path
from html import escape as esc

APEX = "https://www.910cpr.com"
OUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "landers" / "job"
CSV_PATH = "class-landers-summary.csv"
SEE_ALL = "https://www.hovn.app/910cpr/courses"
CT = {
    # "BLS": "/courses/bls",
    # "ACLS": "/courses/acls",
    # "PALS": "/courses/pals",
    # "FA": "/courses/first-aid",
}

TPL = """<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <title>{title} - CPR Requirements</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <meta name='description' content='{desc}'>
  <link rel='canonical' href='{canonical}'>
  <style>
    body{{font-family:system-ui;margin:24px;line-height:1.6}}
    nav a{{margin-right:12px;text-decoration:none;color:inherit}}
    .chip a{{display:inline-block;margin:6px 8px 0 0;padding:8px 12px;border:1px solid #ddd;border-radius:999px;text-decoration:none}}
    .muted{{color:#666}}
  </style>
</head>
<body>
  <nav><a href='{apex}/'>Home</a> <a href='{apex}/job/'>Jobs</a> <a href='{apex}/courses/'>Courses</a></nav>
  <h1>{title}</h1>
  <p class='muted'>CPR/First Aid requirements and common certifications for <strong>{occupation}</strong>.</p>
  <h2>Common certifications</h2>
  <ul>
    {cert_list}
  </ul>
  <div class='chip'>
    <a href='{cta_href}'>See upcoming classes</a>
    <a href='{apex}/policies.html' class='muted'>Policies</a>
  </div>
</body>
</html>"""

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")

def row_to_html(row: dict) -> str:
    occupation = row.get("occupation","Job").strip()
    slug = slugify(occupation)
    canonical = f"{APEX}/landers/job/{slug}.html"
    certs = [x.strip() for x in row.get("certs","").split("|") if x.strip()]
    ct = row.get("ct","").strip().upper()
    cta_href = CT.get(ct, SEE_ALL)

    cert_list = "\n".join([f"<li>{esc(c)}</li>" for c in certs]) or "<li>BLS Provider (AHA)</li>"
    title = f"{esc(occupation)} - CPR/First Aid Requirements"
    desc = f"CPR and First Aid certification guidance for {esc(occupation)} in southeastern NC. See BLS, ACLS, PALS, and First Aid renewal options."
    return TPL.format(
        title=title, desc=desc, apex=APEX, canonical=canonical,
        occupation=esc(occupation), cert_list=cert_list, cta_href=cta_href
    ), slug

def main(csv_path: str = CSV_PATH):
    src = Path(csv_path)
    if not src.exists():
        print(f"[gen_job_landers] CSV not found: {src}")
        sys.exit(0)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    with src.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            html, slug = row_to_html(row)
            out = OUT_DIR / f"{slug}.html"
            out.write_text(html, encoding="utf-8")
            n += 1
    print(f"[gen_job_landers] wrote {n} pages to {OUT_DIR}")

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else CSV_PATH
    main(arg)
