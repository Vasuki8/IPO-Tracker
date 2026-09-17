/* Permanent company-route renderer.
 * Route HTML embeds one compact public record, so profile pages no longer need
 * to download and parse the multi-megabyte canonical IPO dataset.
 */

const IST_DATE_FORMATTER = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  timeZone: "Asia/Kolkata",
});
const IST_DAY_FORMATTER = new Intl.DateTimeFormat("en-CA", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  timeZone: "Asia/Kolkata",
});
const IST_TIMESTAMP_FORMATTER = new Intl.DateTimeFormat("en-IN", {
  timeZone: "Asia/Kolkata",
  dateStyle: "medium",
  timeStyle: "short",
});
const IST_TIME_FORMATTER = new Intl.DateTimeFormat("en-IN", {
  timeZone: "Asia/Kolkata",
  hour: "2-digit",
  minute: "2-digit",
});
const IST_DATE_TIME_FORMATTER = new Intl.DateTimeFormat("en-IN", {
  timeZone: "Asia/Kolkata",
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

const money = (value) =>
  value == null
    ? "—"
    : `₹${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 })} Cr`;
const rupees = (value) =>
  value == null
    ? "—"
    : `₹${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
const x = (value) =>
  value == null
    ? "—"
    : `${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 })}×`;

function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>'"]/g,
    (char) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "'": "&#39;",
        '"': "&quot;",
      })[char],
  );
}
function escapeAttr(value) {
  return escapeHtml(value);
}

function prettyDate(value) {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00+05:30`);
  return Number.isNaN(date.getTime())
    ? String(value)
    : IST_DATE_FORMATTER.format(date);
}

function formatTimestamp(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? String(value)
    : `${IST_TIMESTAMP_FORMATTER.format(date)} IST`;
}

function currentIstDate() {
  const parts = IST_DAY_FORMATTER.formatToParts(new Date());
  const values = Object.fromEntries(
    parts.map((part) => [part.type, part.value]),
  );
  return `${values.year}-${values.month}-${values.day}`;
}

const TODAY_IST = currentIstDate();

function derivedStatus(ipo) {
  if (ipo.openDate && TODAY_IST < ipo.openDate) return "upcoming";
  if (
    ipo.openDate &&
    ipo.closeDate &&
    TODAY_IST >= ipo.openDate &&
    TODAY_IST <= ipo.closeDate
  )
    return "open";
  if (ipo.listingDate && TODAY_IST >= ipo.listingDate) return "listed";
  if (ipo.closeDate && TODAY_IST > ipo.closeDate) return "closed";
  return ipo.status || "upcoming";
}

function priceBand(ipo) {
  if (!ipo.priceBand) return "—";
  const { min, max } = ipo.priceBand;
  if (min == null && max == null) return "—";
  if (min === max || min == null) return rupees(max);
  if (max == null) return rupees(min);
  return `${rupees(min)}–${rupees(max)}`;
}

function badge(status) {
  return `<span class="badge badge-${escapeAttr(status)}">${escapeHtml(status)}</span>`;
}

function filingStage(ipo) {
  const types = (ipo.documents || []).map((doc) =>
    String(doc?.type || "").toUpperCase(),
  );
  if (
    types.some(
      (type) => type.includes("PROSPECTUS") && !type.includes("ABRIDGED"),
    )
  )
    return "Prospectus";
  if (types.some((type) => type === "RHP" || type.includes("RED HERRING")))
    return "RHP";
  if (types.some((type) => type === "UDRHP")) return "UDRHP";
  if (types.some((type) => type === "DRHP")) return "DRHP";
  return (
    {
      drhp: "DRHP",
      udrhp: "UDRHP",
      rhp: "RHP",
      prospectus: "Prospectus",
      exchange: "Exchange",
    }[ipo.lifecycle?.stage] || "—"
  );
}

function sourceCount(ipo) {
  const sources = ipo.sources || (ipo.source ? [ipo.source] : []);
  return new Set(
    sources
      .map((source) => String(source?.name || "").split(" ")[0])
      .filter(Boolean),
  ).size;
}

