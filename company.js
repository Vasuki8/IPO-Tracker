/* Rich adaptive IPO/company profile. Loaded after phase4.js and becomes the final
 * detail renderer while reusing the data/format helpers from earlier phases.
 */

function companyInitials(name) {
  const words = String(name || 'IPO').trim().split(/\s+/).filter(Boolean);
  return (words.slice(0, 2).map(w => w[0]).join('') || 'IP').toUpperCase();
}

function companyPct(value) {
  return value == null ? '—' : `${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}%`;
}

function companyShares(value) {
  return value == null ? '—' : Number(value).toLocaleString('en-IN');
}

function companyText(value) {
  return value == null || value === '' ? '—' : String(value);
}

function companyLatestDoc(ipo) {
  return (ipo.documents || []).slice().sort((a, b) => String(b.filedDate || '').localeCompare(String(a.filedDate || '')))[0] || null;
}

function companyLatestSource(ipo) {
  return (ipo.sources || (ipo.source ? [ipo.source] : [])).slice().sort((a, b) => String(b.asOf || '').localeCompare(String(a.asOf || '')))[0] || null;
}

function companyTimeline(ipo) {
  const today = currentIstDate();
  const filingDate = ipo.lifecycle?.stageDate || companyLatestDoc(ipo)?.filedDate || null;
  const items = [
    ['Filing', filingDate, filingStage(ipo)],
    ['Open', ipo.openDate, 'Bidding opens'],
    ['Close', ipo.closeDate, 'Bidding closes'],
    ['Allotment', ipo.allotmentDate, 'Basis of allotment'],
    ['Listing', ipo.listingDate, 'Exchange listing']
  ];

  return items.map(([label, date, note]) => {
    let cls = '';
    if (date && date < today) cls = 'done';
    if (date === today) cls = 'current';
    if (label === 'Filing' && !ipo.openDate && filingDate) cls = 'current';
    const dot = cls === 'done' ? '✓' : cls === 'current' ? '•' : '';
    return `<div class="company-timeline-step ${cls}">
      <div class="company-timeline-dot">${dot}</div>
      <div class="company-timeline-label">${escapeHtml(label)}</div>
      <div class="company-timeline-date">${date ? prettyDate(date) : escapeHtml(note || 'Pending')}</div>
    </div>`;
  }).join('');
}

function companyKpis(ipo) {
  const totalSub = ipo.subscription?.total;
  const listingGain = ipo.listing?.gainPct;
  const cards = [
    ['Price band', priceBand(ipo), ipo.priceBand?.max != null ? `Cap ${rupees(ipo.priceBand.max)}` : 'Issue pricing'],
    ['Issue size', money(ipo.issueSizeCr), 'Total issue'],
    ['Lot size', ipo.lotSize ? `${Number(ipo.lotSize).toLocaleString('en-IN')} shares` : '—', 'Shares per lot'],
    ['Subscription', x(totalSub), ipo.subscriptionAsOf ? `As of ${formatTimestamp(ipo.subscriptionAsOf)}` : 'Overall demand'],
    ['Listing return', listingGain == null ? '—' : `${listingGain > 0 ? '+' : ''}${Number(listingGain).toFixed(2)}%`, ipo.listingDate ? prettyDate(ipo.listingDate) : 'After listing']
  ];
  return cards.map(([label, value, note]) => `<div class="company-kpi">
    <div class="company-kpi-label">${escapeHtml(label)}</div>
    <div class="company-kpi-value">${value}</div>
    <div class="company-kpi-note">${escapeHtml(note)}</div>
  </div>`).join('');
}

