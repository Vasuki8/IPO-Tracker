/* Shared company profile for quick views and permanent company routes. */
function companyInitials(name) {
  return (
    String(name || 'IPO')
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((word) => word[0])
      .join('') || 'IP'
  ).toUpperCase();
}
function companyPct(value) {
  return value == null
    ? '—'
    : `${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}%`;
}
function companyShares(value) {
  return value == null ? '—' : Number(value).toLocaleString('en-IN');
}
function companyText(value) {
  return value == null || value === '' ? '—' : String(value);
}
function companyDate(value) {
  return value ? prettyDate(value) : 'Not available';
}
function companyLatestDoc(ipo) {
  return (
    (ipo.documents || [])
      .slice()
      .sort((a, b) => String(b.filedDate || '').localeCompare(String(a.filedDate || '')))[0] || null
  );
}
function companyLatestSource(ipo) {
  return (
    (ipo.sources || (ipo.source ? [ipo.source] : []))
      .slice()
      .sort((a, b) => (Date.parse(b.asOf) || 0) - (Date.parse(a.asOf) || 0))[0] || null
  );
}
function companyHistory(ipo) {
  return typeof p4History === 'function' ? p4History(ipo) : ipo.subscriptionHistory || [];
}
function companySubscription(ipo, history = companyHistory(ipo)) {
  return typeof p4Latest === 'function' ? p4Latest(ipo, history) : ipo.subscription || {};
}
function companyHasSubscription(ipo) {
  return (
    ['qib', 'nii', 'retail', 'total'].some((key) => companySubscription(ipo)?.[key] != null) ||
    companyHistory(ipo).length > 0
  );
}
function companyHasOffer(ipo) {
  const issue = ipo.issueComposition || {};
  return (
    ipo.offerDocumentExtraction?.status === 'extracted' ||
    !!(
      (ipo.leadManagers || []).length ||
      ipo.registrar ||
      (ipo.promoters || []).length ||
      (ipo.objectsOfIssue || []).length ||
      issue.freshShares != null ||
      issue.ofsShares != null ||
      ipo.freshIssueCr != null ||
      ipo.ofsCr != null
    )
  );
}
function companySafeUrl(value) {
  if (!value) return '';
  try {
    const url = new URL(value, document.baseURI);
    return ['https:', 'http:'].includes(url.protocol) ? url.href : '';
  } catch {
    return '';
  }
}
const COMPANY_WATCHLIST_KEY = 'ipoTrackerWatchlist';
let companyWatchlistMemory = null;
let companyWatchlistPersisted = true;
const companyActionRoots = new WeakSet();

