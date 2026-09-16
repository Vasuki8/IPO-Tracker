"""Evidence gates for P4 closure and permission to advance P5 processing."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FINAL_REVALIDATION_PREFIX = "provenance.finalProspectus."


def _final_revalidation_stats(rows):
    matching = []
    fields = 0
    for row in rows:
        pending = [
            str(field)
            for field in (row.get("missingFields") or [])
            if str(field).startswith(FINAL_REVALIDATION_PREFIX)
        ]
        if pending:
            matching.append(row)
            fields += len(pending)
    return len(matching), fields


def status(queue, validation):
    p4 = [row for row in queue['queue'] if row.get('priority') == 4]
    higher = [row for row in queue['queue'] if row.get('priority', 9) < 4]
    p4_revalidation_records, p4_revalidation_fields = _final_revalidation_stats(p4)
    higher_revalidation_records, higher_revalidation_fields = _final_revalidation_stats(higher)
    blocked = bool(p4 or higher or validation['errorCount'] or validation['reviewCount'])
    return {
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'p4': {
            'status': 'incomplete' if blocked else 'complete',
            'actionableRecords': len(p4),
            'higherPriorityRecords': len(higher),
            'semanticErrors': validation['errorCount'],
            'sourceReviewItems': validation['reviewCount'],
            'finalProspectusRevalidationRecords': p4_revalidation_records,
            'finalProspectusRevalidationFields': p4_revalidation_fields,
            'higherPriorityFinalProspectusRevalidationRecords': higher_revalidation_records,
            'higherPriorityFinalProspectusRevalidationFields': higher_revalidation_fields,
            'resolvedUnavailableRecords': queue.get('resolvedUnavailableRecordCount', 0),
        },
        'p5': {
            'status': 'waiting_for_p4' if blocked else 'enabled',
            'actionableRecords': sum(row.get('priority') == 5 for row in queue['queue']),
        },
    }


def main():
    output = status(
        json.loads((ROOT / 'data/missing_queue.json').read_text()),
        json.loads((ROOT / 'data/validation.json').read_text()),
    )
    (ROOT / 'data/phase_status.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output))


if __name__ == '__main__':
    main()
