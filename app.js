const state = { data: [], activeStatus: 'all', search: '', board: 'all', year: 'all', meta: {} };

const els = {
  rows: document.getElementById('ipoRows'), stats: document.getElementById('stats'),
  freshness: document.getElementById('freshness'), recordCount: document.getElementById('recordCount'),
  search: document.getElementById('search'), board: document.getElementById('boardFilter'),
  year: document.getElementById('yearFilter'), empty: document.getElementById('empty'),
  dialog: document.getElementById('detailDialog'), dialogTitle: document.getElementById('dialogTitle'),
  dialogBoard: document.getElementById('dialogBoard'), dialogBody: document.getElementById('dialogBody'),
  dialogClose: document.getElementById('dialogClose'), health: document.getElementById('sourceHealth')
};

const money = v => v == null ? '—' : `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 2 })} Cr`;
const rupees = v => v == null ? '—' : `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
const x = v => v == null ? '—' : `${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 2 })}×`;
const prettyDate = v => {
  if (!v) return '—';
  const d = new Date(`${v}T00:00:00+05:30`);
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata' }).format(d);
};

function currentIstDate() {
  const parts = new Intl.DateTimeFormat('en-CA', { year:'numeric', month:'2-digit', day:'2-digit', timeZone:'Asia/Kolkata' }).formatToParts(new Date());
  const map = Object.fromEntries(parts.map(p => [p.type, p.value]));
  return `${map.year}-${map.month}-${map.day}`;
}

function derivedStatus(ipo) {
  const today = currentIstDate();
  if (ipo.openDate && today < ipo.openDate) return 'upcoming';
  if (ipo.openDate && ipo.closeDate && today >= ipo.openDate && today <= ipo.closeDate) return 'open';
  if (ipo.listingDate && today >= ipo.listingDate) return 'listed';
  if (ipo.closeDate && today > ipo.closeDate) return 'closed';
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
  const sign = pct > 0 ? '+' : '';
  return `<span class="${cls}">${sign}${pct.toFixed(2)}%</span>`;
}

function badge(status) { return `<span class="badge badge-${status}">${status}</span>`; }

function validationBadge(ipo) {
  const status = ipo.validation?.status || 'single-source';
  const label = status === 'single-source' ? '1 source' : status;
  return `<span class="validation validation-${status}">${escapeHtml(label)}</span>`;
}

function filingStage(ipo) {
  const docs = ipo.documents || [];
  const types = docs.map(d => (d.type || '').toUpperCase());
  if (types.some(t => t.includes('PROSPECTUS') && !t.includes('ABRIDGED'))) return 'Prospectus';
  if (types.some(t => t === 'RHP' || t.includes('RED HERRING'))) return 'RHP';
  if (types.some(t => t === 'UDRHP')) return 'UDRHP';
  if (types.some(t => t === 'DRHP')) return 'DRHP';
  const stage = ipo.lifecycle?.stage;
  return ({drhp:'DRHP', udrhp:'UDRHP', rhp:'RHP', prospectus:'Prospectus', exchange:'Exchange'})[stage] || '—';
}

function sourceCount(ipo) {
  const names = new Set((ipo.sources || (ipo.source ? [ipo.source] : [])).map(s => (s.name || '').split(' ')[0]).filter(Boolean));
  return names.size;
}

function filtered() {
  return state.data.filter(ipo => {
    const status = derivedStatus(ipo);
    const matchesStatus = state.activeStatus === 'all' || status === state.activeStatus;
    const matchesBoard = state.board === 'all' || ipo.board === state.board;
    const haystack = `${ipo.company || ''} ${ipo.symbol || ''}`.toLowerCase();
    const matchesSearch = haystack.includes(state.search.toLowerCase());
    const year = (ipo.openDate || ipo.listingDate || ipo.lifecycle?.stageDate || '').slice(0, 4);
    const matchesYear = state.year === 'all' || year === state.year;
    return matchesStatus && matchesBoard && matchesSearch && matchesYear;
  }).sort((a,b) => {
    // Strict opening-date order: latest opening date first. Records that do not
    // yet have an exchange opening date (for example early SEBI filings) stay
    // below all dated IPOs instead of being mixed in using filing/listing dates.
    const ad = a.openDate || '';
    const bd = b.openDate || '';
    if (ad && !bd) return -1;
    if (!ad && bd) return 1;
    if (ad !== bd) return bd.localeCompare(ad);
    return String(a.company || '').localeCompare(String(b.company || ''), 'en', { sensitivity: 'base' });
  });
}

function renderStats() {
  const counts = { open: 0, upcoming: 0, closed: 0, listed: 0, total: state.data.length };
  state.data.forEach(i => { const s = derivedStatus(i); if (counts[s] != null) counts[s]++; });
  const pipeline = state.data.filter(i => ['drhp','udrhp','rhp','prospectus'].includes(i.lifecycle?.stage) && !i.openDate).length;
  const conflicts = state.data.filter(i => i.validation?.status === 'conflict').length;
  const cards = [
    ['Open now', counts.open, 'Accepting bids'], ['Upcoming', counts.upcoming, 'Scheduled + filing pipeline'],
    ['SEBI pipeline', pipeline, 'Pre-exchange filings'], ['Listed', counts.listed, 'Historical listings'],
    ['Data conflicts', conflicts, conflicts ? 'Review required' : 'No flagged conflicts']
  ];
  els.stats.innerHTML = cards.map(([label,value,note]) => `<article class="stat"><div class="stat-label">${label}</div><div class="stat-value">${Number(value).toLocaleString('en-IN')}</div><div class="stat-note">${note}</div></article>`).join('');
}

function renderSourceHealth() {
  if (!els.health) return;
  const health = state.meta.sourceHealth || {};
  const sources = ['NSE-live','NSE-history','SEBI','BSE'];
  els.health.innerHTML = sources.map(name => {
    const h = health[name];
    if (!h) return `<div class="health-item"><span class="health-dot health-unknown"></span><strong>${name}</strong><span>not checked</span></div>`;
    const ok = !!h.ok;
    const note = ok ? `${Number(h.records || 0).toLocaleString('en-IN')} rows` : 'refresh failed';
    return `<div class="health-item"><span class="health-dot ${ok ? 'health-ok' : 'health-bad'}"></span><strong>${name}</strong><span>${escapeHtml(note)}</span></div>`;
  }).join('');
}

function renderTable() {
  const rows = filtered();
  els.empty.classList.toggle('hidden', rows.length > 0);
  els.rows.innerHTML = rows.map(ipo => {
    const status = derivedStatus(ipo);
    const sources = sourceCount(ipo);
    return `<tr data-id="${escapeHtml(ipo.id)}">
      <td class="company">${escapeHtml(ipo.company || 'Unknown')}<span class="symbol">${escapeHtml(ipo.symbol || ipo.exchange || '')}</span></td>
      <td>${badge(status)}</td><td>${escapeHtml(ipo.board || '—')}</td><td><span class="stage-chip">${escapeHtml(filingStage(ipo))}</span></td>
      <td>${priceBand(ipo)}</td><td>${prettyDate(ipo.openDate)}</td><td>${prettyDate(ipo.closeDate)}</td><td>${money(ipo.issueSizeCr)}</td>
      <td>${x(ipo.subscription?.total)}</td><td>${listingReturn(ipo)}</td><td>${validationBadge(ipo)}<span class="source-count">${sources} source${sources === 1 ? '' : 's'}</span></td>
    </tr>`;
  }).join('');
  els.rows.querySelectorAll('tr').forEach(row => row.addEventListener('click', () => openDetail(row.dataset.id)));
}

function renderYears() {
  const years = [...new Set(state.data.map(i => (i.openDate || i.listingDate || i.lifecycle?.stageDate || '').slice(0,4)).filter(Boolean))].sort().reverse();
  els.year.innerHTML = '<option value="all">All years</option>' + years.map(y => `<option value="${y}">${y}</option>`).join('');
}

function openDetail(id) {
  const ipo = state.data.find(i => i.id === id); if (!ipo) return;
  const status = derivedStatus(ipo);
  els.dialogTitle.textContent = ipo.company;
  els.dialogBoard.textContent = `${ipo.board || 'IPO'} · ${status.toUpperCase()} · ${filingStage(ipo)}`;
  const details = [
    ['Price band', priceBand(ipo)], ['Lot size', ipo.lotSize ? `${Number(ipo.lotSize).toLocaleString('en-IN')} shares` : '—'], ['Issue size', money(ipo.issueSizeCr)],
    ['Open date', prettyDate(ipo.openDate)], ['Close date', prettyDate(ipo.closeDate)], ['Allotment', prettyDate(ipo.allotmentDate)],
    ['Listing date', prettyDate(ipo.listingDate)], ['Subscription', x(ipo.subscription?.total)], ['Listing return', ipo.listing?.gainPct == null ? '—' : `${ipo.listing.gainPct > 0 ? '+' : ''}${ipo.listing.gainPct.toFixed(2)}%`],
    ['Fresh issue', money(ipo.freshIssueCr)], ['Offer for sale', money(ipo.ofsCr)], ['Filing stage', filingStage(ipo)]
  ];

  const docs = (ipo.documents || []).slice().sort((a,b) => (b.filedDate || '').localeCompare(a.filedDate || ''));
  const sources = ipo.sources || (ipo.source ? [ipo.source] : []);
  const conflicts = (ipo.validation?.checks || []).filter(c => c.match === false);

  const documentsHtml = docs.length ? `<section class="detail-section"><div class="section-title">Official documents</div><div class="doc-list">${docs.map(d => `
    <a class="doc-row" href="${escapeAttr(d.url)}" target="_blank" rel="noopener">
      <span><strong>${escapeHtml(d.type || 'Document')}</strong><small>${escapeHtml(d.title || '')}</small></span>
      <span>${prettyDate(d.filedDate)} ↗</span>
    </a>`).join('')}</div></section>` : '';

  const conflictsHtml = conflicts.length ? `<section class="detail-section conflict-panel"><div class="section-title">Cross-source conflicts</div>${conflicts.map(c => `
    <div class="conflict-row"><strong>${escapeHtml(c.field)}</strong><span>NSE: ${formatObservation(c.nse)}</span><span>BSE: ${formatObservation(c.bse)}</span></div>`).join('')}</section>` : '';

  const sourcesHtml = `<section class="detail-section"><div class="section-title">Source trail</div><div class="source-list">${sources.map(s => `
    <div class="source-row"><div><strong>${escapeHtml(s.name || 'Unknown source')}</strong><small>${s.asOf ? escapeHtml(formatTimestamp(s.asOf)) : '—'}</small></div>${s.url ? `<a href="${escapeAttr(s.url)}" target="_blank" rel="noopener">Open ↗</a>` : ''}</div>`).join('')}</div></section>`;

  els.dialogBody.innerHTML = `<div class="validation-banner ${ipo.validation?.status === 'conflict' ? 'validation-banner-conflict' : ''}">${validationBadge(ipo)}<span>${validationCopy(ipo)}</span></div>
    <div class="detail-grid">${details.map(([l,v]) => `<div class="detail-card"><div class="detail-label">${l}</div><div class="detail-value">${v}</div></div>`).join('')}</div>
    ${conflictsHtml}${documentsHtml}${sourcesHtml}`;
  els.dialog.showModal();
}

function validationCopy(ipo) {
  const status = ipo.validation?.status || 'single-source';
  if (status === 'verified') return 'At least two independent official sources are attached to this record.';
  if (status === 'conflict') return 'One or more comparable fields disagree across exchange sources.';
  return 'Only one official source currently supports the comparable issue fields.';
}

function formatObservation(v) {
  if (v == null) return '—';
  if (typeof v === 'object') return JSON.stringify(v);
  return String(v);
}

function formatTimestamp(v) {
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return v;
  return d.toLocaleString('en-IN', { timeZone:'Asia/Kolkata', dateStyle:'medium', timeStyle:'short' }) + ' IST';
}

function escapeHtml(str) { return String(str ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
function escapeAttr(str) { return escapeHtml(str); }

function bind() {
  document.querySelectorAll('.tab').forEach(btn => btn.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active')); btn.classList.add('active');
    state.activeStatus = btn.dataset.status; renderTable();
  }));
  els.search.addEventListener('input', e => { state.search = e.target.value; renderTable(); });
  els.board.addEventListener('change', e => { state.board = e.target.value; renderTable(); });
  els.year.addEventListener('change', e => { state.year = e.target.value; renderTable(); });
  els.dialogClose.addEventListener('click', () => els.dialog.close());
  els.dialog.addEventListener('click', e => { if (e.target === els.dialog) els.dialog.close(); });
}

async function init() {
  bind();
  try {
    const res = await fetch(`data/ipos.json?v=${Date.now()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const payload = await res.json();
    state.data = payload.ipos || []; state.meta = payload.meta || {};
    renderYears(); renderStats(); renderSourceHealth(); renderTable();
    const generated = state.meta.generatedAt ? formatTimestamp(state.meta.generatedAt) : 'unknown';
    els.freshness.textContent = state.meta.seed ? `Preview data · ${generated}` : `Updated ${generated}`;
    els.recordCount.textContent = `${state.data.length.toLocaleString('en-IN')} IPO records · schema v${state.meta.schemaVersion || 1}`;
  } catch (err) {
    els.freshness.textContent = 'Data load failed';
    els.empty.textContent = 'Could not load data/ipos.json. Serve the folder through a local web server rather than opening index.html directly.';
    els.empty.classList.remove('hidden');
    console.error(err);
  }
}

init();