function companyOverviewFacts(ipo) {
  const issue = ipo.issueComposition || {};
  const facts = [
    ['Board', ipo.board],
    ['Exchange', ipo.exchange],
    ['Symbol', ipo.symbol],
    ['Issue type', ipo.issueType || 'IPO'],
    ['Fresh issue', ipo.freshIssueCr != null ? money(ipo.freshIssueCr) : issue.freshShares != null ? `${companyShares(issue.freshShares)} shares` : null],
    ['Offer for sale', ipo.ofsCr != null ? money(ipo.ofsCr) : issue.ofsShares != null ? `${companyShares(issue.ofsShares)} shares` : null],
    ['Filing stage', filingStage(ipo)],
    ['Official sources', `${sourceCount(ipo)} source${sourceCount(ipo) === 1 ? '' : 's'}`],
    ['Promoter pre-issue', ipo.shareholding?.promoterPreIssuePct != null ? companyPct(ipo.shareholding.promoterPreIssuePct) : null]
  ];
  return `<div class="company-fact-grid">${facts.map(([label, value]) => `<div class="company-fact"><span>${escapeHtml(label)}</span><strong>${escapeHtml(companyText(value))}</strong></div>`).join('')}</div>`;
}

function companySubscriptionSection(ipo) {
  const history = typeof p4History === 'function' ? p4History(ipo) : (ipo.subscriptionHistory || []);
  const latest = typeof p4Latest === 'function' ? p4Latest(ipo, history) : (ipo.subscription || {});
  const hasData = ['qib', 'nii', 'retail', 'total'].some(k => latest?.[k] != null) || history.length;
  if (!hasData) return '';
  const cards = [
    ['QIB', latest.qib],
    ['NII / HNI', latest.nii],
    ['Retail / Individual', latest.retail],
    ['Total', latest.total]
  ].map(([label, value]) => `<div class="subscription-card"><span>${escapeHtml(label)}</span><strong>${x(value)}</strong></div>`).join('');

  const chart = history.length && typeof p4Chart === 'function' ? p4Chart(history) : '';
  const rows = history.slice(-10).reverse().map(row => `<tr>
    <td>${escapeHtml(typeof p4TimeLabel === 'function' ? p4TimeLabel(row.capturedAt, true) : formatTimestamp(row.capturedAt))}</td>
    <td>${x(row.qib)}</td><td>${x(row.nii)}</td><td>${x(row.retail)}</td><td>${x(row.total)}</td>
  </tr>`).join('');
  const latestSource = ipo.subscriptionSource || history[history.length - 1]?.source || 'Official exchange';

  return `<section class="company-section" id="company-subscription">
    <div class="company-section-head"><div><h3 class="company-section-title">Live subscription</h3><p class="company-section-subtitle">QIB, NII/HNI, Retail/Individual and total demand retained as timestamped changes during the bidding window.</p></div><span class="company-meta-chip">${escapeHtml(latestSource)}</span></div>
    <div class="subscription-latest-grid">${cards}</div>
    ${chart}
    ${rows ? `<div class="subscription-table-wrap"><table class="subscription-table"><thead><tr><th>Snapshot</th><th>QIB</th><th>NII</th><th>Retail</th><th>Total</th></tr></thead><tbody>${rows}</tbody></table></div>` : ''}
  </section>`;
}

