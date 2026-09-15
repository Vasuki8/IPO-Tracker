const state = {
  data: [], activeStatus: 'all', search: '', board: 'all', year: 'all',
  meta: {}, byId: new Map(), indexById: new Map(), detailById: new Map(), masterById: null, summaryMode: false
};

const els = {
  rows: document.getElementById('ipoRows'), stats: document.getElementById('stats'),
  freshness: document.getElementById('freshness'), recordCount: document.getElementById('recordCount'),
  search: document.getElementById('search'), board: document.getElementById('boardFilter'),
  year: document.getElementById('yearFilter'), empty: document.getElementById('empty'),
  dialog: document.getElementById('detailDialog'), dialogTitle: document.getElementById('dialogTitle'),
  dialogBoard: document.getElementById('dialogBoard'), dialogBody: document.getElementById('dialogBody'),
  dialogClose: document.getElementById('dialogClose'), health: document.getElementById('sourceHealth')
};

const IST_DATE_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  day: '2-digit', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata'
});
const IST_DAY_FORMATTER = new Intl.DateTimeFormat('en-CA', {
  year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'Asia/Kolkata'
});
const IST_TIMESTAMP_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short'
});
const COMPANY_COLLATOR = new Intl.Collator('en', { sensitivity: 'base' });

const money = value => value == null ? '—' : `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })} Cr`;
const rupees = value => value == null ? '—' : `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
const x = value => value == null ? '—' : `${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}×`;

function prettyDate(value) {
  if (!value) return '—';
  const date = new Date(`${value}T00:00:00+05:30`);
  return Number.isNaN(date.getTime()) ? String(value) : IST_DATE_FORMATTER.format(date);
}

function currentIstDate() {
  const parts = IST_DAY_FORMATTER.formatToParts(new Date());
  const values = Object.fromEntries(parts.map(part => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

const TODAY_IST = currentIstDate();

function derivedStatus(ipo) {
  if (ipo.openDate && TODAY_IST < ipo.openDate) return 'upcoming';
  if (ipo.openDate && ipo.closeDate && TODAY_IST >= ipo.openDate && TODAY_IST <= ipo.closeDate) return 'open';
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
  const types = (ipo.documents || []).map(doc => String(doc?.type || '').toUpperCase());
  if (types.some(type => type.includes('PROSPECTUS') && !type.includes('ABRIDGED'))) return 'Prospectus';
  if (types.some(type => type === 'RHP' || type.includes('RED HERRING'))) return 'RHP';
  if (types.some(type => type === 'UDRHP')) return 'UDRHP';
  if (types.some(type => type === 'DRHP')) return 'DRHP';
  return ({ drhp:'DRHP', udrhp:'UDRHP', rhp:'RHP', prospectus:'Prospectus', exchange:'Exchange' })[ipo.lifecycle?.stage] || '—';
}

function sourceCount(ipo) {
  if (Number.isFinite(Number(ipo.sourceCount))) return Number(ipo.sourceCount);
  const sources = ipo.sources || (ipo.source ? [ipo.source] : []);
  return new Set(
    sources.map(source => String(source?.name || '').split(' ')[0]).filter(Boolean)
  ).size;
}

function filtered() {
  const search = state.search.trim().toLowerCase();
  return state.data.filter(ipo => {
    const status = derivedStatus(ipo);
    const matchesStatus = state.activeStatus === 'all' || status === state.activeStatus;
    const matchesBoard = state.board === 'all' || ipo.board === state.board;
    const matchesSearch = !search || `${ipo.company || ''} ${ipo.symbol || ''}`.toLowerCase().includes(search);
    const year = (ipo.openDate || ipo.listingDate || ipo.lifecycle?.stageDate || '').slice(0, 4);
    return matchesStatus && matchesBoard && matchesSearch && (state.year === 'all' || year === state.year);
  }).sort((a, b) => {
    const ad = a.openDate || '';
    const bd = b.openDate || '';
    if (ad && !bd) return -1;
    if (!ad && bd) return 1;
    if (ad !== bd) return bd.localeCompare(ad);
    return COMPANY_COLLATOR.compare(String(a.company || ''), String(b.company || ''));
  });
}

function renderStats() {
  const counts = { open: 0, upcoming: 0, closed: 0, listed: 0 };
  let pipeline = 0;
  let conflicts = 0;

  for (const ipo of state.data) {
    const status = derivedStatus(ipo);
    if (counts[status] != null) counts[status]++;
    if (['drhp','udrhp','rhp','prospectus'].includes(ipo.lifecycle?.stage) && !ipo.openDate) pipeline++;
    if (ipo.validation?.status === 'conflict') conflicts++;
  }

  const cards = [
    ['Open now', counts.open, 'Accepting bids'],
    ['Upcoming', counts.upcoming, 'Scheduled + filing pipeline'],
    ['SEBI pipeline', pipeline, 'Pre-exchange filings'],
    ['Listed', counts.listed, 'Historical listings'],
    ['Data conflicts', conflicts, conflicts ? 'Review required' : 'No flagged conflicts']
  ];
  els.stats.innerHTML = cards.map(([label, value, note]) =>
    `<article class="stat"><div class="stat-label">${label}</div><div class="stat-value">${Number(value).toLocaleString('en-IN')}</div><div class="stat-note">${note}</div></article>`
  ).join('');
}

function renderSourceHealth() {
  if (!els.health) return;
  const health = state.meta.sourceHealth || {};
  const sources = ['NSE-live', 'NSE-history', 'SEBI', 'BSE'];
  els.health.innerHTML = sources.map(name => {
    const item = health[name];
    if (!item) return `<div class="health-item"><span class="health-dot health-unknown"></span><strong>${name}</strong><span>not checked</span></div>`;
    const ok = !!item.ok;
    const note = ok ? `${Number(item.records || 0).toLocaleString('en-IN')} rows` : 'refresh failed';
    return `<div class="health-item"><span class="health-dot ${ok ? 'health-ok' : 'health-bad'}"></span><strong>${name}</strong><span>${escapeHtml(note)}</span></div>`;
  }).join('');
}

function companyLink(ipo) {
  const label = escapeHtml(ipo.company || 'Unknown');
  if (!ipo.profilePath) return label;
  return `<a class="company-name-link" href="${escapeAttr(ipo.profilePath)}" aria-label="Open ${escapeAttr(ipo.company || 'IPO')} permanent profile">${label}</a>`;
}

function renderTable() {
  const rows = filtered();
  els.empty.classList.toggle('hidden', rows.length > 0);
  els.rows.innerHTML = rows.map(ipo => {
    const status = derivedStatus(ipo);
    const sources = sourceCount(ipo);
    return `<tr data-id="${escapeAttr(ipo.id)}">
      <td class="company">${companyLink(ipo)}<span class="symbol">${escapeHtml(ipo.symbol || ipo.exchange || '')}</span></td>
      <td>${badge(status)}</td>
      <td>${escapeHtml(ipo.board || '—')}</td>
      <td><span class="stage-chip">${escapeHtml(filingStage(ipo))}</span></td>
      <td>${priceBand(ipo)}</td>
      <td>${prettyDate(ipo.openDate)}</td>
      <td>${prettyDate(ipo.closeDate)}</td>
      <td>${money(ipo.issueSizeCr)}</td>
      <td>${x(ipo.subscription?.total)}</td>
      <td>${listingReturn(ipo)}</td>
      <td>${validationBadge(ipo)}<span class="source-count">${sources} source${sources === 1 ? '' : 's'}</span></td>
    </tr>`;
  }).join('');
}

function renderYears() {
  const years = [...new Set(
    state.data.map(ipo => (ipo.openDate || ipo.listingDate || ipo.lifecycle?.stageDate || '').slice(0, 4)).filter(Boolean)
  )].sort().reverse();
  els.year.innerHTML = '<option value="all">All years</option>' + years.map(year => `<option value="${year}">${year}</option>`).join('');
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
    state.masterById = new Map((payload.ipos || []).map(ipo => [String(ipo.id), ipo]));
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
    if (!profile || String(profile.id) !== key) throw new Error('Embedded profile record missing or mismatched');
    const detail = { ...summary, ...profile };
    state.detailById.set(key, detail);
    return detail;
  } catch (error) {
    // During rollout an old route may not contain embedded JSON yet. Fall back
    // to the canonical file once, then stop paying that cost after routes rebuild.
    console.warn(`Could not lazy-load embedded IPO profile ${key}; using compatibility fallback`, error);
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

async function prepareAndOpenDetail(id) {
  const key = String(id);
  const detail = await loadIpoDetail(key);
  if (!detail) return;
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
  if (status === 'verified') return 'At least two independent official sources are attached to this record.';
  if (status === 'conflict') return 'One or more comparable fields disagree across exchange sources.';
  return 'Only one official source currently supports the comparable issue fields.';
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
  return String(value ?? '').replace(/[&<>'"]/g, char => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;'
  }[char]));
}
function escapeAttr(value) { return escapeHtml(value); }

let renderFrame = 0;
function scheduleTableRender() {
  if (renderFrame) cancelAnimationFrame(renderFrame);
  renderFrame = requestAnimationFrame(() => {
    renderFrame = 0;
    renderTable();
  });
}

function bind() {
  document.querySelectorAll('.tab').forEach(button => button.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    button.classList.add('active');
    state.activeStatus = button.dataset.status;
    renderTable();
  }));
  els.search.addEventListener('input', event => {
    state.search = event.target.value;
    scheduleTableRender();
  });
  els.board.addEventListener('change', event => {
    state.board = event.target.value;
    renderTable();
  });
  els.year.addEventListener('change', event => {
    state.year = event.target.value;
    renderTable();
  });
  els.rows.addEventListener('click', event => {
    if (event.target.closest('a,button')) return;
    const row = event.target.closest('tr[data-id]');
    if (row && els.rows.contains(row)) prepareAndOpenDetail(row.dataset.id);
  });
  els.dialogClose.addEventListener('click', () => els.dialog.close());
  els.dialog.addEventListener('click', event => {
    if (event.target === els.dialog) els.dialog.close();
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
  bind();
  try {
    const payload = await loadDashboardPayload();
    state.data = payload.ipos || [];
    state.meta = payload.meta || {};
    state.summaryMode = Number(state.meta.publicSummaryVersion || 0) >= 1;
    state.byId = new Map(state.data.map(ipo => [String(ipo.id), ipo]));
    state.indexById = new Map(state.data.map((ipo, index) => [String(ipo.id), index]));

    renderYears();
    renderStats();
    renderSourceHealth();
    renderTable();

    const generated = state.meta.generatedAt ? formatTimestamp(state.meta.generatedAt) : 'unknown';
    els.freshness.textContent = state.meta.seed ? `Preview data · ${generated}` : `Updated ${generated}`;
    els.recordCount.textContent = `${state.data.length.toLocaleString('en-IN')} IPO records · schema v${state.meta.schemaVersion || 1}`;
  } catch (error) {
    els.freshness.textContent = 'Data load failed';
    els.empty.textContent = 'Could not load IPO data. Serve the folder through a local web server rather than opening index.html directly.';
    els.empty.classList.remove('hidden');
    console.error(error);
  }
}

init();