function companyParseWatchlist(value) {
  try {
    const ids = typeof value === 'string' ? JSON.parse(value) : value;
    return new Set(Array.isArray(ids) ? ids.filter((id) => typeof id === 'string') : []);
  } catch {
    return new Set();
  }
}
function companySavedIds() {
  if (typeof state !== 'undefined' && state.saved instanceof Set) return state.saved;
  if (companyWatchlistMemory == null) {
    try {
      companyWatchlistMemory = companyParseWatchlist(localStorage.getItem(COMPANY_WATCHLIST_KEY));
    } catch {
      companyWatchlistMemory = new Set();
      companyWatchlistPersisted = false;
    }
  }
  return companyWatchlistMemory;
}
function companySaveFeedback(saved, persisted) {
  if (!persisted)
    return `${saved ? 'Saved' : 'Removed'} for this visit only. Your browser could not store the watchlist.`;
  return saved ? 'Saved to your watchlist on this device.' : 'Removed from your watchlist.';
}
function companyWatchlistAction(ipo) {
  const saved = companySavedIds().has(String(ipo.id));
  return `<div class="company-watchlist-action"><button type="button" class="company-watchlist-button" data-company-save="${escapeAttr(ipo.id)}" aria-pressed="${saved}" aria-label="${saved ? 'Remove from watchlist' : 'Save to watchlist'}"><span aria-hidden="true">${saved ? '✓' : '+'}</span><span data-company-save-label>${saved ? 'Saved to watchlist' : 'Save to watchlist'}</span></button><p class="company-save-status" role="status" aria-live="polite">${!companyWatchlistPersisted && saved ? escapeHtml(companySaveFeedback(saved, false)) : ''}</p></div>`;
}
function syncCompanyWatchlist(root = document, announce = false) {
  const savedIds = companySavedIds();
  root.querySelectorAll('[data-company-save]').forEach((button) => {
    const saved = savedIds.has(button.dataset.companySave);
    button.setAttribute('aria-pressed', String(saved));
    button.setAttribute('aria-label', saved ? 'Remove from watchlist' : 'Save to watchlist');
    button.querySelector('[aria-hidden]').textContent = saved ? '✓' : '+';
    button.querySelector('[data-company-save-label]').textContent = saved
      ? 'Saved to watchlist'
      : 'Save to watchlist';
    const status = button
      .closest('.company-watchlist-action')
      ?.querySelector('.company-save-status');
    if (status && announce)
      status.textContent = companySaveFeedback(saved, companyWatchlistPersisted);
  });
}
function bindCompanyProfileActions(root) {
  syncCompanyWatchlist(root);
  if (companyActionRoots.has(root)) return;
  companyActionRoots.add(root);
  root.addEventListener('click', (event) => {
    const button = event.target.closest('[data-company-save]');
    if (!button || !root.contains(button)) return;
    const id = String(button.dataset.companySave);
    if (typeof toggleSaved === 'function') {
      toggleSaved(id);
      return;
    }
    const ids = companySavedIds();
    if (ids.has(id)) ids.delete(id);
    else ids.add(id);
    let persisted = true;
    try {
      localStorage.setItem(COMPANY_WATCHLIST_KEY, JSON.stringify([...ids]));
    } catch {
      persisted = false;
    }
    document.dispatchEvent(
      new CustomEvent('ipo:watchlist-change', {
        detail: { ids: [...ids], persisted },
      }),
    );
  });
}
document.addEventListener('ipo:watchlist-change', (event) => {
  if (!Array.isArray(event.detail?.ids)) return;
  companyWatchlistMemory = companyParseWatchlist(event.detail.ids);
  companyWatchlistPersisted = event.detail.persisted !== false;
  syncCompanyWatchlist(document, true);
});
window.addEventListener('storage', (event) => {
  // The dashboard owns its storage listener and publishes the same event.
  if (
    typeof toggleSaved === 'function' ||
    (event.key !== COMPANY_WATCHLIST_KEY && event.key !== null)
  )
    return;
  const ids = companyParseWatchlist(event.newValue);
  document.dispatchEvent(
    new CustomEvent('ipo:watchlist-change', {
      detail: { ids: [...ids], persisted: true },
    }),
  );
});

