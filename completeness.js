/* Coverage detail is loaded only when the Data & sources view is opened. */

let qualityDashboardLoaded = false;
let qualityDashboardRequest = null;

function qualityPct(value) {
  return value == null ? '—' : `${Number(value).toFixed(1)}%`;
}

function qualityLabel(field) {
  const labels = {
    'provenance.finalProspectus.priceBand': 'Final prospectus · price band',
    'provenance.finalProspectus.issueSizeCr': 'Final prospectus · issue size',
    'provenance.finalProspectus.ofsCr': 'Final prospectus · offer for sale',
    'provenance.finalProspectus.freshIssueCr': 'Final prospectus · fresh issue',
    'provenance.finalProspectus.objectsOfIssue': 'Final prospectus · objects of issue',
    'provenance.finalProspectus.issueComposition': 'Final prospectus · issue composition',
    'provenance.finalProspectus.listing.issuePrice': 'Final prospectus · issue price',
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
    'provenance.documents': 'Official documents',
  };
  return labels[field] || field.replace(/^[^.]+\./, '').replace(/([A-Z])/g, ' $1');
}

function renderQualityDashboard(audit, queue) {
  const root = document.getElementById('qualityDashboard');
  if (!root) return;

  const scores = audit?.scores || {};
  const segmentCounts = audit?.segmentCounts || {};
  const scoreCards = [
    [
      'Recent IPOs',
      scores.recentExchange2Y,
      `${Number(segmentCounts.recentExchange2Y || 0).toLocaleString('en-IN')} exchange IPOs · last 2 years`,
    ],
    [
      'Exchange data',
      scores.exchangeStage,
      `${Number(segmentCounts.exchangeStage || 0).toLocaleString('en-IN')} exchange-stage records`,
    ],
    [
      'Offer documents',
      scores.offerDocumentEligible,
      `${Number(segmentCounts.offerDocumentEligible || 0).toLocaleString('en-IN')} eligible records`,
    ],
    [
      'Live subscription',
      scores.openSubscription,
      `${Number(segmentCounts.openNow || 0).toLocaleString('en-IN')} open IPOs`,
    ],
    [
      'Key dates',
      scores.maturedLifecycle,
      `${Number(segmentCounts.maturedClosed || 0).toLocaleString('en-IN')} matured issues`,
    ],
    [
      'Source trail',
      scores.provenance,
      `${Number(audit?.recordCount || 0).toLocaleString('en-IN')} total records`,
    ],
  ];

  const fieldGaps = Object.entries(queue?.fieldGapCounts || {})
    .sort((a, b) => Number(b[1]) - Number(a[1]))
    .slice(0, 8);
  const queueRows = (queue?.queue || []).slice(0, 8);
  const today = currentIstDate();

  root.innerHTML = `<section class="quality-panel">
    <div class="quality-panel-head">
      <div><div class="eyebrow">COVERAGE REPORT</div><h2>Data coverage</h2><p>Coverage reflects the information expected at each IPO stage. Open and upcoming IPOs take priority when filling missing official data.</p></div>
      <span class="quality-stamp">Checked ${audit?.generatedAt ? escapeHtml(formatTimestamp(audit.generatedAt)) : 'date unavailable'}</span>
    </div>
    <div class="quality-grid">${scoreCards.map(([label, value, note]) => `<div class="quality-card"><span>${escapeHtml(label)}</span><strong>${qualityPct(value)}</strong><small>${escapeHtml(note)}</small></div>`).join('')}</div>
    <div class="quality-body">
      <div class="quality-subcard"><h3>Most common missing details</h3><p>The eight largest gaps currently eligible for a data update.</p><div class="quality-gap-list">${fieldGaps.length ? fieldGaps.map(([field, count]) => `<div class="quality-gap-row"><strong>${escapeHtml(qualityLabel(field))}</strong><span>${Number(count).toLocaleString('en-IN')} missing</span></div>`).join('') : '<div class="quality-empty">No eligible gaps found in this report.</div>'}</div></div>
      <div class="quality-subcard"><h3>Next IPOs to update</h3><p>Up to eight records, ordered by IPO stage, recency and missing official details.</p><div class="quality-queue-list">${queueRows.length ? queueRows.map((row) => `<div class="quality-queue-row"><div><a href="${escapeAttr(row.profilePath || `ipo/${row.id}/`)}"><strong>${escapeHtml(row.company || row.id || 'IPO')}</strong></a><span>${row.openDate ? `${row.openDate < today ? 'Opened' : 'Opens'} ${prettyDate(row.openDate)}` : escapeHtml(row.stage || '')}</span></div><span class="quality-priority">${escapeHtml(row.priorityLabel || '')}</span><span class="quality-missing">${Number(row.missingFieldCount || 0)} gaps · ${qualityPct(row.completenessPct)}</span></div>`).join('') : '<div class="quality-empty">No records are awaiting an update in this report.</div>'}</div></div>
    </div>
  </section>`;
}

function qualityLoadingNode(root) {
  let node = document.getElementById('qualityLoading');
  if (!node) {
    node = document.createElement('div');
    node.id = 'qualityLoading';
    root.insertAdjacentElement('beforebegin', node);
  }
  node.classList.add('quality-loading');
  return node;
}

function initQualityDashboard() {
  const root = document.getElementById('qualityDashboard');
  if (!root) return Promise.resolve(false);
  if (qualityDashboardLoaded) return Promise.resolve(true);
  if (qualityDashboardRequest) return qualityDashboardRequest;

  const status = qualityLoadingNode(root);
  status.hidden = false;
  status.classList.remove('quality-loading-error');
  status.setAttribute('role', 'status');
  status.textContent = 'Loading data coverage…';
  root.setAttribute('aria-busy', 'true');

  qualityDashboardRequest = (async () => {
    try {
      const [auditResponse, queueResponse] = await Promise.all([
        fetch('data/completeness.json', { cache: 'no-cache' }),
        fetch('data/missing_queue.json', { cache: 'no-cache' }),
      ]);
      if (!auditResponse.ok || !queueResponse.ok) throw new Error('Coverage report request failed');
      const [audit, queue] = await Promise.all([auditResponse.json(), queueResponse.json()]);
      if (
        !audit?.scores ||
        typeof audit.scores !== 'object' ||
        Array.isArray(audit.scores) ||
        !Array.isArray(queue?.queue)
      ) {
        throw new Error('Coverage report format is invalid');
      }
      renderQualityDashboard(audit, queue);
      qualityDashboardLoaded = true;
      status.hidden = true;
      return true;
    } catch (error) {
      status.classList.add('quality-loading-error');
      status.setAttribute('role', 'alert');
      status.innerHTML =
        '<span><strong>Coverage data is unavailable.</strong> Please try again.</span><button type="button" class="quality-retry">Retry</button>';
      status
        .querySelector('.quality-retry')
        .addEventListener('click', () => initQualityDashboard(), { once: true });
      console.warn('Could not load data coverage', error);
      return false;
    } finally {
      root.setAttribute('aria-busy', 'false');
      qualityDashboardRequest = null;
    }
  })();
  return qualityDashboardRequest;
}

document.addEventListener('ipo:view-change', (event) => {
  if (event.detail?.view === 'quality') initQualityDashboard();
});

// A direct link can select this view before the deferred script is ready.
document.addEventListener('DOMContentLoaded', () => {
  const view = document.getElementById('view-quality');
  if (view && !view.hidden) initQualityDashboard();
});
