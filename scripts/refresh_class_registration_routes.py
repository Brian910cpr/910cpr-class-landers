"""Routing-only regeneration for the existing public class listing and its details."""
import json
import re
from pathlib import Path
from scripts.class_registration_routing import rewrite_detail_routes, rewrite_directory_routes
ROOT=Path(__file__).resolve().parents[1]


def refresh(root=ROOT):
    index=root/'docs/classes/index.html'
    original=index.read_text(encoding='utf8')
    ids=re.findall(r'class="class-finder-secondary" href="/classes/(\d+)\.html"',original)
    if not ids or len(ids)!=len(set(ids)): raise ValueError('missing or duplicate public class listing')
    rows=json.loads((root/'docs/data/schedule_future.json').read_text(encoding='utf8'))['sessions']
    sessions={}
    for sid in ids:
        matches=[r for r in rows if str(r.get('session_id'))==sid]
        if len(matches)!=1: raise ValueError('class identity missing or ambiguous: '+sid)
        sessions[sid]=matches[0]
    changes={index:rewrite_directory_routes(original,sessions)}
    for sid in ids:
        file=root/'docs/classes'/(sid+'.html')
        changes[file]=rewrite_detail_routes(file.read_text(encoding='utf8'),sessions[sid],sessions)
    # Build every replacement before writing; never partially apply invalid identities.
    for file,content in changes.items():file.write_bytes(content.encode('utf8'))
    return {'listed':len(ids),'files':len(changes)}

if __name__=='__main__':print(json.dumps(refresh()))
