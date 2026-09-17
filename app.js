const state = {
  data: [],
  activeStatus: 'all',
  search: '',
  board: 'all',
  year: 'all',
  view: 'explore',
  sort: 'recent',
  page: 1,
  pageSize: 25,
  saved: new Set(),
  compare: new Set(),
  loaded: false,
  calendarMonth: '',
  meta: {},
  byId: new Map(),
  indexById: new Map(),
  detailById: new Map(),
  masterById: null,
  summaryMode: false,
};

const els = {
  rows: document.getElementById('ipoRows'),
  stats: document.getElementById('stats'),
  freshness: document.getElementById('freshness'),
  recordCount: document.getElementById('recordCount'),
  search: document.getElementById('search'),
  board: document.getElementById('boardFilter'),
  year: document.getElementById('yearFilter'),
  empty: document.getElementById('empty'),
  dialog: document.getElementById('detailDialog'),
  dialogTitle: document.getElementById('dialogTitle'),
  dialogBoard: document.getElementById('dialogBoard'),
  dialogBody: document.getElementById('dialogBody'),
  dialogClose: document.getElementById('dialogClose'),
  health: document.getElementById('sourceHealth'),
};

const IST_DATE_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  timeZone: 'Asia/Kolkata',
});
const IST_DAY_FORMATTER = new Intl.DateTimeFormat('en-CA', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  timeZone: 'Asia/Kolkata',
});
const IST_TIMESTAMP_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  timeZone: 'Asia/Kolkata',
  dateStyle: 'medium',
  timeStyle: 'short',
});
const COMPANY_COLLATOR = new Intl.Collator('en', { sensitivity: 'base' });

const money = (value) =>
  value == null
    ? '—'
    : `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })} Cr`;