function companyHeading(title, level = 'h3') {
  const tag = level === 'h2' ? 'h2' : 'h3';
  return `<${tag} class="company-section-title">${escapeHtml(title)}</${tag}>`;
}
function companyTimeline(ipo) {
  const today = currentIstDate();
  const document = companyLatestDoc(ipo);
  const filingStageDate = ['drhp', 'udrhp', 'rhp', 'prospectus'].includes(ipo.lifecycle?.stage)
    ? ipo.lifecycle.stageDate
    : null;
  const filingDate = document?.filedDate || filingStageDate || null;
  const items = [
    [
      'Latest filing',
      filingDate,
      document?.filedDate
        ? document.type || 'Offer document'
        : filingDate
          ? filingStage(ipo)
          : 'Dated filing not available',
    ],
    ['Opens', ipo.openDate, 'Bidding opens', 'openDate'],
    ['Closes', ipo.closeDate, 'Bidding closes', 'closeDate'],
    ['Allotment', ipo.allotmentDate, 'Basis of allotment', 'allotmentDate'],
    ['Listing', ipo.listingDate, 'Exchange listing', 'listingDate'],
  ];
  return items
    .map(([label, date, note, field]) => {
      const status = date === today ? 'current' : date && date < today ? 'done' : '';
      return `<div class="company-timeline-step ${status}"><div class="company-timeline-dot" aria-hidden="true">${status === 'done' ? '✓' : status === 'current' ? '•' : ''}</div><div class="company-timeline-label">${escapeHtml(label)}</div><div class="company-timeline-date">${escapeHtml(companyDate(date))}</div><div class="company-timeline-note">${escapeHtml(note)}</div>${field ? IPOQuality.note(ipo, field) : ''}</div>`;
    })
    .join('');
}
function companyKpis(ipo) {
  const latest = companySubscription(ipo);
  const asOf = latest.observedAt;
  const gain = ipo.listing?.gainPct;
  const lotNote =
    ipo.lotSize && ipo.priceBand?.max != null
      ? `One lot at cap: ${rupees(Number(ipo.lotSize) * Number(ipo.priceBand.max))}`
      : 'Shares per lot';
  const cards = [
    ['Price band', priceBand(ipo), 'Price per share', '', 'priceBand'],
    ['Issue size', money(ipo.issueSizeCr), 'Total offer value', '', 'issueSizeCr'],
    ['Bid lot', ipo.lotSize == null ? '—' : `${companyShares(ipo.lotSize)} shares`, lotNote, '', 'lotSize'],
    [
      'Subscription',
      x(latest.total),
      IPOQuality.freshness(latest),
      '',
    ],
    [
      'Listing return',
      gain == null ? '—' : `${gain > 0 ? '+' : ''}${Number(gain).toFixed(2)}%`,
      ipo.listingDate ? companyDate(ipo.listingDate) : 'Listing date not available',
      gain == null || gain === 0 ? '' : gain > 0 ? 'positive' : 'negative',
    ],
  ];
  return cards
    .map(
      ([label, value, note, tone, field]) =>
        `<div class="company-kpi"><div class="company-kpi-label">${escapeHtml(label)}</div><div class="company-kpi-value ${tone}">${escapeHtml(value)}</div><div class="company-kpi-note">${escapeHtml(note)}</div>${field ? IPOQuality.note(ipo, field) : ''}</div>`,
    )
    .join('');
}
function companyCompositionValue(issue, field, currency = false) {
  if (issue[field] == null) return null;
  const value = currency ? money(issue[field]) : `${companyShares(issue[field])} shares`;
  return `${issue.qualifiers?.[field] === 'up_to' ? 'Up to ' : ''}${value}`;
}
function companyOverviewFacts(ipo) {
  const issue = ipo.issueComposition || {};
  const count = sourceCount(ipo);
  const facts = [
    ['Board', ipo.board],
    ['Exchange', ipo.exchange],
    ['Symbol', ipo.symbol],
    ['Issue type', ipo.issueType || 'IPO'],
    ['Market lot', ipo.marketLot == null ? null : `${companyShares(ipo.marketLot)} shares`],
    ['Minimum bid quantity', ipo.minimumBidQuantity == null ? null : `${companyShares(ipo.minimumBidQuantity)} shares`],
    [
      'Fresh issue',
      ipo.freshIssueCr != null
        ? money(ipo.freshIssueCr)
        : companyCompositionValue(issue, 'freshValueCr', true) ?? companyCompositionValue(issue, 'freshShares'),
    ],
    [
      'Offer for sale',
      ipo.ofsCr != null
        ? money(ipo.ofsCr)
        : companyCompositionValue(issue, 'ofsValueCr', true) ?? companyCompositionValue(issue, 'ofsShares'),
    ],
    ['Filing stage', filingStage(ipo)],
    ['Sources attached', `${count} source${count === 1 ? '' : 's'}`],
    [
      'Promoter pre-issue',
      ipo.shareholding?.promoterPreIssuePct != null
        ? companyPct(ipo.shareholding.promoterPreIssuePct)
        : null,
    ],
  ];
  return `<dl class="company-fact-grid">${facts.map(([label, value]) => `<div class="company-fact"><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(companyText(value))}${['Fresh issue', 'Offer for sale'].includes(label) && IPOQuality.decision(ipo, 'issueComposition').state === 'provisional' ? IPOQuality.note(ipo, 'issueComposition') : ''}</dd></div>`).join('')}</dl>`;
}
function companySubscriptionSection(ipo, heading = 'h3') {
  if (!companyHasSubscription(ipo)) return '';
  const history = companyHistory(ipo);
  const latest = companySubscription(ipo, history);
  const source = latest.source || 'Source not available';
  const series = [
    ['qib', 'QIB'],
    ['nii', 'NII / HNI'],
    ['retail', 'Retail / Individual'],
    ['total', 'Total'],
  ];
  const cards = series
    .map(
      ([key, label]) =>
        `<div class="subscription-card"><span>${escapeHtml(label)}</span><strong>${x(latest[key])}</strong></div>`,
    )
    .join('');
  const chart = history.length && typeof p4Chart === 'function' ? p4Chart(history) : '';
  const historyCaption = chart
    ? `<p class="company-data-note">Collection history (not source-reporting times) · through ${escapeHtml(formatTimestamp(history[history.length - 1].capturedAt))}</p>`
    : '';
  const legend = chart
    ? `<div class="sub-legend" aria-label="Chart series">${series.map(([key, label]) => `<span class="sub-legend-item"><span class="sub-swatch sub-${key}" aria-hidden="true"></span>${escapeHtml(label)}</span>`).join('')}</div>`
    : '';
  const rows = history
    .slice(-10)
    .reverse()
    .map(
      (row) =>
        `<tr><th scope="row">${escapeHtml(IPOQuality.formatTime(row.collectedAt))}</th><td>${escapeHtml(IPOQuality.formatTime(row.observedAt))}</td><td>${x(row.qib)}</td><td>${x(row.nii)}</td><td>${x(row.retail)}</td><td>${x(row.total)}</td></tr>`,
    )
    .join('');
  const status = derivedStatus(ipo);
  const subtitle =
    status === 'open'
      ? 'Bidding is open. These are the latest reported demand multiples.'
      : status === 'closed' || status === 'listed'
        ? 'Bidding has closed. Latest recorded multiples are not necessarily the official final subscription.'
        : 'Reported category demand, with each available observation retained.';
  return `<section class="company-section" id="company-subscription"><div class="company-section-head"><div>${companyHeading('Subscription', heading)}<p class="company-section-subtitle">${subtitle}</p></div><span class="company-meta-chip">${escapeHtml(source)}</span></div><div class="subscription-latest-grid">${cards}</div><p class="company-data-note">${escapeHtml(IPOQuality.freshness(latest))}</p>${historyCaption}${legend}${chart}${rows ? `<details class="company-history-details"><summary>View ${Math.min(history.length, 10)} latest snapshot${history.length === 1 ? '' : 's'}${history.length > 10 ? ` of ${history.length}` : ''}</summary><div class="subscription-table-wrap" role="region" aria-label="Subscription snapshots" tabindex="0"><table class="subscription-table"><thead><tr><th scope="col">Collection check · IST</th><th scope="col">Source observation · IST</th><th scope="col">QIB</th><th scope="col">NII</th><th scope="col">Retail</th><th scope="col">Total</th></tr></thead><tbody>${rows}</tbody></table></div></details>` : ''}<p class="company-data-note">Multiples compare bids with the shares offered in each category. A dash means data is unavailable.</p></section>`;
}
function companyOfferIntel(ipo, heading = 'h3') {
  if (!companyHasOffer(ipo)) return '';
  const extraction = ipo.offerDocumentExtraction || {};
  const issue = ipo.issueComposition || {};
  const sourceUrl = companySafeUrl(extraction.documentUrl);
  const facts = [
    ['Registrar', ipo.registrar],
    ['Fresh issue value', ipo.freshIssueCr != null ? money(ipo.freshIssueCr) : companyCompositionValue(issue, 'freshValueCr', true)],
    ['Offer for sale value', ipo.ofsCr != null ? money(ipo.ofsCr) : companyCompositionValue(issue, 'ofsValueCr', true)],
    ['Fresh issue shares', companyCompositionValue(issue, 'freshShares')],
    ['OFS shares', companyCompositionValue(issue, 'ofsShares')],
    [
      'Valuation price used',
      issue.valuationPriceUsed != null ? rupees(issue.valuationPriceUsed) : null,
    ],
  ].filter(([, value]) => value != null);
  const people = (label, names) =>
    names.length
      ? `<div class="company-offer-group"><h4>${escapeHtml(label)}</h4><div class="company-people-list">${names.map((name) => `<div class="company-person">${escapeHtml(name)}</div>`).join('')}</div>`
      : '';
  const objects = ipo.objectsOfIssue || [];
  const compositionNote = IPOQuality.decision(ipo, 'issueComposition').state === 'provisional' ? IPOQuality.note(ipo, 'issueComposition') : '';
  return `<section class="company-section" id="company-offer-intel"><div class="company-section-head"><div>${companyHeading('Offer structure', heading)}<p class="company-section-subtitle">Issue composition, intermediaries and use of proceeds from official disclosures.</p></div>${sourceUrl ? `<a class="company-section-action" href="${escapeAttr(sourceUrl)}" target="_blank" rel="noopener noreferrer">View offer document ↗</a>` : ''}</div>${compositionNote}${facts.length ? `<dl class="company-fact-grid">${facts.map(([label, value]) => `<div class="company-fact"><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`).join('')}</dl>` : ''}${objects.length ? `<div class="company-offer-group" id="company-objects"><h4>Objects of the issue</h4><div class="company-object-list">${objects.map((item) => `<div class="company-object-row"><span>${escapeHtml(item.purpose || 'Purpose')}</span><strong>${money(item.amountCr)}</strong></div>`).join('')}</div></div>` : ''}${people('Lead managers', ipo.leadManagers || [])}${people('Promoters', ipo.promoters || [])}</section>`;
}
function companyFinancials(ipo, heading = 'h3') {
  const periods = ipo.financials?.periods || [];
  if (!periods.length) return IPOQuality.decision(ipo, 'financials').state === 'under_review' ? `<section class="company-section" id="company-financials">${companyHeading('Restated financials', heading)}${IPOQuality.note(ipo, 'financials')}<p class="company-data-note">The table is withheld pending field-level source verification.</p></section>` : '';
  return `<section class="company-section" id="company-financials"><div class="company-section-head"><div>${companyHeading('Restated financials', heading)}<p class="company-section-subtitle">Amount and reporting-period evidence is retained per field. Amounts in ₹ crore, except EPS (₹) and returns (%).</p></div></div>${IPOQuality.note(ipo, 'financials')}<div class="company-financial-wrap" role="region" aria-label="Restated financials; scroll horizontally for all columns" tabindex="0"><table class="company-financial-table"><thead><tr><th scope="col">Period</th><th scope="col">Revenue</th><th scope="col">EBITDA</th><th scope="col">PAT</th><th scope="col">Net worth</th><th scope="col">RONW / ROE</th><th scope="col">EPS</th></tr></thead><tbody>${periods.map((row) => `<tr><th scope="row">${escapeHtml(row.period || '—')}</th><td>${money(row.revenueCr)}</td><td>${money(row.ebitdaCr)}</td><td>${money(row.patCr)}</td><td>${money(row.netWorthCr)}</td><td>${companyPct(row.ronwPct ?? row.roePct)}</td><td>${row.eps == null ? '—' : rupees(row.eps)}</td></tr>`).join('')}</tbody></table></div><p class="company-data-note">A dash means data is unavailable. Compare periods of the same duration.</p></section>`;
}
function companyDocumentSource(url) {
  if (!url) return 'Source unavailable';
  const host = new URL(url).hostname.toLowerCase();
  for (const [domain, label] of [
    ['sebi.gov.in', 'SEBI'],
    ['bseindia.com', 'BSE'],
    ['nseindia.com', 'NSE'],
  ]) {
    if (host === domain || host.endsWith(`.${domain}`)) return label;
  }
  return host.replace(/^www\./, '');
}
function companyDocuments(ipo, heading = 'h3') {
  const docs = (ipo.documents || [])
    .slice()
    .sort((a, b) => String(b.filedDate || '').localeCompare(String(a.filedDate || '')));
  if (!docs.length) return '';
  return `<section class="company-section" id="company-documents"><div class="company-section-head"><div>${companyHeading('Official documents', heading)}<p class="company-section-subtitle">Open the source filing. The newest documents appear first.</p></div><span class="company-meta-chip">${docs.length} document${docs.length === 1 ? '' : 's'}</span></div><div class="company-link-list">${docs
    .map((doc) => {
      const url = companySafeUrl(doc.url);
      const source = companyDocumentSource(url);
      const original = String(doc.title || '');
      const concise = original.replace(/\s+/g, ' ').trim();
      const disclose =
        concise.length > 140 ||
        /BSE Bid Details|Cumulative Bid Details|Cumulative Demand Schedule/i.test(concise);
      const label =
        {
          PROSPECTUS: 'Prospectus',
          'FINAL PROSPECTUS': 'Final prospectus',
          'ABRIDGED PROSPECTUS': 'Abridged prospectus',
        }[String(doc.type || '').toUpperCase()] ||
        doc.type ||
        'Document';
      const meta = `${source} · ${doc.filedDate ? companyDate(doc.filedDate) : 'Filing date not available'}`;
      const inner = `<span class="company-link-copy"><strong>${escapeHtml(label)}</strong><small>${escapeHtml(meta)}</small>${!disclose && concise && concise.toLowerCase() !== String(label).toLowerCase() ? `<small class="company-document-short-title">${escapeHtml(original)}</small>` : ''}</span><span class="company-link-action">${url ? 'Open ↗' : 'Link unavailable'}</span>`;
      return `<div class="company-document-card">${url ? `<a class="company-link-row company-document-link" href="${escapeAttr(url)}" target="_blank" rel="noopener noreferrer">${inner}</a>` : `<div class="company-link-row">${inner}</div>`}${disclose ? `<details class="company-document-title"><summary>View original title</summary><p>${escapeHtml(original)}</p></details>` : ''}</div>`;
    })
    .join('')}</div></section>`;
}
function companySourcesAndValidation(ipo, heading = 'h3') {
  const sources = ipo.sources || (ipo.source ? [ipo.source] : []);
  const conflicts = (ipo.validation?.checks || []).filter((check) => check.match === false);
  const conflictClass = ipo.validation?.status === 'conflict' ? ' conflict' : '';
  const sourceHtml = sources.length
    ? `<div class="company-link-list">${sources
        .map((source) => {
          const url = companySafeUrl(source.url);
          return `<div class="company-link-row"><span class="company-link-copy"><strong>${escapeHtml(source.name || 'Source')}</strong><small>${escapeHtml(source.asOf ? formatTimestamp(source.asOf) : 'Timestamp not available')}</small></span>${url ? `<a class="company-section-action" href="${escapeAttr(url)}" target="_blank" rel="noopener noreferrer" aria-label="Open ${escapeAttr(source.name || 'source')}">Open ↗</a>` : ''}</div>`;
        })
        .join('')}</div>`
    : '<div class="company-empty-note">An official source trail is not available for this record yet.</div>';
  return `<section class="company-section" id="company-sources"><div class="company-section-head"><div>${companyHeading('Data quality & sources', heading)}<p class="company-section-subtitle">Verification applies to individual fields. Historical exchange disagreements below are diagnostic observations, not accepted offer terms.</p></div></div><div class="company-validation-box${conflictClass}">${validationBadge(ipo)}<span>${escapeHtml(validationCopy(ipo))}</span></div>${conflicts.length ? `<div class="company-conflict-list">${conflicts.map((check) => `<div class="company-conflict-row"><strong>${escapeHtml(check.field)}</strong><span>NSE · ${escapeHtml(formatObservation(check.nse))}</span><span>BSE · ${escapeHtml(formatObservation(check.bse))}</span></div>`).join('')}</div>` : ''}${sourceHtml}</section>`;
}
function companySidebar(ipo, heading = 'h3') {
  const latestSource = companyLatestSource(ipo);
  const extraction = ipo.offerDocumentExtraction || {};
  return `<aside class="company-side-stack" aria-label="Company reference information"><section class="company-section"><div class="company-section-head">${companyHeading('At a glance', heading)}</div>${companyOverviewFacts(ipo)}</section><section class="company-section"><div class="company-section-head">${companyHeading('Record freshness', heading)}</div><dl class="company-fact-grid"><div class="company-fact"><dt>Latest source record</dt><dd>${escapeHtml(latestSource?.name || '—')}</dd></div><div class="company-fact"><dt>Source record timestamp</dt><dd>${escapeHtml(latestSource?.asOf ? formatTimestamp(latestSource.asOf) : 'Not available')}</dd></div><div class="company-fact"><dt>Offer document processed</dt><dd>${escapeHtml(extraction.extractedAt ? formatTimestamp(extraction.extractedAt) : 'Not available')}</dd></div><div class="company-fact"><dt>Validation</dt><dd>${validationBadge(ipo)}</dd></div></dl><p class="company-data-note">Dates and timestamps use Indian Standard Time (IST). A later collection check does not make the source observation newer.</p></section></aside>`;
}
function companyNav(ipo) {
  const items = [
    ['Overview', 'company-overview', true],
    ['Timeline', 'company-timeline', true],
    ['Subscription', 'company-subscription', companyHasSubscription(ipo)],
    ['Offer structure', 'company-offer-intel', companyHasOffer(ipo)],
    ['Financials', 'company-financials', !!(ipo.financials?.periods || []).length],
    ['Documents', 'company-documents', !!(ipo.documents || []).length],
    ['Sources', 'company-sources', true],
  ].filter(([, , show]) => show);
  return `<nav class="company-nav" aria-label="Company profile sections">${items.map(([label, id], index) => `<button type="button" data-company-target="${id}"${index === 0 ? ' class="is-active" aria-current="location"' : ''}>${escapeHtml(label)}</button>`).join('')}</nav>`;
}
function companyHero(ipo, { standalone = false } = {}) {
  const status = derivedStatus(ipo);
  const filing = filingStage(ipo);
  const stage =
    {
      open: 'Bidding is open',
      upcoming: ipo.openDate ? 'Opens soon' : 'Awaiting issue schedule',
      listed: 'Listed on the exchange',
      closed: 'Bidding has closed',
    }[status] || 'In the IPO pipeline';
  const dateText =
    status === 'open'
      ? `Closing date · ${companyDate(ipo.closeDate)}`
      : status === 'listed' || status === 'closed'
        ? `Listing date · ${companyDate(ipo.listingDate)}`
        : `Opening date · ${companyDate(ipo.openDate)}`;
  const count = sourceCount(ipo);
  const title = standalone ? 'h1' : 'h2';
  const profileUrl = companySafeUrl(ipo.profilePath);
  return `<section class="company-hero-card" id="company-overview"><div class="company-identity"><div class="company-monogram" aria-hidden="true">${escapeHtml(companyInitials(ipo.company))}</div><div class="company-identity-copy"><div class="company-kicker">${escapeHtml([ipo.symbol, ipo.exchange].filter(Boolean).join(' · ') || 'Indian IPO')}</div><${title} class="company-hero-name">${escapeHtml(ipo.company || 'Unknown company')}</${title}><div class="company-chip-row">${badge(status)}<span class="company-meta-chip">${escapeHtml(ipo.board || 'Board unavailable')}</span>${filing !== '—' ? `<span class="company-meta-chip">${escapeHtml(filing)}</span>` : ''}${validationBadge(ipo)}</div><p class="company-hero-caption">${count} source${count === 1 ? '' : 's'} attached · ${ipo.openDate ? `Bidding ${companyDate(ipo.openDate)}${ipo.closeDate ? ` – ${companyDate(ipo.closeDate)}` : ' · closing date not available'}` : 'Bidding dates not available'}</p></div></div><div class="company-hero-side"><div class="company-side-highlight"><span>Current stage</span><strong>${escapeHtml(stage)}</strong><small>${escapeHtml(dateText)}</small></div>${companyWatchlistAction(ipo)}${!standalone && profileUrl ? `<a class="company-profile-link" href="${escapeAttr(profileUrl)}">Open full company profile <span aria-hidden="true">↗</span></a>` : ''}</div></section>`;
}
function companyProfileHtml(ipo, { standalone = false } = {}) {
  ipo = IPOQuality.sanitize(ipo);
  const heading = standalone ? 'h2' : 'h3';
  const sections = [
    companySubscriptionSection(ipo, heading),
    companyOfferIntel(ipo, heading),
    companyFinancials(ipo, heading),
    companyDocuments(ipo, heading),
  ].filter(Boolean);
  const sparse =
    sections.length <= 1 &&
    !(ipo.subscriptionHistory || []).length &&
    (ipo.documents || []).length <= 3 &&
    (ipo.objectsOfIssue || []).length <= 3 &&
    (ipo.leadManagers || []).length <= 4 &&
    (ipo.promoters || []).length <= 4;
  const main = `<div class="company-main-sections">${sections.join('')}${IPOQuality.panel(ipo)}${companySourcesAndValidation(ipo, heading)}</div>`;
  const sidebar = companySidebar(ipo, heading);
  return `<div class="company-profile${standalone ? ' company-route-profile' : ''}${sparse ? ' company-profile-sparse' : ''}">${companyNav(ipo)}<div class="company-profile-inner">${companyHero(ipo, { standalone })}<div class="company-kpis">${companyKpis(ipo)}</div><section class="company-section" id="company-timeline"><div class="company-section-head"><div>${companyHeading('IPO timeline', heading)}<p class="company-section-subtitle">Key dates from official filings through allotment and listing. Missing dates are marked Not available.</p></div><span class="company-meta-chip">All dates · IST</span></div><div class="company-timeline">${companyTimeline(ipo)}</div></section><div class="company-two-col">${sparse ? sidebar + main : main + sidebar}</div></div></div>`;
}
const companyNavigationCleanups = new WeakMap();
function bindCompanyProfileNavigation(root = els.dialogBody, { scrollRoot = root } = {}) {
  companyNavigationCleanups.get(root)?.();
  const nav = root.querySelector('.company-nav');
  if (!nav) return;
  const buttons = [...nav.querySelectorAll('[data-company-target]')];
  const sections = buttons.map((button) =>
    root.querySelector(`#${CSS.escape(button.dataset.companyTarget)}`),
  );
  const scroller = scrollRoot || window;
  let frame = 0;
  const setActive = (index) =>
    buttons.forEach((button, i) => {
      button.classList.toggle('is-active', i === index);
      if (i === index) button.setAttribute('aria-current', 'location');
      else button.removeAttribute('aria-current');
    });
  const update = () => {
    frame = 0;
    const edge = nav.getBoundingClientRect().bottom + 32;
    let active = 0;
    sections.forEach((section, index) => {
      if (section && section.getBoundingClientRect().top <= edge) active = index;
    });
    const atEnd = scrollRoot
      ? scrollRoot.scrollTop + scrollRoot.clientHeight >= scrollRoot.scrollHeight - 3
      : window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 3;
    if (atEnd && (scrollRoot ? scrollRoot.scrollTop : window.scrollY) > 0)
      active = buttons.length - 1;
    setActive(active);
  };
  const schedule = () => {
    if (!frame) frame = requestAnimationFrame(update);
  };
  const click = (event) => {
    const button = event.target.closest('[data-company-target]');
    if (!button || !nav.contains(button)) return;
    const index = buttons.indexOf(button);
    const section = sections[index];
    if (!section) return;
    event.preventDefault();
    const behavior = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      ? 'auto'
      : 'smooth';
    const offset = nav.offsetHeight + 16;
    if (scrollRoot)
      scrollRoot.scrollTo({
        top:
          section.getBoundingClientRect().top -
          scrollRoot.getBoundingClientRect().top +
          scrollRoot.scrollTop -
          offset,
        behavior,
      });
    else
      window.scrollTo({
        top: section.getBoundingClientRect().top + window.scrollY - offset,
        behavior,
      });
    setActive(index);
  };
  nav.addEventListener('click', click);
  scroller.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule);
  update();
  companyNavigationCleanups.set(root, () => {
    nav.removeEventListener('click', click);
    scroller.removeEventListener('scroll', schedule);
    window.removeEventListener('resize', schedule);
    if (frame) cancelAnimationFrame(frame);
  });
}
openDetail = function (id) {
  const ipo = state.byId.get(String(id));
  if (!ipo) return;
  els.dialog.classList.add('company-dialog');
  els.dialogTitle.textContent = ipo.company || 'IPO company profile';
  els.dialogBoard.textContent = 'COMPANY QUICK VIEW';
  els.dialogBody.innerHTML = companyProfileHtml(ipo);
  els.dialogBody.scrollTop = 0;
  if (!els.dialog.open) els.dialog.showModal();
  bindCompanyProfileNavigation(els.dialogBody);
  bindCompanyProfileActions(els.dialogBody);
};
