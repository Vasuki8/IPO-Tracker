"""Read two exact Final Prospectuses for hold acceptance; never publish values.

Full-file hashes bind the source; selected pages still need human visual review.
Only those pages and a receipt are retained, not copies of the full prospectuses.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys

import requests
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {'snehaa': (18126150, 467, 1), 'sacheerome': (7589875, 293, 3)}


def verify(output):
    holds = {h['id']: h for h in json.loads((ROOT / 'data/public_display_holds.json').read_text())['holds']}
    rows = {r['id']: r for r in json.loads((ROOT / 'tests/public_intermediary_reviews_retained.json').read_text())['ipos']}
    checked = []
    for identifier, (size, pages, physical_page) in EXPECTED.items():
        hold, row = holds[identifier], rows[identifier]
        if not all(row.get(k) == v for k, v in hold['identity'].items()):
            raise ValueError('Retained offer identity differs from the review')
        bindings = list(hold['fields'].values())
        url, expected_hash = bindings[0]['sourceUrl'], bindings[0]['sha256']
        if url != 'https://nsearchives.nseindia.com/emerge/corporates/content/' + {
            'snehaa':'SnehaaOrganicsLimited_PROSP.pdf', 'sacheerome':'SacheeromeLimited_PROSP.pdf'}[identifier]:
            raise ValueError('Unexpected source URL; review it explicitly')
        for field, binding in hold['fields'].items():
            proof = row['staticFieldProvenance'][field]
            value_bytes = json.dumps(row[field], sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()
            if (binding['sha256'] != expected_hash or binding['sourceUrl'] != url
                    or proof['sha256'] != expected_hash or proof['sourceUrl'] != url
                    or proof['issueOpenDate'] != row['openDate']
                    or proof['documentDate'] != binding['documentDate']
                    or proof['documentType'] != 'PROSPECTUS'
                    or proof['value'] != row[field]
                    or hashlib.sha256(value_bytes).hexdigest() != binding['valueDigest']):
                raise ValueError('Field/document/value binding differs from retained review')
        with requests.get(url, stream=True, timeout=(15, 45), headers={'User-Agent':'IPO-Tracker-source-review'}) as response:
            response.raise_for_status()
            if response.url != url:
                raise ValueError('Source redirected; review the destination explicitly')
            buffer = bytearray()
            for chunk in response.iter_content(65536):
                buffer.extend(chunk)
                if len(buffer) > size:
                    raise ValueError('Source grew beyond its reviewed byte identity')
        raw = bytes(buffer)
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != expected_hash:
            raise ValueError('Final Prospectus bytes differ from retained review')
        reader = PdfReader(io.BytesIO(raw))
        if len(reader.pages) != pages:
            raise ValueError('Unexpected PDF page count')
        writer = PdfWriter()
        writer.add_page(reader.pages[physical_page - 1])
        preview = output / f'{identifier}-physical-page-{physical_page}.pdf'
        with preview.open('wb') as target:
            writer.write(target)
        checked.append({'id':identifier, 'sourceUrl':url, 'documentDate':bindings[0]['documentDate'],
                        'sha256':expected_hash, 'bytes':len(raw), 'pages':pages,
                        'physicalPageForVisualReview':physical_page,
                        'pageArtifactSha256':hashlib.sha256(preview.read_bytes()).hexdigest()})
    return checked


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output', type=Path, default=ROOT / 'artifacts/intermediary-sources')
    args = cli.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    receipt = {'scope':'exact-file-and-field-binding-not-automatic-source-value-acceptance',
               'checkedAt':datetime.now(timezone.utc).isoformat(), 'status':'failed'}
    protected = [ROOT / 'data' / name for name in ('ipos.json', 'pending_updates.json')]
    before = [p.read_bytes() for p in protected]
    try:
        receipt['checked'] = verify(args.output)
        if before != [p.read_bytes() for p in protected]:
            raise ValueError('Source acceptance modified protected inputs')
        receipt['status'] = 'passed'
        receipt['visualReview'] = 'required-before-acceptance'
    except Exception as error:
        receipt['error'] = f'{type(error).__name__}: {error}'
    (args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
