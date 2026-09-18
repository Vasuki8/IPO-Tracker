/* Source-health semantics + clickable diagnostics.
 *
 * NSE history can legitimately return zero rows for a checked window (weekends,
 * holidays, or simply no newly listed IPOs). That is healthy, not a refresh
 * failure. This file is loaded immediately after app.js so later Phase 3/4
 * wrappers inherit the corrected renderer and the diagnostics behavior.
 */

const baseSourceHealthRenderer = renderSourceHealth;
let openHealthKey = null;

const SOURCE_HEALTH_INFO = {
  'NSE-live': {
    label: 'NSE-live',
    role: 'Current and upcoming IPO exchange data',
    scope: 'Live/current and upcoming NSE public issues',
    url: 'https://www.nseindia.com/market-data/all-upcoming-issues-ipo'
  },
  'NSE-history': {
    label: 'NSE-history',
    role: 'Historical IPO reconciliation',
    scope: 'Recent NSE past-issue window; the daily job performs the wider reconciliation',
    url: 'https://www.nseindia.com/market-data/all-upcoming-issues-ipo'
  },
  'SEBI': {
    label: 'SEBI',
    role: 'Regulatory filing discovery',
    scope: 'DRHP, UDRHP, RHP and prospectus filings',
    url: 'https://www.sebi.gov.in/filings/public-issues.html'
  },
  'BSE': {
    label: 'BSE',
    role: 'Independent exchange validation',
    scope: 'Current BSE public issues and comparable issue terms',
    url: 'https://www.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=1&Type=p'
  },
  'Offer-docs': {
    label: 'Offer docs',
    role: 'Retained offer-document extraction diagnostics',
    scope: 'Legacy extraction outcomes; completed static terms still require matching Final Prospectus evidence',
    url: 'https://www.sebi.gov.in/filings/public-issues.html'
  },
  'IPO-subscription': {
    label: 'Subscription feed',
    role: 'Live category-wise IPO subscription tracking',
    scope: 'QIB, NII/HNI, Retail/Individual and Total demand snapshots',
    url: 'https://www.nseindia.com/market-data/all-upcoming-issues-ipo'
  },
  'NSE-subscription': {
    label: 'Subscription feed',
    role: 'Live category-wise IPO subscription tracking',
    scope: 'QIB, NII/HNI, Retail/Individual and Total demand snapshots',
    url: 'https://www.nseindia.com/market-data/all-upcoming-issues-ipo'
  }
};

function nseHistoryError(meta) {
  const errors = Array.isArray(meta?.errors) ? meta.errors : [];
  return errors.find(message => String(message).startsWith('NSE history ')) || null;
}

function sourceHealthError(key, health) {
  if (health?.error) return String(health.error);
  const errors = Array.isArray(state.meta?.errors) ? state.meta.errors : [];
  const prefixes = {
    'NSE-live': ['NSE live/upcoming:'],
    'NSE-history': ['NSE history '],
    'SEBI': ['SEBI filings:'],
    'BSE': ['BSE public issues:'],
    'Offer-docs': ['Offer docs:', 'Offer document'],
    'IPO-subscription': ['Subscription ', 'IPO subscription'],
    'NSE-subscription': ['Subscription ', 'IPO subscription']
  }[key] || [];
  return errors.find(message => prefixes.some(prefix => String(message).startsWith(prefix))) || null;
}

