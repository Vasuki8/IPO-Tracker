/* Phase 4 UI: timestamped official-exchange QIB / NII / Retail / Total history.
 * Loaded after phase3.js and wraps its detail/source-health renderers.
 */

const phase3OpenDetail = openDetail;
const phase3RenderSourceHealth = renderSourceHealth;

const p4Esc = (value) =>
  String(value ?? "").replace(
    /[&<>'"]/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[
        c
      ],
  );
const p4X = (value) =>
  value == null
    ? "—"
    : `${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 })}×`;
const p4Series = [
  ["qib", "QIB"],
  ["nii", "NII / HNI"],
  ["retail", "Retail / Individual"],
  ["total", "Total"],
];

function phase4SourceHealth() {
  phase3RenderSourceHealth();
  if (!els.health) return;
  const h =
    state.meta?.sourceHealth?.["IPO-subscription"] ||
    state.meta?.sourceHealth?.["NSE-subscription"];
  if (!h || els.health.querySelector('[data-health="ipo-subscription"]'))
    return;
  const ok = !!h.ok;
  const attempted = Number(h.attempted || 0);
  const updated = Number(h.records || 0);
  const added = Number(h.snapshotsAdded || 0);
  const bseFallback = Number(h.bseFallbackRecords || 0);
  const sourceNote = bseFallback ? ` · BSE fallback ${bseFallback}` : "";
  const note = attempted
    ? `${updated}/${attempted} live issues · +${added} snapshots${sourceNote}`
    : "no open issues";
  els.health.insertAdjacentHTML(
    "beforeend",
    `<div class="health-item" data-health="ipo-subscription"><span class="health-dot ${ok ? "health-ok" : "health-bad"}"></span><strong>Subscription feed</strong><span>${p4Esc(note)}</span></div>`,
  );
}

renderSourceHealth = phase4SourceHealth;

function p4History(ipo) {
  return IPOQuality.history(ipo);
}

function p4Latest(ipo, history) {
  return IPOQuality.snapshot(ipo);
}

function p4TimeLabel(value, includeDate = false) {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value || "—");
  return d
    .toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata",
      day: includeDate ? "2-digit" : undefined,
      month: includeDate ? "short" : undefined,
      hour: "2-digit",
      minute: "2-digit",
    })
    .replace(",", "");
}

function p4Chart(history) {
  if (!history.length) return "";
  const width = 860;
  const height = 310;
  const margin = { left: 58, right: 20, top: 22, bottom: 52 };
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;
  const values = history.flatMap((row) =>
    p4Series
      .map(([key]) => (row[key] == null ? null : Number(row[key])))
      .filter((value) => value != null && Number.isFinite(value)),
  );
  const maxValue = Math.max(1, ...values);
  const roundedMax =
    maxValue <= 5
      ? Math.ceil(maxValue * 2) / 2
      : maxValue <= 20
        ? Math.ceil(maxValue / 2) * 2
        : Math.ceil(maxValue / 10) * 10;
  const times = history.map((row) => new Date(row.capturedAt).getTime());
  const validTimes = times.filter(Number.isFinite);
  const tMin = validTimes.length ? Math.min(...validTimes) : 0;
  const tMax = validTimes.length ? Math.max(...validTimes) : history.length - 1;
  const xAt = (row, index) => {
    const t = new Date(row.capturedAt).getTime();
    if (Number.isFinite(t) && tMax > tMin)
      return margin.left + ((t - tMin) / (tMax - tMin)) * plotW;
    return (
      margin.left +
      (history.length <= 1 ? plotW / 2 : (index / (history.length - 1)) * plotW)
    );
  };
  const yAt = (value) =>
    margin.top + plotH - (Math.max(0, Number(value) || 0) / roundedMax) * plotH;

  const yTicks = [0, 0.25, 0.5, 0.75, 1]
    .map((frac) => {
      const value = roundedMax * frac;
      const y = yAt(value);
      return `<line class="sub-grid" x1="${margin.left}" y1="${y.toFixed(1)}" x2="${width - margin.right}" y2="${y.toFixed(1)}"></line><text class="sub-axis-label" x="${margin.left - 10}" y="${(y + 4).toFixed(1)}" text-anchor="end">${p4Esc(p4X(value))}</text>`;
    })
    .join("");

  // Tick positions follow elapsed time, so clusters of observations cannot
  // crowd the labels. Keep endpoint labels inside the SVG plotting bounds.
  const hasTimeRange = validTimes.length > 1 && tMax > tMin;
  const tickCount = hasTimeRange ? Math.min(4, history.length) : 1;
  const xTicks = Array.from({ length: tickCount }, (_, index) => {
    const fraction = tickCount === 1 ? 0.5 : index / (tickCount - 1);
    const pointX = margin.left + fraction * plotW;
    const tickTime = validTimes.length ? tMin + fraction * (tMax - tMin) : null;
    const label =
      tickTime == null
        ? "Timestamp not available"
        : `${p4TimeLabel(new Date(tickTime).toISOString(), true)} IST`;
    const anchor =
      tickCount === 1
        ? "middle"
        : index === 0
          ? "start"
          : index === tickCount - 1
            ? "end"
            : "middle";
    return `<text class="sub-axis-label" x="${pointX.toFixed(1)}" y="${height - 18}" text-anchor="${anchor}">${p4Esc(label)}</text>`;
  }).join("");

  const lines = p4Series
    .map(([key, label]) => {
      const points = history
        .map((row, index) => {
          if (row[key] == null) return null;
          const value = Number(row[key]);
          return Number.isFinite(value)
            ? { x: xAt(row, index), y: yAt(value), value, row }
            : null;
        })
        .filter(Boolean);
      if (!points.length) return "";
      const polyline = points
        .map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`)
        .join(" ");
      const dots = points
        .map(
          (p) =>
            `<circle class="sub-point sub-${key}" cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4"><title>${p4Esc(`${label}: ${p4X(p.value)} · ${formatTimestamp(p.row.capturedAt)} · ${p.row.source || "source unavailable"}`)}</title></circle>`,
        )
        .join("");
      return `<polyline class="sub-line sub-${key}" points="${polyline}"></polyline>${dots}`;
    })
    .join("");

  return `<div class="subscription-chart-wrap"><svg class="subscription-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="IPO subscription collection-history chart">${yTicks}${xTicks}${lines}</svg></div>`;
}

