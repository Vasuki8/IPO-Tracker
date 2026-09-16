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


def _review_gate_stats(queue, validation):
    """Separate pre-P5 review blockers from P5-only historical review work.

    Validation intentionally scans every record, including P5 history. Using its
    aggregate ``reviewCount`` as a P4 gate would therefore require P5 review work
    before P5 can be enabled. Resolve each review issue through the authoritative
    missing-data queue priority instead. Unknown/unmapped review items fail closed.
    """
    priority_by_id = {}
    for row in queue.get("queue") or []:
        record_id = row.get("id")
        if not record_id:
            continue
        try:
            priority = int(row.get("priority"))
        except (TypeError, ValueError):
            continue
        priority_by_id[record_id] = min(priority, priority_by_id.get(record_id, priority))

    review_items = [
        item
        for item in (validation.get("issues") or [])
        if isinstance(item, dict) and item.get("severity") == "review"
    ]
    blocking = 0
    p5_only = 0
    unmapped = 0
    for item in review_items:
        priority = priority_by_id.get(item.get("id"))
        if priority == 5:
            p5_only += 1
        elif priority is not None and priority < 5:
            blocking += 1
        else:
            # A review on a record absent from the current queue cannot safely be
            # classified as historical, so retain it as a P4 blocker.
            unmapped += 1

    reported_total = int(validation.get("reviewCount") or 0)
    unexpanded = max(0, reported_total - len(review_items))
    unmapped += unexpanded
    blocking += unmapped
    return {
        "total": reported_total,
        "blocking": blocking,
        "p5Only": p5_only,
        "unmapped": unmapped,
    }


def status(queue, validation):
    p4 = [row for row in queue['queue'] if row.get('priority') == 4]
    higher = [row for row in queue['queue'] if row.get('priority', 9) < 4]
    p4_revalidation_records, p4_revalidation_fields = _final_revalidation_stats(p4)
    higher_revalidation_records, higher_revalidation_fields = _final_revalidation_stats(higher)
    reviews = _review_gate_stats(queue, validation)
    blocked = bool(p4 or higher or validation['errorCount'] or reviews['blocking'])
    return {
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'p4': {
            'status': 'incomplete' if blocked else 'complete',
            'actionableRecords': len(p4),
            'higherPriorityRecords': len(higher),
            'semanticErrors': validation['errorCount'],
            'sourceReviewItems': reviews['total'],
            'blockingSourceReviewItems': reviews['blocking'],
            'p5OnlySourceReviewItems': reviews['p5Only'],
            'unmappedSourceReviewItems': reviews['unmapped'],
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