function recordedSourceOutcome(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || !Object.keys(value).length) return 'unknown';
  for (const key of ['ok', 'degraded', 'available']) if (key in value && typeof value[key] !== 'boolean') return 'invalid';
  if ('failed' in value && (typeof value.failed !== 'number' || !Number.isFinite(value.failed) || value.failed < 0) || value.exitCode != null && !Number.isInteger(value.exitCode)) return 'invalid';
  const status = value.status;
  if (['source_unavailable', 'unavailable'].includes(status) || value.available === false) return 'source_unavailable';
  if (status === 'source_blocked') return 'source_blocked';
  const errors = Array.isArray(value.errors) ? value.errors.length > 0 : !!value.errors;
  const failed = value.ok === false || ['failed', 'failure', 'timed_out', 'cancelled'].includes(status) || !!value.error || errors || (value.failed || 0) > 0 || (value.exitCode || 0) !== 0;
  if (failed) return typeof value.failed === 'number' && value.failed > 0 && value.ok === true ? 'partial_failure' : 'failed';
  if (status === 'deferred') return 'deferred';
  if (value.degraded === true) return 'degraded';
  if (status != null && !['updated', 'no_change', 'completed', 'checked', 'refreshed'].includes(status)) return 'unknown';
  return value.ok === true || ['updated', 'no_change', 'completed', 'checked', 'refreshed'].includes(status) ? 'successful' : 'unknown';
}

function sourceClockIdentity(value) {
  if (value == null) return {state: 'missing'};
  if (typeof value !== 'string') return {state: 'invalid'};
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(Z|[+-]\d{2}:\d{2})$/);
  if (!match) return {state: 'invalid'};
  const [, y, m, d, h, min, sec, fraction, zone] = match;
  const wall = new Date(0);
  wall.setUTCFullYear(Number(y), Number(m)-1, Number(d));
  wall.setUTCHours(Number(h), Number(min), Number(sec), 0);
  if (Number(y) < 1 || wall.getUTCFullYear() !== Number(y) || wall.getUTCMonth()+1 !== Number(m) || wall.getUTCDate() !== Number(d) || Number(h)>23 || Number(min)>59 || Number(sec)>59) return {state: 'invalid'};
  const offset = zone === 'Z' ? 0 : (Number(zone.slice(1,3))*60 + Number(zone.slice(4))) * (zone[0] === '-' ? -1 : 1);
  if (zone !== 'Z' && (Number(zone.slice(1,3))>23 || Number(zone.slice(4))>59)) return {state: 'invalid'};
  const milliseconds = wall.getTime() - offset*60000;
  // Preserve microsecond differences when comparing aliases, as Python does.
  return {state: 'valid', identity: String(BigInt(milliseconds)*1000n + BigInt((fraction || '').padEnd(6,'0')))};
}

function sourceCheckClock(value) {
  value = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const chosen = 'checkedAt' in value ? value.checkedAt : value.asOf;
  const selected = sourceClockIdentity(chosen);
  if ('checkedAt' in value && 'asOf' in value && JSON.stringify(sourceClockIdentity(value.checkedAt)) !== JSON.stringify(sourceClockIdentity(value.asOf))) return {state: 'conflicting_check_clocks', stored: chosen};
  return {state: selected.state, stored: chosen ?? null};
}

function sourceHealthState(key, health) {
  // Unbound legacy meta.errors can describe a failed fallback before a later
  // success. Retain them as diagnostics, not a replacement for this outcome.
  const outcome = recordedSourceOutcome(health);
  const labels = {successful:'Collection reported', failed:'Collection failed', partial_failure:'Partial failure', source_blocked:'Source blocked', source_unavailable:'Source unavailable', deferred:'Deferred', degraded:'Degraded', invalid:'Invalid metadata', unknown:'Outcome unknown'};
  return {outcome, ok: outcome === 'successful' ? true : ['failed','partial_failure','source_blocked','source_unavailable'].includes(outcome) ? false : null,
    label: labels[outcome], note: health?.note || 'Recorded collection outcome only; source observation time and field verification are separate.'};
}

function renderSourceHealthSemantically() {
  baseSourceHealthRenderer();
  if (!els.health) return;

  scheduleHealthInteractivity();
}

renderSourceHealth = renderSourceHealthSemantically;