function phase4DetailSection(ipo) {
  const history = p4History(ipo);
  const latest = p4Latest(ipo, history);
  const hasData =
    p4Series.some(([key]) => latest[key] != null) || history.length;
  if (!hasData) return "";

  const latestCards = p4Series
    .map(
      ([key, label]) =>
        `<div class="subscription-card"><span>${p4Esc(label)}</span><strong>${p4X(latest[key])}</strong></div>`,
    )
    .join("");
  const legend = p4Series
    .map(
      ([key, label]) =>
        `<span class="sub-legend-item"><i class="sub-swatch sub-${key}"></i>${p4Esc(label)}</span>`,
    )
    .join("");
  const historyNote = `${history.length.toLocaleString('en-IN')} stored checks`;
  const sourceLink = latest.sourceUrl
    ? `<a href="${p4Esc(latest.sourceUrl)}" target="_blank" rel="noopener noreferrer">Open subscription source ↗</a>` : '';
  const latestSource = latest.source || 'Source unavailable';

  const tableRows = history
    .slice(-8)
    .reverse()
    .map(
      (row) =>
        `<tr><td>${p4Esc(p4TimeLabel(row.capturedAt, true))}</td><td>${p4X(row.qib)}</td><td>${p4X(row.nii)}</td><td>${p4X(row.retail)}</td><td>${p4X(row.total)}</td></tr>`,
    )
    .join("");
  const historyTable = history.length
    ? `<div class="subscription-table-wrap"><table class="subscription-table"><thead><tr><th>Collection check · IST</th><th>QIB</th><th>NII</th><th>Retail</th><th>Total</th></tr></thead><tbody>${tableRows}</tbody></table></div>`
    : "";

  return `<section class="detail-section subscription-intelligence"><div class="subscription-section-head"><div><div class="section-title">Subscription collection history</div><p>Stored demand snapshots retain their original source. Collection time is not source observation time; secondary sources are identified separately.</p></div>${sourceLink}</div><div class="subscription-latest-grid">${latestCards}</div><div class="subscription-meta"><span>${p4Esc(historyNote)} · ${p4Esc(latestSource)}</span><span>${p4Esc(IPOQuality.freshness(latest))}</span></div>${history.length ? `<div class="sub-legend">${legend}</div>${p4Chart(history)}` : ""}${historyTable}</section>`;
}

openDetail = function (id) {
  phase3OpenDetail(id);
  const ipo = state.data.find((item) => item.id === id);
  if (!ipo || !els.dialogBody) return;
  const html = phase4DetailSection(ipo);
  if (html) els.dialogBody.insertAdjacentHTML("beforeend", html);
};