function validationBadge(ipo) {
  const status = ipo.validation?.status || "single-source";
  const count = sourceCount(ipo);
  const label = status === "single-source" ? (count === 0 ? "No sources" : count === 1 ? "1 source" : "Not cross-verified") : status;
  return `<span class="validation validation-${escapeAttr(status)}">${escapeHtml(label)}</span>`;
}

function validationCopy(ipo) {
  const status = ipo.validation?.status || "single-source";
  if (status === "verified")
    return "At least two independent official sources are attached to this record.";
  if (status === "conflict")
    return "One or more comparable fields disagree across exchange sources.";
  return sourceCount(ipo)
    ? "This record has not been cross-verified across independent sources."
    : "No source is attached to this record yet.";
}

function formatObservation(value) {
  if (value == null) return "—";
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}

function p4History(ipo) {
  return (ipo.subscriptionHistory || [])
    .filter((row) => row && row.capturedAt)
    .slice()
    .sort((a, b) => String(a.capturedAt).localeCompare(String(b.capturedAt)));
}

function p4Latest(ipo, history) {
  const current = {
    ...(ipo.subscription || {}),
    capturedAt: ipo.subscriptionAsOf || null,
    source: ipo.subscriptionSource || null,
  };
  const recorded = history[history.length - 1];
  if (!recorded) return current;
  const hasCurrent = ["qib", "nii", "retail", "total"].some(
    (key) => current[key] != null,
  );
  if (!hasCurrent) return { ...recorded };
  const currentTime = Date.parse(current.capturedAt);
  const recordedTime = Date.parse(recorded.capturedAt);
  // Keep each observation's values, timestamp and source together. The canonical
  // snapshot can be newer than the last stored change in the history series.
  if (
    Number.isFinite(currentTime) &&
    Number.isFinite(recordedTime) &&
    recordedTime > currentTime
  )
    return { ...recorded };
  return current;
}

function p4TimeLabel(value, includeDate = false) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value || "—");
  return (includeDate ? IST_DATE_TIME_FORMATTER : IST_TIME_FORMATTER)
    .format(date)
    .replace(",", "");
}

function p4Chart(history) {
  if (!history.length) return "";
  const series = [
    ["qib", "QIB"],
    ["nii", "NII / HNI"],
    ["retail", "Retail / Individual"],
    ["total", "Total"],
  ];
  const width = 860;
  const height = 310;
  const margin = { left: 58, right: 20, top: 22, bottom: 52 };
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;

  let maxValue = 1;
  const times = [];
  for (const row of history) {
    times.push(new Date(row.capturedAt).getTime());
    for (const [key] of series) {
      const value = Number(row[key]);
      if (row[key] != null && Number.isFinite(value))
        maxValue = Math.max(maxValue, value);
    }
  }
  const roundedMax =
    maxValue <= 5
      ? Math.ceil(maxValue * 2) / 2
      : maxValue <= 20
        ? Math.ceil(maxValue / 2) * 2
        : Math.ceil(maxValue / 10) * 10;
  const validTimes = times.filter(Number.isFinite);
  const tMin = validTimes.length ? Math.min(...validTimes) : 0;
  const tMax = validTimes.length ? Math.max(...validTimes) : history.length - 1;

  const xAt = (row, index) => {
    const time = times[index];
    if (Number.isFinite(time) && tMax > tMin) {
      return margin.left + ((time - tMin) / (tMax - tMin)) * plotW;
    }
    return (
      margin.left +
      (history.length <= 1 ? plotW / 2 : (index / (history.length - 1)) * plotW)
    );
  };
  const yAt = (value) =>
    margin.top + plotH - (Math.max(0, Number(value) || 0) / roundedMax) * plotH;

  const yTicks = [0, 0.25, 0.5, 0.75, 1]
    .map((fraction) => {
      const value = roundedMax * fraction;
      const y = yAt(value);
      return `<line class="sub-grid" x1="${margin.left}" y1="${y.toFixed(1)}" x2="${width - margin.right}" y2="${y.toFixed(1)}"></line><text class="sub-axis-label" x="${margin.left - 10}" y="${(y + 4).toFixed(1)}" text-anchor="end">${escapeHtml(x(value))}</text>`;
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
    return `<text class="sub-axis-label" x="${pointX.toFixed(1)}" y="${height - 18}" text-anchor="${anchor}">${escapeHtml(label)}</text>`;
  }).join("");

  const lines = series
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
        .map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`)
        .join(" ");
      const dots = points
        .map(
          (point) =>
            `<circle class="sub-point sub-${key}" cx="${point.x.toFixed(1)}" cy="${point.y.toFixed(1)}" r="4"><title>${escapeHtml(`${label}: ${x(point.value)} · ${formatTimestamp(point.row.capturedAt)}`)}</title></circle>`,
        )
        .join("");
      return `<polyline class="sub-line sub-${key}" points="${polyline}"></polyline>${dots}`;
    })
    .join("");

  return `<div class="subscription-chart-wrap"><svg class="subscription-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="IPO subscription history chart">${yTicks}${xTicks}${lines}</svg></div>`;
}

