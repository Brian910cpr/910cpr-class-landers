"""Routing-only plan for the known family selectors and aliases; no schedule calculation."""
import json,re,subprocess
from pathlib import Path
from scripts.build_bls_block_schedule_pilot import selector_registration_action_script,selector_registration_capabilities
ROOT=Path(__file__).resolve().parents[1]
VERSION='20261119-request-containment2'
def plan_refresh(root=ROOT):
    # Immutable Git reads preserve distinct case-sensitive aliases on Windows.
    files=subprocess.check_output(['git','grep','-l','-E','ResolvedSelectorAvailability.registration(Action|Destination)','HEAD','--','docs'],cwd=root,text=True).splitlines()
    files=[v.removeprefix('HEAD:') for v in files]
    if len(files)!=13:raise ValueError('unexpected_selector_output_scope')
    plans={}
    for name in files:
        old=subprocess.check_output(['git','show','HEAD:'+name],cwd=root).decode('utf8')
        marker='        link.href = ResolvedSelectorAvailability.registrationDestination(course);' if '        link.href = ResolvedSelectorAvailability.registrationDestination(course);' in old else '        const action = ResolvedSelectorAvailability.registrationAction(course,'
        start=old.index(marker)
        end=old.index("        link.addEventListener('click'",start)
        new=old[:start]+selector_registration_action_script('/'+name.removeprefix('docs/'))+'\n'+old[end:]
        new=re.sub(r'        item.append\(summary, badge, link\);(?:\n        if \(requestNotice\) item.appendChild\(requestNotice\);)?','        item.append(summary, badge, link);\n        if (requestNotice) item.appendChild(requestNotice);',new)
        lines=[l for l in new.splitlines(keepends=True) if not l.startswith('    const nativeClassCapabilities = ')];indices=[i for i,l in enumerate(lines) if l.startswith('    const courseOptions = ')]
        if len(indices)!=1:raise ValueError('course_option_marker_ambiguous')
        lines.insert(indices[0]+1,'    const nativeClassCapabilities = '+json.dumps(selector_registration_capabilities())+';\n')
        new=''.join(lines).replace('resolved-selector-availability.js?v=20261119-canonical-origin1','resolved-selector-availability.js?v='+VERSION).replace('resolved-selector-availability.js?v=20261119-request-containment1','resolved-selector-availability.js?v='+VERSION)
        if 'registrationDestination(course)' in new or "link.href = '/register/skills-session/?'" in new:raise ValueError('incomplete_selector_action_replacement')
        plans[name]=new
    return plans
if __name__=='__main__':
    # A plan output is deliberate: Windows cannot materialize distinct upper/lowercase paths together.
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args()
    plans=plan_refresh();Path(args.output).write_text(json.dumps(plans),encoding='utf8')
    print(json.dumps({'planned_files':len(plans),'schedule_rebuilt':False,'writes_to_site':False}))
