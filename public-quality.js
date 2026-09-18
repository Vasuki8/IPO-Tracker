/* Shared public display contract. Pure helpers are also exercised under Node. */
(function (root) {
  'use strict';
  const labels = {
    final_verified: 'Final Prospectus verified', provisional: 'Provisional disclosure',
    under_review: 'Under review', awaiting_disclosure: 'Awaiting disclosure',
    source_unavailable: 'Source unavailable', reported: 'Reported',
  };
  const fieldNames = {
    priceBand: 'Price band', lotSize: 'Bid lot', marketLot: 'Market lot',
    minimumBidQuantity: 'Minimum bid quantity', issueSizeCr: 'Issue size',
    freshIssueCr: 'Fresh issue', ofsCr: 'Offer for sale', issueComposition: 'Issue composition',
    financials: 'Financials', promoters: 'Promoters', leadManagers: 'Lead managers',
    registrar: 'Registrar', objectsOfIssue: 'Use of proceeds', shareholding: 'Shareholding',
    'listing.issuePrice': 'Final issue price', listing: 'Listing data', subscription: 'Subscription',
    openDate: 'Opening date', closeDate: 'Closing date', listingDate: 'Listing date', allotmentDate: 'Allotment date',
  };
  const staticFields = ['priceBand', 'lotSize', 'marketLot', 'minimumBidQuantity', 'issueSizeCr',
    'freshIssueCr', 'ofsCr', 'issueComposition', 'financials', 'promoters', 'leadManagers',
    'registrar', 'objectsOfIssue', 'shareholding', 'listing.issuePrice'];
  const reasons = {
    source_review: 'Source evidence requires review. The affected value is withheld.',
    composition_review: 'Issue totals or their supporting evidence require review. The complete composition is withheld.',
    quarantined: 'This field is quarantined pending source review.',
    final_evidence_required: 'Matching field-level Final Prospectus evidence is not yet available. This is not proof that the earlier disclosure was wrong.',
    pending_source_repair: 'The retained value is withheld while its source evidence is reviewed. A correction needs matching evidence before publication.',
    document_conflict: 'This prospectus contains conflicting disclosures for this field. The value is withheld until authoritative source evidence resolves the conflict.',
    provisional_expired: 'The provisional bidding disclosure has expired. Final Prospectus verification is required.',
    legacy_projection: 'This cached public record predates field-level checks. Unverified static values are withheld; reload after the public snapshot is rebuilt.',
  };
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeUrl = value => { try { const u = new URL(value); return u.protocol === 'https:' && !u.username && !u.password ? u.href : null; } catch { return null; } };
  const istDay = (now = new Date()) => new Intl.DateTimeFormat('en-CA', {timeZone:'Asia/Kolkata', year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
  const timestamp = value => typeof value === 'string' && /(?:Z|[+-]\d\d:\d\d)$/.test(value) && Number.isFinite(Date.parse(value)) ? value : null;
  const formatTime = value => timestamp(value) ? new Intl.DateTimeFormat('en-IN', {timeZone:'Asia/Kolkata',day:'numeric',month:'short',year:'numeric',hour:'numeric',minute:'2-digit'}).format(new Date(value)) + ' IST' : 'unavailable';
  function decision(ipo, field, now = new Date()) {
    const value = (ipo.publicQuality?.version === 1 && ipo.publicQuality?.fields?.[field]) || {state:'under_review',reason:'legacy_projection'};
    if (value.state === 'provisional' && (!/^\d{4}-\d{2}-\d{2}$/.test(value.until || '') || value.until < istDay(now)))
      return {state:'under_review',reason:'provisional_expired'};
    return value;
  }
  function sanitize(ipo, now = new Date()) {
    const out = {...ipo, listing: {...(ipo.listing || {})}};
    // Defense in depth for old cached summaries/profiles. The canonical master
    // is never fetched as a compatibility fallback.
    for (const field of new Set([...staticFields, ...Object.keys(ipo.publicQuality?.fields || {})])) {
      const d = decision(ipo, field, now);
      if (!['final_verified','provisional','reported'].includes(d.state)) {
        if (field === 'listing.issuePrice') delete out.listing.issuePrice;
        else out[field] = null;
      }
    }
    if (out.listing && (ipo.publicQuality?.version !== 1 || (!out.listing.issuePrice && ipo.publicQuality?.fields?.['listing.issuePrice']))) delete out.listing.gainPct;
    if (ipo.publicQuality?.fields?.subscription?.state === 'under_review') out.subscriptionHistory = [];
    return out;
  }
  function note(ipo, field) {
    const d = decision(ipo, field), source = ipo.publicQuality?.sources?.[d.source];
    const baseUrl = safeUrl(source?.sourceUrl);
    const url = baseUrl && Number.isInteger(d.page) && d.page > 0 ? baseUrl.split('#')[0] + '#page=' + d.page : baseUrl;
    const label = labels[d.state] || labels.under_review;
    const title = reasons[d.reason] || (d.state === 'provisional' ? `Active-issue disclosure; valid through ${d.until}. Not final IPO terms.` : label);
    return `<small class="quality-note quality-${esc(d.state)}" data-quality-field="${esc(field)}" title="${esc(title)}">${esc(label)}${url ? ` <a href="${esc(url)}" target="_blank" rel="noopener noreferrer" aria-label="Source for ${esc(fieldNames[field] || field)}">Source ↗</a>` : ''}</small>`;
  }
  function overview(ipo) {
    if (ipo.publicQuality?.version !== 1) return '<span class="validation validation-conflict">Field verification unavailable</span>';
    const fields = Object.keys(ipo.publicQuality?.fields || {});
    const count = fields.filter(f => decision(ipo,f).state === 'under_review').length;
    return `<span class="validation ${count ? 'validation-conflict' : 'validation-single-source'}">${count ? 'Some fields under review' : 'Field-level evidence'}</span>`;
  }
  function sourceAuthority(source, url, declared) {
    if (declared === 'secondary' || /secondary/i.test(source || '')) return 'Secondary source';
    const official = new Set(['nseindia.com','www.nseindia.com','nsearchives.nseindia.com','archives.nseindia.com','bseindia.com','www.bseindia.com','bsesme.com','www.bsesme.com']);
    try { if (safeUrl(url) && official.has(new URL(url).hostname)) return 'Official exchange'; } catch { /* unknown */ }
    return 'Source authority unverified';
  }
  function snapshot(ipo) {
    return {...(ipo.subscription || {}), observedAt: ipo.subscriptionTimeBasis === 'collection-only' ? null : timestamp(ipo.subscriptionObservedAt),
      collectedAt: timestamp(ipo.subscriptionCollectedAt || ipo.subscriptionAsOf),
      source: ipo.subscriptionSource || null, sourceUrl: safeUrl(ipo.subscriptionSourceUrl),
      authority: sourceAuthority(ipo.subscriptionSource, ipo.subscriptionSourceUrl, ipo.subscriptionAuthority)};
  }
  function freshness(s) {
    const reported = s.observedAt ? `Source reported at ${formatTime(s.observedAt)}` : 'Source time unavailable';
    return `${reported} · Checked at ${formatTime(s.collectedAt)} · ${s.authority || sourceAuthority(s.source,s.sourceUrl)}`;
  }
  function history(ipo) {
    return (ipo.subscriptionHistory || []).filter(r => r && timestamp(r.capturedAt || r.collectedAt))
      .map(r => ({...r, observedAt:timestamp(r.observedAt), collectedAt:timestamp(r.collectedAt || r.capturedAt)}))
      .sort((a,b) => Date.parse(a.collectedAt) - Date.parse(b.collectedAt));
  }
  function panel(ipo) {
    const fields = Object.keys(ipo.publicQuality?.fields || {}).filter(f => f !== 'listing' && f !== 'subscription');
    return `<section class="company-section" id="company-field-quality"><h3>Field evidence</h3><p class="company-data-note">Verification applies to each field, not the whole IPO. Review holds remain in the audit trail; missing values are not zero. Provisional disclosures are not final terms.</p><dl class="quality-grid">${fields.map(f => `<div><dt>${esc(fieldNames[f] || f)}</dt><dd>${note(ipo,f)}${reasons[decision(ipo,f).reason] ? `<p class="company-data-note">${esc(reasons[decision(ipo,f).reason])}</p>` : ''}</dd></div>`).join('')}</dl></section>`;
  }
  root.IPOQuality = {labels, fieldNames, decision, sanitize, note, overview, snapshot, freshness, history, formatTime, sourceAuthority, panel};
  if (typeof module !== 'undefined' && module.exports) module.exports = root.IPOQuality;
})(globalThis);
