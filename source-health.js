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
    role: 'Structured SEBI offer-document extraction',
    scope: 'Abridged prospectus / RHP fields such as issue composition, managers and financials',
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

function sourceHealthState(key, health) {
  if (!health) return { ok: null, label: 'Not checked', note: 'No health metadata is available for this source yet.' };
  const error = sourceHealthError(key, health);
  const records = Number(health.records || 0);

  if (key === 'NSE-history' && !error && records === 0) {
    return { ok: true, label: 'Healthy', note: health.note || 'Checked successfully · 0 new historical rows' };
  }
  if (error) return { ok: false, label: 'Failed', note: 'The most recent source request or parser attempt reported an error.' };
  if (health.ok) return { ok: true, label: 'Healthy', note: health.note || 'Latest source check completed successfully.' };
  return { ok: false, label: 'Failed', note: health.note || 'The latest source refresh did not complete successfully.' };
}

function renderSourceHealthSemantically() {
  baseSourceHealthRenderer();
  if (!els.health) return;

  const history = state.meta?.sourceHealth?.['NSE-history'];
  if (history) {
    const item = [...els.health.querySelectorAll('.health-item')]
      .find(node => node.querySelector('strong')?.textContent === 'NSE-history');
    if (item) {
      const error = history.error || nseHistoryError(state.meta);
      const records = Number(history.records || 0);
      const dot = item.querySelector('.health-dot');
      const note = item.querySelector('span:last-child');

      if (!error && records === 0) {
        if (dot) dot.className = 'health-dot health-ok';
        if (note) note.textContent = history.note || 'checked · 0 new rows';
      } else if (!error && history.ok) {
        if (dot) dot.className = 'health-dot health-ok';
        if (note) note.textContent = history.note || `${records.toLocaleString('en-IN')} rows`;
      } else {
        if (dot) dot.className = 'health-dot health-bad';
        if (note) note.textContent = 'refresh failed';
      }
    }
  }

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
  if (key === 'NSE-history' && Number(health.records || 0) === 0 && !sourceHealthError(key, health)) {
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
  const info = SOURCE_HEALTH_INFO[key] || { label: key, role: 'Official data source', scope: 'Tracker data source', url: null };
  const status = sourceHealthState(key, health);
  const error = sourceHealthError(key, health);
  const checkedAt = health?.checkedAt || health?.asOf || state.meta?.generatedAt;
  const checkedLabel = checkedAt ? formatTimestamp(checkedAt) : 'Not available';
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
      <div class="health-detail-cell"><div class="health-detail-label">Last dataset check</div><div class="health-detail-value">${escapeHtml(checkedLabel)}</div></div>
      <div class="health-detail-cell"><div class="health-detail-label">Role</div><div class="health-detail-value">${escapeHtml(info.role)}</div></div>
    </div>
    <div class="health-detail-body">
      <div class="health-detail-section${error ? ' error' : ''}">
        <strong>${error ? 'Latest error' : 'What happened'}</strong>
        <p>${escapeHtml(error || refreshNote)}</p>
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
