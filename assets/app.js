let IPO_DATA = [];
const state = { board: "all", status: "all", query: "" };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[char]));
}

function fieldValue(field) {
  return field && field.value !== null && field.value !== undefined ? field.value : null;
}

function sourceStatus(field) {
  return field?.status || "missing";
}

function formatMoney(value) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value);
}

function formatCrores(value) {
  if (value === null || value === undefined) return "—";
  return `₹${new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(Number(value) / 10000000)} Cr`;
}

function formatShares(value) {
  if (value === null || value === undefined) return "—";
  return `${Number(value).toLocaleString("en-IN")} shares`;
}

function formatPriceBand(field, issuePriceField) {
  const band = fieldValue(field);
  if (band && typeof band === "object" && band.min !== null && band.max !== null) {
    return `${formatMoney(band.min)} – ${formatMoney(band.max)}`;
  }
  const issuePrice = fieldValue(issuePriceField);
  return issuePrice !== null ? formatMoney(issuePrice) : "—";
}

function formatDate(value) {
  if (!value) return "—";
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return escapeHtml(value);
  return parsed.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function dateRange(ipo) {
  const open = fieldValue(ipo.open_date);
  const close = fieldValue(ipo.close_date);
  if (!open && !close) return "—";
  if (open && close) return `${formatDate(open)} – ${formatDate(close)}`;
  return formatDate(open || close);
}

function statusBadge(status) {
  if (!status) return '<span class="status">UNKNOWN</span>';
  const label = String(status).toUpperCase();
  return `<span class="status status--${escapeHtml(status)}">${escapeHtml(label)}</span>`;
}

function sourceBadge(status) {
  const labels = {
    verified: "✓ VERIFIED",
    provisional: "PROVISIONAL",
    conflict: "CONFLICT",
    missing: "SOURCE MISSING"
  };
  return `<span class="source source--${escapeHtml(status)}">${labels[status] || "SOURCE MISSING"}</span>`;
}

function recordSourceStatus(ipo) {
  const statuses = [
    ipo.price_band, ipo.issue_price, ipo.issue_size_inr, IPOLotSize.lotSizeField(ipo),
    ipo.open_date, ipo.close_date, ipo.listing_date
  ].map(sourceStatus);
  if (statuses.includes("conflict")) return "conflict";
  if (statuses.includes("provisional")) return "provisional";
  if (statuses.every((status) => status === "verified")) return "verified";
  return "missing";
}

function filteredRows() {
  return IPO_DATA
    .filter((ipo) => {
      const boardMatch = state.board === "all" || String(ipo.board || "").toLowerCase() === state.board;
      const statusMatch = state.status === "all" || ipo.status === state.status;
      const haystack = [ipo.issuer_name, ipo.sector, ipo.board].filter(Boolean).join(" ").toLowerCase();
      const queryMatch = !state.query || haystack.includes(state.query);
      return boardMatch && statusMatch && queryMatch;
    })
    .sort(IPOOrder.compareNewestFirst);
}

function initials(name) {
  return String(name || "?").split(/\s+/).slice(0, 2).map((part) => part[0] || "").join("").toUpperCase();
}

function render() {
  const rows = filteredRows();
  $("#ipoRows").innerHTML = rows.map((ipo) => {
    const source = recordSourceStatus(ipo);
    return `
      <tr>
        <td class="company-cell"><div class="company-row"><div class="company-logo">${escapeHtml(initials(ipo.issuer_name))}</div><div><div class="company-name">${escapeHtml(ipo.issuer_name)}</div><div class="company-meta">${escapeHtml(ipo.board || "Board unavailable")}${ipo.sector ? ` · ${escapeHtml(ipo.sector)}` : ""}</div></div></div></td>
        <td>${statusBadge(ipo.status)}</td>
        <td><div class="number">${escapeHtml(formatPriceBand(ipo.price_band, ipo.issue_price))}</div><div class="secondary">Price</div></td>
        <td><div class="number">${escapeHtml(formatShares(IPOLotSize.lotSizeValue(ipo)))}</div><div class="secondary">Lot size</div></td>
        <td><div class="number">${escapeHtml(dateRange(ipo))}</div></td>
        <td><div class="number">${escapeHtml(formatCrores(fieldValue(ipo.issue_size_inr)))}</div></td>
        <td>${sourceBadge(source)}</td>
        <td><button class="view-button" data-ipo="${escapeHtml(ipo.id)}">View →</button></td>
      </tr>`;
  }).join("");

  $("#mobileCards").innerHTML = rows.map((ipo) => {
    const source = recordSourceStatus(ipo);
    return `
      <article class="mobile-card">
        <div class="mobile-card__head"><div><div class="company-name">${escapeHtml(ipo.issuer_name)}</div><div class="company-meta">${escapeHtml(ipo.board || "Board unavailable")}${ipo.sector ? ` · ${escapeHtml(ipo.sector)}` : ""}</div></div>${statusBadge(ipo.status)}</div>
        <div class="mobile-price">${escapeHtml(formatPriceBand(ipo.price_band, ipo.issue_price))}</div>
        <div class="mobile-grid">
          <div><div class="kv-label">LOT SIZE</div><div class="kv-value">${escapeHtml(formatShares(IPOLotSize.lotSizeValue(ipo)))}</div></div>
          <div><div class="kv-label">DATES</div><div class="kv-value">${escapeHtml(dateRange(ipo))}</div></div>
          <div><div class="kv-label">ISSUE SIZE</div><div class="kv-value">${escapeHtml(formatCrores(fieldValue(ipo.issue_size_inr)))}</div></div>
        </div>
        <div class="mobile-card__foot">${sourceBadge(source)}<button class="view-button" data-ipo="${escapeHtml(ipo.id)}">View IPO →</button></div>
      </article>`;
  }).join("");

  const noPublishedData = IPO_DATA.length === 0;
  $("#emptyState").hidden = rows.length !== 0;
  $("#emptyState").textContent = noPublishedData
    ? "No source-verified IPO records are published yet. The recovery pipeline is being reconnected."
    : "No IPOs match these filters.";
  $("#metricOpen").textContent = IPO_DATA.filter((x) => x.status === "open").length;
  $("#metricUpcoming").textContent = IPO_DATA.filter((x) => x.status === "upcoming").length;
  $("#metricClosing").textContent = IPO_DATA.filter((x) => x.status === "open" && fieldValue(x.close_date)).length;
  $("#metricListed").textContent = IPO_DATA.filter((x) => x.status === "listed").length;
  $("#datasetCount").textContent = `${IPO_DATA.length} source-backed record${IPO_DATA.length === 1 ? "" : "s"}`;
  bindDynamicButtons();
}

function bindDynamicButtons() {
  $$("[data-ipo]").forEach((button) => button.addEventListener("click", () => showDetail(button.dataset.ipo)));
}

function setActive(group, active) {
  group.forEach((button) => button.classList.toggle("active", button === active));
}

function syncSearch(value) {
  state.query = value.trim().toLowerCase();
  $("#topSearch").value = value;
  $("#heroSearch").value = value;
  render();
}

function showHome() {
  $("#homeView").hidden = false;
  $("#detailView").hidden = true;
  window.scrollTo({ top: 0, behavior: "smooth" });
  history.replaceState(null, "", "#");
}

function bestEvidence(field) {
  return field?.evidence?.[0] || null;
}

function showDetail(id) {
  const ipo = IPO_DATA.find((row) => row.id === id);
  if (!ipo) {
    showHome();
    return;
  }

  const priceText = formatPriceBand(ipo.price_band, ipo.issue_price);
  const issueText = formatCrores(fieldValue(ipo.issue_size_inr));
  const lotText = formatShares(IPOLotSize.lotSizeValue(ipo));
  const priceField = fieldValue(ipo.price_band) !== null ? ipo.price_band : ipo.issue_price;
  const evidence = bestEvidence(priceField);
  const source = sourceStatus(priceField);

  $("#detailLogo").textContent = initials(ipo.issuer_name);
  $("#detailName").textContent = ipo.issuer_name;
  $("#detailBoard").textContent = ipo.board || "Board unavailable";
  $("#detailSector").textContent = ipo.sector || "Sector unavailable";
  $("#detailStatus").className = `status status--${ipo.status || ""}`;
  $("#detailStatus").textContent = ipo.status ? ipo.status.toUpperCase() : "UNKNOWN";
  ["#detailPrice", "#detailPrice2", "#sidePrice"].forEach((selector) => $(selector).textContent = priceText);
  ["#detailIssue", "#detailIssue2"].forEach((selector) => $(selector).textContent = issueText);
  ["#detailLot", "#detailLot2"].forEach((selector) => $(selector).textContent = lotText);
  $("#detailSource").textContent = evidence?.document_type || "No retained price source";
  $("#detailSourceDate").textContent = evidence?.publication_date ? formatDate(evidence.publication_date) : "Publication date unavailable";
  $("#detailSourceBadge").className = `source source--${source}`;
  $("#detailSourceBadge").textContent = { verified: "✓ VERIFIED", provisional: "PROVISIONAL", conflict: "CONFLICT", missing: "SOURCE MISSING" }[source];

  $("#documentList").innerHTML = (ipo.documents || []).length
    ? ipo.documents.map((doc) => `
        <article><div><strong>${escapeHtml(doc.type)}</strong><small>${escapeHtml(doc.publication_date ? formatDate(doc.publication_date) : "Publication date unavailable")}</small></div>
        ${doc.url ? `<a class="text-button" href="${escapeHtml(doc.url)}" target="_blank" rel="noopener">Open ↗</a>` : sourceBadge("missing")}</article>`
      ).join("")
    : '<article><div><strong>No retained documents</strong><small>Documents will appear when the recovery pipeline publishes them.</small></div><span class="source source--missing">SOURCE MISSING</span></article>';

  $("#homeView").hidden = true;
  $("#detailView").hidden = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
  history.replaceState(null, "", `#ipo/${ipo.id}`);
}

let toastTimer;
function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => node.classList.remove("show"), 2400);
}