function companyOfferIntel(ipo) {
  const extraction = ipo.offerDocumentExtraction || {};
  const issue = ipo.issueComposition || {};
  const leads = ipo.leadManagers || [];
  const promoters = ipo.promoters || [];
  const objects = ipo.objectsOfIssue || [];
  const hasData = extraction.status === 'extracted' || leads.length || ipo.registrar || promoters.length || objects.length || issue.freshShares != null || issue.ofsShares != null;
  if (!hasData) return '';

  const facts = [
    ['Registrar', ipo.registrar],
    ['Fresh issue shares', issue.freshShares != null ? companyShares(issue.freshShares) : null],
    ['OFS shares', issue.ofsShares != null ? companyShares(issue.ofsShares) : null],
    ['Valuation price used', issue.valuationPriceUsed != null ? rupees(issue.valuationPriceUsed) : null]
  ].filter(([, value]) => value != null && value !== '—');

  const leadHtml = leads.length ? `<div class="company-section"><div class="company-section-head"><div><h3 class="company-section-title">Lead managers</h3></div></div><div class="company-people-list">${leads.map(name => `<div class="company-person"><strong>${escapeHtml(name)}</strong></div>`).join('')}</div></div>` : '';
  const promoterHtml = promoters.length ? `<div class="company-section"><div class="company-section-head"><div><h3 class="company-section-title">Promoters</h3></div></div><div class="company-people-list">${promoters.map(name => `<div class="company-person"><strong>${escapeHtml(name)}</strong></div>`).join('')}</div></div>` : '';
  const objectsHtml = objects.length ? `<section class="company-section" id="company-objects"><div class="company-section-head"><div><h3 class="company-section-title">Objects of the issue</h3><p class="company-section-subtitle">Use of proceeds extracted from the official SEBI offer document.</p></div></div><div class="company-object-list">${objects.map(item => `<div class="company-object-row"><span>${escapeHtml(item.purpose || 'Purpose')}</span><strong>${money(item.amountCr)}</strong></div>`).join('')}</div></section>` : '';

  return `<section class="company-section" id="company-offer-intel">
    <div class="company-section-head"><div><h3 class="company-section-title">Offer-document intelligence</h3><p class="company-section-subtitle">Structured fields extracted from the official SEBI offer document.</p></div>${extraction.documentUrl ? `<a class="company-section-action" href="${escapeAttr(extraction.documentUrl)}" target="_blank" rel="noopener">Open source PDF ↗</a>` : ''}</div>
    ${facts.length ? `<div class="company-fact-grid">${facts.map(([label, value]) => `<div class="company-fact"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join('')}</div>` : ''}
  </section>${objectsHtml}${leadHtml}${promoterHtml}`;
}

function companyFinancials(ipo) {
  const periods = ipo.financials?.periods || [];
  if (!periods.length) return '';
  return `<section class="company-section" id="company-financials">
    <div class="company-section-head"><div><h3 class="company-section-title">Restated financials</h3><p class="company-section-subtitle">Financial history extracted from the official SEBI offer document.</p></div></div>
    <div class="company-financial-wrap"><table class="company-financial-table"><thead><tr><th>Period</th><th>Revenue</th><th>EBITDA</th><th>PAT</th><th>Net worth</th><th>RONW / ROE</th><th>EPS</th></tr></thead><tbody>
      ${periods.map(row => `<tr><td><strong>${escapeHtml(row.period || '—')}</strong></td><td>${money(row.revenueCr)}</td><td>${money(row.ebitdaCr)}</td><td>${money(row.patCr)}</td><td>${money(row.netWorthCr)}</td><td>${companyPct(row.ronwPct ?? row.roePct)}</td><td>${row.eps == null ? '—' : rupees(row.eps)}</td></tr>`).join('')}
    </tbody></table></div>
  </section>`;
}

function companyDocuments(ipo) {
  const docs = (ipo.documents || []).slice().sort((a,b) => String(b.filedDate || '').localeCompare(String(a.filedDate || '')));
  if (!docs.length) return '';
  return `<section class="company-section" id="company-documents"><div class="company-section-head"><div><h3 class="company-section-title">Official documents</h3><p class="company-section-subtitle">DRHP, UDRHP, RHP, prospectus and other official filing links retained with dates.</p></div></div><div class="company-link-list">
    ${docs.map(doc => `<a class="company-link-row" href="${escapeAttr(doc.url)}" target="_blank" rel="noopener"><span><strong>${escapeHtml(doc.type || 'Document')}</strong><small>${escapeHtml(doc.title || '')}${doc.filedDate ? ` · ${prettyDate(doc.filedDate)}` : ''}</small></span><span>Open ↗</span></a>`).join('')}
  </div></section>`;
}

function companySourcesAndValidation(ipo) {
  const sources = ipo.sources || (ipo.source ? [ipo.source] : []);
  const conflicts = (ipo.validation?.checks || []).filter(c => c.match === false);
  const validationStatus = ipo.validation?.status || 'single-source';
  const conflictClass = validationStatus === 'conflict' ? ' conflict' : '';
  const sourcesHtml = sources.length ? `<div class="company-link-list">${sources.map(source => `<div class="company-link-row"><span><strong>${escapeHtml(source.name || 'Official source')}</strong><small>${source.asOf ? escapeHtml(formatTimestamp(source.asOf)) : 'Timestamp unavailable'}</small></span>${source.url ? `<a class="company-section-action" href="${escapeAttr(source.url)}" target="_blank" rel="noopener">Open ↗</a>` : ''}</div>`).join('')}</div>` : '<div class="company-empty-note">No source trail is attached yet.</div>';
  const conflictsHtml = conflicts.length ? `<div class="company-conflict-list" style="margin-top:10px">${conflicts.map(c => `<div class="company-conflict-row"><strong>${escapeHtml(c.field)}</strong><span>NSE · ${escapeHtml(formatObservation(c.nse))}</span><span>BSE · ${escapeHtml(formatObservation(c.bse))}</span></div>`).join('')}</div>` : '';

  return `<section class="company-section" id="company-sources"><div class="company-section-head"><div><h3 class="company-section-title">Data quality & sources</h3><p class="company-section-subtitle">Every available official source is retained; comparable exchange conflicts are shown instead of overwritten.</p></div></div>
    <div class="company-validation-box${conflictClass}">${validationBadge(ipo)} ${escapeHtml(validationCopy(ipo))}</div>
    ${conflictsHtml}
    <div style="height:10px"></div>
    ${sourcesHtml}
  </section>`;
}

function companySidebar(ipo) {
  const latestSource = companyLatestSource(ipo);
  const extraction = ipo.offerDocumentExtraction || {};
  return `<div class="company-side-stack">
    <section class="company-section" style="margin-top:0"><div class="company-section-head"><div><h3 class="company-section-title">At a glance</h3></div></div>${companyOverviewFacts(ipo)}</section>
    ${ipo.registrar ? `<section class="company-section" style="margin-top:0"><div class="company-section-head"><div><h3 class="company-section-title">Key intermediary</h3></div></div><div class="company-person"><span><small>Registrar</small><strong>${escapeHtml(ipo.registrar)}</strong></span></div></section>` : ''}
    <section class="company-section" style="margin-top:0"><div class="company-section-head"><div><h3 class="company-section-title">Record freshness</h3></div></div><div class="company-fact-grid">
      <div class="company-fact"><span>Latest source</span><strong>${escapeHtml(latestSource?.name || '—')}</strong></div>
      <div class="company-fact"><span>Source timestamp</span><strong>${escapeHtml(latestSource?.asOf ? formatTimestamp(latestSource.asOf) : '—')}</strong></div>
      <div class="company-fact"><span>Offer-doc parse</span><strong>${escapeHtml(extraction.extractedAt ? formatTimestamp(extraction.extractedAt) : '—')}</strong></div>
      <div class="company-fact"><span>Validation</span><strong>${escapeHtml(ipo.validation?.status || 'single-source')}</strong></div>
    </div></section>
  </div>`;
}

function companyNav(ipo) {
  const items = [
    ['Overview', 'company-overview', true],
    ['Timeline', 'company-timeline', true],
    ['Subscription', 'company-subscription', !!(ipo.subscription?.total != null || (ipo.subscriptionHistory || []).length)],
    ['Financials', 'company-financials', !!(ipo.financials?.periods || []).length],
    ['Documents', 'company-documents', !!(ipo.documents || []).length],
    ['Sources', 'company-sources', true]
  ].filter(([, , show]) => show);
  return `<nav class="company-nav">${items.map(([label, id]) => `<button type="button" data-company-target="${id}">${escapeHtml(label)}</button>`).join('')}</nav>`;
}

function companyHero(ipo) {
  const status = derivedStatus(ipo);
  const latestSource = companyLatestSource(ipo);
  const filing = filingStage(ipo);
  const stageNote = status === 'open' ? 'Live bidding window' : status === 'upcoming' ? 'Pre-open monitoring' : status === 'listed' ? 'Listed issue' : status === 'closed' ? 'Bidding closed' : 'IPO pipeline';
  return `<section class="company-hero-card" id="company-overview">
    <div class="company-identity"><div class="company-monogram">${escapeHtml(companyInitials(ipo.company))}</div><div><div class="company-kicker">${escapeHtml(ipo.symbol || ipo.exchange || 'Indian IPO')}</div><h2 class="company-hero-name">${escapeHtml(ipo.company || 'Unknown company')}</h2><div class="company-chip-row">${badge(status)}<span class="company-meta-chip">${escapeHtml(ipo.board || 'Board unknown')}</span><span class="company-meta-chip">${escapeHtml(filing)}</span>${validationBadge(ipo)}<span class="company-meta-chip">${sourceCount(ipo)} official source${sourceCount(ipo) === 1 ? '' : 's'}</span></div></div></div>
    <div class="company-hero-side"><div class="company-side-highlight"><span>Current stage</span><strong>${escapeHtml(stageNote)}</strong><small>${status === 'open' && ipo.closeDate ? `Closes ${prettyDate(ipo.closeDate)}` : ipo.listingDate ? `Listing ${prettyDate(ipo.listingDate)}` : ipo.openDate ? `Opens ${prettyDate(ipo.openDate)}` : 'Monitoring official filings and exchange updates'}</small></div><div class="company-side-highlight"><span>Latest official source</span><strong>${escapeHtml(latestSource?.name || '—')}</strong><small>${latestSource?.asOf ? escapeHtml(formatTimestamp(latestSource.asOf)) : 'Timestamp unavailable'}</small></div></div>
  </section>`;
}

function bindCompanyProfileNavigation() {
  els.dialogBody.querySelectorAll('[data-company-target]').forEach(button => {
    button.addEventListener('click', () => {
      const target = els.dialogBody.querySelector(`#${CSS.escape(button.dataset.companyTarget)}`);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

openDetail = function(id) {
  const ipo = state.data.find(item => item.id === id);
  if (!ipo) return;
  els.dialog.classList.add('company-dialog');
  els.dialogTitle.textContent = ipo.company || 'IPO company profile';
  els.dialogBoard.textContent = `${ipo.symbol || ipo.exchange || 'IPO'} · ${derivedStatus(ipo).toUpperCase()} · COMPANY PROFILE`;

  const subscription = companySubscriptionSection(ipo);
  const offerIntel = companyOfferIntel(ipo);
  const financials = companyFinancials(ipo);
  const documents = companyDocuments(ipo);
  const sources = companySourcesAndValidation(ipo);

  els.dialogBody.innerHTML = `<div class="company-profile">
    ${companyNav(ipo)}
    <div class="company-profile-inner">
      ${companyHero(ipo)}
      <div class="company-kpis">${companyKpis(ipo)}</div>
      <section class="company-section" id="company-timeline"><div class="company-section-head"><div><h3 class="company-section-title">IPO lifecycle</h3><p class="company-section-subtitle">From SEBI filing through bidding, allotment and exchange listing.</p></div></div><div class="company-timeline">${companyTimeline(ipo)}</div></section>
      <div class="company-two-col">
        <div>
          ${subscription}
          ${offerIntel}
          ${financials}
          ${documents}
          ${sources}
        </div>
        ${companySidebar(ipo)}
      </div>
    </div>
  </div>`;

  bindCompanyProfileNavigation();
  els.dialog.showModal();
};
