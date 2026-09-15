/* Permanent company-route renderer.
 * Route HTML embeds one compact public record, so profile pages no longer need
 * to download and parse the multi-megabyte canonical IPO dataset.
 */

const IST_DATE_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  day: '2-digit', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata'
});
const IST_DAY_FORMATTER = new Intl.DateTimeFormat('en-CA', {
  year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'Asia/Kolkata'
});
const IST_TIMESTAMP_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short'
});
const IST_TIME_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit'
});
const IST_DATE_TIME_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
});

const money = value => value == null ? '—' : `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })} Cr`;
const rupees = value => value == null ? '—' : `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
const x = value => value == null ? '—' : `${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}×`;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, char => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;'
  }[char]));
}
function escapeAttr(value) { return escapeHtml(value); }

function prettyDate(value) {
  if (!value) return '—';
  const date = new Date(`${value}T00:00:00+05:30`);
  return Number.isNaN(date.getTime()) ? String(value) : IST_DATE_FORMATTER.format(date);
}

function formatTimestamp(value) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : `${IST_TIMESTAMP_FORMATTER.format(date)} IST`;
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

function badge(status) {
  return `<span class="badge badge-${escapeAttr(status)}">${escapeHtml(status)}</span>`;
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
  const sources = ipo.sources || (ipo.source ? [ipo.source] : []);
  return new Set(
    sources.map(source => String(source?.name || '').split(' ')[0]).filter(Boolean)
  ).size;
}

function validationBadge(ipo) {
  const status = ipo.validation?.status || 'single-source';
  const label = status === 'single-source' ? '1 source' : status;
  return `<span class="validation validation-${escapeAttr(status)}">${escapeHtml(label)}</span>`;
}

function validationCopy(ipo) {
  const status = ipo.validation?.status || 'single-source';
  if (status === 'verified') return 'At least two independent official sources are attached to this record.';
  if (status === 'conflict') return 'One or more comparable fields disagree across exchange sources.';
  return 'Only one official source currently supports the comparable issue fields.';
}

function formatObservation(value) {
  if (value == null) return '—';
  return typeof value === 'object' ? JSON.stringify(value) : String(value);
}

function p4History(ipo) {
  return (ipo.subscriptionHistory || [])
    .filter(row => row && row.capturedAt)
    .slice()
    .sort((a, b) => String(a.capturedAt).localeCompare(String(b.capturedAt)));
}

function p4Latest(ipo, history) {
  return history.length
    ? { ...(ipo.subscription || {}), ...history[history.length - 1] }
    : (ipo.subscription || {});
}

function p4TimeLabel(value, includeDate = false) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value || '—');
  return (includeDate ? IST_DATE_TIME_FORMATTER : IST_TIME_FORMATTER).format(date).replace(',', '');
}

function p4Chart(history) {
  if (!history.length) return '';
  const series = [['qib','QIB'], ['nii','NII / HNI'], ['retail','Retail / Individual'], ['total','Total']];
  const width = 860;
  const height = 310;
  const margin = { left:58, right:20, top:22, bottom:52 };
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;

  let maxValue = 1;
  const times = [];
  for (const row of history) {
    times.push(new Date(row.capturedAt).getTime());
    for (const [key] of series) {
      const value = Number(row[key]);
      if (row[key] != null && Number.isFinite(value)) maxValue = Math.max(maxValue, value);
    }
  }
  const roundedMax = maxValue <= 5
    ? Math.ceil(maxValue * 2) / 2
    : maxValue <= 20 ? Math.ceil(maxValue / 2) * 2 : Math.ceil(maxValue / 10) * 10;
  const validTimes = times.filter(Number.isFinite);
  const tMin = validTimes.length ? Math.min(...validTimes) : 0;
  const tMax = validTimes.length ? Math.max(...validTimes) : history.length - 1;

  const xAt = (row, index) => {
    const time = times[index];
    if (Number.isFinite(time) && tMax > tMin) {
      return margin.left + ((time - tMin) / (tMax - tMin)) * plotW;
    }
    return margin.left + (history.length <= 1 ? plotW / 2 : (index / (history.length - 1)) * plotW);
  };
  const yAt = value => margin.top + plotH - (Math.max(0, Number(value) || 0) / roundedMax) * plotH;

  const yTicks = [0, .25, .5, .75, 1].map(fraction => {
    const value = roundedMax * fraction;
    const y = yAt(value);
    return `<line class="sub-grid" x1="${margin.left}" y1="${y.toFixed(1)}" x2="${width - margin.right}" y2="${y.toFixed(1)}"></line><text class="sub-axis-label" x="${margin.left - 10}" y="${(y + 4).toFixed(1)}" text-anchor="end">${escapeHtml(x(value))}</text>`;
  }).join('');

  const indexes = [...new Set([
    0,
    Math.floor((history.length - 1) * .25),
    Math.floor((history.length - 1) * .5),
    Math.floor((history.length - 1) * .75),
    history.length - 1
  ])].filter(index => index >= 0);
  const xTicks = indexes.map(index => {
    const pointX = xAt(history[index], index);
    return `<text class="sub-axis-label" x="${pointX.toFixed(1)}" y="${height - 18}" text-anchor="middle">${escapeHtml(p4TimeLabel(history[index].capturedAt, true))}</text>`;
  }).join('');

  const lines = series.map(([key, label]) => {
    const points = history.map((row, index) => {
      if (row[key] == null) return null;
      const value = Number(row[key]);
      return Number.isFinite(value) ? { x:xAt(row, index), y:yAt(value), value, row } : null;
    }).filter(Boolean);
    if (!points.length) return '';
    const polyline = points.map(point => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(' ');
    const dots = points.map(point =>
      `<circle class="sub-point sub-${key}" cx="${point.x.toFixed(1)}" cy="${point.y.toFixed(1)}" r="4"><title>${escapeHtml(`${label}: ${x(point.value)} · ${formatTimestamp(point.row.capturedAt)}`)}</title></circle>`
    ).join('');
    return `<polyline class="sub-line sub-${key}" points="${polyline}"></polyline>${dots}`;
  }).join('');

  return `<div class="subscription-chart-wrap"><svg class="subscription-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="IPO subscription history chart">${yTicks}${xTicks}${lines}</svg></div>`;
}

