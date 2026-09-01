#!/usr/bin/env python3
"""Classify unresolved Hx locations and model archive-only authority effects."""

from __future__ import annotations

import argparse, copy, hashlib, html, json, re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from hx_builder import HxBuilder


SOURCE_ONLY = {
    "", "Residence", "Huff Family - Wilmington", "Roos Residence", "4902 Merlot Court; Wilmington, NC",
    "Residence - 6239 Mirage Way, Wilm", "443 Holly View Lane Loris, SC 29569", "___TBD___", "Tassi Classes",
    "Contail Road",
}
AMBIGUOUS = {
    "CT - Colchester", "Camp Lejeune", "Balfour Beatty US - Office", "910CPR's Office",
    "19 Oak Ridge Dr, Colchester, CT", "Geosyntec Consultants of NC P.C.",
}


def clean_label(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    value = re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", "[redacted-email]", value, flags=re.I)
    return re.sub(r"\s+", " ", value).strip()


def family(value: str) -> str:
    v=clean_label(value).lower()
    for needle,name in (("phlebot","Phlebotomy"),("acls","ACLS"),("pals","PALS"),("bls","BLS"),
                        ("heartsaver","Heartsaver"),("first aid","First Aid / CPR AED"),("hsi","HSI"),
                        ("red cross","American Red Cross"),("family","Family & Friends")):
        if needle in v: return name
    return "Other / legacy"


def metadata(label: str) -> dict:
    clean=clean_label(label)
    streets=re.findall(r"\b\d{1,5}\s+[A-Za-z0-9.' -]+(?:Rd|Road|Dr|Drive|Ave|Avenue|St|Street|Blvd|Boulevard|Way|Court|Pkwy|Parkway|Loop)\b",clean,re.I)
    states=re.findall(r"\b(?:NC|SC|CT)\s+\d{5}\b",clean)
    cities=re.findall(r"\b(?:Wilmington|Jacksonville|Colchester|Holly Ridge|Loris|Raleigh|Fayetteville|Southport|Leland|Supply|Myrtle Beach|Bolivia|Hampstead|Surf City|Bladenboro)\b",clean,re.I)
    return {"clean_label":clean,"street_fragments":sorted(set(streets)),"city_fragments":sorted(set(cities)),"state_postal_fragments":sorted(set(states)),
            "source_metadata_scope":"Enrollware location label only; no separate structured address fields were supplied"}


def canonical_name(label: str) -> str:
    if label.startswith("NC - Holly Ridge: 325 Sound Rd, Unit 204"):
        return "910CPR Office - Parkhill Village, Holly Ridge (historical)"
    if label == "910CPR Office @ Hinton Ave, Wlmington":
        return "910CPR Office - Hinton Avenue, Wilmington (historical)"
    name=clean_label(label).replace("[redacted-email]","").strip(" -")
    name=name.split("Visit our hosts' social:",1)[0].strip()
    if name.startswith("Williams Love Grove Baptist Church"):
        return "Williams Love Grove Baptist Church"
    return name[:240]


def source_flags(label: str, data_type: str) -> list[str]:
    flags=[]
    if not label: flags.append("missing")
    if '<' in label and '>' in label: flags.append("html_markup")
    if label in SOURCE_ONLY: flags.append("source_only")
    if any(x in label.lower() for x in ('residence','family -','___tbd___')): flags.append("one_time_or_private")
    if re.match(r"^\d+\s",clean_label(label)): flags.append("address_only")
    if data_type == 'ambiguous': flags.append("insufficient_specificity")
    if not flags: flags.append("named_venue")
    return flags


def classification(label: str) -> tuple[str,str,bool,str]:
    if label in SOURCE_ONLY:
        return "SOURCE-ONLY / DO NOT CANONICALIZE", "missing, private/one-time, placeholder, or non-location free text", False, "free_text_or_one_time"
    if label in AMBIGUOUS:
        return "AMBIGUOUS / REVIEW REQUIRED", "insufficient specificity or possible collision with a different canonical place", False, "ambiguous"
    if label.startswith("NC - Holly Ridge: 325 Sound Rd, Unit 204"):
        return "CANONICAL HISTORICAL LOCATION CANDIDATE", "historical 910CPR office is explicit; Unit 204 conflicts with current Spectrum Suite 305 and must remain distinct", True, "historic_named_site"
    return "CANONICAL HISTORICAL LOCATION CANDIDATE", "named organization, facility, branch, or venue usable across historical sessions", True, "reusable_physical_location"


class RelaxedBuilder(HxBuilder):
    allow_unknown_instructor=False; allow_unknown_duration=False
    def canonicalize_session(self, record):
        super().canonicalize_session(record)
        s=record["session"]
        required=[s.get("course_id"),s.get("location_id"),s.get("start_at")]
        if not self.allow_unknown_instructor: required.append(s.get("lead_instructor_id"))
        if not self.allow_unknown_duration: required.append(s.get("end_at"))
        return all(v not in (None,"") for v in required)


def run_variant(payload,reference,instructor,duration):
    cls=type("PolicyBuilder",(RelaxedBuilder,),{"allow_unknown_instructor":instructor,"allow_unknown_duration":duration})
    return cls(copy.deepcopy(payload),copy.deepcopy(reference)).process()["summary"]["sessions_created"]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--payload',type=Path,required=True);ap.add_argument('--run',type=Path,required=True);ap.add_argument('--reference',type=Path,required=True)
    ap.add_argument('--json-output',type=Path,required=True);ap.add_argument('--markdown-output',type=Path,required=True);ap.add_argument('--simulation-reference',type=Path,required=True)
    a=ap.parse_args();payload=json.loads(a.payload.read_text(encoding='utf-8-sig'));run=json.loads(a.run.read_text());ref=json.loads(a.reference.read_text(encoding='utf-8-sig'))
    records={r['source_record_id']:r for r in payload['records']}; unresolved=[x for x in run['unresolved_or_ambiguous'] if x['kind']=='session_location']
    grouped=defaultdict(list)
    for item in unresolved: grouped[records[item['source_record_id']]['session'].get('location_name') or ''].append(records[item['source_record_id']])
    inventory=[]; proposed=[]; sim=copy.deepcopy(ref)
    for label,rows in sorted(grouped.items(),key=lambda x:(-len(x[1]),x[0])):
        category,reason,reusable,data_type=classification(label); dates=sorted(r['session'].get('start_at') for r in rows if r['session'].get('start_at'))
        meta=metadata(label); digest=hashlib.sha256(label.encode()).hexdigest(); exact=False
        item={"source_label":clean_label(label) or "[missing]","source_label_sha256":digest,"occurrence_count":len(rows),
              "course_families":sorted({family(r['session'].get('course_name','')) for r in rows}),
              "date_range":{"first":dates[0] if dates else None,"last":dates[-1] if dates else None},"source_metadata":meta,
              "existing_canonical_exact_evidence":exact,"real_reusable_physical_location":reusable,"data_character":data_type,
              "source_flags":source_flags(label,data_type),"classification":category,"classification_reason":reason}
        if category in ("CANONICAL HISTORICAL LOCATION CANDIDATE","SAFE ALIAS TO EXISTING LOCATION"):
            pid=f"proposed-historical-location:{digest[:24]}"; name=canonical_name(label)
            record={"id":pid,"location_key":f"historical-{digest[:24]}","name":name,"public":False,"historical_only":True,"scheduling_status":"archive_only",
                    "address_line1":meta['street_fragments'][0] if meta['street_fragments'] else None,"city":meta['city_fragments'][0] if meta['city_fragments'] else None,
                    "state_postal":meta['state_postal_fragments'][0] if meta['state_postal_fragments'] else None,
                    "provenance":{"source":"enrollware_student_report","source_label_sha256":digest,"original_label_retained_in_private_source":True}}
            item['proposed_canonical_record']=record; proposed.append(record);sim.setdefault('locations',[]).append(record)
            sim.setdefault('location_aliases',[]).append({"source":"enrollware_student_report","source_label":label,"location_id":pid,"active":True,"review_status":"reviewed"})
        inventory.append(item)
    a.simulation_reference.write_text(json.dumps(sim,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    strict=HxBuilder(copy.deepcopy(payload),copy.deepcopy(sim)).process(); policies={
      "strict_current":strict['summary']['sessions_created'],
      "allow_unknown_instructor":run_variant(payload,sim,True,False),
      "allow_unknown_duration":run_variant(payload,sim,False,True),
      "allow_both_unknown":run_variant(payload,sim,True,True)}
    cats=Counter();catrows=Counter()
    for x in inventory: cats[x['classification']]+=1;catrows[x['classification']]+=x['occurrence_count']
    report={"report":"Hx historical location authority analysis","mode":"review_only","production_changed":False,"historical_imported":False,
      "unresolved_before":{"rows":len(unresolved),"distinct":len(inventory)},"classification_distinct":dict(sorted(cats.items())),"classification_rows":dict(sorted(catrows.items())),
      "inventory":inventory,"proposed_historical_locations":len(proposed),"safe_aliases_to_existing":cats['SAFE ALIAS TO EXISTING LOCATION'],
      "session_effect":{"fully_canonicalized_before":run['canonicalization_summary']['sessions_ready'],"fully_canonicalized_after_safe_locations":strict['canonicalization_summary']['sessions_ready'],
                        "additional_fully_canonicalized":strict['canonicalization_summary']['sessions_ready']-run['canonicalization_summary']['sessions_ready'],
                        "session_records_created_under_policy":policies},
      "historical_session_policy_recommendation":{"instructor":"allow unknown when source never supplied it; retain an explicit missing-instructor evidence assertion and review state",
        "duration":"allow unknown when source never supplied a defensible duration/end; never synthesize end_at",
        "minimum_authority":"course_id, location_id or explicit location-unknown state, timezone-aware start_at, durable source session ID, provenance and review status",
        "operational_boundary":"unknown instructor/duration historical sessions must remain archive-only and ineligible for public scheduling, instructor workload, payroll, capacity, or duration analytics",
        "current_schema_constraint":"public.class_sessions currently requires lead_instructor_id, location_id, and end_at; true unknown values cannot be persisted directly under the current contract",
        "implementation_review_needed":{"instructor":"either use the canonical Unknown Historical Instructor only with explicit missing-evidence/review state and archive-only enforcement, or review nullable lead_instructor_id for historical sessions",
          "duration":"review nullable end_at for archive-only historical sessions or retain timing as non-authoritative evidence until resolved; never insert a dummy end time",
          "location":"the current locations table has public but no historical_only/scheduling_status columns; approve an equivalent enforceable archive-only guard before creating any candidate"}},
      "nhcso":"2026 evidence is absent from this export and was not manufactured","recommendation":"READY FOR HISTORICAL LOCATION AUTHORITY REVIEW"}
    a.json_output.parent.mkdir(parents=True,exist_ok=True);a.json_output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    lines=["# Hx Historical Location Authority Review","","No production changes, historical import, or application deployment occurred.","","## Classification summary","","| Classification | Distinct labels | Rows |","| --- | ---: | ---: |"]
    for key in ("CANONICAL HISTORICAL LOCATION CANDIDATE","SAFE ALIAS TO EXISTING LOCATION","SOURCE-ONLY / DO NOT CANONICALIZE","AMBIGUOUS / REVIEW REQUIRED"):
        lines.append(f"| {key} | {cats[key]:,} | {catrows[key]:,} |")
    lines += ["","## Session effect","",f"- Fully canonicalized before: **{report['session_effect']['fully_canonicalized_before']:,}**",f"- After all safe archive-only candidates: **{report['session_effect']['fully_canonicalized_after_safe_locations']:,}**",f"- Increase: **{report['session_effect']['additional_fully_canonicalized']:,}**","", "## Historical completeness policy","","An otherwise supported historical session should be allowed to exist with instructor and/or duration explicitly unknown. Unknown is evidence state, not a guessed value. Such sessions must remain archive-only and excluded from operational scheduling, payroll, capacity, and duration projections.","","The production contract currently makes `class_sessions.lead_instructor_id`, `location_id`, and `end_at` NOT NULL. Therefore this recommendation is not directly importable yet: instructor-unknown needs either the canonical historical placeholder plus explicit missing-evidence state or a reviewed nullable-field change; duration-unknown needs a reviewed nullable `end_at`/historical evidence path and must never use a fabricated end time. Likewise, `locations` has `public` but not the proposed `historical_only`/`scheduling_status` guards, so an enforceable archive-only boundary requires schema review before candidate creation.","","```json",json.dumps(policies,indent=2,sort_keys=True),"```","","## Frequency-ranked inventory","","| Source label | Count | Course families | Date range | Source metadata | Existing exact map | Reusable | Character | Classification |","| --- | ---: | --- | --- | --- | --- | --- | --- | --- |"]
    esc=lambda v:str(v).replace('|','\\|').replace('\n',' ')
    for item in inventory:
        meta=item['source_metadata']; metadata_text=', '.join(meta['street_fragments']+meta['city_fragments']+meta['state_postal_fragments']) or 'label only'
        dates=f"{item['date_range']['first'] or 'unknown'} — {item['date_range']['last'] or 'unknown'}"
        lines.append(f"| {esc(item['source_label'])} | {item['occurrence_count']} | {esc(', '.join(item['course_families']))} | {esc(dates)} | {esc(metadata_text)} | {'yes' if item['existing_canonical_exact_evidence'] else 'no'} | {'yes' if item['real_reusable_physical_location'] else 'no'} | {esc(', '.join(item['source_flags']))} | {item['classification']} |")
    lines += ["","The companion JSON includes provenance hashes and every proposed minimum archive-only canonical record.","","NHCSO 2026 remains outside the supplied source period and was not reconstructed."]
    a.markdown_output.write_text('\n'.join(lines)+'\n',encoding='utf-8');return 0

if __name__=='__main__':raise SystemExit(main())
