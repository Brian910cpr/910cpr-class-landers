#!/usr/bin/env python3
"""Build unapplied, fail-closed Hx session alias review artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


INSTRUCTOR_IDS = {
    "A. Babineau":"fecf368f-e3c4-4a94-b63f-9c7ec5cd98de", "B. Williamson":"ca0d95dd-44d1-4377-9c53-b247d6dc30f7",
    "W. Perry":"a311d40b-5d3b-4914-909c-4ac6aeb1b053", "B. Woodard":"431447f2-25b5-4d14-8f81-f5a99bcb1f54",
    "J. Ezzell":"f4be701a-4e09-4b27-934e-7f1168296e4a", "E. Brown":"19a650e2-3d24-41c5-8f17-2bcae65ef28e",
    "T. VanPelt":"e646118a-c654-4f25-9198-eddafa00fc03", "T. Balog":"71db8183-1a44-4370-8c90-2ff104002644",
    "A. Glantz":"9d5577ae-46c3-41ee-9f3b-4a7b9a055f27", "C. Lind":"53d36fb7-7817-4b57-adff-64cfb81f8af3",
    "J. Bratton":"0d38a4bd-f425-4465-baa2-d0444f002dd1", "K. Wasner":"541ecbff-69d7-43b1-9e81-e3263d54cc03",
    "A. Williams":"c989da7e-9174-4acd-bc89-33ca2f68303b", "B. Bailey":"291ef9ce-d392-46ad-a112-630f5c6cdc89",
    "j. tassi":"b25084f0-d2a0-4616-a837-094147d5c7ac", "V. Carey":"944570ed-dd4c-44d0-a1bc-98d4346f3919",
    "R. Meyer":"0047b62b-2eb7-4832-9c96-0c5ef41f11e4", "M. Cox":"d5c112fb-52a6-40c7-9c32-26672172aa17",
    "L. Fowler":"8a0799ef-b249-44ea-ad98-f9bb4df9f0d6", "J. Brown":"c8379585-56bd-44b3-8756-0b06179262e8",
    "M. Kabay":"17ce9bfd-5bc2-454f-8bc8-66741ceb856e", "L. Raynor":"2f6a86e1-bc20-4270-a76b-d2f1cb2c7e19",
    "C. Kiefner":"f1675079-974a-48dd-b6b4-c68e6d8bc101", "J. Russ":"31f46e75-2167-45ab-8669-02e2b938a742",
    "A. Tabb":"e4927ccb-7242-4577-a694-a22a882fc8c5", "B. McKendree":"a533f169-5363-4e26-afb0-d0446a44d93c",
    "A. White":"fb803607-57d2-4d94-a4bf-26e7fc8b4e06", "K. Belitsos":"226bfabe-90a2-482d-9941-fdd1486ba7fd",
    "J. Gordon":"e5c54283-3b6e-4c96-8ba3-b36c4e517107", "A. Schoettle":"e1092b5d-ec5a-47fe-a3f5-802f0d4b0fb1",
    "F. Richardson III":"8be3d052-719e-4544-9548-c3a0651b9c72", "R. Robinson":"9b27d07c-d6f5-4427-b93b-1e86f9aa446a",
    "T. Tims":"e4c34895-da52-4de8-93e6-ba7e8218b9b1", "H. Williams":"11a0fea3-e933-4b67-91c7-8c2f86d879b6",
    "H. Hendrick":"013ccbaa-183c-40ca-ab4d-67eaf3d7dd7b", "R. Henderson":"4a4ccf0c-42b5-47e1-ad56-d27d26c7b0d9",
    "D. McIntire":"874c5823-d19b-4d11-82f8-7d8e6c9122cc", "J. Logan Jones":"b74cce48-609a-4f72-81c7-1796dd7df758",
    "S. Relyea":"48bc020b-ed55-462a-a83e-fdadf1643427", "K. Raynor":"04e8eb85-f5d5-405c-9004-45aed6c51ad9",
    "T. Gatewood":"09db259a-7f40-4644-a601-9de5702dc327", "L. Trynovich":"8a92815e-6b85-48a6-80bb-577f69a29f1c",
    "T. Jones":"a1d82b18-c467-41fa-93b6-b8eb2a075707", "C. Maywald":"37d46943-5ea0-4a55-a195-e669885ec0cf",
    "K. Ashley":"0a966898-5a80-4266-95f7-06bd8da22a41", "O. Feest":"d45c1873-5fe4-4a9c-99dd-c636a665dc85",
    "A. Carafas":"96e47994-477b-4780-8d7b-656ff2db0dde", "L. Penca":"0217872a-210b-4d4c-9b0b-ac7ae503a29c",
    "E. Johnson":"8daf7a31-4586-48b1-a2ab-8473a34d6a3b", "J. Bryant":"a8cdbc60-db48-4a7b-917a-bf563bdd0a50",
    "D. Whittington":"4c1b9bc2-c405-4806-813a-82cc58460a65", "S. Garcia":"0e34e21a-1c9f-4c07-bac4-7cbc8a637bc3",
    "J. Henry":"2940a650-4208-4c88-9134-448194fcc93d", "L. Colon":"2e9d1687-1d1e-47ac-b795-3d92c41087e3",
    "T. Johnson":"d11919c9-9e0d-4757-8284-3d7e89527e54",
}

INSTRUCTOR_LABELS = {
    "Audrie Babineau":"A. Babineau", "Beth Williamson":"B. Williamson", "William Perry":"W. Perry",
    "Benjamin Woodard":"B. Woodard", "Jennifer Ezzell":"J. Ezzell", "Eric Brown":"E. Brown",
    "Timothy VanPelt":"T. VanPelt", "Taylor Balog":"T. Balog", "Ashlie Glantz":"A. Glantz",
    "Crystal Lind":"C. Lind", "Justin Bratton":"J. Bratton", "Kaitlyn Wasner":"K. Wasner",
    "Amy Williams":"A. Williams", "Burke Bailey":"B. Bailey", "joseph tassi":"j. tassi",
    "Virginia Carey":"V. Carey", "Robert Meyer":"R. Meyer", "Mathew Cox":"M. Cox", "Lea Fowler":"L. Fowler",
    "Justin Brown":"J. Brown", "Michelle Kabay":"M. Kabay", "Luke Raynor":"L. Raynor", "Cori Kiefner":"C. Kiefner",
    "Jennifer Russ":"J. Russ", "Ashia Tabb":"A. Tabb", "Brian McKendree":"B. McKendree", "Amber White":"A. White",
    "Kweilin Belitsos":"K. Belitsos", "Jana Gordon":"J. Gordon", "Alexa Schoettle":"A. Schoettle",
    "Frank Richardson III":"F. Richardson III", "Rynee Robinson":"R. Robinson", "Tara Tims":"T. Tims",
    "Heather Williams":"H. Williams", "Holly Hendrick":"H. Hendrick", "Robert Henderson":"R. Henderson",
    "Donna McIntire":"D. McIntire", "Joan Logan Jones":"J. Logan Jones", "Suzanne Relyea":"S. Relyea",
    "Katherine Raynor":"K. Raynor", "Tiffaney Gatewood":"T. Gatewood", "Luke Trynovich":"L. Trynovich",
    "Taylor Jones":"T. Jones", "Corey Maywald":"C. Maywald", "Kandy Ashley":"K. Ashley", "Owen Feest":"O. Feest",
    "Angela Carafas":"A. Carafas", "Laurie Penca":"L. Penca", "Ebony Johnson":"E. Johnson",
    "Jasmine Bryant":"J. Bryant", "Damiano Whittington":"D. Whittington", "Sheila Garcia":"S. Garcia",
    "Jasmine Henry":"J. Henry", "Lydia Colon":"L. Colon", "Tracey Johnson":"T. Johnson",
}

COURSES = {
    "American Heart Association's Online Heartsaver® Programs":("7e97f53e-dd56-4d63-b42e-5acc76076460","AHA Heartsaver® First Aid CPR AED – Blended"),
    "Take your AHA CPR programs online!":("fb983908-788e-4d8f-ba12-36179a0d288b","Take your AHA CPR programs online!"),
    "HSI Adult First Aid | CPR AED<br><i>Traditional Classroom</i>":("475f89ad-25e5-4a7c-89c5-3115194db97b","HSI Adult First Aid | Adult CPR AED"),
    "Heartsaver® K-12 - In-person [AHA]":("bd7d2142-bb45-47e1-a6be-391d8394ee51","Heartsaver First Aid CPR AED for K-12 Schools [AHA]"),
    "Elementary First Aid<img src=\"https://www.enrollware.com/sitefiles/coastalcprtraining/Logo/stripes.png\" style=\"float:right;width:75px;vertical-align:top;\"></img><br><style> p { text-indent: 50px; } </style> <i>to meet \"U.S. Coast Guard Maritime Elementary First Aid and CPR\" Requirement </i>":("0433bcf8-d6fc-4666-ab4a-7afd479be633","USCG Elementary First Aid | CPR (AHA Heartsaver®)"),
    "ARC - BLS - In-Person Classroom":("af63680e-54c7-4c77-9d6d-5c87f344d0e4","ARC BLS"),
    "RCP para Familiares y Amigos [American Heart Association]":("bd22a38a-06e8-46f5-981a-ebebd1e178e2","AHA - RCP para Familiares y Amigos"),
    "Phlebotomy Technician Program (80 Hr - 9 Weeks - M,T,W)":("49cd2c4b-8c57-4336-b1bb-0e7567831627","Phlebotomy Technician Program (80 Hr - 9 Weeks - M,T,W)"),
    "ARC - Adult and Pediatric First Aid/CPR/AED [American Red Cross] ✚":("9688186e-a9ef-47f9-9857-bdb74b792c6b","ARC Adult and Pediatric First Aid/CPR/AED"),
    "AHA - PALS Provider - In Person - Initial":("cc977571-db34-4508-b82c-24061f5919e8","AHA PALS Provider"),
    "Elementary First Aid <b>ONLINE</b><img src=\"https://www.enrollware.com/sitefiles/coastalcprtraining/Logo/stripes.png\" style=\"float:right;width:75px;vertical-align:top;\"></img><br><i>to meet \"U.S. Coast Guard Maritime Elementary First Aid and CPR\" Requirement </i>":("499d874a-db42-4e8f-aa90-587ae848c61c","USCG Elementary First Aid | CPR - (AHA Heartsaver Online + Skills)"),
    "ARC - PALS Blended Learning":("05da03f8-64d1-4dc6-a457-a352b1a9501e","American Red Cross PALS - Blended Learning"),
    "Phlebotomy - National Cert Test Prep":("25f0d0a0-fbed-404e-956c-d7b0d841f934","Phlebotomy - National Cert Test Prep"),
    "ARC - ALS In-person [American Red Cross] ✚":("671d2b5b-c0a7-4c4a-9c3d-0801b4402559","American Red Cross ALS - In-person"),
    "AHA - Heartsaver® - Become an American Heart Association Instructor":("347456b6-b637-442d-9663-abed1c9fad73","AHA Heartsaver Instructor"),
}

LOCATIONS = {
    "Spectrum Learning Solutions, LLC":("06fe938f-6f56-4815-8dc7-beecd22a3895","Spectrum Learning Solutions, LLC"),
    "Long Leaf Park, Wilmington, NC":("531815f7-f1f9-4c13-8557-344bd0b3f792",":: Long Leaf Park"),
}


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def redact(value: str) -> str:
    return re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", "[redacted-email]", value, flags=re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", type=Path, required=True); ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("--base-reference", type=Path, required=True); ap.add_argument("--reference-output", type=Path, required=True)
    ap.add_argument("--inventory-output", type=Path, required=True); ap.add_argument("--sql-output", type=Path, required=True)
    a = ap.parse_args(); payload=json.loads(a.payload.read_text()); before=json.loads(a.before.read_text()); ref=json.loads(a.base_reference.read_text(encoding="utf-8-sig"))
    records={r["source_record_id"]:r for r in payload["records"]}
    fields={"session_location":"location_name","session_instructor":"instructor_name","session_course":"course_name","session_end_at":"duration_hours"}
    inventories={}
    for kind,field in fields.items():
        count=Counter((records[x["source_record_id"]]["session"].get(field) or "") for x in before["unresolved_or_ambiguous"] if x["kind"]==kind)
        inventories[kind]=[{"source_value":"[missing]" if not k else redact(k),"frequency":v} for k,v in count.most_common()]
    for source,label in INSTRUCTOR_LABELS.items():
        pid=INSTRUCTOR_IDS[label]; ref.setdefault("people",[]).append({"id":pid,"display_name":label})
        ref.setdefault("instructor_aliases",[]).append({"source":"enrollware_student_report","source_label":source,"person_id":pid})
    for source,(cid,name) in COURSES.items():
        ref.setdefault("courses",[]).append({"id":cid,"name":name})
        ref.setdefault("course_aliases",[]).append({"source":"enrollware_student_report","source_label_sha256":hashlib.sha256(source.encode()).hexdigest(),"course_id":cid})
    for source,(lid,name) in LOCATIONS.items():
        ref.setdefault("locations",[]).append({"id":lid,"name":name})
        ref.setdefault("location_aliases",[]).append({"source":"enrollware_student_report","source_label":source,"location_id":lid})
    a.reference_output.write_text(json.dumps(ref,indent=2,sort_keys=True)+"\n", encoding="utf-8")
    inventory={"source":"enrollware_student_report","before_counts":{k:sum(x["frequency"] for x in v) for k,v in inventories.items()},
               "frequency_ranked":inventories,"proposals":{"locations":len(LOCATIONS),"instructors":len(INSTRUCTOR_LABELS),"courses":len(COURSES),"timing":0},
               "instructor_classification":{"uniquely_resolvable_aliases":len(INSTRUCTOR_LABELS),"absent_from_authority":0,"ambiguous_or_missing_representations":1},
               "timing_review":{"missing":81,"range_value_3_to_4":2,"implausible_90_hours":1,"zero_duration":1,"safe_corrections":0},
               "nhcso":"source export lacks the 2026 period; no history manufactured"}
    a.inventory_output.write_text(json.dumps(inventory,indent=2,sort_keys=True)+"\n", encoding="utf-8")
    tables=(("historical_location_aliases","location_id",LOCATIONS),("historical_instructor_aliases","person_id",{k:(INSTRUCTOR_IDS[v],v) for k,v in INSTRUCTOR_LABELS.items()}),("historical_course_aliases","course_id",COURSES))
    lines=["-- REVIEW ONLY: do not apply before approval.","begin;"]
    for table,_,_ in tables:
        lines += [f"alter table public.{table} add column if not exists source_system text not null default 'legacy_unscoped';",
                  f"alter table public.{table} add column if not exists provenance jsonb not null default '{{}}'::jsonb;",
                  f"alter table public.{table} add column if not exists review_status text not null default 'approved_legacy';",
                  f"alter table public.{table} add column if not exists active boolean not null default true;",
                  f"alter table public.{table} add column if not exists reviewed_at timestamptz;",
                  f"alter table public.{table} drop constraint if exists {table}_pkey;",
                  f"alter table public.{table} add constraint {table}_pkey primary key (source_system, source_label);" ]
    for table,target,items in tables:
        for source,(entity_id,canonical) in items.items():
            prov=json.dumps({"evidence":"exact/curated Enrollware historical label","canonical_label":canonical,"review_commit":"8de12539406b2fdfcf56c67a5e97fa4a9239cc18"},separators=(",",":"))
            lines.append(f"insert into public.{table} (source_system,source_label,{target},provenance,review_status,active) values ('enrollware_student_report',{sql_quote(source)},'{entity_id}',{sql_quote(prov)}::jsonb,'reviewed',true);")
    lines += ["-- Plain INSERT plus the scoped primary key deliberately fails closed on collisions.","commit;"]
    a.sql_output.write_text("\n".join(lines)+"\n", encoding="utf-8")
    return 0

if __name__ == "__main__": raise SystemExit(main())