function routeProfileHtml(ipo) {
  const subscription = companySubscriptionSection(ipo);
  const offerIntel = companyOfferIntel(ipo);
  const financials = companyFinancials(ipo);
  const documents = companyDocuments(ipo);
  const sources = companySourcesAndValidation(ipo);
  return `<div class="company-profile company-route-profile">
    ${companyNav(ipo)}
    <div class="company-profile-inner">
      ${companyHero(ipo)}
      <div class="company-kpis">${companyKpis(ipo)}</div>
      <section class="company-section" id="company-timeline"><div class="company-section-head"><div><h3 class="company-section-title">IPO lifecycle</h3><p class="company-section-subtitle">From SEBI filing through bidding, allotment and exchange listing.</p></div></div><div class="company-timeline">${companyTimeline(ipo)}</div></section>
      <div class="company-two-col"><div>${subscription}${offerIntel}${financials}${documents}${sources}</div>${companySidebar(ipo)}</div>
    </div>
  </div>`;
}

function bindRouteNavigation(root) {
  root.addEventListener('click', event => {
    const button = event.target.closest('[data-company-target]');
    if (!button || !root.contains(button)) return;
    const target = root.querySelector(`#${CSS.escape(button.dataset.companyTarget)}`);
    if (target) target.scrollIntoView({ behavior:'smooth', block:'start' });
  });
}

async function copyPermanentLink(button) {
  try {
    await navigator.clipboard.writeText(window.location.href);
    const original = button.textContent;
    button.textContent = 'Link copied ✓';
    setTimeout(() => { button.textContent = original; }, 1600);
  } catch (error) {
    console.warn('Could not copy URL', error);
  }
}

function embeddedProfile() {
  const node = document.getElementById('ipo-profile-data');
  if (!node) return null;
  try {
    const payload = JSON.parse(node.textContent || '{}');
    return payload?.ipo && typeof payload.ipo === 'object' ? payload.ipo : null;
  } catch (error) {
    console.warn('Could not parse embedded IPO profile', error);
    return null;
  }
}

function latestProfileTimestamp(ipo) {
  let latest = '';
  for (const source of ipo.sources || []) {
    const value = String(source?.asOf || '');
    if (value > latest) latest = value;
  }
  for (const value of [ipo.subscriptionAsOf, ipo.offerDocumentExtraction?.extractedAt]) {
    if (value && String(value) > latest) latest = String(value);
  }
  return latest || null;
}

async function fallbackMasterRecord(ipoId) {
  const response = await fetch('data/ipos.json', { cache:'no-cache' });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const payload = await response.json();
  return (payload.ipos || []).find(item => String(item.id) === String(ipoId)) || null;
}

async function initCompanyRoute() {
  const root = document.getElementById('companyPage');
  const freshness = document.getElementById('routeFreshness');
  const ipoId = document.body.dataset.ipoId;

  try {
    // New routes are self-contained. The master fetch is only a temporary
    // compatibility fallback for route files generated before template v3.
    const ipo = embeddedProfile() || await fallbackMasterRecord(ipoId);
    if (!ipo) {
      root.innerHTML = '<div class="company-route-error"><div class="eyebrow">IPO NOT FOUND</div><h1>This company route is no longer available.</h1><p>The company may have been renamed or merged into another official record.</p><a href="./">Return to IPO tracker</a></div>';
      return;
    }

    document.title = `${ipo.company} IPO | India IPO Tracker`;
    const description = document.querySelector('meta[name="description"]');
    if (description) {
      description.content = `${ipo.company} IPO details, issue dates, price band, subscription, SEBI documents, financials and official source validation.`;
    }

    const updatedAt = latestProfileTimestamp(ipo);
    freshness.textContent = updatedAt ? `Record updated ${formatTimestamp(updatedAt)}` : 'Official-source IPO profile';
    root.innerHTML = routeProfileHtml(ipo);
    bindRouteNavigation(root);

    const shareButton = document.getElementById('copyCompanyLink');
    if (shareButton) shareButton.addEventListener('click', () => copyPermanentLink(shareButton));
  } catch (error) {
    console.error(error);
    freshness.textContent = 'Data load failed';
    root.innerHTML = '<div class="company-route-error"><div class="eyebrow">DATA LOAD ERROR</div><h1>Could not load this IPO profile.</h1><p>Please retry in a moment.</p><a href="./">Return to IPO tracker</a></div>';
  }
}

document.addEventListener('DOMContentLoaded', initCompanyRoute);
