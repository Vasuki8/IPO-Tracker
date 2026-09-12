/* Phase 4.5 data-completeness dashboard. */

function qualityPct(value) {
  return value == null ? '—' : `${Number(value).toFixed(1)}%`;
}

function qualityLabel(field) {
  const labels = {
    'exchange.lotSize': 'Lot size',
    'exchange.issueSizeCr': 'Issue size',
    'exchange.issueComposition': 'Fresh issue / OFS',
    'exchange.priceBand': 'Price band',
    'offer.registrar': 'Registrar',
    'offer.leadManagers': 'Lead managers',
    'offer.promoters': 'Promoters',
    'offer.objectsOfIssue': 'Objects of issue',
    'offer.financials': 'Financials',
    'offer.promoterShareholding': 'Promoter shareholding',
    'subscription.qib': 'QIB subscription',
    'subscription.nii': 'NII subscription',
    'subscription.retail': 'Retail subscription',
    'subscription.total': 'Total subscription',
    'lifecycle.allotmentDate': 'Allotment date',
    'lifecycle.listingDate': 'Listing date',
    'provenance.sources': 'Source trail',
    'provenance.validation': 'Validation',
    'provenance.documents': 'Official documents'
  };
  return labels[field] || field.replace(/^[^.]+\./, '').replace(/([A-Z])/g, ' $1');
}

function renderQualityDashboard(audit, queue) {
  const root = document.getElementById('qualityDashboard');
  if (!root) return;

  const scores = audit?.scores || {};
  const segmentCounts = audit?.segmentCounts || {};
  const scoreCards = [
    ['Recent exchange', scores.recentExchange2Y, `${Number(segmentCounts.recentExchange2Y || 0).toLocaleString('en-IN')} IPOs · last 2 years`],
    ['Core exchange', scores.exchangeStage, `${Number(segmentCounts.exchangeStage || 0).toLocaleString('en-IN')} exchange-stage records`],
    ['Offer documents', scores.offerDocumentEligible, `${Number(segmentCounts.offerDocumentEligible || 0).toLocaleString('en-IN')} eligible records`],
    ['Live subscription', scores.openSubscription, `${Number(segmentCounts.openNow || 0).toLocaleString('en-IN')} open IPOs`],
    ['Lifecycle dates', scores.maturedLifecycle, `${Number(segmentCounts.maturedClosed || 0).toLocaleString('en-IN')} matured issues`],
    ['Provenance', scores.provenance, `${Number(audit?.recordCount || 0).toLocaleString('en-IN')} total records`]
  ];

  const fieldGaps = Object.entries(queue?.fieldGapCounts || {})
    .sort((a, b) => Number(b[1]) - Number(a[1]))
    .slice(0, 8);
  const queueRows = (queue?.queue || []).slice(0, 8);

  root.innerHTML = `<section class="quality-panel">
    <div class="quality-panel-head">
      <div><div class="eyebrow">PHASE 4.5 · DATA QUALITY</div><h2>Completeness audit & repair queue</h2><p>Lifecycle-aware coverage: fields are only considered missing once they should reasonably exist. Current and upcoming IPOs are repaired before historical records.</p></div>
      <span class="quality-stamp">Audit ${audit?.generatedAt ? escapeHtml(formatTimestamp(audit.generatedAt)) : 'pending'}</span>
    </div>
    <div class="quality-grid">${scoreCards.map(([label, value, note]) => `<div class="quality-card"><span>${escapeHtml(label)}</span><strong>${qualityPct(value)}</strong><small>${escapeHtml(note)}</small></div>`).join('')}</div>
    <div class="quality-body">
      <div class="quality-subcard"><h3>Largest actionable gaps</h3><p>Highest-count missing fields in the repair queue.</p><div class="quality-gap-list">${fieldGaps.length ? fieldGaps.map(([field, count]) => `<div class="quality-gap-row"><strong>${escapeHtml(qualityLabel(field))}</strong><span>${Number(count).toLocaleString('en-IN')} missing</span></div>`).join('') : '<div class="quality-empty">No actionable gaps found.</div>'}</div></div>
      <div class="quality-subcard"><h3>Next records to repair</h3><p>Priority queue generated from lifecycle stage, recency and missing official fields.</p><div class="quality-queue-list">${queueRows.length ? queueRows.map(row => `<div class="quality-queue-row"><div><a href="${escapeAttr(row.profilePath || `ipo/${row.id}/`)}"><strong>${escapeHtml(row.company || row.id || 'IPO')}</strong></a><span>${row.openDate ? ` · opens ${prettyDate(row.openDate)}` : ` · ${escapeHtml(row.stage || '')}`}</span></div><span class="quality-priority">${escapeHtml(row.priorityLabel || '')}</span><span class="quality-missing">${Number(row.missingFieldCount || 0)} gaps · ${qualityPct(row.completenessPct)}</span></div>`).join('') : '<div class="quality-empty">Repair queue is empty.</div>'}</div></div>
    </div>
  </section>`;
}

async function initQualityDashboard() {
  try {
    const [auditResponse, queueResponse] = await Promise.all([
      fetch(`data/completeness.json?v=${Date.now()}`),
      fetch(`data/missing_queue.json?v=${Date.now()}`)
    ]);
    if (!auditResponse.ok || !queueResponse.ok) return;
    const [audit, queue] = await Promise.all([auditResponse.json(), queueResponse.json()]);
    renderQualityDashboard(audit, queue);
  } catch (error) {
    console.warn('Could not load completeness dashboard', error);
  }
}

document.addEventListener('DOMContentLoaded', initQualityDashboard);
