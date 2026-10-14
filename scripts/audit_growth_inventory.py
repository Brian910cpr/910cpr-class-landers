"""Read-only growth inventory audit. Never imports or runs public builders."""
import argparse
from collections import Counter
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


def audit(root):
    docs = root / 'docs'
    files = sorted(docs.rglob('*.html'))
    families = Counter(p.relative_to(docs).parts[0] if len(p.relative_to(docs).parts) > 1 else '(root)' for p in files)
    maps = []
    missing = []
    for path in sorted(docs.glob('*sitemap*.xml')):
        tree = ET.parse(path)
        kind = tree.getroot().tag.rsplit('}', 1)[-1]
        urls = [e.text for e in tree.iter() if e.tag.rsplit('}', 1)[-1] == 'loc' and e.text]
        maps.append({'path': path.relative_to(root).as_posix(), 'kind': kind, 'entries': len(urls), 'bytes': path.stat().st_size, 'duplicate_entries': len(urls) - len(set(urls))})
        if kind == 'urlset':
            for url in urls:
                parsed = urlsplit(url)
                if parsed.hostname not in ('www.910cpr.com', '910cpr.com'):
                    continue
                target = docs / unquote(parsed.path).lstrip('/')
                if not target.is_file() and not (target / 'index.html').is_file():
                    missing.append(url)
    return {'scope': 'Checked-in local HTML and root sitemap XML only; not indexability, content quality, deployed state or GSC proof.', 'html_files': len(files), 'families': dict(sorted(families.items())), 'sitemaps': maps, 'missing_sitemap_targets': sorted(set(missing)), 'persistent_evidence': 'BUILT only; acquisition end-to-end proof not established by this audit.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(audit(args.root), indent=2))


if __name__ == '__main__':
    main()
