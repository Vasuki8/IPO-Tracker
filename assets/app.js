/* Static directory UI. Published data and its source fields remain read-only. */
let IPO_DATA = [];
let loadState = "loading";
const PAGE_SIZE = 20;
const state = {
  board: "all",
  status: "all",
  query: "",
  year: "all",
  sort: "newest",
  page: 1,
};
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const number = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 });
const statuses = {
  open: "Open",
  upcoming: "Upcoming",
  closed: "Closed",
  listed: "Listed",
};
const sourceLabels = {
  verified: "Verified",
  provisional: "Provisional",
  conflict: "Conflict",
  missing: "Missing",
};

function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
      })[char],
  );
}
function fieldValue(field) {
  return field?.value ?? null;
}
function sourceStatus(field) {
  return Object.hasOwn(sourceLabels, field?.status) ? field.status : "missing";
}
function safeUrl(value) {
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}
function formatMoney(value) {
  return value == null ? "—" : `₹${number.format(value)}`;
}
function formatCrores(value) {
  return value == null ? "—" : `₹${number.format(Number(value) / 10000000)} Cr`;
}
function formatShares(value) {
  return value == null ? "—" : number.format(value);
}
function hasBand(field) {
  const value = fieldValue(field);
  return (
    value && typeof value === "object" && value.min != null && value.max != null
  );
}
function priceField(ipo) {
  return hasBand(ipo.price_band) ? ipo.price_band : ipo.issue_price;
}
function formatPriceBand(field, issuePriceField) {
  return hasBand(field)
    ? `${formatMoney(field.value.min)}–${formatMoney(field.value.max)}`
    : formatMoney(fieldValue(issuePriceField));
}
function formatDate(value, withYear = true) {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        ...(withYear ? { year: "numeric" } : {}),
        timeZone: "UTC",
      });
}
function formatTimestamp(value) {
  if (!value) return "Unavailable";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Unavailable"
    : `${date.toLocaleString("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "UTC" })} UTC`;
}
function statusBadge(status) {
  const key = Object.hasOwn(statuses, status) ? status : "unknown";
  return `<span class="status status--${key}">${statuses[key] || "Status unavailable"}</span>`;
}
function sourceBadge(status, label) {
  const key = Object.hasOwn(sourceLabels, status) ? status : "missing";
  return `<span class="source source--${key}">${escapeHtml(label || sourceLabels[key])}</span>`;
}
function fieldFlag(field) {
  const status = sourceStatus(field);
  return ["conflict", "provisional"].includes(status)
    ? `<span class="field-flag field-flag--${status}">${sourceLabels[status]}</span>`
    : "";
}
function recordSourceStatus(ipo) {
  const raw = [
    ipo.price_band,
    ipo.issue_price,
    ipo.market_lot,
    ipo.minimum_bid_quantity,
    ipo.issue_size_inr,
    ipo.open_date,
    ipo.close_date,
    ipo.listing_date,
  ];
  if (raw.some((field) => sourceStatus(field) === "conflict"))
    return "conflict";
  if (raw.some((field) => sourceStatus(field) === "provisional"))
    return "provisional";
  const displayed = [
    priceField(ipo),
    IPOLotSize.lotSizeField(ipo),
    ipo.issue_size_inr,
    ipo.open_date,
    ipo.close_date,
    ipo.listing_date,
  ];
  return displayed.every(
    (field) => fieldValue(field) != null && sourceStatus(field) === "verified",
  )
    ? "verified"
    : "missing";
}
function coverageBadge(ipo) {
  const status = recordSourceStatus(ipo);
  const hasTerms = [
    priceField(ipo),
    IPOLotSize.lotSizeField(ipo),
    ipo.issue_size_inr,
    ipo.open_date,
    ipo.close_date,
    ipo.listing_date,
  ].some((field) => fieldValue(field) != null);
  return sourceBadge(
    status,
    { verified: "Complete", missing: hasTerms ? "Partial" : "Missing" }[status],
  );
}
function recordYear(ipo) {
  const date =
    fieldValue(ipo.open_date) ||
    fieldValue(ipo.close_date) ||
    fieldValue(ipo.listing_date);
  return date ? String(date).slice(0, 4) : "undated";
}
function initials(name) {
  return String(name || "?")
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}
function tone(ipo) {
  return [...ipo.id].reduce((value, char) => value + char.charCodeAt(0), 0) % 4;
}
function companyMarkup(ipo) {
  return `<div class="company-row"><span class="company-logo tone-${tone(ipo)}" aria-hidden="true">${escapeHtml(initials(ipo.issuer_name))}</span><div><a class="company-name" href="#ipo/${encodeURIComponent(ipo.id)}">${escapeHtml(ipo.issuer_name)}</a><div class="company-meta">${escapeHtml(ipo.board || "Board unavailable")}${ipo.sector ? ` · ${escapeHtml(ipo.sector)}` : ""}</div></div></div>`;
}
function offerDates(ipo) {
  const open = fieldValue(ipo.open_date),
    close = fieldValue(ipo.close_date);
  if (open && close)
    return `<span class="number">${escapeHtml(formatDate(open, false))} – ${escapeHtml(formatDate(close, false))}</span><span class="secondary">${escapeHtml(open.slice(0, 4) === close.slice(0, 4) ? close.slice(0, 4) : `${open.slice(0, 4)}–${close.slice(0, 4)}`)}</span>${fieldFlag(ipo.open_date)}${fieldFlag(ipo.close_date)}`;
  if (open || close)
    return `<span class="number">${escapeHtml(formatDate(open || close))}</span><span class="secondary">${open ? "Opens · close unavailable" : "Closes · open unavailable"}</span>${fieldFlag(open ? ipo.open_date : ipo.close_date)}`;
  return '<span class="number">—</span><span class="secondary">Dates unavailable</span>';
}
function filteredRows(ignoreStatus = false) {
  const rows = IPO_DATA.filter(
    (ipo) =>
      (state.board === "all" ||
        String(ipo.board || "").toLowerCase() === state.board) &&
      (ignoreStatus || state.status === "all" || ipo.status === state.status) &&
      (state.year === "all" || recordYear(ipo) === state.year) &&
      (!state.query ||
        [ipo.issuer_name, ipo.sector, ipo.board]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(state.query.toLowerCase())),
  );
  return rows.sort(
    state.sort === "name"
      ? (a, b) =>
          a.issuer_name.localeCompare(b.issuer_name, "en", {
            sensitivity: "base",
          })
      : IPOOrder.compareNewestFirst,
  );
}
function updateUrl() {
  const url = new URL(location.href);
  for (const [key, fallback] of Object.entries({
    board: "all",
    status: "all",
    query: "",
    year: "all",
    sort: "newest",
    page: 1,
  })) {
    const param = key === "query" ? "q" : key;
    if (state[key] === fallback) url.searchParams.delete(param);
    else url.searchParams.set(param, state[key]);
  }
  history.replaceState(null, "", url);
}
function readUrl() {
  const params = new URLSearchParams(location.search);
  state.board = ["all", "mainboard", "sme"].includes(params.get("board"))
    ? params.get("board")
    : "all";
  state.status = ["all", ...Object.keys(statuses)].includes(
    params.get("status"),
  )
    ? params.get("status")
    : "all";
  state.query = (params.get("q") || "").trim();
  state.year = [...$("#yearFilter").options].some(
    (option) => option.value === params.get("year"),
  )
    ? params.get("year")
    : "all";
  state.sort = params.get("sort") === "name" ? "name" : "newest";
  state.page = Math.max(1, Math.floor(Number(params.get("page")) || 1));
  $("#searchInput").value = state.query;
  $("#yearFilter").value = state.year;
  $("#sortFilter").value = state.sort;
}
function render() {
  const rows = filteredRows();
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  state.page = Math.min(state.page, pages);
  const start = (state.page - 1) * PAGE_SIZE;
  const pageRows = rows.slice(start, start + PAGE_SIZE);
  $("#ipoRows").innerHTML = pageRows
    .map(
      (ipo) => `<tr>
    <td>${companyMarkup(ipo)}</td><td>${statusBadge(ipo.status)}</td>
    <td class="align-right"><span class="number">${escapeHtml(formatPriceBand(ipo.price_band, ipo.issue_price))}</span>${fieldFlag(priceField(ipo))}</td>
    <td class="align-right"><span class="number">${escapeHtml(formatShares(IPOLotSize.lotSizeValue(ipo)))}</span><span class="secondary">${IPOLotSize.lotSizeValue(ipo) == null ? "Unavailable" : "shares"}</span></td>
    <td>${offerDates(ipo)}</td><td class="align-right"><span class="number">${escapeHtml(formatCrores(fieldValue(ipo.issue_size_inr)))}</span>${fieldFlag(ipo.issue_size_inr)}</td>
    <td>${coverageBadge(ipo)}</td><td><a class="view-link" href="#ipo/${encodeURIComponent(ipo.id)}" aria-label="View ${escapeHtml(ipo.issuer_name)}">↗</a></td></tr>`,
    )
    .join("");
  $("#mobileCards").innerHTML = pageRows
    .map(
      (
        ipo,
      ) => `<article class="mobile-card"><div class="mobile-card__head">${companyMarkup(ipo)}${statusBadge(ipo.status)}</div>
    <dl class="mobile-values"><div><dt>Price / band</dt><dd>${escapeHtml(formatPriceBand(ipo.price_band, ipo.issue_price))}${fieldFlag(priceField(ipo))}</dd></div><div><dt>Lot size · shares</dt><dd>${escapeHtml(formatShares(IPOLotSize.lotSizeValue(ipo)))}</dd></div><div><dt>Issue size</dt><dd>${escapeHtml(formatCrores(fieldValue(ipo.issue_size_inr)))}${fieldFlag(ipo.issue_size_inr)}</dd></div></dl>
    <div class="mobile-card__dates"><span>Offer dates</span><div>${offerDates(ipo)}</div></div><div class="mobile-card__foot">${coverageBadge(ipo)}<a href="#ipo/${encodeURIComponent(ipo.id)}">View IPO <span aria-hidden="true">↗</span></a></div></article>`,
    )
    .join("");
  $("#emptyState").hidden = rows.length > 0;
  $("#emptyTitle").textContent = IPO_DATA.length
    ? "No IPOs match your search."
    : "No IPO records are published yet.";
  $("#emptyDescription").textContent = IPO_DATA.length
    ? "Try another company or clear your filters."
    : "Check back when source-backed records are available.";
  $("#emptyReset").hidden = !IPO_DATA.length;
  $("#resultCount").textContent = rows.length
    ? `${number.format(start + 1)}–${number.format(start + pageRows.length)} of ${number.format(rows.length)} IPOs`
    : "0 IPOs";
  $("#pageLabel").textContent = `${state.page} / ${pages}`;
  $("#previousPage").disabled = state.page <= 1;
  $("#nextPage").disabled = state.page >= pages;
  for (const [selector, status] of Object.entries({
    "#metricTotal": "all",
    "#metricOpen": "open",
    "#metricUpcoming": "upcoming",
    "#metricListed": "listed",
  }))
    $(selector).textContent = number.format(
      IPO_DATA.filter((ipo) => status === "all" || ipo.status === status)
        .length,
    );
  $("#datasetCount").textContent = number.format(IPO_DATA.length);
  const baseRows = filteredRows(true);
  $$("[data-count]").forEach(
    (node) =>
      (node.textContent = number.format(
        baseRows.filter(
          (ipo) =>
            node.dataset.count === "all" || ipo.status === node.dataset.count,
        ).length,
      )),
  );
  for (const key of ["board", "status"])
    $$(`[data-${key}]`).forEach((button) => {
      const active = button.dataset[key] === state[key];
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
  const filters = [
    state.query && `“${state.query}”`,
    state.board !== "all" && (state.board === "sme" ? "SME" : "Mainboard"),
    state.year !== "all" &&
      (state.year === "undated" ? "Year unavailable" : state.year),
    state.status !== "all" && statuses[state.status],
  ].filter(Boolean);
  $("#activeFilters").hidden = !filters.length;
  $("#filterSummary").textContent = filters.join(" · ");
}
function changeFilter(key, value) {
  state[key] = value;
  state.page = 1;
  render();
  updateUrl();
}
function clearFilters() {
  Object.assign(state, {
    board: "all",
    status: "all",
    query: "",
    year: "all",
    sort: "newest",
    page: 1,
  });
  $("#searchInput").value = "";
  $("#yearFilter").value = "all";
  $("#sortFilter").value = "newest";
  render();
  updateUrl();
}
function evidenceMarkup(evidence) {
  const url = safeUrl(evidence.url);
  const label = evidence.document_type || "Official source";
  return `<div class="evidence-source">${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)} ↗</a>` : `<strong>${escapeHtml(label)}</strong>`}${evidence.document_identity ? `<p class="source-identity">${escapeHtml(evidence.document_identity)}</p>` : ""}<p>Published: ${escapeHtml(evidence.publication_date ? formatDate(evidence.publication_date) : "Date unavailable")}${evidence.page != null ? ` · Page ${escapeHtml(evidence.page)}` : ""}</p><p>Collected: ${escapeHtml(formatTimestamp(evidence.collected_at))}</p>${evidence.observed_at ? `<p>Observed: ${escapeHtml(formatTimestamp(evidence.observed_at))}</p>` : ""}${evidence.evidence_text ? `<p>${escapeHtml(evidence.evidence_text)}</p>` : ""}</div>`;
}
function fieldEvidence(label, field, value, note = "") {
  const evidence = Array.isArray(field?.evidence) ? field.evidence : [];
  const corrections = field?.corrections || [];
  return `<details class="evidence-row"><summary><span>${escapeHtml(label)}</span><span class="evidence-value">${escapeHtml(value)}${sourceBadge(sourceStatus(field))}</span></summary><div class="evidence-body">${note ? `<p>${escapeHtml(note)}</p>` : ""}${evidence.length ? evidence.map(evidenceMarkup).join("") : "<p>No retained source evidence is available for this field.</p>"}${corrections.length ? `<p>Retained correction history</p><pre class="correction-history">${escapeHtml(JSON.stringify(corrections, null, 2))}</pre>` : ""}</div></details>`;
}
function documentCategory(doc) {
  const type = (doc.type || "").toLowerCase();
  if (/sebi|prospectus|issuer/.test(type)) return "filings";
  if (/nse|bse|exchange/.test(type)) return "exchange";
  return "other";
}
const documentCategories = [
  ["filings", "Offer filings"],
  ["exchange", "Exchange records"],
  ["other", "Other sources"],
];
function documentMarkup(doc) {
  const url = safeUrl(doc.url);
  const inner = `<strong>${escapeHtml(doc.type || "Official document")}</strong><small>${escapeHtml(doc.identity || "")}</small><small>Published: ${escapeHtml(doc.publication_date ? formatDate(doc.publication_date) : "Date unavailable")}</small><small>Collected: ${escapeHtml(formatTimestamp(doc.collected_at))}</small>`;
  return `<article class="document"><span class="document-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM14 2v6h6M8 13h8M8 17h5"/></svg></span><div class="document-info">${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${inner}<span class="sr-only">Opens in a new tab</span></a>` : inner}</div>${url ? '<span class="document-arrow" aria-hidden="true">↗</span>' : ""}</article>`;
}
function renderDocuments(docs, category = "all") {
  const groups = documentCategories
    .map(([key, label]) => [
      key,
      label,
      docs.filter((doc) => documentCategory(doc) === key),
    ])
    .filter(([, , items]) => items.length);
  const filters = [
    ["all", "All", docs.length],
    ...groups.map(([key, label, items]) => [key, label, items.length]),
  ];
  $("#documentFilters").hidden = groups.length < 2;
  $("#documentFilters").innerHTML = filters
    .map(
      ([key, label, count]) =>
        `<button type="button" data-document-category="${key}" aria-pressed="${category === key}" class="${category === key ? "active" : ""}">${escapeHtml(label)} <span>${count}</span></button>`,
    )
    .join("");
  $("#documentList").innerHTML = docs.length
    ? groups
        .filter(([key]) => category === "all" || category === key)
        .map(
          ([, label, items]) =>
            `<section class="document-group" aria-label="${escapeHtml(label)}"><h3>${escapeHtml(label)} <span>${items.length}</span></h3>${items.map(documentMarkup).join("")}</section>`,
        )
        .join("")
    : '<p class="small muted">No source documents are retained for this record yet.</p>';
}
function showDetail(id) {
  const ipo = IPO_DATA.find((row) => row.id === id);
  if (!ipo) {
    showHome();
    return;
  }
  $("#detailLogo").textContent = initials(ipo.issuer_name);
  $("#detailLogo").className =
    `company-logo company-logo--large tone-${tone(ipo)}`;
  $("#detailName").textContent = ipo.issuer_name;
  $("#detailStatus").innerHTML = statusBadge(ipo.status);
  $("#detailBoard").textContent = ipo.board || "Board unavailable";
  $("#detailSector").hidden = !ipo.sector;
  $("#detailSector").textContent = ipo.sector || "";
  $("#detailPrice").innerHTML =
    escapeHtml(formatPriceBand(ipo.price_band, ipo.issue_price)) +
    fieldFlag(priceField(ipo));
  $("#detailLot").textContent =
    IPOLotSize.lotSizeValue(ipo) == null
      ? "—"
      : `${formatShares(IPOLotSize.lotSizeValue(ipo))} shares`;
  $("#detailIssue").innerHTML =
    escapeHtml(formatCrores(fieldValue(ipo.issue_size_inr))) +
    fieldFlag(ipo.issue_size_inr);
  $("#detailCoverage").innerHTML = coverageBadge(ipo);
  $("#detailCollected").textContent =
    `Record last collected: ${formatTimestamp(ipo.last_collected_at)}`;
  $("#timelineEvents").innerHTML = [
    ["Opens", ipo.open_date],
    ["Closes", ipo.close_date],
    ["Lists", ipo.listing_date],
  ]
    .map(
      ([label, field]) =>
        `<div class="timeline-event ${fieldValue(field) ? "has-date" : ""}"><span>${label}</span><strong>${fieldValue(field) ? escapeHtml(formatDate(fieldValue(field))) : "Unavailable"}</strong>${sourceBadge(sourceStatus(field))}</div>`,
    )
    .join("");
  const lot = IPOLotSize.lotSizeField(ipo);
  $("#evidenceList").innerHTML =
    fieldEvidence(
      "Price band",
      ipo.price_band,
      formatPriceBand(ipo.price_band),
    ) +
    fieldEvidence(
      "Final issue price",
      ipo.issue_price,
      formatMoney(fieldValue(ipo.issue_price)),
    ) +
    fieldEvidence(
      "Lot size",
      lot,
      lot ? `${formatShares(fieldValue(lot))} shares` : "—",
      lot
        ? `Displayed from verified ${lot === ipo.market_lot ? "market lot" : "minimum bid quantity"}.`
        : "No verified market lot or minimum bid quantity is available.",
    ) +
    [
      ["Market lot evidence", ipo.market_lot],
      ["Minimum bid quantity evidence", ipo.minimum_bid_quantity],
    ]
      .filter(([, field]) =>
        ["conflict", "provisional"].includes(sourceStatus(field)),
      )
      .map(([label, field]) =>
        fieldEvidence(
          label,
          field,
          fieldValue(field) == null
            ? "—"
            : `${formatShares(fieldValue(field))} shares`,
          "This unresolved quantity is not used for the displayed lot size.",
        ),
      )
      .join("") +
    fieldEvidence(
      "Issue size",
      ipo.issue_size_inr,
      formatCrores(fieldValue(ipo.issue_size_inr)),
    ) +
    [
      ["Opening date", ipo.open_date],
      ["Closing date", ipo.close_date],
      ["Listing date", ipo.listing_date],
    ]
      .map(([label, field]) =>
        fieldEvidence(label, field, formatDate(fieldValue(field))),
      )
      .join("");
  const docs = Array.isArray(ipo.documents) ? ipo.documents : [];
  $("#documentCount").textContent = docs.length;
  renderDocuments(docs);
  $("#homeView").hidden = true;
  $("#detailView").hidden = false;
  document.title = `${ipo.issuer_name} — IPO Tracker`;
  window.scrollTo(0, 0);
  $("#detailName").focus({ preventScroll: true });
}
function showHome() {
  const returning = !$("#detailView").hidden;
  $("#homeView").hidden = false;
  $("#detailView").hidden = true;
  document.title = "IPO Tracker — Indian IPO directory";
  if (returning) $("#searchInput").focus({ preventScroll: true });
}
function route() {
  if (loadState !== "ready") return;
  if (location.hash.startsWith("#ipo/")) {
    try {
      showDetail(decodeURIComponent(location.hash.slice(5)));
    } catch {
      showHome();
    }
  } else {
    readUrl();
    render();
    showHome();
  }
}
async function loadData() {
  loadState = "loading";
  $("#loadingState").hidden = false;
  $("#errorState").hidden = true;
  $("#results").hidden = true;
  try {
    const response = await fetch("data/ipos.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    if (
      !Array.isArray(payload.records) ||
      payload.records.some(
        (row) =>
          !row ||
          typeof row.id !== "string" ||
          typeof row.issuer_name !== "string",
      )
    )
      throw new Error("Invalid published dataset");
    IPO_DATA = payload.records;
    const years = [...new Set(IPO_DATA.map(recordYear))]
      .filter((year) => year !== "undated")
      .sort()
      .reverse();
    $("#yearFilter").innerHTML =
      '<option value="all">All years</option>' +
      years
        .map(
          (year) =>
            `<option value="${escapeHtml(year)}">${escapeHtml(year)}</option>`,
        )
        .join("") +
      (IPO_DATA.some((ipo) => recordYear(ipo) === "undated")
        ? '<option value="undated">Year unavailable</option>'
        : "");
    $("#datasetTimestamp").textContent =
      `Dataset generated: ${formatTimestamp(payload.generated_at)}`;
    loadState = "ready";
    readUrl();
    render();
    $("#results").hidden = false;
    route();
  } catch (error) {
    loadState = "error";
    $("#errorState").hidden = false;
    console.error("Unable to load IPO dataset:", error);
  } finally {
    $("#loadingState").hidden = true;
  }
}
$("#searchInput").addEventListener("input", (event) =>
  changeFilter("query", event.target.value.trim()),
);
$("#yearFilter").addEventListener("change", (event) =>
  changeFilter("year", event.target.value),
);
$("#sortFilter").addEventListener("change", (event) =>
  changeFilter("sort", event.target.value),
);
for (const key of ["board", "status"])
  $(`#${key}Filter`).addEventListener("click", (event) => {
    const button = event.target.closest(`[data-${key}]`);
    if (button) changeFilter(key, button.dataset[key]);
  });
$$("[data-metric]").forEach((button) =>
  button.addEventListener("click", () => {
    clearFilters();
    changeFilter("status", button.dataset.metric);
    $(".directory").scrollIntoView({ behavior: "smooth" });
  }),
);
$("#resetFilters").addEventListener("click", clearFilters);
$("#emptyReset").addEventListener("click", clearFilters);
for (const [id, delta] of [
  ["previousPage", -1],
  ["nextPage", 1],
])
  $(`#${id}`).addEventListener("click", () => {
    state.page += delta;
    render();
    updateUrl();
    $(".directory").scrollIntoView({ behavior: "smooth" });
  });
$("#retryLoad").addEventListener("click", loadData);
$("#jumpDocuments").addEventListener("click", () => {
  $("#documents").scrollIntoView({ behavior: "smooth" });
});
$(".detail-sections").addEventListener("click", (event) => {
  const button = event.target.closest("[data-detail-section]");
  if (button)
    document
      .getElementById(button.dataset.detailSection)
      .scrollIntoView({ behavior: "smooth" });
});
$("#documentFilters").addEventListener("click", (event) => {
  const button = event.target.closest("[data-document-category]");
  if (!button) return;
  const id = location.hash.startsWith("#ipo/")
    ? decodeURIComponent(location.hash.slice(5))
    : "";
  const ipo = IPO_DATA.find((row) => row.id === id);
  if (ipo)
    renderDocuments(ipo.documents || [], button.dataset.documentCategory);
});
$$("[data-methodology]").forEach((button) =>
  button.addEventListener("click", () => $("#sourcesDialog").showModal()),
);
$("#closeSources").addEventListener("click", () => $("#sourcesDialog").close());
$("#sourcesDone").addEventListener("click", () => $("#sourcesDialog").close());
document.addEventListener("keydown", (event) => {
  if (
    event.key === "/" &&
    !event.ctrlKey &&
    !event.metaKey &&
    !event.altKey &&
    !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName) &&
    !$("#homeView").hidden &&
    !$("#sourcesDialog").open
  ) {
    event.preventDefault();
    $("#searchInput").focus();
  }
});
window.addEventListener("hashchange", route);
window.addEventListener("popstate", route);
loadData();
