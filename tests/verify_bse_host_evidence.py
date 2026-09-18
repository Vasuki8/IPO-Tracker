"""Read-only bounded BSE host inspection; no financial-value or licensing approval."""
from datetime import datetime, timezone
import hashlib
import json
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

HOSTS = {'www.bseindia.com', 'bseindia.com', 'beta.bseindia.com'}
SEEDS = (
    'https://www.bseindia.com/',
    'https://www.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=1&Type=p',
    'https://beta.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=1&Type=p',
)


def bounded_url(url):
    try:
        u = urlsplit(url)
        return (u.scheme == 'https' and u.hostname in HOSTS and u.port in (None, 443)
                and not u.username and not u.password)
    except ValueError:
        return False


def inspect(session, seed):
    item = {'requestedUrl': seed, 'chain': []}
    url = seed
    try:
        for _ in range(4):
            if not bounded_url(url):
                raise ValueError('Redirect outside the exact BSE HTTPS hosts')
            with session.get(url, timeout=(10, 20), allow_redirects=False, stream=True) as response:
                hop = {'url': url, 'status': response.status_code}
                item['chain'].append(hop)
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get('Location')
                    if not location:
                        raise ValueError('Redirect missing Location')
                    url = urljoin(url, location)
                    hop['location'] = url
                    continue
                response.raise_for_status()
                raw = bytearray()
                for chunk in response.iter_content(65536):
                    raw.extend(chunk)
                    if len(raw) > 2_000_000:
                        raise ValueError('Page exceeds the bounded evidence limit')
                soup = BeautifulSoup(bytes(raw), 'html.parser')
                title = soup.title.get_text(' ', strip=True) if soup.title else ''
                text = soup.get_text(' ', strip=True)
                links = []
                for anchor in soup.find_all('a', href=True):
                    target = urljoin(url, anchor['href'])
                    if bounded_url(target):
                        links.append({'url': target, 'text': anchor.get_text(' ', strip=True)[:100]})
                item.update(finalUrl=url, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                            title=title, sameOrganisationLinks=links,
                            textStart=text[:500], textEnd=text[-500:])
                return item
        raise ValueError('Too many redirects')
    except (requests.RequestException, ValueError) as error:
        item['error'] = str(error)[:500]
        return item


def verify_binding(pages):
    """An already trusted BSE endpoint must explicitly direct readers to beta."""
    bindings = []
    for page in pages:
        if urlsplit(page['requestedUrl']).hostname not in {'www.bseindia.com', 'bseindia.com'}:
            continue
        for hop in page['chain']:
            target = hop.get('location', '')
            if bounded_url(target) and urlsplit(target).hostname == 'beta.bseindia.com':
                bindings.append({'kind': 'BSE HTTPS redirect', 'from': hop['url'], 'to': target})
        if not page.get('error'):
            for link in page.get('sameOrganisationLinks', []):
                if urlsplit(link['url']).hostname == 'beta.bseindia.com':
                    bindings.append({'kind': 'BSE page link', 'from': page['finalUrl'], **link})
    healthy_beta = [p for p in pages if not p.get('error')
                    and urlsplit(p.get('finalUrl', '')).hostname == 'beta.bseindia.com'
                    and 'BSE' in p.get('title', '').upper() and p.get('bytes', 0) > 1000]
    return bindings, bool(bindings and healthy_beta)


def main():
    with requests.Session() as session:
        session.headers.update({'User-Agent': 'IPO-Tracker-source-authority-review', 'Accept': 'text/html'})
        pages = [inspect(session, seed) for seed in SEEDS]
    bindings, passed = verify_binding(pages)
    print(json.dumps({'scope': 'host-link-evidence-not-values-finality-or-redistribution-rights',
                      'checkedAt': datetime.now(timezone.utc).isoformat(),
                      'status': 'passed' if passed else 'needs_review',
                      'bindings': bindings, 'pages': pages}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