const rupees = (value) =>
  value == null ? '—' : `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
const x = (value) =>
  value == null ? '—' : `${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}×`;

function prettyDate(value) {
  if (!value) return '—';
  const date = new Date(`${value}T00:00:00+05:30`);
  return Number.isNaN(date.getTime()) ? String(value) : IST_DATE_FORMATTER.format(date);
}

function currentIstDate() {
  const parts = IST_DAY_FORMATTER.formatToParts(new Date());
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

const TODAY_IST = currentIstDate();

function derivedStatus(ipo) {
  if (ipo.openDate && TODAY_IST < ipo.openDate) return 'upcoming';
  if (ipo.openDate && ipo.closeDate && TODAY_IST >= ipo.openDate && TODAY_IST <= ipo.closeDate)
    return 'open';
  if (ipo.listingDate && TODAY_IST >= ipo.listingDate) return 'listed';
  if (ipo.closeDate && TODAY_IST > ipo.closeDate) return 'closed';
  return ipo.status || 'upcoming';
}

function priceBand(ipo) {
  if (!ipo.priceBand) return '—';
  const { min, max } = ipo.priceBand;
  if (min == null && max == null) return '—';
  if (min === max || min == null) return rupees(max);
  if (max == null) return rupees(min);
  return `${rupees(min)}–${rupees(max)}`;
}

function listingReturn(ipo) {
  const pct = ipo.listing?.gainPct;
  if (pct == null) return '<span class="muted">—</span>';
  const cls = pct >= 0 ? 'positive' : 'negative';
  return `<span class="${cls}">${pct > 0 ? '+' : ''}${Number(pct).toFixed(2)}%</span>`;
}

function badge(status) {
  return `<span class="badge badge-${escapeAttr(status)}">${escapeHtml(status)}</span>`;
}

function validationBadge(ipo) {
  const status = ipo.validation?.status || 'single-source';
  const label = status === 'single-source' ? '1 source' : status;
  return `<span class="validation validation-${escapeAttr(status)}">${escapeHtml(label)}</span>`;
}

function filingStage(ipo) {
  const types = (ipo.documents || []).map((doc) => String(doc?.type || '').toUpperCase());
  if (types.some((type) => type.includes('PROSPECTUS') && !type.includes('ABRIDGED')))
    return 'Prospectus';
  if (types.some((type) => type === 'RHP' || type.includes('RED HERRING'))) return 'RHP';
  if (types.some((type) => type === 'UDRHP')) return 'UDRHP';
  if (types.some((type) => type === 'DRHP')) return 'DRHP';
  return (
    { drhp: 'DRHP', udrhp: 'UDRHP', rhp: 'RHP', prospectus: 'Prospectus', exchange: 'Exchange' }[
      ipo.lifecycle?.stage
    ] || '—'
  );
}

function sourceCount(ipo) {
  if (Number.isFinite(Number(ipo.sourceCount))) return Number(ipo.sourceCount);
  const sources = ipo.sources || (ipo.source ? [ipo.source] : []);
  return new Set(sources.map((source) => String(source?.name || '').split(' ')[0]).filter(Boolean))
    .size;
}

function statusBucket(ipo) {
  const status = derivedStatus(ipo);
  return status === 'upcoming' && !ipo.openDate ? 'pipeline' : status;
}

function matchesBase(ipo) {
  const search = state.search.trim().toLowerCase();
  const year = (ipo.openDate || ipo.listingDate || ipo.lifecycle?.stageDate || '').slice(0, 4);
  return (
    (state.view !== 'watchlist' || state.saved.has(String(ipo.id))) &&
    (state.board === 'all' || ipo.board === state.board) &&
    (!search || `${ipo.company || ''} ${ipo.symbol || ''}`.toLowerCase().includes(search)) &&
    (state.year === 'all' || year === state.year)
  );
}

function filtered() {
  const metric = {
    size: (ipo) => ipo.issueSizeCr,
    subscription: (ipo) => ipo.subscription?.total,
    return: (ipo) => ipo.listing?.gainPct,
  }[state.sort];
  return state.data
    .filter(
      (ipo) =>
        matchesBase(ipo) &&
        (state.activeStatus === 'all' || statusBucket(ipo) === state.activeStatus),
    )
    .sort((a, b) => {
      if (state.sort === 'company')
        return COMPANY_COLLATOR.compare(a.company || '', b.company || '');
      if (metric) {
        const av = metric(a),
          bv = metric(b);
        if (av == null && bv != null) return 1;
        if (av != null && bv == null) return -1;
        if (av != null && bv != null && Number(av) !== Number(bv)) return Number(bv) - Number(av);
      }
      if (state.sort === 'closing') {
        const ad = a.closeDate && a.closeDate >= TODAY_IST ? a.closeDate : '';
        const bd = b.closeDate && b.closeDate >= TODAY_IST ? b.closeDate : '';
        if (ad && !bd) return -1;
        if (!ad && bd) return 1;
        if (ad !== bd) return ad.localeCompare(bd);
      }
      const ad = a.openDate || a.listingDate || a.lifecycle?.stageDate || '';
      const bd = b.openDate || b.listingDate || b.lifecycle?.stageDate || '';
      if (ad !== bd) return bd.localeCompare(ad);
      return COMPANY_COLLATOR.compare(String(a.company || ''), String(b.company || ''));
    });
}

function renderStats() {
  const counts = { open: 0, upcoming: 0, closed: 0, listed: 0, pipeline: 0 };
  state.data.forEach((ipo) => {
    const key = statusBucket(ipo);
    if (key in counts) counts[key]++;
  });
  const cards = [
    ['Open for bids', counts.open, 'View current issues', 'open'],
    ['Upcoming IPOs', counts.upcoming, 'With an opening date', 'upcoming'],
    ['Bidding closed', counts.closed, 'Awaiting listing updates', 'closed'],
    ['Listed IPOs', counts.listed, 'Explore the archive', 'listed'],
  ];
  els.stats.innerHTML = cards
    .map(
      ([label, value, note, status]) =>
        `<button type="button" class="stat stat-${status}" data-stat-status="${status}" aria-label="View ${value} ${label.toLowerCase()}"><span class="stat-top">${label}<span class="stat-status-dot"></span></span><div class="stat-value">${value.toLocaleString('en-IN')}</div><span class="stat-bottom"><span class="stat-note">${note}</span><span class="stat-arrow" aria-hidden="true">↗</span></span></button>`,
    )
    .join('');
}

function renderSourceHealth() {
  if (!els.health) return;
  const health = state.meta.sourceHealth || {};
  const sources = ['NSE-live', 'NSE-history', 'SEBI', 'BSE'];
  els.health.innerHTML = sources
    .map((name) => {
      const item = health[name];
      if (!item)
        return `<div class="health-item"><span class="health-dot health-unknown"></span><strong>${name}</strong><span>not checked</span></div>`;
      const ok = !!item.ok;
      const note = ok
        ? `${Number(item.records || 0).toLocaleString('en-IN')} rows`
        : 'refresh failed';
      return `<div class="health-item"><span class="health-dot ${ok ? 'health-ok' : 'health-bad'}"></span><strong>${name}</strong><span>${escapeHtml(note)}</span></div>`;
    })
    .join('');
}

function companyLink(ipo) {
  const label = escapeHtml(ipo.company || 'Unknown');
  if (!ipo.profilePath) return label;
  return `<a class="company-name-link" href="${escapeAttr(ipo.profilePath)}" aria-label="Open ${escapeAttr(ipo.company || 'IPO')} permanent profile">${label}</a>`;
}

const ACTION_ICONS = {
  save: '<svg viewBox="0 0 24 24" class="bookmark-icon" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z"/></svg>',
  compare:
    '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="7" height="14" rx="1"/><rect x="14" y="5" width="7" height="14" rx="1"/></svg>',
  preview:
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>',
};

function rowActions(ipo) {
  const key = String(ipo.id),
    name = escapeAttr(ipo.company || 'IPO');
  return `<div class="row-actions"><button type="button" class="action-button" data-action="save" data-id="${escapeAttr(key)}" aria-pressed="${state.saved.has(key)}" aria-label="${state.saved.has(key) ? 'Remove' : 'Save'} ${name} ${state.saved.has(key) ? 'from' : 'to'} watchlist" title="${state.saved.has(key) ? 'Remove from' : 'Save to'} watchlist">${ACTION_ICONS.save}</button><button type="button" class="action-button" data-action="compare" data-id="${escapeAttr(key)}" aria-pressed="${state.compare.has(key)}" aria-label="${state.compare.has(key) ? 'Remove' : 'Add'} ${name} ${state.compare.has(key) ? 'from' : 'to'} comparison" title="${state.compare.has(key) ? 'Remove from comparison' : 'Compare IPO'}">${ACTION_ICONS.compare}</button><button type="button" class="action-button" data-action="preview" data-id="${escapeAttr(key)}" aria-label="Quick view ${name}" title="Quick view">${ACTION_ICONS.preview}</button></div>`;
}

function keyDates(ipo) {
  if (statusBucket(ipo) === 'listed' && ipo.listingDate)
    return `<span class="table-date">${prettyDate(ipo.listingDate)}<small>Listed on exchange</small></span>`;
  if (ipo.openDate)
    return `<span class="table-date">${prettyDate(ipo.openDate)}<small>${ipo.closeDate ? `Closes ${prettyDate(ipo.closeDate)}` : 'Closing date unavailable'}</small></span>`;
  return `<span class="date-note">Dates unavailable${filingStage(ipo) !== '—' ? `<small class="metric-note">${escapeHtml(filingStage(ipo))} filed</small>` : ''}</span>`;
}

function renderTable() {
  if (!state.loaded) {
    syncUrl(false);
    return;
  }
  const rows = filtered();
  const pageCount = Math.max(1, Math.ceil(rows.length / state.pageSize));
  state.page = Math.min(pageCount, Math.max(1, state.page));
  const start = (state.page - 1) * state.pageSize;
  const visible = rows.slice(start, start + state.pageSize);
  els.empty.classList.toggle('hidden', rows.length > 0);
  els.rows.innerHTML = visible
    .map((ipo, index) => {
      const status = statusBucket(ipo),
        name = ipo.company || 'Unknown company';
      const initials = name
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map((part) => part[0])
        .join('')
        .toUpperCase();
      const validation =
        ipo.validation?.status === 'conflict'
          ? ` · <span class="validation validation-conflict">Source conflict</span>`
          : '';
      return `<tr data-id="${escapeAttr(ipo.id)}"><td data-label="Company"><div class="company-cell"><span class="ipo-monogram tone-${index % 4}" aria-hidden="true">${escapeHtml(initials)}</span><div class="ipo-company">${companyLink(ipo)}<span class="symbol">${escapeHtml([ipo.symbol, ipo.board || ipo.exchange].filter(Boolean).join(' · '))}${validation}</span></div></div></td><td class="status-cell" data-label="Status">${status === 'pipeline' ? '<span class="badge badge-pipeline">Dates pending</span>' : badge(status)}</td><td class="date-cell" data-label="Key dates">${keyDates(ipo)}</td><td class="numeric" data-label="Price band"><span class="metric">${priceBand(ipo)}</span></td><td class="numeric" data-label="Issue size"><span class="metric">${money(ipo.issueSizeCr)}</span></td><td class="numeric" data-label="Subscription"><span class="metric">${x(ipo.subscription?.total)}</span></td><td class="numeric" data-label="Listing return"><span class="metric">${listingReturn(ipo)}</span></td><td class="actions-cell" data-label="Actions">${rowActions(ipo)}</td></tr>`;
    })
    .join('');
  document.getElementById('resultCount').textContent = rows.length
    ? `Showing ${(start + 1).toLocaleString('en-IN')}–${Math.min(start + state.pageSize, rows.length).toLocaleString('en-IN')} of ${rows.length.toLocaleString('en-IN')} IPOs`
    : '0 IPOs found';
  document.getElementById('directoryTotal').textContent = (
    state.view === 'watchlist' ? state.saved.size : state.data.length
  ).toLocaleString('en-IN');
  document.getElementById('pageInfo').textContent = `Page ${state.page} of ${pageCount}`;
  document.getElementById('prevPage').disabled = state.page <= 1;
  document.getElementById('nextPage').disabled = state.page >= pageCount;
  document.getElementById('exportCsv').disabled = !rows.length;
  document.getElementById('clearFilters').hidden = !hasFilters();
  const emptySaved = state.view === 'watchlist' && !state.saved.size;
  document.getElementById('emptyTitle').textContent = emptySaved
    ? 'Your watchlist starts here'
    : 'No IPOs match your filters';
  document.getElementById('emptyDescription').textContent = emptySaved
    ? 'Use the bookmark button beside an IPO to keep it here. Saved on this device.'
    : 'Try another company name or broaden your filters.';
  document.getElementById('emptyReset').textContent = emptySaved ? 'Explore IPOs' : 'Clear filters';
  const counts = { all: 0, open: 0, upcoming: 0, closed: 0, listed: 0, pipeline: 0 };
  for (const ipo of state.data.filter(matchesBase)) {
    counts.all++;
    const bucket = statusBucket(ipo);
    if (bucket in counts) counts[bucket]++;
  }
  document.querySelectorAll('#tabs .tab').forEach((button) => {
    const active = button.dataset.status === state.activeStatus;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
    button.querySelector('span').textContent =
      counts[button.dataset.status].toLocaleString('en-IN');
  });
  document.getElementById('watchlistCount').textContent = state.saved.size;
  syncUrl(false);
}

function renderYears() {
  const years = [
    ...new Set(
      state.data
        .map((ipo) =>
          (ipo.openDate || ipo.listingDate || ipo.lifecycle?.stageDate || '').slice(0, 4),
        )
        .filter(Boolean),
    ),
  ]
    .sort()
    .reverse();
  els.year.innerHTML =
    '<option value="all">All years</option>' +
    years.map((year) => `<option value="${year}">${year}</option>`).join('');
}

function parseProfileHtml(text) {
  const documentNode = new DOMParser().parseFromString(text, 'text/html');
  const node = documentNode.getElementById('ipo-profile-data');
  if (!node) return null;
  const payload = JSON.parse(node.textContent || '{}');
  return payload?.ipo && typeof payload.ipo === 'object' ? payload.ipo : null;
}

async function masterDetail(id) {
  const key = String(id);
  if (!state.masterById) {
    const response = await fetch('data/ipos.json', { cache: 'no-cache' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    state.masterById = new Map((payload.ipos || []).map((ipo) => [String(ipo.id), ipo]));
  }
  return state.masterById.get(key) || null;
}

async function loadIpoDetail(id) {
  const key = String(id);
  if (state.detailById.has(key)) return state.detailById.get(key);

  const summary = state.byId.get(key);
  if (!summary) return null;

  if (!state.summaryMode || !summary.profilePath) {
    state.detailById.set(key, summary);
    return summary;
  }

  try {
    const response = await fetch(summary.profilePath, { cache: 'no-cache' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const profile = parseProfileHtml(await response.text());
    if (!profile || String(profile.id) !== key)
      throw new Error('Embedded profile record missing or mismatched');
    const detail = { ...summary, ...profile };
    state.detailById.set(key, detail);
    return detail;
  } catch (error) {
    // During rollout an old route may not contain embedded JSON yet. Fall back
    // to the canonical file once, then stop paying that cost after routes rebuild.
    console.warn(
      `Could not lazy-load embedded IPO profile ${key}; using compatibility fallback`,
      error,
    );
    try {
      const detail = await masterDetail(key);
      if (detail) {
        state.detailById.set(key, detail);
        return detail;
      }
    } catch (fallbackError) {
      console.warn(`Could not load master IPO detail ${key}`, fallbackError);
    }
    return summary;
  }
}

let detailRequest = 0;
let detailTrigger = null;
async function prepareAndOpenDetail(id, trigger) {
  const key = String(id),
    summary = state.byId.get(key);
  if (!summary) return;
  const request = ++detailRequest;
  detailTrigger = trigger || document.activeElement;
  els.dialogTitle.textContent = summary.company || 'IPO';
  els.dialogBoard.textContent = 'COMPANY QUICK VIEW';
  els.dialogBody.innerHTML =
    '<div class="company-empty-note" role="status">Loading company details…</div>';
  if (!els.dialog.open) els.dialog.showModal();
  const detail = await loadIpoDetail(key);
  if (!detail || request !== detailRequest || !els.dialog.open) return;
  if (state.summaryMode && summary.profilePath && !state.detailById.has(key)) {
    els.dialogBody.innerHTML = `<div class="company-empty-note"><h3>Company details could not be loaded</h3><p>The IPO directory is still available. Try again or open the company page.</p><button type="button" class="button primary" id="retryCompanyDetail">Try again</button> <a class="button secondary" href="${escapeAttr(summary.profilePath)}">Open company page →</a></div>`;
    document
      .getElementById('retryCompanyDetail')
      .addEventListener('click', () => prepareAndOpenDetail(key, detailTrigger));
    return;
  }
  state.byId.set(key, detail);
  const index = state.indexById.get(key);
  if (index != null) state.data[index] = detail;
  openDetail(key);
}

async function openDetail(id) {
  const summary = state.byId.get(String(id));
  if (!summary) return;
  els.dialogTitle.textContent = summary.company || 'IPO';
  els.dialogBoard.textContent = `${summary.board || 'IPO'} · ${derivedStatus(summary).toUpperCase()} · ${filingStage(summary)}`;
  els.dialogBody.innerHTML = '<div class="company-empty-note">Loading company profile…</div>';
  if (!els.dialog.open) els.dialog.showModal();

  const ipo = await loadIpoDetail(id);
  if (!ipo) return;
  els.dialogBody.innerHTML = `<div class="detail-grid">
    <div class="detail-card"><div class="detail-label">Price band</div><div class="detail-value">${priceBand(ipo)}</div></div>
    <div class="detail-card"><div class="detail-label">Issue size</div><div class="detail-value">${money(ipo.issueSizeCr)}</div></div>
    <div class="detail-card"><div class="detail-label">Open date</div><div class="detail-value">${prettyDate(ipo.openDate)}</div></div>
    <div class="detail-card"><div class="detail-label">Close date</div><div class="detail-value">${prettyDate(ipo.closeDate)}</div></div>
  </div>`;
}

function validationCopy(ipo) {
  const status = ipo.validation?.status || 'single-source';
  if (status === 'verified')
    return 'At least two independent official sources are attached to this record.';
  if (status === 'conflict')
    return 'One or more comparable fields disagree across exchange sources.';
  return sourceCount(ipo)
    ? 'This record has not been cross-verified across independent sources.'
    : 'No source is attached to this record yet.';
}

function formatObservation(value) {
  if (value == null) return '—';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function formatTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${IST_TIMESTAMP_FORMATTER.format(date)} IST`;
}

