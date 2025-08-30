import csv, os, pathlib, re
OUT_DIR="landers/job"; APEX="https://www.910cpr.com"; ENROLL="https://coastalcprtraining.enrollware.com/schedule"
CT={"bls":"CT_BLS_NUMBER","acls":"CT_ACLS_NUMBER","pals":"CT_PALS_NUMBER","afa":"CT_AFA_NUMBER"}
TPL="""<!doctype html><html lang="en"><head><meta charset="utf-8" />
<title>CPR/BLS for {T} | 910CPR</title>
<meta name="description" content="Training for {TP}: HSI/AHA/ARC acceptance and fast enrollment." />
<link rel="canonical" href="{APEX}/job/{slug}" /><meta name="x-910-courses" content="{keys}"></head>
<body><header><h1>CPR/BLS for {TP}</h1>
<p>HSI, AHA, and American Red Cross programs widely accepted. If policy names AHA/ARC, choose those sessions—we offer them.</p>
<p>{CTA}</p></header>
<section><h2>Which class?</h2><ul>
<li><a href="{APEX}/courses/bls">BLS Provider</a></li>
<li><a href="{APEX}/courses/acls">ACLS</a></li>
<li><a href="{APEX}/courses/bls">CPR/AED &amp; First Aid</a></li>
</ul></section>
<section><h2>Ready to schedule?</h2><p>{CTA}</p>
<p>Questions? <a href="tel:+19103955193">910-395-5193</a> · <a href="mailto:info@910cpr.com">info@910cpr.com</a></p>
</section></body></html>"""
def plural(s): return s if re.search(r's$', s, re.I) else s+"s"
def link(k,l): 
  ct=CT.get(k); 
  return f'<a class="btn" href="{ENROLL}#ct[{ct}]">See {l} classes</a>' if ct and "CT_" not in ct else f'<a class="btn" href="{ENROLL}">See {l} classes</a>'
def ctas(keys):
  parts=[]; 
  if "bls" in keys: parts.append(link("bls","BLS"))
  if "acls" in keys: parts.append(link("acls","ACLS"))
  if "pals" in keys: parts.append(link("pals","PALS"))
  if "afa"  in keys: parts.append(link("afa","First Aid | CPR AED"))
  parts.append(f'<a class="ghost" href="{ENROLL}">See all classes</a>')
  return " &nbsp;|&nbsp; ".join(parts)
def main(csv_path="ooh_jobs.csv"):
  pathlib.Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
  if not pathlib.Path(csv_path).exists(): return
  with open(csv_path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
      T=row["title"].strip(); slug=row["slug"].strip().lower()
      keys=[k.strip().lower() for k in row["course_keys"].split(",") if k.strip()]
      html=TPL.format(T=T,TP=plural(T),APEX=APEX,slug=slug,keys=",".join(keys),CTA=ctas(keys))
      out=os.path.join(OUT_DIR, f"{slug}.html"); open(out,"w",encoding="utf-8").write(html); print("wrote",out)
if __name__=="__main__": main()
