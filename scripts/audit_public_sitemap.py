"""Read-only sitemap evidence; prints aggregate counts, never private records."""
import argparse
from collections import Counter
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen
import xml.etree.ElementTree as ET

BASE = 'https://www.910cpr.com'
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}


def inspect_sitemap(raw):
    root = ET.fromstring(raw)
    if root.tag != '{' + NS['s'] + '}urlset':
        raise ValueError('expected sitemap urlset')
    nodes = root.findall('s:url', NS)
    urls = [(n.findtext('s:loc', default='', namespaces=NS)).strip() for n in nodes]
    counts = Counter()
    for url in urls:
        parsed = urlsplit(url)
        parts = parsed.path.lower().split('/')
        if parsed.scheme != 'https' or parsed.netloc != 'www.910cpr.com':
            counts['foreign_or_insecure'] += 1
        if any(p in {'admin', 'private', 'data', 'ops'} for p in parts):
            counts['private_path'] += 1
        if parsed.query or parsed.fragment:
            counts['parameterized'] += 1
        counts['classes' if parsed.path.startswith('/classes/') else 'courses' if parsed.path.startswith('/courses/') else 'other_public'] += 1
    return {'url_count': len(urls), 'unique_url_count': len(set(urls)),
            'duplicate_count': len(urls) - len(set(urls)),
            'lastmod_count': sum(n.find('s:lastmod', NS) is not None for n in nodes),
            'categories': dict(sorted(counts.items()))}, set(urls)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sitemap', type=Path, default=Path('docs/sitemap.xml'))
    parser.add_argument('--live', action='store_true', help='Explicitly fetch public sitemap and robots; no credentials')
    args = parser.parse_args()
    report, local_urls = inspect_sitemap(args.sitemap.read_bytes())
    result = {'local': report, 'google_submission': 'unknown', 'reachability': 'not_checked', 'mutations': 0}
    if args.live:
        with urlopen(BASE + '/sitemap.xml', timeout=30) as response:
            live, live_urls = inspect_sitemap(response.read())
            live['http_status'] = response.status
            live['last_modified_header'] = response.headers.get('Last-Modified')
        with urlopen(BASE + '/robots.txt', timeout=30) as response:
            robots = response.read().decode('utf-8')
        result.update(live=live, local_only_count=len(local_urls-live_urls), live_only_count=len(live_urls-local_urls),
                      robots_sitemap_declared=('Sitemap: ' + BASE + '/sitemap.xml').lower() in robots.lower())
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