function healthKeyFromItem(item) {
  const dataKey = item?.dataset?.health;
  if (dataKey === 'offer-docs') return 'Offer-docs';
  if (dataKey === 'ipo-subscription') {
    return state.meta?.sourceHealth?.['IPO-subscription'] ? 'IPO-subscription' : 'NSE-subscription';
  }

  const label = item?.querySelector('strong')?.textContent?.trim();
  const direct = ['NSE-live', 'NSE-history', 'SEBI', 'BSE'].find(key => key === label);
  if (direct) return direct;
  if (label === 'Offer docs') return 'Offer-docs';
  if (label === 'Subscription feed') {
    return state.meta?.sourceHealth?.['IPO-subscription'] ? 'IPO-subscription' : 'NSE-subscription';
  }
  return null;
}

function scheduleHealthInteractivity() {
  setTimeout(() => {
    if (!els.health) return;
    els.health.querySelectorAll('.health-item').forEach(item => {
      const key = healthKeyFromItem(item);
      if (!key) return;
      const status = sourceHealthState(key, state.meta?.sourceHealth?.[key]);
      const dot = item.querySelector('.health-dot');
      const note = item.querySelector('span:last-child');
      if (dot) dot.className = 'health-dot ' + (status.ok === true ? 'health-ok' : status.ok === false ? 'health-bad' : 'health-unknown');
      if (note) note.textContent = status.label;
      item.dataset.sourceHealthKey = key;
      item.setAttribute('role', 'button');
      item.setAttribute('tabindex', '0');
      item.setAttribute('aria-expanded', openHealthKey === key ? 'true' : 'false');
      item.setAttribute('title', 'Click for source diagnostics');
    });
  }, 0);
}

function healthMetricText(key, health) {
  if (!health) return '—';
  const records = Number(health.records || 0);
  const attempted = Number(health.attempted || 0);
  if ((key === 'IPO-subscription' || key === 'NSE-subscription') && attempted) {
    return `${records.toLocaleString('en-IN')} / ${attempted.toLocaleString('en-IN')} live issues`;
  }
  if (key === 'Offer-docs' && attempted) {
    return `${records.toLocaleString('en-IN')} / ${attempted.toLocaleString('en-IN')} PDFs`;
  }
  return `${records.toLocaleString('en-IN')} row${records === 1 ? '' : 's'}`;
}

function healthExtraDiagnostics(key, health) {
  if (!health) return 'No additional metrics have been recorded.';
  const parts = [];
  if (health.companiesAttached != null) parts.push(`${Number(health.companiesAttached).toLocaleString('en-IN')} companies attached`);
  if (health.attempted != null) parts.push(`${Number(health.attempted).toLocaleString('en-IN')} attempted`);
  if (health.snapshotsAdded != null) parts.push(`+${Number(health.snapshotsAdded).toLocaleString('en-IN')} snapshots`);
  if (health.bseFallbackRecords != null && Number(health.bseFallbackRecords) > 0) parts.push(`${Number(health.bseFallbackRecords).toLocaleString('en-IN')} BSE fallback`);
  if (key === 'NSE-history' && Number(health.records || 0) === 0 && recordedSourceOutcome(health) === 'successful' && !sourceHealthError(key, health)) {
    parts.push('zero rows is valid when no IPO entered the checked history window');
  }
  return parts.length ? parts.join(' · ') : 'No extra diagnostic counters were recorded for this source.';
}

function ensureHealthDetailPanel() {
  let panel = document.getElementById('sourceHealthDetail');
  if (panel) return panel;
  const host = els.health?.parentElement;
  if (!host) return null;
  host.insertAdjacentHTML('beforeend', '<div class="source-health-detail" id="sourceHealthDetail" hidden></div>');
  panel = document.getElementById('sourceHealthDetail');
  return panel;
}

function closeHealthDetail() {
  openHealthKey = null;
  const panel = document.getElementById('sourceHealthDetail');
  if (panel) panel.hidden = true;
  els.health?.querySelectorAll('.health-item').forEach(item => item.setAttribute('aria-expanded', 'false'));
}

