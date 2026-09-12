/* Convert company names in the tracker table into permanent clean profile URLs.
 * Loaded after app.js/company.js so it can wrap the existing table renderer.
 */

function companyRouteSlug(value) {
  return String(value || '')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'ipo';
}

const routeTableRenderer = renderTable;
renderTable = function() {
  routeTableRenderer();
  els.rows.querySelectorAll('tr[data-id]').forEach(row => {
    const cell = row.querySelector('td.company');
    if (!cell || cell.querySelector('.company-name-link')) return;
    const ipo = state.data.find(item => String(item.id) === String(row.dataset.id));
    if (!ipo) return;
    const symbol = cell.querySelector('.symbol');
    const link = document.createElement('a');
    link.className = 'company-name-link';
    link.href = `ipo/${companyRouteSlug(ipo.id || ipo.company)}/`;
    link.textContent = ipo.company || 'Unknown';
    link.setAttribute('aria-label', `Open ${ipo.company || 'IPO'} permanent profile`);
    link.addEventListener('click', event => event.stopPropagation());
    cell.textContent = '';
    cell.appendChild(link);
    if (symbol) cell.appendChild(symbol);
  });
};
