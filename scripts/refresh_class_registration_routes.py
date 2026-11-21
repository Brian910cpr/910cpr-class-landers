"""Routing-only regeneration for the existing public class listing and its details."""
import json
import re
from pathlib import Path
from scripts.class_registration_routing import rewrite_detail_routes, rewrite_directory_routes
from scripts import build_index_and_sitemap as class_index
from scripts import refresh_class_finder_index as finder
ROOT=Path(__file__).resolve().parents[1]

# Rejected canonical-linked or explicitly nonpublic appointments may have a
# previously generated, directly addressable legacy detail HTML file. Hiding
# the finder card alone is insufficient: those bookmarked pages must not keep
# advertising a private appointment or an inherited external booking URL.
UNLISTED_DETAIL_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<link rel="canonical" href="https://www.910cpr.com/classes/index.html">
<title>Class listing unavailable | 910CPR</title>
</head>
<body>
<main>
<h1>This class is not publicly listed</h1>
<p>No registration is available from this class page. Please choose from our current public classes.</p>
<p><a href="/classes/index.html">Browse current classes</a></p>
</main>
</body>
</html>
"""


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
    # Include otherwise filtered private/offsite source records ONLY while
    # retiring existing detail pages. The finder and verified_ids remain
    # public-only; source records never enter the rendered inventory.
    rows=class_index.load_schedule_future_sessions(include_nonpublic_locations=True)
    sessions={}
    for sid in ids:
        matches=[r for r in rows if str(r.get('session_id'))==sid]
        if len(matches)!=1: raise ValueError('class identity missing or ambiguous: '+sid)
        sessions[sid]=matches[0]
    changes={}
    if ids:
        changes[index]=rewrite_directory_routes(original,sessions)
    for sid in ids:
        file=root/'docs/classes'/(sid+'.html')
        changes[file]=rewrite_detail_routes(file.read_text(encoding='utf8'),sessions[sid],sessions)

    # Retire only existing detail files explicitly rejected by the SAME fresh
    # selected source. Do not delete internal bookings, alter source rows, or
    # assume missing identity/legacy inventory is safe to de-list.
    rejected_public_ids=set()
    for row in rows:
        sid=str(row.get('session_id') or row.get('id') or '').strip()
        if not re.fullmatch(r'[0-9]+',sid) or sid in verified_ids:
            continue
        if class_index.schedule_future_to_public_session(row) is not None:
            continue
        rejected_public_ids.add(sid)
        file=root/'docs/classes'/(sid+'.html')
        if file.is_file():
            changes[file]=UNLISTED_DETAIL_HTML

    # Retiring a private class detail must also remove its discovery URL from
    # the sitemap in the SAME verified-source publication. Preserve unrelated
    # historic/public URLs and all other sitemap entries byte-for-byte.
    sitemap=root/'docs/sitemap.xml'
    if rejected_public_ids and sitemap.is_file():
        xml=sitemap.read_text(encoding='utf8')
        def retire_url(match):
            block=match.group(0)
            location=re.search(r'<loc>\\s*https://(?:www\\.)?910cpr\\.com/classes/(\\d+)\\.html\\s*</loc>',block)
            return '' if location and location.group(1) in rejected_public_ids else block
        updated=re.sub(r'(?ms)^[ \\t]*<url>.*?</url>[ \\t]*(?:\\r?\\n|$)',retire_url,xml)
        if updated != xml:
            changes[sitemap]=updated

    # Build every replacement before writing; never partially apply invalid identities.
    for file,content in changes.items():file.write_bytes(content.encode('utf8'))
    return {'listed':len(ids),'files':len(changes)}

if __name__=='__main__':print(json.dumps(refresh()))
