"""Routing-only regeneration for the existing public class listing and its details."""
import json
import re
from pathlib import Path
from scripts.class_registration_routing import rewrite_detail_routes, rewrite_directory_routes
from scripts import build_index_and_sitemap as class_index
from scripts import refresh_class_finder_index as finder
ROOT=Path(__file__).resolve().parents[1]


def refresh(root=ROOT):
    index=root/'docs/classes/index.html'
    original=index.read_text(encoding='utf8')
    ids=re.findall(r'class="class-finder-secondary" href="/classes/(\d+)\.html"',original)
    if len(ids)!=len(set(ids)): raise ValueError('duplicate public class listing')
    if not ids and 'class="class-finder-card' in original:
        raise ValueError('empty listing has unexpected class cards')
    # The finder may select an authoritative class report instead of schedule_future.
    # Independently revalidate the chosen fresh source and its actual public IDs
    # before rewriting any CTA. Never use an unrelated snapshot to route a card.
    _, verified_ids = finder.render_current_class_finder()
    if set(ids) != verified_ids:
        raise ValueError('public class listing mismatches current eligible source')
    if not ids:
        return {'listed': 0, 'files': 0}
    rows=class_index.load_schedule_future_sessions()
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
