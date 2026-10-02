"""Build one read-only dashboard policy asset from authoritative local config."""
import json
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"docs/admin/open-shift-policy.js"
def build():
    paths=["data/config/instructors.json","data/config/calendar_sources.json","data/config/location_resource_map.json","data/config/travel_time_rules.json","data/inventory/appointment_containers.json","data/inventory/course_consumption_rules.json","data/config/course_catalog.json","data/config/block_schedule_pages.json","data/config/public_offer_policy.json","data/config/calendar_duration_policy.json"]
    data={p:json.loads((ROOT/p).read_text(encoding="utf-8")) for p in paths}
    rules={r["course_id"]:{**data[paths[5]].get("defaults",{}),**r} for r in data[paths[5]]["rules"]}
    catalog={r["course_id"]:r for r in data[paths[6]]["courses"]}
    occupancy={cid:max(r["duration_minutes"]+int(r.get("setup_buffer_minutes") or 0)+int(r.get("cleanup_buffer_minutes") or 0),r.get("minimum_reservation_block_minutes") or 0) for cid,r in rules.items()}
    authority=data[paths[9]]
    kinds={}
    for page in data[paths[7]]["pages"].values():
        for option in page.get("course_options",[]):
            cid=option["course_id"]
            if option.get("delivery_mode")=="in-person":kinds[cid]="full"
            elif option.get("delivery_mode") in {"skills-session","blended"} and page["family"] not in authority["excluded_short_skills_families"]:kinds[cid]="skills"
    course_times={cid:{"kind":kind,"instructionMinutes":authority["in_person_instruction_minutes"] if kind=="full" else authority["skills_instruction_minutes"],"cleanupMinutes":authority["in_person_cleanup_minutes"] if kind=="full" else authority["skills_cleanup_minutes"],"authority":authority["authority"]} for cid,kind in kinds.items()}
    names={}
    for cid,course in catalog.items():
        for key in ["official_title","short_title"]:
            if course.get(key) and cid in course_times:names[course[key].strip().lower()]=cid
    selected={}
    full={}
    for page in ["bls","heartsaver","arc","hsi","acls","pals"]:
        for option in data[paths[7]]["pages"][page]["course_options"]:
            cid=option["course_id"]
            if cid not in rules:continue
            if option.get("delivery_mode")=="in-person":
                full[cid]={"id":cid,"name":option["display_label"],"family":catalog[cid]["family"],"kind":"full","instructionMinutes":course_times[cid]["instructionMinutes"],"cleanupMinutes":course_times[cid]["cleanupMinutes"],"minutes":occupancy[cid],"durationConflict":catalog[cid]["duration_minutes"]!=rules[cid]["duration_minutes"],"catalogMinutes":catalog[cid]["duration_minutes"],"ruleMinutes":rules[cid]["duration_minutes"]}
                continue
            if page not in {"bls","heartsaver","arc","hsi"} or option.get("delivery_mode") not in {"skills-session","blended"}:continue
            selected[cid]={"id":cid,"name":option["display_label"],"family":catalog[cid]["family"],"instructionMinutes":course_times[cid]["instructionMinutes"],"cleanupMinutes":course_times[cid]["cleanupMinutes"],"minutes":occupancy[cid],"durationConflict":catalog[cid]["duration_minutes"]!=rules[cid]["duration_minutes"],"catalogMinutes":catalog[cid]["duration_minutes"],"ruleMinutes":rules[cid]["duration_minutes"]}
    instructors=data[paths[0]]["instructors"]
    for p in instructors:p["aliases"]={"brian":["Brian Ennis","B. Ennis"],"amy":["Amy Jones","A. Jones"],"nick":[]}.get(p["instructor_key"],[])
    locations=[{**l,"resources":[v for r in l.get("internal_resources",[]) for v in [r["resource_name"],*r.get("aliases",[])]]} for l in data[paths[2]]["locations"]]
    return {"timezone":"America/New_York","maxSourceAgeMinutes":30,"minimumLeadMinutes":data[paths[8]]["minimum_lead_hours"]*60,"cleanupMinutes":0,"instructors":instructors,"sources":[{k:s.get(k) for k in ["calendar_source_key","instructor_key","mode","active","default_location_key"]} for s in data[paths[1]]["calendar_sources"]],"locations":locations,"travel":{**data[paths[3]],"instructor_key":"brian"},"containers":data[paths[4]]["containers"],"occupancyMinutes":occupancy,"courseTimes":course_times,"courseNameIds":names,"durationAuthority":authority,"shortSkills":list(selected.values()),"fullCourses":list(full.values()),"fullBarnaclesPerFamilyDay":1,"sourceHashes":{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},"qualificationEvidence":"Configured family eligibility in data/config/instructors.json; credential expiry not verified."}
def main():
    policy=build()
    content="(function(root){root.OpenShiftPolicy="+json.dumps(policy,separators=(",",":"))+";if(typeof module!==\"undefined\"&&module.exports)module.exports=root.OpenShiftPolicy;})(typeof window!==\"undefined\"?window:globalThis);\n"
    OUTPUT.write_text(content,encoding="utf-8")
    print("Wrote one dashboard policy asset:",OUTPUT)
if __name__=="__main__":main()