function routeProfileHtml(ipo) {
  return companyProfileHtml(ipo, { standalone: true });
}

function bindRouteNavigation(root) {
  bindCompanyProfileNavigation(root, { scrollRoot: null });
}

function companyReturnUrl() {
  const base = new URL("./", document.baseURI);
  try {
    const saved = sessionStorage.getItem("ipoTrackerReturnUrl");
    if (saved) {
      const url = new URL(saved, base);
      if (
        url.origin === window.location.origin &&
        !url.username &&
        !url.password &&
        (url.pathname === base.pathname ||
          url.pathname === `${base.pathname}index.html`)
      )
        return url.href;
    }
  } catch {
    /* Private browsing can disable session storage. */
  }
  return base.href;
}

function bindCompanyReturnLinks() {
  const href = companyReturnUrl();
  document
    .querySelectorAll(
      ".company-route-back, .company-route-footer a, .company-route-error a, [data-company-return]",
    )
    .forEach((link) => {
      link.href = href;
    });
}

function copyWithSelection(value) {
  const active = document.activeElement;
  const field = document.createElement("textarea");
  field.value = value;
  field.setAttribute("readonly", "");
  field.style.cssText = "position:fixed;left:-9999px;top:0;opacity:0;";
  document.body.appendChild(field);
  let copied = false;
  try {
    field.focus({ preventScroll: true });
    field.select();
    copied =
      typeof document.execCommand === "function" &&
      document.execCommand("copy");
  } catch {
    copied = false;
  } finally {
    field.remove();
    if (active && typeof active.focus === "function")
      active.focus({ preventScroll: true });
  }
  return copied;
}

async function copyPermanentLink(button) {
  const value = window.location.href;
  const original = button.textContent;
  let feedback = document.getElementById("companyCopyFeedback");
  if (!feedback) {
    feedback = document.createElement("div");
    feedback.id = "companyCopyFeedback";
    feedback.className = "company-copy-feedback";
    feedback.setAttribute("role", "status");
    feedback.setAttribute("aria-live", "polite");
    document
      .querySelector(".company-route-topbar")
      .insertAdjacentElement("afterend", feedback);
  }
  button.disabled = true;
  let copied = false;
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
      copied = true;
    }
  } catch {
    /* Fall back to a selected text field when clipboard permission is unavailable. */
  }
  if (!copied) copied = copyWithSelection(value);
  button.disabled = false;
  if (copied) {
    button.textContent = "Link copied ✓";
    feedback.textContent = "Profile link copied to your clipboard.";
    setTimeout(() => {
      button.textContent = original;
    }, 1800);
  } else {
    feedback.textContent =
      "Automatic copying is unavailable. Select and copy this profile link:";
    const input = document.createElement("input");
    input.type = "text";
    input.value = value;
    input.readOnly = true;
    input.setAttribute("aria-label", "Company profile link");
    input.addEventListener("focus", () => input.select());
    feedback.appendChild(input);
    input.focus({ preventScroll: true });
    input.select();
  }
}

