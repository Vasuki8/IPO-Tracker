"""Read a reviewed-only publication request; never collect or write IPO data."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST_PATH = 'data/reviewed_publication_request.json'


def request_ids(request, known_ids):
    if (not isinstance(request, dict)
            or set(request) != {'schemaVersion', 'requestId', 'ids'}
            or type(request['schemaVersion']) is not int or request['schemaVersion'] != 1
            or not isinstance(request['requestId'], str)
            or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}', request['requestId'])):
        raise ValueError('Unsupported reviewed publication request')
    ids = request['ids']
    if (not isinstance(ids, list) or not 0 < len(ids) <= 16
            or any(not isinstance(identifier, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', identifier) for identifier in ids)
            or len(ids) != len(set(ids)) or set(ids) - set(known_ids)):
        raise ValueError('Request requires unique issuer IDs with complete reviewed proofs')
    return ','.join(ids)


def main():
    from reviewed_evidence import load_groups
    request = json.loads((ROOT / REQUEST_PATH).read_text(encoding='utf-8'))
    print(request_ids(request, [group['identity']['id'] for group in load_groups()]))


if __name__ == '__main__':
    main()
