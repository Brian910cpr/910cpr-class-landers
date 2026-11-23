"""Routing-only regeneration for the existing public class listing and its details."""
import json
import re
from pathlib import Path
from scripts.class_registration_routing import rewrite_detail_routes, rewrite_directory_routes
from scripts import build_index_and_sitemap as class_index
from scripts import refresh_class_finder_index as finder
ROOT=Path(__file__).resolve().parents[1]
# Only public-class numeric IDs and canonical UUIDs may identify a generated
# detail page. Never treat arbitrary slugs (notably index.html) as appointments.
DETAIL_ID = re.compile(r'(?:[0-9]+|[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})')

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


def refresh(root=ROOT, retired_previous_ids=None):
    index=root/'docs/classes/index.html'
    original=index.read_text(encoding='utf8')
    ids=re.findall(r'class="class-finder-secondary" href="/classes/(\d+)\.html"',original)
    if len(ids)!=len(set(ids)): raise ValueError('duplicate public class listing')
    if not ids and 'class="class-finder-card' in original:
        raise ValueError('empty listing has unexpected class cards')
    # The finder may select an authoritative class report instead of schedule_future.
    # Independently revalidate the chosen fresh source and its actual public IDs
    # before rewriting any CTA. Never use an unrelated snapshot to route a card.
    fresh_html, verified_ids = finder.render_current_class_finder()
    if set(ids) != verified_ids:
        raise ValueError('public class listing mismatches current eligible source')
    # Identity parity alone is insufficient: a moved session may retain its ID
    # while the finder advertises an old start, course or registration action.
    # Demand that this exact finder matches the freshly selected authoritative
    # source before writing any detail, sidebar, sitemap or CTA replacement.
    if original != fresh_html:
        raise ValueError('public class listing content mismatches current eligible source')
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

    # Retire only numeric/UUID detail files explicitly rejected by the SAME fresh
    # selected source. Do not delete internal bookings, alter source rows, or
    # assume missing identity/legacy inventory is safe to de-list.
    rejected_public_ids=set()
    for row in rows:
        sid=str(row.get('session_id') or row.get('id') or '').strip()
        if not DETAIL_ID.fullmatch(sid) or sid in verified_ids:
            continue
        if class_index.schedule_future_to_public_session(row) is not None:
            continue
        rejected_public_ids.add(sid)
        file=root/'docs/classes'/(sid+'.html')
        if file.is_file():
            changes[file]=UNLISTED_DETAIL_HTML

    # A fresh source need not contain a class that has just expired or was
    # withdrawn. It nevertheless had a public detail page in the PREVIOUS
    # finder. Retire precisely those previously listed IDs removed by the
    # verified refresh; do not sweep unrelated historical class archives.
    for retired_id in retired_previous_ids or ():
        sid=str(retired_id)
        if not re.fullmatch(r'[0-9]+',sid):
            raise ValueError('invalid previously published class identity')
        if sid in verified_ids:
            raise ValueError('cannot retire a currently eligible public class')
        rejected_public_ids.add(sid)
        file=root/'docs/classes'/(sid+'.html')
        if file.is_file():
            changes[file]=UNLISTED_DETAIL_HTML

    # Previously redacted details are source-absent tombstones too. An archive
    # cannot revive their discovery links just because an old row vanished.
    for detail in (root / 'docs/classes').glob('*.html'):
        if not DETAIL_ID.fullmatch(detail.stem) or detail.stem in verified_ids:
            continue
        content = changes.get(detail)
        if content is None:
            content = detail.read_text(encoding='utf8')
        if ('name="robots" content="noindex,nofollow"' in content
                and "This class is not publicly listed" in content):
            rejected_public_ids.add(detail.stem)

    # Include earlier redacted/source-absent detail tombstones in sitemap
    # cleanup as well as archive cleanup; otherwise verification halts every
    # refresh while the same private URL remains discoverable.
    # Retiring a private class detail must also remove its discovery URL from
    # the sitemap in the SAME verified-source publication. Preserve unrelated
    # historic/public URLs and all other sitemap entries byte-for-byte.
    sitemap=root/'docs/sitemap.xml'
    if rejected_public_ids and sitemap.is_file():
        xml=sitemap.read_text(encoding='utf8')
        def retire_url(match):
            block=match.group(0)
            location=re.search(r'<loc>\s*https://(?:www\.)?910cpr\.com/classes/([0-9a-fA-F-]+)\.html\s*</loc>',block)
            return '' if location and location.group(1) in rejected_public_ids else block
        updated=re.sub(r'(?ms)^[ \t]*<url>.*?</url>[ \t]*(?:\r?\n|$)',retire_url,xml)
        if updated != xml:
            changes[sitemap]=updated

    # Remove only *whole isolated archive cards* for explicitly rejected IDs.
    # Changing just the href would leave the private class date visible nearby.
    # A compound card or unstructured reference fails closed at verification;
    # unrelated historic class links remain untouched.
    if rejected_public_ids:
        archive_paths = set()
        for directory in class_index.STALE_CLASS_INDEX_DIRS:
            relative = directory.relative_to(class_index.ROOT)
            archive_dir = root / relative
            if archive_dir.is_dir():
                archive_paths.update(archive_dir.rglob('*.html'))
        for file in class_index.STALE_CLASS_INDEX_FILES:
            relative = file.relative_to(class_index.ROOT)
            archive_file = root / relative
            if archive_file.is_file():
                archive_paths.add(archive_file)
        id_ref = re.compile(
            r'''(?:href=["'](?:https?://(?:www\.)?910cpr\.com)?/classes/([0-9a-fA-F-]+)\.html(?:[?#][^"']*)?["']|data-session-id=["']([0-9a-fA-F-]+)["'])''',
            re.IGNORECASE,
        )
        cards = [
            # Prefer the entire class card over a child list item so private
            # class labels/dates outside the link are removed as one unit.
            re.compile(r'(?is)<article\b[^>]*>.*?</article\s*>'),
            re.compile(r'(?is)<li\b[^>]*>.*?</li\s*>'),
        ]
        def references(card):
            return {match.group(1) or match.group(2) for match in id_ref.finditer(card)}
        for path in sorted(archive_paths):
            original_archive = path.read_text(encoding='utf8')
            updated_archive = original_archive
            for card_pattern in cards:
                def remove_isolated_card(match):
                    ids = references(match.group(0))
                    if ids & rejected_public_ids:
                        if ids - rejected_public_ids:
                            raise ValueError('compound archived card mixes public and nonpublic classes')
                        return ''
                    return match.group(0)
                updated_archive = card_pattern.sub(remove_isolated_card, updated_archive)
            if references(updated_archive) & rejected_public_ids:
                raise ValueError('ambiguous archived reference to nonpublic class')
            if updated_archive != original_archive:
                changes[path] = updated_archive

    # Build every replacement before writing; never partially apply invalid identities.
    for file,content in changes.items():file.write_bytes(content.encode('utf8'))
    return {'listed':len(ids),'files':len(changes)}

if __name__=='__main__':print(json.dumps(refresh()))
