"""Read-only operational freshness, not source accuracy or publication authority.

Use an explicit assessment instant. Print JSON only; never collect sources, change
reviews or publish. Optional GitHub run/jobs snapshots diagnose unpublished work.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconcile_pending_updates import (ROOT, SUBSCRIPTION_FIELDS, clock, digest,
                                       encoded, equal, read_json, subscription_evidence)

REPOSITORY = 'Vasuki8/IPO-Tracker'
# Operator tolerances, NOT exchange sessions, source SLAs or proof of missed runs.
# Core is hourly; subscriptions are scheduled 04:00–12:30 UTC weekdays. Filings
# have a six-hour fallback and are conditional on high-priority repair work.
LIMITS = {'core': 120, 'subscriptions': 90, 'filings': 480, 'publication': 30}
STAGES = {'run_update_final_policy.py': 'core',
          'run_priority_subscriptions_v3.py': 'subscriptions',
          'enrich_sebi_priority_registers_v2.py': 'filings',
          'enrich_sebi_document_links.py': 'filings',
          'collect_nse_offer_filings_final_policy.py': 'filings',
          'run_offer_documents.py': 'filings', 'run_issuer_offer_docs.py': 'filings'}
SOURCES = {'NSE-live': 'core', 'BSE': 'core', 'SEBI': 'core',
           'IPO-subscription': 'subscriptions', 'Issuer-offer-docs': 'filings',
           'SEBI-document-links': 'filings', 'SEBI-priority-registers': 'filings'}


def instant(value):
    checked = clock(value)
    if checked['status'] != 'valid':
        raise ValueError('Assessment/evidence needs a valid timezone-aware timestamp')
    return datetime.fromisoformat(checked['utc'])


def age(value, now, limit=None, *, due=True):
    result = {'stored': copy.deepcopy(value), 'thresholdMinutes': limit}
    checked = clock(value)
    if checked['status'] != 'valid':
        return {**result, 'state': checked['status']}
    minutes = (now - datetime.fromisoformat(checked['utc'])).total_seconds() / 60
    if minutes < 0:
        state = 'future_timestamp'
    elif limit is None:
        state = 'recorded_only'
    elif not due:
        state = 'outside_monitoring_deadline'
    else:
        state = 'overdue' if minutes > limit else 'within_tolerance'
    return {**result, 'state': state, 'ageMinutes': round(minutes, 3)}


def subscription_deadline(now):
    utc = now.astimezone(timezone.utc)
    # First 04:00 scheduled attempt receives the same 90-minute grace. After
    # the last 12:30 attempt + grace, no continuous intraday SLA is implied.
    minute = utc.hour * 60 + utc.minute
    return utc.weekday() < 5 and 330 <= minute <= 840


def lifecycle(row, today):
    if str(row.get('status') or '').lower() in {'listed', 'withdrawn', 'cancelled', 'postponed'}:
        return 'not_live_status'
    try:
        opens, closes = (date.fromisoformat(row[k]) for k in ('openDate', 'closeDate'))
        if opens > closes:
            return 'invalid_dates'
    except (ValueError, TypeError, KeyError):
        return 'unknown_dates'
    return 'before_open' if today < opens else 'after_close' if today > closes else 'open_by_recorded_dates'


def health_entry(name, value, kind, now, active, filing_work):
    if not isinstance(value, dict):
        return {'name': name, 'reportedOutcome': 'malformed', 'requiresInvestigation': True,
                'attemptFreshness': {'state': 'invalid'}, 'evidenceSha256': digest(encoded(value))}
    limit = LIMITS.get(kind)
    due = kind != 'subscriptions' or (active and subscription_deadline(now))
    if kind == 'filings' and not filing_work:
        due = False
    # Retain disagreements; do not pick the newest of two conflicting clocks.
    clocks = {k: value[k] for k in ('checkedAt', 'asOf') if k in value}
    timestamp = value.get('checkedAt', value.get('asOf'))
    conflicting = (len(clocks) == 2 and clock(clocks['checkedAt']) != clock(clocks['asOf']))
    check_age = age(timestamp, now, limit, due=due)
    if conflicting:
        check_age['state'] = 'conflicting_check_clocks'
    failed = value.get('failed')
    malformed = (('ok' in value and type(value['ok']) is not bool)
                 or ('failed' in value and (type(failed) not in (int, float) or failed < 0))
                 or ('ok' not in value and 'status' not in value)
                 or ('degraded' in value and type(value['degraded']) is not bool)
                 or (value.get('exitCode') is not None and type(value['exitCode']) is not int))
    failure = (value.get('ok') is False or value.get('status') in {'failed', 'source_blocked'}
               or (type(failed) in (int, float) and failed > 0)
               or (type(value.get('exitCode')) is int and value['exitCode'] != 0))
    outcome = value.get('status', 'reported_ok' if value.get('ok') is True else 'unknown')
    return {'name': name, 'monitoring': kind or 'recorded_only', 'reportedOutcome': outcome,
            'exitCode': value.get('exitCode'), 'durationSeconds': value.get('durationSeconds'),
            'failureEvidence': failure, 'degraded': value.get('degraded') is True,
            'counts': {k: value[k] for k in ('attempted', 'failed', 'remaining', 'records') if k in value},
            'storedCheckClocks': clocks, 'attemptFreshness': check_age,
            'requiresInvestigation': bool((malformed and kind and due) or failure or value.get('degraded') is True or outcome == 'deferred'
                or (kind and due and outcome == 'unknown')
                or (kind and due and check_age['state'] not in {'within_tolerance'})),
            'evidenceSha256': digest(encoded(value)),
            'nextAction': 'Inspect the recorded outcome and original run; a recent attempt is not source success.'}


def workflow_delivery(publication, run, jobs, now):
    if run is None and jobs is None:
        return {'state': 'not_assessed', 'reason': 'No unpublished workflow evidence supplied; snapshot age alone cannot establish publication delay.'}
    if (not isinstance(run, dict) or not isinstance(jobs, dict)
            or run.get('repository', {}).get('full_name') != REPOSITORY
            or run.get('head_repository', {}).get('full_name') != REPOSITORY
            or run.get('event') not in {'push', 'schedule', 'workflow_dispatch'}
            or run.get('head_branch') != 'main' or run.get('path') != '.github/workflows/refresh.yml'
            or type(run.get('id')) is not int or run['id'] <= 0
            or type(run.get('run_attempt')) is not int or run['run_attempt'] < 1
            or not re.fullmatch(r'[a-f0-9]{40}', str(run.get('head_sha', '')))):
        raise ValueError('Unbound or malformed collector workflow evidence')
    items = jobs.get('jobs')
    if (not isinstance(items, list) or type(jobs.get('total_count')) is not int
            or jobs['total_count'] != len(items)):
        raise ValueError('Incomplete workflow jobs page; supply all jobs for the attempt')
    selected = {}
    for job in items:
        if (not isinstance(job, dict) or job.get('run_id') != run['id']
                or job.get('run_attempt') != run['run_attempt']):
            raise ValueError('Workflow jobs belong to a different run or attempt')
        if job.get('name') in {'collect', 'publish'}:
            if job['name'] in selected:
                raise ValueError('Ambiguous collector/publication jobs')
            selected[job['name']] = job
    result = {'runId': str(run['id']), 'collectorCommit': run['head_sha'],
              'runAttempt': run['run_attempt'], 'recordedRunStatus': run.get('status'),
              'recordedRunConclusion': run.get('conclusion'), 'recordedRunUpdatedAt': run.get('updated_at'),
              'jobs': {k: {a: v.get(a) for a in ('status', 'conclusion', 'started_at', 'completed_at')}
                       for k, v in selected.items()},
              'scope': 'supplied-workflow-snapshot-not-live-polling-or-source-acceptance'}
    if str(run['id']) == publication.get('runId'):
        result['state'] = ('accepted_run_matches' if run['head_sha'] == publication.get('collectorCommit')
                           and publication.get('status') in {'published', 'published_with_pending_conflicts'}
                           else 'acceptance_binding_conflict')
        return result
    collector, publisher = selected.get('collect', {}), selected.get('publish', {})
    if collector.get('conclusion') in {'failure', 'timed_out', 'cancelled', 'skipped'}:
        result['state'] = 'collection_' + collector['conclusion']
    elif collector.get('status') != 'completed' or collector.get('conclusion') != 'success':
        result['state'] = 'collection_unfinished_or_unknown'
    else:
        waiting = age(collector.get('completed_at'), now, LIMITS['publication'])
        result['timeSinceCollectionCompleted'] = waiting
        start, end = clock(collector.get('started_at')), clock(collector.get('completed_at'))
        if (waiting['state'] in {'missing', 'invalid', 'future_timestamp'}
                or start['status'] != 'valid'
                or datetime.fromisoformat(start['utc']) > datetime.fromisoformat(end['utc'])):
            result['state'] = 'collection_completion_time_unknown'
        elif publisher.get('conclusion') in {'failure', 'timed_out', 'cancelled', 'skipped'}:
            result['state'] = 'publication_' + publisher['conclusion']
        elif publisher.get('status') == 'completed' or run.get('status') == 'completed':
            # A successful no-change run creates no new accepted run ID. Nor
            # can this report prove which concurrent data-only run superseded it.
            result['state'] = 'completed_without_matching_acceptance'
        elif run.get('status') in {'queued', 'in_progress', 'waiting', 'pending'}:
            result['state'] = ('recorded_publication_overdue' if waiting['state'] == 'overdue'
                               else 'recorded_publication_waiting')
        else:
            result['state'] = 'publication_state_unknown'
    result['nextAction'] = 'Inspect this run and retained bundle; source-manifest validation and source review still govern any retry.'
    return result


def build_report(payload, phase, holds, *, as_of, run=None, jobs=None):
    now = instant(as_of)
    if (not isinstance(payload, dict) or not isinstance(payload.get('meta'), dict)
            or not isinstance(payload.get('ipos'), list) or not isinstance(phase, dict)):
        raise ValueError('Missing accepted dataset or phase evidence')
    rows, meta = payload['ipos'], payload['meta']
    if any(not isinstance(r, dict) or not isinstance(r.get('id'), str) or not r['id'] for r in rows):
        raise ValueError('Malformed canonical issuer identity')
    if len({r['id'] for r in rows}) != len(rows) or meta.get('recordCount') != len(rows):
        raise ValueError('Ambiguous or incomplete canonical inventory')
    today = now.astimezone(ZoneInfo('Asia/Kolkata')).date()
    scopes = [lifecycle(r, today) for r in rows]
    live = [r for r, scope in zip(rows, scopes) if scope == 'open_by_recorded_dates']
    filing_work = (phase.get('p4', {}).get('higherPriorityRecords') or 0) > 0
    stages, sources = meta.get('pipelineStages', {}), meta.get('sourceHealth', {})
    if not isinstance(stages, dict) or not isinstance(sources, dict):
        raise ValueError('Malformed operational evidence inventory')
    stage_rows = [health_entry(k, stages.get(k, {}), STAGES.get(k), now, bool(live), filing_work)
                  for k in sorted(set(stages) | set(STAGES))]
    source_rows = [health_entry(k, sources.get(k, {}), SOURCES.get(k), now, bool(live), filing_work)
                   for k in sorted(set(sources) | set(SOURCES))]
    subscriptions = []
    for row in live:
        group = {k: row[k] for k in SUBSCRIPTION_FIELDS if k in row}
        evidence = subscription_evidence(row, group, as_of=today, holds=holds)
        due = subscription_deadline(now)
        observed = evidence['observed']
        observation_age = age(observed.get('utc'), now, LIMITS['subscriptions'], due=due)
        if observed['status'] != 'valid':
            observation_age['state'] = 'source_time_unknown'
        elif 'source_observation_after_collection' in evidence['issues']:
            observation_age['state'] = 'inconsistent_source_clock'
        collection_age = age(evidence['collected'].get('utc'), now, LIMITS['subscriptions'], due=due)
        if 'collection_alias_disagrees' in evidence['issues']:
            collection_age['state'] = 'conflicting_collection_clocks'
        subscriptions.append({'id': row['id'], 'company': row.get('company'),
            'openDate': row['openDate'], 'closeDate': row['closeDate'],
            'source': {'label': evidence['sourceLabel'], 'url': evidence['sourceUrl'],
                       'authority': evidence['authority'], 'binding': evidence['sourceBinding']},
            'publicState': evidence.get('publicState'), 'storedClocks': evidence['storedClocks'],
            'observationFreshness': observation_age,
            'collectionFreshness': collection_age,
            'issues': evidence['issues'], 'snapshotSha256': digest(encoded(group)),
            'finality': evidence['finality'],
            'nextAction': 'Check issue-bound source evidence; collection time cannot supply an observation or final subscription.'})
    publication = meta.get('publication', {})
    if not isinstance(publication, dict):
        raise ValueError('Malformed accepted publication metadata')
    return {'schemaVersion': 1, 'scope': 'read-only-recorded-operational-health-not-source-accuracy',
        'asOf': now.isoformat(), 'mutationsApplied': 0,
        'policy': {'thresholdMinutes': LIMITS, 'subscriptionDeadlineActive': subscription_deadline(now),
                   'scheduleBasis': 'configured UTC weekdays, not an exchange holiday/session calendar',
                   'missingSourceTimeIsFresh': False, 'alertsConfigured': False},
        'acceptedPublication': {'metadata': copy.deepcopy(publication),
            'snapshotAge': age(meta.get('generatedAt'), now, LIMITS['core']),
            'timestampMeaning': 'accepted snapshot generation; not individual source observation or deployed-at time',
            'delivery': workflow_delivery(publication, run, jobs, now),
            'liveDeployment': 'not_assessed_by_this_offline_report'},
        'stages': stage_rows, 'sources': source_rows, 'subscriptions': subscriptions,
        'summary': {'canonicalRecords': len(rows), 'lifecycleScopes': dict(sorted(Counter(scopes).items())),
            'openSubscriptions': len(subscriptions),
            'observationStates': dict(sorted(Counter(r['observationFreshness']['state'] for r in subscriptions).items())),
            'collectionStates': dict(sorted(Counter(r['collectionFreshness']['state'] for r in subscriptions).items())),
            'stagesNeedingInvestigation': sum(r['requiresInvestigation'] for r in stage_rows),
            'sourcesNeedingInvestigation': sum(r['requiresInvestigation'] for r in source_rows)},
        'phaseGateEvidence': copy.deepcopy(phase),
        'limitations': ['No source collection, accepted correction, proposal resolution or phase advancement.',
            'Recorded stage outcomes can outlive the run that produced them; unpublished failures need separate run/job evidence.',
            'Within tolerance describes clock age only, never source success or accurate financial values.',
            'Unknown/invalid lifecycle dates remain counted; no live deadline is guessed for those records.',
            'Successful no-change runs need not create a publication; an old snapshot alone does not prove publication delay.']}


def from_files(data, phase, *, as_of, run_path=None, jobs_path=None):
    if bool(run_path) != bool(jobs_path):
        raise ValueError('Supply both --workflow-run and --workflow-jobs')
    paths = {'canonical': Path(data), 'phase': Path(phase), 'displayHolds': ROOT / 'data/public_display_holds.json'}
    if run_path:
        paths.update(workflowRun=Path(run_path), workflowJobs=Path(jobs_path))
    raw = {k: p.read_bytes() for k, p in paths.items()}
    parsed = {k: read_json(v) for k, v in raw.items()}
    report = build_report(parsed['canonical'], parsed['phase'], parsed['displayHolds']['holds'],
                          as_of=as_of, run=parsed.get('workflowRun'), jobs=parsed.get('workflowJobs'))
    report['inputSha256'] = {k: digest(v) for k, v in raw.items()}
    dependencies = [*sorted((ROOT / 'scripts').rglob('*.py')), *sorted((ROOT / 'tools').glob('*.py')),
                    ROOT / 'pyproject.toml', ROOT / 'uv.lock', ROOT / '.github/workflows/refresh.yml']
    schedule = (ROOT / '.github/workflows/refresh.yml').read_text(encoding='utf-8')
    crons = set(re.findall(r'''^\s*-\s*cron:\s*['"]([^'"]+)['"]\s*$''', schedule, re.MULTILINE))
    if crons != {'17 * * * *', '0,30 4-12 * * 1-5', '43 13 * * *', '31 */6 * * *'}:
        raise ValueError('Collection schedule changed; review operational tolerances before reporting')
    report['codePolicySha256'] = digest(encoded({p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in dependencies}))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT / 'data/ipos.json')
    parser.add_argument('--phase', type=Path, default=ROOT / 'data/phase_status.json')
    parser.add_argument('--as-of', help='Required zoned assessment instant, unless replaying --check-report')
    parser.add_argument('--workflow-run', type=Path, help='Raw GitHub refresh workflow run JSON')
    parser.add_argument('--workflow-jobs', type=Path, help='Complete raw jobs JSON for that run attempt')
    parser.add_argument('--check-report', type=Path, help='Reproduce a report at its original assessment instant, not declare it fresh now')
    args = parser.parse_args(argv)
    try:
        prior = read_json(args.check_report.read_bytes()) if args.check_report else None
        at = args.as_of or (prior['asOf'] if prior else None)
        report = from_files(args.data, args.phase, as_of=at, run_path=args.workflow_run, jobs_path=args.workflow_jobs)
        if prior is not None:
            if not equal(prior, report):
                raise ValueError('Report inputs, policy or content changed; regenerate for the intended assessment instant')
            print(json.dumps({'status': 'reproduced', 'asOf': report['asOf'], 'freshNow': 'not_asserted'}))
        else:
            print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
