const state = { data: [], activeStatus: 'all', search: '', board: 'all', year: 'all', meta: {} };

const els = {
  rows: document.getElementById('ipoRows'), stats: document.getElementById('stats'),
  freshness: document.getElementById('freshness'), recordCount: document.getElementById('recordCount'),
  search: document.getElementById('search'), board: document.getElementById('boardFilter'),
  year: document.getElementById('yearFilter'), empty: document.getElementById('empty'),
  dialog: document.getElementById('detailDialog'), dialogTitle: document.getElementById('dialogTitle'),
  dialogBoard: document.getElementById('dialogBoard'), dialogBody: document.getElementById('dialogBody'),
  dialogClose: document.getElementById('dialogClose')
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

function filtered() {
  return state.data.filter(ipo => {
    const status = derivedStatus(ipo);
    const matchesStatus = state.activeStatus === 'all' || status === state.activeStatus;
    const matchesBoard = state.board === 'all' || ipo.board === state.board;
    const haystack = `${ipo.company || ''} ${ipo.symbol || ''}`.toLowerCase();
    const matchesSearch = haystack.includes(state.search.toLowerCase());
    const year = (ipo.openDate || ipo.listingDate || '').slice(0, 4);
    const matchesYear = state.year === 'all' || year === state.year;
    return matchesStatus && matchesBoard && matchesSearch && matchesYear;
  }).sort((a,b) => (b.openDate || b.listingDate || '').localeCompare(a.openDate || a.listingDate || ''));
}

function renderStats() {
  const counts = { open: 0, upcoming: 0, closed: 0, listed: 0, total: state.data.length };
  state.data.forEach(i => { const s = derivedStatus(i); if (counts[s] != null) counts[s]++; });
  const mainboard = state.data.filter(i => i.board === 'Mainboard').length;
  const cards = [
    ['Open now', counts.open, 'Accepting bids'], ['Upcoming', counts.upcoming, 'Scheduled / pipeline'],
    ['Closed', counts.closed, 'Awaiting listing / allotment'], ['Listed', counts.listed, 'Historical listings'],
    ['Mainboard', mainboard, `${state.data.length - mainboard} SME records`]
  ];
  els.stats.innerHTML = cards.map(([label,value,note]) => `<article class="stat"><div class="stat-label">${label}</div><div class="stat-value">${value.toLocaleString('en-IN')}</div><div class="stat-note">${note}</div></article>`).join('');
}

function renderTable() {
  const rows = filtered();
  els.empty.classList.toggle('hidden', rows.length > 0);
  els.rows.innerHTML = rows.map(ipo => {
    const status = derivedStatus(ipo);
    return `<tr data-id="${ipo.id}">
      <td class="company">${escapeHtml(ipo.company || 'Unknown')}<span class="symbol">${escapeHtml(ipo.symbol || ipo.exchange || '')}</span></td>
      <td>${badge(status)}</td><td>${escapeHtml(ipo.board || '—')}</td><td>${priceBand(ipo)}</td>
      <td>${prettyDate(ipo.openDate)}</td><td>${prettyDate(ipo.closeDate)}</td><td>${money(ipo.issueSizeCr)}</td>
      <td>${x(ipo.subscription?.total)}</td><td>${listingReturn(ipo)}</td>
    </tr>`;
  }).join('');
  els.rows.querySelectorAll('tr').forEach(row => row.addEventListener('click', () => openDetail(row.dataset.id)));
}

function renderYears() {
  const years = [...new Set(state.data.map(i => (i.openDate || i.listingDate || '').slice(0,4)).filter(Boolean))].sort().reverse();
  els.year.innerHTML = '<option value="all">All years</option>' + years.map(y => `<option value="${y}">${y}</option>`).join('');
}

function openDetail(id) {
  const ipo = state.data.find(i => i.id === id); if (!ipo) return;
  const status = derivedStatus(ipo);
  els.dialogTitle.textContent = ipo.company;
  els.dialogBoard.textContent = `${ipo.board || 'IPO'} · ${status.toUpperCase()}`;
  const details = [
    ['Price band', priceBand(ipo)], ['Lot size', ipo.lotSize ? `${ipo.lotSize.toLocaleString('en-IN')} shares` : '—'], ['Issue size', money(ipo.issueSizeCr)],
    ['Open date', prettyDate(ipo.openDate)], ['Close date', prettyDate(ipo.closeDate)], ['Allotment', prettyDate(ipo.allotmentDate)],
    ['Listing date', prettyDate(ipo.listingDate)], ['Subscription', x(ipo.subscription?.total)], ['Listing return', ipo.listing?.gainPct == null ? '—' : `${ipo.listing.gainPct > 0 ? '+' : ''}${ipo.listing.gainPct.toFixed(2)}%`],
    ['Fresh issue', money(ipo.freshIssueCr)], ['Offer for sale', money(ipo.ofsCr)], ['Shares offered', ipo.sharesOffered?.toLocaleString('en-IN') || '—']
  ];
  const source = ipo.source || {};
  els.dialogBody.innerHTML = `<div class="detail-grid">${details.map(([l,v]) => `<div class="detail-card"><div class="detail-label">${l}</div><div class="detail-value">${v}</div></div>`).join('')}</div>
    <div class="source-card"><strong>Source:</strong> ${escapeHtml(source.name || 'Unknown')}<br><strong>Observed:</strong> ${source.asOf ? new Date(source.asOf).toLocaleString('en-IN', { timeZone:'Asia/Kolkata' }) + ' IST' : '—'}<br>${source.url ? `<a href="${source.url}" target="_blank" rel="noopener">Open source page ↗</a>` : ''}</div>`;
  els.dialog.showModal();
}

function escapeHtml(str) { return String(str).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }

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
    renderYears(); renderStats(); renderTable();
    const generated = state.meta.generatedAt ? new Date(state.meta.generatedAt).toLocaleString('en-IN', { timeZone:'Asia/Kolkata', dateStyle:'medium', timeStyle:'short' }) : 'unknown';
    els.freshness.textContent = state.meta.seed ? `Preview data · ${generated} IST` : `Updated ${generated} IST`;
    els.recordCount.textContent = `${state.data.length.toLocaleString('en-IN')} IPO records`;
  } catch (err) {
    els.freshness.textContent = 'Data load failed';
    els.empty.textContent = 'Could not load data/ipos.json. Serve the folder through a local web server rather than opening index.html directly.';
    els.empty.classList.remove('hidden');
    console.error(err);
  }
}

init();
