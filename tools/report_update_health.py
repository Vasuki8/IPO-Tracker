"""Read-only operational freshness, not source accuracy or publication authority.

Use an explicit assessment instant. Print JSON or Markdown; never collect sources, change
reviews or publish. Optional GitHub run/jobs snapshots diagnose unpublished work.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
from datetime import date, datetime, timezone
import json
import math
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconcile_pending_updates import (ROOT, SUBSCRIPTION_FIELDS, clock, digest,
                                       encoded, equal, read_json, subscription_evidence)
import reconcile_pending_updates as reconciliation

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
SOURCE_STAGES = {
    'NSE-live': 'run_update_final_policy.py', 'NSE-history': 'run_update_final_policy.py',
    'BSE': 'run_update_final_policy.py', 'SEBI': 'run_update_final_policy.py',
    'IPO-subscription': 'run_priority_subscriptions_v3.py',
    'Issuer-offer-docs': 'run_issuer_offer_docs.py',
    'SEBI-document-links': 'enrich_sebi_document_links.py',
    'SEBI-priority-registers': 'enrich_sebi_priority_registers_v2.py'}
SOURCE_AUTHORITY = {
    'NSE-live': 'official_exchange', 'NSE-history': 'official_exchange', 'BSE': 'official_exchange',
    'SEBI': 'official_regulator', 'SEBI-document-links': 'document_specific',
    'SEBI-priority-registers': 'official_regulator', 'Issuer-offer-docs': 'document_specific',
    'IPO-subscription': 'per_snapshot_official_secondary_or_unknown'}
OUTCOME_ACTIONS = {
    'successful': 'A recorded success is not source freshness or field verification; inspect independent clocks and reviews.',
    'failed': 'Inspect the recorded failure and original run; preserve accepted values before an authorized retry.',
    'partial_failure': 'Review failed items individually; successful items do not clear the failures.',
    'source_blocked': 'Inspect the retained source/parser diagnostic; do not convert a blocked attempt into permanent unavailability.',
    'source_unavailable': 'Retain the unavailable source and unknown values; seek matching official evidence without declaring completion.',
    'deferred': 'Resume through the existing bounded collector when due; no collection success is implied.',
    'degraded': 'Review the actual source authority and observation time; secondary fallback is not official freshness.',
    'invalid': 'Inspect malformed or contradictory operational metadata; no successful collection is established.',
    'unknown': 'Inspect missing outcome evidence; do not infer success from a build timestamp or zero rows.'}


def recorded_outcome(value):
    """Same recorded-outcome contract as source-health.js; not a freshness claim."""
    if not isinstance(value, dict) or not value:
        return 'unknown'
    for key in ('ok', 'degraded', 'available'):
        if key in value and type(value[key]) is not bool:
            return 'invalid'
    if ('failed' in value and (type(value['failed']) not in (int, float) or not math.isfinite(value['failed']) or value['failed'] < 0)
            or value.get('exitCode') is not None and type(value['exitCode']) is not int):
        return 'invalid'
    status = value.get('status')
    if status in {'source_unavailable', 'unavailable'} or value.get('available') is False:
        return 'source_unavailable'
    if status == 'source_blocked':
        return 'source_blocked'
    failed = (value.get('ok') is False or status in {'failed', 'failure', 'timed_out', 'cancelled'}
              or bool(value.get('error')) or bool(value.get('errors'))
              or (value.get('failed') or 0) > 0 or (value.get('exitCode') or 0) != 0)
    if failed:
        return 'partial_failure' if type(value.get('failed')) in (int, float) and value['failed'] > 0 and value.get('ok') is True else 'failed'
    if status == 'deferred':
        return 'deferred'
    if value.get('degraded') is True:
        return 'degraded'
    if status not in (None, 'updated', 'no_change', 'completed', 'checked', 'refreshed'):
        return 'unknown'
    if value.get('ok') is True or status in {'updated', 'no_change', 'completed', 'checked', 'refreshed'}:
        return 'successful'
    return 'unknown'


def check_clock(value):
    """An explicit missing/invalid check clock cannot borrow the build clock."""
    value = value if isinstance(value, dict) else {}
    clocks = {k: value[k] for k in ('checkedAt', 'asOf') if k in value}
    chosen = value.get('checkedAt', value.get('asOf'))
    checks = {k: clock(v) for k, v in clocks.items()}
    conflict = len(checks) == 2 and checks['checkedAt'] != checks['asOf']
    return {'state': 'conflicting_check_clocks' if conflict else clock(chosen)['status'],
            'stored': chosen, 'storedClocks': clocks}


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
    recorded_clock = check_clock(value)
    check_age = age(recorded_clock['stored'], now, limit, due=due)
    if recorded_clock['state'] == 'conflicting_check_clocks':
        check_age['state'] = 'conflicting_check_clocks'
    collection_outcome = recorded_outcome(value)
    malformed = collection_outcome == 'invalid'
    failure = collection_outcome in {'failed', 'partial_failure', 'source_blocked', 'source_unavailable'}
    outcome = value.get('status', 'reported_ok' if value.get('ok') is True else 'unknown')
    return {'name': name, 'monitoring': kind or 'recorded_only', 'reportedOutcome': outcome,
            'exitCode': value.get('exitCode'), 'durationSeconds': value.get('durationSeconds'),
            'failureEvidence': failure, 'degraded': value.get('degraded') is True,
            'counts': {k: value[k] for k in ('attempted', 'failed', 'remaining', 'records') if k in value},
            'storedCheckClocks': recorded_clock['storedClocks'], 'attemptFreshness': check_age,
            'collectionOutcome': collection_outcome,
            'latestFailureOrDeferredReason': {k: copy.deepcopy(value[k]) for k in ('reason', 'error', 'errors', 'diagnostics', 'warnings')
                if value.get(k)} if collection_outcome != 'successful' else {},
            'lastSuccessfulRecordedOutcome': {'status': outcome, 'checkedAt': recorded_clock['stored']}
                if collection_outcome == 'successful' and recorded_clock['state'] == 'valid' else None,
            'requiresInvestigation': bool((malformed and kind and due) or failure or value.get('degraded') is True or outcome == 'deferred'
                or (kind and due and collection_outcome == 'unknown')
                or (kind and due and check_age['state'] not in {'within_tolerance'})),
            'evidenceSha256': digest(encoded(value)),
            'nextAction': OUTCOME_ACTIONS[collection_outcome]}


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
        # The recorded run ID is not a clock. Successful job evidence supplies
        # a bounded publication window, never an invented commit timestamp.
        publisher = selected.get('publish', {})
        collector = selected.get('collect', {})
        result['publisherWindow'] = publisher_window(publisher if result['state'] == 'accepted_run_matches' else {}, now)
        result['collectionToPublisherCompletion'] = (elapsed_interval(
            collector.get('completed_at'), publisher.get('completed_at'), now)
            if result['publisherWindow']['state'] == 'bound_successful_publisher' and collector.get('conclusion') == 'success'
            else {'state': 'unknown', 'minutes': None})
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


def elapsed_interval(start, end, now):
    first, last = clock(start), clock(end)
    if first['status'] != 'valid' or last['status'] != 'valid':
        return {'state': 'unknown', 'minutes': None}
    a, b = instant(start), instant(end)
    if a > b or b > now:
        return {'state': 'inconsistent', 'minutes': None}
    return {'state': 'recorded_interval', 'minutes': round((b-a).total_seconds()/60, 3),
            'from': start, 'to': end}


def publisher_window(publisher, now):
    start, end = publisher.get('started_at'), publisher.get('completed_at')
    interval = elapsed_interval(start, end, now)
    valid = publisher.get('status') == 'completed' and publisher.get('conclusion') == 'success' and interval['state'] == 'recorded_interval'
    return {'state': 'bound_successful_publisher' if valid else 'publisher_time_not_verified',
            'startedAt': start if valid else None, 'completedAt': end if valid else None,
            'acceptedAt': None,
            'meaning': 'Publisher execution window; exact accepted commit time is not recorded in canonical publication metadata.'}


def proposal_health(pending_report, bundles, now):
    if pending_report is None:
        return {'state': 'not_supplied', 'retainedProposals': None, 'entries': []}
    if bundles is not None and not isinstance(bundles, list):
        raise ValueError('Proposal workflow evidence must be an array')
    origins = {}
    for bundle in bundles or []:
        if not isinstance(bundle, dict):
            raise ValueError('Malformed proposal workflow bundle')
        run, jobs = bundle.get('run'), bundle.get('jobs')
        # Reuse the existing strict repository/workflow/attempt/page binding.
        evidence = workflow_delivery({}, run, jobs, now)
        key = str(run['id'])
        if key in origins:
            raise ValueError('Duplicate proposal workflow evidence')
        publisher = evidence['jobs'].get('publish', {})
        origins[key] = publisher_window(publisher, now)
    entries = []
    for proposal in pending_report['entries']:
        origin = origins.get(proposal.get('runId'))
        exact = {'state': 'unknown', 'minutes': None, 'reason': 'Retained proposal envelope has no creation timestamp.'}
        age_bounds = None
        if origin and origin['state'] == 'bound_successful_publisher':
            age_bounds = {'minimumMinutes': age(origin['completedAt'], now)['ageMinutes'],
                          'maximumMinutes': age(origin['startedAt'], now)['ageMinutes'],
                          'meaning': 'Age of originating publisher execution, not proof of the proposal creation instant or source observation.'}
        entries.append({k: copy.deepcopy(proposal.get(k)) for k in
            ('inputIndex', 'fingerprint', 'runId', 'id', 'path', 'comparisonState', 'nextAction', 'reviewDecisions')}
            | {'proposalAge': exact, 'originatingPublisherAgeRange': age_bounds})
    return {'state': 'retained_unresolved', 'retainedProposals': len(entries), 'resolutionsApplied': 0,
            'summary': copy.deepcopy(pending_report['summary']),
            'reviewDecisionAudit': copy.deepcopy(pending_report.get('reviewDecisionAudit')),
            'exactAgeUnknown': len(entries), 'originatingPublisherWindows': origins,
            'originWindowAvailable': sum(r['originatingPublisherAgeRange'] is not None for r in entries),
            'entries': entries}


def build_report(payload, phase, holds, *, as_of, run=None, jobs=None,
                 pending_report=None, proposal_runs=None, queue=None):
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
    stage_lookup = {s['name']: s for s in stage_rows}
    for source in source_rows:
        value = sources.get(source['name'], {})
        value = value if isinstance(value, dict) else {}
        stage = stage_lookup.get(SOURCE_STAGES.get(source['name']))
        source.update(authority=SOURCE_AUTHORITY.get(source['name'], 'not_assessed'),
            authorityMeaning='Source role only; field authority and issuer binding require separate source review.',
            lastSourceObservation=age(value.get('observedAt'), now),
            observationMeaning='Explicit sourceHealth.observedAt only; no check, build or stage clock fallback.',
            relatedStage=stage['name'] if stage else None,
            lastSuccessfulStageOutcome=copy.deepcopy(stage.get('lastSuccessfulRecordedOutcome')) if stage else None,
            stageHistoryMeaning='Only the latest retained stage outcome is available; a wrapper success is not success of every source.')
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
            'lifecycle': 'active_issue_by_recorded_dates',
            'source': {'label': evidence['sourceLabel'], 'url': evidence['sourceUrl'],
                       'authority': evidence['authority'], 'binding': evidence['sourceBinding']},
            'publicState': evidence.get('publicState'), 'storedClocks': evidence['storedClocks'],
            'observationFreshness': observation_age,
            'observationOlderThanTolerance': observation_age.get('ageMinutes', -1) > LIMITS['subscriptions']
                if observation_age['state'] not in {'source_time_unknown', 'inconsistent_source_clock', 'future_timestamp'} else None,
            'collectionFreshness': collection_age,
            'issues': evidence['issues'], 'snapshotSha256': digest(encoded(group)),
            'finality': evidence['finality'],
            'nextAction': 'Check issue-bound source evidence; collection time cannot supply an observation or final subscription.'})
    publication = meta.get('publication', {})
    if not isinstance(publication, dict):
        raise ValueError('Malformed accepted publication metadata')
    delivery = workflow_delivery(publication, run, jobs, now)
    proposals = proposal_health(pending_report, proposal_runs, now)
    queue_evidence = {'state': 'not_supplied'}
    if queue is not None:
        if not isinstance(queue, dict) or not isinstance(queue.get('queue'), list) or queue.get('queueCount') != len(queue['queue']):
            raise ValueError('Incomplete source-review queue')
        queue_evidence = {'state': 'recorded', 'queuedRecords': queue['queueCount'],
            'sourceReviewItems': sum(row.get('sourceReviewCount', 0) for row in queue['queue']),
            'generatedAt': queue.get('generatedAt'), 'meaning': 'Retained review counts, not resolution or freshness.'}
    for source in source_rows:
        source['lastAcceptedPublication'] = {'runId': publication.get('runId'), 'acceptedAt': None,
            'publisherWindow': copy.deepcopy(delivery.get('publisherWindow')),
            'scope': 'Dataset publisher evidence; per-source acceptance time is not recorded.'}
        source['publicationLag'] = copy.deepcopy(delivery.get('collectionToPublisherCompletion', {'state': 'unknown', 'minutes': None}))
    return {'schemaVersion': 2, 'scope': 'read-only-recorded-operational-health-not-source-accuracy',
        'asOf': now.isoformat(), 'mutationsApplied': 0,
        'policy': {'thresholdMinutes': LIMITS, 'subscriptionDeadlineActive': subscription_deadline(now),
                   'scheduleBasis': 'configured UTC weekdays, not an exchange holiday/session calendar',
                   'missingSourceTimeIsFresh': False, 'alertsConfigured': False},
        'acceptedPublication': {'metadata': copy.deepcopy(publication),
            'acceptedAt': None,
            'snapshotAge': age(meta.get('generatedAt'), now, LIMITS['core']),
            'timestampMeaning': 'accepted snapshot generation; not individual source observation or deployed-at time',
            'delivery': delivery,
            'liveDeployment': 'not_assessed_by_this_offline_report'},
        'stages': stage_rows, 'sources': source_rows, 'subscriptions': subscriptions,
        'proposals': proposals, 'sourceReviewQueue': queue_evidence,
        'summary': {'canonicalRecords': len(rows), 'lifecycleScopes': dict(sorted(Counter(scopes).items())),
            'openSubscriptions': len(subscriptions),
            'observationStates': dict(sorted(Counter(r['observationFreshness']['state'] for r in subscriptions).items())),
            'collectionStates': dict(sorted(Counter(r['collectionFreshness']['state'] for r in subscriptions).items())),
            'sourceOutcomes': dict(sorted(Counter(r.get('collectionOutcome', 'unknown') for r in source_rows).items())),
            'stageOutcomes': dict(sorted(Counter(r.get('collectionOutcome', 'unknown') for r in stage_rows).items())),
            'overdueSourceChecks': sum(r['attemptFreshness']['state'] == 'overdue' for r in source_rows),
            'overdueStages': sum(r['attemptFreshness']['state'] == 'overdue' for r in stage_rows),
            'observationsOlderThanTolerance': sum(r['observationOlderThanTolerance'] is True for r in subscriptions),
            'unresolvedProposals': proposals['retainedProposals'],
            'stagesNeedingInvestigation': sum(r['requiresInvestigation'] for r in stage_rows),
            'sourcesNeedingInvestigation': sum(r['requiresInvestigation'] for r in source_rows)},
        'phaseGateEvidence': copy.deepcopy(phase),
        'limitations': ['No source collection, accepted correction, proposal resolution or phase advancement.',
            'Recorded stage outcomes can outlive the run that produced them; unpublished failures need separate run/job evidence.',
            'No historical success clock is invented when the latest retained outcome failed or was deferred.',
            'Proposal creation and exact accepted-commit timestamps are absent; workflow execution windows remain separately labelled.',
            'Within tolerance describes clock age only, never source success or accurate financial values.',
            'Unknown/invalid lifecycle dates remain counted; no live deadline is guessed for those records.',
            'Successful no-change runs need not create a publication; an old snapshot alone does not prove publication delay.']}


def from_files(data, phase, *, as_of, run_path=None, jobs_path=None,
               pending_path=None, queue_path=None, proposal_runs_path=None):
    if bool(run_path) != bool(jobs_path):
        raise ValueError('Supply both --workflow-run and --workflow-jobs')
    paths = {'canonical': Path(data), 'phase': Path(phase), 'displayHolds': ROOT / 'data/public_display_holds.json',
             'pending': Path(pending_path or ROOT / 'data/pending_updates.json'),
             'sourceReviewQueue': Path(queue_path or ROOT / 'data/missing_queue.json')}
    if run_path:
        paths.update(workflowRun=Path(run_path), workflowJobs=Path(jobs_path))
    if proposal_runs_path:
        paths['proposalWorkflows'] = Path(proposal_runs_path)
    raw = {k: p.read_bytes() for k, p in paths.items()}
    parsed = {k: read_json(v) for k, v in raw.items()}
    pending_report = reconciliation.report_from_files(paths['canonical'], paths['pending'],
        as_of=instant(as_of).astimezone(ZoneInfo('Asia/Kolkata')).date())
    if any(pending_report['inputSha256'][k] != digest(raw[ours]) for k, ours in
           (('canonical', 'canonical'), ('pending', 'pending'), ('displayHolds', 'displayHolds'))):
        raise ValueError('Operational inputs changed during reconciliation')
    report = build_report(parsed['canonical'], parsed['phase'], parsed['displayHolds']['holds'],
                          as_of=as_of, run=parsed.get('workflowRun'), jobs=parsed.get('workflowJobs'),
                          pending_report=pending_report, proposal_runs=parsed.get('proposalWorkflows'),
                          queue=parsed['sourceReviewQueue'])
    report['proposalReconciliationInputs'] = {'inputSha256': pending_report['inputSha256'],
        'codePolicySha256': pending_report['codePolicySha256'], 'reviewDecisionInputs': pending_report['reviewDecisionInputs']}
    report['inputSha256'] = {k: digest(v) for k, v in raw.items()}
    dependencies = [*sorted((ROOT / 'scripts').rglob('*.py')), *sorted((ROOT / 'tools').glob('*.py')),
                    ROOT / 'pyproject.toml', ROOT / 'uv.lock', ROOT / '.github/workflows/refresh.yml']
    schedule = (ROOT / '.github/workflows/refresh.yml').read_text(encoding='utf-8')
    crons = set(re.findall(r'''^\s*-\s*cron:\s*['"]([^'"]+)['"]\s*$''', schedule, re.MULTILINE))
    if crons != {'17 * * * *', '0,30 4-12 * * 1-5', '43 13 * * *', '31 */6 * * *'}:
        raise ValueError('Collection schedule changed; review operational tolerances before reporting')
    report['codePolicySha256'] = digest(encoded({p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in dependencies}))
    return report


def markdown_report(report):
    """A view of the same immutable report, not a second operational state store."""
    def cell(value):
        if value is None:
            return 'unknown'
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, sort_keys=True)
        return str(value).replace('|', '&#124;').replace('\r', ' ').replace('\n', ' ')

    def clock_cell(value):
        return f"{cell(value.get('stored'))} ({cell(value.get('state'))})"

    def table(headers, rows):
        return ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |',
                *['| ' + ' | '.join(cell(v) for v in row) + ' |' for row in rows], '']

    summary, publication = report['summary'], report['acceptedPublication']
    lines = ['# Recorded operational health', '', f"Assessed at **{report['asOf']}**. Frozen evidence, not live monitoring.", '',
        'Source observation, collection attempts, publisher execution and exact acceptance are separate clocks. Missing clocks stay unknown.', '',
        '## Counts', '']
    lines += table(['Signal', 'Count / state'], summary.items())
    lines += ['## Publication', '',
        f"Recorded dataset publisher: {cell(publication['metadata'])}.", '',
        'Exact accepted publication time: **unknown**. Publisher execution does not establish per-source acceptance or deployment.', '',
        f"Delivery evidence: {cell(publication['delivery'])}.", '',
        '## Sources', '',
        'Check clocks describe collection attempts. Source roles do not establish field-level authority. Retained older entries remain visible without an invented cadence.', '']
    lines += table(['Source / authority', 'Observation', 'Last check / freshness', 'Outcome', 'Latest retained successful stage', 'Failure / deferral evidence', 'Next action'],
        ([f"{r['name']} / {r['authority']}", clock_cell(r['lastSourceObservation']), clock_cell(r['attemptFreshness']),
          r.get('collectionOutcome', 'unknown'), r['lastSuccessfulStageOutcome'], r.get('latestFailureOrDeferredReason', {}), r.get('nextAction', 'Inspect malformed metadata.')]
         for r in report['sources']))
    lines += ['## Stage outcomes', '']
    lines += table(['Stage', 'Last check / freshness', 'Outcome', 'Failure / deferral evidence'],
        ([r['name'], clock_cell(r['attemptFreshness']), r.get('collectionOutcome', 'unknown'), r.get('latestFailureOrDeferredReason', {})]
         for r in report['stages']))
    lines += ['## Active subscriptions', '',
        'Scope follows recorded offer dates in Asia/Kolkata. Outside monitoring hours does not make an old observation current. Provisional snapshots do not become final.', '']
    lines += table(['Issuer', 'Source / authority', 'Observation', 'Collection', 'Public state / finality', 'Next action'],
        ([r['id'], r['source'], clock_cell(r['observationFreshness']), clock_cell(r['collectionFreshness']),
          {'publicState': r['publicState'], 'finality': r['finality']}, r['nextAction']] for r in report['subscriptions']))
    proposals = report['proposals']
    lines += ['## Retained proposals and reviews', '',
        f"Unresolved envelopes: **{cell(proposals['retainedProposals'])}**. Exact creation age unknown: **{cell(proposals.get('exactAgeUnknown'))}**. Resolutions applied: **0**.", '',
        f"Comparison summary: {cell(proposals.get('summary'))}.", '',
        f"Source-review queue: {cell(report['sourceReviewQueue'])}.", '',
        'Each envelope, comparison, review decision and next action is retained in the JSON report. Originating publisher windows are supporting workflow evidence, not exact proposal creation times.', '']
    lines += table(['Origin run', 'Publisher start', 'Publisher end', 'Window state'],
        ([key, value['startedAt'], value['completedAt'], value['state']]
         for key, value in proposals.get('originatingPublisherWindows', {}).items()))
    lines += ['## Limitations', '', *['- ' + item for item in report['limitations']], '',
        'Reproduce the JSON report with the original input files and assessment instant. A successful replay does not declare it fresh now.', '']
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT / 'data/ipos.json')
    parser.add_argument('--phase', type=Path, default=ROOT / 'data/phase_status.json')
    parser.add_argument('--as-of', help='Required zoned assessment instant, unless replaying --check-report')
    parser.add_argument('--workflow-run', type=Path, help='Raw GitHub refresh workflow run JSON')
    parser.add_argument('--workflow-jobs', type=Path, help='Complete raw jobs JSON for that run attempt')
    parser.add_argument('--pending', type=Path, default=ROOT / 'data/pending_updates.json')
    parser.add_argument('--queue', type=Path, default=ROOT / 'data/missing_queue.json')
    parser.add_argument('--proposal-workflows', type=Path, help='JSON array of retained origin {run, jobs} snapshots; no automatic polling')
    parser.add_argument('--format', choices=('json', 'markdown'), default='json', help='Output view; replay always checks the JSON report')
    parser.add_argument('--check-report', type=Path, help='Reproduce a report at its original assessment instant, not declare it fresh now')
    args = parser.parse_args(argv)
    try:
        prior = read_json(args.check_report.read_bytes()) if args.check_report else None
        at = args.as_of or (prior['asOf'] if prior else None)
        report = from_files(args.data, args.phase, as_of=at, run_path=args.workflow_run, jobs_path=args.workflow_jobs,
                            pending_path=args.pending, queue_path=args.queue, proposal_runs_path=args.proposal_workflows)
        if prior is not None:
            if not equal(prior, report):
                raise ValueError('Report inputs, policy or content changed; regenerate for the intended assessment instant')
            print(json.dumps({'status': 'reproduced', 'asOf': report['asOf'], 'freshNow': 'not_asserted'}))
        else:
            print(markdown_report(report) if args.format == 'markdown' else json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