function openHealthDetail(key) {
  const panel = ensureHealthDetailPanel();
  if (!panel || !key) return;
  if (openHealthKey === key && !panel.hidden) {
    closeHealthDetail();
    return;
  }

  const health = state.meta?.sourceHealth?.[key];
  const info = SOURCE_HEALTH_INFO[key] || { label: key, role: 'Source authority not assessed', scope: 'Tracker data source', url: null };
  const status = sourceHealthState(key, health);
  const error = sourceHealthError(key, health);
  const checked = sourceCheckClock(health);
  const checkedLabel = checked.state === 'valid' ? formatTimestamp(checked.stored) : checked.state === 'conflicting_check_clocks' ? 'Conflicting check timestamps' : checked.state === 'invalid' ? 'Invalid check timestamp' : 'Not available';
  const statusClass = status.ok === true ? 'ok' : status.ok === false ? 'bad' : 'unknown';
  const refreshNote = health?.note || status.note;

  panel.innerHTML = `
    <div class="health-detail-head">
      <div><div class="health-detail-kicker">Source diagnostics</div><div class="health-detail-title">${escapeHtml(info.label)}</div></div>
      <button class="health-detail-close" type="button" aria-label="Close source diagnostics">×</button>
    </div>
    <div class="health-detail-grid">
      <div class="health-detail-cell"><div class="health-detail-label">Status</div><div class="health-detail-value"><span class="health-detail-status ${statusClass}">${escapeHtml(status.label)}</span></div></div>
      <div class="health-detail-cell"><div class="health-detail-label">Latest result</div><div class="health-detail-value">${escapeHtml(healthMetricText(key, health))}</div></div>
      <div class="health-detail-cell"><div class="health-detail-label">Last source check</div><div class="health-detail-value">${escapeHtml(checkedLabel)}</div></div>
      <div class="health-detail-cell"><div class="health-detail-label">Role</div><div class="health-detail-value">${escapeHtml(info.role)}</div></div>
    </div>
    <div class="health-detail-body">
      <div class="health-detail-section${error ? ' error' : ''}">
        <strong>${error ? 'Retained diagnostic' : 'What happened'}</strong>
        <p>${escapeHtml(error || refreshNote)}</p>
        <p>A collection result does not establish a fresh source observation or verify the issue’s terms. Missing check times remain unavailable.</p>
        ${info.url ? `<a class="health-detail-link" href="${escapeAttr(info.url)}" target="_blank" rel="noopener">Open official source ↗</a>` : ''}
      </div>
      <div class="health-detail-section">
        <strong>Coverage & diagnostics</strong>
        <p>${escapeHtml(info.scope)}<br><br>${escapeHtml(healthExtraDiagnostics(key, health))}</p>
      </div>
    </div>`;

  panel.hidden = false;
  openHealthKey = key;
  els.health.querySelectorAll('.health-item').forEach(item => {
    item.setAttribute('aria-expanded', healthKeyFromItem(item) === key ? 'true' : 'false');
  });
  panel.querySelector('.health-detail-close')?.addEventListener('click', closeHealthDetail, { once: true });
}

function bindSourceHealthDiagnostics() {
  if (!els.health || els.health.dataset.diagnosticsBound === 'true') return;
  els.health.dataset.diagnosticsBound = 'true';
  els.health.addEventListener('click', event => {
    const item = event.target.closest('.health-item');
    if (!item || !els.health.contains(item)) return;
    openHealthDetail(healthKeyFromItem(item));
  });
  els.health.addEventListener('keydown', event => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    const item = event.target.closest('.health-item');
    if (!item || !els.health.contains(item)) return;
    event.preventDefault();
    openHealthDetail(healthKeyFromItem(item));
  });
}

// Re-render after all deferred scripts have installed their wrappers. The actual
// data fetch may complete later, so renderSourceHealthSemantically also schedules
// interactivity each time the source badges are drawn.
document.addEventListener('DOMContentLoaded', () => {
  bindSourceHealthDiagnostics();
  scheduleHealthInteractivity();
});