function embeddedProfile() {
  const node = document.getElementById("ipo-profile-data");
  if (!node) return null;
  try {
    const payload = JSON.parse(node.textContent || "{}");
    return payload?.ipo && typeof payload.ipo === "object" ? payload.ipo : null;
  } catch (error) {
    console.warn("Could not parse embedded IPO profile", error);
    return null;
  }
}

function latestProfileTimestamp(ipo) {
  let latest = "";
  for (const source of ipo.sources || []) {
    const value = String(source?.asOf || "");
    if (value > latest) latest = value;
  }
  for (const value of [
    ipo.subscriptionAsOf,
    ipo.offerDocumentExtraction?.extractedAt,
  ]) {
    if (value && String(value) > latest) latest = String(value);
  }
  return latest || null;
}

async function fallbackMasterRecord(ipoId) {
  const response = await fetch("data/ipos.json", { cache: "no-cache" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const payload = await response.json();
  return (
    (payload.ipos || []).find((item) => String(item.id) === String(ipoId)) ||
    null
  );
}

async function initCompanyRoute() {
  const root = document.getElementById("companyPage");
  const freshness = document.getElementById("routeFreshness");
  const ipoId = document.body.dataset.ipoId;
  if (!root) return;
  const theme = document.querySelector('meta[name="theme-color"]');
  if (theme) theme.content = "#f5f7f9";
  if (!document.querySelector('link[rel="icon"]')) {
    const favicon = document.createElement("link");
    favicon.rel = "icon";
    favicon.type = "image/svg+xml";
    favicon.href = new URL("favicon.svg", document.baseURI).href;
    document.head.appendChild(favicon);
  }
  if (!document.querySelector(".skip-link")) {
    const skip = document.createElement("a");
    skip.className = "skip-link";
    skip.href = `${window.location.pathname}${window.location.search}#companyPage`;
    skip.textContent = "Skip to company profile";
    document.body.prepend(skip);
  }
  root.setAttribute("tabindex", "-1");
  bindCompanyReturnLinks();

  try {
    // New routes are self-contained. The master fetch is only a temporary
    // compatibility fallback for route files generated before template v3.
    const ipo = embeddedProfile() || (await fallbackMasterRecord(ipoId));
    if (!ipo) {
      root.innerHTML =
        '<div class="company-route-error"><div class="eyebrow">IPO NOT FOUND</div><h1>This company route is no longer available.</h1><p>The company may have been renamed or merged into another official record.</p><a href="./">Return to IPO tracker</a></div>';
      bindCompanyReturnLinks();
      return;
    }

    document.title = `${ipo.company} IPO | India IPO Tracker`;
    const description = document.querySelector('meta[name="description"]');
    if (description) {
      description.content = `${ipo.company} IPO details, issue dates, price band, subscription, offer documents, financials and official source validation.`;
    }

    const updatedAt = latestProfileTimestamp(ipo);
    if (freshness)
      freshness.textContent = updatedAt
        ? `Record updated ${formatTimestamp(updatedAt)}`
        : "IPO research profile";
    root.innerHTML = routeProfileHtml(ipo);
    bindRouteNavigation(root);
    bindCompanyProfileActions(root);

    const shareButton = document.getElementById("copyCompanyLink");
    if (shareButton)
      shareButton.addEventListener("click", () =>
        copyPermanentLink(shareButton),
      );
  } catch (error) {
    console.error(error);
    if (freshness) freshness.textContent = "Data load failed";
    root.innerHTML =
      '<div class="company-route-error"><div class="eyebrow">DATA LOAD ERROR</div><h1>Could not load this IPO profile.</h1><p>Please retry in a moment.</p><a href="./">Return to IPO tracker</a></div>';
    bindCompanyReturnLinks();
  }
}

document.addEventListener("DOMContentLoaded", initCompanyRoute);
