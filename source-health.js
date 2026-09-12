/* Source-health semantics.
 * NSE history can legitimately return zero rows for a checked window (weekends,
 * holidays, or simply no newly listed IPOs). That is healthy, not a refresh
 * failure. Loaded immediately after app.js so later Phase 3/4 wrappers inherit
 * the corrected renderer.
 */

const baseSourceHealthRenderer = renderSourceHealth;

function nseHistoryError(meta) {
  const errors = Array.isArray(meta?.errors) ? meta.errors : [];
  return errors.find(message => String(message).startsWith('NSE history ')) || null;
}

function renderSourceHealthSemantically() {
  baseSourceHealthRenderer();
  if (!els.health) return;

  const history = state.meta?.sourceHealth?.['NSE-history'];
  if (!history) return;

  const item = [...els.health.querySelectorAll('.health-item')]
    .find(node => node.querySelector('strong')?.textContent === 'NSE-history');
  if (!item) return;

  const error = history.error || nseHistoryError(state.meta);
  const records = Number(history.records || 0);
  const dot = item.querySelector('.health-dot');
  const note = item.querySelector('span:last-child');

  if (!error && records === 0) {
    if (dot) dot.className = 'health-dot health-ok';
    if (note) note.textContent = history.note || 'checked · 0 new rows';
    return;
  }

  if (!error && history.ok) {
    if (dot) dot.className = 'health-dot health-ok';
    if (note) note.textContent = history.note || `${records.toLocaleString('en-IN')} rows`;
    return;
  }

  if (dot) dot.className = 'health-dot health-bad';
  if (note) note.textContent = 'refresh failed';
}

renderSourceHealth = renderSourceHealthSemantically;

// Also re-render once all deferred scripts have installed their wrappers. This
// makes the correction deterministic even when data/ipos.json is browser-cached.
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    if (state?.meta?.sourceHealth) renderSourceHealth();
  }, 0);
});