function escapeHtml(value) {
  return String(value ?? '').replace(
    /[&<>'"]/g,
    (char) =>
      ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;',
      })[char],
  );
}
function escapeAttr(value) {
  return escapeHtml(value);
}

const VIEWS = {
  explore: [
    'Explore IPOs',
    'The IPO market, in focus.',
    'Find the next issue. Understand the details. Follow what happens next.',
  ],
  watchlist: [
    'Watchlist',
    'Your IPO shortlist.',
    'Keep the issues you are following together. Saved on this browser and device.',
  ],
  calendar: [
    'IPO calendar',
    'Stay ahead of the key dates.',
    'See when bidding opens, closes and moves to the exchange.',
  ],
  quality: [
    'Data & sources',
    'Research you can trace.',
    'Understand source coverage, data gaps and how the tracker checks its records.',
  ],
};
const VALID_STATUSES = ['all', 'open', 'upcoming', 'closed', 'listed', 'pipeline'];
const VALID_SORTS = ['recent', 'closing', 'company', 'size', 'subscription', 'return'];
function readUrl() {
  const params = new URLSearchParams(location.search);
  state.view = Object.hasOwn(VIEWS, params.get('view')) ? params.get('view') : 'explore';
  state.activeStatus = VALID_STATUSES.includes(params.get('status')) ? params.get('status') : 'all';
  state.search = (params.get('q') || '').slice(0, 200);
  state.board = ['Mainboard', 'SME'].includes(params.get('board')) ? params.get('board') : 'all';
  state.year = /^\d{4}$/.test(params.get('year') || '') ? params.get('year') : 'all';
  state.sort = VALID_SORTS.includes(params.get('sort')) ? params.get('sort') : 'recent';
  state.page = Math.max(1, Math.min(100000, parseInt(params.get('page'), 10) || 1));
  state.pageSize = params.get('limit') === '50' ? 50 : 25;
  state.calendarMonth = /^\d{4}-(0[1-9]|1[0-2])$/.test(params.get('month') || '')
    ? params.get('month')
    : TODAY_IST.slice(0, 7);
}
function syncUrl(push = false) {
  const params = new URLSearchParams();
  if (state.view !== 'explore') params.set('view', state.view);
  if (state.activeStatus !== 'all') params.set('status', state.activeStatus);
  if (state.search) params.set('q', state.search);
  if (state.board !== 'all') params.set('board', state.board);
  if (state.year !== 'all') params.set('year', state.year);
  if (state.sort !== 'recent') params.set('sort', state.sort);
  if (state.page !== 1) params.set('page', state.page);
  if (state.pageSize !== 25) params.set('limit', state.pageSize);
  if (state.view === 'calendar' && state.calendarMonth !== TODAY_IST.slice(0, 7))
    params.set('month', state.calendarMonth);
  const query = params.toString(),
    url = `${location.pathname}${query ? '?' + query : ''}`;
  if (url !== location.pathname + location.search)
    history[push ? 'pushState' : 'replaceState']({}, '', url);
}
function syncControls() {
  els.search.value = state.search;
  els.board.value = state.board;
  if (![...els.year.options].some((option) => option.value === state.year)) state.year = 'all';
  els.year.value = state.year;
  document.getElementById('sortFilter').value = state.sort;
  document.getElementById('pageSize').value = String(state.pageSize);
}
function hasFilters() {
  return !!(
    state.search ||
    state.board !== 'all' ||
    state.year !== 'all' ||
    state.activeStatus !== 'all' ||
    state.sort !== 'recent'
  );
}
function resetFilters() {
  state.search = '';
  state.board = 'all';
  state.year = 'all';
  state.activeStatus = 'all';
  state.sort = 'recent';
  state.page = 1;
  syncControls();
  syncUrl(true);
  renderTable();
}
function changeView(view, push = true) {
  if (!Object.hasOwn(VIEWS, view)) return;
  state.view = view;
  const [label, title, description] = VIEWS[view];
  document.getElementById('viewBreadcrumb').textContent = label;
  document.getElementById('pageTitle').textContent = title;
  document.getElementById('pageDescription').textContent = description;
  document.title = `${label} | India IPO Tracker`;
  document.getElementById('view-explore').hidden = !['explore', 'watchlist'].includes(view);
  document.getElementById('view-calendar').hidden = view !== 'calendar';
  document.getElementById('view-quality').hidden = view !== 'quality';
  els.stats.hidden = view !== 'explore';
  document.querySelectorAll('.main-nav [data-view]').forEach((link) => {
    const active = link.dataset.view === view;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
  document.getElementById('directoryTitle').childNodes[0].textContent =
    view === 'watchlist' ? 'Saved IPOs ' : 'Explore IPOs ';
  document.getElementById('directoryDescription').textContent =
    view === 'watchlist'
      ? 'Your saved issues, with the same filters and comparison tools.'
      : 'From upcoming offers to the latest listings.';
  syncUrl(push);
  if (state.loaded && ['explore', 'watchlist'].includes(view)) renderTable();
  if (state.loaded && view === 'calendar') renderCalendar();
  else if (view === 'calendar')
    document.getElementById('calendarEvents').innerHTML = state.loadError
      ? '<div class="empty"><h3>Calendar data is unavailable</h3><p>Reload the page to try again.</p></div>'
      : '<div class="empty" role="status">Loading calendar dates…</div>';
  document.dispatchEvent(new CustomEvent('ipo:view-change', { detail: { view } }));
  closeMenu();
}
let toastTimer;
function showToast(message) {
  const toast = document.getElementById('toast');
  clearTimeout(toastTimer);
  toast.textContent = message;
  toast.hidden = false;
  toastTimer = setTimeout(() => {
    toast.hidden = true;
  }, 3500);
}
function readSaved(value) {
  try {
    const list = JSON.parse(value || '[]');
    return new Set(
      Array.isArray(list) ? list.filter((id) => typeof id === 'string').slice(0, 5000) : [],
    );
  } catch {
    return new Set();
  }
}
function saveReturnUrl() {
  try {
    sessionStorage.setItem('ipoTrackerReturnUrl', location.pathname + location.search);
  } catch {
    /* Navigation still works without session storage. */
  }
}
function refreshActions() {
  document.querySelectorAll('#ipoRows tr').forEach((row) => {
    const ipo = state.byId.get(String(row.dataset.id));
    if (ipo) row.querySelector('.actions-cell').innerHTML = rowActions(ipo);
  });
  document.getElementById('watchlistCount').textContent = state.saved.size;
}
function focusDirectoryAction(action, id = '') {
  const visibleDirectory = ['explore', 'watchlist'].includes(state.view);
  const exact = id
    ? document.querySelector(
        `#ipoRows button[data-action="${action}"][data-id="${CSS.escape(id)}"]`,
      )
    : null;
  const target = visibleDirectory
    ? exact ||
      document.querySelector(`#ipoRows button[data-action="${action}"]`) ||
      document.getElementById('emptyReset')
    : document.querySelector('.main-nav [aria-current="page"]');
  target?.focus({ preventScroll: true });
}
function toggleSaved(id) {
  if (state.saved.has(id)) state.saved.delete(id);
  else state.saved.add(id);
  let persisted = true;
  try {
    localStorage.setItem('ipoTrackerWatchlist', JSON.stringify([...state.saved]));
  } catch {
    persisted = false;
  }
  if (state.view === 'watchlist') renderTable();
  else refreshActions();
  showToast(
    persisted
      ? state.saved.has(id)
        ? 'Saved to your watchlist on this device.'
        : 'Removed from your watchlist.'
      : 'Updated for this visit. Your browser could not save the watchlist.',
  );
}
function toggleCompare(id) {
  if (state.compare.has(id)) state.compare.delete(id);
  else if (state.compare.size >= 3) {
    showToast('You can compare up to 3 IPOs. Remove one to add another.');
    return;
  } else state.compare.add(id);
  refreshActions();
  renderCompareTray();
}
function renderCompareTray() {
  const count = state.compare.size;
  document.getElementById('compareTray').hidden = count === 0;
  document.body.classList.toggle('has-compare', count > 0);
  document.getElementById('compareCount').textContent =
    `${count} IPO${count === 1 ? '' : 's'} selected`;
  document.getElementById('openCompare').disabled = count < 2;
  document.getElementById('compareNames').innerHTML = [...state.compare]
    .map((id) => {
      const ipo = state.byId.get(id);
      return `<div class="compare-token"><span>${escapeHtml(ipo?.company || id)}</span><button type="button" data-remove-compare="${escapeAttr(id)}" aria-label="Remove ${escapeAttr(ipo?.company || id)} from comparison">×</button></div>`;
    })
    .join('');
}
function openComparison() {
  const records = [...state.compare].map((id) => state.byId.get(id)).filter(Boolean);
  if (records.length < 2) return;
  const fields = [
    [
      'Status',
      (ipo) =>
        badge(statusBucket(ipo) === 'pipeline' ? 'pipeline' : derivedStatus(ipo)).replace(
          '>pipeline<',
          '>Dates pending<',
        ),
    ],
    ['Board', (ipo) => escapeHtml(ipo.board || '—')],
    ['Price band', priceBand],
    ['Issue size', (ipo) => money(ipo.issueSizeCr)],
    ['Bidding opens', (ipo) => prettyDate(ipo.openDate)],
    ['Bidding closes', (ipo) => prettyDate(ipo.closeDate)],
    ['Listing date', (ipo) => prettyDate(ipo.listingDate)],
    ['Subscription', (ipo) => x(ipo.subscription?.total)],
    ['Listing return', listingReturn],
    ['Filing stage', (ipo) => escapeHtml(filingStage(ipo))],
    ['Data validation', validationBadge],
    ['Sources attached', (ipo) => String(sourceCount(ipo))],
  ];
  document.getElementById('compareBody').innerHTML =
    `<p class="compare-note">Recorded issue details, side by side. Missing values are shown as —. Figures may have different reporting dates; check the source in each profile.</p><div class="compare-table-wrap" tabindex="0" role="region" aria-label="IPO comparison table, scroll horizontally on small screens"><table class="compare-table"><caption class="sr-only">Comparison of ${records.map((ipo) => escapeHtml(ipo.company)).join(', ')}</caption><thead><tr><th scope="col">Issue details</th>${records.map((ipo) => `<th scope="col">${companyLink(ipo)}<span class="symbol">${escapeHtml(ipo.symbol || ipo.board || '')}</span></th>`).join('')}</tr></thead><tbody>${fields.map(([label, value]) => `<tr><th scope="row">${label}</th>${records.map((ipo) => `<td>${value(ipo)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  document.getElementById('compareDialog').showModal();
}
function exportCsv() {
  const quote = (value) => {
    if (typeof value === 'number' && Number.isFinite(value)) return String(value);
    let str = String(value ?? '');
    if (/^[=+@\-\t\r]/.test(str)) str = "'" + str;
    return '"' + str.replace(/"/g, '""') + '"';
  };
  const header = [
    'Company',
    'Symbol',
    'Board',
    'Status',
    'Open date',
    'Close date',
    'Listing date',
    'Price minimum INR',
    'Price maximum INR',
    'Issue size crore INR',
    'Subscription multiple',
    'Listing gain percent',
    'Validation',
    'Source count',
    'Profile URL',
    'Dataset timestamp',
  ];
  const lines = filtered().map((ipo) => [
    ipo.company,
    ipo.symbol,
    ipo.board,
    statusBucket(ipo),
    ipo.openDate,
    ipo.closeDate,
    ipo.listingDate,
    ipo.priceBand?.min,
    ipo.priceBand?.max,
    ipo.issueSizeCr,
    ipo.subscription?.total,
    ipo.listing?.gainPct,
    ipo.validation?.status,
    sourceCount(ipo),
    ipo.profilePath ? new URL(ipo.profilePath, document.baseURI).href : '',
    state.meta.generatedAt,
  ]);
  const blob = new Blob(
    ['\uFEFF' + [header, ...lines].map((row) => row.map(quote).join(',')).join('\r\n')],
    { type: 'text/csv;charset=utf-8' },
  );
  const url = URL.createObjectURL(blob),
    link = document.createElement('a');
  link.href = url;
  link.download = `ipo-tracker-${TODAY_IST}.csv`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  showToast(`Exported ${lines.length.toLocaleString('en-IN')} matching IPOs.`);
}
function renderCalendar() {
  if (!state.loaded) {
    syncUrl(false);
    return;
  }
  const [year, month] = state.calendarMonth.split('-').map(Number);
  document.getElementById('calendarMonth').textContent = new Intl.DateTimeFormat('en-IN', {
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(Date.UTC(year, month - 1, 1)));
  const groups = new Map();
  state.data.forEach((ipo) => {
    [
      ['openDate', 'Bidding opens', 'upcoming'],
      ['closeDate', 'Bidding closes', 'closed'],
      ['listingDate', 'Listing', 'listed'],
    ].forEach(([field, label, status]) => {
      const date = ipo[field];
      if (!date || !date.startsWith(state.calendarMonth + '-')) return;
      if (!groups.has(date)) groups.set(date, []);
      groups.get(date).push({ ipo, label, status });
    });
  });
  const root = document.getElementById('calendarEvents');
  root.innerHTML = groups.size
    ? [...groups]
        .sort(([a], [b]) => a.localeCompare(b))
        .map(
          ([date, events]) =>
            `<section class="calendar-day ${date === TODAY_IST ? 'today' : ''}" aria-label="${escapeAttr(prettyDate(date))}"><time datetime="${date}">${new Intl.DateTimeFormat('en-IN', { weekday: 'short', timeZone: 'Asia/Kolkata' }).format(new Date(date + 'T00:00:00+05:30'))}<strong>${Number(date.slice(-2))}</strong>${date === TODAY_IST ? 'Today' : ''}</time><div>${events
              .sort((a, b) => COMPANY_COLLATOR.compare(a.ipo.company, b.ipo.company))
              .map(
                ({ ipo, label, status }) =>
                  `<div class="calendar-event"><a href="${escapeAttr(ipo.profilePath || './')}">${escapeHtml(ipo.company)}<small>${escapeHtml(ipo.board || ipo.exchange || '')}</small></a><span class="badge badge-${status}">${label}</span></div>`,
              )
              .join('')}</div></section>`,
        )
        .join('')
    : '<div class="empty"><h3>No recorded dates this month</h3><p>Try a different month. Issues without announced dates appear under Dates pending in Explore IPOs.</p></div>';
  syncUrl(false);
}
function moveCalendar(delta) {
  const [year, month] = state.calendarMonth.split('-').map(Number),
    next = new Date(Date.UTC(year, month - 1 + delta, 1));
  state.calendarMonth = `${next.getUTCFullYear()}-${String(next.getUTCMonth() + 1).padStart(2, '0')}`;
  syncUrl(true);
  renderCalendar();
}
function closeMenu() {
  document.body.classList.remove('nav-open');
  document.getElementById('menuToggle').setAttribute('aria-expanded', 'false');
  document.getElementById('navBackdrop').hidden = true;
}
function bind() {
  document.querySelectorAll('[data-view]').forEach((link) =>
    link.addEventListener('click', (event) => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      changeView(link.dataset.view);
      document.getElementById('main').focus({ preventScroll: true });
    }),
  );
  document.getElementById('menuToggle').addEventListener('click', () => {
    if (document.body.classList.contains('nav-open')) return closeMenu();
    document.body.classList.add('nav-open');
    document.getElementById('menuToggle').setAttribute('aria-expanded', 'true');
    document.getElementById('navBackdrop').hidden = false;
    document.querySelector('.sidebar a').focus();
  });
  document.getElementById('navBackdrop').addEventListener('click', () => {
    closeMenu();
    document.getElementById('menuToggle').focus();
  });
  document.addEventListener('keydown', (event) => {
    if (document.body.classList.contains('nav-open')) {
      if (event.key === 'Escape') {
        closeMenu();
        document.getElementById('menuToggle').focus();
      }
      if (event.key === 'Tab') {
        const links = [...document.querySelectorAll('.sidebar a')];
        const first = links[0],
          last = links[links.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    }
    if (
      event.key === '/' &&
      !event.ctrlKey &&
      !event.metaKey &&
      !event.altKey &&
      !event.target.closest('input,textarea,select,[contenteditable=true]') &&
      !document.querySelector('dialog[open]')
    ) {
      event.preventDefault();
      if (!['explore', 'watchlist'].includes(state.view)) changeView('explore');
      els.search.focus();
    }
  });
  els.stats.addEventListener('click', (event) => {
    const card = event.target.closest('[data-stat-status]');
    if (!card) return;
    state.search = '';
    state.board = 'all';
    state.year = 'all';
    state.sort = 'recent';
    state.activeStatus = card.dataset.statStatus;
    state.page = 1;
    syncControls();
    syncUrl(true);
    renderTable();
    document.getElementById('directory').scrollIntoView({
      block: 'start',
      behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
    });
  });
  document.querySelectorAll('#tabs .tab').forEach((button) =>
    button.addEventListener('click', () => {
      state.activeStatus = button.dataset.status;
      state.page = 1;
      syncUrl(true);
      renderTable();
    }),
  );
  let searchFrame;
  els.search.addEventListener('input', (event) => {
    state.search = event.target.value;
    state.page = 1;
    cancelAnimationFrame(searchFrame);
    searchFrame = requestAnimationFrame(renderTable);
  });
  [
    [els.board, 'board'],
    [els.year, 'year'],
    [document.getElementById('sortFilter'), 'sort'],
    [document.getElementById('pageSize'), 'pageSize'],
  ].forEach(([element, key]) =>
    element.addEventListener('change', () => {
      state[key] = key === 'pageSize' ? Number(element.value) : element.value;
      state.page = 1;
      syncUrl(true);
      renderTable();
    }),
  );
  document.getElementById('clearFilters').addEventListener('click', resetFilters);
  document.getElementById('emptyReset').addEventListener('click', () => {
    if (!state.loaded) {
      location.reload();
      return;
    }
    if (state.view === 'watchlist' && !state.saved.size) changeView('explore');
    resetFilters();
    els.search.focus();
  });
  ['prevPage', 'nextPage'].forEach((id, index) =>
    document.getElementById(id).addEventListener('click', () => {
      state.page += index ? 1 : -1;
      syncUrl(true);
      renderTable();
      document.getElementById('directory').scrollIntoView({ block: 'start' });
    }),
  );
  els.rows.addEventListener('click', (event) => {
    const action = event.target.closest('button[data-action]');
    if (!action) return;
    const id = action.dataset.id;
    if (action.dataset.action === 'preview') prepareAndOpenDetail(id, action);
    else {
      if (action.dataset.action === 'save') toggleSaved(id);
      else toggleCompare(id);
      focusDirectoryAction(action.dataset.action, id);
    }
  });
  document.addEventListener('click', (event) => {
    if (event.target.closest('a[href*="ipo/"]')) saveReturnUrl();
  });
  els.dialogClose.addEventListener('click', () => els.dialog.close());
  els.dialog.addEventListener('close', () => {
    detailRequest++;
    if (detailTrigger?.isConnected) detailTrigger.focus({ preventScroll: true });
  });
  [els.dialog, document.getElementById('compareDialog')].forEach((dialog) =>
    dialog.addEventListener('click', (event) => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      if (
        event.clientX < rect.left ||
        event.clientX > rect.right ||
        event.clientY < rect.top ||
        event.clientY > rect.bottom
      )
        dialog.close();
    }),
  );
  document.getElementById('openCompare').addEventListener('click', openComparison);
  document
    .getElementById('closeCompare')
    .addEventListener('click', () => document.getElementById('compareDialog').close());
  document.getElementById('clearCompare').addEventListener('click', () => {
    state.compare.clear();
    refreshActions();
    renderCompareTray();
    focusDirectoryAction('compare');
  });
  document.getElementById('compareNames').addEventListener('click', (event) => {
    const button = event.target.closest('[data-remove-compare]');
    if (button) {
      toggleCompare(button.dataset.removeCompare);
      const next = document.querySelector('[data-remove-compare]');
      if (next) next.focus();
      else focusDirectoryAction('compare');
    }
  });
  document.getElementById('exportCsv').addEventListener('click', exportCsv);
  document.getElementById('previousMonth').addEventListener('click', () => moveCalendar(-1));
  document.getElementById('nextMonth').addEventListener('click', () => moveCalendar(1));
  document.getElementById('calendarToday').addEventListener('click', () => {
    state.calendarMonth = TODAY_IST.slice(0, 7);
    syncUrl(true);
    renderCalendar();
  });
  window.addEventListener('popstate', () => {
    readUrl();
    syncControls();
    changeView(state.view, false);
  });
  window.addEventListener('storage', (event) => {
    if (event.key !== 'ipoTrackerWatchlist') return;
    state.saved = readSaved(event.newValue);
    if (state.loaded) {
      state.saved = new Set([...state.saved].filter((id) => state.byId.has(id)));
      renderTable();
    }
  });
}

async function loadDashboardPayload() {
  const sources = ['data/ipos-summary.json', 'data/ipos.json'];
  let lastError = null;
  for (const url of sources) {
    try {
      const response = await fetch(url, { cache: 'no-cache' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      if (!Array.isArray(payload?.ipos)) throw new Error('IPO payload missing records');
      return payload;
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error('No IPO data source available');
}

async function init() {
  readUrl();
  try {
    state.saved = readSaved(localStorage.getItem('ipoTrackerWatchlist'));
  } catch {
    /* Optional device storage. */
  }
  bind();
  document.getElementById('marketDate').textContent = prettyDate(TODAY_IST);
  changeView(state.view, false);
  try {
    const payload = await loadDashboardPayload();
    state.data = payload.ipos || [];
    state.meta = payload.meta || {};
    state.summaryMode = Number(state.meta.publicSummaryVersion || 0) >= 1;
    state.byId = new Map(state.data.map((ipo) => [String(ipo.id), ipo]));
    state.indexById = new Map(state.data.map((ipo, index) => [String(ipo.id), index]));
    state.saved = new Set([...state.saved].filter((id) => state.byId.has(id)));
    state.loaded = true;
    renderYears();
    syncControls();
    renderStats();
    renderSourceHealth();
    renderTable();
    changeView(state.view, false);
    const generated = state.meta.generatedAt
      ? formatTimestamp(state.meta.generatedAt)
      : 'timestamp unavailable';
    const age = Date.now() - new Date(state.meta.generatedAt).getTime();
    els.freshness.classList.add('loaded');
    if (Number.isFinite(age) && age > 36 * 60 * 60 * 1000) els.freshness.classList.add('stale');
    els.freshness.textContent = `${state.meta.seed ? 'Preview data' : 'Snapshot'} · ${generated}`;
    els.freshness.title =
      'Dataset publication time. Individual figures retain their own source timestamps.';
    els.recordCount.textContent = `${state.data.length.toLocaleString('en-IN')} records · Mainboard & SME`;
  } catch (error) {
    state.loadError = true;
    els.freshness.textContent = 'Snapshot unavailable';
    els.freshness.classList.add('failed');
    document.getElementById('resultCount').textContent = 'Data could not be loaded';
    document.getElementById('emptyTitle').textContent = 'We could not load the IPOs';
    document.getElementById('emptyDescription').textContent =
      'Check your connection and try again.';
    document.getElementById('emptyReset').textContent = 'Try again';
    els.empty.classList.remove('hidden');
    if (state.view === 'calendar')
      document.getElementById('calendarEvents').innerHTML =
        '<div class="empty"><h3>Calendar data is unavailable</h3><p>Reload the page to try again.</p></div>';
    console.error(error);
  }
}

init();