$("#topSearch").addEventListener("input", (event) => syncSearch(event.target.value));
$("#heroSearch").addEventListener("input", (event) => syncSearch(event.target.value));
$$("[data-home]").forEach((button) => button.addEventListener("click", showHome));
$$("[data-placeholder]").forEach((button) => button.addEventListener("click", () => toast(`${button.dataset.placeholder} is reserved for a later verified product phase.`)));
$("#boardFilter").addEventListener("click", (event) => {
  if (!event.target.matches("button[data-board]")) return;
  state.board = event.target.dataset.board;
  setActive($$("#boardFilter button"), event.target);
  render();
});
$("#statusFilter").addEventListener("click", (event) => {
  if (!event.target.matches("button[data-status]")) return;
  state.status = event.target.dataset.status;
  setActive($$("#statusFilter button"), event.target);
  render();
});
$("#jumpSources").addEventListener("click", () => $("#documents").scrollIntoView({ behavior: "smooth" }));
$("#jumpFinancials").addEventListener("click", () => $("#financials").scrollIntoView({ behavior: "smooth" }));
$("#jumpTimeline").addEventListener("click", () => $("#timeline").scrollIntoView({ behavior: "smooth" }));
$("#jumpDocuments").addEventListener("click", () => $("#documents").scrollIntoView({ behavior: "smooth" }));

async function loadData() {
  try {
    const response = await fetch("data/ipos.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    IPO_DATA = Array.isArray(payload.records) ? payload.records : [];
  } catch (error) {
    console.error("Unable to load IPO dataset:", error);
    IPO_DATA = [];
  }

  render();
  if (location.hash.startsWith("#ipo/")) showDetail(location.hash.split("/")[1]);
}

loadData();
