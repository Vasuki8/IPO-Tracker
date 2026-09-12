/* Phase 3 UI: SEBI offer-document intelligence.
 * Loaded after app.js and wraps the existing detail/source-health renderers.
 */

const phase2OpenDetail = openDetail;
const phase2RenderSourceHealth = renderSourceHealth;

const p3Esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const p3Money = value => value == null ? '—' : `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })} Cr`;
const p3Shares = value => value == null ? '—' : Number(value).toLocaleString('en-IN');
const p3Pct = value => value == null ? '—' : `${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}%`;

function phase3SourceHealth() {
  phase2RenderSourceHealth();
  if (!els.health) return;
  const h = state.meta?.sourceHealth?.['Offer-docs'];
  if (!h || els.health.querySelector('[data-health="offer-docs"]')) return;
  const ok = !!h.ok;
  const note = h.attempted
    ? `${Number(h.records || 0).toLocaleString('en-IN')}/${Number(h.attempted || 0).toLocaleString('en-IN')} PDFs parsed`
    : 'no new PDFs';
  els.health.insertAdjacentHTML('beforeend', `<div class="health-item" data-health="offer-docs"><span class="health-dot ${ok ? 'health-ok' : 'health-bad'}"></span><strong>Offer docs</strong><span>${p3Esc(note)}</span></div>`);
}

renderSourceHealth = phase3SourceHealth;

function phase3DetailSections(ipo) {
  const extraction = ipo.offerDocumentExtraction || {};
  const issue = ipo.issueComposition || {};
  const leads = ipo.leadManagers || [];
  const promoters = ipo.promoters || [];
  const objects = ipo.objectsOfIssue || [];
  const periods = ipo.financials?.periods || [];
  const shareholding = ipo.shareholding || {};

  const hasIntel = extraction.status === 'extracted' || leads.length || ipo.registrar || promoters.length || objects.length || periods.length;
  if (!hasIntel) return '';

  const cards = [];
  if (leads.length) cards.push(['Book running lead manager', leads.join(', ')]);
  if (ipo.registrar) cards.push(['Registrar', ipo.registrar]);
  if (shareholding.promoterPreIssuePct != null) cards.push(['Promoter holding · pre-issue', p3Pct(shareholding.promoterPreIssuePct)]);
  if (issue.freshShares != null) cards.push(['Fresh issue shares', p3Shares(issue.freshShares)]);
  if (issue.ofsShares != null) cards.push(['OFS shares', p3Shares(issue.ofsShares)]);
  if (issue.valuationPriceUsed != null) cards.push(['Issue-size valuation price', `₹${Number(issue.valuationPriceUsed).toLocaleString('en-IN')}`]);

  const intelCards = cards.length ? `<div class="offer-intel-grid">${cards.map(([label, value]) => `
    <div class="offer-intel-card"><div class="detail-label">${p3Esc(label)}</div><div class="offer-intel-value">${p3Esc(value)}</div></div>`).join('')}</div>` : '';

  const promotersHtml = promoters.length ? `<div class="offer-subsection"><div class="section-title">Promoters</div><div class="chip-list">${promoters.map(name => `<span class="data-chip">${p3Esc(name)}</span>`).join('')}</div></div>` : '';

  const objectsHtml = objects.length ? `<div class="offer-subsection"><div class="section-title">Objects of the issue</div><div class="object-list">${objects.map(item => `
    <div class="object-row"><span>${p3Esc(item.purpose)}</span><strong>${p3Money(item.amountCr)}</strong></div>`).join('')}</div></div>` : '';

  const financialsHtml = periods.length ? `<div class="offer-subsection"><div class="section-title">Restated financials</div><div class="financial-table-wrap"><table class="financial-table">
    <thead><tr><th>Period</th><th>Revenue</th><th>EBITDA</th><th>PAT</th><th>Net worth</th><th>RONW</th><th>EPS</th></tr></thead>
    <tbody>${periods.map(row => `<tr>
      <td><strong>${p3Esc(row.period || '—')}</strong></td>
      <td>${p3Money(row.revenueCr)}</td><td>${p3Money(row.ebitdaCr)}</td><td>${p3Money(row.patCr)}</td><td>${p3Money(row.netWorthCr)}</td><td>${p3Pct(row.ronwPct ?? row.roePct)}</td><td>${row.eps == null ? '—' : `₹${Number(row.eps).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`}</td>
    </tr>`).join('')}</tbody>
  </table></div></div>` : '';

  const documentLink = extraction.documentUrl ? `<a href="${p3Esc(extraction.documentUrl)}" target="_blank" rel="noopener">Open source PDF ↗</a>` : '';
  const pageNote = extraction.pagesRead ? `${extraction.pagesRead}${extraction.pageCount ? `/${extraction.pageCount}` : ''} pages parsed` : 'Structured extraction';
  const extractionMeta = extraction.status === 'extracted' ? `<div class="offer-extraction-meta"><div><strong>SEBI ${p3Esc(extraction.documentType || 'offer document')}</strong><span>${p3Esc(pageNote)}${extraction.extractedAt ? ` · ${p3Esc(formatTimestamp(extraction.extractedAt))}` : ''}</span></div>${documentLink}</div>` : '';

  return `<section class="detail-section offer-intelligence"><div class="section-title">SEBI offer-document intelligence</div>${extractionMeta}${intelCards}${promotersHtml}${objectsHtml}${financialsHtml}</section>`;
}

openDetail = function(id) {
  phase2OpenDetail(id);
  const ipo = state.data.find(item => item.id === id);
  if (!ipo || !els.dialogBody) return;
  const html = phase3DetailSections(ipo);
  if (html) els.dialogBody.insertAdjacentHTML('beforeend', html);
};
